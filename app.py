import json
import os
import streamlit as st
import pandas as pd
from datetime import date
import urllib.parse

# Archivos de datos independientes
ARCHIVO_INVENTARIO = "inventario_tallas.json"
ARCHIVO_VENTAS = "ventas_tallas.json"
ARCHIVO_BINANCE = "binance_fondos.json"
CARPETA_FOTOS = "fotos_productos"

if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

LOGO_PATH = os.path.join(CARPETA_FOTOS, "logo_luisstore.jpg")

# Inventario base con tus gorras y productos principales para que NUNCA amanezca en blanco
INVENTARIO_BASE_ESTABLE = [
    {"nombre": "Gorra MLB Black", "talla": "Única", "costo_usdt": 6.0, "envio_usdt": 1.0, "precio_usdt": 12.0, "precio_bcv": 12.0, "stock": 10, "foto": ""},
    {"nombre": "Clemont Apparel", "talla": "M", "costo_usdt": 7.0, "envio_usdt": 1.0, "precio_usdt": 15.0, "precio_bcv": 15.0, "stock": 8, "foto": ""},
    {"nombre": "Clemont Apparel", "talla": "L", "costo_usdt": 7.0, "envio_usdt": 1.0, "precio_usdt": 15.0, "precio_bcv": 15.0, "stock": 8, "foto": ""},
    {"nombre": "Fortaleza Streetwear", "talla": "M", "costo_usdt": 8.0, "envio_usdt": 1.0, "precio_usdt": 18.0, "precio_bcv": 18.0, "stock": 6, "foto": ""},
    {"nombre": "Fortaleza Streetwear", "talla": "L", "costo_usdt": 8.0, "envio_usdt": 1.0, "precio_usdt": 18.0, "precio_bcv": 18.0, "stock": 6, "foto": ""},
    {"nombre": "Gorra New York Yankees", "talla": "Única", "costo_usdt": 6.0, "envio_usdt": 1.0, "precio_usdt": 12.0, "precio_bcv": 12.0, "stock": 10, "foto": ""},
    {"nombre": "Gorra Atlanta Braves", "talla": "Única", "costo_usdt": 6.0, "envio_usdt": 1.0, "precio_usdt": 12.0, "precio_bcv": 12.0, "stock": 10, "foto": ""},
    {"nombre": "Gorra Washington Nationals", "talla": "Única", "costo_usdt": 6.0, "envio_usdt": 1.0, "precio_usdt": 12.0, "precio_bcv": 12.0, "stock": 10, "foto": ""},
    {"nombre": "Gorra Houston Astros", "talla": "Única", "costo_usdt": 6.0, "envio_usdt": 1.0, "precio_usdt": 12.0, "precio_bcv": 12.0, "stock": 10, "foto": ""},
    {"nombre": "Gorra St. Louis Cardinals", "talla": "Única", "costo_usdt": 6.0, "envio_usdt": 1.0, "precio_usdt": 12.0, "precio_bcv": 12.0, "stock": 10, "foto": ""}
]

def cargar_datos(archivo, datos_por_defecto=[]):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            try:
                contenido = json.load(f)
                if not contenido and datos_por_defecto:
                    guardar_datos(archivo, datos_por_defecto)
                    return datos_por_defecto
                return contenido
            except json.JSONDecodeError:
                guardar_datos(archivo, datos_por_defecto)
                return datos_por_defecto
    else:
        guardar_datos(archivo, datos_por_defecto)
        return datos_por_defecto

