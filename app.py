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
        opciones_prod = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']} | USDT: ${p['precio_usdt']} | $ BCV: ${p.get('precio_bcv', 0)})" for i, p in enumerate(inventario)]
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
                            msg_wa += f"• {itm['cantidad']}x {itm['nombre']} (Talla {itm['talla']}) - ${sub_b:.2f} BCV\n"
                        msg_wa += f"\n*Condición:* {estado}\n*TOTAL A PAGAR:* ${total_bcv_carrito:.2f} a BCV\n\n¡Gracias por tu compra en Luis Store! 🚀\n_En breve te enviaremos la imagen de tu factura digital generada desde nuestro sistema._"
                        
                        url_whatsapp = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(msg_wa)}"
                        st.markdown(f'<a href="{url_whatsapp}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:12px 20px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:15px; margin-bottom:15px;">💬 Enviar Detalle por WhatsApp al {telefono_cliente}</button></a>', unsafe_allow_html=True)

                    filas_tabla_factura = ""
                    for itm in venta_reg["items_carrito"]:
                        sub_bcv_f = itm.get('precio_bcv', 0) * itm['cantidad']
                        filas_tabla_factura += f'<tr><td>{itm["cantidad"]}</td><td>{itm["nombre"]} (Talla: {itm["talla"]})</td><td>${itm.get("precio_bcv", 0):.2f}</td><td><b>${sub_bcv_f:.2f}</b></td></tr>'

                    factura_html = (
                        '<div class="invoice-card">'
                        '<div class="invoice-header">'
                        '<div>'
                        '<h2 style="margin:0; color:#b89728; font-size:22px; font-weight:bold; letter-spacing:1px;">LUIS STORE</h2>'
                        '<p style="margin:5px 0 0 0; font-size:12px; color:#555555;">Tienda Online | Cabimas, Zulia<br>Tel: 0412-4543304</p>'
                        '</div>'
                        '<div style="text-align: right;">'
                        '<h3 style="margin:0; color:#222222; font-size:15px; letter-spacing:1px;">FACTURA</h3>'
                        f'<p style="margin:5px 0 0 0; font-size:12px; color:#555555;">N°: #{venta_reg["id_venta"]}<br>Fecha: {fecha_entrega}</p>'
                        '</div>'
                        '</div>'
                        f'<p style="margin-bottom:15px; font-size:13px; color:#222222;"><b>Cliente:</b> {cliente}</p>'
                        '<table class="invoice-table">'
                        '<tr><th>Cant</th><th>Descripción</th><th>Precio Unit.</th><th>Total</th></tr>'
                        f'{filas_tabla_factura}'
                        '</table>'
                        '<div style="text-align: right; margin-top:15px;">'
                        f'<p style="margin:4px 0; font-size:13px; color:#555555;"><b>Condición:</b> {estado}</p>'
                        f'<h2 style="color:#b89728; margin:8px 0; font-size:20px;">TOTAL: ${total_bcv_carrito:.2f} a BCV</h2>'
                        '</div>'
                        '<hr style="border:0; border-top:1px solid #dddddd; margin:20px 0;">'
                        '<div style="text-align: center; font-size: 11px; color: #666666; letter-spacing:0.5px;">'
                        'Instagram: @luisstore.ve | TikTok: @luisstorecabimas<br>'
                        '<b>¡Gracias por tu compra en Luis Store!</b>'
                        '</div>'
                        '</div>'
                    )
                    st.markdown(factura_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MÓDULO DE INVENTARIO
# ---------------------------------------------------------
elif menu == "📦 Módulo de Inventario (Tallas y Stock)":
    st.subheader("📦 Inventario General Organizado en la Nube")
    
    if not inventario:
        st.info("No hay productos registrados en Firebase todavía.")
    else:
        for i, p in enumerate(inventario):
            st.markdown("---")
            col_img, col_info = st.columns([1, 3])
            with col_img:
                if p.get('foto_base64'):
                    try:
                        img_bytes = base64.b64decode(p['foto_base64'])
                        st.image(img_bytes, width=120)
                    except Exception:
                        st.info("Sin foto")
                else:
                    st.info("Sin foto")
            with col_info:
                st.write(f"**ID:** {i} | **Prenda:** {p['nombre']} (Talla: {p['talla']})")
                st.write(f"**Stock Disponible:** {p['stock']} unidades")
                st.write(f"**Precio oficial ($ a BCV):** ${p.get('precio_bcv', 0):.2f}")

# ---------------------------------------------------------
# 3. AGREGAR NUEVO PRODUCTO O TALLA AL INVENTARIO
# ---------------------------------------------------------
elif menu == "➕ Agregar Nuevo Producto / Talla":
    st.subheader("➕ Registrar Ropa, Talla, Costos, Precios y Foto en Firebase")
    
    with st.form("form_producto"):
        nombre = st.text_input("Nombre de la prenda (Ej: Oversize Streetwear, Bermuda, Short)")
        talla = st.selectbox("Selecciona la Talla", ["S", "M", "L", "XL", "XXL", "Única", "30", "32", "34", "36", "38"])
        costo_usdt = st.number_input("Costo interno con proveedor (en USDT):", min_value=0.0, step=0.5)
        envio_usdt = st.number_input("Costo de envío unitario (en USDT):", min_value=0.0, step=0.1)
        precio_usdt = st.number_input("Precio interno de referencia (en USDT):", min_value=0.0, step=0.5)
        precio_bcv = st.number_input("Precio de venta oficial ($ a BCV):", min_value=0.0, step=0.5)
        stock = st.number_input("Cantidad / Stock inicial para esta talla:", min_value=0, step=1, value=1)
        
        foto_subida = st.file_uploader("Sube una foto del producto (Opcional):", type=["jpg", "png", "jpeg"])
        
        submit = st.form_submit_button("Guardar en Firebase 🚀")
        
        if submit:
            if nombre.strip() == "":
                st.error("❌ El nombre del producto no puede estar vacío.")
            else:
                foto_b64 = ""
                if foto_subida is not None:
                    try:
                        img = Image.open(foto_subida)
                        img.thumbnail((400, 400))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG", quality=85)
                        foto_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    except Exception:
                        foto_b64 = base64.b64encode(foto_subida.read()).decode("utf-8")

                nuevo_prod = {
                    "nombre": nombre.strip(),
                    "talla": talla,
                    "costo_usdt": costo_usdt,
                    "envio_usdt": envio_usdt,
                    "precio_usdt": precio_usdt,
                    "precio_bcv": precio_bcv,
                    "stock": int(stock),
                    "foto_base64": foto_b64
                }
                db.collection("inventario").add(nuevo_prod)
                st.success(f"✅ ¡{nombre} (Talla: {talla}) guardado con éxito en Firebase Cloud con su foto optimizada!")
                st.rerun()

# ---------------------------------------------------------
# 4. EDITAR / ELIMINAR / FOTOS EN INVENTARIO
# ---------------------------------------------------------
elif menu == "✏️ Editar / Eliminar / Fotos (Inventario)":
    st.subheader("✏️ Modificar Precios, Stock, Foto o Eliminar Producto Cloud")
    
    if not inventario:
        st.warning("⚠️ No hay productos en el inventario de la nube para gestionar.")
    else:
        opciones_editar = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']})" for i, p in enumerate(inventario)]
        seleccion_edit = st.selectbox("Selecciona el producto a gestionar:", opciones_editar)
        idx_edit = int(seleccion_edit.split(":")[0].replace("ID", "").strip())
        
        prod_actual = inventario[idx_edit]
        
        if prod_actual.get('foto_base64'):
            try:
                img_bytes = base64.b64decode(prod_actual['foto_base64'])
                st.image(img_bytes, width=150, caption="Foto actual")
            except Exception:
                pass
            
        with st.form("form_editar"):
            nuevo_nombre = st.text_input("Nombre de la prenda:", value=prod_actual['nombre'])
            nueva_talla = st.text_input("Talla:", value=prod_actual['talla'])
            nuevo_costo = st.number_input("Costo proveedor ($ USDT):", min_value=0.0, value=float(prod_actual['costo_usdt']), step=0.5)
            nuevo_envio = st.number_input("Costo envío unitario ($ USDT):", min_value=0.0, value=float(prod_actual['envio_usdt']), step=0.1)
            nuevo_precio_usdt = st.number_input("Precio ref USDT:", min_value=0.0, value=float(prod_actual['precio_usdt']), step=0.5)
            nuevo_precio_bcv = st.number_input("Precio oficial ($ a BCV):", min_value=0.0, value=float(prod_actual.get('precio_bcv', 0)), step=0.5)
            nuevo_stock = st.number_input("Stock total actual:", min_value=0, value=int(prod_actual['stock']), step=1)
            
            nueva_foto_subida = st.file_uploader("Actualizar foto del producto (Opcional):", type=["jpg", "png", "jpeg"], key="edit_foto_file")
            
            guardar_cambios = st.form_submit_button("Actualizar Producto Cloud")
            
            if guardar_cambios:
                prod_id_doc = prod_actual.get('id_doc')
                
                foto_b64_act = prod_actual.get('foto_base64', '')
                if nueva_foto_subida is not None:
                    try:
                        img = Image.open(nueva_foto_subida)
                        img.thumbnail((400, 400))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG", quality=85)
                        foto_b64_act = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    except Exception:
                        foto_b64_act = base64.b64encode(nueva_foto_subida.read()).decode("utf-8")

                datos_act = {
                    "nombre": nuevo_nombre.strip(),
                    "talla": nueva_talla.strip(),
                    "costo_usdt": nuevo_costo,
                    "envio_usdt": nuevo_envio,
                    "precio_usdt": nuevo_precio_usdt,
                    "precio_bcv": nuevo_precio_bcv,
                    "stock": int(nuevo_stock),
                    "foto_base64": foto_b64_act
                }
                if prod_id_doc:
                    db.collection("inventario").document(prod_id_doc).set(datos_act)
                st.success(f"✅ ¡El producto ha sido actualizado en la nube correctamente!")
                st.rerun()

        st.markdown("---")
        st.error("⚠️ Zona de eliminación:")
        if st.button("🗑️ Eliminar este producto del inventario Cloud", type="primary"):
            prod_id_doc = prod_actual.get('id_doc')
            if prod_id_doc:
                db.collection("inventario").document(prod_id_doc).delete()
            st.success("✅ ¡Producto eliminado de Firebase correctamente!")
            st.rerun()

# ---------------------------------------------------------
# 5. FONDOS DISPONIBLES EN BINANCE
# ---------------------------------------------------------
elif menu == "🟡 Fondos Disponibles en Binance":
    st.subheader("🟡 Control Manual y Automático de Fondos en Binance (Cloud)")
    
    saldo_actual = binance_data.get("saldo_actual", 0.0)
    st.metric("💰 Saldo Actual en Binance", f"${saldo_actual:,.2f} USDT")
    
    st.markdown("---")
    st.subheader("➕ / ➖ Registrar Entrada o Salida de USDT Manual")
    
    with st.form("form_ajuste_binance"):
        tipo_mov = st.selectbox("Tipo de movimiento:", ["Entrada de USDT (Venta / Abono)", "Salida / Retiro (Ej: Compra 1688, Envío, Gastos)"])
        monto_mov = st.number_input("Monto exacto en USDT:", min_value=0.0, value=10.0, step=0.5)
        desc_mov = st.text_input("Descripción (Ej: Compra de mercancía, Pago de flete, etc.)")
        
        btn_ajuste = st.form_submit_button("Guardar en Binance Cloud")
        
        if btn_ajuste:
            if monto_mov <= 0:
                st.error("❌ Ingresa un monto válido mayor a 0.")
            else:
                if "Entrada" in tipo_mov:
                    binance_data["saldo_actual"] += monto_mov
                    tipo_str = "Entrada USDT"
                else:
                    binance_data["saldo_actual"] -= monto_mov
                    tipo_str = "Salida USDT"
                
                binance_data["movimientos"].append({
                    "fecha": str(date.today()),
                    "tipo": tipo_str,
                    "monto": monto_mov if "Entrada" in tipo_mov else -monto_mov,
                    "descripcion": desc_mov.strip() if desc_mov.strip() else tipo_str
                })
                
                guardar_binance_cloud(binance_data)
                st.success(f"✅ ¡Movimiento registrado en la nube! Nuevo saldo: ${binance_data['saldo_actual']:.2f} USDT")
                st.rerun()
                
    st.markdown("---")
    st.subheader("📜 Historial de Movimientos en Binance")
    movs = binance_data.get("movimientos", [])
    if not movs:
        st.info("No hay movimientos registrados en Binance todavía.")
    else:
        df_movs = pd.DataFrame(movs)
        st.dataframe(df_movs)

        st.markdown("### 🗑️ Limpiar o Eliminar Transacciones de Binance")
        col_del1, col_del2 = st.columns(2)
        
        with col_del1:
            if st.button("🗑️ Eliminar el último movimiento"):
                if binance_data["movimientos"]:
                    ultimo = binance_data["movimientos"].pop()
                    binance_data["saldo_actual"] -= ultimo["monto"]
                    guardar_binance_cloud(binance_data)
                    st.success("✅ ¡Último movimiento eliminado y saldo ajustado en la nube!")
                    st.rerun()
                    
        with col_del2:
            if st.button("⚠️ Resetear / Limpiar todo el historial de Binance", type="primary"):
                binance_data = {"saldo_actual": 0.0, "movimientos": []}
                guardar_binance_cloud(binance_data)
                st.success("✅ ¡Historial de Binance limpiado en la nube!")
                st.rerun()

# ---------------------------------------------------------
# 6. CUENTAS POR COBRAR (CUOTAS)
# ---------------------------------------------------------
elif menu == "📋 Cuentas por Cobrar (Cuotas)":
    st.subheader("📋 Cuentas Pendientes por Cobrar (Cloud)")
    
    cuotas_pendientes = []
    for v in ventas:
        if v.get("estado") == "CUOTAS (Pendiente)":
            cuotas_detalle = v.get("detalle_cuotas", [])
            if any(not c.get("pagada", False) for c in cuotas_detalle):
                cuotas_pendientes.append(v)
    
    if not cuotas_pendientes:
        st.success("🎉 ¡Excelente! No hay cuentas pendientes por cobrar en la nube.")
    else:
        for idx_v, v in enumerate(cuotas_pendientes):
            st.markdown(f"---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**ID Venta:** #{v['id_venta']}")
                st.write(f"**Cliente:** {v.get('cliente', 'Cliente')}")
                if v.get('telefono'):
                    st.write(f"📱 **Tlf:** {v['telefono']}")
                st.write(f"**Entrega:** {v.get('fecha_entrega', 'N/A')}")
            with col2:
                total_bcv_ref = v.get('total_venta_bcv', 0)
                st.write(f"**Prenda(s):** {v['producto']}")
                st.write(f"**Total Venta:** ${total_bcv_ref:.2f} a BCV")
                
                cuotas_detalle = v.get('detalle_cuotas', [])
                tasa_bcv_ref = total_bcv_ref / v['total_venta_usdt'] if v.get('total_venta_usdt', 0) > 0 else 0
                
                total_pagado_bcv = sum(c.get('monto_pagado_bcv', 0.0) for c in cuotas_detalle)
                resta_bcv = total_bcv_ref - total_pagado_bcv
                
                st.markdown(f"🔴 **Resta por cobrar:** **${resta_bcv:.2f} a BCV**")
                
                st.markdown("**Desglose de Cuotas y Abonos:**")
                for c in cuotas_detalle:
                    nro_c = c['nro']
                    fecha_c = c['fecha']
                    pagada_c = c.get('pagada', False)
                    
                    if pagada_c:
                        st.markdown(f"✅ ~~Cuota {nro_c} (Vence: {fecha_c}) | Pagada~~ **[PAGADA]**")
                    else:
                        st.markdown(f"⏳ **Cuota {nro_c}:** Vence el {fecha_c}")
                        
                        with st.expander(f"Registrar abono / pago Cuota #{nro_c}"):
                            key_abono_usdt = f"abono_usdt_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_abono_bcv = f"abono_bcv_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_fact_bcv = f"fact_bcv_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_fact_resta = f"fact_resta_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_btn_conf = f"btn_conf_{idx_v}_v{v['id_venta']}_c{nro_c}"

                            deuda_esta_cuota_bcv = (c['monto_estimado'] * tasa_bcv_ref) - c.get('monto_pagado_bcv', 0.0)
                            deuda_esta_cuota_usdt = deuda_esta_cuota_bcv / tasa_bcv_ref if tasa_bcv_ref > 0 else c['monto_estimado']
                            
                            abono_usdt = st.number_input(f"Monto abonado (USDT):", value=float(deuda_esta_cuota_usdt), step=0.5, key=key_abono_usdt)
                            abono_bcv = st.number_input(f"Monto abonado ($ a BCV):", value=float(deuda_esta_cuota_bcv), step=0.5, key=key_abono_bcv)
                            
                            st.markdown("---")
                            st.markdown("✏️ **Personalizar Comprobante para el Cliente:**")
                            monto_factura_bcv = st.number_input("Monto a mostrar en factura ($ a BCV):", value=float(abono_bcv), step=0.5, key=key_fact_bcv)
                            resta_factura_bcv = st.number_input("Resta a mostrar en factura ($ a BCV):", value=float(resta_bcv - abono_bcv), step=0.5, key=key_fact_resta)
                            
                            if st.button(f"Aplicar Abono Cuota #{nro_c}", key=key_btn_conf):
                                if abono_usdt <= 0 and abono_bcv <= 0:
                                    st.warning("⚠️ Ingresa un monto de abono válido mayor a 0.")
                                else:
                                    c['monto_pagado'] = c.get('monto_pagado', 0.0) + abono_usdt
                                    c['monto_pagado_bcv'] = c.get('monto_pagado_bcv', 0.0) + abono_bcv
                                    
                                    estimado_bcv_cuota = c['monto_estimado'] * tasa_bcv_ref
                                    if c['monto_pagado_bcv'] >= estimado_bcv_cuota - 0.01:
                                        c['pagada'] = True
                                    
                                    binance_data["saldo_actual"] += abono_usdt
                                    binance_data["movimientos"].append({
                                        "fecha": str(date.today()),
                                        "tipo": "Entrada USDT (Abono Cuotas Cloud)",
                                        "monto": abono_usdt,
                                        "descripcion": f"Abono Cuota #{nro_c} - Cliente: {v.get('cliente', 'Cliente')} (Venta #{v['id_venta']})"
                                    })
                                    guardar_binance_cloud(binance_data)
                                    
                                    if all(item.get('pagada', False) for item in cuotas_detalle):
                                        v['estado'] = "PAGADO"
                                        st.success(f"✅ ¡Venta #{v['id_venta']} saldada por completo!")
                                    else:
                                        st.success(f"✅ ¡Abono registrado en la nube con éxito!")

                                    if v.get('telefono'):
                                        tel_limpio = ''.join(filter(str.isdigit, v['telefono']))
                                        if not tel_limpio.startswith("58") and len(tel_limpio) == 10:
                                            tel_limpio = "58" + tel_limpio
                                        msg_abono = f"Hola {v.get('cliente', 'Cliente')}, registramos tu abono de la Cuota #{nro_c} (Venta #{v['id_venta']}). Abonado: ${monto_factura_bcv:.2f} BCV. Restante: ${resta_factura_bcv:.2f} BCV. ¡Gracias!\n_En breve te enviaremos la imagen de tu recibo._"
                                        url_wa_abono = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(msg_abono)}"
                                        st.markdown(f'<a href="{url_wa_abono}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 18px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:14px; margin-bottom:10px;">💬 Enviar Comprobante por WhatsApp</button></a>', unsafe_allow_html=True)

                                    st.markdown("---")
                                    st.markdown("### 🧾 Comprobante de Abono (Listo para capture)")
                                    factura_abono = (
                                        '<div class="invoice-card">'
                                        '<div class="invoice-header">'
                                        '<div>'
                                        '<h2 style="margin:0; color:#b89728; font-size:22px; font-weight:bold; letter-spacing:1px;">LUIS STORE</h2>'
                                        f'<p style="margin:5px 0 0 0; font-size:12px; color:#555555;">Comprobante de Abono — Cuota #{nro_c}</p>'
                                        '</div>'
                                        '<div style="text-align: right;">'
                                        f'<p style="margin:0; font-size:12px; color:#555555;">Ref: #{v["id_venta"]}<br>Fecha: {date.today()}</p>'
                                        '</div>'
                                        '</div>'
                                        f'<p style="margin-bottom:15px; font-size:13px; color:#222222;"><b>Cliente:</b> {v.get("cliente", "Cliente")}<br><b>Productos:</b> {v["producto"]}</p>'
                                        '<div style="background:#f8f9fa; padding:15px; border-radius:8px; border:1px solid #e0e0e0; margin-bottom:15px;">'
                                        f'<p style="margin:0; font-size:14px; color:#2e7d32; font-weight:bold;">MONTO ABONADO: ${monto_factura_bcv:.2f} a BCV</p>'
                                        f'<p style="margin:8px 0 0 0; font-size:14px; color:#c62828; font-weight:bold;">RESTA POR PAGAR: ${resta_factura_bcv:.2f} a BCV</p>'
                                        '</div>'
                                        '<div style="text-align: center; font-size: 11px; color: #666666; letter-spacing:0.5px;">'
                                        'Pedidos: 0412-4543304 | Instagram: @luisstore.ve<br>'
                                        '<b>¡Gracias por tu abono!</b>'
                                        '</div>'
                                        '</div>'
                                    )
                                    st.markdown(factura_abono, unsafe_allow_html=True)
                                    
                                    if 'id_doc' in v:
                                        actualizar_venta_cloud(v['id_doc'], v)
                                    st.rerun()

            with col3:
                if st.button(f"Marcar Todo Pagado #{v['id_venta']}", key=f"pay_all_{idx_v}_v{v['id_venta']}"):
                    cuotas_detalle = v.get('detalle_cuotas', [])
                    total_deuda_restante_usdt = sum(c.get('monto_estimado', 0) - c.get('monto_pagado', 0) for c in cuotas_detalle if not c.get('pagada', False))
                    
                    for c in cuotas_detalle:
                        c['monto_pagado'] = c.get('monto_estimado', 0)
                        c['monto_pagado_bcv'] = c.get('monto_estimado', 0) * tasa_bcv_ref
                        c['pagada'] = True
                    v['estado'] = "PAGADO"
                    
                    if total_deuda_restante_usdt > 0:
                        binance_data["saldo_actual"] += total_deuda_restante_usdt
                        binance_data["movimientos"].append({
                            "fecha": str(date.today()),
                            "tipo": "Entrada USDT (Pago Total Cuotas Cloud)",
                            "monto": total_deuda_restante_usdt,
                            "descripcion": f"Saldado completo Venta #{v['id_venta']} - Cliente: {v.get('cliente', 'Cliente')}"
                        })
                        guardar_binance_cloud(binance_data)

                    if 'id_doc' in v:
                        actualizar_venta_cloud(v['id_doc'], v)
                    st.success(f"¡Venta #{v['id_venta']} marcada como pagada en la nube!")
                    st.rerun()

