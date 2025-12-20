from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, Boolean, Enum, Table, \
    CheckConstraint, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class TipoTransaccion(str, enum.Enum):
    ingreso = "ingreso"
    egreso = "egreso"

class EstadoDeuda(str, enum.Enum):
    pendiente = "pendiente"
    parcial = "parcial"
    saldado = "saldado"

usuarios_negocios = Table(
    "usuarios_negocios",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
          Column("negocio_id", Integer, ForeignKey("negocios.id", ondelete="CASCADE"), primary_key=True),
)

class Usuario(Base):
    __tablename__= "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(150), nullable=False)
    activo = Column(Boolean, default=True)
    telegram_chat_id = Column(String(50), nullable=True)

    negocios = relationship("Negocio", secondary=usuarios_negocios ,back_populates="usuarios")

class Negocio(Base):
    __tablename__ = "negocios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_creacion = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    usuarios = relationship("Usuario", secondary=usuarios_negocios, back_populates="negocios")

    transacciones = relationship("Transaccion", back_populates="negocio", cascade="all, delete-orphan")

    clientes = relationship("Cliente", back_populates="negocio", cascade="all, delete-orphan")

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    identidad = Column(String(50), nullable=False)
    nombre = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    negocio_id = Column(Integer, ForeignKey("negocios.id", ondelete="CASCADE"), nullable=False, index=True)

    negocio = relationship("Negocio", back_populates="clientes")
    deudas = relationship("Deuda", back_populates="cliente", cascade="all, delete-orphan")

    @hybrid_property
    def deuda_total(self):
        return sum(deuda.saldo_pendiente for deuda in self.deudas)

    __table_args__ = (
        UniqueConstraint('negocio_id', 'identidad', name='uq_cliente_identidad_negocio'),
    )

class Transaccion(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(Enum(TipoTransaccion), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    negocio = relationship("Negocio", back_populates="transacciones")
    deuda = relationship("Deuda", back_populates="transaccion", uselist=False, cascade="all, delete-orphan")

class Deuda(Base):
    __tablename__ = "deudas"
    id = Column(Integer, primary_key=True, index=True)
    transaccion_id = Column(Integer, ForeignKey("transacciones.id", ondelete="CASCADE"), nullable=False, unique=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    monto_total = Column(Numeric(12, 2), nullable=False)
    monto_pagado = Column(Numeric(12, 2), default=0, nullable=False)
    estado = Column(Enum(EstadoDeuda), default=EstadoDeuda.pendiente, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaccion = relationship("Transaccion", back_populates="deuda")
    cliente = relationship("Cliente", back_populates="deudas")
    abonos = relationship("Abono", back_populates="deuda", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('monto_pagado <= monto_total', name='check_monto_pagado_deuda'),
        CheckConstraint('monto_total > 0', name='check_monto_total_positivo'),
    )

    @hybrid_property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente de la deuda"""
        return float(self.monto_total) - float(self.monto_pagado)

    def actualizar_estado(self):
        """Actualiza el estado de la deuda basado en el monto pagado"""
        if self.monto_pagado == 0:
            self.estado = EstadoDeuda.pendiente
        elif self.monto_pagado >= self.monto_total:
            self.estado = EstadoDeuda.saldado
            self.monto_pagado = self.monto_total
        else:
            self.estado = EstadoDeuda.parcial

class Abono(Base):
    __tablename__ = "abonos"
    id = Column(Integer, primary_key=True, index=True)
    deuda_id = Column(Integer, ForeignKey("deudas.id", ondelete="CASCADE"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(Date, nullable=False)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    deuda = relationship("Deuda", back_populates="abonos")

    __table_args__ = (
        CheckConstraint('monto > 0', name='check_monto_abono_positivo'),
    )