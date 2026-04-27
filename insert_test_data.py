from datetime import date, timedelta
from database import SessionLocal
from models.models import Maquina, Componente, Incidencia, Venta, Importe, Servicio, Intervencion

db = SessionLocal()

try:
    # 0. LIMPIEZA TOTAL (Orden inverso para evitar conflictos de Claves Foráneas)
    db.query(Intervencion).delete()
    db.query(Incidencia).delete()
    db.query(Componente).delete()
    db.query(Maquina).delete()
    db.query(Servicio).delete()
    db.query(Importe).delete()
    db.query(Venta).delete()
    db.commit()

    # 1. TABLA: venta
    # Nota: fin_garantia debe ser un objeto date o None
    v1 = Venta(id_venta=1, cliente="GRANADA LUZAUSE", num_pedido_mkv="1-000002", num_pedido_proveedor="HSG20230628ZM01", fecha_entrega=date(2024, 4, 2), entregado=True, fin_garantia=date(2026, 4, 2))
    v2 = Venta(id_venta=2, cliente="LUGER", num_pedido_mkv="1-000255", num_pedido_proveedor="HSG20231205ZM01", fecha_entrega=date(2024, 5, 24), entregado=True)
    v4 = Venta(id_venta=4, cliente="CROMADOS", num_pedido_mkv="23-1-000369", num_pedido_proveedor="HSG20231229ZM01", fecha_entrega=date(2024, 5, 14), entregado=True, fin_garantia=date(2027, 5, 14))
    v6 = Venta(id_venta=6, cliente="CORMETAL", num_pedido_mkv="24-1-000086", num_pedido_proveedor="HSG20240219ZM01", fecha_entrega=date(2024, 9, 6), entregado=True)
    
    db.add_all([v1, v2, v4, v6])
    db.commit()

    # 2. TABLA: importe
    db.add_all([
        Importe(id_venta=1, precio_venta=185000.00, precio_compra=145289.41, total=185000.00),
        Importe(id_venta=2, precio_venta=219500.00, precio_compra=162287.68, total=219500.00),
        Importe(id_venta=4, precio_venta=262000.00, precio_compra=209836.30, total=262000.00),
        Importe(id_venta=6, precio_venta=260000.00, precio_compra=162800.00, total=260000.00)
    ])

    # 3. TABLA: servicio (Desglose de costes)
    db.add_all([
        Servicio(id_venta=1, tipo="TRANSPORTE", precio=3220.00, observaciones="COTRANSA"),
        Servicio(id_venta=1, tipo="SEGURO", precio=105.50),
        Servicio(id_venta=2, tipo="COMISION", precio=5000.00, observaciones="Agente externo"),
        Servicio(id_venta=4, tipo="TRANSPORTE", precio=33950.00, observaciones="Especial pesado")
    ])

    # 4. TABLA: maquina 
    # USAMOS 'instalacion' porque así se llama la variable en tu clase Maquina
    m1 = Maquina(id_maquina=1, num_serie="11022308162", fabricante="HSG", tecnologia="Fibra Laser", id_venta=1, instalacion=date(2022, 9, 22))
    m2 = Maquina(id_maquina=2, num_serie="11022312201", fabricante="HSG", tecnologia="Fibra Laser", id_venta=2)
    m4 = Maquina(id_maquina=4, num_serie="11022401293", fabricante="HSG", tecnologia="Fibra Laser", id_venta=4)
    m6 = Maquina(id_maquina=6, num_serie="1201240178", fabricante="HSG", tecnologia="Fibra Laser", id_venta=6)
    
    db.add_all([m1, m2, m4, m6])
    db.commit()

    # 5. TABLA: componente
    c_compresor = Componente(id_maquina=2, nombre="COMPRESOR", modelo="AIRECOCUT 50/16", num_serie="OP2024012617", tipo="Neumática", estado="OK")
    db.add(c_compresor)
    db.add_all([
        Componente(id_maquina=1, nombre="RESONADOR", modelo="RLF-C12000S", num_serie="60001514", tipo="Láser"),
        Componente(id_maquina=4, nombre="ASPIRADOR", modelo="SIDEROS ECO12", num_serie="563/24", tipo="Extracción"),
        Componente(id_maquina=6, nombre="CABEZAL", modelo="Precitec", num_serie="SN-99882", tipo="Óptica")
    ])
    db.commit()

    # 6. TABLA: intervencion
    db.add(Intervencion(id_componente=c_compresor.id_componente, fecha=date(2025, 9, 30), descripcion="Sustitución completa por fallo en motor"))

    # 7. TABLA: incidencia
    db.add_all([
        Incidencia(id_maquina=4, descripcion="Falta cable de monitorización", fecha=date(2024, 5, 14), estado="ABIERTA"),
        Incidencia(id_maquina=6, descripcion="Pendiente de formación al cliente", fecha=date(2024, 9, 7), estado="PENDIENTE")
    ])

    db.commit()
    print("Base de datos actualizada con éxito: 7 tablas cargadas.")

except Exception as e:
    db.rollback()
    print(f"Error detectado: {e}")
finally:
    db.close()