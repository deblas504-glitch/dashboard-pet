import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(layout="wide", page_title="PVD LOGÍSTICA - Dashboard")

AZUL_BARRA = "#002d5a" 
MAGENTA = "#b5006a"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@700&display=swap');
    html, body, [class*="st-"] {{
        font-family: "Franklin Gothic Demi Cond", "Franklin Gothic Medium Cond", "Arial Narrow", sans-serif;
    }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_BARRA}; }}
    [data-testid="stSidebar"] * {{ color: white !important; font-family: "Franklin Gothic Demi Cond", sans-serif; }}
    h1, h2, h3 {{ font-family: "Franklin Gothic Demi Cond", sans-serif !important; font-weight: bold; }}
    div[data-testid="stDataFrame"] > div {{ overflow-x: auto; }}
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
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat_i': [21.88, 30.84, 26.04, 19.83, 16.75, 28.63, 19.43, 27.05, 19.24, 24.02, 19.35, 21.01, 17.43, 20.09, 20.65, 19.70, 18.92, 21.50, 25.68, 17.07, 19.04, 20.58, 19.18, 22.15, 24.80, 29.07, 17.84, 23.73, 19.31, 19.17, 20.96, 22.77],
        'lon_i': [-102.28, -115.28, -111.66, -90.53, -93.12, -106.06, -99.13, -101.70, -103.72, -104.65, -99.10, -101.25, -99.54, -98.76, -103.34, -101.18, -99.23, -104.89, -100.31, -96.72, -98.20, -100.38, -88.47, -100.98, -107.39, -110.96, -92.61, -99.14, -98.23, -96.13, -89.59, -102.58]
    }
    df_coords = pd.DataFrame(coords)
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 4. FUNCIÓN LIQUID FILL
def draw_liquid_fill(percent):
    level = 100 - percent
    return f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 260px;">
        <div style="width: 200px; height: 200px; border-radius: 50%; border: 6px solid {AZUL_BARRA}; position: relative; overflow: hidden; background: #f0f0f0;">
            <div style="position: absolute; width: 200%; height: 200%; top: {level}%; left: -50%; background: {MAGENTA}; border-radius: 40%; animation: wave_animation 5s linear infinite;"></div>
            <div style="position: absolute; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-family: 'Franklin Gothic Demi Cond', sans-serif; font-size: 42px; font-weight: bold; color: {'white' if percent > 55 else AZUL_BARRA}; z-index: 10;">
                {percent:.1f}%
            </div>
        </div>
    </div>
    <style> @keyframes wave_animation {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }} </style>
    """

# 5. MENÚ LATERAL (Gestión de Inventario primero)
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    menu = st.radio("Sección del Sistema:", ["📦 Gestión de Inventario", "✨ Nuevas Campañas", "📊 Análisis 360"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 6. VISTA: GESTIÓN DE INVENTARIO (PRIMERA VENTANA)
if menu == "📦 Gestión de Inventario":
    st.title("📦 Gestión de Inventario")
    
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1: 
        sel_alm = st.selectbox("Almacén", ["Todas"] + sorted(df_master['Nombre'].unique().tolist()))
    with r1c2: 
        search_t = st.text_input("Buscador Descripción / SKU", placeholder="Escribe para buscar...")

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1: 
        sel_cl = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))
    with r2c2: 
        sel_ca = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with r2c3: 
        sel_cn = st.selectbox("Canal", ["Todas"] + sorted(df_master['Canal'].unique().tolist()))

    df_t = df_master.copy()
    if sel_alm != "Todas": df_t = df_t[df_t['Nombre'] == sel_alm]
    if search_t: df_t = df_t[df_t['Descripción'].str.contains(search_t, case=False, na=False) | df_t['código'].str.contains(search_t, case=False, na=False)]
    if sel_cl != "Todas": df_t = df_t[df_t['Clasificación'] == sel_cl]
    if sel_ca != "Todas": df_t = df_t[df_t['Campaña'] == sel_ca]
    if sel_cn != "Todas": df_t = df_t[df_t['Canal'] == sel_cn]

    # --- ORDEN ESTRICTO DE COLUMNAS (C, D, E, F, H, I, J, K, L, M) ---
    cols_t = [
        'código',             # C
        'Descripción',        # D
        'Disponible',             # E
        'Apartados',              # F
        'Nombre',      # H
        'Canal',            # I
        'Clasificación', # J
        'Campaña',          # K
        'Estado de material',         # L
        'Unidad'              # M
    ]
    
    # Solo mostrar si existen en el DF
    cols_validas = [c for c in cols_t if c in df_t.columns]

    st.dataframe(df_t[cols_validas], use_container_width=True, hide_index=True)
    st.download_button("📥 Reporte CSV", df_t[cols_validas].to_csv(index=False).encode('utf-8'), "inventario.csv", "text/csv")

# 7. VISTA: NUEVAS CAMPAÑAS
elif menu == "✨ Nuevas Campañas":
    st.title("✨ Catálogo Visual de Lanzamientos")
    search_cat = st.text_input("🔍 Buscar por SKU o Descripción", placeholder="Ej: MAR100...")
    nuevas = ["Todas"] + sorted([c for c in df_master['Campaña'].unique() if "2026" in str(c) or "NOVA" in str(c)])
    sel_new = st.selectbox("Filtrar Campaña:", nuevas)
    
    df_cat = df_master.copy()
    if sel_new != "Todas": df_cat = df_cat[df_cat['Campaña'] == sel_new]
    if search_cat: df_cat = df_cat[df_cat['Descripción'].str.contains(search_cat, case=False, na=False) | df_cat['código'].str.contains(search_cat, case=False, na=False)]

    st.markdown("---")
    if not df_cat.empty:
        cols_grid = st.columns(3)
        for index, (i, row) in enumerate(df_cat.iterrows()):
            with cols_grid[index % 3]:
                with st.container(border=True):
                    sku_limpio = str(row['código']).strip()
                    ruta_img = None
                    for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
                        path_p = os.path.join("IMAGENES", f"{sku_limpio}{ext}")
                        if os.path.exists(path_p): ruta_img = path_p; break
                    
                    if ruta_img: st.image(ruta_img, use_container_width=True)
                    else: st.image("https://via.placeholder.com/300x200?text=SIN+FOTO", use_container_width=True)
                    
                    st.markdown(f"### {row['Descripción']}")
                    st.write(f"**SKU:** `{sku_limpio}`")
                    ci1, ci2 = st.columns(2)
                    ci1.metric("Disp.", f"{row['Disponible']:,.0f}")
                    ci2.metric("Apart.", f"{row['Apartados']:,.0f}")
                    if st.button("➕ Agregar", key=f"btn_{sku_limpio}_{index}"): st.success("Agregado")

# 8. VISTA: ANÁLISIS 360
else:
    st.title("Dashboard de análisis de inventario")
    c1, c2 = st.columns(2)
    with c1: canal = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with c2: camp = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    
    df_f = df_master.copy()
    if canal != "Todos": df_f = df_f[df_f['Canal'] == canal]
    if camp != "Todas": df_f = df_f[df_f['Campaña'] == camp]

    total_g = df_master['Disponible'].sum()
    total_f = df_f['Disponible'].sum()
    porc = (total_f / total_g) * 100 if total_g > 0 else 0
    st.components.v1.html(draw_liquid_fill(porc), height=280)
    st.markdown(f"<div style='text-align:center; padding:45px; background:{MAGENTA}; border-radius:15px; color:white;'><h1 style='font-size: 80px;'>{total_f:,.0f}</h1></div>", unsafe_allow_html=True)