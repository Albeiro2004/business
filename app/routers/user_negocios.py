from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.schemas import UsuarioShema
from app import models

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

@router.get("/buscar", response_model=List[UsuarioShema])
async def buscar_usuarios(query: str = Query(..., min_length=4), db: AsyncSession = Depends(get_db)):
    query_lower = f"%{query.lower()}%"

    result = await db.execute(
        select(models.Usuario).where(
            models.Usuario.nombre.ilike(query_lower) |
            models.Usuario.email.ilike(query_lower)
        ).order_by(models.Usuario.nombre.asc())
    )

    return result.scalars().all()