# ---------------------------------------------------------
# 7. HISTORIAL, FACTURACIÓN & FINANZAS
# ---------------------------------------------------------
elif menu == "📊 Historial, Facturación & Finanzas":
    st.subheader("📊 Historial General Cloud, Recibos Digitales & Finanzas")
    
    if not ventas:
        st.info("No hay ventas registradas en la nube todavía.")
    else:
        df_ventas = pd.DataFrame(ventas)
        st.dataframe(df_ventas[['id_venta', 'cliente', 'telefono', 'producto', 'cantidad', 'estado', 'fecha_entrega', 'cuotas', 'total_venta_usdt', 'total_venta_bcv', 'ganancia_usdt', 'reinversion_usdt']])
        
        st.markdown("---")
        st.subheader("🧾 Generar Factura Digital Profesional para WhatsApp")
        opciones_factura = [f"Venta #{v['id_venta']} — Cliente: {v.get('cliente', 'Cliente')} — {v['producto']}" for v in ventas]
        sel_factura = st.selectbox("Selecciona la venta para ver su factura:", opciones_factura)
        
        if sel_factura:
            id_sel = int(sel_factura.split("—")[0].replace("Venta #", "").strip())
            v_encontrada = next((v for v in ventas if v['id_venta'] == id_sel), None)
            
            if v_encontrada:
                total_bcv_val = v_encontrada.get('total_venta_bcv', 0)
                cuotas_d = v_encontrada.get('detalle_cuotas', [])
                tasa_ref = total_bcv_val / v_encontrada['total_venta_usdt'] if v_encontrada.get('total_venta_usdt', 0) > 0 else 0
                
                total_pagado_bcv_val = sum(c.get('monto_pagado_bcv', 0.0) for c in cuotas_d)
                resta_bcv_val = total_bcv_val - total_pagado_bcv_val

                if v_encontrada.get('telefono'):
                    tel_h = ''.join(filter(str.isdigit, v_encontrada['telefono']))
                    if not tel_h.startswith("58") and len(tel_h) == 10:
                        tel_h = "58" + tel_h
                    msg_h = f"Hola {v_encontrada.get('cliente', 'Cliente')}, detalle de factura N° #{v_encontrada['id_venta']}: Total: ${total_bcv_val:.2f} BCV. Estado: {v_encontrada['estado']}. ¡Gracias!\n_En breve te enviaremos la imagen de tu factura digital._"
                    url_wa_h = f"https://wa.me/{tel_h}?text={urllib.parse.quote(msg_h)}"
                    st.markdown(f'<a href="{url_wa_h}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 18px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:14px; margin-bottom:15px;">💬 Enviar esta Factura por WhatsApp</button></a>', unsafe_allow_html=True)

                texto_resta_html = ""
                if v_encontrada['estado'] == "CUOTAS (Pendiente)":
                    texto_resta_html = f'<p style="margin:4px 0; font-size:13px; color:#c62828;"><b>Resta por pagar:</b> ${resta_bcv_val:.2f} a BCV</p>'

                filas_hist = ""
                if "items_carrito" in v_encontrada:
                    for itm in v_encontrada["items_carrito"]:
                        sub_bcv_h = itm.get('precio_bcv', 0) * itm.get('cantidad', 1)
                        filas_hist += f'<tr><td>{itm.get("cantidad", 1)}</td><td>{itm.get("nombre", "Prenda")} (Talla: {itm.get("talla", "Única")})</td><td><b>${sub_bcv_h:.2f}</b></td></tr>'
                else:
                    filas_hist += f'<tr><td>{v_encontrada["cantidad"]}</td><td>{v_encontrada["producto"]} (Talla: {v_encontrada["talla"]})</td><td><b>${total_bcv_val:.2f}</b></td></tr>'

                factura_historial = (
                    '<div class="invoice-card">'
                    '<div class="invoice-header">'
                    '<div>'
                    '<h2 style="margin:0; color:#b89728; font-size:22px; font-weight:bold; letter-spacing:1px;">LUIS STORE</h2>'
                    '<p style="margin:5px 0 0 0; font-size:12px; color:#555555;">Tienda Online | Cabimas, Zulia<br>Tel: 0412-4543304</p>'
                    '</div>'
                    '<div style="text-align: right;">'
                    '<h3 style="margin:0; color:#222222; font-size:15px; letter-spacing:1px;">FACTURA</h3>'
                    f'<p style="margin:5px 0 0 0; font-size:12px; color:#555555;">N°: #{v_encontrada["id_venta"]}<br>Fecha: {v_encontrada["fecha_entrega"]}</p>'
                    '</div>'
                    '</div>'
                    f'<p style="margin-bottom:15px; font-size:13px; color:#222222;"><b>Cliente:</b> {v_encontrada.get("cliente", "Cliente")}</p>'
                    '<table class="invoice-table">'
                    '<tr><th>Cant</th><th>Descripción</th><th>Total</th></tr>'
                    f'{filas_hist}'
                    '</table>'
                    '<div style="text-align: right; margin-top:15px;">'
                    f'<p style="margin:4px 0; font-size:13px; color:#555555;"><b>Condición:</b> {v_encontrada["estado"]}</p>'
                    f'{texto_resta_html}'
                    f'<h2 style="color:#b89728; margin:8px 0; font-size:20px;">TOTAL: ${total_bcv_val:.2f} a BCV</h2>'
                    '</div>'
                    '<hr style="border:0; border-top:1px solid #dddddd; margin:20px 0;">'
                    '<div style="text-align: center; font-size: 11px; color: #666666; letter-spacing:0.5px;">'
                    'Instagram: @luisstore.ve | TikTok: @luisstorecabimas<br>'
                    '<b>¡Gracias por tu compra en Luis Store!</b>'
                    '</div>'
                    '</div>'
                )
                st.markdown(factura_historial, unsafe_allow_html=True)

        # Cálculos automáticos directos de Firebase para las 4 métricas principales
        total_acum_usdt = df_ventas['total_venta_usdt'].sum()
        total_acum_bcv = df_ventas.get('total_venta_bcv', pd.Series([0]*len(df_ventas))).sum()
        total_ganancias_realizadas = df_ventas['ganancia_usdt'].sum()
        total_reinversion_realizada = df_ventas['reinversion_usdt'].sum()
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Venta Total ($ USDT)", f"${total_acum_usdt:.2f}")
        col2.metric("Venta Total ($ a BCV)", f"${total_acum_bcv:.2f}")
        col3.metric("Ganancias Totales", f"${total_ganancias_realizadas:.2f}")
        col4.metric("Fondo de Reinversión", f"${total_reinversion_realizada:.2f}")
        
        st.markdown("---")
        st.subheader("🗑️ Eliminar Venta Errónea o de Prueba")
        opciones_borrar = [f"ID Venta #{v['id_venta']} — Cliente: {v.get('cliente', 'Cliente')} — Prenda: {v['producto']} (${v['total_venta_usdt']} USDT)" for v in ventas]
        sel_borrar = st.selectbox("Selecciona la venta que deseas eliminar del historial:", opciones_borrar)
        
        if st.button("Eliminar Venta Seleccionada", type="primary"):
            id_a_borrar = int(sel_borrar.split("—")[0].replace("ID Venta #", "").strip())
            v_borrar = next((v for v in ventas if v['id_venta'] == id_a_borrar), None)
            if v_borrar and 'id_doc' in v_borrar:
                eliminar_venta_cloud(v_borrar['id_doc'])
            st.success(f"✅ ¡La venta #{id_a_borrar} ha sido eliminada de Firebase correctamente!")
            st.rerun()
