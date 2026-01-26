import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(layout="wide", page_title="Dashboard PET Interactivos")

# Colores del negocio
MAGENTA = "#b5006a"

# 2. CONEXIÓN EN VIVO A TU GOOGLE SHEETS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60) # Se refresca cada minuto para ser casi "en vivo"
def load_data():
    df = pd.read_excel(URL)
    # Coordenadas maestras para que el mapa NUNCA dé error de 'lat'
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 3. EL TREEMAP (FILTRO MAESTRO)
st.write("### Selecciona un Canal para filtrar todo")

fig_tree = px.treemap(df_master, path=['Canal'], values='Total',
                      color='Canal', color_discrete_sequence=px.colors.qualitative.Set2)

# ESTA LÍNEA ES LA MAGIA: Captura el clic y reinicia la app con el filtro aplicado
seleccion = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun", key="filtro_maestro")

# LÓGICA DE ACTUALIZACIÓN DE DATOS
df_filtrado = df_master.copy()
nombre_canal = "Global"

# Si el usuario hace clic en un cuadro...
if seleccion and "selection" in seleccion and seleccion["selection"]["points"]:
    punto = seleccion["selection"]["points"][0]
    # Sacamos el nombre del canal (ej: Tradicional PET)
    canal_clic = punto.get("label")
    if canal_clic:
        df_filtrado = df_master[df_master['Canal'] == canal_clic]
        nombre_canal = canal_clic

# 4. RESULTADOS DINÁMICOS
c1, c2 = st.columns([1, 2])

with c1:
    # ESTA TARJETA AHORA SÍ VA A CAMBIAR
    total_unidades = df_filtrado['Total'].sum()
    st.markdown(f"""
        <div style="background-color: {MAGENTA}; color: white; padding: 25px; border-radius: 15px; text-align: center;">
            <p style="margin:0; font-size: 18px;">Total {nombre_canal}</p>
            <h1 style="margin:0; font-size: 55px;">{total_unidades:,.0f}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("#### Ranking por Estado")
    ranking = df_filtrado.groupby('Estado')['Total'].sum().sort_values(ascending=False).reset_index()
    st.dataframe(ranking, hide_index=True, use_container_width=True)

with c2:
    st.write("#### Mapa de Stock")
    resumen_mapa = df_filtrado.dropna(subset=['lat']).groupby(['Estado','lat','lon'])['Total'].sum().reset_index()
    fig_map = px.scatter_mapbox(resumen_mapa, lat="lat", lon="lon", size="Total", color="Total",
                                color_continuous_scale='Blues', zoom=3.8, mapbox_style="carto-positron")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
    st.plotly_chart(fig_map, use_container_width=True)