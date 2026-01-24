import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="Dashboard Logística PET")

MAGENTA = "#b5006a"
AZUL_BI = "#002d5a"

# Estilos CSS para Tarjetas y Sidebar
st.markdown(f"""
    <style>
    .main {{ background-color: #f4f7f9; }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_BI}; color: white; }}
    .metric-card {{
        background-color: white; padding: 20px; border-radius: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center;
        border: 2px solid {MAGENTA}; margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("Inventario_Pet_23012026.xlsx")
    coordenadas = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coordenadas)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# --- LÓGICA DE NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Analisis"

with st.sidebar:
    st.title("Inventario PET")
    if st.button("📊 Análisis de Inventario"):
        st.session_state.pagina = "Analisis"
    if st.button("📋 Detalle por Almacén"):
        st.session_state.pagina = "Inventario"
    st.divider()
    if st.button("🔄 Resetear Todo"):
        st.cache_data.clear()
        st.rerun()

# --- PÁGINA: ANÁLISIS ---
if st.session_state.pagina == "Analisis":
    st.subheader("Selecciona un Canal en el Treemap para filtrar todo el tablero")

    # Layout de la parte superior
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        # Treemap interactivo
        fig_tree = px.treemap(
            df_master, path=['Canal'], values='Total',
            color='Canal', color_discrete_map={
                'Tradicional PET': '#e91e63', 'Changarro': '#0d47a1',
                'Multicanal PET': '#7b1fa2', 'Autoservicio PET': '#2196f3'
            }
        )
        # La clave 'on_select="rerun"' es vital para la interactividad
        seleccion = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun", key="main_treemap")

    # --- CEREBRO DEL FILTRADO ---
    df_filtrado = df_master.copy()
    subtitulo = "Total General"

    # Capturar la selección del clic
    if seleccion and "selection" in seleccion and seleccion["selection"]["points"]:
        canal_clic = seleccion["selection"]["points"][0].get("label")
        if canal_clic:
            df_filtrado = df_master[df_master['Canal'] == canal_clic]
            subtitulo = f"Total {canal_clic}"

    with col_der:
        # TARJETA DINÁMICA QUE DEBE CAMBIAR
        total_p = df_filtrado['Total'].sum()
        st.markdown(f"""
            <div class="metric-card">
                <p style="color: {AZUL_BI}; margin:0; font-weight:bold;">{subtitulo}</p>
                <h1 style="color: {MAGENTA}; font-size: 50px; margin:0;">{total_p:,.0f}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        # Filtros manuales que también afectan
        camp_sel = st.multiselect("Filtrar Campaña", options=df_filtrado['Campaña'].unique(), default=df_filtrado['Campaña'].unique())
        df_filtrado = df_filtrado[df_filtrado['Campaña'].isin(camp_sel)]

    # Fila inferior
    c_rank, c_map = st.columns([1, 1.5])
    with c_rank:
        st.write("### Ranking Almacén")
        resumen = df_filtrado.groupby('Estado')['Total'].sum().sort_values(ascending=False).reset_index()
        st.dataframe(resumen, hide_index=True, use_container_width=True, height=350)

    with c_map:
        st.write("### Mapa de Distribución")
        resumen_geo = df_filtrado.dropna(subset=['lat']).groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(
            resumen_geo, lat="lat", lon="lon", size="Total", color="Total",
            color_continuous_scale='Blues', size_max=25, zoom=3.5, mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=350)
        st.plotly_chart(fig_map, use_container_width=True)

# --- PÁGINA: DETALLE ---
else:
    st.header("Inventario Detallado por Almacén")
    f1, f2 = st.columns(2)
    with f1:
        alms = st.multiselect("Almacén", options=sorted(df_master['Estado'].unique()), default=df_master['Estado'].unique())
    with f2:
        search = st.text_input("Buscador", placeholder="Descripción o SKU...")

    df_tab = df_master[df_master['Estado'].isin(alms)]
    if search:
        df_tab = df_tab[df_tab['Descripción'].str.contains(search, case=False)]
    
    st.dataframe(df_tab, use_container_width=True, height=600)