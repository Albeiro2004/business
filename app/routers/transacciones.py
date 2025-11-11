# app/routers/transacciones.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/transacciones", tags=["transacciones"])

@router.post("", response_model=schemas.TransaccionOut)
async def create_transaccion(tx_in: schemas.TransaccionCreate, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    negocio = await crud.get_negocio(db, tx_in.negocio_id)
    if not negocio or negocio.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado o no pertenece al usuario")
    return await crud.create_transaccion(db, tx_in)

@router.get("/negocio/{negocio_id}", response_model=List[schemas.TransaccionOut])
async def list_transacciones(negocio_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    negocio = await crud.get_negocio(db, negocio_id)
    if not negocio or negocio.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado o no pertenece al usuario")
    return await crud.get_transacciones_by_negocio(db, negocio_id)

@router.get("/negocio/{negocio_id}/balance", response_model=schemas.BalanceOut)
async def get_balance(negocio_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    negocio = await crud.get_negocio(db, negocio_id)
    if not negocio or negocio.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado o no pertenece al usuario")
    return await crud.get_balance(db, negocio_id)

@router.put("/{trans_id}", response_model=schemas.TransaccionOut)
async def update_transaccion(trans_id: int, tx_up: schemas.TransaccionCreate, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    trans = await crud.get_transaccion(db, trans_id)
    if not trans:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    # validar propiedad del negocio
    negocio = await crud.get_negocio(db, trans.negocio_id)
    if not negocio or negocio.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return await crud.update_transaccion(db, trans_id, tx_up)

@router.delete("/{trans_id}")
async def delete_transaccion(trans_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    trans = await crud.get_transaccion(db, trans_id)
    if not trans:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    negocio = await crud.get_negocio(db, trans.negocio_id)
    if not negocio or negocio.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    await crud.delete_transaccion(db, trans_id)
    return {"detail": "Transacción eliminada"}
