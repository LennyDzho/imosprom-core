from typing import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import db_helper


class DatabaseProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def provide_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with db_helper.session_factory() as session:
            yield session
