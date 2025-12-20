from datetime import date
from http.client import HTTPException

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import joinedload

from app import models, schemas
from app.utils.telegram import enviar_mensaje_telegram


# Usuarios
async def get_usuario_por_email(db: AsyncSession, email: str) -> Optional[models.Usuario]:
    result = await db.execute(select(models.Usuario).where(models.Usuario.email == email))
    return result.scalar_one_or_none()


# Negocios
async def create_negocio(db: AsyncSession, negocio_in: schemas.NegocioCreate, usuario_id: int) -> models.Negocio:
    obj = models.Negocio(
        nombre=negocio_in.nombre,
        descripcion=negocio_in.descripcion,
        fecha_creacion=date.today(),
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
        .options(joinedload(models.Negocio.usuarios))
        .join(
            models.usuarios_negocios,
            models.usuarios_negocios.c.negocio_id == models.Negocio.id
        )
        .where(models.usuarios_negocios.c.usuario_id == usuario_id)
        .order_by(models.Negocio.created_at.desc())
    )
    return result.unique().scalars().all()


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


async def update_negocio(db: AsyncSession, negocio_id: int, usuario_id: int, negocio_up: schemas.NegocioUpdate) -> \
Optional[models.Negocio]:
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


# Clientes
async def create_cliente(
    db: AsyncSession,
    cliente_in: schemas.ClienteCreate,
    usuario_id: int
) -> dict:
    if not await usuario_en_negocio(db, cliente_in.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    obj = models.Cliente(
        negocio_id=cliente_in.negocio_id,
        identidad=cliente_in.identidad,
        nombre=cliente_in.nombre
    )

    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    # cliente nuevo → deuda = 0
    return {
        "id": obj.id,
        "negocio_id": obj.negocio_id,
        "identidad": obj.identidad,
        "nombre": obj.nombre,
        "created_at": obj.created_at
    }



async def get_clientes_by_negocio(db: AsyncSession, negocio_id: int, usuario_id: int) -> List[models.Cliente]:
    if not await usuario_en_negocio(db, negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    result = await db.execute(
        select(models.Cliente)
        .where(models.Cliente.negocio_id == negocio_id)
        .order_by(models.Cliente.nombre)
    )
    return result.scalars().all()


async def get_cliente(db: AsyncSession, cliente_id: int) -> Optional[models.Cliente]:
    result = await db.execute(select(models.Cliente).where(models.Cliente.id == cliente_id))
    return result.scalar_one_or_none()


async def update_cliente(db: AsyncSession, cliente_id: int, cliente_up: schemas.ClienteUpdate, usuario_id: int) -> \
Optional[models.Cliente]:
    obj = await get_cliente(db, cliente_id)
    if not obj:
        return None

    if not await usuario_en_negocio(db, obj.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    if cliente_up.identidad is not None:
        obj.identidad = cliente_up.identidad
    if cliente_up.nombre is not None:
        obj.nombre = cliente_up.nombre

    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_cliente(db: AsyncSession, cliente_id: int, usuario_id: int) -> bool:
    obj = await get_cliente(db, cliente_id)
    if not obj:
        return False

    if not await usuario_en_negocio(db, obj.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

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
        fecha=date.today(),
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    result = await db.execute(select(models.Usuario).where(models.Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()

    if usuario and usuario.telegram_chat_id:
        mensaje = (
            f"Transacción registrada por {usuario.nombre}\n\n"
            f"<b>Tipo:</b> {tx_in.tipo.value}\n"
            f"<b>Monto:</b> ${tx_in.monto}\n"
            f"<b>Descripción:</b> {tx_in.descripcion or 'Sin descripción'}\n"
            f"<b>Negocio ID:</b> {tx_in.negocio_id}"
        )
        await enviar_mensaje_telegram(usuario.telegram_chat_id, mensaje)

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


async def update_transaccion(db: AsyncSession, trans_id: int, tx_up: schemas.TransaccionCreate, usuario_id: int) -> \
Optional[models.Transaccion]:
    obj = await get_transaccion(db, trans_id)
    if not obj:
        return None
    obj.tipo = models.TipoTransaccion(tx_up.tipo.value)
    obj.monto = tx_up.monto
    obj.descripcion = tx_up.descripcion
    obj.fecha = tx_up.fecha
    await db.commit()
    await db.refresh(obj)

    result = await db.execute(select(models.Usuario).where(models.Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()

    if usuario and usuario.telegram_chat_id:
        mensaje = (
            f"{usuario.nombre} ha modificado la transacción a:\n\n"
            f"<b>Tipo:</b> {tx_up.tipo.value}\n"
            f"<b>Monto:</b> ${tx_up.monto}\n"
            f"<b>Descripción:</b> {tx_up.descripcion or 'Sin descripción'}\n"
            f"<b>Negocio ID:</b> {tx_up.negocio_id}"
        )
        await enviar_mensaje_telegram(usuario.telegram_chat_id, mensaje)

    return obj


async def delete_transaccion(db: AsyncSession, trans_id: int, usuario_id: int) -> bool:
    obj = await get_transaccion(db, trans_id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()

    result = await db.execute(select(models.Usuario).where(models.Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()

    if usuario and usuario.telegram_chat_id:
        mensaje = (
            f"Transacción eliminada por: {usuario.nombre}\n\n"
            f"<b>User:</b> {usuario.email}\n"
        )
        await enviar_mensaje_telegram(usuario.telegram_chat_id, mensaje)

    return True


# Deudas
async def create_deuda(db: AsyncSession, deuda_in: schemas.DeudaCreate, usuario_id: int) -> models.Deuda:
    # Verificar que la transacción existe
    transaccion = await get_transaccion(db, deuda_in.transaccion_id)
    if not transaccion:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    # Verificar que el cliente existe
    cliente = await get_cliente(db, deuda_in.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Verificar que ambos pertenecen al mismo negocio
    if transaccion.negocio_id != cliente.negocio_id:
        raise HTTPException(status_code=400, detail="Cliente y transacción deben pertenecer al mismo negocio")

    # Verificar que el usuario tiene acceso
    if not await usuario_en_negocio(db, transaccion.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    obj = models.Deuda(
        transaccion_id=deuda_in.transaccion_id,
        cliente_id=deuda_in.cliente_id,
        monto_total=deuda_in.monto_total
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_deudas_by_cliente(db: AsyncSession, cliente_id: int, usuario_id: int) -> List[models.Deuda]:
    cliente = await get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if not await usuario_en_negocio(db, cliente.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    result = await db.execute(
        select(models.Deuda)
        .options(joinedload(models.Deuda.transaccion))
        .where(models.Deuda.cliente_id == cliente_id)
        .order_by(models.Deuda.created_at.desc())
    )
    return result.unique().scalars().all()


async def get_deudas_by_negocio(
        db: AsyncSession,
        negocio_id: int,
        usuario_id: int,
        estado: Optional[models.EstadoDeuda] = None
) -> List[models.Deuda]:
    if not await usuario_en_negocio(db, negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    query = (
        select(models.Deuda)
        .options(
            joinedload(models.Deuda.cliente),
            joinedload(models.Deuda.transaccion)
        )
        .join(models.Cliente)
        .where(models.Cliente.negocio_id == negocio_id)
    )

    if estado:
        query = query.where(models.Deuda.estado == estado)

    query = query.order_by(models.Deuda.created_at.desc())

    result = await db.execute(query)
    return result.unique().scalars().all()


async def get_deuda(db: AsyncSession, deuda_id: int) -> Optional[models.Deuda]:
    result = await db.execute(
        select(models.Deuda)
        .options(
            joinedload(models.Deuda.cliente),
            joinedload(models.Deuda.transaccion)
        )
        .where(models.Deuda.id == deuda_id)
    )
    return result.unique().scalar_one_or_none()


# Abonos
async def create_abono(db: AsyncSession, abono_in: schemas.AbonoCreate, usuario_id: int) -> models.Abono:
    # Obtener la deuda
    deuda = await get_deuda(db, abono_in.deuda_id)
    if not deuda:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")

    # Verificar acceso al negocio
    if not await usuario_en_negocio(db, deuda.cliente.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    # Validar que el abono no exceda el saldo pendiente
    if abono_in.monto > deuda.saldo_pendiente:
        raise HTTPException(
            status_code=400,
            detail=f"El abono (${abono_in.monto}) excede el saldo pendiente (${deuda.saldo_pendiente})"
        )

    # Crear el abono
    obj = models.Abono(
        deuda_id=abono_in.deuda_id,
        monto=abono_in.monto,
        fecha=abono_in.fecha or date.today(),
        notas=abono_in.notas
    )

    # Actualizar el monto pagado de la deuda
    deuda.monto_pagado += abono_in.monto
    deuda.actualizar_estado()

    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await db.refresh(deuda)

    # Notificación por Telegram
    result = await db.execute(select(models.Usuario).where(models.Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()

    if usuario and usuario.telegram_chat_id:
        mensaje = (
            f"💰 Abono registrado por {usuario.nombre}\n\n"
            f"<b>Cliente:</b> {deuda.cliente.nombre}\n"
            f"<b>Monto abono:</b> ${abono_in.monto}\n"
            f"<b>Saldo pendiente:</b> ${deuda.saldo_pendiente}\n"
            f"<b>Estado:</b> {deuda.estado.value}"
        )
        await enviar_mensaje_telegram(usuario.telegram_chat_id, mensaje)

    return obj


async def get_abonos_by_deuda(db: AsyncSession, deuda_id: int, usuario_id: int) -> List[models.Abono]:
    deuda = await get_deuda(db, deuda_id)
    if not deuda:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")

    if not await usuario_en_negocio(db, deuda.cliente.negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    result = await db.execute(
        select(models.Abono)
        .where(models.Abono.deuda_id == deuda_id)
        .order_by(models.Abono.fecha.desc())
    )
    return result.scalars().all()


# Balance
async def get_balance(db: AsyncSession, negocio_id: int, fecha_inicio: Optional[date] = None,
                      fecha_fin: Optional[date] = None):
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


async def get_resumen_deudas(db: AsyncSession, negocio_id: int, usuario_id: int):
    """Obtiene un resumen de todas las deudas del negocio"""
    if not await usuario_en_negocio(db, negocio_id, usuario_id):
        raise HTTPException(status_code=403, detail="No autorizado para este negocio")

    # Total de deudas
    q_total = select(func.coalesce(func.sum(models.Deuda.monto_total), 0)).join(
        models.Cliente
    ).where(models.Cliente.negocio_id == negocio_id)

    # Total pendiente (monto_total - monto_pagado de deudas no saldadas)
    q_pendiente = select(
        func.coalesce(func.sum(models.Deuda.monto_total - models.Deuda.monto_pagado), 0)
    ).join(models.Cliente).where(
        models.Cliente.negocio_id == negocio_id,
        models.Deuda.estado != models.EstadoDeuda.saldado
    )

    # Total saldado
    q_saldado = select(func.coalesce(func.sum(models.Deuda.monto_total), 0)).join(
        models.Cliente
    ).where(
        models.Cliente.negocio_id == negocio_id,
        models.Deuda.estado == models.EstadoDeuda.saldado
    )

    # Cantidad de clientes con deuda pendiente
    q_clientes = select(func.count(func.distinct(models.Deuda.cliente_id))).join(
        models.Cliente
    ).where(
        models.Cliente.negocio_id == negocio_id,
        models.Deuda.estado != models.EstadoDeuda.saldado
    )

    total = (await db.execute(q_total)).scalar()
    pendiente = (await db.execute(q_pendiente)).scalar()
    saldado = (await db.execute(q_saldado)).scalar()
    clientes = (await db.execute(q_clientes)).scalar()

    return {
        "negocio_id": negocio_id,
        "total_deudas": total,
        "total_pendiente": pendiente,
        "total_saldado": saldado,
        "cantidad_clientes_con_deuda": clientes
    }


# Utilidades
async def usuario_en_negocio(db: AsyncSession, negocio_id: int, usuario_id: int) -> bool:
    result = await db.execute(
        select(models.usuarios_negocios)
        .where(
            models.usuarios_negocios.c.negocio_id == negocio_id,
            models.usuarios_negocios.c.usuario_id == usuario_id
        )
    )
    return result.first() is not None


async def agregar_usuario_a_negocio(db: AsyncSession, negocio_id: int, usuario_id: int):
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