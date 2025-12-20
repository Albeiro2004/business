from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/abonos", tags=["abonos"])


@router.post("", response_model=schemas.AbonoOut, status_code=status.HTTP_201_CREATED)
async def create_abono(
        abono_in: schemas.AbonoCreate,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """
    Registrar un abono a una deuda.

    El sistema automáticamente:
    - Actualiza el monto_pagado de la deuda
    - Actualiza el estado de la deuda (pendiente/parcial/saldado)
    - Valida que el abono no exceda el saldo pendiente
    - Envía notificación por Telegram si está configurado
    """
    return await crud.create_abono(db, abono_in, current_user.id)