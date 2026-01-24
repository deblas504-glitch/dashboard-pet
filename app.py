import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(layout="wide", page_title="Dashboard PET")

MAGENTA = "#b5006a"
AZUL_BI = "#002d5a"

@st.cache_data
def load_data():
    # Carga de datos desde GitHub
    df = pd.read_excel("Inventario_Pet_23012026.xlsx")
    
    # Coordenadas de respaldo para evitar el KeyError 'lat'
    coordenadas_mexico = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coordenadas_mexico)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    # Unión forzada para asegurar que 'lat' y 'lon' siempre existan
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 2. NAVEGACIÓN
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Analisis"

with st.sidebar:
    st.markdown(f"<h2 style='color:white;'>Inventario PET</h2>", unsafe_allow_html=True)
    if st.button("📈 Análisis de Inventario"): st.session_state.pagina = "Analisis"
    if st.button("📁 Inventario por Almacén"): st.session_state.pagina = "Inventario"
    st.divider()
    if st.button("🔄 Resetear"): st.rerun()

# 3. PÁGINA: ANÁLISIS DINÁMICO
if st.session_state.pagina == "Analisis":
    st.subheader("Selecciona un Canal en el Treemap para filtrar todo")

    # Treemap con evento de selección activado
    fig_tree = px.treemap(df_master, path=['Canal'], values='Total',
                         color='Canal', color_discrete_map={
                             'Tradicional PET': '#e91e63', 'Changarro': '#0d47a1',
                             'Multicanal PET': '#7b1fa2', 'Autoservicio PET': '#2196f3'
                         })
    
    # Esta línea es la que "escucha" el clic en el gráfico
    seleccion = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun")

    # CEREBRO DEL FILTRADO: Si hay clic, df_f se reduce. Si no, es global.
    df_f = df_master.copy()
    label_kpi = "Total Global"

    if seleccion and "selection" in seleccion and seleccion["selection"]["points"]:
        canal_detectado = seleccion["selection"]["points"][0].get("label")
        if canal_detectado:
            df_f = df_master[df_master['Canal'] == canal_detectado]
            label_kpi = f"Total {canal_detectado}"

    # Visualización de Resultados
    col_kpi, col_map = st.columns([1, 2])
    
    with col_kpi:
        # Tarjeta Magenta Dinámica que RESPONDE al clic
        st.markdown(f"""
            <div style="background-color: {MAGENTA}; color: white; padding: 25px; border-radius: 10px; text-align: center;">
                <p style="margin:0; font-weight: bold;">{label_kpi}</p>
                <h1 style="margin:0; font-size: 50px;">{df_f['Total'].sum():,.0f}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("### Ranking Almacén")
        resumen = df_f.groupby('Estado')['Total'].sum().sort_values(ascending=False).reset_index()
        st.dataframe(resumen, hide_index=True, use_container_width=True, height=350)

    with col_map:
        st.write("### Mapa de Distribución")
        # El mapa ahora solo usa los datos filtrados por el Treemap
        resumen_mapa = df_f.dropna(subset=['lat', 'lon']).groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
        fig_map = px.scatter_mapbox(resumen_mapa, lat="lat", lon="lon", size="Total", color="Total",
                                   color_continuous_scale='Blues', size_max=30, zoom=3.5, mapbox_style="carto-positron")
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
        st.plotly_chart(fig_map, use_container_width=True)

# 4. PÁGINA: INVENTARIO POR ALMACÉN
else:
    st.header("Inventario Detallado")
    st.dataframe(df_master[['código', 'Descripción', 'Campaña', 'Estado', 'Canal', 'Total']], use_container_width=True)
    
