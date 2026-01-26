import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(layout="wide", page_title="Dashboard Logística - Almacenes")

# Color corporativo
MAGENTA = "#b5006a"

# 2. CARGA DE DATOS DESDE GOOGLE SHEETS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Limpieza de nombres para asegurar que los filtros no fallen
    df['Almacen'] = df['Almacen'].astype(str).str.strip()
    df['Canal'] = df['Canal'].astype(str).str.strip()
    return df

df_master = load_data()

# 3. INTERFAZ DE FILTROS (BOTONES)
st.title("📦 Control de Inventario por Almacén")
st.write("### Selecciona un Canal para filtrar:")

if "canal_activo" not in st.session_state:
    st.session_state.canal_activo = "Global"

canales = ["Global"] + sorted(df_master['Canal'].unique().tolist())
cols_btns = st.columns(len(canales))

for i, nombre_canal in enumerate(canales):
    estilo = "primary" if st.session_state.canal_activo == nombre_canal else "secondary"
    if cols_btns[i].button(nombre_canal, use_container_width=True, type=estilo):
        st.session_state.canal_activo = nombre_canal
        st.rerun()

# 4. FILTRADO DE DATOS
df_f = df_master.copy()
if st.session_state.canal_activo != "Global":
    df_f = df_master[df_master['Canal'] == st.session_state.canal_activo]

# 5. DASHBOARD EN DOS COLUMNAS
col_datos, col_grafica = st.columns([1, 2])

with col_datos:
    # Tarjeta Magenta Dinámica
    total_unidades = df_f['Total'].sum()
    st.markdown(f"""
        <div style="background:{MAGENTA}; color:white; padding:30px; border-radius:15px; text-align:center; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
            <p style="margin:0; font-size: 18px; font-weight: bold;">{st.session_state.canal_activo}</p>
            <h1 style="margin:0; font-size: 55px;">{total_unidades:,.0f}</h1>
            <p style="margin:0; font-size: 14px;">Unidades Totales</p>
        </div>""", unsafe_allow_html=True)
    
    st.write("#### Detalle por Almacén")
    # Agrupamos por Almacén para la tabla
    ranking_almacen = df_f.groupby('Almacen')['Total'].sum().sort_values(ascending=False).reset_index()
    st.dataframe(ranking_almacen, hide_index=True, use_container_width=True)

with col_grafica:
    st.write(f"#### Volumetría por Almacén: {st.session_state.canal_activo}")
    
    # Preparar datos para las burbujas (agrupado por Almacén)
    df_bubble = df_f.groupby('Almacen')['Total'].sum().reset_index()
    
    # GRÁFICO DE BURBUJAS POR ALMACÉN
    fig_bubble = px.scatter(
        df_bubble, 
        x="Almacen", 
        y="Total",
        size="Total", 
        color="Almacen",
        hover_name="Almacen", 
        size_max=80,             # Burbujas grandes para impacto visual
        template="plotly_dark",  # Estilo visual moderno
    )
    
    fig_bubble.update_layout(
        margin={"r":10,"t":30,"l":10,"b":10},
        height=550,
        showlegend=False,        # Ocultamos leyenda porque los nombres están en el eje X
        xaxis_title="Nombre del Almacén",
        yaxis_title="Cantidad de Unidades",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    st.plotly_chart(fig_bubble, use_container_width=True)
        
