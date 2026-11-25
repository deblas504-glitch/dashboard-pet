import re
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests
from packaging.version import Version
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(layout="wide", page_title="PVD LOGÍSTICA - Dashboard")

AZUL_BARRA = "#002d5a"
MAGENTA = "#b5006a"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@700&display=swap');
    html, body, [class*="st-"] {{
        font-family: "Franklin Gothic Demi Cond", "Franklin Gothic Medium Cond", "Arial Narrow", sans-serif;
    }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_BARRA}; }}
    [data-testid="stSidebar"] * {{ color: white !important; font-family: "Franklin Gothic Demi Cond", sans-serif; }}
    h1, h2, h3 {{ font-family: "Franklin Gothic Demi Cond", sans-serif !important; font-weight: bold; }}
    div[data-testid="stDataFrame"] > div {{ overflow-x: auto; }}
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE ACCESO
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso PVD LOGÍSTICA")
    clave = st.text_input("Contraseña:", type="password")
    if st.button("Entrar"):
        if clave == "MARSPET2026":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# 3. CARGA DE DATOS (directo de Logify → "Nuevo Reportes", se refresca cada hora)
LOGIFY_URL = "https://cliente.logify.com.mx"
LOGIFY_CLIENTE = "MRS"
LOGIFY_PROYECTO = "0001"                  # 0001-Exhibidores
ACTUALIZAR_CADA = 60 * 60                 # inventario: cada hora (segundos)
CATALOGO_CADA = 24 * 60 * 60              # catálogo (fotos): una vez al día
ESPERA_BOTON = 10 * 60                    # mínimo entre clics de "Actualizar ahora"
REINTENTO_ERROR = 5 * 60                  # si Logify falla, esperar antes de reintentar
HORA_MX = timezone(timedelta(hours=-6))   # Centro de México (sin horario de verano)

# Cada almacén se ubica por la ciudad que trae en su nombre (columna 'Nombre').
# clave (minúsculas, sin acentos) -> (Ciudad, Estado, latitud, longitud)
# Si abren un almacén nuevo, solo agreguen una línea aquí.
UBICACIONES = {
    "acapulco":        ("Acapulco",         "Guerrero",          16.85,  -99.88),
    "vallejo":         ("Ciudad de México", "Ciudad de México",  19.49,  -99.15),
    "chihuahua":       ("Chihuahua",        "Chihuahua",         28.63, -106.07),
    "cuernavaca":      ("Cuernavaca",       "Morelos",           18.92,  -99.23),
    "culiacan":        ("Culiacán",         "Sinaloa",           24.80, -107.39),
    "guadalajara":     ("Guadalajara",      "Jalisco",           20.67, -103.35),
    "hermosillo":      ("Hermosillo",       "Sonora",            29.07, -110.96),
    "leon":            ("León",             "Guanajuato",        21.12, -101.68),
    "merida":          ("Mérida",           "Yucatán",           20.97,  -89.62),
    "mexicali":        ("Mexicali",         "Baja California",   32.62, -115.45),
    "monterrey":       ("Monterrey",        "Nuevo León",        25.69, -100.32),
    "morelia":         ("Morelia",          "Michoacán",         19.70, -101.19),
    "oaxaca":          ("Oaxaca",           "Oaxaca",            17.07,  -96.73),
    "puebla":          ("Puebla",           "Puebla",            19.04,  -98.21),
    "queretaro":       ("Querétaro",        "Querétaro",         20.59, -100.39),
    "san luis potosi": ("San Luis Potosí",  "San Luis Potosí",   22.15, -100.98),
    "tampico":         ("Tampico",          "Tamaulipas",        22.23,  -97.86),
    "tijuana":         ("Tijuana",          "Baja California",   32.51, -117.04),
    "toluca":          ("Toluca",           "Estado de México",  19.29,  -99.66),
    "torreon":         ("Torreón",          "Coahuila",          25.54, -103.41),
    "veracruz":        ("Veracruz",         "Veracruz",          19.17,  -96.13),
    "villahermosa":    ("Villahermosa",     "Tabasco",           17.99,  -92.93),
}
_PATRONES = [(re.compile(rf"\b{re.escape(k)}\b"), v) for k, v in UBICACIONES.items()]
_SIN_UBICACION = (None, None, float("nan"), float("nan"))


