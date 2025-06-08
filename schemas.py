from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


# =======================
# 🔹 Usuario
# =======================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "user"
    branch: Optional[str] = "soacha"

class User(BaseModel):
    id: int
    username: str
    email: str
    role: str
    branch: str
    created_at: datetime

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str]
    branch: Optional[str]


# =======================
# 🔹 Inventario (Stock)
# =======================

class StockCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    quantity: int = Field(..., ge=0)
    branch: str

class Stock(BaseModel):
    id: int
    name: str
    quantity: int
    branch: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class StockUpdate(BaseModel):
    name: Optional[str]
    quantity: Optional[int] = Field(None, ge=0)
    branch: Optional[str]


# =======================
# 🔹 Solicitud de Stock entre sucursales
# =======================

class StockRequestCreate(BaseModel):
    producto: str = Field(..., min_length=2)
    cantidad: int = Field(..., ge=1)
    sucursal_origen: str
    sucursal_destino: str
    usuario: str

class StockRequest(BaseModel):
    id: int
    producto: str
    cantidad: int
    sucursal_origen: str
    sucursal_destino: str
    usuario: str
    fecha: datetime

    class Config:
        orm_mode = True
