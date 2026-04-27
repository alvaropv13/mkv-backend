from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioCreate(BaseModel):
    username: str
    password: str
    rol: str = "tecnico"
    email: EmailStr
    telefono: str

class UsuarioLogin(BaseModel):
    username: str
    password: str

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None

class UsuarioOut(BaseModel):
    id: int
    username: str
    activo: bool
    email: str
    telefono: str

    class Config:
        from_attributes = True

class ChangePassword(BaseModel):
    password_actual: str
    nueva_password: str