def guardar_datos(archivo, datos):
    # Guardado principal
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    
    # Copia de seguridad (Backup automático) instantánea por seguridad
    archivo_backup = archivo.replace(".json", "_backup.json")
    with open(archivo_backup, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def cargar_binance():
    if os.path.exists(ARCHIVO_BINANCE):
        with open(ARCHIVO_BINANCE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"saldo_actual": 0.0, "movimientos": []}
    return {"saldo_actual": 0.0, "movimientos": []}

def guardar_binance(datos):
    with open(ARCHIVO_BINANCE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    
    # Backup automático de Binance
    with open(ARCHIVO_BINANCE.replace(".json", "_backup.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# Configuración de la página web
st.set_page_config(page_title="LUIS STORE | Control & Ventas", layout="wide")

st.markdown("""
    <style>
        .invoice-card {
            background: #ffffff;
            color: #111111;
            padding: 35px;
            border-radius: 14px;
            border: 1px solid #d4af37;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            max-width: 520px;
            margin: auto;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        .invoice-header {
            display: flex;
            justify-content: space-between;
            border-bottom: 2px solid #d4af37;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .invoice-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            margin-bottom: 20px;
        }
        .invoice-table th {
            background-color: #f9f9f9;
            color: #b89728;
            padding: 10px;
            text-align: left;
            font-size: 13px;
            border-bottom: 1px solid #ddd;
        }
        .invoice-table td {
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 13px;
            color: #222222;
        }
    </style>
""", unsafe_allow_html=True)

# Cargar datos seguros con recuperación automática si faltan
inventario = cargar_datos(ARCHIVO_INVENTARIO, INVENTARIO_BASE_ESTABLE)
ventas = cargar_datos(ARCHIVO_VENTAS, [])
binance_data = cargar_binance()

# Blindaje para ventas
for v in ventas:
    if 'telefono' not in v:
        v['telefono'] = ""
    if 'cliente' not in v:
        v['cliente'] = "Cliente General"
    if 'total_venta_bcv' not in v:
        v['total_venta_bcv'] = v.get('total_venta_usdt', 0.0)

if 'carrito_ventas' not in st.session_state:
    st.session_state.carrito_ventas = []

# Barra lateral
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("## 🔥 LUIS STORE")
    
    st.markdown("---")
    menu = st.sidebar.selectbox("Menú Principal", [
        "🛒 Registrar Venta", 
        "📦 Módulo de Inventario (Tallas y Stock)", 
        "➕ Agregar Nuevo Producto / Talla", 
        "✏️ Editar / Eliminar / Fotos (Inventario)", 
        "📋 Cuentas por Cobrar (Cuotas)", 
        "🟡 Fondos Disponibles en Binance",
        "📊 Historial, Facturación & Finanzas"
    ])

st.title("🔥 LUIS STORE — Control de Inventario & Ventas")
st.markdown("Administra tus prendas, tallas, stock, precios a $ a BCV, Binance y genera facturas digitales profesionales.")

# ---------------------------------------------------------
# 1. REGISTRAR VENTA
# ---------------------------------------------------------
if menu == "🛒 Registrar Venta":
    st.subheader("🛒 Registrar Venta Multiproducto (Carrito)")
    
    if not inventario:
        st.warning("⚠️ No hay productos en el inventario para vender.")
    else:
        opciones_prod = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']} | USDT: ${p['precio_usdt']} | $ BCV: ${p.get('precio_bcv', 0)})" for i, p in enumerate(inventario)]
        seleccion = st.selectbox("Selecciona un producto para agregar al carrito:", opciones_prod)
        idx = int(seleccion.split(":")[0].replace("ID", "").strip())
        
        producto_elegido = inventario[idx]
        
        if producto_elegido.get('foto') and os.path.exists(producto_elegido['foto']):
            st.image(producto_elegido['foto'], width=130, caption=f"{producto_elegido['nombre']} - Talla {producto_elegido['talla']}")
        
        cantidad_a_vender = st.number_input("Cantidad:", min_value=1, max_value=max(1, producto_elegido['stock']), step=1, key="input_cant_carrito")
        
        if st.button("➕ Agregar al Carrito de Venta"):
            if producto_elegido['stock'] < cantidad_a_vender:
                st.error("❌ Stock insuficiente.")
            else:
                en_carrito = False
                for item in st.session_state.carrito_ventas:
                    if item['id_inventario'] == idx:
                        item['cantidad'] += cantidad_a_vender
                        en_carrito = True
                        break
                if not en_carrito:
                    st.session_state.carrito_ventas.append({
                        "id_inventario": idx,
                        "nombre": producto_elegido['nombre'],
                        "talla": producto_elegido['talla'],
                        "cantidad": cantidad_a_vender,
                        "costo_usdt": producto_elegido['costo_usdt'],
                        "envio_usdt": producto_elegido['envio_usdt'],
                        "precio_usdt": producto_elegido['precio_usdt'],
                        "precio_bcv": producto_elegido.get('precio_bcv', 0)
                    })
                st.success("✅ ¡Agregado al carrito!")

        st.markdown("---")
        st.subheader("📋 Productos en el Carrito Actual")
        
        if not st.session_state.carrito_ventas:
            st.info("El carrito está vacío.")
        else:
            total_usdt_carrito = 0
            total_bcv_carrito = 0
            for i, item in enumerate(st.session_state.carrito_ventas):
                sub_usdt = item['precio_usdt'] * item['cantidad']
                sub_bcv = item['precio_bcv'] * item['cantidad']
                total_usdt_carrito += sub_usdt
                total_bcv_carrito += sub_bcv
                
                col_c1, col_c2, col_c3 = st.columns([3, 2, 1])
                with col_c1:
                    st.write(f"**{item['nombre']}** (Talla: {item['talla']}) x{item['cantidad']}")
                with col_c2:
                    st.write(f"Subtotal: ${sub_bcv:.2f} a BCV")
                with col_c3:
                    if st.button("🗑️", key=f"del_cart_{i}"):
                        st.session_state.carrito_ventas.pop(i)
                        st.rerun()
            
            st.markdown(f"### 💵 **Monto Total a Pagar: ${total_bcv_carrito:.2f} a BCV**")
            
            cliente = st.text_input("Nombre del Cliente:")
            telefono_cliente = st.text_input("Teléfono / WhatsApp del Cliente:")
            tipo_pago = st.radio("Condición de pago:", ["Contado (Pagado de una vez)", "Venta por Cuotas (Pendiente)"])
            
            if not cliente.strip():
                cliente = "Cliente General"
                
            fecha_entrega = str(date.today())
            cuotas = 1
            detalle_cuotas = []
            
            if "Cuotas" in tipo_pago:
                fecha_entrega_obj = st.date_input("Fecha de Entrega:", value=date.today())
                fecha_entrega = str(fecha_entrega_obj)
                cuotas = st.selectbox("Número de Cuotas:", [1, 2, 3, 4, 5, 6, 12])
                monto_por_cuota_usdt = total_usdt_carrito / cuotas
                for c in range(1, cuotas + 1):
                    f_cuota = st.date_input(f"Fecha límite cuota #{c}:", value=date.today(), key=f"cuota_f_{c}")
                    detalle_cuotas.append({
                        "nro": c,
                        "monto_estimado": monto_por_cuota_usdt,
                        "monto_pagado": 0.0,
                        "monto_pagado_bcv": 0.0,
                        "fecha": str(f_cuota),
                        "pagada": False
                    })

            if st.button("Confirmar y Registrar Venta Total"):
                for item in st.session_state.carrito_ventas:
                    inventario[item['id_inventario']]['stock'] -= item['cantidad']

                estado = "CUOTAS (Pendiente)" if "Cuotas" in tipo_pago else "PAGADO"
                if not detalle_cuotas:
                    detalle_cuotas = [{
                        "nro": 1,
                        "monto_estimado": total_usdt_carrito,
                        "monto_pagado": total_usdt_carrito,
                        "monto_pagado_bcv": total_bcv_carrito,
                        "fecha": fecha_entrega,
                        "pagada": True
                    }]
                    binance_data["saldo_actual"] += total_usdt_carrito
                    binance_data["movimientos"].append({
                        "fecha": str(date.today()),
                        "tipo": "Entrada USDT (Venta Contado)",
                        "monto": total_usdt_carrito,
                        "descripcion": f"Venta: {cliente}"
                    })
                    guardar_binance(binance_data)

                venta_reg = {
                    "id_venta": len(ventas) + 1,
                    "producto": " / ".join([f"{i['cantidad']}x {i['nombre']}" for i in st.session_state.carrito_ventas]),
                    "talla": "Múltiple",
                    "cantidad": sum(i['cantidad'] for i in st.session_state.carrito_ventas),
                    "total_venta_usdt": total_usdt_carrito,
                    "total_venta_bcv": total_bcv_carrito,
                    "ganancia_usdt": sum((i['precio_usdt'] - (i['costo_usdt'] + i['envio_usdt'])) * i['cantidad'] for i in st.session_state.carrito_ventas),
                    "reinversion_usdt": sum((i['costo_usdt'] + i['envio_usdt']) * i['cantidad'] for i in st.session_state.carrito_ventas),
                    "estado": estado,
                    "cliente": cliente,
                    "telefono": telefono_cliente.strip(),
                    "fecha_entrega": fecha_entrega,
                    "cuotas": cuotas,
                    "detalle_cuotas": detalle_cuotas,
                    "items_carrito": st.session_state.carrito_ventas.copy()
                }
                
                ventas.append(venta_reg)
                guardar_datos(ARCHIVO_INVENTARIO, inventario)
                guardar_datos(ARCHIVO_VENTAS, ventas)
                st.session_state.carrito_ventas = []
                st.success("✅ ¡Venta registrada y respaldada con éxito!")
                st.rerun()

# ---------------------------------------------------------
# 2. MÓDULO DE INVENTARIO
# ---------------------------------------------------------
elif menu == "📦 Módulo de Inventario (Tallas y Stock)":
    st.subheader("📦 Inventario General")
    for i, p in enumerate(inventario):
        st.markdown(f"**ID {i}:** {p['nombre']} (Talla: {p['talla']}) — Stock: **{p['stock']}** — Precio: **${p.get('precio_bcv', 0):.2f} BCV**")

# ---------------------------------------------------------
# 3. AGREGAR NUEVO PRODUCTO
# ---------------------------------------------------------
elif menu == "➕ Agregar Nuevo Producto / Talla":
    st.subheader("➕ Agregar Nuevo Producto")
    with st.form("form_prod"):
        nombre = st.text_input("Nombre de la prenda:")
        talla = st.selectbox("Talla:", ["Única", "S", "M", "L", "XL", "XXL"])
        costo = st.number_input("Costo USDT:", min_value=0.0, step=0.5)
        envio = st.number_input("Envío USDT:", min_value=0.0, step=0.1)
        ref_usdt = st.number_input("Precio Ref USDT:", min_value=0.0, step=0.5)
        precio_bcv = st.number_input("Precio Venta ($ a BCV):", min_value=0.0, step=0.5)
        stock = st.number_input("Stock inicial:", min_value=0, value=5)
        
        if st.form_submit_button("Guardar en el Inventario"):
            inventario.append({
                "nombre": nombre.strip(),
                "talla": talla,
                "costo_usdt": costo,
                "envio_usdt": envio,
                "precio_usdt": ref_usdt,
                "precio_bcv": precio_bcv,
                "stock": int(stock),
                "foto": ""
            })
            guardar_datos(ARCHIVO_INVENTARIO, inventario)
            st.success("✅ ¡Producto guardado y respaldado!")

# ---------------------------------------------------------
# 4. EDITAR / ELIMINAR
# ---------------------------------------------------------
elif menu == "✏️ Editar / Eliminar / Fotos (Inventario)":
    st.subheader("✏️ Gestionar Inventario")
    if inventario:
        opciones = [f"ID {i}: {p['nombre']} ({p['talla']}) - Stock: {p['stock']}" for i, p in enumerate(inventario)]
        sel = st.selectbox("Selecciona:", opciones)
        idx = int(sel.split(":")[0].replace("ID", "").strip())
        p = inventario[idx]
        
        with st.form("edit"):
            nn = st.text_input("Nombre:", value=p['nombre'])
            ns = st.number_input("Stock:", value=int(p['stock']), min_value=0)
            npb = st.number_input("Precio BCV:", value=float(p.get('precio_bcv', 0)), min_value=0.0)
            if st.form_submit_button("Actualizar"):
                inventario[idx]['nombre'] = nn
                inventario[idx]['stock'] = ns
                inventario[idx]['precio_bcv'] = npb
                guardar_datos(ARCHIVO_INVENTARIO, inventario)
                st.success("✅ ¡Actualizado!")
                st.rerun()

# ---------------------------------------------------------
# 5. BINANCE
# ---------------------------------------------------------
elif menu == "🟡 Fondos Disponibles en Binance":
    st.subheader("🟡 Fondos en Binance")
    st.metric("Saldo Actual", f"${binance_data.get('saldo_actual', 0.0):,.2f} USDT")
    movs = binance_data.get("movimientos", [])
    if movs:
        st.dataframe(pd.DataFrame(movs))

# ---------------------------------------------------------
# 6. CUENTAS POR COBRAR
# ---------------------------------------------------------
elif menu == "📋 Cuentas por Cobrar (Cuotas)":
    st.subheader("📋 Cuentas por Cobrar")
    pendientes = [v for v in ventas if v.get("estado") == "CUOTAS (Pendiente)"]
    if not pendientes:
        st.success("🎉 No hay cuotas pendientes.")
    else:
        for v in pendientes:
            st.write(f"Venta #{v['id_venta']} — Cliente: {v['cliente']} — Total: ${v['total_venta_bcv']:.2f} BCV")

# ---------------------------------------------------------
# 7. HISTORIAL Y FINANZAS
# ---------------------------------------------------------
elif menu == "📊 Historial, Facturación & Finanzas":
    st.subheader("📊 Historial General")
    if ventas:
        st.dataframe(pd.DataFrame(ventas)[['id_venta', 'cliente', 'producto', 'total_venta_bcv', 'estado', 'fecha_entrega']])
    else:
        st.info("No hay ventas registradas.")
