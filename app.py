import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA Y TEMA
st.set_page_config(layout="wide", page_title="Control PET - Premium Dashboard")

# Definición de la Paleta de Colores
MAGENTA_PRIMARY = "#b5006a"
DARK_NAVY = "#002d5a"
BG_OFF_WHITE = "#f8f9fa"

# Inyección de CSS para personalizar Pestañas y Controles
st.markdown(f"""
    <style>
    /* Fondo general */
    .main {{ background-color: {BG_OFF_WHITE}; }}
    
    /* Estilo de las Pestañas (Tabs) */
    button[data-baseweb="tab"] {{
        color: #666 !important;
        font-weight: 500;
    }}
    button[aria-selected="true"] {{
        color: {MAGENTA_PRIMARY} !important;
        border-bottom-color: {MAGENTA_PRIMARY} !important;
    }}

    /* Personalización de los Selectboxes y controles de entrada */
    div[data-baseweb="select"] > div {{
        border-color: #eee !important;
    }}
    div[data-baseweb="select"]:focus-within {{
        border-color: {MAGENTA_PRIMARY} !important;
    }}

    /* Estilo de las métricas (KPIs) */
    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid {MAGENTA_PRIMARY};
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    div[data-testid="stMetricValue"] {{
        color: {DARK_NAVY};
    }}

    /* Botones de descarga y acciones */
    .stButton>button {{
        background-color: {MAGENTA_PRIMARY} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS (Mismo ID de tu Google Sheet)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Lógica de limpieza de columnas según tu estructura anterior
    return df

df_master = load_data()

# 3. NAVEGACIÓN POR PESTAÑAS (TABS)
# Implementamos las pestañas que pediste con el estilo magenta
tab1, tab2, tab3 = st.tabs(["📊 Canal Global", "📋 Lista de Activos", "📑 Tabla de Inventario"])

with tab1:
    st.subheader("Análisis Estratégico Global")
    # Aquí insertarías tus métricas y mapas actuales
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Inventario", f"{df_master['Total'].sum():,.0f}")

with tab2:
    st.subheader("Visualización de Activos por Estado")
    # Espacio para el gráfico de barras o lista visual

with tab3:
    st.subheader("Gestión Detallada de Inventario")
    
    # Filtros de cabecera con el nuevo tema
    f1, f2, f3 = st.columns(3)
    with f1: st.selectbox("Almacén", ["Todas"] + sorted(df_master['Almacén'].unique().tolist()))
    with f2: st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f3: st.selectbox("Canal", ["Todas"] + sorted(df_master['Canal'].unique().tolist()))

    # Selección de columnas (C, D, E, H, I, J, K, L, R, Q)
    # Ajustado a los índices que definimos anteriormente
    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16] 
    cols = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
    
    st.dataframe(df_master[cols], use_container_width=True, hide_index=True)