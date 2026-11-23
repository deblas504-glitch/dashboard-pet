import re
import unicodedata

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
        if clave == "MARSPET2026":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# 3. CARGA DE DATOS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# Cada almacén se ubica por la ciudad que trae en su nombre (columna 'Nombre').
# clave (minúsculas, sin acentos) -> (Ciudad, Estado, latitud, longitud)
# Si abren un almacén nuevo, solo agreguen una línea aquí.
UBICACIONES = {
    "acapulco":        ("Acapulco",         "Guerrero",          16.85,  -99.88),
    "vallejo":         ("Ciudad de México", "Ciudad de México",  19.49,  -99.15),
    "chihuahua":       ("Chihuahua",        "Chihuahua",         28.63, -106.07),
    "cuernavaca":      ("Cuernavaca",       "Morelos",           18.92,  -99.23),
    "culiacan":        ("Culiacán",         "Sinaloa",           24.80, -107.39),
    "guadalajara":     ("Guadalajara",      "Jalisco",           20.67, -103.35),
    "hermosillo":      ("Hermosillo",       "Sonora",            29.07, -110.96),
    "leon":            ("León",             "Guanajuato",        21.12, -101.68),
    "merida":          ("Mérida",           "Yucatán",           20.97,  -89.62),
    "mexicali":        ("Mexicali",         "Baja California",   32.62, -115.45),
    "monterrey":       ("Monterrey",        "Nuevo León",        25.69, -100.32),
    "morelia":         ("Morelia",          "Michoacán",         19.70, -101.19),
    "oaxaca":          ("Oaxaca",           "Oaxaca",            17.07,  -96.73),
    "puebla":          ("Puebla",           "Puebla",            19.04,  -98.21),
    "queretaro":       ("Querétaro",        "Querétaro",         20.59, -100.39),
    "san luis potosi": ("San Luis Potosí",  "San Luis Potosí",   22.15, -100.98),
    "tampico":         ("Tampico",          "Tamaulipas",        22.23,  -97.86),
    "tijuana":         ("Tijuana",          "Baja California",   32.51, -117.04),
    "toluca":          ("Toluca",           "Estado de México",  19.29,  -99.66),
    "torreon":         ("Torreón",          "Coahuila",          25.54, -103.41),
    "veracruz":        ("Veracruz",         "Veracruz",          19.17,  -96.13),
    "villahermosa":    ("Villahermosa",     "Tabasco",           17.99,  -92.93),
}
_PATRONES = [(re.compile(rf"\b{re.escape(k)}\b"), v) for k, v in UBICACIONES.items()]
_SIN_UBICACION = (None, None, float("nan"), float("nan"))


def _norm(valor):
    """Texto comparable: sin acentos, minúsculas, sin espacios extra. Vacío -> ''."""
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode("ascii")
    return " ".join(texto.lower().split())


def ubicar_almacen(nombre):
    """'GUADALAJARA PVD' -> ('Guadalajara', 'Jalisco', 20.67, -103.35)"""
    texto = _norm(nombre)
    for patron, datos in _PATRONES:
        if patron.search(texto):
            return datos
    return _SIN_UBICACION


