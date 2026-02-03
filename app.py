import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN Y ESTILO (FRANKLIN GOTHIC)
st.set_page_config(layout="wide", page_title="PVD LOGÍSTICA")

AZUL_BARRA = "#002d5a" 
MAGENTA = "#b5006a"

st.markdown(f"""
    <style>
    html, body, [class*="st-"] {{
        font-family: "Franklin Gothic Demi Cond", "Franklin Gothic Medium Cond", Arial, sans-serif;
    }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_BARRA}; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE ACCESO
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
    # Coordenadas internas para mapas
    coords = {{'Estado': ['Ciudad de México', 'Nuevo León', 'Jalisco'], 'lat_i': [19.43, 25.68, 20.65], 'lon_i': [-99.13, -100.31, -103.34]}}
    df_c = pd.DataFrame(coords)
    return pd.merge(df, df_c, on='Estado', how='left')

df_master = load_data()

# 4. FUNCIÓN LIQUID FILL (OLEAJE)
def draw_liquid_fill(percent):
    level = 100 - percent
    return f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 260px;">
        <div style="width: 200px; height: 200px; border-radius: 50%; border: 6px solid {AZUL_BARRA}; position: relative; overflow: hidden; background: #f0f0f0;">
            <div style="position: absolute; width: 200%; height: 200%; top: {level}%; left: -50%; background: {MAGENTA}; border-radius: 40%; animation: wave_animation 5s linear infinite;"></div>
            <div style="position: absolute; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-family: sans-serif; font-size: 42px; font-weight: bold; color: {'white' if percent > 55 else AZUL_BARRA}; z-index: 10;">
                {percent:.1f}%
            </div>
        </div>
    </div>
    <style> @keyframes wave_animation {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }} </style>
    """

# 5. MENÚ LATERAL (NUEVA SECCIÓN AÑADIDA)
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    menu = st.radio("Sección:", ["📊 Análisis 360", "📦 Gestión de Inventario", "✨ Nuevas Campañas"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 6. VISTA: NUEVAS CAMPAÑAS (NUEVA)
if menu == "✨ Nuevas Campañas":
    st.title("✨ Control de Lanzamientos y Nuevas Campañas")
    
    # Filtrar solo campañas de 2026 o marcadas como "NUEVA"
    nuevas_camps = [c for c in df_master['Campaña'].unique() if "2026" in str(c) or "Q1" in str(c)]
    sel_new = st.multiselect("Seleccionar Lanzamientos:", nuevas_camps, default=nuevas_camps[:1])
    
    df_new = df_master[df_master['Campaña'].isin(sel_new)]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("SKUs en Lanzamiento", len(df_new['código'].unique()))
    c2.metric("Unidades Disponibles", f"{df_new['Disponible'].sum():,.0f}")
    c3.metric("Almacenes con Stock", len(df_new['Nombre'].unique()))

    st.write("### 📈 Despliegue de Inventario por Almacén")
    fig_new = px.bar(df_new, x="Nombre", y="Disponible", color="Clasificación", 
                     barmode="group", template="plotly_white", color_discrete_sequence=[MAGENTA, AZUL_BARRA])
    st.plotly_chart(fig_new, use_container_width=True)

# 7. VISTA: ANÁLISIS 360
elif menu == "📊 Análisis 360":
    st.title("Dashboard de análisis de inventario")
    # ... (Misma lógica del Análisis 360 con el Liquid Fill)
    porc = (df_master['Disponible'].sum() / 1000000) * 100 # Ejemplo de cálculo
    st.components.v1.html(draw_liquid_fill(porc), height=280)

# 8. VISTA: GESTIÓN DE INVENTARIO
else:
    st.title("📦 Gestión de Inventario")
    # Filtros y Tabla con orden C, D, E, F, H, I, J, K, L, Q
    cols = ['código', 'Descripción', 'Nombre', 'Canal', 'Clasificación', 'Campaña', 'Estado de material', 'Apartados', 'Disponible']
    st.dataframe(df_master[cols], use_container_width=True, hide_index=True)
    