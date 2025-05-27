from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)

class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True

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