@st.cache_data(ttl=30)
def load_data():
    try:
        df = pd.read_excel(URL)
        df.columns = df.columns.astype(str).str.strip()

        for col in ["Disponible", "Apartados"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        nombres = df["Nombre"] if "Nombre" in df.columns else pd.Series("", index=df.index)
        ubic = pd.DataFrame(
            [ubicar_almacen(n) for n in nombres],
            columns=["_ciudad", "_estado", "lat_i", "lon_i"],
            index=df.index,
        )

        # Lo que ya esté capturado en el Sheet se respeta; el almacén solo llena los vacíos.
        for col, aux in [("Ciudad", "_ciudad"), ("Estado", "_estado")]:
            if col in df.columns:
                actual = df[col].astype("object")
                vacio = actual.isna() | (actual.astype(str).str.strip() == "")
                df[col] = actual.where(~vacio, ubic[aux])
            else:
                df[col] = ubic[aux]

        # Coordenadas = ciudad del almacén (donde físicamente está el material)
        df["lat_i"] = ubic["lat_i"].astype(float)
        df["lon_i"] = ubic["lon_i"].astype(float)

        sin_ubicar = sorted(nombres[df["lat_i"].isna()].dropna().astype(str).unique())
        if sin_ubicar:
            st.warning("Almacenes sin ubicación (agrégalos a UBICACIONES): " + ", ".join(sin_ubicar))

        return df
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return pd.DataFrame()

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

# 5. FUNCIÓN AUXILIAR SELECTBOX
def get_options(df, column_name, first_option="Todas"):
    if column_name in df.columns:
        vals = sorted(df[column_name].dropna().unique().astype(str).tolist())
        return [first_option] + vals
    return [first_option]

# 6. MENÚ LATERAL
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    menu = st.radio("Sección del Sistema:", ["📦 Gestión de Inventario", "✨ Nuevas Campañas", "📊 Análisis 360"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 7. VISTA: GESTIÓN DE INVENTARIO
if menu == "📦 Gestión de Inventario":
    st.title("📦 Gestión de Inventario")
    
    if not df_master.empty:
        r1c1, r1c2 = st.columns([1, 2])
        with r1c1: 
            sel_alm = st.selectbox("Almacén", get_options(df_master, 'Nombre'))
        with r1c2: 
            search_t = st.text_input("Buscador Descripción / SKU", placeholder="Escribe para buscar...")

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: 
            sel_cl = st.selectbox("Clasificación", get_options(df_master, 'Clasificación'))
        with r2c2: 
            sel_ca = st.selectbox("Campaña", get_options(df_master, 'Campaña'))
        with r2c3: 
            sel_cn = st.selectbox("Canal", get_options(df_master, 'Canal'))

        df_t = df_master.copy()
        if sel_alm != "Todas": df_t = df_t[df_t['Nombre'].astype(str) == sel_alm]
        if search_t: 
            df_t = df_t[df_t['Descripción'].astype(str).str.contains(search_t, case=False, na=False) | 
                        df_t['código'].astype(str).str.contains(search_t, case=False, na=False)]
        if sel_cl != "Todas": df_t = df_t[df_t['Clasificación'].astype(str) == sel_cl]
        if sel_ca != "Todas": df_t = df_t[df_t['Campaña'].astype(str) == sel_ca]
        if sel_cn != "Todas": df_t = df_t[df_t['Canal'].astype(str) == sel_cn]

        cols_t = ['código', 'Descripción', 'Disponible', 'Apartados', 'Nombre', 'Ciudad', 'Estado', 'Canal', 'Clasificación', 'Campaña', 'Estado de material', 'AÑO', 'Unidad']
        cols_validas = [c for c in cols_t if c in df_t.columns]

        st.dataframe(df_t[cols_validas], use_container_width=True, hide_index=True)
        st.download_button("📥 Reporte CSV", df_t[cols_validas].to_csv(index=False).encode('utf-8'), "inventario.csv", "text/csv")

# 8. VISTA: NUEVAS CAMPAÑAS
elif menu == "✨ Nuevas Campañas":
    st.title("✨ Nuevas Campañas")
    st.info("📦 Sección en preparación.")

# 9. VISTA: ANÁLISIS 360
else:
    st.title("📊 Análisis 360 - Dashboard")
    
    if not df_master.empty:
        c1, c2 = st.columns(2)
        with c1: canal_d = st.selectbox("Canal Dashboard", get_options(df_master, 'Canal', "Todos"))
        with c2: camp_d = st.selectbox("Campaña Dashboard", get_options(df_master, 'Campaña'))
        
        df_d = df_master.copy()
        if canal_d not in ["Todos", "Todas"]: df_d = df_d[df_d['Canal'].astype(str) == canal_d]
        if camp_d != "Todas": df_d = df_d[df_d['Campaña'].astype(str) == camp_d]

        # KPIs
        col_dash1, col_dash2 = st.columns([1, 2])
        with col_dash1:
            total_g = df_master['Disponible'].sum() if 'Disponible' in df_master.columns else 0
            total_f = df_d['Disponible'].sum() if 'Disponible' in df_d.columns else 0
            porc = (total_f / total_g * 100) if total_g > 0 else 0
            st.components.v1.html(draw_liquid_fill(porc), height=280)
        
        with col_dash2:
            st.markdown(f"""<div style='text-align:center; padding:45px; background:{MAGENTA}; border-radius:15px; color:white; margin-top:20px;'><p style='margin:0; font-size:20px;'>Inventario Disponible</p><h1 style='font-size: 80px; margin:0;'>{total_f:,.0f}</h1></div>""", unsafe_allow_html=True)

        st.markdown("---")
        g1, g2, g3 = st.columns(3)
        
        with g1:
            st.subheader("🗺️ Cobertura")
            df_mapa = df_d.dropna(subset=['lat_i', 'lon_i'])
            if not df_mapa.empty:
                # Una burbuja por ciudad (Monterrey DTS + Monterrey PVD se suman)
                df_mapa = (
                    df_mapa.groupby(['Ciudad', 'Estado', 'lat_i', 'lon_i'], as_index=False, dropna=False)
                    .agg(Disponible=('Disponible', 'sum'),
                         Almacenes=('Nombre', lambda s: ', '.join(sorted(s.astype(str).unique()))))
                )
                # El tamaño de la burbuja no acepta negativos (hay ajustes con Disponible < 0)
                df_mapa['Tamaño'] = df_mapa['Disponible'].clip(lower=0)
                if df_mapa['Tamaño'].max() == 0:
                    df_mapa['Tamaño'] = 1
                try:
                    fig_map = px.scatter_mapbox(
                        df_mapa, lat="lat_i", lon="lon_i", size="Tamaño", color="Disponible",
                        hover_name="Ciudad",
                        hover_data={"Estado": True, "Almacenes": True, "Disponible": True,
                                    "Tamaño": False, "lat_i": False, "lon_i": False},
                        color_continuous_scale=[AZUL_BARRA, MAGENTA], size_max=30,
                        center={"lat": 23.6, "lon": -102.5}, zoom=3.3,
                        mapbox_style="carto-positron", height=300,
                    )
                    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig_map, use_container_width=True)
                except Exception as e:
                    st.warning(f"No se pudo dibujar el mapa: {e}")
            else: st.info("No hay coordenadas para graficar.")
            
        with g2:
            st.subheader("📊 Almacenes")
            if 'Nombre' in df_d.columns and not df_d.empty:
                df_rank = df_d.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible')
                if not df_rank.empty:
                    fig_bar = px.bar(df_rank, x="Disponible", y="Nombre", orientation='h', height=300)
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        with g3:
            st.subheader("🟣 Campaña")
            if not df_d.empty and {'Campaña', 'Canal', 'Disponible'}.issubset(df_d.columns):
                # Un punto por Campaña + Canal con su total (en vez de un punto por renglón)
                df_camp = df_d.groupby(['Campaña', 'Canal'], as_index=False)['Disponible'].sum()
                # El tamaño no acepta negativos: sin existencia = sin burbuja
                df_camp['Tamaño'] = df_camp['Disponible'].clip(lower=0)
                if df_camp.empty:
                    st.info("Datos insuficientes para dispersión.")
                else:
                    if df_camp['Tamaño'].max() == 0:
                        df_camp['Tamaño'] = 1
                    try:
                        fig_scat = px.scatter(
                            df_camp, x="Campaña", y="Canal", size="Tamaño",
                            hover_data={"Disponible": True, "Tamaño": False},
                            color_discrete_sequence=[MAGENTA], size_max=30, height=300,
                        )
                        st.plotly_chart(fig_scat, use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pudo dibujar la gráfica: {e}")
            else: st.info("Datos insuficientes para dispersión.")
