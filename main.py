from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import date
from routes import auth
from models.usuario import Usuario
from schemas.usuario import UsuarioCreate
from routes.auth import get_current_user, require_role


from database import SessionLocal, engine
from models.models import (
    Base,
    Maquina as MaquinaModel,
    Componente as ComponenteModel,
    Incidencia as IncidenciaModel,
    Venta as VentaModel,
    Importe as ImporteModel,
    Servicio as ServicioModel
)

from schemas.schemas import (
    IncidenciaEstadoUpdate, MaquinaCreate, Maquina, MaquinaList, MaquinaDetalle, MaquinaUpdate,
    ComponenteCreate, Componente,
    IncidenciaCreate, Incidencia,
    VentaCreate, Venta,
    ImporteCreate, Importe,
    ServicioCreate, Servicio
)

from fastapi.middleware.cors import CORSMiddleware

# ---------------- CREAR TABLAS ----------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API MKV Spain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

# ---------------- DEPENDENCIA DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    
def calcular_estado_maquina(maquina):
    estados = [i.estado for i in maquina.incidencias]

    if "ABIERTA" in estados:
        return "CRÍTICA"
    if "PENDIENTE" in estados:
        return "ATENCIÓN"
    return "OK"

# ---------------- ROOT & HEALTH ----------------
@app.get("/")
def root():
    return {"api": "API MKV Spain", "status": "online"}

@app.get("/health")
def health():
    return {"status": "ok", "database": "connected"}

# ============================================================
# MAQUINAS - CRUD COMPLETO CON CLIENTE
# ============================================================

