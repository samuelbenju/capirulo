from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from base import BaseSQL, BaseSQLStock  # ✅ Importar desde base.py

class User(BaseSQL):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100))
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    role = Column(String(20), default="user")
    branch = Column(String(50), default="soacha")

class Stock(BaseSQLStock):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    branch = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
