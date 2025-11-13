import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import ssl

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

ssl_context = ssl.create_default_context()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"ssl": ssl_context}
)

# Crea una clase factoría (constructor) para generar sesiones asíncronas.
# - engine: El motor asíncrono que manejará las conexiones.
# - class_=AsyncSession: Indica que las sesiones generadas serán asíncronas.
# - expire_on_commit=False: Evita que los objetos ORM expiren tras un commit.
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """
    Proporciona una sesión de base de datos asíncrona para ser inyectada
    como dependencia (típicamente en FastAPI o frameworks similares).

    La estructura 'async with' garantiza que la sesión se cierre
    correctamente después de su uso (commit o rollback).
    """
    async with AsyncSessionLocal() as session:
        # 'yield' entrega la sesión al llamador.
        yield session

# Ejemplo de uso:
# @router.get("/items")
# async def read_items(db: AsyncSession = Depends(get_db)):
#     ...