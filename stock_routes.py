from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import os

from models import Stock as StockDB, StockRequest as StockRequestDB
from schemas import Stock
from database import get_session_stock
from auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# =============================================
# 🔸 Rutas para navegador (HTML y formularios)
# =============================================

@router.get("/stock/html", response_class=HTMLResponse)
async def mostrar_stock_html(
    request: Request,
    search: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session_stock)
):
    try:
        search = search.strip() if search else None
        branch = user.branch if user.role != "admin" else None

        if search:
            stmt = select(StockDB).where(StockDB.name.ilike(f"%{search}%"))
            if branch:
                stmt = stmt.where(StockDB.branch == branch)
        else:
            stmt = select(StockDB).where(StockDB.branch == branch) if branch else select(StockDB)

        result = await session.execute(stmt)
        productos = result.scalars().all()

        solicitudes = []
        if user.role == "admin":
            result_solicitudes = await session.execute(select(StockRequestDB))
            solicitudes = result_solicitudes.scalars().all()

        template_name = f"branch{user.branch}.html" if user.role != "admin" else "administration.html"
        template_path = f"templates/{template_name}"
        if not os.path.exists(template_path):
            raise HTTPException(status_code=500, detail=f"Plantilla no encontrada: {template_name}")

        return templates.TemplateResponse(template_name, {
            "request": request,
            "username": user.username,
            "productos": productos,
            "solicitudes": solicitudes
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/registrar-venta")
async def registrar_venta(
    producto: str = Form(...),
    cantidad: int = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session_stock)
):
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    result = await session.execute(
        select(StockDB).where((StockDB.name == producto) & (StockDB.branch == user.branch))
    )
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado en tu sucursal")
    if item.quantity < cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    item.quantity -= cantidad
    session.add(item)
    await session.commit()

    return RedirectResponse(url="/stock/html", status_code=303)

@router.post("/solicitar-stock")
async def solicitar_stock(
    producto: str = Form(...),
    cantidad: int = Form(...),
    sucursal_destino: str = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session_stock)
):
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")
    if user.branch == sucursal_destino:
        raise HTTPException(status_code=400, detail="No puedes solicitar productos a tu propia sucursal")

    result = await session.execute(
        select(StockDB).where((StockDB.name == producto) & (StockDB.branch == sucursal_destino))
    )
    producto_destino = result.scalar_one_or_none()

    if producto_destino is None:
        raise HTTPException(status_code=404, detail=f"El producto '{producto}' no existe en {sucursal_destino}")

    if producto_destino.quantity < cantidad:
        raise HTTPException(status_code=400, detail=f"No hay suficiente stock en {sucursal_destino}. Solo hay {producto_destino.quantity} unidades.")

    producto_destino.quantity -= cantidad
    session.add(producto_destino)

    nueva_solicitud = StockRequestDB(
        producto=producto,
        cantidad=cantidad,
        sucursal_origen=user.branch,
        sucursal_destino=sucursal_destino,
        usuario=user.username
    )
    session.add(nueva_solicitud)

    await session.commit()

    return RedirectResponse(url="/stock/html", status_code=303)

@router.post("/admin/productos/crear")
async def crear_producto_admin(
    name: str = Form(...),
    quantity: int = Form(...),
    branch: str = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session_stock)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    nuevo_producto = StockDB(
        name=name,
        quantity=quantity,
        branch=branch
    )
    session.add(nuevo_producto)
    await session.commit()

    return RedirectResponse(url="/stock/html", status_code=303)

@router.get("/stock", include_in_schema=False)
async def redirect_to_stock_html():
    return RedirectResponse(url="/stock/html")

# =============================================
# 🔹 API REST - Para consumo externo (JSON)
# =============================================

@router.get("/stock/{stock_id}", response_model=Stock)
async def get_stock(stock_id: int, session: AsyncSession = Depends(get_session_stock)):
    result = await session.execute(select(StockDB).filter(StockDB.id == stock_id))
    stock_db = result.scalar_one_or_none()
    if stock_db is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Stock.from_orm(stock_db)

@router.get("/stock/", response_model=List[Stock])
async def get_all_stocks(session: AsyncSession = Depends(get_session_stock)):
    result = await session.execute(select(StockDB))
    stocks_db = result.scalars().all()
    return [Stock.from_orm(stock_db) for stock_db in stocks_db]
