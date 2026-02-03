import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN Y ESTILO ORIGINAL
st.set_page_config(layout="wide", page_title="PVD LOGÍSTICA")

AZUL_BARRA = "#002d5a" 
MAGENTA = "#b5006a"

st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {AZUL_BARRA}; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE ACCESO
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso PVD LOGÍSTICA")
    clave = st.text_input("Contraseña:", type="password")
    if st.button("Entrar"):
        if clave == "12345":
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
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat_i': [21.88, 30.84, 26.04, 19.83, 16.75, 28.63, 19.43, 27.05, 19.24, 24.02, 19.35, 21.01, 17.43, 20.09, 20.65, 19.70, 18.92, 21.50, 25.68, 17.07, 19.04, 20.58, 19.18, 22.15, 24.80, 29.07, 17.84, 23.73, 19.31, 19.17, 20.96, 22.77],
        'lon_i': [-102.28, -115.28, -111.66, -90.53, -93.12, -106.06, -99.13, -101.70, -103.72, -104.65, -99.10, -101.25, -99.54, -98.76, -103.34, -101.18, -99.23, -104.89, -100.31, -96.72, -98.20, -100.38, -88.47, -100.98, -107.39, -110.96, -92.61, -99.14, -98.23, -96.13, -89.59, -102.58]
    }
    df_coords = pd.DataFrame(coords)
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 4. FUNCIÓN LIQUID FILL CORREGIDA (CON OLEAJE REAL)
def draw_liquid_fill(percent):
    # El nivel del agua sube de 100 (vacío) a 0 (lleno)
    level = 100 - percent
    return f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 260px;">
        <div style="width: 200px; height: 200px; border-radius: 50%; border: 6px solid {AZUL_BARRA}; position: relative; overflow: hidden; background: #f0f0f0;">
            <div style="position: absolute; width: 200%; height: 200%; top: {level}%; left: -50%; background: {MAGENTA}; border-radius: 40%; animation: wave_animation 5s linear infinite;">
            </div>
            <div style="position: absolute; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-family: sans-serif; font-size: 42px; font-weight: bold; color: {'white' if percent > 55 else AZUL_BARRA}; z-index: 10;">
                {percent:.1f}%
            </div>
        </div>
    </div>
    <style>
        @keyframes wave_animation {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
    </style>
    """

# 5. MENÚ LATERAL
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    menu = st.radio("Sección:", ["📊 Análisis 360", "📦 Gestión de Inventario"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 6. DASHBOARD ANÁLISIS 360
if menu == "📊 Análisis 360":
    st.title("Dashboard de análisis de inventario")
    c1, c2 = st.columns(2)
    with c1: canal = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with c2: camp = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    
    df_f = df_master.copy()
    if canal != "Todos": df_f = df_f[df_f['Canal'] == canal]
    if camp != "Todas": df_f = df_f[df_f['Campaña'] == camp]

    c_g, c_t = st.columns([1, 2])
    with c_g:
        porc = (df_f['Disponible'].sum() / df_master['Disponible'].sum()) * 100 if df_master['Disponible'].sum() > 0 else 0
        st.components.v1.html(draw_liquid_fill(porc), height=280)
    with c_t:
        st.markdown(f"<div style='text-align:center; padding:45px; background:{MAGENTA}; border-radius:15px; color:white; margin-top:20px;'><p style='margin:0;'>Inventario Disponible</p><h1 style='font-size: 80px; margin:0;'>{df_f['Disponible'].sum():,.0f}</h1></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    # ... (Gráficas se mantienen igual)
    with col1:
        st.write("🗺️ **Cobertura**")
        st.plotly_chart(px.scatter_mapbox(df_f, lat="lat_i", lon="lon_i", size="Disponible", color="Disponible", color_continuous_scale="Viridis", zoom=3, mapbox_style="carto-positron", height=300), use_container_width=True)
    with col2:
        st.write("📊 **Ranking Almacenes**")
        st.plotly_chart(px.bar(df_f.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible'), x="Disponible", y="Nombre", orientation='h', color="Disponible", color_continuous_scale="Blues", height=300), use_container_width=True)
    with col3:
        st.write("🟣 **Campaña vs Canal**")
        st.plotly_chart(px.scatter(df_f, x="Campaña", y="Canal", size="Disponible", color="Canal", height=300), use_container_width=True)

# 7. GESTIÓN DE INVENTARIO
else:
    st.title("📦 Gestión de Inventario")
    
    # FILTROS RESTAURADOS
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1: sel_alm = st.selectbox("Almacén", ["Todas"] + sorted(df_master['Nombre'].unique().tolist()))
    with r1c2: search = st.text_input("Buscador", placeholder="Search...")

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1: sel_cl = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))
    with r2c2: sel_ca = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with r2c3: sel_cn = st.selectbox("Canal", ["Todas"] + sorted(df_master['Canal'].unique().tolist()))

    df_t = df_master.copy()
    if sel_alm != "Todas": df_t = df_t[df_t['Nombre'] == sel_alm]
    if search: df_t = df_t[df_t['Descripción'].str.contains(search, case=False, na=False)]
    if sel_cl != "Todas": df_t = df_t[df_t['Clasificación'] == sel_cl]
    if sel_ca != "Todas": df_t = df_t[df_t['Campaña'] == sel_ca]
    if sel_cn != "Todas": df_t = df_t[df_t['Canal'] == sel_cn]

    cols = ['código', 'Descripción', 'Nombre', 'Canal', 'Clasificación', 'Campaña', 'Estado de material', 'Apartados', 'Disponible']
    st.dataframe(df_t[cols], use_container_width=True, hide_index=True)
    st.download_button("📥 Descargar Reporte", df_t[cols].to_csv(index=False).encode('utf-8'), "inventario.csv", "text/csv")