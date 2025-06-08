from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Declaración de los Base
BaseSQL = declarative_base()
BaseSQLStock = declarative_base()

# Obtener URLs de conexión desde entorno
DATABASE_URL_SQL = os.environ.get("DATABASE_URL_SQL")
DATABASE_URL_SQL_STOCK = os.environ.get("DATABASE_URL_SQL_STOCK")

if not DATABASE_URL_SQL or not DATABASE_URL_SQL_STOCK:
    raise RuntimeError("DATABASE_URL_SQL y DATABASE_URL_SQL_STOCK deben definirse.")

# Crear motores de base de datos
engine_sql = create_async_engine(DATABASE_URL_SQL, echo=True, future=True)
engine_stock = create_async_engine(DATABASE_URL_SQL_STOCK, echo=True, future=True)

# Crear sessionmakers
SessionLocal = sessionmaker(bind=engine_sql, class_=AsyncSession, expire_on_commit=False)
SessionLocalStock = sessionmaker(bind=engine_stock, class_=AsyncSession, expire_on_commit=False)

# Dependencia para usuarios
async def get_session():
    async with SessionLocal() as session:
        yield session

# Dependencia para inventario
async def get_session_stock():
    async with SessionLocalStock() as session:
        yield session

# Inicialización de las bases de datos
async def init_db():
    async with engine_sql.begin() as conn:
        await conn.run_sync(BaseSQL.metadata.create_all)
    async with engine_stock.begin() as conn:
        await conn.run_sync(BaseSQLStock.metadata.create_all)
    print("Bases inicializadas exitosamente.")
