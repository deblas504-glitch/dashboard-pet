import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ORIGINAL
st.set_page_config(layout="wide", page_title="PVD LOGÍSTICA - Dashboard")

# Paleta de colores recuperada de las imágenes
AZUL_BARRA = "#002d5a"  # Azul oscuro de la barra lateral
AZUL_GRAFICAS = "#1f77b4" # Azul estándar para barras
VERDE_TABLA = "#d1f2eb"  # Fondo verde claro de la columna Total/Disponible

# Aplicar estilos CSS para la barra lateral y fuentes
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{
        background-color: {AZUL_BARRA};
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    .main {{
        background-color: #ffffff;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE ACCESO (PROTECCIÓN)
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

# 3. CARGA DE DATOS DESDE GOOGLE SHEETS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    df.columns = df.columns.str.strip()
    # Coordenadas por Estado
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.88, 30.84, 26.04, 19.83, 16.75, 28.63, 19.43, 27.05, 19.24, 24.02, 19.35, 21.01, 17.43, 20.09, 20.65, 19.70, 18.92, 21.50, 25.68, 17.07, 19.04, 20.58, 19.18, 22.15, 24.80, 29.07, 17.84, 23.73, 19.31, 19.17, 20.96, 22.77],
        'lon': [-102.28, -115.28, -111.66, -90.53, -93.12, -106.06, -99.13, -101.70, -103.72, -104.65, -99.10, -101.25, -99.54, -98.76, -103.34, -101.18, -99.23, -104.89, -100.31, -96.72, -98.20, -100.38, -88.47, -100.98, -107.39, -110.96, -92.61, -99.14, -98.23, -96.13, -89.59, -102.58]
    }
    df_coords = pd.DataFrame(coords)
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 4. BARRA LATERAL (MENÚ)
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    st.write("---")
    menu = st.radio("Sección del Sistema:", ["📊 Análisis 360", "📦 Gestión de Inventario"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 5. VISTA: ANÁLISIS 360 (VISTA AVANZADA ORIGINAL)
if menu == "📊 Análisis 360":
    st.title("Dashboard de análisis de inventario")
    
    # Filtros horizontales superiores
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        canal_sel = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with c_f2:
        camp_sel = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    
    df_ana = df_master.copy()
    if canal_sel != "Todos": df_ana = df_ana[df_ana['Canal'] == canal_sel]
    if camp_sel != "Todas": df_ana = df_ana[df_ana['Campaña'] == camp_sel]

    # Fila de Indicadores (Gráfica circular y Total)
    c_gauge, c_total = st.columns([1, 2])
    
    with c_gauge:
        # Gráfica de porcentaje circular (Donut)
        total_g = df_master['Disponible'].sum()
        total_f = df_ana['Disponible'].sum()
        porc = (total_f / total_g) * 100 if total_g > 0 else 0
        
        fig_donut = go.Figure(go.Pie(
            values=[porc, 100-porc], hole=.7,
            marker_colors=["#d6006e", "#eeeeee"], # Color resaltado similar a imagen
            textinfo='none'
        ))
        fig_donut.update_layout(
            annotations=[dict(text=f'{porc:.1f}%', x=0.5, y=0.5, font_size=40, showarrow=False)],
            showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c_total:
        st.markdown(f"""
            <div style="text-align:center; padding:40px;">
                <h2 style="color: #555; margin-bottom:0;">Inventario Disponible</h2>
                <h1 style="font-size: 80px; margin-top:0;">{total_f:,.0f}</h1>
            </div>""", unsafe_allow_html=True)

    # Gráficas Inferiores
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("🗺️ **Cobertura**")
        fig_map = px.scatter_mapbox(df_ana, lat="lat", lon="lon", size="Disponible", color="Disponible",
                                    color_continuous_scale="Viridis", zoom=3, mapbox_style="carto-positron")
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=300)
        st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        st.write("📊 **Ranking Almacenes**")
        df_r = df_ana.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible')
        fig_r = px.bar(df_r, x="Disponible", y="Nombre", orientation='h', color="Disponible",
                       color_continuous_scale="Blues")
        fig_r.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0))
        st.plotly_chart(fig_r, use_container_width=True)

    with col3:
        st.write("🟣 **Campaña vs Canal**")
        fig_bubble = px.scatter(df_ana, x="Campaña", y="Canal", size="Disponible", color="Canal")
        fig_bubble.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig_bubble, use_container_width=True)

# 6. VISTA: GESTIÓN DE INVENTARIO (TABLA ORIGINAL)
else:
    st.title("📦 Gestión de Inventario")
    
    # Filtros exactamente como en la imagen adjunta
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1:
        sel_alm = st.selectbox("Almacén", ["Todas"] + sorted(df_master['Nombre'].unique().tolist()))
    with r1c2:
        search = st.text_input("Descripción", placeholder="Search...")

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        sel_clas = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))
    with r2c2:
        sel_camp = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with r2c3:
        sel_can = st.selectbox("Canal", ["Todas"] + sorted(df_master['Canal'].unique().tolist()))

    # Lógica de filtrado
    df_t = df_master.copy()
    if sel_alm != "Todas": df_t = df_t[df_t['Nombre'] == sel_alm]
    if search: df_t = df_t[df_t['Descripción'].str.contains(search, case=False, na=False)]
    if sel_clas != "Todas": df_t = df_t[df_t['Clasificación'] == sel_clas]
    if sel_camp != "Todas": df_t = df_t[df_t['Campaña'] == sel_camp]
    if sel_can != "Todas": df_t = df_t[df_t['Canal'] == sel_can]

    # Orden de columnas: C, D, E, H, I, J, K, L, R, Disponible
    indices = [2, 3, 4, 7, 8, 9, 10, 11, 17, 18]
    cols_finales = [df_master.columns[i] for i in indices if i < len(df_master.columns)]

    # Mostrar tabla con fondo verde claro para la última columna (simulando imagen)
    st.dataframe(df_t[cols_finales], use_container_width=True, hide_index=True)
    