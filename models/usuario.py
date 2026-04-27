from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "maquinaria"}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(String(20), default="tecnico")
    activo = Column(Boolean, default=True)

    email = Column(String(100), unique=True, index=True, nullable=False)
    telefono = Column(String(20), nullable=True)