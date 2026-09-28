import json
import os
import streamlit as st
import pandas as pd
from datetime import date

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
st.markdown("Administra tus prendas, tallas, stock, precios a dólar BCV, Binance y genera facturas digitales profesionales.")

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
                    st.write(f"Subtotal: ${sub_bcv:.2f} dólar BCV")
                with col_c3:
                    if st.button("🗑️", key=f"del_cart_{i}"):
                        st.session_state.carrito_ventas.pop(i)
                        st.rerun()
            
            st.markdown(f"### 💵 **Monto Total a Pagar: ${total_bcv_carrito:.2f} dólar BCV**")
            
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
                
                monto_por_cuota_bcv = round(total_bcv_carrito / cuotas, 2)

                st.markdown("📝 **Fechas y montos de las cuotas:**")
                for c in range(1, cuotas + 1):
                    f_cuota = st.date_input(f"Fecha límite cuota #{c}:", value=date.today(), key=f"cuota_f_{c}")
                    detalle_cuotas.append({
                        "nro": c,
                        "monto_estimado_bcv": monto_por_cuota_bcv,
                        "monto_pagado_bcv": 0.0,
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
                            "monto_estimado_bcv": total_bcv_carrito,
                            "monto_pagado_bcv": total_bcv_carrito,
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
                st.write(f"**Precio oficial (dólar BCV):** ${p.get('precio_bcv', 0):.2f}")

# ---------------------------------------------------------
# 3. AGREGAR NUEVO PRODUCTO O TALLA AL INVENTARIO
# ---------------------------------------------------------
elif menu == "➕ Agregar Nuevo Producto / Talla":
    st.subheader("➕ Registrar Ropa, Talla, Costos, Precios y Foto")
    with st.form("form_producto"):
        nombre = st.text_input("Nombre de la prenda")
        talla = st.selectbox("Selecciona la Talla", ["S", "M", "L", "XL", "XXL", "Única", "30", "32", "34", "36", "38"])
        costo_usdt = st.number_input("Costo interno con proveedor (USDT):", min_value=0.0, step=0.5)
        envio_usdt = st.number_input("Costo de envío unitario (USDT):", min_value=0.0, step=0.1)
        precio_usdt = st.number_input("Precio interno de referencia (USDT):", min_value=0.0, step=0.5)
        precio_bcv = st.number_input("Precio de venta oficial (dólar BCV):", min_value=0.0, step=0.5)
        stock = st.number_input("Stock inicial:", min_value=0, step=1, value=1)
        foto_subida = st.file_uploader("Sube una foto del producto (Opcional):", type=["jpg", "png", "jpeg"])
        
        submit = st.form_submit_button("Guardar en el Inventario")
        if submit:
            if nombre.strip() == "":
                st.error("❌ El nombre no puede estar vacío.")
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
                st.success("✅ ¡Guardado con éxito!")

# ---------------------------------------------------------
# 4. EDITAR / ELIMINAR / FOTOS EN INVENTARIO
# ---------------------------------------------------------
elif menu == "✏️ Editar / Eliminar / Fotos (Inventario)":
    st.subheader("✏️ Modificar o Eliminar Producto")
    if not inventario:
        st.warning("⚠️ No hay productos en el inventario.")
    else:
        opciones_editar = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']})" for i, p in enumerate(inventario)]
        seleccion_edit = st.selectbox("Selecciona:", opciones_editar)
        idx_edit = int(seleccion_edit.split(":")[0].replace("ID", "").strip())
        prod_actual = inventario[idx_edit]
        
        with st.form("form_editar"):
            nuevo_nombre = st.text_input("Nombre:", value=prod_actual['nombre'])
            nueva_talla = st.text_input("Talla:", value=prod_actual['talla'])
            nuevo_costo = st.number_input("Costo USDT:", min_value=0.0, value=float(prod_actual['costo_usdt']), step=0.5)
            nuevo_envio = st.number_input("Envío USDT:", min_value=0.0, value=float(prod_actual['envio_usdt']), step=0.1)
            nuevo_precio_usdt = st.number_input("Ref USDT:", min_value=0.0, value=float(prod_actual['precio_usdt']), step=0.5)
            nuevo_precio_bcv = st.number_input("Precio dólar BCV:", min_value=0.0, value=float(prod_actual.get('precio_bcv', 0)), step=0.5)
            nuevo_stock = st.number_input("Stock:", min_value=0, value=int(prod_actual['stock']), step=1)
            
            if st.form_submit_button("Actualizar Producto"):
                inventario[idx_edit].update({
                    'nombre': nuevo_nombre.strip(),
                    'talla': nueva_talla.strip(),
                    'costo_usdt': nuevo_costo,
                    'envio_usdt': nuevo_envio,
                    'precio_usdt': nuevo_precio_usdt,
                    'precio_bcv': nuevo_precio_bcv,
                    'stock': int(nuevo_stock)
                })
                guardar_datos(ARCHIVO_INVENTARIO, inventario)
                st.success("✅ ¡Actualizado correctamente!")
                st.rerun()

        if st.button("🗑️ Eliminar este producto", type="primary"):
            inventario.pop(idx_edit)
            guardar_datos(ARCHIVO_INVENTARIO, inventario)
            st.success("✅ ¡Eliminado!")
            st.rerun()

# ---------------------------------------------------------
# 5. FONDOS DISPONIBLES EN BINANCE
# ---------------------------------------------------------
elif menu == "🟡 Fondos Disponibles en Binance":
    st.subheader("🟡 Control de Fondos en Binance (USDT)")
    saldo_actual = binance_data.get("saldo_actual", 0.0)
    st.metric("💰 Saldo Actual", f"${saldo_actual:,.2f} USDT")
    
    with st.form("form_ajuste_binance"):
        tipo_mov = st.selectbox("Movimiento:", ["Entrada de USDT", "Salida / Retiro"])
        monto_mov = st.number_input("Monto USDT:", min_value=0.0, value=10.0, step=0.5)
        desc_mov = st.text_input("Descripción:")
        
        if st.form_submit_button("Guardar en Binance"):
            if monto_mov > 0:
                cambio = monto_mov if "Entrada" in tipo_mov else -monto_mov
                binance_data["saldo_actual"] += cambio
                binance_data["movimientos"].append({
                    "fecha": str(date.today()),
                    "tipo": tipo_mov,
                    "monto": cambio,
                    "descripcion": desc_mov.strip() or tipo_mov
                })
                guardar_binance(binance_data)
                st.success("✅ ¡Registrado!")
                st.rerun()

    if binance_data.get("movimientos"):
        st.dataframe(pd.DataFrame(binance_data["movimientos"]))

# ---------------------------------------------------------
# 6. CUENTAS POR COBRAR (CUOTAS) - CÁLCULO EXACTO EN DÓLAR BCV
# ---------------------------------------------------------
elif menu == "📋 Cuentas por Cobrar (Cuotas)":
    st.subheader("📋 Cuentas Pendientes por Cobrar (Venta por Cuotas)")
    
    cuotas_pendientes = [v for v in ventas if v.get("estado") == "CUOTAS (Pendiente)"]
    
    if not cuotas_pendientes:
        st.success("🎉 ¡Excelente! No hay cuentas pendientes por cobrar.")
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
                st.write(f"**Total Venta:** ${total_bcv_ref:.2f} dólar BCV")
                
                cuotas_detalle = v.get('detalle_cuotas', [])
                
                resta_bcv = sum(c.get('monto_estimado_bcv', 0) - c.get('monto_pagado_bcv', 0) for c in cuotas_detalle if not c.get('pagada', False))
                
                st.markdown(f"🔴 **Resta por cobrar:** **${resta_bcv:.2f} dólar BCV**")
                
                st.markdown("**Desglose de Cuotas y Abonos:**")
                for c in cuotas_detalle:
                    nro_c = c['nro']
                    monto_est_bcv = c.get('monto_estimado_bcv', 0)
                    monto_pag_bcv = c.get('monto_pagado_bcv', 0)
                    deuda_cuota_bcv = monto_est_bcv - monto_pag_bcv
                    fecha_c = c['fecha']
                    pagada_c = c.get('pagada', False)
                    
                    if pagada_c:
                        st.markdown(f"✅ ~~Cuota {nro_c} (Vence: {fecha_c}) | Pagada~~ **[PAGADA]**")
                    else:
                        st.markdown(f"⏳ **Cuota {nro_c}:** Vence el {fecha_c} (Resta: ${deuda_cuota_bcv:.2f} dólar BCV)")
                        
                        with st.expander(f"Registrar abono / pago Cuota #{nro_c}"):
                            key_abono_bcv = f"abono_bcv_{idx_v}_v{v['id_venta']}_c{nro_c}"
                            key_btn_conf = f"btn_conf_{idx_v}_v{v['id_venta']}_c{nro_c}"

                            abono_bcv = st.number_input(f"Monto abonado en dólares BCV:", min_value=0.0, value=float(deuda_cuota_bcv), step=0.5, key=key_abono_bcv)
                            
                            if st.button(f"Aplicar Abono Cuota #{nro_c}", key=key_btn_conf):
                                if abono_bcv <= 0:
                                    st.warning("⚠️ Ingresa un monto válido mayor a 0.")
                                else:
                                    dinero_restante_bcv = abono_bcv
                                    
                                    for idx_cuota in range(nro_c - 1, len(cuotas_detalle)):
                                        cuota_actual = cuotas_detalle[idx_cuota]
                                        if dinero_restante_bcv <= 0:
                                            break
                                        
                                        est_bcv = cuota_actual.get('monto_estimado_bcv', 0)
                                        pag_bcv = cuota_actual.get('monto_pagado_bcv', 0)
                                        deuda_cuota = est_bcv - pag_bcv
                                        
                                        if dinero_restante_bcv >= deuda_cuota:
                                            cuota_actual['monto_pagado_bcv'] = pag_bcv + deuda_cuota
                                            cuota_actual['pagada'] = True
                                            dinero_restante_bcv -= deuda_cuota
                                        else:
                                            cuota_actual['monto_pagado_bcv'] = pag_bcv + dinero_restante_bcv
                                            dinero_restante_bcv = 0.0

                                    tasa_aproximada = total_bcv_ref / v['total_venta_usdt'] if v['total_venta_usdt'] > 0 else 36.5
                                    abono_usdt_equivalente = abono_bcv / tasa_aproximada

                                    binance_data["saldo_actual"] += abono_usdt_equivalente
                                    binance_data["movimientos"].append({
                                        "fecha": str(date.today()),
                                        "tipo": "Entrada USDT (Abono Cuotas)",
                                        "monto": abono_usdt_equivalente,
                                        "descripcion": f"Abono Cuota #{nro_c} (${abono_bcv} dólar BCV) - Cliente: {v['cliente']}"
                                    })
                                    guardar_binance(binance_data)
                                    
                                    if all(item.get('pagada', False) for item in cuotas_detalle):
                                        v['estado'] = "PAGADO"
                                        st.success(f"✅ ¡Venta #{v['id_venta']} saldada por completo!")
                                    else:
                                        st.success(f"✅ ¡Abono de ${abono_bcv:.2f} dólar BCV registrado con éxito!")

                                    guardar_datos(ARCHIVO_VENTAS, ventas)
                                    st.rerun()

            with col3:
                if st.button(f"Marcar Todo Pagado #{v['id_venta']}", key=f"pay_all_{idx_v}_v{v['id_venta']}"):
                    cuotas_detalle = v.get('detalle_cuotas', [])
                    for c in cuotas_detalle:
                        c['monto_pagado_bcv'] = c.get('monto_estimado_bcv', 0)
                        c['pagada'] = True
                    v['estado'] = "PAGADO"
                    guardar_datos(ARCHIVO_VENTAS, ventas)
                    st.success(f"¡Venta #{v['id_venta']} marcada como pagada!")
                    st.rerun()

# ---------------------------------------------------------
# 7. HISTORIAL, FACTURACIÓN & FINANZAS
# ---------------------------------------------------------
elif menu == "📊 Historial, Facturación & Finanzas":
    st.subheader("📊 Historial General & Finanzas")
    if not ventas:
        st.info("No hay ventas registradas todavía.")
    else:
        df_ventas = pd.DataFrame(ventas)
        st.dataframe(df_ventas[['id_venta', 'cliente', 'producto', 'cantidad', 'estado', 'fecha_entrega', 'cuotas', 'total_venta_usdt', 'total_venta_bcv', 'ganancia_usdt']])
        
        total_acum_usdt = df_ventas['total_venta_usdt'].sum()
        total_acum_bcv = df_ventas.get('total_venta_bcv', pd.Series([0]*len(df_ventas))).sum()
        total_ganancias = df_ventas['ganancia_usdt'].sum()
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Venta Total ($ USDT)", f"${total_acum_usdt:.2f}")
        col2.metric("Venta Total (dólar BCV)", f"${total_acum_bcv:.2f}")
        col3.metric("Ganancias Totales", f"${total_ganancias:.2f}")
