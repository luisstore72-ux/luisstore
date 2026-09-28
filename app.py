import json
import os
import streamlit as st
import pandas as pd
from datetime import date

# Archivos de datos independientes para inventario, ventas y finanzas
ARCHIVO_INVENTARIO = "inventario_tallas.json"
ARCHIVO_VENTAS = "ventas_tallas.json"
ARCHIVO_BINANCE = "binance_fondos.json"
CARPETA_FOTOS = "fotos_productos"

if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

LOGO_PATH = os.path.join(CARPETA_FOTOS, "logo_luisstore.jpg")

def cargar_datos(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def guardar_datos(archivo, datos):
    with open(archivo, "w", encoding="utf-8") as f:
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

# Configuración de la página web
st.set_page_config(page_title="LUIS STORE | Control & Ventas", layout="wide")

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

# Cargar datos actuales
inventario = cargar_datos(ARCHIVO_INVENTARIO)
ventas = cargar_datos(ARCHIVO_VENTAS)
binance_data = cargar_binance()

if 'carrito_ventas' not in st.session_state:
    st.session_state.carrito_ventas = []

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
# 1. REGISTRAR VENTA (MULTIPRODUCTO / CARRITO)
# ---------------------------------------------------------
if menu == "🛒 Registrar Venta":
    st.subheader("🛒 Registrar Venta Multiproducto (Carrito)")
    
    if not inventario:
        st.warning("⚠️ No hay productos en el inventario para vender. Ve primero a 'Agregar Nuevo Producto / Talla'.")
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
            tipo_pago = st.radio("Condición de pago para toda la compra:", ["Contado (Pagado de una vez)", "Venta por Cuotas (Pendiente)"])
            
            cliente = "Contado"
            fecha_entrega = str(date.today())
            cuotas = 1
            detalle_cuotas = []
            
            if "Cuotas" in tipo_pago:
                cliente = st.text_input("Nombre del Cliente:", value="")
                if not cliente.strip():
                    cliente = "Cliente General"
                
                fecha_entrega_obj = st.date_input("Fecha de Entrega del Producto:", value=date.today())
                fecha_entrega = str(fecha_entrega_obj)
                    
                cuotas = st.selectbox("Número de Cuotas (Máximo 4):", [1, 2, 3, 4])
                
                monto_por_cuota_ref = total_bcv_carrito / cuotas
                tasa_ref_temp = total_usdt_carrito / total_bcv_carrito if total_bcv_carrito > 0 else 1.0

                st.markdown("📝 **Indica la fecha límite y el monto exacto para cada cuota a tu preferencia:**")
                for c in range(1, cuotas + 1):
                    col_fc, col_mc = st.columns(2)
                    with col_fc:
                        f_cuota = st.date_input(f"Fecha límite cuota #{c}:", value=date.today(), key=f"cuota_f_{c}")
                    with col_mc:
                        m_cuota_bcv = st.number_input(f"Monto cuota #{c} ($ a BCV):", min_value=0.0, value=float(monto_por_cuota_ref), step=0.5, key=f"cuota_m_{c}")
                    
                    m_cuota_usdt = m_cuota_bcv * tasa_ref_temp

                    detalle_cuotas.append({
                        "nro": c,
                        "monto_estimado": m_cuota_usdt,
                        "monto_pagado": 0.0,
                        "fecha": str(f_cuota),
                        "pagada": False
                    })

            if st.button("Confirmar y Registrar Venta Total"):
                stock_suficiente = True
                for item in st.session_state.carrito_ventas:
                    prod_inv = inventario[item['id_inventario']]
                    if prod_inv['stock'] < item['cantidad']:
                        st.error(f"❌ Stock insuficiente para {item['nombre']} (Talla {item['talla']}).")
                        stock_suficiente = False
                        break
                
                if stock_suficiente:
                    inversion_total_lote = 0
                    ganancia_total_lote = 0
                    productos_resumen_factura = []
                    
                    for item in st.session_state.carrito_ventas:
                        prod_inv = inventario[item['id_inventario']]
                        prod_inv['stock'] -= item['cantidad']
                        
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
                            "fecha": fecha_entrega,
                            "pagada": True
                        }]
                        
                        binance_data["saldo_actual"] += total_usdt_carrito
                        binance_data["movimientos"].append({
                            "fecha": str(date.today()),
                            "tipo": "Entrada USDT (Venta Contado Carrito)",
                            "monto": total_usdt_carrito,
                            "descripcion": f"Venta Multiproducto Contado: {', '.join(productos_resumen_factura)}"
                        })
                        guardar_binance(binance_data)

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
                        "fecha_entrega": fecha_entrega,
                        "cuotas": cuotas,
                        "detalle_cuotas": detalle_cuotas,
                        "items_carrito": st.session_state.carrito_ventas.copy()
                    }
                    
                    ventas.append(venta_reg)
                    guardar_datos(ARCHIVO_INVENTARIO, inventario)
                    guardar_datos(ARCHIVO_VENTAS, ventas)
                    
                    st.session_state.carrito_ventas = []
                    
                    st.success("✅ ¡Venta multiproducto registrada exitosamente!")
                    
                    st.markdown("---")
                    st.markdown("### 🧾 Factura Digital Consolidada (Tómale capture para WhatsApp)")
                    
                    filas_tabla_factura = ""
                    for itm in venta_reg["items_carrito"]:
                        sub_bcv_f = itm['precio_bcv'] * itm['cantidad']
                        filas_tabla_factura += f'<tr><td>{itm["cantidad"]}</td><td>{itm["nombre"]} (Talla: {itm["talla"]})</td><td>${itm["precio_bcv"]:.2f}</td><td><b>${sub_bcv_f:.2f}</b></td></tr>'

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
    st.subheader("📦 Inventario General Organizado por Tallas")
    
    if not inventario:
        st.warning("⚠️ No hay productos registrados en el inventario todavía.")
    else:
        for i, p in enumerate(inventario):
            st.markdown("---")
            col_img, col_info = st.columns([1, 3])
            with col_img:
                if p.get('foto') and os.path.exists(p['foto']):
                    st.image(p['foto'], width=120)
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
    st.subheader("➕ Registrar Ropa, Talla, Costos, Precios y Foto")
    
    with st.form("form_producto"):
        nombre = st.text_input("Nombre de la prenda (Ej: Oversize Streetwear, Bermuda, Short)")
        talla = st.selectbox("Selecciona la Talla", ["S", "M", "L", "XL", "XXL", "Única", "30", "32", "34", "36", "38"])
        costo_usdt = st.number_input("Costo interno con proveedor (en USDT):", min_value=0.0, step=0.5)
        envio_usdt = st.number_input("Costo de envío unitario (en USDT):", min_value=0.0, step=0.1)
        precio_usdt = st.number_input("Precio interno de referencia (en USDT):", min_value=0.0, step=0.5)
        precio_bcv = st.number_input("Precio de venta oficial ($ a BCV):", min_value=0.0, step=0.5)
        stock = st.number_input("Cantidad / Stock inicial para esta talla:", min_value=0, step=1, value=1)
        
        foto_subida = st.file_uploader("Sube una foto del producto (Opcional):", type=["jpg", "png", "jpeg"])
        
        submit = st.form_submit_button("Guardar en el Inventario")
        
        if submit:
            if nombre.strip() == "":
                st.error("❌ El nombre del producto no puede estar vacío.")
            else:
                ruta_foto = ""
                if foto_subida is not None:
                    ruta_foto = os.path.join(CARPETA_FOTOS, f"{nombre}_{talla}_{len(inventario)}.jpg")
                    with open(ruta_foto, "wb") as f:
                        f.write(foto_subida.getbuffer())

                nuevo_prod = {
                    "nombre": nombre.strip(),
                    "talla": talla,
                    "costo_usdt": costo_usdt,
                    "envio_usdt": envio_usdt,
                    "precio_usdt": precio_usdt,
                    "precio_bcv": precio_bcv,
                    "stock": int(stock),
                    "foto": ruta_foto
                }
                inventario.append(nuevo_prod)
                guardar_datos(ARCHIVO_INVENTARIO, inventario)
                st.success(f"✅ ¡{nombre} (Talla: {talla}) guardado con éxito en el inventario!")

