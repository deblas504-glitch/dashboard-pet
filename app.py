import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN Y ESTILO ORIGINAL
st.set_page_config(layout="wide", page_title="PVD LOGÍSTICA")

AZUL_BARRA = "#002d5a" 
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {AZUL_BARRA}; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# 2. ACCESO PROTEGIDO (Clave 12345)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso PVD LOGÍSTICA")
    clave = st.text_input("Contraseña:", type="password")
    if st.button("Entrar"):
        if clave == "12345": # Clave definida por el usuario
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# 3. CARGA DE DATOS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_excel(URL)
    df.columns = df.columns.str.strip()
    # Coordenadas internas para el mapa
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat_mapa': [21.88, 30.84, 26.04, 19.83, 16.75, 28.63, 19.43, 27.05, 19.24, 24.02, 19.35, 21.01, 17.43, 20.09, 20.65, 19.70, 18.92, 21.50, 25.68, 17.07, 19.04, 20.58, 19.18, 22.15, 24.80, 29.07, 17.84, 23.73, 19.31, 19.17, 20.96, 22.77],
        'lon_mapa': [-102.28, -115.28, -111.66, -90.53, -93.12, -106.06, -99.13, -101.70, -103.72, -104.65, -99.10, -101.25, -99.54, -98.76, -103.34, -101.18, -99.23, -104.89, -100.31, -96.72, -98.20, -100.38, -88.47, -100.98, -107.39, -110.96, -92.61, -99.14, -98.23, -96.13, -89.59, -102.58]
    }
    df_coords = pd.DataFrame(coords)
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 4. BARRA LATERAL
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    menu = st.radio("Sección del Sistema:", ["📊 Análisis 360", "📦 Gestión de Inventario"])

# 5. VISTA: GESTIÓN DE INVENTARIO (FILTRADO POR COLUMNAS C, D, E, F, H, I, J, K, L, Q)
if menu == "📦 Gestión de Inventario":
    st.title("📦 Gestión de Inventario")
    
    # Filtros originales
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1: sel_alm = st.selectbox("Almacén", ["Todas"] + sorted(df_master['Nombre'].unique().tolist()))
    with r1c2: search = st.text_input("Descripción", placeholder="Search...")

    df_t = df_master.copy()
    if sel_alm != "Todas": df_t = df_t[df_t['Nombre'] == sel_alm]
    if search: df_t = df_t[df_t['Descripción'].str.contains(search, case=False, na=False)]

    # --- LISTA DEFINITIVA DE COLUMNAS (Nombres basados en tus letras) ---
    columnas_finales = [
        'código',         # C
        'Descripción',    # D
        'Nombre',         # E
        'Canal',          # F
        'Clasificación',  # H
        'Campaña',        # I
        'Estado de material', # J
        'Apartados',      # K (Movida por usuario)
        'Disponible',     # L (Q original)
        # La columna Q es la que ahora contiene el dato final
    ]

    # Validar que las columnas existan antes de mostrar
    cols_a_mostrar = [c for c in columnas_finales if c in df_t.columns]
    
    st.dataframe(df_t[cols_a_mostrar], use_container_width=True, hide_index=True)

# 6. VISTA: ANÁLISIS 360
else:
    st.title("Dashboard de análisis de inventario")
    # ... (Se mantiene la lógica de gráficas usando 'lat_mapa' y 'lon_mapa')