from fastapi import FastAPI, Depends, Request, Form, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from contextlib import asynccontextmanager
import os

from admin_routes import router as admin_router
from stock_routes import router as stock_router
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_session, init_db
from auth import create_access_token, get_user, verify_password
from schemas import User as PydanticUser
from models import User

# Configuración de plantillas HTML
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

# Inicialización del ciclo de vida de la app
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏳ Inicializando aplicación...")
    try:
        await init_db()
        print("✅ Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        raise
    yield

# Instancia principal de la aplicación FastAPI
app = FastAPI(lifespan=lifespan)

# Montaje de routers
app.include_router(stock_router, prefix="")
app.include_router(admin_router, prefix="/admin")

# Ruta para obtener datos de usuario por ID
@app.get("/users/{user_id}", response_model=PydanticUser)
async def get_user_endpoint(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# Ruta de login y emisión del token JWT
@app.post("/token")
async def login_access_token(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    user = await get_user(session, username=username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    response = RedirectResponse(url="/stock/html", status_code=303)
    response.set_cookie(
        key="Authorization",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return response

# Página de inicio con el login
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try:
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo cargar login.html: {e}")

# Ruta de depuración opcional
@app.get("/debug", include_in_schema=False)
async def debug(local_kw: str = Query(default=None)):
    return {"mensaje": "Ruta debug capturó el parámetro local_kw", "local_kw": local_kw}

# Ejecución local
if __name__ == "__main__":
    import uvicorn
    print("🚀 Ejecutando en modo local...")
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
