import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Detectar si estamos en Railway (nube) o local
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("DATABASE_URL") is not None

if IS_RAILWAY:
    # En Railway: usar MySQL en Aiven (nube)
    DB_HOST = os.getenv("DB_HOST", "mysql-mkv-dashboard-alvaropv13.i.aivencloud.com")
    DB_PORT = os.getenv("DB_PORT", "16316")
    DB_USER = os.getenv("DB_USER", "avnadmin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "defaultdb")
    
    # CORREGIDO: sin ssl-mode en la URL, usamos connect_args
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print("📡 Usando MySQL en Railway (Aiven)")
    
    # Configuración SSL para Railway
    ssl_args = {
        "ssl": {
            "ssl-mode": "REQUIRED"
        }
    }
else:
    # En local: usar MySQL local
    DB_USER = "root"
    DB_PASSWORD = ""  
    DB_HOST = "localhost"
    DB_NAME = "maquinaria"
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    print("📡 Usando MySQL en local")
    ssl_args = {}

# Motor de conexión
if IS_RAILWAY:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        echo=True, 
        future=True,
        connect_args=ssl_args
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)

# Sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()