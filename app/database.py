import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"ssl": True},
    pool_pre_ping=True,     # evita usar conexiones muertas
    pool_size=5,
    max_overflow=10
)


# Nuevo: async_sessionmaker (SQLAlchemy 2.x)
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db():
    async with async_session_maker() as session:  # <-- Fíjate en los ()
        yield session
