import json
import logging
import time
from datetime import datetime
from typing import Optional

from dishka.integrations.taskiq import inject, FromDishka
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import broker
from src.database.models.jobs import Job, JobStatusE
from src.database.models.research import Research, ResearchStatusE
from src.database.models.research_results import (
    ResearchResult,
    ProcessingStatusE,
    PathologyStatusE,
)
from src.utils.run_test_model.test_model import _run_model_inference, _coerce_pathology_status, _coerce_pathology_type

logger = logging.getLogger("jobs")


# ============
# ВСПОМОГАТЕЛЬНОЕ: место вызова вашей модели
# ============




# ============
# ТАСКИ
# ============

@broker.task(task_name="enqueue_jobs_for_batch")
@inject(patch_module=True)
async def enqueue_jobs_for_batch(
    session: FromDishka[AsyncSession],
    batch_id: int,
    model_version: str,
    params_json: Optional[dict] = None,
) -> int:
    """
    Создать Job для каждого Research из батча, у которых статус READY.
    Возвращает количество созданных заданий.
    """
    logger.info("enqueue_jobs_for_batch: batch_id=%s", batch_id)

    params = params_json or {}

    q = (
        select(Research)
        .where(
            Research.batch_id == batch_id,
            Research.status == ResearchStatusE.READY,
        )
        .order_by(Research.research_id.asc())
    )

    researches = (await session.execute(q)).scalars().all()
    if not researches:
        logger.info("No READY research in batch %s", batch_id)
        return 0

    created = 0
    for r in researches:
        job = Job(
            research_id=r.research_id,
            model_version=model_version,
            params_json=params,
            status=JobStatusE.QUEUED,
        )
        session.add(job)
        created += 1

    await session.commit()
    logger.info("Created %s jobs for batch %s", created, batch_id)
    return created


@broker.task(task_name="process_single_job")
@inject(patch_module=True)
async def process_single_job(
    session: FromDishka[AsyncSession],
    job_id: int,
) -> None:
    """
    Обработать одну джобу по id.
    """
    logger.info("process_single_job: job_id=%s", job_id)

    stmt = (
        select(Job)
        .options(selectinload(Job.research))
        .where(Job.job_id == job_id)
        .limit(1)
    )
    job = (await session.execute(stmt)).scalars().first()
    if not job:
        logger.warning("Job %s not found", job_id)
        return

    if not job.research:
        logger.warning("Job %s has no research relation", job_id)
        return

    if job.status not in (JobStatusE.QUEUED, JobStatusE.FAILURE):
        logger.info("Job %s has status=%s, skip", job.job_id, job.status)
        return

    # RUNNING
    job.status = JobStatusE.RUNNING
    job.started_at = datetime.utcnow()
    await session.commit()

    t0 = time.perf_counter()
    try:
        # вызов вашей модели
        result = await _run_model_inference(
            object_uri=job.research.object_uri,
            model_version=job.model_version,
            params=job.params_json or {},
        )

        # собрать ResearchResult
        prob = float(result.get("probability_of_pathology", 0.0))
        p_status = _coerce_pathology_status(result.get("pathology_status", "uncertain"))
        p_type = _coerce_pathology_type(result.get("pathology_type"))
        p_type_danger = _coerce_pathology_type(result.get("most_dangerous_pathology_type"))

        rr = ResearchResult(
            job_id=job.job_id,
            research_id=job.research_id,
            # поля для .xlsx/совместимости
            path_to_study=job.research.object_uri,
            study_uid=None,
            series_uid=None,
            probability_of_pathology=prob,
            pathology=1 if p_status == PathologyStatusE.PATHOLOGY else 0,
            processing_status=ProcessingStatusE.SUCCESS,
            time_of_processing=None,  # заполним после замера

            # расширенный диагноз
            pathology_status=p_status,
            pathology_type=p_type,
            most_dangerous_pathology_type=p_type_danger,

            # распределения / топ-K
            pathology_probs=result.get("pathology_probs"),
            topk_pathologies=result.get("topk_pathologies"),

            # локализация / артефакты
            primary_bbox=result.get("primary_bbox"),
            slice_index=result.get("slice_index"),
            mask_uri=result.get("mask_uri"),
            heatmap_uri=result.get("heatmap_uri"),
            localization_note=result.get("localization_note"),
        )
        session.add(rr)

        # завершение job
        job.finished_at = datetime.utcnow()
        job.time_sec = round(time.perf_counter() - t0, 3)
        rr.time_of_processing = job.time_sec
        job.status = JobStatusE.SUCCESS

        await session.commit()
        logger.info("Job %s finished: SUCCESS (time=%ss)", job.job_id, job.time_sec)

    except Exception as e:
        logger.exception("Job %s failed: %s", job.job_id, e)
        job.finished_at = datetime.utcnow()
        job.time_sec = round(time.perf_counter() - t0, 3)
        job.status = JobStatusE.FAILURE
        job.error_message = str(e)[:2000]
        await session.commit()


@broker.task(task_name="process_queued_jobs", schedule=[{"cron": "* * * * *"}])
@inject(patch_module=True)
async def process_queued_jobs(
    session: FromDishka[AsyncSession],
    limit: int = 50,
) -> None:
    """
    Периодическая задача: обрабатывает пачку `queued`-джобов (FIFO) раз в минуту.

    - Берём до `limit` заданий со статусом 'queued';
    - Переводим каждое в 'running' и запускаем обработку;
    - Пишем ResearchResult и обновляем статус.
    """
    logger.info("process_queued_jobs: start (limit=%s)", limit)

    # подхватываем LIMIT джобов в статусе QUEUED
    stmt = (
        select(Job)
        .options(selectinload(Job.research))
        .where(Job.status == JobStatusE.QUEUED)
        .order_by(Job.created_at.asc())
        .limit(limit)
    )
    jobs = (await session.execute(stmt)).scalars().all()
    if not jobs:
        logger.info("No queued jobs")
        return

    for job in jobs:
        try:
            await process_single_job.kiq(job_id=job.job_id)  # ставим в очередь tasq (не блокируем цикл)
        except Exception:
            logger.exception("Failed to enqueue process_single_job for job_id=%s", job.job_id)
