import logging

from minio import Minio

from src.core.config.settings import BASE_DIR
from src.core import settings

logger = logging.getLogger(__name__)


class MinioClient(Minio):
    def __init__(self, bucket_name: str = "ct-screening", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._bucket_name = bucket_name
        self._prefix = "batches/"



minio_client = MinioClient(
    endpoint=settings.minio.endpoint,
    access_key=settings.minio.access_key,
    secret_key=settings.minio.secret_key,
    bucket_name=settings.minio.bucket_name,
    secure=False,
)
