
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(layout="wide", page_title="Dashboard Logística PET")

# COLORES
MAGENTA = "#b5006a"
AZUL_BI = "#002d5a"

# 2. CONEXIÓN A GOOGLE SHEETS (TU ID)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=300) # Se actualiza cada 5 minutos si cambias el Excel en la nube
def load_data():
    df = pd.read_excel(URL)
    # Coordenadas maestras para que el mapa nunca falle
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 3. INTERFAZ Y FILTRO MAESTRO
st.title("📦 Control de Inventario PET")
st.markdown("### Selecciona un Canal en el gráfico para filtrar todo")

fig_tree = px.treemap(df_master, path=['Canal'], values='Total',
                     color='Canal', color_discrete_sequence=px.colors.qualitative.Pastel)

# Aquí activamos la "escucha" del clic
seleccion = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun")

# Lógica de Filtrado Dinámico
df_f = df_master.copy()
titulo_kpi = "Total Global"

if seleccion and "selection" in seleccion and seleccion["selection"]["points"]:
    canal_detectado = seleccion["selection"]["points"][0].get("label")
    if canal_detectado:
        df_f = df_master[df_master['Canal'] == canal_detectado]
        titulo_kpi = f"Total {canal_detectado}"

# 4. DASHBOARD VISUAL
col1, col2 = st.columns([1, 2])

with col1:
    # LA TARJETA QUE DEBE CAMBIAR AL HACER CLIC
    st.markdown(f"""
        <div style="background-color: {MAGENTA}; color: white; padding: 25px; border-radius: 10px; text-align: center;">
            <p style="margin:0; font-weight: bold;">{titulo_kpi}</p>
            <h1 style="margin:0; font-size: 55px;">{df_f['Total'].sum():,.0f}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("### Ranking Almacén")
    ranking = df_f.groupby('Estado')['Total'].sum().sort_values(ascending=False).reset_index()
    st.dataframe(ranking, hide_index=True, use_container_width=True)

with col2:
    st.write("### Mapa de Distribución")
    geo = df_f.dropna(subset=['lat']).groupby(['Estado', 'lat', 'lon'])['Total'].sum().reset_index()
    fig_map = px.scatter_mapbox(geo, lat="lat", lon="lon", size="Total", color="Total",
                               color_continuous_scale='Blues', size_max=25, zoom=3.8, mapbox_style="carto-positron")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
    st.plotly_chart(fig_map, use_container_width=True)
    