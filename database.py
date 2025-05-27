from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from base import BaseSQL, BaseSQLStock
import os

# ✅ Validar y obtener variables del entorno (Cloud Run o .env local)
DATABASE_URL_SQL = os.environ.get("DATABASE_URL_SQL")
DATABASE_URL_SQL_STOCK = os.environ.get("DATABASE_URL_SQL_STOCK")

if not DATABASE_URL_SQL or not DATABASE_URL_SQL_STOCK:
    raise RuntimeError("❌ Las variables de entorno DATABASE_URL_SQL y DATABASE_URL_SQL_STOCK deben estar definidas.")

# ✅ Crear motores asincrónicos para SQLAlchemy con Aiomysql
engine_sql = create_async_engine(DATABASE_URL_SQL, echo=True, future=True)
engine_stock = create_async_engine(DATABASE_URL_SQL_STOCK, echo=True, future=True)

# ✅ Crear sesiones asíncronas separadas
SessionLocal = sessionmaker(bind=engine_sql, class_=AsyncSession, expire_on_commit=False)
SessionStock = sessionmaker(bind=engine_stock, class_=AsyncSession, expire_on_commit=False)

# ✅ Proveedor de sesión de usuarios
async def get_session():
    async with SessionLocal() as session:
        yield session

# ✅ Inicializar ambas bases (users y stock)
async def init_db():
    try:
        async with engine_sql.begin() as conn:
            await conn.run_sync(BaseSQL.metadata.create_all)
        async with engine_stock.begin() as conn:
            await conn.run_sync(BaseSQLStock.metadata.create_all)
        print("✅ Tablas creadas exitosamente en ambas bases.")
    except Exception as e:
        print(f"❌ Error al inicializar las bases de datos: {e}")
        raise