# ---------------------------------------------------------
# 4. EDITAR / ELIMINAR / FOTOS EN INVENTARIO
# ---------------------------------------------------------
elif menu == "✏️ Editar / Eliminar / Fotos (Inventario)":
    st.subheader("✏️ Modificar Precios, Stock, Foto o Eliminar Producto")
    
    if not inventario:
        st.warning("⚠️ No hay productos en el inventario para gestionar.")
    else:
        opciones_editar = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']})" for i, p in enumerate(inventario)]
        seleccion_edit = st.selectbox("Selecciona el producto a gestionar:", opciones_editar)
        idx_edit = int(seleccion_edit.split(":")[0].replace("ID", "").strip())
        
        prod_actual = inventario[idx_edit]
        
        if prod_actual.get('foto') and os.path.exists(prod_actual['foto']):
            st.image(prod_actual['foto'], width=150, caption="Foto actual")
            
        with st.form("form_editar"):
            nuevo_nombre = st.text_input("Nombre de la prenda:", value=prod_actual['nombre'])
            nueva_talla = st.text_input("Talla:", value=prod_actual['talla'])
            nuevo_costo = st.number_input("Costo proveedor ($ USDT):", min_value=0.0, value=float(prod_actual['costo_usdt']), step=0.5)
            nuevo_envio = st.number_input("Costo envío unitario ($ USDT):", min_value=0.0, value=float(prod_actual['envio_usdt']), step=0.1)
            nuevo_precio_usdt = st.number_input("Precio ref USDT:", min_value=0.0, value=float(prod_actual['precio_usdt']), step=0.5)
            nuevo_precio_bcv = st.number_input("Precio oficial ($ a BCV):", min_value=0.0, value=float(prod_actual.get('precio_bcv', 0)), step=0.5)
            nuevo_stock = st.number_input("Stock total actual:", min_value=0, value=int(prod_actual['stock']), step=1)
            
            guardar_cambios = st.form_submit_button("Actualizar Producto")
            
            if guardar_cambios:
                inventario[idx_edit]['nombre'] = nuevo_nombre.strip()
                inventario[idx_edit]['talla'] = nueva_talla.strip()
                inventario[idx_edit]['costo_usdt'] = nuevo_costo
                inventario[idx_edit]['envio_usdt'] = nuevo_envio
                inventario[idx_edit]['precio_usdt'] = nuevo_precio_usdt
                inventario[idx_edit]['precio_bcv'] = nuevo_precio_bcv
                inventario[idx_edit]['stock'] = int(nuevo_stock)
                
                guardar_datos(ARCHIVO_INVENTARIO, inventario)
                st.success(f"✅ ¡El producto ID {idx_edit} ha sido actualizado correctamente!")
                st.rerun()

        st.markdown("---")
        st.error("⚠️ Zona de eliminación:")
        if st.button("🗑️ Eliminar este producto del inventario", type="primary"):
            if prod_actual.get('foto') and os.path.exists(prod_actual['foto']):
                try:
                    os.remove(prod_actual['foto'])
                except:
                    pass
            
            inventario.pop(idx_edit)
            guardar_datos(ARCHIVO_INVENTARIO, inventario)
            st.success("✅ ¡Producto eliminado del inventario correctamente!")
            st.rerun()

