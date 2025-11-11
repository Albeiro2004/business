from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine
from app import models
from app.routers import auth, negocios, transacciones


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 Se ejecuta al iniciar la app
    async with engine.begin() as conn:
        # Solo para desarrollo: crea tablas si no existen
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    # 🛑 Se ejecuta al cerrar la app (si quisieras liberar recursos)
    print("Cerrando aplicación...")

app = FastAPI(
    title="Gestor de Negocios - Backend",
    lifespan=lifespan
)

# Rutas
app.include_router(auth.router)
app.include_router(negocios.router)
app.include_router(transacciones.router)

@app.get("/")
async def root():
    return {"message": "API Gestor de Negocios - Up and running"}
