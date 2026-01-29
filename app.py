import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO SOPHISTICATED
st.set_page_config(layout="wide", page_title="Mars-Pet Logística")

# Paleta Mars-Petcare Premium
MARS_BLUE = "#002d5a"  # Azul profundo corporativo
MARS_ORANGE = "#e65100" # Naranja vibrante para acentos
BG_LIGHT = "#f8f9fa"    # Fondo gris muy claro
TEXT_DARK = "#212121"

# Inyección de CSS para diseño sofisticado
st.markdown(f"""
    <style>
    .main {{ background-color: {BG_LIGHT}; }}
    .stMetric {{ 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    div[data-testid="stMetricValue"] {{ color: {MARS_BLUE}; font-weight: bold; }}
    .stSidebar {{ background-color: white !important; border-right: 1px solid #eee; }}
    h1, h2, h3 {{ color: {MARS_BLUE}; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 3. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/ea/Mars_Petcare_logo.svg", width=150) # Logo Mars
    st.title("Control de Activos")
    menu = st.radio("Sección:", ["Análisis de Inventario", "Tabla de Inventario"])
    st.markdown("---")
    
    if menu == "Análisis de Inventario":
        canal_global = st.selectbox("Canal Principal", ["Global"] + sorted(df_master['Canal'].unique().tolist()))
    else:
        canal_global = "Global"

# 4. VISTA: ANÁLISIS DE INVENTARIO
if menu == "Análisis de Inventario":
    st.title(f"📊 Dashboard de Operaciones: {canal_global}")
    df_f = df_master.copy()
    if canal_global != "Global":
        df_f = df_master[df_master['Canal'] == canal_global]

    # KPI con estilo Premium
    total_u = df_f['Total'].sum()
    st.metric(label="Inventario Total Disponible", value=f"{total_u:,.0f} Unidades")

    c1, c2 = st.columns(2)
    with c1:
        st.write("#### 🗺️ Cobertura Geográfica")
        df_mapa = df_f.groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(
            df_mapa, lat="lat", lon="lon", size="Total", color="Total",
            color_continuous_scale=[MARS_BLUE, MARS_ORANGE],
            size_max=35, zoom=3.8, mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
        st.plotly_chart(fig_map, use_container_width=True)

    with c2:
        st.write("#### 📈 Inventario por Almacén")
        df_bar = df_f.groupby('Nombre')['Total'].sum().reset_index().sort_values('Total', ascending=True)
        fig_bar = px.bar(
            df_bar, x="Total", y="Nombre", orientation='h',
            color="Total", color_continuous_scale=[MARS_BLUE, MARS_ORANGE],
            template="plotly_white", text_auto='.2s'
        )
        fig_bar.update_layout(showlegend=False, height=450)
        st.plotly_chart(fig_bar, use_container_width=True)

# 5. VISTA: TABLA DE INVENTARIO (LIMPIA CON COLUMNA R)
else:
    st.title("📋 Inventario Maestro")
    
    # Filtros refinados
    f1, f2, f3, f4 = st.columns(4)
    with f1: sel_c = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with f2: sel_a = st.selectbox("Almacén", ["Todos"] + sorted(df_master['Nombre'].unique().tolist()))
    with f3: sel_p = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f4: sel_l = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))

    df_tabla = df_master.copy()
    if sel_c != "Todos": df_tabla = df_tabla[df_tabla['Canal'] == sel_c]
    if sel_a != "Todos": df_tabla = df_tabla[df_tabla['Nombre'] == sel_a]
    if sel_p != "Todas": df_tabla = df_tabla[df_tabla['Campaña'] == sel_p]
    if sel_l != "Todas": df_tabla = df_tabla[df_tabla['Clasificación'] == sel_l]

    # Selección de columnas: C, D, E, H, I, J, K, L, R, Q (Total)
    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16]
    cols_visibles = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
    
    # Tabla con estilo minimalista
    st.dataframe(df_tabla[cols_visibles].style.format(precision=0), use_container_width=True, hide_index=True)
    
    # Botón de descarga sofisticado
    csv = df_tabla[cols_visibles].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte Ejecutivo (CSV)", 
        data=csv, 
        file_name="inventario_mars_pet.csv", 
        mime="text/csv"
    )