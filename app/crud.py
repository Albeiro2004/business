from datetime import date
from http.client import HTTPException

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from watchfiles import awatch

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
        fecha_creacion = date.today(),
    )
    db.add(obj)
    await db.flush()
    await db.execute(models.usuarios_negocios.insert().values(usuario_id=usuario_id, negocio_id=obj.id))
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_negocios(db: AsyncSession, usuario_id: int):
    result = await db.execute(
        select(models.Negocio)
        .join(models.usuarios_negocios, models.usuarios_negocios.c.negocio_id == models.Negocio.id)
        .where(models.usuarios_negocios.c.usuario_id == usuario_id)
        .order_by(models.Negocio.created_at.desc())
    )
    return result.scalars().all()

async def get_negocio(db: AsyncSession, negocio_id: int, usuario_id: int) -> Optional[models.Negocio]:
    result = await db.execute(
        select(models.Negocio)
        .join(models.usuarios_negocios, models.usuarios_negocios.c.negocio_id == models.Negocio.id)
        .where(
            models.Negocio.id == negocio_id,
            models.usuarios_negocios.c.usuario_id == usuario_id
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
async def create_transaccion(db: AsyncSession, tx_in: schemas.TransaccionCreate, usuario_id: int) -> models.Transaccion:

    if not await usuario_en_negocio(db, tx_in.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    obj = models.Transaccion(
        negocio_id=tx_in.negocio_id,
        tipo=models.TipoTransaccion(tx_in.tipo.value if hasattr(tx_in.tipo, "value") else tx_in.tipo),
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


async def usuario_en_negocio(db: AsyncSession, negocio_id: int, usuario_id: int) -> bool:
    result = await db.execute(
        select(models.usuarios_negocios)
        .where(
            models.usuarios_negocios.c.negocio_id == negocio_id,
                        models.usuarios_negocios.c.usuario_id == usuario_id
        )
    )
    return result.first() is not None

async def agregar_usuario_a_negocio(db:AsyncSession, negocio_id: int, usuario_id: int):

    neg = await db.execute(select(models.Negocio).where(models.Negocio.id == negocio_id))
    negocio = neg.scalar_one_or_none()
    usr = await db.execute(select(models.Usuario).where(models.Usuario.id == usuario_id))
    usuario = usr.scalar_one_or_none()
    if not negocio or not usuario:
        raise HTTPException(status_code=404, detail="Usuario o negocio no encontrado")

    if await usuario_en_negocio(db, negocio_id, usuario_id):
        return {"mensaje": "Usuario ya está asociado al negocio"}

    await db.execute(models.usuarios_negocios.insert().values(usuario_id=usuario_id, negocio_id=negocio_id))
    await db.commit()
    return {"mensaje": "Usuario agregado satisfactoriamente"}