# ---------------------------------------------------------
# 5. FONDOS DISPONIBLES EN BINANCE (100% MANUAL)
# ---------------------------------------------------------
elif menu == "🟡 Fondos Disponibles en Binance":
    st.subheader("🟡 Control Manual y Automático de Fondos en Binance (USDT)")
    
    saldo_actual = binance_data.get("saldo_actual", 0.0)
    st.metric("💰 Saldo Actual in Binance", f"${saldo_actual:,.2f} USDT")
    
    st.markdown("---")
    st.subheader("➕ / ➖ Registrar Entrada o Salida de USDT Manual")
    
    with st.form("form_ajuste_binance"):
        tipo_mov = st.selectbox("Tipo de movimiento:", ["Entrada de USDT (Venta / Abono)", "Salida / Retiro (Ej: Compra 1688, Envío, Gastos)"])
        monto_mov = st.number_input("Monto exacto en USDT:", min_value=0.0, value=10.0, step=0.5)
        desc_mov = st.text_input("Descripción (Ej: Compra de mercancía, Pago de flete, etc.)")
        
        btn_ajuste = st.form_submit_button("Guardar en Binance")
        
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
                
                guardar_binance(binance_data)
                st.success(f"✅ ¡Movimiento registrado! Nuevo saldo en Binance: ${binance_data['saldo_actual']:.2f} USDT")
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
                    guardar_binance(binance_data)
                    st.success("✅ ¡Último movimiento eliminado y saldo ajustado!")
                    st.rerun()
                    
        with col_del2:
            if st.button("⚠️ Resetear / Limpiar todo el historial de Binance", type="primary"):
                binance_data = {"saldo_actual": 0.0, "movimientos": []}
                guardar_binance(binance_data)
                st.success("✅ ¡Historial de Binance limpiado y saldo puesto en 0.00 USDT!")
                st.rerun()

