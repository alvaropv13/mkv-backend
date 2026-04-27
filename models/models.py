from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from database import Base

# ------------------ VENTA ------------------
class Venta(Base):
    __tablename__ = "venta"
    # __table_args__ = {"schema": "maquinaria"}

    id_venta = Column(Integer, primary_key=True, index=True)
    cliente = Column(String(100), nullable=False)
    num_pedido_mkv = Column(String(50))
    num_pedido_proveedor = Column(String(50))
    fecha_entrega = Column(Date)
    entregado = Column(Boolean, default=False)
    fin_garantia = Column(Date)
    observaciones = Column(Text)

    # maquinas = relationship("Maquina", back_populates="venta")
    servicios = relationship("Servicio", back_populates="venta")
    importes = relationship("Importe", back_populates="venta")


# ------------------ MAQUINA ------------------
class Maquina(Base):
    __tablename__ = "maquina"
    # __table_args__ = {"schema": "maquinaria"}

    id_maquina = Column(Integer, primary_key=True, index=True)
    num_serie = Column(String(50))
    fabricante = Column(String(50))
    tecnologia = Column(String(50))
    instalacion = Column("fecha_instalacion", Date)
    fin_garantia = Column(Date, nullable=True)
    inicio_garantia = Column(Date, nullable=True)
    dias_garantia = Column(Integer, nullable=True)
    latitud = Column(Float)
    longitud = Column(Float)
    foto = Column(String(255), nullable=True)
    id_venta = Column(Integer, ForeignKey("maquinaria.venta.id_venta"))

    componentes = relationship("Componente", back_populates="maquina", cascade="all, delete-orphan")
    incidencias = relationship("Incidencia", back_populates="maquina", cascade="all, delete-orphan")
    venta = relationship("Venta", back_populates="maquinas")


# ------------------ COMPONENTE ------------------
class Componente(Base):
    __tablename__ = "componente"
    # __table_args__ = {"schema": "maquinaria"}

    id_componente = Column(Integer, primary_key=True, index=True)
    id_maquina = Column(Integer, ForeignKey("maquinaria.maquina.id_maquina"))
    nombre = Column(String(50))
    num_serie = Column(String(50))
    modelo = Column(String(100))
    tipo = Column(String(50))
    estado = Column(String(50))
    fin_garantia = Column(Date, nullable=True)
    fecha_instalacion = Column(Date, nullable=True)
    inicio_garantia = Column(Date, nullable=True)
    dias_garantia = Column(Integer, nullable=True)
    observaciones = Column(Text)

    maquina = relationship("Maquina", back_populates="componentes")
    intervenciones = relationship("Intervencion", back_populates="componente")


# ------------------ INCIDENCIA ------------------
class Incidencia(Base):
    __tablename__ = "incidencia"
    # __table_args__ = {"schema": "maquinaria"}

    id_incidencia = Column(Integer, primary_key=True, index=True)
    id_maquina = Column(Integer, ForeignKey("maquinaria.maquina.id_maquina"))
    descripcion = Column(String(255))
    fecha = Column(Date)
    estado = Column(String(50))

    maquina = relationship("Maquina", back_populates="incidencias")


# ------------------ SERVICIO ------------------
class Servicio(Base):
    __tablename__ = "servicio"
    # __table_args__ = {"schema": "maquinaria"}

    id_servicio = Column(Integer, primary_key=True, index=True)
    id_venta = Column(Integer, ForeignKey("maquinaria.venta.id_venta"))
    tipo = Column(String(50), nullable=False)
    precio = Column(DECIMAL(10,2))
    observaciones = Column(Text)

    venta = relationship("Venta", back_populates="servicios")


# ------------------ IMPORTE ------------------
class Importe(Base):
    __tablename__ = "importe"
    # __table_args__ = {"schema": "maquinaria"}

    id_importe = Column(Integer, primary_key=True, index=True)
    id_venta = Column(Integer, ForeignKey("maquinaria.venta.id_venta"))
    precio_venta = Column(DECIMAL(12,2))
    precio_compra = Column(DECIMAL(12,2))
    total = Column(DECIMAL(12,2))
    fecha_pago = Column(Date)

    venta = relationship("Venta", back_populates="importes")


# ------------------ INTERVENCION ------------------
class Intervencion(Base):
    __tablename__ = "intervencion"
    # __table_args__ = {"schema": "maquinaria"}

    id_intervencion = Column(Integer, primary_key=True, index=True)
    id_componente = Column(Integer, ForeignKey("maquinaria.componente.id_componente"))
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)

    componente = relationship("Componente", back_populates="intervenciones")