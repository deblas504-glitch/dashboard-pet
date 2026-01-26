import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE ESTILO DARK
st.set_page_config(layout="wide", page_title="PET Warehouse Analytics")

# Colores personalizados para el tema oscuro
MAGENTA = "#b5006a"
FONDO_GRAFICA = "#111111"

# 2. CARGA DE DATOS DESDE GOOGLE SHEETS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Limpieza de columnas clave
    for col in ['Nombre', 'Canal']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

df_master = load_data()

# 3. SELECTORES DE CANAL (BOTONES)
st.title("📊 Warehouse Performance Dashboard")

if "canal_activo" not in st.session_state:
    st.session_state.canal_activo = "Global"

canales = ["Global"] + sorted(df_master['Canal'].unique().tolist())
cols_btns = st.columns(len(canales))

for i, nombre_canal in enumerate(canales):
    tipo = "primary" if st.session_state.canal_activo == nombre_canal else "secondary"
    if cols_btns[i].button(nombre_canal, use_container_width=True, type=tipo):
        st.session_state.canal_activo = nombre_canal
        st.rerun()

# 4. FILTRADO DE DATOS
df_f = df_master.copy()
if st.session_state.canal_activo != "Global":
    df_f = df_master[df_master['Canal'] == st.session_state.canal_activo]

# 5. DISEÑO DE FILA SUPERIOR (KPIs)
total_unidades = df_f['Total'].sum()
st.markdown(f"""
    <div style="background:{MAGENTA}; color:white; padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
        <h2 style="margin:0;">{st.session_state.canal_activo} - Total Units</h2>
        <h1 style="margin:0; font-size: 60px;">{total_unidades:,.0f}</h1>
    </div>""", unsafe_allow_html=True)

# 6. DISEÑO DE COLUMNAS PARA GRÁFICAS (IGUAL A TU REFERENCIA)
col_left, col_right = st.columns(2)

# Agrupación de datos para las visualizaciones
df_viz = df_f.groupby('Nombre')['Total'].sum().reset_index()

with col_left:
    st.markdown("### Stock Distribution by Warehouse")
    # Gráfico de Burbujas (Bubble Chart)
    fig_bubble = px.scatter(
        df_viz, 
        x="Nombre", 
        y="Total",
        size="Total", 
        color="Nombre",
        hover_name="Nombre",
        size_max=80,
        template="plotly_dark"
    )
    fig_bubble.update_layout(
        plot_bgcolor=FONDO_GRAFICA,
        paper_bgcolor=FONDO_GRAFICA,
        showlegend=False,
        height=500,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

with col_right:
    st.markdown("### Total Stock Comparison")
    # Gráfico de Barras (Bar Chart)
    fig_bar = px.bar(
        df_viz,
        x="Nombre",
        y="Total",
        color="Nombre",
        template="plotly_dark"
    )
    fig_bar.update_layout(
        plot_bgcolor=FONDO_GRAFICA,
        paper_bgcolor=FONDO_GRAFICA,
        showlegend=False,
        height=500,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# 7. TABLA DE DATOS AL FINAL
st.markdown("### Detailed Inventory List")
st.dataframe(df_f, use_container_width=True, hide_index=True)
