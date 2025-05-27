import os
#from dotenv import load_dotenv

# Cargar variables de entorno desde .env en local
#load_dotenv()

# Variables para autenticación y seguridad
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Verificación mínima
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set. Define it in .env or Cloud Run environment variables.")
