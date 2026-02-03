import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN Y ESTILO ORIGINAL
st.set_page_config(layout="wide", page_title="PVD LOGÍSTICA")

AZUL_BARRA = "#002d5a" 
MAGENTA = "#b5006a"

# CSS para la barra lateral y fuentes
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {AZUL_BARRA}; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE ACCESO (Clave: 12345)
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
    # Coordenadas internas para el mapa
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat_interna': [21.88, 30.84, 26.04, 19.83, 16.75, 28.63, 19.43, 27.05, 19.24, 24.02, 19.35, 21.01, 17.43, 20.09, 20.65, 19.70, 18.92, 21.50, 25.68, 17.07, 19.04, 20.58, 19.18, 22.15, 24.80, 29.07, 17.84, 23.73, 19.31, 19.17, 20.96, 22.77],
        'lon_interna': [-102.28, -115.28, -111.66, -90.53, -93.12, -106.06, -99.13, -101.70, -103.72, -104.65, -99.10, -101.25, -99.54, -98.76, -103.34, -101.18, -99.23, -104.89, -100.31, -96.72, -98.20, -100.38, -88.47, -100.98, -107.39, -110.96, -92.61, -99.14, -98.23, -96.13, -89.59, -102.58]
    }
    df_coords = pd.DataFrame(coords)
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 4. FUNCIÓN PARA EL FILTRO DE AGUA (LIQUID FILL)
def liquid_fill_gauge(percent):
    # Genera el efecto de olas con SVG animado
    wave_top = 100 - percent
    html_code = f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 250px;">
        <div style="width: 200px; height: 200px; border-radius: 50%; border: 5px solid {AZUL_BARRA}; position: relative; overflow: hidden; background: #eee;">
            <div style="position: absolute; width: 100%; top: {wave_top}%; height: 100%; background: {MAGENTA}; transition: top 1s ease-in-out;">
                <svg viewBox="0 0 500 150" preserveAspectRatio="none" style="position: absolute; top: -40px; left: 0; width: 200%; height: 50px; animation: move_wave 3s linear infinite;">
                    <path d="M0,100 C150,200 350,0 500,100 L500,0 L0,0 Z" style="stroke: none; fill: {MAGENTA};"></path>
                </svg>
            </div>
            <div style="position: absolute; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-family: Arial; font-size: 40px; font-weight: bold; color: {AZUL_BARRA if percent < 50 else 'white'}; z-index: 10;">
                {percent:.1f}%
            </div>
        </div>
    </div>
    <style>
        @keyframes move_wave {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
    </style>
    """
    return html_code

# 5. BARRA LATERAL
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    menu = st.radio("Sección:", ["📊 Análisis 360", "📦 Gestión de Inventario"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 6. VISTA: ANÁLISIS 360 (CON EFECTO DE AGUA)
if menu == "📊 Análisis 360":
    st.title("Dashboard de análisis de inventario")
    
    c1, c2 = st.columns(2)
    with c1: canal_sel = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with c2: camp_sel = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    
    df_ana = df_master.copy()
    if canal_sel != "Todos": df_ana = df_ana[df_ana['Canal'] == canal_sel]
    if camp_sel != "Todas": df_ana = df_ana[df_ana['Campaña'] == camp_sel]

    # Fila Principal: Filtro de Agua y Total
    c_gauge, c_total = st.columns([1, 2])
    with c_gauge:
        total_g = df_master['Disponible'].sum()
        total_f = df_ana['Disponible'].sum()
        porc = (total_f / total_g) * 100 if total_g > 0 else 0
        st.components.v1.html(liquid_fill_gauge(porc), height=280)

    with c_total:
        st.markdown(f"<div style='text-align:center; padding:45px; background:{MAGENTA}; border-radius:15px; color:white; margin-top:20px;'><p style='margin:0; font-size:20px;'>Inventario Disponible</p><h1 style='font-size: 80px; margin:0;'>{total_f:,.0f}</h1></div>", unsafe_allow_html=True)

    # Gráficas inferiores
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("🗺️ **Cobertura**")
        st.plotly_chart(px.scatter_mapbox(df_ana, lat="lat_interna", lon="lon_interna", size="Disponible", color="Disponible", color_continuous_scale="Viridis", zoom=3, mapbox_style="carto-positron", height=300), use_container_width=True)
    with col2:
        st.write("📊 **Ranking Almacenes**")
        df_r = df_ana.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible')
        st.plotly_chart(px.bar(df_r, x="Disponible", y="Nombre", orientation='h', color="Disponible", color_continuous_scale="Blues", height=300), use_container_width=True)
    with col3:
        st.write("🟣 **Campaña vs Canal**")
        st.plotly_chart(px.scatter(df_ana, x="Campaña", y="Canal", size="Disponible", color="Canal", height=300), use_container_width=True)

# 7. VISTA: GESTIÓN DE INVENTARIO (TABLA LIMPIA)
else:
    st.title("📦 Gestión de Inventario")
    
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1: sel_alm = st.selectbox("Almacén", ["Todas"] + sorted(df_master['Nombre'].unique().tolist()))
    with r1c2: search = st.text_input("Buscador", placeholder="Escribe para buscar...")

    df_t = df_master.copy()
    if sel_alm != "Todas": df_t = df_t[df_t['Nombre'] == sel_alm]
    if search: df_t = df_t[df_t['Descripción'].str.contains(search, case=False, na=False)]

    # Columnas específicas: C, D, E, F, H, I, J, K, L y Q (Solo nombres solicitados)
    columnas_finales = ['código', 'Descripción', 'Nombre', 'Canal', 'Clasificación', 'Campaña', 'Estado de material', 'Apartados', 'Disponible']
    
    st.dataframe(df_t[columnas_finales], use_container_width=True, hide_index=True)
    