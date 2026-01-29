import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA Y TEMA MAGENTA
st.set_page_config(layout="wide", page_title="Control PET - Premium Dashboard")

# Paleta de Colores
MAGENTA_MARS = "#b5006a"
DARK_NAVY = "#002d5a"
BG_LIGHT = "#f8f9fa"

# Inyección de CSS para pestañas y controles sofisticados
st.markdown(f"""
    <style>
    .main {{ background-color: {BG_LIGHT}; }}
    
    /* Estilo de las Pestañas (Tabs) */
    button[data-baseweb="tab"] {{
        color: #666 !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }}
    button[aria-selected="true"] {{
        color: {MAGENTA_MARS} !important;
        border-bottom: 3px solid {MAGENTA_MARS} !important;
    }}

    /* Estilo de Métricas (KPIs) */
    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid {MAGENTA_MARS};
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS (GOOGLE SHEETS)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Coordenadas (Mantenemos la lógica interna para el mapa)
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 3. INTERFAZ POR PESTAÑAS (TABS)
tab1, tab2, tab3 = st.tabs(["📊 Canal Global", "📋 Lista de Activos", "📑 Tabla de Inventario"])

with tab1:
    st.title("Dashboard Estratégico Global")
    total_u = df_master['Total'].sum()
    st.metric("Inventario Total Disponible", f"{total_u:,.0f} Unidades")
    
    # Mapa con nueva paleta
    df_mapa = df_master.groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
    fig_map = px.scatter_mapbox(
        df_mapa, lat="lat", lon="lon", size="Total", color="Total",
        color_continuous_scale=[DARK_NAVY, MAGENTA_MARS],
        size_max=40, zoom=3.8, mapbox_style="carto-positron"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
    st.plotly_chart(fig_map, use_container_width=True)

with tab2:
    st.title("Ranking por Almacén")
    df_bar = df_master.groupby('Nombre')['Total'].sum().reset_index().sort_values('Total', ascending=True)
    fig_bar = px.bar(
        df_bar, x="Total", y="Nombre", orientation='h',
        color="Total", color_continuous_scale=[DARK_NAVY, MAGENTA_MARS],
        template="plotly_white", text_auto='.2s'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.title("Gestión Detallada de Inventario")
    
    # SOLUCIÓN AL ERROR: Cambiar 'Almacén' por 'Nombre'
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_a = st.selectbox("Filtrar Almacén", ["Todas"] + sorted(df_master['Nombre'].unique().tolist()))
    with f2:
        sel_c = st.selectbox("Filtrar Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f3:
        sel_n = st.selectbox("Filtrar Canal", ["Todas"] + sorted(df_master['Canal'].unique().tolist()))

    # Aplicación de Filtros
    df_f = df_master.copy()
    if sel_a != "Todas": df_f = df_f[df_f['Nombre'] == sel_a]
    if sel_c != "Todas": df_f = df_f[df_f['Campaña'] == sel_c]
    if sel_n != "Todas": df_f = df_f[df_f['Canal'] == sel_n]

    # SELECCIÓN DE COLUMNAS (C, D, E, H, I, J, K, L, R, Q)
    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16] 
    cols = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
    
    st.dataframe(df_f[cols], use_container_width=True, hide_index=True)
    
    # Botón de Descarga
    csv = df_f[cols].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Reporte Ejecutivo", csv, "reporte_magenta.csv", "text/csv")