def _norm(valor):
    """Texto comparable: sin acentos, minúsculas, sin espacios extra. Vacío -> ''."""
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode("ascii")
    return " ".join(texto.lower().split())


def ubicar_almacen(nombre):
    """'GUADALAJARA PVD' -> ('Guadalajara', 'Jalisco', 20.67, -103.35)"""
    texto = _norm(nombre)
    for patron, datos in _PATRONES:
        if patron.search(texto):
            return datos
    return _SIN_UBICACION


def _credenciales_logify():
    """Usuario y contraseña de Logify desde los secrets de Streamlit (nunca en el código)."""
    try:
        return st.secrets["logify"]["usuario"], st.secrets["logify"]["contrasena"]
    except Exception:
        raise RuntimeError(
            "faltan las credenciales. Agrega en los secrets de Streamlit: "
            '[logify] usuario = "..." y contrasena = "..."'
        ) from None


def _pedir_reporte(sesion, reporte):
    """El mismo dato que 'Nuevo Reportes → Descargar Excel', pero en JSON."""
    r = sesion.get(
        f"{LOGIFY_URL}/WMS/{LOGIFY_PROYECTO}/Get/{reporte}",
        headers={"Accept": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    if "json" not in r.headers.get("Content-Type", ""):
        # Si no se abrió la sesión, Logify regresa su página de inicio de sesión
        raise RuntimeError("Logify no entregó datos; revisa el usuario y la contraseña en los secrets.")
    datos = r.json()
    return datos if isinstance(datos, list) else datos.get("data", [])


def _pedir_catalogo(sesion):
    """Catálogo de productos (de aquí salen las fotos). Si falla, la app sigue sin fotos."""
    try:
        r = sesion.get(f"{LOGIFY_URL}/WMS/Catalogo/Get", timeout=60)
        r.raise_for_status()
        datos = r.json()  # Logify lo manda marcado como HTML, pero es JSON
        return datos if isinstance(datos, list) else datos.get("data", [])
    except Exception:
        return []


def descargar_logify(usuario, contrasena, con_catalogo=True):
    """Inicia sesión como en la página y trae los reportes de inventario (y el catálogo si se pide)."""
    with requests.Session() as s:
        r = s.post(f"{LOGIFY_URL}/login",
                   data={"usuario": usuario, "contrasena": contrasena}, timeout=30)
        r.raise_for_status()
        # La cuenta tiene varios proyectos: fija 0001-Exhibidores
        s.post(f"{LOGIFY_URL}/changebranch",
               data={"url_local": f"/WMS/{LOGIFY_PROYECTO}/Reporting",
                     "client_code_main": LOGIFY_CLIENTE,
                     "branch_number_main": LOGIFY_PROYECTO},
               timeout=30)
        return (_pedir_reporte(s, "stock-almacen"),
                _pedir_reporte(s, "stock-lote"),
                _pedir_catalogo(s) if con_catalogo else [])


# Nombres de Logify -> nombres que usa el resto de la app
COLUMNAS_LOGIFY = {
    "codigo": "código", "descripcion": "Descripción", "disponible": "Disponible",
    "apartado": "Apartados", "total": "Total", "almacen": "Nombre", "canal": "Canal",
    "arte": "Clasificación", "campaign": "Campaña",
}


def _url_foto(producto):
    """Liga pública de la imagen del producto: la 'ficha' y, si no hay, la 'foto'."""
    for campo in ("ficha_prod", "foto_prod"):
        archivo = str(producto.get(campo) or "").strip()
        if archivo:
            return f"{LOGIFY_URL}/assets/inventario/{quote(archivo)}"
    return None


def armar_inventario(stock_almacen, stock_lote, catalogo=None):
    """Une 'Stock por almacén' con 'Stock por lote', la foto del catálogo y la ubicación del almacén."""
    llave = ["almacen", "codigo", "canal"]
    df = pd.DataFrame(stock_almacen)
    if df.empty:
        raise RuntimeError("Logify regresó el reporte de stock vacío.")
    faltan = [c for c in llave if c not in df.columns]
    if faltan:
        raise RuntimeError(f"el reporte de Logify cambió de formato (faltan: {', '.join(faltan)}).")
    df[llave] = df[llave].astype(str)

    # Estado del material y AÑO (fecha de ingreso) vienen del reporte por lote.
    # Si un producto tiene varios lotes en el mismo almacén, manda el lote con más piezas.
    lot = pd.DataFrame(stock_lote)
    if set(llave + ["stock", "fecha_ingreso", "estado"]).issubset(lot.columns):
        lot[llave] = lot[llave].astype(str)
        lot["stock"] = pd.to_numeric(lot["stock"], errors="coerce").fillna(0)
        lot["AÑO"] = pd.to_datetime(lot["fecha_ingreso"], errors="coerce").dt.year.astype("Int64")
        principal = (
            lot.sort_values("stock", ascending=False)
            .drop_duplicates(llave)
            .rename(columns={"estado": "Estado de material"})
            [llave + ["Estado de material", "AÑO"]]
        )
        df = df.merge(principal, on=llave, how="left")

    df = df.rename(columns=COLUMNAS_LOGIFY)
    for col in ["Disponible", "Apartados", "Total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Foto: liga a la imagen que el producto tiene en 'Catálogo de productos'
    fotos = {}
    for producto in catalogo or []:
        sku, url = str(producto.get("sku_prod") or "").strip(), _url_foto(producto)
        if sku and url and sku not in fotos:
            fotos[sku] = url
    df["Foto"] = df["código"].map(fotos)

    # Ciudad, Estado y coordenadas = ciudad del almacén (donde físicamente está el material)
    ubic = pd.DataFrame(
        [ubicar_almacen(n) for n in df["Nombre"]],
        columns=["Ciudad", "Estado", "lat_i", "lon_i"],
        index=df.index,
    )
    ubic[["lat_i", "lon_i"]] = ubic[["lat_i", "lon_i"]].astype(float)
    return df.join(ubic)


@st.cache_resource
def _memoria_logify():
    """Memoria compartida por todos los usuarios de la app (se borra si la app se reinicia)."""
    return {"catalogo": [], "catalogo_fecha": None, "error": None, "error_fecha": None}


@st.cache_data(ttl=ACTUALIZAR_CADA, show_spinner="Descargando inventario de Logify…")
def load_data():
    # Si algo falla, el error NO se guarda en caché (ver _cargar_con_freno)
    mem = _memoria_logify()
    ahora = datetime.now(HORA_MX)
    # El catálogo (fotos) casi no cambia: se pide en la misma sesión, pero solo 1 vez al día
    pedir_catalogo = (mem["catalogo_fecha"] is None
                      or ahora - mem["catalogo_fecha"] > timedelta(seconds=CATALOGO_CADA))
    usuario, contrasena = _credenciales_logify()
    stock_almacen, stock_lote, catalogo = descargar_logify(usuario, contrasena, pedir_catalogo)
    if catalogo:  # solo se reemplaza si llegó bien; si falló, se reintenta en la siguiente carga
        mem["catalogo"], mem["catalogo_fecha"] = catalogo, ahora
    return armar_inventario(stock_almacen, stock_lote, mem["catalogo"]), ahora


def _cargar_con_freno():
    """Si Logify está fallando, no vuelve a iniciar sesión en cada clic: espera REINTENTO_ERROR."""
    mem = _memoria_logify()
    ahora = datetime.now(HORA_MX)
    if mem["error_fecha"] and ahora - mem["error_fecha"] < timedelta(seconds=REINTENTO_ERROR):
        reintento = mem["error_fecha"] + timedelta(seconds=REINTENTO_ERROR)
        raise RuntimeError(f"{mem['error']} (siguiente intento a las {reintento:%H:%M})")
    try:
        resultado = load_data()
    except Exception as e:
        mem["error"], mem["error_fecha"] = str(e), ahora
        raise
    mem["error"] = mem["error_fecha"] = None
    return resultado


try:
    df_master, actualizado = _cargar_con_freno()
except Exception as e:
    st.error(f"No se pudo cargar el inventario de Logify: {e}")
    df_master, actualizado = pd.DataFrame(), None

if not df_master.empty:
    sin_ubicar = sorted(df_master.loc[df_master["lat_i"].isna(), "Nombre"].dropna().astype(str).unique())
    if sin_ubicar:
        st.warning("Almacenes sin ubicación en el mapa (agrégalos a UBICACIONES): " + ", ".join(sin_ubicar))

# 4. FUNCIÓN LIQUID FILL
def draw_liquid_fill(percent):
    level = 100 - percent
    return f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 260px;">
        <div style="width: 200px; height: 200px; border-radius: 50%; border: 6px solid {AZUL_BARRA}; position: relative; overflow: hidden; background: #f0f0f0;">
            <div style="position: absolute; width: 200%; height: 200%; top: {level}%; left: -50%; background: {MAGENTA}; border-radius: 40%; animation: wave_animation 5s linear infinite;"></div>
            <div style="position: absolute; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-family: 'Franklin Gothic Demi Cond', sans-serif; font-size: 42px; font-weight: bold; color: {'white' if percent > 55 else AZUL_BARRA}; z-index: 10;">
                {percent:.1f}%
            </div>
        </div>
    </div>
    <style> @keyframes wave_animation {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }} </style>
    """

# 5. FUNCIÓN AUXILIAR SELECTBOX
def get_options(df, column_name, first_option="Todas"):
    if column_name in df.columns:
        vals = sorted(df[column_name].dropna().unique().astype(str).tolist())
        return [first_option] + vals
    return [first_option]

# 5b. FOTO EN GRANDE (ventana encima de la app, sin abrir otra pestaña)
# Desde Streamlit 1.49 se puede dar clic directo a una celda; antes solo a la casilla del renglón.
CLIC_EN_CELDA = Version(st.__version__) >= Version("1.49.0")


@st.dialog("Foto del producto", width="large")
def ver_foto(fila):
    st.image(fila["Foto"])
    st.markdown(f"**{fila['código']}** · {fila['Descripción']}")
    st.caption(f"{fila['Nombre']} · {fila['Canal']} · Disponible: {fila['Disponible']:,.0f}")
    st.link_button("Abrir imagen original", fila["Foto"])


def _al_seleccionar_foto():
    """Se ejecuta al dar clic en la tabla: anota qué foto abrir y limpia la selección,
    para que el mismo 📷 se pueda volver a abrir después de cerrar la ventana."""
    seleccion = st.session_state.get("tabla_inventario", {}).get("selection", {})
    celdas = [fila for fila, columna in seleccion.get("cells", []) if columna == "📷"]
    filas = list(seleccion.get("rows", []))
    destino = celdas[0] if celdas else (filas[0] if filas else None)
    if destino is None:
        return  # clic en otra columna: no abre nada
    st.session_state.foto_pendiente = destino
    try:
        st.session_state.tabla_inventario = {"selection": {"rows": [], "columns": [], "cells": []}}
    except Exception:
        pass  # versiones viejas no permiten limpiar la selección; solo no se re-abre con el mismo clic


def abrir_foto_pendiente(df_vista):
    """Abre la ventana una sola vez por clic (no en cada recarga de la página)."""
    destino = st.session_state.pop("foto_pendiente", None)
    if destino is None or destino >= len(df_vista):
        return
    fila = df_vista.iloc[destino]
    if pd.notna(fila.get("Foto")):
        ver_foto(fila)
    else:
        st.toast("Este producto no tiene foto en Logify.")

# 6. MENÚ LATERAL
with st.sidebar:
    st.header("PVD LOGÍSTICA")
    menu = st.radio("Sección del Sistema:", ["📦 Gestión de Inventario", "✨ Nuevas Campañas", "📊 Análisis 360"])
    if actualizado is not None:
        st.caption(f"Inventario Logify · actualizado {actualizado:%d/%m/%Y %H:%M}")
    if st.button("🔄 Actualizar ahora"):
        # Freno: entre actualizaciones deben pasar al menos ESPERA_BOTON (cuenta para todos los usuarios)
        siguiente = actualizado + timedelta(seconds=ESPERA_BOTON) if actualizado else None
        if siguiente and datetime.now(HORA_MX) < siguiente:
            st.toast(f"Los datos son de las {actualizado:%H:%M}. "
                     f"Puedes volver a actualizar a las {siguiente:%H:%M}.")
        else:
            load_data.clear()
            st.rerun()
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# 7. VISTA: GESTIÓN DE INVENTARIO
if menu == "📦 Gestión de Inventario":
    st.title("📦 Gestión de Inventario")

    if not df_master.empty:
        r1c1, r1c2 = st.columns([1, 2])
        with r1c1:
            sel_alm = st.selectbox("Almacén", get_options(df_master, 'Nombre'))
        with r1c2:
            search_t = st.text_input("Buscador Descripción / SKU", placeholder="Escribe para buscar...")

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            sel_cl = st.selectbox("Clasificación", get_options(df_master, 'Clasificación'))
        with r2c2:
            sel_ca = st.selectbox("Campaña", get_options(df_master, 'Campaña'))
        with r2c3:
            sel_cn = st.selectbox("Canal", get_options(df_master, 'Canal'))

        df_t = df_master.copy()
        if sel_alm != "Todas": df_t = df_t[df_t['Nombre'].astype(str) == sel_alm]
        if search_t:
            df_t = df_t[df_t['Descripción'].astype(str).str.contains(search_t, case=False, na=False) |
                        df_t['código'].astype(str).str.contains(search_t, case=False, na=False)]
        if sel_cl != "Todas": df_t = df_t[df_t['Clasificación'].astype(str) == sel_cl]
        if sel_ca != "Todas": df_t = df_t[df_t['Campaña'].astype(str) == sel_ca]
        if sel_cn != "Todas": df_t = df_t[df_t['Canal'].astype(str) == sel_cn]

        cols_t = ['código', 'Descripción', 'Foto', 'Disponible', 'Apartados', 'Total', 'Nombre', 'Ciudad', 'Estado', 'Canal', 'Clasificación', 'Campaña', 'Estado de material', 'AÑO', 'Unidad']
        cols_validas = [c for c in cols_t if c in df_t.columns]

        # En pantalla, 📷 solo indica que hay foto; la liga (columna Foto) queda oculta.
        # El CSV de abajo sí incluye la liga.
        df_vista = df_t[cols_validas].reset_index(drop=True)
        df_vista.insert(df_vista.columns.get_loc('Foto'), '📷',
                        df_vista['Foto'].notna().map({True: '📷', False: ''}))

        if CLIC_EN_CELDA:
            st.caption("📷 Da clic en la camarita de un producto para ver su foto en grande.")
        else:
            st.caption("📷 Marca la casilla de un producto (a la izquierda) para ver su foto en grande.")
        st.dataframe(
            df_vista, use_container_width=True, hide_index=True,
            on_select=_al_seleccionar_foto, key="tabla_inventario",
            selection_mode=["single-row", "single-cell"] if CLIC_EN_CELDA else "single-row",
            column_config={
                "Foto": None,
                "📷": st.column_config.TextColumn("📷", width="small",
                                                  help="Da clic para ver la foto en grande"),
            },
        )
        abrir_foto_pendiente(df_vista)
        st.download_button("📥 Reporte CSV", df_t[cols_validas].to_csv(index=False).encode('utf-8'), "inventario.csv", "text/csv")

# 8. VISTA: NUEVAS CAMPAÑAS
elif menu == "✨ Nuevas Campañas":
    st.title("✨ Nuevas Campañas")
    st.info("📦 Sección en preparación.")

# 9. VISTA: ANÁLISIS 360
else:
    st.title("📊 Análisis 360 - Dashboard")

    if not df_master.empty:
        c1, c2 = st.columns(2)
        with c1: canal_d = st.selectbox("Canal Dashboard", get_options(df_master, 'Canal', "Todos"))
        with c2: camp_d = st.selectbox("Campaña Dashboard", get_options(df_master, 'Campaña'))

        df_d = df_master.copy()
        if canal_d not in ["Todos", "Todas"]: df_d = df_d[df_d['Canal'].astype(str) == canal_d]
        if camp_d != "Todas": df_d = df_d[df_d['Campaña'].astype(str) == camp_d]

        # KPIs
        col_dash1, col_dash2 = st.columns([1, 2])
        with col_dash1:
            total_g = df_master['Disponible'].sum() if 'Disponible' in df_master.columns else 0
            total_f = df_d['Disponible'].sum() if 'Disponible' in df_d.columns else 0
            porc = (total_f / total_g * 100) if total_g > 0 else 0
            st.components.v1.html(draw_liquid_fill(porc), height=280)

        with col_dash2:
            st.markdown(f"""<div style='text-align:center; padding:45px; background:{MAGENTA}; border-radius:15px; color:white; margin-top:20px;'><p style='margin:0; font-size:20px;'>Inventario Disponible</p><h1 style='font-size: 80px; margin:0;'>{total_f:,.0f}</h1></div>""", unsafe_allow_html=True)

        st.markdown("---")
        g1, g2, g3 = st.columns(3)

        with g1:
            st.subheader("🗺️ Cobertura")
            df_mapa = df_d.dropna(subset=['lat_i', 'lon_i'])
            if not df_mapa.empty:
                # Una burbuja por ciudad (Monterrey DTS + Monterrey PVD se suman)
                df_mapa = (
                    df_mapa.groupby(['Ciudad', 'Estado', 'lat_i', 'lon_i'], as_index=False, dropna=False)
                    .agg(Disponible=('Disponible', 'sum'),
                         Almacenes=('Nombre', lambda s: ', '.join(sorted(s.astype(str).unique()))))
                )
                # El tamaño de la burbuja no acepta negativos (hay ajustes con Disponible < 0)
                df_mapa['Tamaño'] = df_mapa['Disponible'].clip(lower=0)
                if df_mapa['Tamaño'].max() == 0:
                    df_mapa['Tamaño'] = 1
                try:
                    fig_map = px.scatter_mapbox(
                        df_mapa, lat="lat_i", lon="lon_i", size="Tamaño", color="Disponible",
                        hover_name="Ciudad",
                        hover_data={"Estado": True, "Almacenes": True, "Disponible": True,
                                    "Tamaño": False, "lat_i": False, "lon_i": False},
                        color_continuous_scale=[AZUL_BARRA, MAGENTA], size_max=30,
                        center={"lat": 23.6, "lon": -102.5}, zoom=3.3,
                        mapbox_style="carto-positron", height=300,
                    )
                    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig_map, use_container_width=True)
                except Exception as e:
                    st.warning(f"No se pudo dibujar el mapa: {e}")
            else: st.info("No hay coordenadas para graficar.")

        with g2:
            st.subheader("📊 Almacenes")
            if 'Nombre' in df_d.columns and not df_d.empty:
                df_rank = df_d.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible')
                if not df_rank.empty:
                    fig_bar = px.bar(df_rank, x="Disponible", y="Nombre", orientation='h', height=300)
                    st.plotly_chart(fig_bar, use_container_width=True)

        with g3:
            st.subheader("🟣 Campaña")
            if not df_d.empty and {'Campaña', 'Canal', 'Disponible'}.issubset(df_d.columns):
                # Un punto por Campaña + Canal con su total (en vez de un punto por renglón)
                df_camp = df_d.groupby(['Campaña', 'Canal'], as_index=False)['Disponible'].sum()
                # El tamaño no acepta negativos: sin existencia = sin burbuja
                df_camp['Tamaño'] = df_camp['Disponible'].clip(lower=0)
                if df_camp.empty:
                    st.info("Datos insuficientes para dispersión.")
                else:
                    if df_camp['Tamaño'].max() == 0:
                        df_camp['Tamaño'] = 1
                    try:
                        fig_scat = px.scatter(
                            df_camp, x="Campaña", y="Canal", size="Tamaño",
                            hover_data={"Disponible": True, "Tamaño": False},
                            color_discrete_sequence=[MAGENTA], size_max=30, height=300,
                        )
                        st.plotly_chart(fig_scat, use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pudo dibujar la gráfica: {e}")
            else: st.info("Datos insuficientes para dispersión.")
