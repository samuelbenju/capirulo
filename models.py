from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from database import BaseSQL, BaseSQLStock

# ===========================
# Modelo de Usuarios
# ===========================
class User(BaseSQL):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100))
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    role = Column(String(20), default="user")
    branch = Column(String(50), default="soacha")

# ===========================
# Modelo de Inventario
# ===========================
class Stock(BaseSQLStock):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    branch = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

# ===========================
# Modelo de Solicitudes de Stock
# ===========================
class StockRequest(BaseSQLStock):
    __tablename__ = "stock_requests"
    id = Column(Integer, primary_key=True, index=True)
    producto = Column(String(100), nullable=False)
    cantidad = Column(Integer, nullable=False)
    sucursal_origen = Column(String(50), nullable=False)
    sucursal_destino = Column(String(50), nullable=False)
    usuario = Column(String(100), nullable=False)
    fecha = Column(DateTime, default=datetime.now(timezone.utc))
    estado = Column(String(20), default="pendiente")  # Nuevo campo
