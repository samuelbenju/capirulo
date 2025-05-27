from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import os

from models import Stock as StockDB
from schemas import Stock
from database import SessionStock
from auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# =============================================
# 🔹 API REST - Para consumo externo (JSON)
# =============================================

@router.get("/stock/{stock_id}", response_model=Stock)
async def get_stock(stock_id: int, session: AsyncSession = Depends(SessionStock)):
    result = await session.execute(select(StockDB).filter(StockDB.id == stock_id))
    stock_db = result.scalar_one_or_none()
    if stock_db is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Stock.from_orm(stock_db)

@router.get("/stock/", response_model=List[Stock])
async def get_all_stocks(session: AsyncSession = Depends(SessionStock)):
    result = await session.execute(select(StockDB))
    stocks_db = result.scalars().all()
    return [Stock.from_orm(stock_db) for stock_db in stocks_db]

# =============================================
# 🔸 Rutas para navegador (HTML y formularios)
# =============================================

@router.get("/stock/html", response_class=HTMLResponse)
async def mostrar_stock_html(
    request: Request,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(SessionStock),
    query: Optional[str] = Query(default=None)
):
    branch = user.branch if user.role != "admin" else None

    try:
        if query:
            if branch:
                stmt = select(StockDB).where(StockDB.branch == branch, StockDB.name.ilike(f"%{query}%"))
            else:
                stmt = select(StockDB).where(StockDB.name.ilike(f"%{query}%"))
        else:
            stmt = select(StockDB).where(StockDB.branch == branch) if branch else select(StockDB)

        result = await session.execute(stmt)
        productos = result.scalars().all()

        template_name = f"branch{user.branch}.html" if user.role != "admin" else "administration.html"
        if not os.path.exists(f"templates/{template_name}"):
            raise HTTPException(status_code=500, detail="Plantilla HTML no encontrada para esta sucursal")

        return templates.TemplateResponse(template_name, {
            "request": request,
            "username": user.username,
            "productos": productos
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/registrar-venta")
async def registrar_venta(
    producto: str = Form(...),
    cantidad: int = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(SessionStock)
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
    user=Depends(get_current_user)
):
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    print(f"[SOLICITUD] {user.username} ({user.branch}) solicita {cantidad} de '{producto}' a {sucursal_destino}")
    return RedirectResponse(url="/stock/html", status_code=303)

@router.get("/stock", include_in_schema=False)
async def redirect_to_stock_html():
    return RedirectResponse(url="/stock/html")
