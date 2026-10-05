import os
import streamlit as st
import pandas as pd
from datetime import date
import urllib.parse
import json
import base64
import io
from PIL import Image

# Importar Firebase Admin SDK para Python
import firebase_admin
from firebase_admin import credentials, firestore

# Inicialización segura de Firebase usando st.secrets (para Streamlit Cloud y GitHub) o archivo local si existiera
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

# Funciones de lectura y escritura en la Nube (Firebase Firestore)
def cargar_inventario_cloud():
    if not db: return []
    docs = db.collection("inventario").stream()
    inv = []
    for doc in docs:
        item = doc.to_dict()
        item['id_doc'] = doc.id
        inv.append(item)
    return inv

def guardar_inventario_cloud(inventario_lista):
    if not db: return
    for i, item in enumerate(inventario_lista):
        if 'id_doc' in item and item['id_doc']:
            doc_id = item['id_doc']
            item_data = {k: v for k, v in item.items() if k != 'id_doc'}
            db.collection("inventario").document(doc_id).set(item_data)
        else:
            item_data = {k: v for k, v in item.items() if k != 'id_doc'}
            ref = db.collection("inventario").add(item_data)
            item['id_doc'] = ref[1].id

def cargar_ventas_cloud():
    if not db: return []
    docs = db.collection("ventas").stream()
    v_lista = []
    for doc in docs:
        v = doc.to_dict()
        v['id_doc'] = doc.id
        v_lista.append(v)
    return sorted(v_lista, key=lambda x: x.get('id_venta', 0))

def guardar_venta_cloud(venta_reg):
    if db:
        db.collection("ventas").add(venta_reg)

def actualizar_venta_cloud(id_doc, venta_reg):
    if db:
        data_limpia = {k: v for k, v in venta_reg.items() if k != 'id_doc'}
        db.collection("ventas").document(id_doc).set(data_limpia)

def eliminar_venta_cloud(id_doc):
    if db:
        db.collection("ventas").document(id_doc).delete()

def cargar_binance_cloud():
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

# Cargar datos actuales desde Firebase
inventario = cargar_inventario_cloud()
ventas = cargar_ventas_cloud()
binance_data = cargar_binance_cloud()

# Blindaje de ventas viejas para evitar errores de claves faltantes
for v in ventas:
    if 'telefono' not in v:
        v['telefono'] = ""
    if 'cliente' not in v:
        v['cliente'] = "Cliente General"
    if 'total_venta_bcv' not in v:
        v['total_venta_bcv'] = v.get('total_venta_usdt', 0.0)

# Inicializar el carrito temporal de ventas múltiples en la sesión de Streamlit
if 'carrito_ventas' not in st.session_state:
    st.session_state.carrito_ventas = []

# Configuración de la página web
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
    st.error("⚠️ No se encontró la conexión con Firebase. Configura tus Secrets en Streamlit Cloud.")

# Barra lateral con el Logo y Navegación completa intacta
with st.sidebar:
    st.markdown("## 🔥 LUIS STORE (Cloud)")
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

st.title("🔥 LUIS STORE — Control Cloud & Ventas")
st.markdown("Administra tus prendas, tallas, stock, precios a $ a BCV, Binance y genera facturas digitales profesionales sincronizadas en la nube.")

