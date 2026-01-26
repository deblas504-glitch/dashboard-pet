import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN VISUAL DEL TEMA
st.set_page_config(layout="wide", page_title="Sistema de Control PET")

# Definición de Colores de Estilo
MAGENTA = "#b5006a"
FONDO_OSCURO = "#0e1117"

# 2. CARGA DE DATOS DESDE GOOGLE SHEETS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Limpieza de columnas clave según tu estructura
    for col in ['Nombre', 'Canal', 'Estado']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

df_master = load_data()

# 3. MENÚ DE NAVEGACIÓN (BOTONES SUPERIORES)
st.markdown("### 🗂️ Selección de Canal Logístico")

if "canal_activo" not in st.session_state:
    st.session_state.canal_activo = "Global"

# Generamos los botones basados en tus datos reales
canales = ["Global"] + sorted(df_master['Canal'].unique().tolist())
cols_menu = st.columns(len(canales))

for i, nombre_canal in enumerate(canales):
    # El botón seleccionado resalta en color primario
    tipo_boton = "primary" if st.session_state.canal_activo == nombre_canal else "secondary"
    if cols_menu[i].button(nombre_canal, use_container_width=True, type=tipo_boton):
        st.session_state.canal_activo = nombre_canal
        st.rerun()

# 4. FILTRADO DINÁMICO
df_f = df_master.copy()
if st.session_state.canal_activo != "Global":
    df_f = df_master[df_master['Canal'] == st.session_state.canal_activo]

# 5. PANEL DE INDICADORES (KPIs)
st.markdown("---")
total_unidades = df_f['Total'].sum()
st.markdown(f"""
    <div style="background:{MAGENTA}; color:white; padding:15px; border-radius:12px; text-align:center; margin-bottom:25px;">
        <p style="margin:0; font-size: 20px; font-weight: 300;">Inventario Total: {st.session_state.canal_activo}</p>
        <h1 style="margin:0; font-size: 65px; font-weight: bold;">{total_unidades:,.0f}</h1>
    </div>""", unsafe_allow_html=True)

# 6. DISTRIBUCIÓN DE GRÁFICAS (MODO ESPEJO)
col_izq, col_der = st.columns(2)

# Agrupamos por Almacén (Columna H "Nombre")
df_viz = df_f.groupby('Nombre')['Total'].sum().reset_index().sort_values('Total', ascending=False)

with col_izq:
    st.markdown("#### 🔵 Distribución por Volumen (Burbujas)")
    fig_bubble = px.scatter(
        df_viz, 
        x="Nombre", 
        y="Total",
        size="Total", 
        color="Nombre",
        hover_name="Nombre",
        size_max=70,
        template="plotly_dark"
    )
    fig_bubble.update_layout(
        showlegend=False, 
        height=450, 
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="Almacenes",
        yaxis_title="Unidades"
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

with col_der:
    st.markdown("#### 📊 Comparativo de Stock (Barras)")
    fig_bar = px.bar(
        df_viz,
        x="Nombre",
        y="Total",
        color="Nombre",
        text_auto='.2s',
        template="plotly_dark"
    )
    fig_bar.update_layout(
        showlegend=False, 
        height=450, 
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="Almacenes",
        yaxis_title="Unidades"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# 7. TABLA DE DETALLE FINAL
st.markdown("#### 📋 Listado Maestro de Inventario")
st.dataframe(df_f, use_container_width=True, hide_index=True)
