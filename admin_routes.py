from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.hash import bcrypt

from database import get_session, get_session_stock
from models import Stock as StockDB, User as UserDB, StockRequest
from schemas import StockCreate, UserCreate
from auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def admin_dashboard(
    request: Request,
    user=Depends(get_current_user),
    session_stock: AsyncSession = Depends(get_session_stock),
    session_user: AsyncSession = Depends(get_session)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    result_stock = await session_stock.execute(select(StockDB))
    productos = result_stock.scalars().all()

    result_solicitudes = await session_stock.execute(
        select(StockRequest).order_by(StockRequest.fecha.desc())
    )
    solicitudes = result_solicitudes.scalars().all()

    return templates.TemplateResponse("administration.html", {
        "request": request,
        "username": user.username,
        "productos": productos,
        "solicitudes": solicitudes
    })

@router.post("/productos/crear")
async def crear_producto(
    name: str = Form(...),
    quantity: int = Form(...),
    branch: str = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session_stock)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    nuevo = StockDB(name=name, quantity=quantity, branch=branch)
    session.add(nuevo)
    await session.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/productos/eliminar")
async def eliminar_producto(
    id: int = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session_stock)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    result = await session.execute(select(StockDB).where(StockDB.id == id))
    producto = result.scalar_one_or_none()
    if producto:
        await session.delete(producto)
        await session.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.get("/usuarios")
async def listar_usuarios(
    request: Request,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    result = await session.execute(select(UserDB))
    usuarios = result.scalars().all()

    return templates.TemplateResponse("usuarios_admin.html", {
        "request": request,
        "username": user.username,
        "usuarios": usuarios
    })

@router.post("/usuarios/crear")
async def crear_usuario(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    branch: str = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    new_user = UserDB(
        username=username,
        email=email,
        password_hash=bcrypt.hash(password),
        role=role,
        branch=branch
    )
    session.add(new_user)
    await session.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)

@router.post("/usuarios/eliminar")
async def eliminar_usuario(
    id: int = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    result = await session.execute(select(UserDB).where(UserDB.id == id))
    usuario = result.scalar_one_or_none()
    if usuario:
        await session.delete(usuario)
        await session.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)

@router.post("/solicitudes/aprobar")
async def aprobar_solicitud(
    id: int = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session_stock)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    solicitud_result = await session.execute(select(StockRequest).where(StockRequest.id == id))
    solicitud = solicitud_result.scalar_one_or_none()
    
    if not solicitud or solicitud.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solicitud no válida o ya procesada")

    origen_result = await session.execute(select(StockDB).where(
        StockDB.name == solicitud.producto,
        StockDB.branch == solicitud.sucursal_origen
    ))
    stock_origen = origen_result.scalar_one_or_none()

    if not stock_origen or stock_origen.quantity < solicitud.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente en sucursal origen")

    stock_origen.quantity -= solicitud.cantidad

    destino_result = await session.execute(select(StockDB).where(
        StockDB.name == solicitud.producto,
        StockDB.branch == solicitud.sucursal_destino
    ))
    stock_destino = destino_result.scalar_one_or_none()

    if stock_destino:
        stock_destino.quantity += solicitud.cantidad
    else:
        nuevo = StockDB(
            name=solicitud.producto,
            quantity=solicitud.cantidad,
            branch=solicitud.sucursal_destino
        )
        session.add(nuevo)

    solicitud.estado = "aprobado"
    await session.commit()

    return RedirectResponse(url="/admin", status_code=303)
