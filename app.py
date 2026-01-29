import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="Control PET - Sistema Maestro")

# Paleta Corporativa Mars-Pet
MAGENTA = "#b5006a"
AZUL_MARS = "#002d5a"
BLANCO = "#ffffff"

# 2. INYECCIÓN DE ESTILO (CSS) PARA FORZAR COLORES
st.markdown(f"""
    <style>
    /* Fondo de la aplicación */
    .stApp {{
        background-color: #f4f4f4;
    }}
    
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

    /* Estilo de las Pestañas (Tabs) */
    button[data-baseweb="tab"] {{
        color: #555 !important;
        font-weight: 600 !important;
        background-color: transparent !important;
    }}
    
    /* Pestaña activa en Magenta */
    button[aria-selected="true"] {{
        color: {MAGENTA} !important;
        border-bottom: 3px solid {MAGENTA} !important;
    }}

    /* Métricas (KPIs) con acento Magenta */
    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-top: 5px solid {MAGENTA};
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}

    /* Botones de descarga en Magenta */
    .stButton>button {{
        background-color: {MAGENTA} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE DATOS (GOOGLE SHEETS)
# Usando tu ID de hoja actual
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

# 4. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.title("📂 Control PET")
    st.write("Bienvenido al sistema logístico.")
    st.markdown("---")
    # Los Radio Buttons en el sidebar ahora son blancos por el CSS arriba
    menu_principal = st.radio("Sección:", ["Análisis de Red", "Gestión de Inventario"])

# 5. ESTRUCTURA DE PESTAÑAS (TABS)
if menu_principal == "Análisis de Red":
    st.title("📊 Análisis Estratégico Global")
    
    # KPIs en la parte superior
    total_u = df_master['Total'].sum()
    st.metric("Inventario Total en Sistema", f"{total_u:,.0f} U")

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 🗺️ Mapa de Distribución")
        df_mapa = df_master.groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(
            df_mapa, lat="lat", lon="lon", size="Total", color="Total",
            color_continuous_scale=[AZUL_MARS, MAGENTA],
            size_max=35, zoom=3.8, mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
        st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        st.write("#### 📈 Ranking de Almacenes")
        # Usamos 'Nombre' para evitar el KeyError
        df_bar = df_master.groupby('Nombre')['Total'].sum().reset_index().sort_values('Total', ascending=True)
        fig_bar = px.bar(
            df_bar, x="Total", y="Nombre", orientation='h',
            color="Total", color_continuous_scale=[AZUL_MARS, MAGENTA],
            template="plotly_white", text_auto='.2s'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.title("📋 Gestión de Inventario Maestro")
    
    # Pestañas Estilizadas
    tab_tabla, tab_filtros = st.tabs(["📑 Vista de Datos", "🔍 Filtros Avanzados"])

    with tab_filtros:
        f1, f2, f3 = st.columns(3)
        with f1:
            # Corrección: Columna 'Nombre' en lugar de 'Almacén'
            sel_a = st.selectbox("Almacén", ["Todos"] + sorted(df_master['Nombre'].unique().tolist()))
        with f2:
            sel_c = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
        with f3:
            sel_n = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))

    with tab_tabla:
        # Aplicación de filtros
        df_f = df_master.copy()
        if sel_a != "Todos": df_f = df_f[df_f['Nombre'] == sel_a]
        if sel_c != "Todas": df_f = df_f[df_f['Campaña'] == sel_c]
        if sel_n != "Todos": df_f = df_f[df_f['Canal'] == sel_n]

        # SELECCIÓN DE COLUMNAS: C, D, E, H, I, J, K, L, R, Q (Total)
        # Columna R (índice 17) colocada antes del Total (índice 16)
        indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16] 
        cols_visibles = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
        
        st.dataframe(df_f[cols_visibles], use_container_width=True, hide_index=True)
        
        # Botón de Descarga
        csv = df_f[cols_visibles].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar Reporte Magenta", csv, "inventario_final.csv", "text/csv")