import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_echarts import st_echarts
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="Control PET - PVD Logística", page_icon="📊")

# Colores PVD
MAGENTA_PVD = "#b5006a"
AZUL_PVD = "#002d5a"

# 2. ESTILO CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #fcfcfc; }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_PVD} !important; }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label {{ color: white !important; }}
    .stMetric {{ 
        background-color: white; 
        border-radius: 15px; 
        border-left: 10px solid {MAGENTA_PVD}; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); 
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE DATOS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # CORRECCIÓN DE SINTAXIS AQUÍ
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 4. SIDEBAR CON LOGO PVD
with st.sidebar:
    if os.path.exists("logo_PVD.png"):
        st.image("logo_PVD.png", use_container_width=True)
    else:
        st.title("PVD LOGÍSTICA")
    st.markdown("---")
    menu = st.radio("Sección del Sistema:", ["📊 Análisis 360", "📋 Gestión de Inventario"])

# 5. VISTA: ANÁLISIS 360
if menu == "📊 Análisis 360":
    st.title("Dashboard de análisis de Inventario")
    
    a1, a2 = st.columns(2)
    with a1: ana_canal = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with a2: ana_campana = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))

    df_ana = df_master.copy()
    if ana_canal != "Todos": df_ana = df_ana[df_ana['Canal'] == ana_canal]
    if ana_campana != "Todas": df_ana = df_ana[df_ana['Campaña'] == ana_campana]

    # --- FILTRO DE AGUA ---
    col_met, col_niv = st.columns([1, 2])
    total_u = df_ana['Total'].sum()
    porc = min(total_u / 1000000, 1.0) # Basado en 1M de capacidad

    with col_met:
        st.metric("Inventario Total Seleccionado", f"{total_u:,.0f} U")
    
    with col_niv:
        # Gráfica de agua con ola suave
        liquid_opt = {
            "series": [{
                "type": 'liquidFill',
                "data": [porc, porc - 0.05],
                "color": [MAGENTA_PVD, "#d6007d"],
                "radius": '90%',
                "amplitude": 10,
                "backgroundStyle": {"color": "#eee"},
                "outline": {"borderDistance": 2, "itemStyle": {"borderWidth": 4, "borderColor": AZUL_PVD}},
                "label": {"fontSize": 30, "color": AZUL_PVD, "formatter": f"{porc*100:.1f}%"}
            }]
        }
        st_echarts(liquid_opt, height="200px")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("#### 🗺️ Cobertura")
        df_mapa = df_ana.groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(df_mapa, lat="lat", lon="lon", size="Total", color="Estado",
                                    color_discrete_sequence=px.colors.qualitative.Prism, 
                                    size_max=25, zoom=3.0, mapbox_style="carto-positron")
        fig_map.update_layout(height=400, margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
        st.plotly_chart(fig_map, use_container_width=True)
    with c2:
        st.write("#### 📈 Ranking Almacenes")
        df_bar = df_ana.groupby('Nombre')['Total'].sum().reset_index().sort_values('Total', ascending=True)
        fig_bar = px.bar(df_bar, x="Total", y="Nombre", orientation='h', color="Nombre", 
                         color_discrete_sequence=px.colors.qualitative.G10, template="plotly_white")
        fig_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    with c3:
        st.write("#### 🫧 Campaña vs Canal")
        df_bubble = df_ana.groupby(['Campaña', 'Canal'])['Total'].sum().reset_index()
        fig_bubble = px.scatter(df_bubble, x="Campaña", y="Canal", size="Total", color="Campaña",
                                color_discrete_sequence=px.colors.qualitative.Vivid, 
                                size_max=45, template="plotly_white")
        fig_bubble.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bubble, use_container_width=True)

# 6. GESTIÓN DE INVENTARIO
else:
    st.title("Gestión de Inventario Maestro")
    col_alm = 'Nombre' if 'Nombre' in df_master.columns else df_master.columns[3]
    f1, f2, f3, f4 = st.columns(4)
    with f1: s_c = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with f2: s_a = st.selectbox("Almacén", ["Todos"] + sorted(df_master[col_alm].unique().tolist()))
    with f3: s_p = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f4: s_l = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))

    df_f = df_master.copy()
    if s_c != "Todos": df_f = df_f[df_f['Canal'] == s_c]
    if s_a != "Todos": df_f = df_f[df_f[col_alm] == s_a]
    if s_p != "Todas": df_f = df_f[df_f['Campaña'] == s_p]
    if s_l != "Todas": df_f = df_f[df_f['Clasificación'] == s_l]

    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16] 
    cols_vis = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
    st.dataframe(df_f[cols_vis], use_container_width=True, hide_index=True, height=500)