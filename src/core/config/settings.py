from pathlib import Path
from typing import Optional

from environs import Env
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class AppConfig(BaseModel):
    debug: bool
    api_key: str

class DatabaseConfig(BaseModel):
    database: str
    user: str
    password: str
    host: str
    port: int

    def connection_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:"
            f"{self.port}/{self.database}"
        )


class RedisConfig(BaseModel):
    host: str
    port: int
    password: str
    db: int

    def connection_url(self, db: Optional[int] = None) -> str:
        actual_db = db if db is not None else self.db
        return f"redis://:{self.password}@{self.host}:{self.port}/{actual_db}"


class RabbitMQConfig(BaseModel):
    user: str
    password: str
    host: str
    port: int

    def connection_url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}"


class Settings(BaseModel):
    app: AppConfig
    db: DatabaseConfig
    redis: RedisConfig
    rabbitmq: RabbitMQConfig


def load_settings() -> Settings:
    env_path = BASE_DIR / ".env"
    env = Env()

    env.read_env(env_path)

    return Settings(
        app=AppConfig(
          debug=env.bool("DEBUG"),
          api_key=env.str("API_KEY"),
        ),
        db=DatabaseConfig(
            database=env.str("DB_NAME"),
            user=env.str("DB_USER"),
            password=env.str("DB_PASSWORD"),
            host=env.str("DB_HOST"),
            port=env.int("DB_PORT"),
        ),
        redis=RedisConfig(
            host=env.str("REDIS_HOST"),
            port=env.int("REDIS_PORT"),
            password=env.str("REDIS_PASSWORD"),
            db=env.int("REDIS_DB"),
        ),
        rabbitmq=RabbitMQConfig(
            user=env.str("RABBITMQ_USER"),
            password=env.str("RABBITMQ_PASSWORD"),
            host=env.str("RABBITMQ_HOST"),
            port=env.int("RABBITMQ_PORT"),
        ),
    )


settings: Settings = load_settings()