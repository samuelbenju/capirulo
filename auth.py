from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
import os
from passlib.hash import bcrypt
from database import get_session
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from typing import Optional

# OAuth2 scheme for token dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# ✅ Verifica si el password ingresado coincide con el hash
def verify_password(plain_password, hashed_password):
    return bcrypt.verify(plain_password, hashed_password)

# ✅ Hashea un password antes de almacenarlo
def get_password_hash(password: str) -> str:
    return bcrypt.hash(password)

# ✅ Crea un JWT token válido
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ Obtiene el usuario actual desde el JWT
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

# ✅ Crea un nuevo usuario y guarda el hash de su contraseña
async def create_user(session: AsyncSession, username: str, email: str, password: str, role: str = "user") -> User:
    hashed_password = get_password_hash(password)
    db_user = User(username=username, email=email, password_hash=hashed_password, role=role)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

# ✅ Busca un usuario por su username
async def get_user(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()
