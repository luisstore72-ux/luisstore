import streamlit as st
import pandas as pd
from datetime import date
import urllib.parse
import os
import json

# Importar Firebase Admin SDK para Python
import firebase_admin
from firebase_admin import credentials, firestore

# Configuración de carpetas locales para fotos (si usas la app en PC o localmente)
CARPETA_FOTOS = "fotos_productos"
if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)
LOGO_PATH = os.path.join(CARPETA_FOTOS, "logo_luisstore.jpg")

# Inicialización segura de Firebase usando st.secrets (para Streamlit Cloud y GitHub) o archivo local
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif os.path.exists("firebase_key.json"):
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Error al inicializar Firebase: {e}")

db = firestore.client() if firebase_admin._apps else None

st.set_page_config(page_title="LUIS STORE | Control & Ventas Cloud", layout="wide")

# Estilos CSS con diseño de factura elegante
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

if not db:
    st.error("⚠️ No se encontró la conexión con Firebase. Configura tus Secrets en Streamlit Cloud o coloca tu 'firebase_key.json'.")

# Funciones de lectura y escritura en Firestore
def obtener_inventario():
    if not db: return []
    docs = db.collection("inventario").stream()
    inventario = []
    for doc in docs:
        item = doc.to_dict()
        item['id_doc'] = doc.id
        inventario.append(item)
    return inventario

def obtener_ventas():
    if not db: return []
    docs = db.collection("ventas").stream()
    ventas = []
    for doc in docs:
        v = doc.to_dict()
        v['id_doc'] = doc.id
        ventas.append(v)
    return sorted(ventas, key=lambda x: x.get('id_venta', 0))

def obtener_binance():
    if not db: return {"saldo_actual": 0.0, "movimientos": []}
    doc_ref = db.collection("binance").document("fondos")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        datos_iniciales = {"saldo_actual": 0.0, "movimientos": []}
        doc_ref.set(datos_iniciales)
        return datos_iniciales

def guardar_binance_cloud(datos):
    if db:
        db.collection("binance").document("fondos").set(datos)

# Cargar datos desde la nube
inventario = obtener_inventario()
ventas = obtener_ventas()
binance_data = obtener_binance()

if 'carrito_ventas' not in st.session_state:
    st.session_state.carrito_ventas = []

# Barra lateral de navegación
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("## 🔥 LUIS STORE (Cloud)")
    
    st.markdown("---")
    menu = st.sidebar.selectbox("Menú Principal", [
        "🛒 Registrar Venta", 
        "📦 Módulo de Inventario (Tallas y Stock)", 
        "➕ Agregar Nuevo Producto / Talla", 
        "📋 Cuentas por Cobrar (Cuotas)", 
        "🟡 Fondos Disponibles en Binance",
        "📊 Historial, Facturación & Finanzas"
    ])

st.title("🔥 LUIS STORE — Control Cloud (Firebase)")
st.markdown("Inventario, ventas, abonos y Binance sincronizados en la nube en tiempo real.")

# ---------------------------------------------------------
# 1. REGISTRAR VENTA
# ---------------------------------------------------------
if menu == "🛒 Registrar Venta":
    st.subheader("🛒 Registrar Venta Multiproducto (Carrito Cloud)")
    
    if not inventario:
        st.warning("⚠️ No hay productos en la nube. Agrega uno nuevo en el menú lateral.")
    else:
        opciones_prod = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']} | USDT: ${p['precio_usdt']} | $ BCV: ${p.get('precio_bcv', 0)})" for i, p in enumerate(inventario)]
        seleccion = st.selectbox("Selecciona un producto para agregar al carrito:", opciones_prod)
        idx = int(seleccion.split(":")[0].replace("ID", "").strip())
        
        producto_elegido = inventario[idx]
        cantidad_a_vender = st.number_input("Cantidad:", min_value=1, max_value=max(1, producto_elegido['stock']), step=1, key="input_cant_carrito")
        
        if st.button("➕ Agregar al Carrito de Venta"):
            if producto_elegido['stock'] < cantidad_a_vender:
                st.error("❌ Stock insuficiente.")
            else:
                en_carrito = False
                for item in st.session_state.carrito_ventas:
                    if item['id_doc'] == producto_elegido['id_doc']:
                        item['cantidad'] += cantidad_a_vender
                        en_carrito = True
                        break
                if not en_carrito:
                    st.session_state.carrito_ventas.append({
                        "id_doc": producto_elegido['id_doc'],
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
            total_usdt_carrito = sum(i['precio_usdt'] * i['cantidad'] for i in st.session_state.carrito_ventas)
            total_bcv_carrito = sum(i['precio_bcv'] * i['cantidad'] for i in st.session_state.carrito_ventas)
            
            for i, item in enumerate(st.session_state.carrito_ventas):
                col_c1, col_c2, col_c3 = st.columns([3, 2, 1])
                with col_c1:
                    st.write(f"**{item['nombre']}** (Talla: {item['talla']}) x{item['cantidad']}")
                with col_c2:
                    st.write(f"Subtotal: ${(item['precio_bcv']*item['cantidad']):.2f} BCV")
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

            if st.button("Confirmar y Registrar Venta Cloud"):
                # Actualizar stock restando en la colección inventario de Firebase
                for item in st.session_state.carrito_ventas:
                    for p in inventario:
                        if p['id_doc'] == item['id_doc']:
                            nuevo_stock = p['stock'] - item['cantidad']
                            db.collection("inventario").document(p['id_doc']).update({"stock": nuevo_stock})

                estado = "CUOTAS (Pendiente)" if "Cuotas" in tipo_pago else "PAGADO"
                nuevo_id_venta = len(ventas) + 1
                
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
                        "tipo": "Entrada USDT (Venta Contado Cloud)",
                        "monto": total_usdt_carrito,
                        "descripcion": f"Venta #{nuevo_id_venta} - {cliente}"
                    })
                    guardar_binance_cloud(binance_data)

                productos_resumen = [f"{i['cantidad']}x {i['nombre']} (Talla {i['talla']})" for i in st.session_state.carrito_ventas]
                
                venta_reg = {
                    "id_venta": nuevo_id_venta,
                    "producto": " / ".join(productos_resumen),
                    "cantidad": sum(i['cantidad'] for i in st.session_state.carrito_ventas),
                    "total_venta_usdt": total_usdt_carrito,
                    "total_venta_bcv": total_bcv_carrito,
                    "ganancia_usdt": sum((i['precio_usdt'] - (i['costo_usdt'] + i['envio_usdt'])) * i['cantidad'] for i in st.session_state.carrito_ventas),
                    "estado": estado,
                    "cliente": cliente,
                    "telefono": telefono_cliente.strip(),
                    "fecha_entrega": fecha_entrega,
                    "cuotas": cuotas,
                    "detalle_cuotas": detalle_cuotas,
                    "items_carrito": st.session_state.carrito_ventas.copy()
                }
                
                db.collection("ventas").add(venta_reg)
                st.session_state.carrito_ventas = []
                st.success("✅ ¡Venta registrada y respaldada en Firebase Cloud con éxito!")
                st.rerun()

