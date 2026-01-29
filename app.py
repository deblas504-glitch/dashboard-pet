import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="Control PET - Sistema Maestro")

# Paleta Corporativa Mars-Pet
MAGENTA = "#b5006a"
AZUL_MARS = "#002d5a"
BLANCO = "#ffffff"

# 2. ESTILO CSS PARA PROPORCIONES Y COLORES (Sidebar Azul, Filtros Magenta)
st.markdown(f"""
    <style>
    /* Fondo general */
    .stApp {{ background-color: #f4f4f4; }}
    
    /* Sidebar (Menú Lateral) en Azul Mars */
    [data-testid="stSidebar"] {{
        background-color: {AZUL_MARS} !important;
    }}
    
    /* Texto en Sidebar blanco */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] label {{
        color: {BLANCO} !important;
    }}

    /* Ajuste de Proporción de la Tabla */
    .stDataFrame {{ 
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        background-color: white;
    }}

    /* Estilo de los Selectores (Filtros) */
    .stSelectbox label {{ 
        color: {AZUL_MARS} !important; 
        font-weight: bold; 
        font-size: 15px; 
    }}

    /* Botones y Radio Buttons */
    .stButton>button {{
        background-color: {MAGENTA} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold;
    }}
    
    /* Métrica (KPI) */
    div[data-testid="stMetricValue"] {{
        color: {MAGENTA} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE DATOS (GOOGLE SHEETS)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Coordenadas por Estado para el Mapa
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 4. BARRA LATERAL (SIDEBAR) - NAVEGACIÓN
with st.sidebar:
    st.title("📂 Control PET")
    st.markdown("---")
    menu_principal = st.radio("Sección del Sistema:", ["📊 Análisis de Red", "📋 Gestión de Inventario"])

# 5. CONTENIDO PRINCIPAL
if menu_principal == "📊 Análisis de Red":
    st.title("Dashboard Estratégico de Activos")
    
    total_u = df_master['Total'].sum()
    st.metric("Inventario Global Disponible", f"{total_u:,.0f} U")

    c1, c2 = st.columns(2)
    with c1:
        st.write("#### 🗺️ Cobertura Nacional")
        df_mapa = df_master.groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(
            df_mapa, lat="lat", lon="lon", size="Total", color="Total",
            color_continuous_scale=[AZUL_MARS, MAGENTA],
            size_max=35, zoom=3.5, mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
        st.plotly_chart(fig_map, use_container_width=True)

    with c2:
        st.write("#### 📈 Top Almacenes por Volumen")
        # Corrección: Usamos 'Nombre' para evitar el KeyError
        df_bar = df_master.groupby('Nombre')['Total'].sum().reset_index().sort_values('Total', ascending=True)
        fig_bar = px.bar(
            df_bar, x="Total", y="Nombre", orientation='h',
            color="Total", color_continuous_scale=[AZUL_MARS, MAGENTA],
            template="plotly_white", text_auto='.2s'
        )
        fig_bar.update_layout(showlegend=False, height=450)
        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.title("Inventario Maestro de PET")
    
    # BOTONES DE SELECCIÓN (FILTROS)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_c = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with f2:
        # Usamos 'Nombre' para Almacén para evitar errores
        sel_a = st.selectbox("Almacén", ["Todos"] + sorted(df_master['Nombre'].unique().tolist()))
    with f3:
        sel_p = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f4:
        sel_l = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))

    # Aplicación de Filtros
    df_f = df_master.copy()
    if sel_c != "Todos": df_f = df_f[df_f['Canal'] == sel_c]
    if sel_a != "Todos": df_f = df_f[df_f['Nombre'] == sel_a]
    if sel_p != "Todas": df_f = df_f[df_f['Campaña'] == sel_p]
    if sel_l != "Todas": df_f = df_f[df_f['Clasificación'] == sel_l]

    # SELECCIÓN DE COLUMNAS (C, D, E, H, I, J, K, L, R, Q)
    # Columna R (17) antes de Total (16)
    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16] 
    cols_visibles = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
    
    # Tabla con altura controlada para evitar desproporción
    st.dataframe(df_f[cols_visibles], use_container_width=True, hide_index=True, height=500)
    
    # Botón de Descarga
    st.download_button(
        label="📥 Descargar Reporte Personalizado",
        data=df_f[cols_visibles].to_csv(index=False).encode('utf-8'),
        file_name="inventario_pet_magenta.csv",
        mime="text/csv"
    )