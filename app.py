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

# Ruta del logo de la marca
LOGO_PATH = os.path.join(CARPETA_FOTOS, "logo_luisstore.jpg")

def guardar_logo_desde_imagen():
    # Guardamos la imagen del logo adjuntada si no existe localmente
    if not os.path.exists(LOGO_PATH):
        # Intentamos copiar o guardar si viene en el contexto
        pass

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

# Configuración de la página web para PC y teléfono
st.set_page_config(page_title="LUIS STORE | Control & Ventas", layout="wide")

# Estilos CSS con los tonos oscuros y dorados del logo (Estética Streetwear Premium)
st.markdown("""
    <style>
        .stButton>button {
            background-color: #1a1a1a;
            color: #d4af37;
            border-radius: 8px;
            border: 1px solid #d4af37;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #d4af37;
            color: #1a1a1a;
            border-color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True)

# Cargar datos actuales
inventario = cargar_datos(ARCHIVO_INVENTARIO)
ventas = cargar_datos(ARCHIVO_VENTAS)
binance_data = cargar_binance()

# Barra lateral con el Logo y Navegación
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("## 🔥 LUIS STORE")
    
    st.markdown("---")
    menu = st.selectbox("Menú Principal", [
        "🛒 Registrar Venta", 
        "📦 Módulo de Inventario (Tallas y Stock)", 
        "➕ Agregar Nuevo Producto / Talla", 
        "✏️ Editar / Eliminar / Fotos (Inventario)", 
        "📋 Cuentas por Cobrar (Fiados)", 
        "🟡 Fondos Disponibles en Binance",
        "📊 Historial, Facturación & Finanzas"
    ])

st.title("🔥 LUIS STORE — Control de Inventario & Ventas")
st.markdown("Administra tus prendas, tallas, stock, precios en USDT, BCV, Binance y genera recibos digitales.")

# ---------------------------------------------------------
# 1. REGISTRAR VENTA
# ---------------------------------------------------------
if menu == "🛒 Registrar Venta":
    st.subheader("🛒 Registrar una Venta o Salida")
    
    if not inventario:
        st.warning("⚠️ No hay productos en el inventario para vender. Ve primero a 'Agregar Nuevo Producto / Talla'.")
    else:
        opciones_prod = [f"ID {i}: {p['nombre']} - Talla: {p['talla']} (Stock: {p['stock']} | USDT: ${p['precio_usdt']} | $ BCV: ${p.get('precio_bcv', 0)})" for i, p in enumerate(inventario)]
        seleccion = st.selectbox("Selecciona el producto y talla:", opciones_prod)
        idx = int(seleccion.split(":")[0].replace("ID", "").strip())
        
        producto = inventario[idx]
        
        if producto.get('foto') and os.path.exists(producto['foto']):
            st.image(producto['foto'], width=150, caption=f"{producto['nombre']} - Talla {producto['talla']}")
        
        cantidad = st.number_input("Cantidad a vender:", min_value=1, max_value=max(1, producto['stock']), step=1)
        
        tipo_pago = st.radio("Condición de pago:", ["Contado (Pagado de una vez)", "Fiado (Quedó pendiente)"])
        
        cliente = "Contado"
        fecha_entrega = str(date.today())
        cuotas = 1
        detalle_cuotas = []
        
        precio_final_usdt = producto['precio_usdt']
        precio_final_bcv = producto.get('precio_bcv', 0)
        
        if "Fiado" in tipo_pago:
            cliente = st.text_input("Nombre del Cliente (para la cuenta por cobrar):", value="")
            if not cliente.strip():
                cliente = "Cliente General"
            
            st.markdown("### 💰 Precios Especiales para Fiado")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                precio_final_usdt = st.number_input("Precio en USDT (Fiado):", min_value=0.0, value=float(producto['precio_usdt']), step=0.5)
            with col_p2:
                precio_final_bcv = st.number_input("Precio a $ BCV (Fiado):", min_value=0.0, value=float(producto.get('precio_bcv', 0)), step=0.5)
            
            st.markdown("### 📅 Fechas y Cuotas del Fiado")
            fecha_entrega_obj = st.date_input("Fecha de Entrega del Producto:", value=date.today())
            fecha_entrega = str(fecha_entrega_obj)
                
            cuotas = st.selectbox("Número de Cuotas (Máximo 4):", [1, 2, 3, 4])
            
            total_v_usdt_calc = precio_final_usdt * cantidad
            monto_por_cuota = total_v_usdt_calc / cuotas

            st.markdown("📝 **Indica la fecha límite para cada cuota:**")
            for c in range(1, cuotas + 1):
                f_cuota = st.date_input(f"Fecha límite cuota #{c}:", value=date.today(), key=f"cuota_f_{c}")
                detalle_cuotas.append({
                    "nro": c,
                    "monto_estimado": monto_por_cuota,
                    "monto_pagado": 0.0,
                    "fecha": str(f_cuota),
                    "pagada": False
                })

        if st.button("Confirmar y Registrar Venta"):
            if producto['stock'] < cantidad:
                st.error("❌ Stock insuficiente para completar la venta.")
            else:
                producto['stock'] -= cantidad
                
                inversion_unitaria = producto['costo_usdt'] + producto['envio_usdt']
                inversion_total = inversion_unitaria * cantidad
                
                total_venta_usdt = precio_final_usdt * cantidad
                total_venta_bcv = precio_final_bcv * cantidad
                
                ganancia_usdt = total_venta_usdt - inversion_total
                reinversion_usdt = inversion_total
                
                estado = "FIADO (Pendiente)" if "Fiado" in tipo_pago else "PAGADO"
                
                if not detalle_cuotas:
                    detalle_cuotas = [{
                        "nro": 1,
                        "monto_estimado": total_venta_usdt,
                        "monto_pagado": total_venta_usdt,
                        "fecha": fecha_entrega,
                        "pagada": True
                    }]
                    
                    binance_data["saldo_actual"] += total_venta_usdt
                    binance_data["movimientos"].append({
                        "fecha": str(date.today()),
                        "tipo": "Entrada USDT (Venta Contado)",
                        "monto": total_venta_usdt,
                        "descripcion": f"Venta Contado: {producto['nombre']} (Talla {producto['talla']} x{cantidad})"
                    })
                    guardar_binance(binance_data)

                venta_reg = {
                    "id_venta": len(ventas) + 1,
                    "producto": producto['nombre'],
                    "talla": producto['talla'],
                    "cantidad": cantidad,
                    "precio_compra_usdt": producto['costo_usdt'],
                    "precio_envio_usdt": producto['envio_usdt'],
                    "precio_usdt_aplicado": precio_final_usdt,
                    "precio_bcv_aplicado": precio_final_bcv,
                    "total_venta_usdt": total_venta_usdt,
                    "total_venta_bcv": total_venta_bcv,
                    "ganancia_usdt": ganancia_usdt,
                    "reinversion_usdt": reinversion_usdt,
                    "estado": estado,
                    "cliente": cliente,
                    "fecha_entrega": fecha_entrega,
                    "cuotas": cuotas,
                    "detalle_cuotas": detalle_cuotas
                }
                
                ventas.append(venta_reg)
                guardar_datos(ARCHIVO_INVENTARIO, inventario)
                guardar_datos(ARCHIVO_VENTAS, ventas)
                
                st.success("✅ ¡Venta registrada exitosamente y sincronizada con Binance!")
                st.metric("Total Venta ($ USDT)", f"${total_venta_usdt:.2f}")
                st.metric("Total Venta ($ a BCV)", f"${total_venta_bcv:.2f}")
                
                # Mostrar Recibo Digital con los datos de Luis Store
                st.markdown("---")
                st.subheader("🧾 Recibo Digital para WhatsApp")
                recibo_texto = f"""
----------------------------------------
            🔥 LUIS STORE 🔥
        Tienda Online | Cabimas, Zulia
----------------------------------------
Nota de Venta / Factura #{venta_reg['id_venta']}
Fecha: {fecha_entrega}
Cliente: {cliente}
----------------------------------------
Producto: {producto['nombre']}
Talla: {producto['talla']}
Cantidad: {cantidad} unidad(es)
----------------------------------------
Precio Unitario: ${precio_final_usdt:.2f} USDT (${precio_final_bcv:.2f} BCV)
TOTAL A PAGAR: ${total_venta_usdt:.2f} USDT (${total_venta_bcv:.2f} BCV)
Estado: {estado}
----------------------------------------
📞 Pedidos: 0412-4543304
📷 Instagram: luisstore.ve
tiktok: @luisstorecabimas
----------------------------------------
¡Gracias por tu compra en LUIS STORE!
----------------------------------------
                """
                st.code(recibo_texto, language="text")

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
                st.write(f"**Costo Proveedor:** ${p['costo_usdt']:.2f} | **Envío:** ${p['envio_usdt']:.2f}")
                st.write(f"**Precio USDT:** ${p['precio_usdt']:.2f} | **Precio $ BCV:** ${p.get('precio_bcv', 0):.2f}")

# ---------------------------------------------------------
# 3. AGREGAR NUEVO PRODUCTO O TALLA AL INVENTARIO
# ---------------------------------------------------------
elif menu == "➕ Agregar Nuevo Producto / Talla":
    st.subheader("➕ Registrar Ropa, Talla, Costos, Precios y Foto")
    
    with st.form("form_producto"):
        nombre = st.text_input("Nombre de la prenda (Ej: Oversize Streetwear, Bermuda, Short)")
        talla = st.selectbox("Selecciona la Talla", ["S", "M", "L", "XL", "XXL", "Única", "30", "32", "34", "36", "38"])
        costo_usdt = st.number_input("Costo del producto con proveedor (en USDT):", min_value=0.0, step=0.5)
        envio_usdt = st.number_input("Costo de envío unitario (en USDT):", min_value=0.0, step=0.1)
        precio_usdt = st.number_input("Precio en USDT:", min_value=0.0, step=0.5)
        precio_bcv = st.number_input("Precio a $ BCV:", min_value=0.0, step=0.5)
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
            nuevo_precio_usdt = st.number_input("Precio en USDT:", min_value=0.0, value=float(prod_actual['precio_usdt']), step=0.5)
            nuevo_precio_bcv = st.number_input("Precio a $ BCV:", min_value=0.0, value=float(prod_actual.get('precio_bcv', 0)), step=0.5)
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
    st.metric("💰 Saldo Actual en Binance", f"${saldo_actual:,.2f} USDT")
    
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

# ---------------------------------------------------------
# 6. CUENTAS POR COBRAR (FIADOS)
# ---------------------------------------------------------
elif menu == "📋 Cuentas por Cobrar (Fiados)":
    st.subheader("📋 Cuentas Pendientes por Cobrar (Fiados)")
    
    fiados = []
    for v in ventas:
        if v.get("estado") == "FIADO (Pendiente)":
            cuotas_detalle = v.get("detalle_cuotas", [])
            if any(not c.get("pagada", False) for c in cuotas_detalle):
                fiados.append(v)
    
    if not fiados:
        st.success("🎉 ¡Excelente! No hay deudas pendientes por cobrar (todo está pagado).")
    else:
        for v in fiados:
            st.markdown(f"---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**ID Venta:** #{v['id_venta']}")
                st.write(f"**Cliente:** {v['cliente']}")
                st.write(f"**Entrega:** {v.get('fecha_entrega', 'N/A')}")
            with col2:
                st.write(f"**Prenda:** {v['producto']} (Talla: {v['talla']} x{v['cantidad']})")
                st.write(f"**Total Venta:** ${v['total_venta_usdt']:.2f} USDT | ${v.get('total_venta_bcv', 0):.2f} BCV")
                
                cuotas_detalle = v.get('detalle_cuotas', [])
                total_pagado_usdt = sum(c.get('monto_pagado', 0) for c in cuotas_detalle)
                resta_usdt = v['total_venta_usdt'] - total_pagado_usdt
                
                tasa_bcv_ref = v.get('total_venta_bcv', 0) / v['total_venta_usdt'] if v['total_venta_usdt'] > 0 else 0
                resta_bcv = resta_usdt * tasa_bcv_ref
                
                st.markdown(f"🔴 **Resta por cobrar:** **${resta_usdt:.2f} USDT** | **${resta_bcv:.2f} BCV**")
                
                st.markdown("**Desglose de Cuotas y Abonos:**")
                for c in cuotas_detalle:
                    nro_c = c['nro']
                    monto_pag = c.get('monto_pagado', 0)
                    fecha_c = c['fecha']
                    pagada_c = c.get('pagada', False)
                    
                    if pagada_c:
                        st.markdown(f"✅ ~~Cuota {nro_c} (Vence: {fecha_c}) | Abonado: **${monto_pag:.2f}**~~ **[PAGADA]**")
                    else:
                        st.markdown(f"⏳ **Cuota {nro_c}:** Vence el {fecha_c}")
                        
                        with st.expander(f"Registrar abono / pago Cuota #{nro_c}"):
                            abono_usdt = st.number_input(f"Monto abonado en USDT:", min_value=0.0, value=float(resta_usdt), step=0.5, key=f"inp_abono_usdt_{v['id_venta']}_{nro_c}")
                            abono_bcv = st.number_input(f"Monto abonado en $ BCV:", min_value=0.0, value=float(abono_usdt * tasa_bcv_ref), step=0.5, key=f"inp_abono_bcv_{v['id_venta']}_{nro_c}")
                            
                            if st.button(f"Aplicar Abono Cuota #{nro_c}", key=f"btn_conf_{v['id_venta']}_{nro_c}"):
                                if abono_usdt <= 0:
                                    st.warning("⚠️ Ingresa un monto de abono válido mayor a 0.")
                                else:
                                    dinero_restante = abono_usdt
                                    
                                    for idx_cuota in range(nro_c - 1, len(cuotas_detalle)):
                                        cuota_actual = cuotas_detalle[idx_cuota]
                                        if dinero_restante <= 0:
                                            break
                                        
                                        deuda_cuota = cuota_actual['monto_estimado'] - cuota_actual.get('monto_pagado', 0.0)
                                        
                                        if dinero_restante >= deuda_cuota:
                                            cuota_actual['monto_pagado'] = cuota_actual.get('monto_pagado', 0.0) + deuda_cuota
                                            cuota_actual['pagada'] = True
                                            dinero_restante -= deuda_cuota
                                        else:
                                            cuota_actual['monto_pagado'] = cuota_actual.get('monto_pagado', 0.0) + dinero_restante
                                            dinero_restante = 0.0
                                    
                                    binance_data["saldo_actual"] += abono_usdt
                                    binance_data["movimientos"].append({
                                        "fecha": str(date.today()),
                                        "tipo": "Entrada USDT (Abono Fiado)",
                                        "monto": abono_usdt,
                                        "descripcion": f"Abono Cuota #{nro_c} - Cliente: {v['cliente']} (Venta #{v['id_venta']})"
                                    })
                                    guardar_binance(binance_data)
                                    
                                    if all(item.get('pagada', False) for item in cuotas_detalle):
                                        v['estado'] = "PAGADO"
                                        st.success(f"¡Excelente! La venta #{v['id_venta']} ha sido saldada por completo y sumada a Binance.")
                                    else:
                                        st.success(f"¡Abono de ${abono_usdt:.2f} USDT (${abono_bcv:.2f} BCV) registrado y sumado a Binance!")
                                    
                                    guardar_datos(ARCHIVO_VENTAS, ventas)
                                    st.rerun()

            with col3:
                if st.button(f"Marcar Todo Pagado #{v['id_venta']}", key=f"pay_all_{v['id_venta']}"):
                    cuotas_detalle = v.get('detalle_cuotas', [])
                    total_deuda_restante = sum(c.get('monto_estimado', 0) - c.get('monto_pagado', 0) for c in cuotas_detalle if not c.get('pagada', False))
                    
                    for c in cuotas_detalle:
                        c['monto_pagado'] = c.get('monto_estimado', 0)
                        c['pagada'] = True
                    v['estado'] = "PAGADO"
                    
                    if total_deuda_restante > 0:
                        binance_data["saldo_actual"] += total_deuda_restante
                        binance_data["movimientos"].append({
                            "fecha": str(date.today()),
                            "tipo": "Entrada USDT (Pago Total Fiado)",
                            "monto": total_deuda_restante,
                            "descripcion": f"Saldado completo Venta #{v['id_venta']} - Cliente: {v['cliente']}"
                        })
                        guardar_binance(binance_data)

                    guardar_datos(ARCHIVO_VENTAS, ventas)
                    st.success(f"¡Venta #{v['id_venta']} marcada como pagada y saldo agregado a Binance!")
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
        st.dataframe(df_ventas[['id_venta', 'cliente', 'producto', 'talla', 'cantidad', 'estado', 'fecha_entrega', 'cuotas', 'total_venta_usdt', 'total_venta_bcv', 'ganancia_usdt', 'reinversion_usdt']])
        
        st.markdown("---")
        st.subheader("🧾 Generar Recibo Digital para WhatsApp")
        opciones_factura = [f"Venta #{v['id_venta']} — Cliente: {v['cliente']} — {v['producto']} (Talla {v['talla']})" for v in ventas]
        sel_factura = st.selectbox("Selecciona la venta para ver/copiar su recibo:", opciones_factura)
        
        if sel_factura:
            id_sel = int(sel_factura.split("—")[0].replace("Venta #", "").strip())
            v_encontrada = next((v for v in ventas if v['id_venta'] == id_sel), None)
            
            if v_encontrada:
                recibo_generado = f"""
----------------------------------------
            🔥 LUIS STORE 🔥
        Tienda Online | Cabimas, Zulia
----------------------------------------
Nota de Venta / Factura #{v_encontrada['id_venta']}
Fecha: {v_encontrada['fecha_entrega']}
Cliente: {v_encontrada['cliente']}
----------------------------------------
Producto: {v_encontrada['producto']}
Talla: {v_encontrada['talla']}
Cantidad: {v_encontrada['cantidad']} unidad(es)
----------------------------------------
TOTAL A PAGAR: ${v_encontrada['total_venta_usdt']:.2f} USDT 
Equivalente BCV: ${v_encontrada.get('total_venta_bcv', 0):.2f} BCV
Estado: {v_encontrada['estado']}
----------------------------------------
📞 Pedidos: 0412-4543304
📷 Instagram: luisstore.ve
tiktok: @luisstorecabimas
----------------------------------------
¡Gracias por tu compra en LUIS STORE!
----------------------------------------
                """
                st.code(recibo_generado, language="text")
                st.info("💡 Copia este texto y envíaselo directamente al cliente por WhatsApp.")

        total_acum_usdt = df_ventas['total_venta_usdt'].sum()
        total_acum_bcv = df_ventas.get('total_venta_bcv', pd.Series([0]*len(df_ventas))).sum()
        total_ganancias = df_ventas['ganancia_usdt'].sum()
        total_reinversion = df_ventas['reinversion_usdt'].sum()
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Venta Total ($ USDT)", f"${total_acum_usdt:.2f}")
        col2.metric("Venta Total ($ BCV)", f"${total_acum_bcv:.2f}")
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
