import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# 1. CONFIGURACIÓN
st.set_page_config(layout="wide", page_title="Dashboard PET")

MAGENTA = "#b5006a"
AZUL_BI = "#002d5a"

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

# NAVEGACIÓN
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Analisis"

with st.sidebar:
    st.title("Logística PET")
    if st.button("📈 Análisis de Inventario"): st.session_state.pagina = "Analisis"
    if st.button("📁 Detalle por Almacén"): st.session_state.pagina = "Inventario"
    if st.button("🔄 Resetear"): st.rerun()

# --- PÁGINA ANÁLISIS ---
if st.session_state.pagina == "Analisis":
    st.write("### Selecciona un Canal para filtrar todo")
    
    # 1. EL TREEMAP (FILTRO MAESTRO)
    fig_tree = px.treemap(df_master, path=['Canal'], values='Total',
                          color='Canal', color_discrete_map={
                              'Tradicional PET': '#e91e63', 'Changarro': '#0d47a1',
                              'Multicanal PET': '#7b1fa2', 'Autoservicio PET': '#2196f3'
                          })
    
    # Capturamos la selección
    seleccion = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun", key="tree_click")

    # 2. LÓGICA DE FILTRADO (EL CEREBRO)
    df_f = df_master.copy()
    canal_txt = "Total Global"

    # Verificamos si realmente hubo un clic válido
    if seleccion and "selection" in seleccion and seleccion["selection"]["points"]:
        puntos = seleccion["selection"]["points"]
        if len(puntos) > 0:
            # Intentamos obtener el label del punto seleccionado
            canal_detectado = puntos[0].get("label")
            if canal_detectado:
                df_f = df_master[df_master['Canal'] == canal_detectado]
                canal_txt = f"Canal: {canal_detectado}"

    # 3. VISUALES DINÁMICOS
    c_kpi, c_filt = st.columns([1, 1])
    with c_kpi:
        st.markdown(f"""
            <div style="background: white; padding: 20px; border: 2px solid {MAGENTA}; text-align: center; border-radius: 10px;">
                <p style="color: {AZUL_BI}; margin:0; font-weight:bold;">{canal_txt}</p>
                <h1 style="color: {MAGENTA}; font-size: 50px; margin:0;">{df_f['Total'].sum():,.0f}</h1>
            </div>""", unsafe_allow_html=True)
    
    with c_filt:
        camp_sel = st.multiselect("Campaña", df_f['Campaña'].unique(), default=df_f['Campaña'].unique())
        df_f = df_f[df_f['Campaña'].isin(camp_sel)]

    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.write("### Top Almacenes")
        ranking = df_f.groupby('Estado')['Total'].sum().sort_values(ascending=False).reset_index()
        st.dataframe(ranking, hide_index=True, use_container_width=True)
    
    with c2:
        st.write("### Mapa de Stock")
        geo = df_f.dropna(subset=['lat']).groupby(['Estado','lat','lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(geo, lat="lat", lon="lon", size="Total", color="Total",
                                   color_continuous_scale='Blues', zoom=3.5, mapbox_style="carto-positron")
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=350)
        st.plotly_chart(fig_map, use_container_width=True)

else:
    # PÁGINA INVENTARIO
    st.header("Detalle por Almacén")
    st.dataframe(df_master, use_container_width=True)
    