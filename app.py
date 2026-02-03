import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="Control PET - Dashboard Maestro")

# Estilo Magenta Corporativo
MAGENTA = "#b5006a"
AZUL_PROFUNDO = "#002d5a"

# 2. CARGA DE DATOS (GOOGLE SHEETS)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Limpieza de nombres de columnas para evitar el error de Disponible
    df.columns = df.columns.str.strip()
    
    # Coordenadas por Estado para el Mapa
    coords = {
        'Estado': ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'],
        'lat': [21.8823, 30.8406, 26.0444, 19.8301, 16.7569, 28.6330, 19.4326, 27.0587, 19.2433, 24.0277, 19.3562, 21.0190, 17.4392, 20.0911, 20.6597, 19.7008, 18.9220, 21.5095, 25.6866, 17.0732, 19.0414, 20.5888, 19.1817, 22.1565, 24.8091, 29.0730, 17.8409, 23.7369, 19.3181, 19.1738, 20.9674, 22.7709],
        'lon': [-102.2826, -115.2838, -111.6661, -90.5349, -93.1292, -106.0691, -99.1332, -101.7068, -103.7250, -104.6532, -99.1013, -101.2574, -99.5451, -98.7624, -103.3496, -101.1844, -99.2347, -104.8946, -100.3161, -96.7266, -98.2063, -100.3899, -88.4711, -100.9855, -107.3940, -110.9673, -92.6189, -99.1460, -98.2375, -96.1342, -89.5926, -102.5831]
    }
    df_coords = pd.DataFrame(coords)
    df['Estado'] = df['Estado'].astype(str).str.strip()
    return pd.merge(df, df_coords, on='Estado', how='left')

df_master = load_data()

# 3. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.title("📂 Control de Activos")
    menu = st.radio("Sección:", ["Análisis de Inventario", "Tabla de Inventario"])
    st.markdown("---")
    
    if menu == "Análisis de Inventario":
        st.write("**Filtro Maestro:**")
        canal_global = st.selectbox("Canal Principal", ["Global"] + sorted(df_master['Canal'].unique().tolist()))
    else:
        canal_global = "Global"

# 4. VISTA: ANÁLISIS DE INVENTARIO
if menu == "Análisis de Inventario":
    st.title(f"📊 Dashboard Estratégico: {canal_global}")
    df_f = df_master.copy()
    if canal_global != "Global":
        df_f = df_master[df_master['Canal'] == canal_global]

    # AJUSTE: Se cambió 'Total' por 'Disponible'
    total_u = df_f['Disponible'].sum()
    st.markdown(f"""
        <div style="background:{MAGENTA}; color:white; padding:20px; border-radius:12px; text-align:center; margin-bottom:25px;">
            <p style="margin:0; font-size: 20px;">Inventario Disponible</p>
            <h1 style="margin:0; font-size: 60px;">{total_u:,.0f}</h1>
        </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.write("#### 🗺️ Mapa de Volumen por Estado")
        # AJUSTE: Se cambió 'Total' por 'Disponible'
        df_mapa = df_f.groupby(['Estado', 'lat', 'lon'])['Disponible'].sum().reset_index()
        fig_map = px.scatter_mapbox(
            df_mapa, lat="lat", lon="lon", size="Disponible", color="Disponible",
            color_continuous_scale=[[0, AZUL_PROFUNDO], [1, MAGENTA]],
            size_max=40, zoom=3.8, mapbox_style="carto-positron",
            template="plotly_dark", hover_name="Estado"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with c2:
        st.write("#### 📊 Ranking de Almacenes")
        # AJUSTE: Se cambió 'Total' por 'Disponible'
        df_bar = df_f.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible', ascending=True)
        fig_bar = px.bar(
            df_bar, x="Disponible", y="Nombre", orientation='h',
            color="Disponible", color_continuous_scale=[[0, AZUL_PROFUNDO], [1, MAGENTA]],
            template="plotly_dark", text_auto='.2s'
        )
        fig_bar.update_layout(showlegend=False, height=500, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

# 5. VISTA: TABLA DE INVENTARIO (AJUSTADA CON R Y DISPONIBLE)
else:
    st.title("📋 Tabla Maestra de Inventario")
    
    # FILTROS DE CABECERA
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_c = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with f2:
        sel_a = st.selectbox("Almacén", ["Todos"] + sorted(df_master['Nombre'].unique().tolist()))
    with f3:
        sel_p = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f4:
        sel_l = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))

    # Aplicación de filtros
    df_tabla = df_master.copy()
    if sel_c != "Todos": df_tabla = df_tabla[df_tabla['Canal'] == sel_c]
    if sel_a != "Todos": df_tabla = df_tabla[df_tabla['Nombre'] == sel_a]
    if sel_p != "Todas": df_tabla = df_tabla[df_tabla['Campaña'] == sel_p]
    if sel_l != "Todas": df_tabla = df_tabla[df_tabla['Clasificación'] == sel_l]

    # AJUSTE: Selección de columnas incluyendo R (17) y Disponible (18)
    # C(2), D(3), E(4), H(7), I(8), J(9), K(10), L(11), R(17), Disponible(18)
    indices_deseados = [2, 3, 4, 7, 8, 9, 10, 11, 17, 18]
    columnas_finales = [df_master.columns[i] for i in indices_deseados]
    
    # Mostrar solo lo solicitado
    st.dataframe(df_tabla[columnas_finales], use_container_width=True, hide_index=True)
    
    # Botón de Descarga
    csv = df_tabla[columnas_finales].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Reporte Seleccionado", csv, "inventario_especifico.csv", "text/csv")