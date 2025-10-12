from dishka import make_async_container
from dishka.integrations.fastapi import DishkaRoute, FastapiProvider, setup_dishka
from fastapi import APIRouter, Depends, FastAPI

from src.guard.auth import auth_guard

# Modules
from ..providers.db_provider import DatabaseProvider


api_router = APIRouter(
    prefix="/api", dependencies=[Depends(auth_guard)], route_class=DishkaRoute
)


# Регистрация провайдеров
def setup_container(app: FastAPI) -> None:
    container = make_async_container(
        FastapiProvider(),
        DatabaseProvider(),
    )

    setup_dishka(container, app)


__all__ = ["api_router", "setup_container"]
