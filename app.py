import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="Sistema Logístico PET")

# Estilo Magenta
MAGENTA = "#b5006a"

# 2. CARGA DE DATOS (GOOGLE SHEETS)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    # Limpiamos espacios en blanco de las columnas clave
    columnas_clave = ['Nombre', 'Canal', 'Campaña', 'Clasificación', 'Estado']
    for col in columnas_clave:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

df_master = load_data()

# 3. BARRA LATERAL (MENÚ IZQUIERDO)
with st.sidebar:
    st.title("📂 Menú de Control")
    # Navegación entre las dos secciones que pediste
    menu = st.radio(
        "Ir a:",
        ["Análisis de Inventario", "Tabla de Inventario"]
    )
    st.markdown("---")
    st.info("Datos actualizados desde Google Sheets")

# 4. LÓGICA DE VISTAS
if menu == "Análisis de Inventario":
    st.title("📊 Análisis de Inventario")
    
    # Filtro de Canal para las gráficas
    canales = ["Todos"] + sorted(df_master['Canal'].unique().tolist())
    canal_sel = st.selectbox("Filtrar Canal para Gráficas:", canales)
    
    df_ana = df_master.copy()
    if canal_sel != "Todos":
        df_ana = df_master[df_master['Canal'] == canal_sel]

    # Tarjeta de KPI
    total = df_ana['Total'].sum()
    st.markdown(f"""
        <div style="background:{MAGENTA}; color:white; padding:20px; border-radius:12px; text-align:center; margin-bottom:20px;">
            <p style="margin:0;">Inventario {canal_sel}</p>
            <h1 style="margin:0; font-size: 50px;">{total:,.0f}</h1>
        </div>""", unsafe_allow_html=True)

    # Gráficas en Espejo
    c1, c2 = st.columns(2)
    df_viz = df_ana.groupby('Nombre')['Total'].sum().reset_index()
    
    with c1:
        st.write("#### Volumen por Almacén")
        fig_bubble = px.scatter(df_viz, x="Nombre", y="Total", size="Total", color="Nombre", 
                                template="plotly_dark", size_max=60)
        fig_bubble.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_bubble, use_container_width=True)
    
    with c2:
        st.write("#### Comparativa de Stock")
        fig_bar = px.bar(df_viz, x="Nombre", y="Total", color="Nombre", template="plotly_dark")
        fig_bar.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

else:
    # --- SECCIÓN: TABLA DE INVENTARIO CON FILTROS ---
    st.title("📋 Tabla de Inventario")
    st.write("Usa los filtros de abajo para buscar productos específicos:")

    # FILTROS DE LA TABLA (Tal cual los pediste)
    f1, f2, f3 = st.columns(3)
    
    with f1:
        lista_canales = ["Todos"] + sorted(df_master['Canal'].unique().tolist())
        sel_canal = st.selectbox("Filtrar por Canal", lista_canales)
    
    with f2:
        lista_campanas = ["Todas"] + sorted(df_master['Campaña'].unique().tolist())
        sel_campana = st.selectbox("Filtrar por Campaña", lista_campanas)
        
    with f3:
        lista_clasif = ["Todas"] + sorted(df_master['Clasificación'].unique().tolist())
        sel_clasif = st.selectbox("Filtrar por Clasificación", lista_clasif)

    # Aplicación de filtros a la tabla
    df_tabla = df_master.copy()
    
    if sel_canal != "Todos":
        df_tabla = df_tabla[df_tabla['Canal'] == sel_canal]
        
    if sel_campana != "Todas":
        df_tabla = df_tabla[df_tabla['Campaña'] == sel_campana]
        
    if sel_clasif != "Todas":
        df_tabla = df_tabla[df_tabla['Clasificación'] == sel_clasif]

    # Mostrar Tabla Final
    st.markdown(f"**Mostrando {len(df_tabla)} registros filtrados:**")
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)

    # Botón de descarga
    csv = df_tabla.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar esta selección a Excel (CSV)",
        data=csv,
        file_name='inventario_filtrado.csv',
        mime='text/csv',
    )