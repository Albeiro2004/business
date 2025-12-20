from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import schemas, crud
from app.models import Usuario
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UsuarioOut)
async def register(user_in: schemas.UsuarioCreate, db: AsyncSession = Depends(get_db)):
    email = user_in.email.strip().lower()
    existing = await crud.get_usuario_por_email(db, email)
    if len(user_in.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    user = Usuario(
        nombre=user_in.nombre,
        email=email,
        hashed_password=hash_password(user_in.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user.nombre, "email": user.email}
