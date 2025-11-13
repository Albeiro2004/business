import os
from datetime import datetime, timedelta
from jose import JWTError, jwt  # Librería para manejar JSON Web Tokens (JWT)
from passlib.context import CryptContext  # Librería para el hashing de contraseñas
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dotenv import load_dotenv

from app.database import get_db
from app.models import Usuario

load_dotenv()

# --- Constantes de Seguridad ---
SECRET_KEY = os.getenv("SECRET_KEY")  # Clave secreta para firmar tokens
ALGORITHM = "HS256"  # Algoritmo de firma para JWT (HMAC con SHA-256)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Contexto para el manejo de contraseñas (usa bcrypt por seguridad)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Esquema para obtener el token de las cabeceras de la solicitud (Bearer)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- Funciones de Hashing de Contraseña ---
def hash_password(password: str) -> str:
    """Aplica hashing a una contraseña de texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña de texto plano contra el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

def very_secret_key():
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY not defined")

# --- Función de JWT ---
def create_access_token(data: dict, expire_delta: timedelta = None):
    """Crea un nuevo Token de Acceso JWT con la carga útil (payload) dada."""
    to_encode = data.copy()

    # Calcula el tiempo de expiración
    expire = datetime.utcnow() + (expire_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    # Codifica y firma el token usando la clave secreta y el algoritmo
    very_secret_key()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- Función de Dependencia (Autenticación) ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Usuario:
    """
    Función de dependencia de FastAPI que decodifica y valida el JWT,
    y luego busca el usuario asociado en la base de datos.
    """
    # Excepción estándar para credenciales inválidas
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:

        very_secret_key()

        # Decodifica el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        # Captura errores de JWT (firma inválida, expiración, etc.)
        raise credentials_exception

    # Busca el usuario en la base de datos usando el ID
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user  # Devuelve el objeto Usuario autenticado