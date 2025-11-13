from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

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
        fecha_creacion = datetime.now(),
        usuario_id = usuario_id
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async  def get_negocios(db: AsyncSession, usuario_id: int) -> List[models.Negocio]:
    result = await db.execute(
        select(models.Negocio).where(models.Negocio.usuario_id == usuario_id).order_by(models.Negocio.created_at.desc())
    )
    return result.scalars().all()

async def get_negocio(db: AsyncSession, negocio_id: int, usuario_id: int) -> Optional[models.Negocio]:
    result = await db.execute(
        select(models.Negocio).where(
            models.Negocio.id == negocio_id,
            models.Negocio.usuario_id == usuario_id
        )
    )
    return result.scalar_one_or_none()

async def update_negocio(db: AsyncSession, negocio_id: int, usuario_id: int, negocio_up: schemas.NegocioUpdate) -> Optional[models.Negocio]:
    obj = await get_negocio(db, negocio_id, usuario_id)
    if not obj:
        return None
    if negocio_up.nombre is not None:
        obj.nombre = negocio_up.nombre
    if negocio_up.descripcion is not None:
        obj.descripcion = negocio_up.descripcion
    await db.commit()
    await db.refresh(obj)
    return obj

async def delete_negocio(db: AsyncSession, negocio_id: int, usuario_id: int) -> bool:
    obj = await get_negocio(db, negocio_id, usuario_id)
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

async def get_transacciones_by_negocio(
    db: AsyncSession,
    negocio_id: int,
    tipo: Optional[models.TipoTransaccion] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None
) -> List[models.Transaccion]:
    query = select(models.Transaccion).where(models.Transaccion.negocio_id == negocio_id)

    if tipo:
        query = query.where(models.Transaccion.tipo == tipo)
    if fecha_inicio:
        query = query.where(models.Transaccion.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.where(models.Transaccion.fecha <= fecha_fin)

    query = query.order_by(models.Transaccion.fecha.desc())

    result = await db.execute(query)
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
async def get_balance(db: AsyncSession, negocio_id: int, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None):
    q_ing = select(func.coalesce(func.sum(models.Transaccion.monto), 0)).where(
        models.Transaccion.negocio_id == negocio_id,
        models.Transaccion.tipo == models.TipoTransaccion.ingreso
    )
    q_eg = select(func.coalesce(func.sum(models.Transaccion.monto), 0)).where(
        models.Transaccion.negocio_id == negocio_id,
        models.Transaccion.tipo == models.TipoTransaccion.egreso
    )

    if fecha_inicio:
        q_ing = q_ing.where(models.Transaccion.fecha >= fecha_inicio)
        q_eg = q_eg.where(models.Transaccion.fecha >= fecha_inicio)
    if fecha_fin:
        q_ing = q_ing.where(models.Transaccion.fecha <= fecha_fin)
        q_eg = q_eg.where(models.Transaccion.fecha <= fecha_fin)

    res_ing = await db.execute(q_ing)
    total_ing = res_ing.scalar() or Decimal("0.00")
    res_eg = await db.execute(q_eg)
    total_eg = res_eg.scalar() or Decimal("0.00")
    balance = (total_ing or Decimal("0.00")) - (total_eg or Decimal("0.00"))
    return {
        "negocio_id": negocio_id,
        "total_ingresos": total_ing,
        "total_egresos": total_eg,
        "balance": balance,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }