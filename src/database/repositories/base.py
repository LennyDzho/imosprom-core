from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Base


class BaseRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, obj: Base) -> None:
        self.session.add(obj)

    async def delete(self, obj: Base) -> None:
        await self.session.delete(obj)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
