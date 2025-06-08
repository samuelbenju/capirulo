from fastapi import HTTPException, Depends, status, Request
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.hash import bcrypt
from typing import Optional

from models import User
from database import get_session
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

#  Verifica si el password ingresado coincide con el hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)

#  Hashea un password antes de almacenarlo
def get_password_hash(password: str) -> str:
    return bcrypt.hash(password)

#  Crea un JWT válido con expiración
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#  Obtiene el usuario actual desde la cookie segura Authorization
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    token = request.cookies.get("Authorization")

    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado o mal formado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = token[7:]  # Quitar "Bearer "
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if not username:
            raise HTTPException(status_code=401, detail="Token sin usuario")

        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

#  Crea un nuevo usuario con contraseña hasheada
async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: str = "user",
    branch: Optional[str] = None
) -> User:
    hashed_password = get_password_hash(password)
    db_user = User(username=username, email=email, password_hash=hashed_password, role=role, branch=branch)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

#  Busca un usuario por username
async def get_user(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

