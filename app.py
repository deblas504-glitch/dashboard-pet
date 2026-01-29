import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="Control PET - Dashboard 360")

# Paleta Corporativa
MAGENTA = "#b5006a"
AZUL_MARS = "#002d5a"

# 2. ESTILO CSS (Sidebar y Proporciones)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa; }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_MARS} !important; }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label {{ color: white !important; }}
    .stSelectbox label {{ color: {AZUL_MARS} !important; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE DATOS
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

# 4. SIDEBAR
with st.sidebar:
    st.title("📂 Control PET")
    menu = st.radio("Sección:", ["📊 Análisis de Red", "📋 Tabla Maestra"])

# 5. ANÁLISIS DE RED (3 Gráficos en una fila)
if menu == "📊 Análisis de Red":
    st.title("Visualización Estratégica 360°")
    
    # Filtros superiores
    a1, a2 = st.columns(2)
    with a1: ana_canal = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with a2: ana_campana = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))

    df_ana = df_master.copy()
    if ana_canal != "Todos": df_ana = df_ana[df_ana['Canal'] == ana_canal]
    if ana_campana != "Todas": df_ana = df_ana[df_ana['Campaña'] == ana_campana]

    st.metric("Total Unidades Seleccionadas", f"{df_ana['Total'].sum():,.0f}")

    # --- FILA DE 3 COLUMNAS ---
    c1, c2, c3 = st.columns(3)

    with c1:
        st.write("#### 🗺️ Mapa Geográfico")
        df_mapa = df_ana.groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(df_mapa, lat="lat", lon="lon", size="Total", color="Total",
                                    color_continuous_scale=[AZUL_MARS, MAGENTA], size_max=25, zoom=3.0, mapbox_style="carto-positron")
        fig_map.update_layout(height=450, margin={"r":5,"t":0,"l":5,"b":0}, showlegend=False)
        st.plotly_chart(fig_map, use_container_width=True)

    with c2:
        st.write("#### 📈 Ranking Almacén")
        df_bar = df_ana.groupby('Nombre')['Total'].sum().reset_index().sort_values('Total', ascending=True)
        fig_bar = px.bar(df_bar, x="Total", y="Nombre", orientation='h', color="Total", 
                         color_continuous_scale=[AZUL_MARS, MAGENTA], template="plotly_white")
        fig_bar.update_layout(height=450, showlegend=False, margin={"r":5,"t":0,"l":5,"b":0})
        st.plotly_chart(fig_bar, use_container_width=True)

    with c3:
        st.write("#### 🫧 Concentración Campaña")
        df_bubble = df_ana.groupby(['Nombre', 'Campaña'])['Total'].sum().reset_index()
        fig_bubble = px.scatter(df_bubble, x="Nombre", y="Campaña", size="Total", color="Total",
                                color_continuous_scale=[AZUL_MARS, MAGENTA], size_max=40, template="plotly_white")
        fig_bubble.update_layout(height=450, showlegend=False, margin={"r":5,"t":0,"l":5,"b":0})
        st.plotly_chart(fig_bubble, use_container_width=True)

# 6. TABLA MAESTRA
else:
    st.title("Gestión de Inventario Maestro")
    f1, f2, f3, f4 = st.columns(4)
    with f1: sel_c = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with f2: sel_a = st.selectbox("Almacén", ["Todos"] + sorted(df_master['Nombre'].unique().tolist()))
    with f3: sel_p = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f4: sel_l = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))

    df_f = df_master.copy()
    if sel_c != "Todos": df_f = df_f[df_f['Canal'] == sel_c]
    if sel_a != "Todos": df_f = df_f[df_f['Nombre'] == sel_a]
    if sel_p != "Todas": df_f = df_f[df_f['Campaña'] == sel_p]
    if sel_l != "Todas": df_f = df_f[df_f['Clasificación'] == sel_l]

    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 16] 
    cols = [df_master.columns[i] for i in indices if i < len(df_master.columns)]
    st.dataframe(df_f[cols], use_container_width=True, hide_index=True, height=500)