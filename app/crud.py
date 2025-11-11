from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Optional

from app import models, schemas

# Usuarios
async def get_usuario_por_email(db: AsyncSession, email: str) -> Optional[models.Usuario]:
    result = await db.execute(select(models.Usuario).where(models.Usuario.email == email))
    return result.scalar_one_or_none()

# Negocios

async def create_negocio(db: AsyncSession, negocio_in: schemas.NegocioCreate, usuario_id: int) -> models.Negocio:
    obj = models.Negocio(
        nombre = negocio_in.nombre,
        descripcion = negocio_in.descripcion,
        fecha_creacion = negocio_in.fecha_creacion,
        usuario_id = usuario_id
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def get_negocio(db: AsyncSession, negocio_id: int) -> Optional[models.Negocio]:
    result = await db.execute(select(models.Negocio).where(models.Negocio.id == negocio_id))
    return result.scalar_one_or_none()

async def update_negocio(db: AsyncSession, negocio_id: int, negocio_up: schemas.NegocioUpdate) -> Optional[models.Negocio]:
    obj = await get_negocio(db, negocio_id)
    if not obj:
        return None
    if negocio_up.nombre is not None:
        obj.nombre = negocio_up.nombre
    if negocio_up.descripcion is not None:
        obj.descripcion = negocio_up.descripcion
    await db.commit()
    await db.refresh(obj)
    return obj

async def delete_negocio(db: AsyncSession, negocio_id: int) -> bool:
    obj = await get_negocio(db, negocio_id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True

# Transacciones
async def create_transaccion(db: AsyncSession, tx_in: schemas.TransaccionCreate) -> models.Transaccion:
    obj = models.Transaccion(
        negocio_id=tx_in.negocio_id,
        tipo=models.TipoTransaccion(tx_in.tipo.value),
        monto=tx_in.monto,
        descripcion=tx_in.descripcion,
        fecha=tx_in.fecha
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def get_transacciones_by_negocio(db: AsyncSession, negocio_id: int) -> List[models.Transaccion]:
    result = await db.execute(select(models.Transaccion).where(models.Transaccion.negocio_id == negocio_id).order_by(models.Transaccion.fecha.desc()))
    return result.scalars().all()

async def get_transaccion(db: AsyncSession, trans_id: int) -> Optional[models.Transaccion]:
    result = await db.execute(select(models.Transaccion).where(models.Transaccion.id == trans_id))
    return result.scalar_one_or_none()

async def update_transaccion(db: AsyncSession, trans_id: int, tx_up: schemas.TransaccionCreate) -> Optional[models.Transaccion]:
    obj = await get_transaccion(db, trans_id)
    if not obj:
        return None
    obj.tipo = models.TipoTransaccion(tx_up.tipo.value)
    obj.monto = tx_up.monto
    obj.descripcion = tx_up.descripcion
    obj.fecha = tx_up.fecha
    await db.commit()
    await db.refresh(obj)
    return obj

async def delete_transaccion(db: AsyncSession, trans_id: int) -> bool:
    obj = await get_transaccion(db, trans_id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True

# Balance
async def get_balance(db: AsyncSession, negocio_id: int):
    q_ing = select(func.coalesce(func.sum(models.Transaccion.monto), 0)).where(
        models.Transaccion.negocio_id == negocio_id,
        models.Transaccion.tipo == models.TipoTransaccion.ingreso
    )
    q_eg = select(func.coalesce(func.sum(models.Transaccion.monto), 0)).where(
        models.Transaccion.negocio_id == negocio_id,
        models.Transaccion.tipo == models.TipoTransaccion.egreso
    )
    res_ing = await db.execute(q_ing)
    total_ing = res_ing.scalar() or Decimal("0.00")
    res_eg = await db.execute(q_eg)
    total_eg = res_eg.scalar() or Decimal("0.00")
    balance = (total_ing or Decimal("0.00")) - (total_eg or Decimal("0.00"))
    return {
        "negocio_id": negocio_id,
        "total_ingresos": total_ing,
        "total_egresos": total_eg,
        "balance": balance
    }