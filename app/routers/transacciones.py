# app/routers/transacciones.py
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/transacciones", tags=["transacciones"])

@router.post("", response_model=schemas.TransaccionOut)
async def create_transaccion(tx_in: schemas.TransaccionCreate,
                             db: AsyncSession = Depends(get_db),
                             current_user: models.Usuario = Depends(get_current_user)):
    is_member = await crud.usuario_en_negocio(db, tx_in.negocio_id, current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")
    return await crud.create_transaccion(db, tx_in, current_user.id)

@router.get("/negocio/{negocio_id}", response_model=List[schemas.TransaccionOut])
async def list_transacciones(negocio_id: int, tipo: Optional[schemas.TipoTransaccion] = None, fecha_inicio: Optional[date] = None,
                             fecha_fin: Optional[date] = None, db: AsyncSession = Depends(get_db),
                             current_user: models.Usuario = Depends(get_current_user)):
    is_member = await crud.usuario_en_negocio(db, negocio_id, current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")
    return await crud.get_transacciones_by_negocio(db, negocio_id, tipo, fecha_inicio, fecha_fin)

@router.get("/{trans_id}", response_model=schemas.TransaccionOut)
async def get_transaccion(
        trans_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)):
    obj = await crud.get_transaccion(db, trans_id)
    if not obj:
        raise HTTPException(status_code=404, detail="NO autorizado")
    return obj

@router.put("/{trans_id}", response_model=schemas.TransaccionOut)
async def update_transaccion(trans_id: int, tx_up: schemas.TransaccionCreate, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    trans = await crud.get_transaccion(db, trans_id)
    if not trans:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")

    is_member = await crud.usuario_en_negocio(db, trans.negocio_id, current_user)
    if not is_member:
        raise HTTPException(status_code=403, detail="No autorizado")
    return await crud.update_transaccion(db, trans_id, tx_up)

@router.delete("/{trans_id}")
async def delete_transaccion(trans_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    trans = await crud.get_transaccion(db, trans_id)
    if not trans:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    is_member = await crud.usuario_en_negocio(db, trans.negocio_id, current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="No autorizado")
    await crud.delete_transaccion(db, trans_id)
    return {"detail": "Transacción eliminada"}

@router.get("/negocio/{negocio_id}/balance", response_model=schemas.BalanceOut)
async def get_balance(negocio_id: int, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    is_member = await crud.usuario_en_negocio(db, negocio_id, current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="No autorizado")
    return await crud.get_balance(db, negocio_id, fecha_inicio, fecha_fin)
