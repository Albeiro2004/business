from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/deudas", tags=["deudas"])


@router.post("", response_model=schemas.DeudaOut, status_code=status.HTTP_201_CREATED)
async def create_deuda(
        deuda_in: schemas.DeudaCreate,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Crear una nueva deuda asociada a una transacción y cliente"""
    return await crud.create_deuda(db, deuda_in, current_user.id)


@router.get("/negocio/{negocio_id}", response_model=List[schemas.DeudaDetalle])
async def list_deudas_negocio(
        negocio_id: int,
        estado: Optional[schemas.EstadoDeuda] = Query(None, description="Filtrar por estado de deuda"),
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Listar todas las deudas de un negocio con opción de filtrar por estado"""
    return await crud.get_deudas_by_negocio(db, negocio_id, current_user.id, estado)


@router.get("/negocio/{negocio_id}/resumen", response_model=schemas.ResumenDeudasOut)
async def get_resumen_deudas(
        negocio_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Obtener resumen estadístico de deudas del negocio"""
    return await crud.get_resumen_deudas(db, negocio_id, current_user.id)


@router.get("/{deuda_id}", response_model=schemas.DeudaDetalle)
async def get_deuda(
        deuda_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Obtener detalle de una deuda específica"""
    obj = await crud.get_deuda(db, deuda_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deuda no encontrada")

    # Verificar acceso al negocio
    is_member = await crud.usuario_en_negocio(db, obj.cliente.negocio_id, current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="No autorizado")

    return obj


@router.get("/{deuda_id}/abonos", response_model=List[schemas.AbonoOut])
async def get_abonos_deuda(
        deuda_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.Usuario = Depends(get_current_user)
):
    """Obtener historial de abonos de una deuda"""
    return await crud.get_abonos_by_deuda(db, deuda_id, current_user.id)