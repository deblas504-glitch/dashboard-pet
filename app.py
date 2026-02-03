import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA Y ACCESO
st.set_page_config(layout="wide", page_title="Control PET - Acceso Seguro")

# Estilos de Marca
MAGENTA = "#b5006a"
AZUL_PROFUNDO = "#002d5a"

# --- SISTEMA DE LOGUEO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema PET")
    clave = st.text_input("Introduce la clave de acceso:", type="password")
    if st.button("Entrar"):
        if clave == "12345": # Clave solicitada
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# 2. CARGA DE DATOS (GOOGLE SHEETS)
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    df.columns = df.columns.str.strip() # Limpieza de nombres
    return df

df_master = load_data()

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🚀 Gestión de Inventarios")
    menu = st.radio("Sección:", ["Análisis de Inventario", "Tabla Maestra"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 4. VISTA: ANÁLISIS DE INVENTARIO
if menu == "Análisis de Inventario":
    st.title("📊 Análisis Estratégico")
    
    # Filtro de Canal
    lista_canales = ["Todos"] + sorted(df_master['Canal'].unique().tolist())
    canal_sel = st.selectbox("Seleccionar Canal:", lista_canales)
    
    df_ana = df_master.copy()
    if canal_sel != "Todos":
        df_ana = df_master[df_master['Canal'] == canal_sel]

    # Cálculo de Disponibilidad
    total_disponible = df_ana['Disponible'].sum()
    
    st.markdown(f"""
        <div style="background:{MAGENTA}; color:white; padding:20px; border-radius:12px; text-align:center; margin-bottom:20px;">
            <p style="margin:0; font-size: 20px;">Inventario Disponible en {canal_sel}</p>
            <h1 style="margin:0; font-size: 50px;">{total_disponible:,.0f}</h1>
        </div>""", unsafe_allow_html=True)

    # Gráfica de Barras por Almacén
    df_viz = df_ana.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible')
    fig_bar = px.bar(df_viz, x="Disponible", y="Nombre", orientation='h',
                     color="Disponible", color_continuous_scale=[[0, AZUL_PROFUNDO], [1, MAGENTA]],
                     template="plotly_dark")
    st.plotly_chart(fig_bar, use_container_width=True)

# 5. VISTA: TABLA MAESTRA (COLUMNA R JUNTO A DISPONIBLE)
else:
    st.title("📋 Tabla de Inventario Detallada")
    
    # Filtros superiores
    f1, f2, f3 = st.columns(3)
    with f1: sel_c = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with f2: sel_p = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f3: sel_l = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))

    df_tabla = df_master.copy()
    if sel_c != "Todos": df_tabla = df_tabla[df_tabla['Canal'] == sel_c]
    if sel_p != "Todas": df_tabla = df_tabla[df_tabla['Campaña'] == sel_p]
    if sel_l != "Todas": df_tabla = df_tabla[df_tabla['Clasificación'] == sel_l]

    # Selección de columnas: C, D, E, H, I, J, K, L, R, Disponible
    # Los índices 17 (R) y 18 (Disponible) quedan juntos al final
    indices_finales = [2, 3, 4, 7, 8, 9, 10, 11, 17, 18]
    columnas_visibles = [df_master.columns[i] for i in indices_finales if i < len(df_master.columns)]

    st.markdown(f"**Mostrando {len(df_tabla)} registros filtrados:**")
    st.dataframe(df_tabla[columnas_visibles], use_container_width=True, hide_index=True)

    # Botón de descarga
    csv = df_tabla[columnas_visibles].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Reporte Personalizado", csv, "inventario_pet.csv", "text/csv")