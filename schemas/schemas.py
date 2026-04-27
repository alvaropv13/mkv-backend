from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from decimal import Decimal
from datetime import date
from typing import Optional, List


# ------------------ MAQUINA ------------------
class MaquinaBase(BaseModel):
    num_serie: str
    fabricante: str
    tecnologia: str
    instalacion: Optional[date] = None 
    cliente_nombre: Optional[str] = None
    fin_garantia: Optional[date] = None
    inicio_garantia: Optional[date] = None
    dias_garantia: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    foto: Optional[str] = None
    id_venta: Optional[int] = None

class MaquinaCreate(MaquinaBase):
    pass

class Maquina(MaquinaBase):
    id_maquina: int

    class Config:
        from_attributes = True

# ------------------ COMPONENTE ------------------
class ComponenteBase(BaseModel):
    id_maquina: int
    nombre: str
    num_serie: str
    modelo: Optional[str] = None
    tipo: Optional[str] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_instalacion: Optional[date] = None
    fin_garantia: Optional[date] = None
    inicio_garantia: Optional[date] = None
    dias_garantia: Optional[int] = None

class ComponenteCreate(ComponenteBase):
    pass

class Componente(ComponenteBase):
    id_componente: int

    class Config:
        from_attributes = True

# ------------------ INCIDENCIA ------------------
class IncidenciaBase(BaseModel):
    id_maquina: int
    descripcion: str
    fecha: Optional[date] = None
    estado: Optional[str] = None

class IncidenciaCreate(IncidenciaBase):
    pass

class Incidencia(IncidenciaBase):
    id_incidencia: int

    class Config:
        from_attributes = True

# ------------------ VENTA ------------------
class VentaBase(BaseModel):
    cliente: str
    num_pedido_mkv: Optional[str] = None
    num_pedido_proveedor: Optional[str] = None
    fecha_entrega: Optional[date] = None
    entregado: Optional[bool] = False
    fin_garantia: Optional[date] = None
    observaciones: Optional[str] = None

class VentaCreate(VentaBase):
    pass

class Venta(VentaBase):
    id_venta: int

    class Config:
        from_attributes = True

# ------------------ INTERVENCION ------------------
class IntervencionBase(BaseModel):
    id_componente: int
    fecha: date
    descripcion: str

class IntervencionCreate(IntervencionBase):
    pass

class Intervencion(IntervencionBase):
    id_intervencion: int

    class Config:
        from_attributes = True

# ------------------ IMPORTE ------------------
class ImporteBase(BaseModel):
    id_venta: int
    precio_venta: Optional[Decimal] = None
    precio_compra: Optional[Decimal] = None
    total: Optional[Decimal] = None
    fecha_pago: Optional[date] = None

class ImporteCreate(ImporteBase):
    pass

class Importe(ImporteBase):
    id_importe: int

    class Config:
        from_attributes = True

# ------------------ SERVICIO ------------------
class ServicioBase(BaseModel):
    id_venta: int
    tipo: str
    precio: Optional[Decimal] = None 
    observaciones: Optional[str] = None

class ServicioCreate(ServicioBase):
    pass

class Servicio(ServicioBase):
    id_servicio: int

    class Config:
        from_attributes = True


# ==============================
# LISTADO ENRIQUECIDO
# ==============================

class MaquinaList(BaseModel):
    id_maquina: int
    num_serie: str
    fabricante: str
    tecnologia: Optional[str]
    instalacion: Optional[date]
    latitud: Optional[float]
    longitud: Optional[float]
    cliente_nombre: Optional[str]
    estado: str
    fin_garantia: Optional[date]

    class Config:
        from_attributes = True


# ==============================
# DETALLE COMPLETO
# ==============================

class MaquinaDetalle(BaseModel):
    id_maquina: int
    num_serie: str
    fabricante: str
    tecnologia: Optional[str]
    instalacion: Optional[date]
    latitud: Optional[float]
    longitud: Optional[float]
    cliente_nombre: Optional[str]
    fin_garantia: Optional[date]

    componentes: List[Componente] = []
    incidencias: List[Incidencia] = []

    class Config:
        from_attributes = True


# ==============================
# UPDATE MAQUINA
# ==============================

class MaquinaUpdate(BaseModel):
    num_serie: Optional[str] = None
    fabricante: Optional[str] = None
    tecnologia: Optional[str] = None
    inicio_garantia: Optional[date] = None
    fin_garantia: Optional[date] = None
    dias_garantia: Optional[int] = None
    cliente_nombre: Optional[str] = None
    instalacion: Optional[date] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    foto: Optional[str] = None
    id_venta: Optional[int] = None


class IncidenciaEstadoUpdate(BaseModel):
    estado: str