# ---------------------------------------------------------
# 2. MÓDULO DE INVENTARIO
# ---------------------------------------------------------
elif menu == "📦 Módulo de Inventario (Tallas y Stock)":
    st.subheader("📦 Inventario General en la Nube")
    if not inventario:
        st.info("No hay productos registrados en Firebase.")
    else:
        for p in inventario:
            st.markdown(f"**Prenda:** {p['nombre']} (Talla: {p['talla']}) — Stock: **{p['stock']}** — Precio: **${p.get('precio_bcv', 0):.2f} BCV**")

# ---------------------------------------------------------
# 3. AGREGAR NUEVO PRODUCTO
# ---------------------------------------------------------
elif menu == "➕ Agregar Nuevo Producto / Talla":
    st.subheader("➕ Agregar Producto a Firebase Cloud")
    with st.form("form_cloud_prod"):
        nombre = st.text_input("Nombre de la prenda:")
        talla = st.selectbox("Talla:", ["Única", "S", "M", "L", "XL", "XXL"])
        costo = st.number_input("Costo USDT:", min_value=0.0, step=0.5)
        envio = st.number_input("Envío USDT:", min_value=0.0, step=0.1)
        ref_usdt = st.number_input("Precio Ref USDT:", min_value=0.0, step=0.5)
        precio_bcv = st.number_input("Precio Venta ($ a BCV):", min_value=0.0, step=0.5)
        stock = st.number_input("Stock inicial:", min_value=0, value=5)
        
        if st.form_submit_button("Guardar en Firebase 🚀"):
            nuevo_prod = {
                "nombre": nombre.strip(),
                "talla": talla,
                "costo_usdt": costo,
                "envio_usdt": envio,
                "precio_usdt": ref_usdt,
                "precio_bcv": precio_bcv,
                "stock": int(stock),
                "foto": ""
            }
            db.collection("inventario").add(nuevo_prod)
            st.success("✅ ¡Producto guardado de forma permanente en Firebase!")
            st.rerun()

# ---------------------------------------------------------
# 4. CUENTAS POR COBRAR (CUOTAS)
# ---------------------------------------------------------
elif menu == "📋 Cuentas por Cobrar (Cuotas)":
    st.subheader("📋 Cuentas Pendientes por Cobrar (Cloud)")
    pendientes = [v for v in ventas if v.get("estado") == "CUOTAS (Pendiente)"]
    if not pendientes:
        st.success("🎉 No hay cuotas pendientes en la nube.")
    else:
        for v in pendientes:
            st.write(f"Venta #{v['id_venta']} — Cliente: {v['cliente']} — Total: ${v['total_venta_bcv']:.2f} BCV")

# ---------------------------------------------------------
# 5. BINANCE
# ---------------------------------------------------------
elif menu == "🟡 Fondos Disponibles en Binance":
    st.subheader("🟡 Control de Binance en la Nube")
    saldo_actual = binance_data.get("saldo_actual", 0.0)
    st.metric("Saldo Actual", f"${saldo_actual:,.2f} USDT")
    movs = binance_data.get("movimientos", [])
    if movs:
        st.dataframe(pd.DataFrame(movs))

# ---------------------------------------------------------
# 6. HISTORIAL Y FINANZAS
# ---------------------------------------------------------
elif menu == "📊 Historial, Facturación & Finanzas":
    st.subheader("📊 Historial General Cloud")
    if ventas:
        st.dataframe(pd.DataFrame(ventas)[['id_venta', 'cliente', 'producto', 'total_venta_bcv', 'estado', 'fecha_entrega']])
    else:
        st.info("No hay ventas registradas en Firebase todavía.")
