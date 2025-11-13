from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/negocios", tags=["negocios"])

@router.post("", response_model=schemas.NegocioOut)
async def create_negocio(negocio_in: schemas.NegocioCreate, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    return await crud.create_negocio(db, negocio_in, current_user.id)

@router.get("", response_model=List[schemas.NegocioOut])
async def list_negocios(db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    return await crud.get_negocios(db, current_user.id)

@router.get("/{negocio_id}", response_model=schemas.NegocioOut)
async def get_negocio(negocio_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    obj = await crud.get_negocio(db, negocio_id, current_user.id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")
    return obj

@router.put("/{negocio_id}", response_model=schemas.NegocioOut)
async def update_negocio(negocio_id: int, negocio_up: schemas.NegocioUpdate, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    obj = await crud.get_negocio(db, negocio_id, current_user.id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")
    return await crud.update_negocio(db, negocio_id, negocio_up)

@router.delete("/{negocio_id}")
async def delete_negocio(negocio_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    obj = await crud.get_negocio(db, negocio_id, current_user.id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")
    await crud.delete_negocio(db, negocio_id)
    return {"detail": "Negocio eliminado"}


