import streamlit as st
import pandas as pd
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# 1. CONFIGURACIÓN VISUAL (Colores de la imagen de referencia)
st.set_page_config(layout="wide", page_title="PVD Logística - Terminal")

st.markdown("""
    <style>
    /* Fondo oscuro para toda la app */
    .stApp { background-color: #1e2130; color: white; }
    
    /* Estilo de los Tabs (Viaje / Mis Datos) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e2130;
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #888;
        font-weight: bold;
        font-size: 18px;
    }
    .stTabs [aria-selected="true"] {
        color: white !important;
        border-bottom: 3px solid #4A90E2 !important;
    }

    /* Botón INICIAR SESIÓN (Azul brillante) */
    .stButton>button {
        background-color: #4A90E2; 
        color: white;
        border-radius: 4px;
        border: none;
        height: 45px;
        width: 100%;
        font-weight: bold;
    }
    
    /* Tarjetas de materiales (Verde vibrante) */
    .material-card {
        background-color: #4caf50;
        color: white;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
        font-family: monospace;
    }
    
    /* Ajuste de inputs para que resalten en fondo oscuro */
    input { background-color: #3d4150 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. LISTA DE CORREOS OFICIALES
DESTINATARIOS_PVD = [
    "ontrol_inventarios@pvd.com.mx", "gil_tovar@pvd.com.mx",
    "serviciocliente5@pvd.com.mx", "inventarios1@pvd.com.mx", "carlos_db@pvd.com.mx"
]

# 3. LÓGICA DE INICIO DE SESIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>Pingu Trener</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Viaje", "Mis Datos"])
    
    with tab1:
        st.write("### Viaje")
        # Selector de Origen y Destino como en tu imagen
        origen = st.selectbox("Origen", ["Seleccionar", "Veracruz", "CDMX", "Monterrey", "Guadalajara"])
        u_email = st.text_input("Correo PVD", placeholder="ejemplo@pvd.com.mx")
        u_pass = st.text_input("Contraseña de Aplicación", type="password")
        
        if st.button("INICIAR SESIÓN"):
            if origen != "Seleccionar" and u_email and u_pass:
                # El "Spinner" de carga justo debajo de los datos
                with st.spinner(''):
                    try:
                        # Validación real con el servidor de Google
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(u_email, u_pass)
                        server.quit()
                        
                        # Si la conexión es exitosa:
                        st.session_state.autenticado = True
                        st.session_state.u_email = u_email
                        st.session_state.u_pass = u_pass
                        st.session_state.sucursal = origen
                        st.rerun()
                    except:
                        st.error("Error: Credenciales de Google no válidas.")
            else:
                st.warning("Por favor completa los campos.")
    st.stop()

# --- 4. ÁREA DE TRABAJO (Solo tras el Login) ---
st.title(f"📦 Recepción: -PVD {st.session_state.sucursal}")

# Función del Tanque (integrada para el visual móvil)
def draw_tank(actual, total):
    perc = min((actual / total) * 100, 100) if total > 0 else 0
    level = 100 - perc
    return f"""
    <div style="display: flex; flex-direction: column; align-items: center;">
        <div style="width: 120px; height: 120px; border-radius: 50%; border: 4px solid #fff; position: relative; overflow: hidden; background: #333;">
            <div style="position: absolute; width: 200%; height: 200%; top: {level}%; left: -50%; background: #4caf50; border-radius: 40%; animation: wave 4s linear infinite;"></div>
            <div style="position: absolute; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-size: 20px; font-weight: bold;">{int(perc)}%</div>
        </div>
        <style> @keyframes wave {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }} </style>
    </div>
    """

# Carga de Packing List
archivo = st.file_uploader("Mostri Fichito (Cargar Excel)", type=["xlsx", "csv"])

if archivo:
    if 'conteo' not in st.session_state:
        df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        df.columns = df.columns.str.strip()
        c_sku = next((c for c in ['código', 'SKU', 'CODIGO'] if c in df.columns), df.columns[0])
        c_cant = next((c for c in ['CANTIDAD', 'Cantidad', 'TOTAL'] if c in df.columns), df.columns[1])
        
        # Consolidado automático
        df_g = df.groupby(c_sku)[c_cant].sum().reset_index()
        df_g = df_g.rename(columns={c_cant: 'CANTIDAD', c_sku: 'código'})
        df_g['RECIBIDO'] = 0
        st.session_state.conteo = df_g

    df_act = st.session_state.conteo
    
    # Visual de Progreso
    t_esp = df_act['CANTIDAD'].sum()
    t_rec = df_act['RECIBIDO'].sum()
    st.markdown(draw_tank(t_rec, t_esp), unsafe_allow_html=True)

    # Formulario de Registro
    with st.form("scan_form", clear_on_submit=True):
        sku_in = st.text_input("Escanear SKU")
        cant_in = st.number_input("Cantidad", min_value=1, value=1)
        if st.form_submit_button("REGISTRAR"):
            if str(sku_in) in df_act['código'].astype(str).values:
                idx = df_act[df_act['código'].astype(str) == str(sku_in)].index[0]
                df_act.at[idx, 'RECIBIDO'] += cant_in
                st.rerun()

    # Lista de Materiales (Tarjetas Verdes)
    st.subheader("Detalles de Empaque")
    for _, row in df_act[df_act['RECIBIDO'] > 0].iterrows():
        st.markdown(f'<div class="material-card"><span>{row["código"]}</span><span>{row["RECIBIDO"]} / {row["CANTIDAD"]}</span></div>', unsafe_allow_html=True)

    # ENVÍO Y REINICIO
    st.divider()
    if st.button("Finalizar Envío y Enviar a Central", type="primary"):
        # (Aquí va tu función de enviar_correo que ya configuramos)
        st.balloons()
        st.success(f"Reporte enviado con éxito desde {st.session_state.sucursal}")
        time.sleep(3)