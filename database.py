from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Datos de la base de datos
DB_USER = "root"
DB_PASSWORD = ""  
DB_HOST = "localhost"
DB_NAME = "maquinaria"

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Motor de conexión
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