@app.post("/maquinas", response_model=Maquina)
def crear_maquina(
    maquina: MaquinaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    # Extraer cliente_nombre si existe
    cliente_nombre = getattr(maquina, 'cliente_nombre', None)
    
    # Convertir a dict y eliminar cliente_nombre (no existe en la tabla)
    maquina_dict = maquina.model_dump()
    maquina_dict.pop('cliente_nombre', None)
    
    # Crear la máquina
    db_maquina = MaquinaModel(**maquina_dict)
    db.add(db_maquina)
    db.flush()  # Para obtener el id_maquina
    
    # Si hay cliente_nombre, crear una venta asociada
    if cliente_nombre:
        venta = VentaModel(
            cliente=cliente_nombre,
            fecha_entrega=None,
            entregado=False
        )
        db.add(venta)
        db.flush()
        db_maquina.id_venta = venta.id_venta
    
    db.commit()
    db.refresh(db_maquina)
    return db_maquina

@app.get("/maquinas", response_model=List[Maquina])
def listar_maquinas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(MaquinaModel).all()

# ============================================================
# ENDPOINTS DE MAQUINAS - RUTAS FIJAS (PRIMERO)
# ============================================================

@app.get("/maquinas/listado", response_model=List[MaquinaList])
def listar_maquinas_enriquecido(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquinas = db.query(MaquinaModel).options(
        joinedload(MaquinaModel.venta)
    ).all()

    resultado = []

    for m in maquinas:
        cliente_nombre = None
        fin_garantia = None

        if m.venta:
            cliente_nombre = m.venta.cliente
            fin_garantia = m.venta.fin_garantia

        # Calcular estado simple
        estado = "OK"
        if fin_garantia and fin_garantia < date.today():
            estado = "GARANTÍA VENCIDA"

        resultado.append(
            MaquinaList(
                id_maquina=m.id_maquina,
                num_serie=m.num_serie,
                fabricante=m.fabricante,
                tecnologia=m.tecnologia,
                instalacion=m.instalacion,
                latitud=m.latitud,
                longitud=m.longitud,
                cliente_nombre=cliente_nombre,
                estado=estado,
                fin_garantia=fin_garantia
            )
        )

    return resultado

@app.get("/maquinas/paginadas")
def listar_maquinas_paginadas(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(MaquinaModel)

    total = query.count()

    maquinas = query.offset((page - 1) * size).limit(size).all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "data": maquinas
    }

@app.get("/maquinas/buscar", response_model=List[Maquina])
def buscar_maquinas(
    fabricante: str | None = None,
    tecnologia: str | None = None,
    cliente: str | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(MaquinaModel).join(VentaModel, isouter=True)

    if fabricante:
        query = query.filter(MaquinaModel.fabricante == fabricante)
    if tecnologia:
        query = query.filter(MaquinaModel.tecnologia == tecnologia)
    if cliente:
        query = query.filter(VentaModel.cliente == cliente)

    return query.all()

@app.get("/maquinas/cliente/{cliente}", response_model=List[Maquina])
def maquinas_por_cliente(
    cliente: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return (
        db.query(MaquinaModel)
        .join(VentaModel)
        .filter(VentaModel.cliente == cliente)
        .all()
    )

# ============================================================
# ENDPOINTS DE MAQUINAS - RUTAS CON PARÁMETROS (DESPUÉS)
# ============================================================

@app.get("/maquinas/{id_maquina}", response_model=Maquina)
def obtener_maquina(
    id_maquina: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).filter(
        MaquinaModel.id_maquina == id_maquina
    ).first()

    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    return maquina

@app.get("/maquinas/{id_maquina}/componentes", response_model=List[Componente])
def componentes_maquina(
    id_maquina: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).filter(MaquinaModel.id_maquina == id_maquina).first()
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    return sorted(maquina.componentes, key=lambda c: c.nombre)

@app.get("/maquinas/{id_maquina}/detalle", response_model=MaquinaDetalle)
def detalle_maquina(
    id_maquina: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).options(
        joinedload(MaquinaModel.componentes),
        joinedload(MaquinaModel.incidencias),
        joinedload(MaquinaModel.venta)
    ).filter(MaquinaModel.id_maquina == id_maquina).first()

    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    cliente_nombre = maquina.venta.cliente if maquina.venta else None
    fin_garantia = maquina.venta.fin_garantia if maquina.venta else None

    return MaquinaDetalle(
        id_maquina=maquina.id_maquina,
        num_serie=maquina.num_serie,
        fabricante=maquina.fabricante,
        tecnologia=maquina.tecnologia,
        instalacion=maquina.instalacion,
        latitud=maquina.latitud,
        longitud=maquina.longitud,
        cliente_nombre=cliente_nombre,
        fin_garantia=fin_garantia,
        componentes=maquina.componentes,
        incidencias=maquina.incidencias
    )

@app.get("/maquinas/{id_maquina}/historial")
def historial_tecnico(
    id_maquina: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidencias = db.query(IncidenciaModel).filter(
        IncidenciaModel.id_maquina == id_maquina
    ).order_by(IncidenciaModel.fecha.desc()).all()

    return incidencias

# ============================================================
# ACTUALIZAR MÁQUINA - CORREGIDO (sin inicio_garantia en venta)
# ============================================================

@app.put("/maquinas/{id_maquina}")
def actualizar_maquina(
    id_maquina: int,
    datos: MaquinaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).filter(
        MaquinaModel.id_maquina == id_maquina
    ).first()

    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    # Extraer todos los campos
    datos_dict = datos.model_dump(exclude_unset=True)
    
    # Extraer campos que NO están en la tabla maquina
    cliente_nombre = datos_dict.pop('cliente_nombre', None)
    fin_garantia = datos_dict.pop('fin_garantia', None)
    inicio_garantia = datos_dict.pop('inicio_garantia', None)  # Ignorado
    dias_garantia = datos_dict.pop('dias_garantia', None)      # Ignorado
    
    # Actualizar campos de la máquina (num_serie, fabricante, tecnologia, instalacion, etc.)
    for key, value in datos_dict.items():
        setattr(maquina, key, value)

    # Gestionar la venta (solo cliente y fin_garantia)
    if maquina.id_venta:
        venta = db.query(VentaModel).filter(VentaModel.id_venta == maquina.id_venta).first()
        if venta:
            if cliente_nombre is not None:
                venta.cliente = cliente_nombre
            if fin_garantia is not None:
                venta.fin_garantia = fin_garantia
    else:
        # Si no hay venta pero hay datos de cliente o garantía, crear una
        if cliente_nombre or fin_garantia:
            venta = VentaModel(
                cliente=cliente_nombre,
                fin_garantia=fin_garantia
            )
            db.add(venta)
            db.flush()
            maquina.id_venta = venta.id_venta

    db.commit()
    db.refresh(maquina)

    return maquina

@app.delete("/maquinas/{id_maquina}")
def eliminar_maquina(
    id_maquina: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).filter(
        MaquinaModel.id_maquina == id_maquina
    ).first()

    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    db.delete(maquina)
    db.commit()

    return {"mensaje": "Máquina eliminada correctamente"}

# ============================================================
# COMPONENTES - CRUD COMPLETO
# ============================================================

@app.post("/componentes", response_model=Componente)
def crear_componente(
    componente: ComponenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).filter(MaquinaModel.id_maquina == componente.id_maquina).first()
    if not maquina:
        raise HTTPException(status_code=404, detail="La máquina no existe")

    db_componente = ComponenteModel(**componente.model_dump())
    db.add(db_componente)
    db.commit()
    db.refresh(db_componente)
    return db_componente

@app.get("/componentes", response_model=List[Componente])
def listar_componentes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(ComponenteModel).all()

@app.put("/componentes/{id_componente}", response_model=Componente)
def actualizar_componente(
    id_componente: int,
    datos: ComponenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    componente = db.query(ComponenteModel).filter(
        ComponenteModel.id_componente == id_componente
    ).first()

    if not componente:
        raise HTTPException(status_code=404, detail="Componente no encontrado")

    for key, value in datos.model_dump().items():
        setattr(componente, key, value)

    db.commit()
    db.refresh(componente)
    return componente

@app.delete("/componentes/{id_componente}")
def eliminar_componente(
    id_componente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    componente = db.query(ComponenteModel).filter(
        ComponenteModel.id_componente == id_componente
    ).first()

    if not componente:
        raise HTTPException(status_code=404, detail="Componente no encontrado")

    db.delete(componente)
    db.commit()

    return {"mensaje": "Componente eliminado correctamente"}

# ============================================================
# INCIDENCIAS - CRUD COMPLETO
# ============================================================

@app.post("/incidencias", response_model=Incidencia)
def crear_incidencia(
    incidencia: IncidenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).filter(MaquinaModel.id_maquina == incidencia.id_maquina).first()
    if not maquina:
        raise HTTPException(status_code=404, detail="La máquina no existe")

    db_incidencia = IncidenciaModel(**incidencia.model_dump())
    db.add(db_incidencia)
    db.commit()
    db.refresh(db_incidencia)
    return db_incidencia

@app.get("/incidencias", response_model=List[Incidencia])
def listar_incidencias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(IncidenciaModel).all()

@app.get("/incidencias/activas", response_model=List[Incidencia])
def incidencias_activas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return (
        db.query(IncidenciaModel)
        .filter(IncidenciaModel.estado.in_(["ABIERTA", "PENDIENTE"]))
        .all()
    )

@app.put("/incidencias/{id_incidencia}", response_model=Incidencia)
def actualizar_incidencia(
    id_incidencia: int,
    datos: IncidenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidencia = db.query(IncidenciaModel).filter(
        IncidenciaModel.id_incidencia == id_incidencia
    ).first()

    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    for key, value in datos.model_dump().items():
        setattr(incidencia, key, value)

    db.commit()
    db.refresh(incidencia)

    return incidencia

@app.patch("/incidencias/{id_incidencia}/estado", response_model=Incidencia)
def cambiar_estado_incidencia(
    id_incidencia: int,
    datos: IncidenciaEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidencia = db.query(IncidenciaModel).filter(
        IncidenciaModel.id_incidencia == id_incidencia
    ).first()

    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    incidencia.estado = datos.estado

    db.commit()
    db.refresh(incidencia)

    return incidencia

@app.delete("/incidencias/{id_incidencia}")
def eliminar_incidencia(
    id_incidencia: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    incidencia = db.query(IncidenciaModel).filter(
        IncidenciaModel.id_incidencia == id_incidencia
    ).first()

    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    db.delete(incidencia)
    db.commit()

    return {"mensaje": "Incidencia eliminada correctamente"}

# ============================================================
# VENTAS - CRUD COMPLETO
# ============================================================

@app.post("/ventas", response_model=Venta)
def crear_venta(
    venta: VentaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    db_venta = VentaModel(**venta.model_dump())
    db.add(db_venta)
    db.commit()
    db.refresh(db_venta)
    return db_venta

@app.get("/ventas", response_model=List[Venta])
def listar_ventas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(VentaModel).all()

@app.delete("/ventas/{id_venta}")
def eliminar_venta(
    id_venta: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    venta = db.query(VentaModel).filter(
        VentaModel.id_venta == id_venta
    ).first()

    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    db.delete(venta)
    db.commit()

    return {"mensaje": "Venta eliminada correctamente"}

# ============================================================
# IMPORTES - CRUD COMPLETO
# ============================================================

@app.post("/importes", response_model=Importe)
def crear_importe(
    importe: ImporteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    venta = db.query(VentaModel).filter(VentaModel.id_venta == importe.id_venta).first()
    if not venta:
        raise HTTPException(status_code=404, detail="La venta no existe")

    db_importe = ImporteModel(**importe.model_dump())
    db.add(db_importe)
    db.commit()
    db.refresh(db_importe)
    return db_importe

@app.get("/importes", response_model=List[Importe])
def listar_importes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(ImporteModel).all()

# ============================================================
# SERVICIOS - CRUD COMPLETO
# ============================================================

@app.post("/servicios", response_model=Servicio)
def crear_servicio(
    servicio: ServicioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    venta = db.query(VentaModel).filter(VentaModel.id_venta == servicio.id_venta).first()
    if not venta:
        raise HTTPException(status_code=404, detail="La venta no existe")

    db_servicio = ServicioModel(**servicio.model_dump())
    db.add(db_servicio)
    db.commit()
    db.refresh(db_servicio)
    return db_servicio

@app.get("/servicios", response_model=List[Servicio])
def listar_servicios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(ServicioModel).all()

# ============================================================
# ENDPOINTS ADICIONALES
# ============================================================

@app.get("/ventas/{id_venta}/resumen")
def resumen_venta(
    id_venta: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    venta = db.query(VentaModel).filter(VentaModel.id_venta == id_venta).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    total_servicios = sum(s.precio or 0 for s in venta.servicios)
    importe = venta.importes[0] if venta.importes else None

    return {
        "cliente": venta.cliente,
        "precio_venta": importe.precio_venta if importe else None,
        "precio_compra": importe.precio_compra if importe else None,
        "costes_servicios": total_servicios,
        "margen": (
            importe.precio_venta - importe.precio_compra - total_servicios
            if importe and importe.precio_venta and importe.precio_compra
            else None
        )
    }

@app.get("/clientes/{cliente}/resumen")
def resumen_cliente(
    cliente: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    ventas = db.query(VentaModel).filter(VentaModel.cliente == cliente).all()

    total_ventas = 0
    total_costes = 0

    for v in ventas:
        if v.importes:
            imp = v.importes[0]
            total_ventas += imp.precio_venta or 0
            total_costes += imp.precio_compra or 0

        total_costes += sum(s.precio or 0 for s in v.servicios)

    return {
        "cliente": cliente,
        "ventas": len(ventas),
        "facturacion": total_ventas,
        "costes": total_costes,
        "margen": total_ventas - total_costes
    }

@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return {
        "maquinas": db.query(MaquinaModel).count(),
        "ventas": db.query(VentaModel).count(),
        "componentes": db.query(ComponenteModel).count(),
        "incidencias_abiertas": db.query(IncidenciaModel)
            .filter(IncidenciaModel.estado == "ABIERTA")
            .count()
    }

# ============================================================
# ENDPOINT PARA ACTUALIZAR SOLO EL CLIENTE
# ============================================================

@app.patch("/maquinas/{id_maquina}/cliente")
def actualizar_cliente_maquina(
    id_maquina: int,
    cliente: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    maquina = db.query(MaquinaModel).filter(
        MaquinaModel.id_maquina == id_maquina
    ).first()

    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    if maquina.id_venta:
        venta = db.query(VentaModel).filter(VentaModel.id_venta == maquina.id_venta).first()
        if venta:
            venta.cliente = cliente
    else:
        venta = VentaModel(cliente=cliente)
        db.add(venta)
        db.flush()
        maquina.id_venta = venta.id_venta

    db.commit()
    return {"mensaje": "Cliente actualizado correctamente", "cliente": cliente}