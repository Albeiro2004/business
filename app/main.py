import os
from sys import prefix
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine
from app import models
from app.routers import auth, negocios, transacciones, user_negocios


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("ENV") == "dev":
        async with engine.begin() as conn:
            # Solo para desarrollo: crea tablas si no existen
            await conn.run_sync(models.Base.metadata.create_all)
    yield
app = FastAPI(
    title="Gestor de Negocios - Backend",
    lifespan=lifespan
)

origins = [
    "https://gestor-negocios-frontend.vercel.app",
    "http://localhost:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(negocios.router, tags=["Negocios"])
app.include_router(transacciones.router, tags=["Transacciones"])
app.include_router(user_negocios.router, tags=["Usuarios"])

@app.get("/")
async def root():
    return {"message": "API Gestor de Negocios - Up and running"}
