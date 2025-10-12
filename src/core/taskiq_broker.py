__all__ = (
    "broker",
    "scheduler",
)

import logging

import taskiq_fastapi
from taskiq import TaskiqEvents, TaskiqState
from taskiq_aio_pika import AioPikaBroker
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from dishka import make_async_container
from dishka.integrations.taskiq import TaskiqProvider, setup_dishka

from src.core.config.log_setup import setup_logging
from src.core.config.settings import settings
from src.providers.db_provider import DatabaseProvider

logger = logging.getLogger(__name__)

broker = AioPikaBroker(url=settings.rabbitmq.connection_url())

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)

taskiq_fastapi.init(broker, "src.main:app")

container = make_async_container(DatabaseProvider(), TaskiqProvider())

setup_dishka(container, broker)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def on_worker_startup(state: TaskiqState) -> None:
    setup_logging(debug=False)
    logger.info("Worker startup complete, state %s", state)
