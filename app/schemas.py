from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

class TipoTransaccion(str, PyEnum):
    ingreso = "ingreso"
    egreso = "egreso"

class UsuarioBase(BaseModel):
    id: int
    nombre: str
    email: EmailStr

    model_config = {
        "from_attributes": True  # reemplaza a orm_mode
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

#Negocio
class NegocioBase(BaseModel):
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None

class NegocioCreate(NegocioBase):
    pass

class NegocioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] =  None

class NegocioOut(NegocioBase):
    id: int
    created_at: datetime
    usuarios: List[UsuarioOut] = []

    class Config:
        from_attributes = True

#Transaccion
class TransaccionBase(BaseModel):
    negocio_id: int
    tipo: TipoTransaccion
    monto: Decimal = Field(..., gt = 0, description = "Monto debe ser mayor a cero")
    descripcion: Optional[str] = None

class TransaccionCreate(TransaccionBase):
    pass

class TransaccionUpdate(BaseModel):
    tipo: Optional[TipoTransaccion]
    monto: Optional[Decimal]
    descripcion: Optional[str]

class TransaccionOut(TransaccionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

#Balance
class BalanceOut(BaseModel):
    negocio_id: int
    total_ingresos: Decimal
    total_egresos: Decimal
    balance: Decimal
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None