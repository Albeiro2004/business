from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

class TipoTransaccion(str, PyEnum):
    ingreso = "ingreso"
    egreso = "egreso"

class EstadoDeuda(str, PyEnum):
    pendiente = "pendiente"
    parcial = "parcial"
    saldado = "saldado"

# Usuario
class UsuarioBase(BaseModel):
    id: int
    nombre: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }

class UsuarioShema(UsuarioBase):
    pass

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioOut(UsuarioBase):
    id: int
    activo: bool

    class Config:
        from_attributes = True

# Negocio
class NegocioBase(BaseModel):
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None

class NegocioCreate(NegocioBase):
    pass

class NegocioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class NegocioOut(NegocioBase):
    id: int
    created_at: datetime
    usuarios: List[UsuarioOut] = []

    class Config:
        from_attributes = True

class NegocioCreateOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True

# Cliente
class ClienteBase(BaseModel):
    identidad: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=200)

class ClienteCreate(ClienteBase):
    negocio_id: int

class ClienteUpdate(BaseModel):
    identidad: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, max_length=200)

class ClienteOut(ClienteBase):
    id: int
    negocio_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Transacción
class TransaccionBase(BaseModel):
    negocio_id: int
    tipo: TipoTransaccion
    monto: Decimal = Field(..., gt=0, description="Monto debe ser mayor a cero")
    descripcion: Optional[str] = None

class TransaccionCreate(TransaccionBase):
    pass

class TransaccionUpdate(BaseModel):
    tipo: Optional[TipoTransaccion]
    monto: Optional[Decimal]
    descripcion: Optional[str]

class TransaccionOut(TransaccionBase):
    id: int
    fecha: date
    created_at: datetime

    class Config:
        from_attributes = True

# Deuda
class DeudaBase(BaseModel):
    monto_total: Decimal = Field(..., gt=0)

class DeudaCreate(DeudaBase):
    transaccion_id: int
    cliente_id: int

class DeudaUpdate(BaseModel):
    estado: Optional[EstadoDeuda] = None

class DeudaOut(DeudaBase):
    id: int
    transaccion_id: int
    cliente_id: int
    monto_pagado: Decimal
    saldo_pendiente: Decimal
    estado: EstadoDeuda
    created_at: datetime

    class Config:
        from_attributes = True

class DeudaDetalle(DeudaOut):
    """Deuda con información de cliente y transacción"""
    cliente: ClienteOut
    transaccion: TransaccionOut

    class Config:
        from_attributes = True

# Abono
class AbonoBase(BaseModel):
    monto: Decimal = Field(..., gt=0, description="Monto debe ser mayor a cero")
    notas: Optional[str] = None

class AbonoCreate(AbonoBase):
    deuda_id: int
    fecha: Optional[date] = None  # Si no se envía, se usa la fecha actual

class AbonoOut(AbonoBase):
    id: int
    deuda_id: int
    fecha: date
    created_at: datetime

    class Config:
        from_attributes = True

# Balance
class BalanceOut(BaseModel):
    negocio_id: int
    total_ingresos: Decimal
    total_egresos: Decimal
    balance: Decimal
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

# Resumen de Deudas por Negocio
class ResumenDeudasOut(BaseModel):
    negocio_id: int
    total_deudas: Decimal
    total_pendiente: Decimal
    total_saldado: Decimal
    cantidad_clientes_con_deuda: int