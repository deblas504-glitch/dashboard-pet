import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CARGA DE DATOS
@st.cache_data
def load_data():
    # Asegúrate de que el nombre coincida con tu archivo en GitHub
    df = pd.read_excel("Inventario_Pet_23012026.xlsx")
    # ... (aquí va tu lógica de coordenadas que ya tienes)
    return df

df_master = load_data()

# 2. TREEMAP CON SELECCIÓN ACTIVA
st.subheader("Selecciona un Canal para filtrar todo el tablero")

fig_tree = px.treemap(
    df_master, 
    path=['Canal'], 
    values='Total',
    color='Canal',
    color_discrete_map={
        'Tradicional PET': '#e91e63', 'Changarro': '#0d47a1',
        'Multicanal PET': '#7b1fa2', 'Autoservicio PET': '#2196f3'
    }
)

# CLAVE: Usamos 'on_select="rerun"' y capturamos el valor
# Esto fuerza a Streamlit a leer el clic del Treemap
seleccion = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun")

# 3. LÓGICA DE FILTRADO MAESTRO
df_f = df_master.copy()
titulo_dinamico = "Total Global"

# Verificamos si hay un clic en el gráfico
if seleccion and "selection" in seleccion and seleccion["selection"]["points"]:
    # Extraemos el nombre del canal seleccionado
    canal_seleccionado = seleccion["selection"]["points"][0].get("label")
    if canal_seleccionado:
        df_f = df_master[df_master['Canal'] == canal_seleccionado]
        titulo_dinamico = f"Total {canal_seleccionado}"

# 4. ELEMENTOS DINÁMICOS (Ahora todos usan df_f)
col_kpi, col_map = st.columns([1, 2])

with col_kpi:
    # Tarjeta Magenta Dinámica
    total_unidades = df_f['Total'].sum()
    st.markdown(f"""
        <div style="background-color: #b5006a; color: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h2 style="margin:0; font-size: 20px;">{titulo_dinamico}</h2>
            <h1 style="margin:0; font-size: 60px;">{total_unidades:,.0f}</h1>
        </div>
    """, unsafe_allow_html=True)

with col_map:
    # Mapa Dinámico
    resumen_geo = df_f.dropna(subset=['lat']).groupby(['Estado','lat','lon'])['Total'].sum().reset_index()
    fig_map = px.scatter_mapbox(resumen_geo, lat="lat", lon="lon", size="Total", color="Total",
                                color_continuous_scale='Blues', zoom=3.5, mapbox_style="carto-positron")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

# 5. TABLA DE RANKING DINÁMICA
st.write("### Ranking Almacén")
ranking = df_f.groupby('Estado')['Total'].sum().sort_values(ascending=False).reset_index()
st.dataframe(ranking, use_container_width=True, hide_index=True)

