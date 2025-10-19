from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.initial_data import InitialDataService


class InitDataProvider(Provider):
    """Провайдер для инициализации данных"""

    @provide(scope=Scope.APP)
    async def get_initial_data_service(self, db: AsyncSession) -> InitialDataService:
        return InitialDataService(db)