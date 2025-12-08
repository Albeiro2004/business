from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, Boolean, Enum, Table
from sqlalchemy.orm import relationship, declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class TipoTransaccion(str, enum.Enum):
    ingreso = "ingreso"
    egreso = "egreso"

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