# ---------------------------------------------------------
# 1. REGISTRAR VENTA (MULTIPRODUCTO / CARRITO)
# ---------------------------------------------------------
if menu == "🛒 Registrar Venta":
    st.subheader("🛒 Registrar Venta Multiproducto (Carrito Cloud)")
    
    if not inventario:
        st.warning("⚠️ No hay productos en el inventario de la nube. Ve primero a 'Agregar Nuevo Producto / Talla'.")
    else:
        opciones_prod = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']} | USDT: ${p['precio_usdt']} | $BCV:${p.get('precio_bcv', 0)})" for i, p in enumerate(inventario)]
        seleccion = st.selectbox("Selecciona un producto para agregar al carrito:", opciones_prod)
        idx = int(seleccion.split(":")[0].replace("ID", "").strip())
        
        producto_elegido = inventario[idx]
        
        if producto_elegido.get('foto_base64'):
            try:
                img_bytes = base64.b64decode(producto_elegido['foto_base64'])
                st.image(img_bytes, width=130, caption=f"{producto_elegido['nombre']} - Talla {producto_elegido['talla']}")
            except Exception:
                pass
        
        cantidad_a_vender = st.number_input("Cantidad:", min_value=1, max_value=max(1, producto_elegido['stock']), step=1, key="input_cant_carrito")
        
        if st.button("➕ Agregar al Carrito de Venta"):
            if producto_elegido['stock'] < cantidad_a_vender:
                st.error("❌ Stock insuficiente para agregar esa cantidad.")
            else:
                en_carrito = False
                for item in st.session_state.carrito_ventas:
                    if item['id_inventario'] == idx:
                        if (item['cantidad'] + cantidad_a_vender) > producto_elegido['stock']:
                            st.error("❌ La cantidad total en el carrito supera el stock disponible.")
                        else:
                            item['cantidad'] += cantidad_a_vender
                            st.success(f"✅ Se actualizó la cantidad de {producto_elegido['nombre']} en el carrito.")
                        en_carrito = True
                        break
                
                if not en_carrito:
                    st.session_state.carrito_ventas.append({
                        "id_inventario": idx,
                        "id_doc": producto_elegido.get('id_doc', ''),
                        "nombre": producto_elegido['nombre'],
                        "talla": producto_elegido['talla'],
                        "cantidad": cantidad_a_vender,
                        "costo_usdt": producto_elegido['costo_usdt'],
                        "envio_usdt": producto_elegido['envio_usdt'],
                        "precio_usdt": producto_elegido['precio_usdt'],
                        "precio_bcv": producto_elegido.get('precio_bcv', 0)
                    })
                    st.success(f"✅ ¡{producto_elegido['nombre']} agregado al carrito!")

        st.markdown("---")
        st.subheader("📋 Productos en el Carrito Actual")
        
        if not st.session_state.carrito_ventas:
            st.info("El carrito de compras está vacío. Agrega productos arriba.")
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
            st.markdown(f"*(Equivalente interno: ${total_usdt_carrito:.2f} USDT)*")
            
            st.markdown("---")
            cliente = st.text_input("Nombre del Cliente:", value="")
            telefono_cliente = st.text_input("Número de Teléfono / WhatsApp del Cliente (Ej: 04124543304 o +584124543304):", value="")
            
            tipo_pago = st.radio("Condición de pago para toda la compra:", ["Contado (Pagado de una vez)", "Venta por Cuotas (Pendiente)"])
            
            if not cliente.strip():
                cliente = "Cliente General"
                
            fecha_entrega = str(date.today())
            cuotas = 1
            detalle_cuotas = []
            
            if "Cuotas" in tipo_pago:
                fecha_entrega_obj = st.date_input("Fecha de Entrega del Producto:", value=date.today())
                fecha_entrega = str(fecha_entrega_obj)
                    
                cuotas = st.selectbox("Número de Cuotas:", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
                monto_por_cuota_usdt = total_usdt_carrito / cuotas

                st.markdown("📝 **Indica la fecha límite para cada cuota:**")
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
                stock_suficiente = True
                for item in st.session_state.carrito_ventas:
                    prod_inv = next((p for p in inventario if p.get('id_doc') == item['id_doc']), None)
                    if not prod_inv or prod_inv['stock'] < item['cantidad']:
                        st.error(f"❌ Stock insuficiente para {item['nombre']} (Talla {item['talla']}).")
                        stock_suficiente = False
                        break
                
                if stock_suficiente:
                    inversion_total_lote = 0
                    ganancia_total_lote = 0
                    productos_resumen_factura = []
                    
                    for item in st.session_state.carrito_ventas:
                        prod_inv = next((p for p in inventario if p.get('id_doc') == item['id_doc']), None)
                        if prod_inv:
                            prod_inv['stock'] -= item['cantidad']
                            db.collection("inventario").document(prod_inv['id_doc']).update({"stock": prod_inv['stock']})
                            
                            inv_uni = (prod_inv['costo_usdt'] + prod_inv['envio_usdt']) * item['cantidad']
                            inversion_total_lote += inv_uni
                            
                            sub_v_usdt = item['precio_usdt'] * item['cantidad']
                            ganancia_total_lote += (sub_v_usdt - inv_uni)
                            
                            productos_resumen_factura.append(f"{item['cantidad']}x {item['nombre']} (Talla {item['talla']})")

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
                            "tipo": "Entrada USDT (Venta Contado Carrito Cloud)",
                            "monto": total_usdt_carrito,
                            "descripcion": f"Venta Multiproducto Contado: {', '.join(productos_resumen_factura)}"
                        })
                        guardar_binance_cloud(binance_data)

                    venta_reg = {
                        "id_venta": len(ventas) + 1,
                        "producto": " / ".join(productos_resumen_factura),
                        "talla": "Múltiple",
                        "cantidad": sum(item['cantidad'] for item in st.session_state.carrito_ventas),
                        "total_venta_usdt": total_usdt_carrito,
                        "total_venta_bcv": total_bcv_carrito,
                        "ganancia_usdt": ganancia_total_lote,
                        "reinversion_usdt": inversion_total_lote,
                        "estado": estado,
                        "cliente": cliente,
                        "telefono": telefono_cliente.strip(),
                        "fecha_entrega": fecha_entrega,
                        "cuotas": cuotas,
                        "detalle_cuotas": detalle_cuotas,
                        "items_carrito": st.session_state.carrito_ventas.copy()
                    }
                    
                    guardar_venta_cloud(venta_reg)
                    st.session_state.carrito_ventas = []
                    
                    st.success("✅ ¡Venta multiproducto registrada y respaldada en Firebase Cloud exitosamente!")
                    
                    st.markdown("---")
                    st.markdown("### 🧾 Factura Digital Consolidada (Tómale capture y envíala por WhatsApp)")
                    
                    if telefono_cliente.strip():
                        tel_limpio = ''.join(filter(str.isdigit, telefono_cliente.strip()))
                        if not tel_limpio.startswith("58") and len(tel_limpio) == 10:
                            tel_limpio = "58" + tel_limpio
                        
                        msg_wa = f"🔥 *LUIS STORE* 🔥\nFactura N° #{venta_reg['id_venta']}\nCliente: {cliente}\nFecha: {fecha_entrega}\n\n*Detalle de compra:*\n"
                        for itm in venta_reg["items_carrito"]:
                            sub_b = itm.get('precio_bcv', 0) * itm['cantidad']
