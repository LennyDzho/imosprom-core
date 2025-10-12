from typing import Optional

from src.database.models.research_results import (
    PathologyStatusE,
    PathologyTypeE,
)

async def _run_model_inference(object_uri: str, model_version: str, params: dict) -> dict:
    """
    Заглушка вызова инференса.

    Здесь вы:
      - скачиваете DICOM из MinIO (object_uri),
      - гоняете через свою модель,
      - возвращаете словарь результата.

    Ожидаемый формат (пример):
    {
      "probability_of_pathology": 0.8234,
      "pathology_status": "pathology",                # normal|pathology|uncertain
      "pathology_type": "pneumonia",                  # одно из PathologyTypeE
      "most_dangerous_pathology_type": "pneumonia",   # опционально
      "pathology_probs": {"pneumonia": 0.82, "cancer": 0.12, "other": 0.06},
      "topk_pathologies": [{"type": "pneumonia", "prob": 0.82}, {"type": "cancer", "prob": 0.12}],
      "primary_bbox": [10, 50, 20, 80, 5, 15],        # или None
      "slice_index": 42,
      "mask_uri": "s3://bucket/researchs/research_123/mask.nii.gz",      # если сохраняете
      "heatmap_uri": "s3://bucket/researchs/research_123/heatmap.nii.gz",# если сохраняете
      "localization_note": "Right upper lobe"
    }

    В текущей заглушке вернем фиктивные данные.
    """
    # TODO: заменить на реальный вызов вашей модели
    # простейшая фиктивная логика
    p = 0.85
    return {
        "probability_of_pathology": p,
        "pathology_status": "pathology" if p >= 0.5 else "normal",
        "pathology_type": "pneumonia",
        "most_dangerous_pathology_type": "pneumonia",
        "pathology_probs": {"pneumonia": p, "cancer": 0.1, "other": 0.05},
        "topk_pathologies": [{"type": "pneumonia", "prob": p}, {"type": "cancer", "prob": 0.1}],
        "primary_bbox": [10, 50, 20, 80, 5, 15],
        "slice_index": 42,
        "mask_uri": None,
        "heatmap_uri": None,
        "localization_note": "Right upper lobe",
    }


def _coerce_pathology_status(val: str) -> PathologyStatusE:
    try:
        return PathologyStatusE(val)
    except Exception:
        return PathologyStatusE.UNCERTAIN


def _coerce_pathology_type(val: Optional[str]) -> Optional[PathologyTypeE]:
    if val is None:
        return None
    try:
        return PathologyTypeE(val)
    except Exception:
        return PathologyTypeE.OTHER