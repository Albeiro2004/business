from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.post("", response_model=schemas.ClienteOut, status_code=status.HTTP_201_CREATED)
async def create_cliente(
        cliente_in: schemas.ClienteCreate,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Crear un nuevo cliente"""
    return await crud.create_cliente(db, cliente_in, current_user.id)


@router.get("/negocio/{negocio_id}", response_model=List[schemas.ClienteOut])
async def list_clientes(
        negocio_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Listar todos los clientes de un negocio"""
    return await crud.get_clientes_by_negocio(db, negocio_id, current_user.id)


@router.get("/{cliente_id}", response_model=schemas.ClienteOut)
async def get_cliente(
        cliente_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Obtener un cliente específico"""
    obj = await crud.get_cliente(db, cliente_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    # Verificar acceso al negocio
    is_member = await crud.usuario_en_negocio(db, obj.negocio_id, current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="No autorizado")

    return obj


@router.put("/{cliente_id}", response_model=schemas.ClienteOut)
async def update_cliente(
        cliente_id: int,
        cliente_up: schemas.ClienteUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Actualizar un cliente"""
    obj = await crud.update_cliente(db, cliente_id, cliente_up, current_user.id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return obj


@router.delete("/{cliente_id}")
async def delete_cliente(
        cliente_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Eliminar un cliente"""
    success = await crud.delete_cliente(db, cliente_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return {"detail": "Cliente eliminado"}


@router.get("/{cliente_id}/deudas", response_model=List[schemas.DeudaOut])
async def get_deudas_cliente(
        cliente_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Obtener todas las deudas de un cliente"""
    return await crud.get_deudas_by_cliente(db, cliente_id, current_user.id)