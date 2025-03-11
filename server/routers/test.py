import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from server.backend.database import get_session, Base

router = APIRouter(prefix="/test", tags=["test"])


@router.delete("/clean-db", summary="Очистка БД (только для тестового окружения или с правильным ADMIN_KEY)")
async def clean_db(admin_key: str = Query(None), session: AsyncSession = Depends(get_session)):
    if os.getenv("ENV_TYPE") != "test" and admin_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Доступ разрешён только в тестовом окружении или с правильным ADMIN_KEY")
    for table in reversed(Base.metadata.sorted_tables):
        await session.execute(table.delete())
    await session.commit()
    return {"detail": "База данных очищена"}