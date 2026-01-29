import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA Y TEMA VISUAL
st.set_page_config(layout="wide", page_title="Mars-Pet Logística")

# Paleta de Colores
MAGENTA_MARS = "#b5006a"
AZUL_MARS = "#002d5a"
FONDO_GRIS = "#f8f9fa"

# Inyección de CSS para menús, pestañas y botones en Magenta
st.markdown(f"""
    <style>
    /* Fondo de la aplicación */
    .main {{ background-color: {FONDO_GRIS}; }}
    
    /* PESTAÑAS (TABS) SUPERIORES */
    button[data-baseweb="tab"] {{
        color: #666 !important;
        font-weight: 500 !important;
    }}
    button[aria-selected="true"] {{
        color: {MAGENTA_MARS} !important;
        border-bottom: 3px solid {MAGENTA_MARS} !important;
    }}

    /* MENÚ LATERAL (SIDEBAR) */
    [data-testid="stSidebar"] {{
        background-color: white !important;
        border-right: 1px solid #eee;
    }}
    /* Color de los Radio Buttons activos */
    div[data-testid="stSidebar"] .st-at {{
        background-color: {MAGENTA_MARS} !important;
    }}

    /* MÉTRICAS Y CONTENEDORES */
    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-top: 4px solid {MAGENTA_MARS};
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}

    /* BOTONES */
    .stButton>button {{
        background-color: {MAGENTA_MARS} !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS (GOOGLE SHEETS)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Coordenadas internas para el mapa
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 3. INTERFAZ DE NAVEGACIÓN
tab1, tab2, tab3 = st.tabs(["📊 Análisis Global", "🚛 Planificación", "📑 Tabla de Inventario"])

# --- TAB 1: ANÁLISIS ---
with tab1:
    st.subheader("Estado General del Inventario")
    total_u = df_master['Total'].sum()
    st.metric("Capacidad Total en Red", f"{total_u:,.0f} Unidades")
    
    # Mapa con paleta Mars (Azul a Magenta)
    df_mapa = df_master.groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
    fig_map = px.scatter_mapbox(
        df_mapa, lat="lat", lon="lon", size="Total", color="Total",
        color_continuous_scale=[AZUL_MARS, MAGENTA_MARS],
        size_max=35, zoom=3.8, mapbox_style="carto-positron"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
    st.plotly_chart(fig_map, use_container_width=True)

# --- TAB 3: TABLA (CON CORRECCIÓN DE COLUMNA 'NOMBRE') ---
with tab3:
    st.subheader("Gestión Operativa")
    
    # Filtros usando la columna correcta 'Nombre'
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_a = st.selectbox("Almacén (Nombre)", ["Todos"] + sorted(df_master['Nombre'].unique().tolist()))
    with f2:
        sel_c = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f3:
        sel_n = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))

    # Aplicación de filtros
    df_f = df_master.copy()
    if sel_a != "Todos": df_f = df_f[df_f['Nombre'] == sel_a]
    if sel_c != "Todas": df_f = df_f[df_f['Campaña'] == sel_c]
    if sel_n != "Todos": df_f = df_f[df_f['Canal'] == sel_n]

    # Selección de columnas: C, D, E, H, I, J, K, L, R, Q (Total)
    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16] 
    cols_visibles = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
    
    st.dataframe(df_f[cols_visibles], use_container_width=True, hide_index=True)