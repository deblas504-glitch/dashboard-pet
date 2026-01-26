import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(layout="wide", page_title="Control PET")

# Conexión a tu Google Sheets
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Blindaje de coordenadas para el mapa
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, pd.DataFrame(coords), on='Estado', how='left')

df_master = load_data()

# --- FILTRO MANUAL (Para asegurar que funcione) ---
st.markdown("### Filtro de Canal")
canal_sel = st.selectbox("Elige un Canal:", ["Ver Todo"] + list(df_master['Canal'].unique()))

# Lógica de Filtrado
df_f = df_master.copy()
if canal_sel != "Ver Todo":
    df_f = df_master[df_master['Canal'] == canal_sel]

# --- VISUALIZACIÓN ---
c1, c2 = st.columns([1, 2])

with c1:
    total = df_f['Total'].sum()
    st.markdown(f"""
        <div style="background:#b5006a; color:white; padding:20px; border-radius:10px; text-align:center;">
            <h3>Total {canal_sel}</h3>
            <h1 style="font-size:50px;">{total:,.0f}</h1>
        </div>""", unsafe_allow_html=True)
    
    st.write("#### Ranking")
    st.dataframe(df_f.groupby('Estado')['Total'].sum().sort_values(ascending=False), use_container_width=True)

with c2:
    st.write("#### Mapa de Stock")
    geo = df_f.dropna(subset=['lat']).groupby(['Estado','lat','lon'])['Total'].sum().reset_index()
    fig_map = px.scatter_mapbox(geo, lat="lat", lon="lon", size="Total", color="Total",
                               color_continuous_scale='Blues', zoom=3.5, mapbox_style="carto-positron")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)