# ---------------------------------------------------------
# 6. CUENTAS POR COBRAR (CUOTAS) — CORREGIDO EXACTO EN BCV
# ---------------------------------------------------------
elif menu == "📋 Cuentas por Cobrar (Cuotas)":
    st.subheader("📋 Cuentas Pendientes por Cobrar (Venta por Cuotas)")
    
    cuotas_pendientes = []
    for v in ventas:
        if v.get("estado") == "CUOTAS (Pendiente)":
            cuotas_detalle = v.get("detalle_cuotas", [])
            if any(not c.get("pagada", False) for c in cuotas_detalle):
                cuotas_pendientes.append(v)
    
    if not cuotas_pendientes:
        st.success("🎉 ¡Excelente! No hay cuentas pendientes por cobrar (todo está pagado).")
    else:
        for idx_v, v in enumerate(cuotas_pendientes):
            st.markdown(f"---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**ID Venta:** #{v['id_venta']}")
                st.write(f"**Cliente:** {v['cliente']}")
                st.write(f"**Entrega:** {v.get('fecha_entrega', 'N/A')}")
            with col2:
                total_bcv_ref = v.get('total_venta_bcv', 0)
                st.write(f"**Prenda(s):** {v['producto']}")
                st.write(f"**Total Venta:** ${total_bcv_ref:.2f} a BCV")
                
                cuotas_detalle = v.get('detalle_cuotas', [])
                tasa_bcv_ref = total_bcv_ref / v['total_venta_usdt'] if v['total_venta_usdt'] > 0 else 0
                
                total_pagado_bcv = sum(c.get('monto_pagado_bcv', c.get('monto_pagado', 0) * tasa_bcv_ref) for c in cuotas_detalle)
                resta_bcv = total_bcv_ref - total_pagado_bcv
                
                st.markdown(f"🔴 **Resta por cobrar:** **${resta_bcv:.2f} a BCV**")
                
                st.markdown("**Desglose de Cuotas y Abonos:**")
                for c in cuotas_detalle:
                    nro_c = c['nro']
                    fecha_c = c['fecha']
                    pagada_c = c.get('pagada', False)
                    
                    monto_est_usdt = c.get('monto_estimado', 0)
                    monto_est_bcv = monto_est_usdt * tasa_bcv_ref
                    
                    monto_pag_bcv = c.get('monto_pagado_bcv', c.get('monto_pagado', 0) * tasa_bcv_ref)
                    deuda_cuota_bcv = monto_est_bcv - monto_pag_bcv

                    if pagada_c:
                        st.markdown(f"✅ ~~Cuota {nro_c} (Vence: {fecha_c}) | Pagada~~ **[PAGADA]**")
                    else:
                        st.markdown(f"⏳ **Cuota {nro_c}:** Vence el {fecha_c} (Resta: ${deuda_cuota_bcv:.2f} a BCV)")
                        
                        with st.expander(f"Registrar abono / pago Cuota #{nro_c}"):
                            key_abono_bcv = f"abono_bcv_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_fact_bcv = f"fact_bcv_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_fact_resta = f"fact_resta_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_btn_conf = f"btn_conf_{idx_v}_v{v['id_venta']}_c{nro_c}"

                            abono_bcv = st.number_input(f"Monto abonado ($ a BCV):", min_value=0.0, value=float(deuda_cuota_bcv), step=0.5, key=key_abono_bcv)
                            
                            st.markdown("---")
                            st.markdown("✏️ **Personalizar Comprobante para el Cliente:**")
                            monto_factura_bcv = st.number_input("Monto a mostrar en factura ($ a BCV):", min_value=0.0, value=float(abono_bcv), step=0.5, key=key_fact_bcv)
                            resta_factura_bcv = st.number_input("Resta a mostrar en factura ($ a BCV):", min_value=0.0, value=float(resta_bcv - abono_bcv), step=0.5, key=key_fact_resta)
                            
                            if st.button(f"Aplicar Abono Cuota #{nro_c}", key=key_btn_conf):
                                if abono_bcv <= 0:
                                    st.warning("⚠️ Ingresa un monto de abono válido mayor a 0.")
                                else:
                                    dinero_restante_bcv = abono_bcv
                                    
                                    for idx_cuota in range(nro_c - 1, len(cuotas_detalle)):
                                        cuota_actual = cuotas_detalle[idx_cuota]
                                        if dinero_restante_bcv <= 0:
                                            break
                                        
                                        est_bcv_val = cuota_actual.get('monto_estimado', 0) * tasa_bcv_ref
                                        pag_bcv_val = cuota_actual.get('monto_pagado_bcv', cuota_actual.get('monto_pagado', 0) * tasa_bcv_ref)
                                        deuda_cuota = est_bcv_val - pag_bcv_val
                                        
                                        if dinero_restante_bcv >= deuda_cuota:
                                            cuota_actual['monto_pagado_bcv'] = pag_bcv_val + deuda_cuota
                                            cuota_actual['monto_pagado'] = cuota_actual['monto_pagado_bcv'] / tasa_bcv_ref if tasa_bcv_ref > 0 else 0
                                            cuota_actual['pagada'] = True
                                            dinero_restante_bcv -= deuda_cuota
                                        else:
                                            cuota_actual['monto_pagado_bcv'] = pag_bcv_val + dinero_restante_bcv
                                            cuota_actual['monto_pagado'] = cuota_actual['monto_pagado_bcv'] / tasa_bcv_ref if tasa_bcv_ref > 0 else 0
                                            dinero_restante_bcv = 0.0
                                    
                                    abono_usdt_equivalente = abono_bcv / tasa_bcv_ref if tasa_bcv_ref > 0 else abono_bcv
                                    
                                    binance_data["saldo_actual"] += abono_usdt_equivalente
                                    binance_data["movimientos"].append({
                                        "fecha": str(date.today()),
                                        "tipo": "Entrada USDT (Abono Cuotas)",
                                        "monto": abono_usdt_equivalente,
                                        "descripcion": f"Abono Cuota #{nro_c} (${abono_bcv} a BCV) - Cliente: {v['cliente']} (Venta #{v['id_venta']})"
                                    })
                                    guardar_binance(binance_data)
                                    
                                    if all(item.get('pagada', False) for item in cuotas_detalle):
                                        v['estado'] = "PAGADO"
                                        st.success(f"✅ ¡Venta #{v['id_venta']} saldada por completo!")
                                    else:
                                        st.success(f"✅ ¡Abono registrado con éxito!")

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
                                        f'<p style="margin-bottom:15px; font-size:13px; color:#222222;"><b>Cliente:</b> {v["cliente"]}<br><b>Productos:</b> {v["producto"]}</p>'
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
                                    
                                    guardar_datos(ARCHIVO_VENTAS, ventas)

            with col3:
                if st.button(f"Marcar Todo Pagado #{v['id_venta']}", key=f"pay_all_{idx_v}_v{v['id_venta']}"):
                    cuotas_detalle = v.get('detalle_cuotas', [])
                    total_deuda_restante_bcv = sum(
                        (c.get('monto_estimado', 0) * tasa_bcv_ref) - c.get('monto_pagado_bcv', c.get('monto_pagado', 0) * tasa_bcv_ref) 
                        for c in cuotas_detalle if not c.get('pagada', False)
                    )
                    
                    for c in cuotas_detalle:
                        c['monto_pagado_bcv'] = c.get('monto_estimado', 0) * tasa_bcv_ref
                        c['monto_pagado'] = c.get('monto_estimado', 0)
                        c['pagada'] = True
                    v['estado'] = "PAGADO"
                    
                    if total_deuda_restante_bcv > 0:
                        deuda_restante_usdt = total_deuda_restante_bcv / tasa_bcv_ref if tasa_bcv_ref > 0 else 0
                        binance_data["saldo_actual"] += deuda_restante_usdt
                        binance_data["movimientos"].append({
                            "fecha": str(date.today()),
                            "tipo": "Entrada USDT (Pago Total Cuotas)",
                            "monto": deuda_restante_usdt,
                            "descripcion": f"Saldado completo Venta #{v['id_venta']} - Cliente: {v['cliente']}"
                        })
                        guardar_binance(binance_data)

                    guardar_datos(ARCHIVO_VENTAS, ventas)
                    st.success(f"¡Venta #{v['id_venta']} marcada como pagada!")
                    st.rerun()

