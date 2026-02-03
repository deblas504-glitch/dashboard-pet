import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN Y ACCESO
st.set_page_config(layout="wide", page_title="Control PET - Dashboard Maestro")

MAGENTA = "#b5006a"
AZUL_PROFUNDO = "#002d5a"

# --- LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema PET")
    clave = st.text_input("Clave de acceso:", type="password")
    if st.button("Entrar"):
        if clave == "12345":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# 2. CARGA DE DATOS
SHEET_ID = "1lHr6sup1Ft59WKqh8gZkC4bXnehw5rM6O-aEr6WmUyc"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel(URL)
    df.columns = df.columns.str.strip()
    return df

df_master = load_data()

# 3. BARRA LATERAL
with st.sidebar:
    st.title("📂 Menú Principal")
    menu = st.radio("Selecciona Vista:", ["Análisis de Inventario", "Tabla de Inventario"])
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 4. VISTA: ANÁLISIS (GRÁFICAS)
if menu == "Análisis de Inventario":
    st.title("📊 Análisis Estratégico")
    
    # KPI Principal
    disp_total = df_master['Disponible'].sum()
    st.markdown(f"""
        <div style="background:{MAGENTA}; color:white; padding:25px; border-radius:15px; text-align:center; margin-bottom:25px;">
            <p style="margin:0; font-size: 1.2rem;">Total Disponible</p>
            <h1 style="margin:0; font-size: 3.5rem;">{disp_total:,.0f}</h1>
        </div>""", unsafe_allow_html=True)

    # Gráfica de Almacenes
    df_viz = df_master.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible')
    fig_bar = px.bar(df_viz, x="Disponible", y="Nombre", orientation='h',
                     color="Disponible", color_continuous_scale=[[0, AZUL_PROFUNDO], [1, MAGENTA]],
                     template="plotly_dark")
    st.plotly_chart(fig_bar, use_container_width=True)

# 5. VISTA: TABLA (ORDEN R -> DISPONIBLE)
else:
    st.title("📋 Tabla Maestra de Inventario")
    
    # FILTROS EN HORIZONTAL (Como en tu foto)
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_c = st.selectbox("Canal", ["Todos"] + sorted(df_master['Canal'].unique().tolist()))
    with f2:
        sel_p = st.selectbox("Campaña", ["Todas"] + sorted(df_master['Campaña'].unique().tolist()))
    with f3:
        sel_l = st.selectbox("Clasificación", ["Todas"] + sorted(df_master['Clasificación'].unique().tolist()))

    # Aplicar Filtros
    df_tab = df_master.copy()
    if sel_c != "Todos": df_tab = df_tab[df_tab['Canal'] == sel_c]
    if sel_p != "Todas": df_tab = df_tab[df_tab['Campaña'] == sel_p]
    if sel_l != "Todas": df_tab = df_tab[df_tab['Clasificación'] == sel_l]

    # SELECCIÓN DE COLUMNAS: C, D, E, H, I, J, K, L, R, Disponible
    # El índice 17 es R y el 18 es Disponible
    indices_finales = [2, 3, 4, 7, 8, 9, 10, 11, 17, 18]
    cols_visibles = [df_master.columns[i] for i in indices_finales if i < len(df_master.columns)]

    # Mostrar Tabla
    st.dataframe(df_tab[cols_visibles], use_container_width=True, hide_index=True)
    
    # Botón de Descarga
    csv = df_tab[cols_visibles].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exportar Reporte", csv, "reporte_pet.csv", "text/csv")