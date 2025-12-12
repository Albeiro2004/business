from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import schemas, crud, models
from app.database import get_db
from app.auth import get_current_user
from app.models import Negocio, Usuario

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
    obj = await crud.update_negocio(db, negocio_id, current_user.id, negocio_up)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")
    return obj

@router.delete("/{negocio_id}")
async def delete_negocio(negocio_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    obj = await crud.delete_negocio(db, negocio_id, current_user.id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")
    await crud.delete_negocio(db, negocio_id, current_user.id)
    return {"detail": "Negocio eliminado"}

@router.get("/{negocio_id}/usuarios", response_model=List[schemas.UsuarioOut])
async def obtener_usuarios_negocio(negocio_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Negocio).options(selectinload(Negocio.usuarios)).where(Negocio.id == negocio_id))
    negocio = result.scalar_one_or_none()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return negocio.usuarios

@router.post("/{negocio_id}/usuarios/{usuario_id}")
async def agregar_usuario_a_negocio(negocio_id: int, usuario_id: int, db: AsyncSession = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):

    is_member = await  crud.usuario_en_negocio(db, negocio_id, current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, datail="No autorizado")
    return await crud.agregar_usuario_a_negocio(db, negocio_id, usuario_id)