# ---------------------------------------------------------
# 7. HISTORIAL, FACTURACIÓN & FINANZAS
# ---------------------------------------------------------
elif menu == "📊 Historial, Facturación & Finanzas":
    st.subheader("📊 Historial General, Recibos Digitales & Finanzas")
    
    if not ventas:
        st.info("No hay ventas registradas todavía.")
    else:
        df_ventas = pd.DataFrame(ventas)
        st.dataframe(df_ventas[['id_venta', 'cliente', 'producto', 'cantidad', 'estado', 'fecha_entrega', 'cuotas', 'total_venta_usdt', 'total_venta_bcv', 'ganancia_usdt', 'reinversion_usdt']])
        
        st.markdown("---")
        st.subheader("🧾 Generar Factura Digital Profesional para WhatsApp")
        opciones_factura = [f"Venta #{v['id_venta']} — Cliente: {v['cliente']} — {v['producto']}" for v in ventas]
        sel_factura = st.selectbox("Selecciona la venta para ver su factura:", opciones_factura)
        
        if sel_factura:
            id_sel = int(sel_factura.split("—")[0].replace("Venta #", "").strip())
            v_encontrada = next((v for v in ventas if v['id_venta'] == id_sel), None)
            
            if v_encontrada:
                total_bcv_val = v_encontrada.get('total_venta_bcv', 0)
                cuotas_d = v_encontrada.get('detalle_cuotas', [])
                tasa_ref_f = total_bcv_val / v_encontrada['total_venta_usdt'] if v_encontrada['total_venta_usdt'] > 0 else 0
                
                pagado_bcv = sum(c.get('monto_pagado_bcv', c.get('monto_pagado', 0) * tasa_ref_f) for c in cuotas_d)
                resta_bcv_val = total_bcv_val - pagado_bcv

                texto_resta_html = ""
                if v_encontrada['estado'] == "CUOTAS (Pendiente)":
                    texto_resta_html = f'<p style="margin:4px 0; font-size:13px; color:#c62828;"><b>Resta por pagar:</b> ${resta_bcv_val:.2f} a BCV</p>'

                filas_hist = ""
                if "items_carrito" in v_encontrada:
                    for itm in v_encontrada["items_carrito"]:
                        sub_bcv_h = itm['precio_bcv'] * itm['cantidad']
                        filas_hist += f'<tr><td>{itm["cantidad"]}</td><td>{itm["nombre"]} (Talla: {itm["talla"]})</td><td><b>${sub_bcv_h:.2f}</b></td></tr>'
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
                    f'<p style="margin-bottom:15px; font-size:13px; color:#222222;"><b>Cliente:</b> {v_encontrada["cliente"]}</p>'
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

        total_acum_usdt = df_ventas['total_venta_usdt'].sum()
        total_acum_bcv = df_ventas.get('total_venta_bcv', pd.Series([0]*len(df_ventas))).sum()
        total_ganancias = df_ventas['ganancia_usdt'].sum()
        total_reinversion = df_ventas['reinversion_usdt'].sum()
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Venta Total ($ USDT)", f"${total_acum_usdt:.2f}")
        col2.metric("Venta Total ($ a BCV)", f"${total_acum_bcv:.2f}")
        col3.metric("Ganancias Totales", f"${total_ganancias:.2f}")
        col4.metric("Fondo de Reinversión", f"${total_reinversion:.2f}")
        
        st.markdown("---")
        st.subheader("🗑️ Eliminar Venta Errónea o de Prueba")
        opciones_borrar = [f"ID Venta #{v['id_venta']} — Cliente: {v['cliente']} — Prenda: {v['producto']} (${v['total_venta_usdt']} USDT)" for v in ventas]
        sel_borrar = st.selectbox("Selecciona la venta que deseas eliminar del historial:", opciones_borrar)
        
        if st.button("Eliminar Venta Seleccionada", type="primary"):
            id_a_borrar = int(sel_borrar.split("—")[0].replace("ID Venta #", "").strip())
            ventas = [v for v in ventas if v['id_venta'] != id_a_borrar]
            guardar_datos(ARCHIVO_VENTAS, ventas)
            st.success(f"✅ ¡La venta #{id_a_borrar} ha sido eliminada del historial correctamente!")
            st.rerun()
