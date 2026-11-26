import base64
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

# 1. CONFIGURACIÓN Y ESTILO (neo brutalista PVD: bordes gruesos, sombras sólidas, Jost)
st.set_page_config(layout="wide", page_title="PVD · Reporte de inventario")

TINTA = "#0B1530"       # bordes, sombras y texto
AZUL_BARRA = "#002d5a"  # azul marino PVD
AZUL = "#1F6FC4"
CIAN = "#27B4EA"
MAGENTA = "#b5006a"

ESTILO_PVD = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700;800;900&display=swap');
.stApp{background:#EEF3F9;color:#0B1530}
.stApp,.stApp p,.stApp span,.stApp div,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp li{font-family:'Jost',system-ui,sans-serif}
.stApp [data-testid="stIconMaterial"],.stApp [class*="material-symbols"]{font-family:'Material Symbols Rounded' !important}
[data-testid="stHeader"]{background:transparent}
[data-testid="stDecoration"]{display:none}
.block-container,[data-testid="stMainBlockContainer"]{padding-top:2rem}
.stApp [data-testid="stMarkdownContainer"] p{color:#0B1530}
[data-testid="InputInstructions"]{display:none}
[data-testid="stWidgetLabel"] p{font-size:13px !important;font-weight:800 !important;letter-spacing:.1em;text-transform:uppercase;color:#0B1530}
.stTextInput [data-baseweb="input"],.stSelectbox [data-baseweb="select"]>div{border:3px solid #0B1530 !important;border-radius:0 !important;background:#FFFFFF !important;box-shadow:4px 4px 0 #0B1530}
.stTextInput [data-baseweb="base-input"],.stTextInput input{background:#FFFFFF !important;color:#0B1530 !important;font-weight:500}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button,.stLinkButton>a{background:#27B4EA !important;color:#0B1530 !important;border:3px solid #0B1530 !important;border-radius:0 !important;box-shadow:4px 4px 0 #0B1530;font-weight:800 !important;letter-spacing:.08em;text-transform:uppercase;transition:transform .08s ease,box-shadow .08s ease}
.stButton>button p,.stDownloadButton>button p,.stFormSubmitButton>button p,.stLinkButton>a p{font-weight:800 !important;color:#0B1530 !important}
.stButton>button:hover,.stDownloadButton>button:hover,.stFormSubmitButton>button:hover,.stLinkButton>a:hover{transform:translate(2px,2px);box-shadow:2px 2px 0 #0B1530}
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible,.stFormSubmitButton>button:focus-visible,.stLinkButton>a:focus-visible{outline:3px solid #B5006A;outline-offset:3px}
[data-testid="stDataFrame"]{border:3px solid #0B1530;box-shadow:6px 6px 0 #0B1530;background:#FFFFFF}
[data-testid="stAlertContainer"]{border:3px solid #0B1530;border-radius:0;box-shadow:4px 4px 0 #0B1530}
[class*="st-key-tarjeta"]{background:#FFFFFF;border:3px solid #0B1530;box-shadow:6px 6px 0 #0B1530;padding:16px}
[data-testid="stDialog"] [role="dialog"]{border:3px solid #0B1530;border-radius:0;box-shadow:8px 8px 0 #0B1530}
[data-testid="stSidebar"]{background:#002D5A;border-right:3px solid #0B1530}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#FFFFFF !important}
[data-testid="stSidebar"] [role="radiogroup"]{gap:10px}
[data-testid="stSidebar"] [role="radiogroup"] label{background:#FFFFFF;border:3px solid #0B1530;box-shadow:4px 4px 0 #27B4EA;padding:10px 12px;margin:0;width:100%;box-sizing:border-box}
[data-testid="stSidebar"] [role="radiogroup"] label p{color:#0B1530 !important;font-weight:800;letter-spacing:.04em;text-transform:uppercase}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#27B4EA;box-shadow:4px 4px 0 #FFFFFF}
[data-testid="stSidebar"] .st-key-btn_salir button{background:#FFFFFF !important}
.pvd-logo{display:inline-flex;align-items:center;gap:8px;background:#FFFFFF;border:3px solid #0B1530;box-shadow:4px 4px 0 #0B1530;padding:6px 14px 6px 10px}
.pvd-logo-texto{display:flex;flex-direction:column;line-height:1}
.pvd-logo-texto b{font-size:24px;font-weight:900;color:#0B1530}
.pvd-logo-texto small{font-size:8px;font-weight:700;letter-spacing:.26em;color:#0B1530}
.pvd-logo--oscuro{background:transparent;border:0;box-shadow:none;padding:0 0 8px}
.pvd-logo--oscuro .pvd-logo-texto b,.pvd-logo--oscuro .pvd-logo-texto small{color:#FFFFFF}
.pvd-encabezado{display:flex;flex-wrap:wrap;gap:12px;align-items:stretch;margin-bottom:6px}
.pvd-seccion{flex:1 1 260px;background:#002D5A;border:3px solid #0B1530;box-shadow:6px 6px 0 #0B1530;padding:10px 16px;display:flex;flex-direction:column;justify-content:center;gap:2px}
.pvd-seccion small{font-size:11px;font-weight:800;letter-spacing:.16em;color:#27B4EA}
.pvd-seccion span{font-size:34px;font-weight:900;line-height:1;text-transform:uppercase;color:#FFFFFF}
.pvd-hora{background:#B5006A;border:3px solid #0B1530;box-shadow:6px 6px 0 #0B1530;padding:8px 14px;display:flex;flex-direction:column;justify-content:center}
.pvd-hora small{font-size:10px;font-weight:800;letter-spacing:.14em;color:#FFFFFF}
.pvd-hora b{font-size:28px;font-weight:900;line-height:1;color:#FFFFFF}
.pvd-etiqueta{display:inline-block;background:#0B1530;color:#FFFFFF;font-size:13px;font-weight:800;letter-spacing:.16em;padding:5px 10px;margin:14px 0 4px;text-transform:uppercase}
.pvd-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:12px;margin:4px 0 14px}
.pvd-kpi{background:#FFFFFF;border:3px solid #0B1530;box-shadow:5px 5px 0 #0B1530;padding:10px 14px;display:flex;flex-direction:column;gap:2px}
.pvd-kpi small{font-size:11px;font-weight:800;letter-spacing:.14em;color:#0B1530}
.pvd-kpi b{font-size:30px;font-weight:900;line-height:1.05;color:#0B1530}
.pvd-kpi--cian{background:#27B4EA}
.pvd-kpi--magenta{background:#B5006A}
.pvd-kpi--magenta small,.pvd-kpi--magenta b{color:#FFFFFF}
.pvd-login-titulo{background:#002D5A;border:3px solid #0B1530;box-shadow:7px 7px 0 #0B1530;padding:22px 20px 24px;margin:18px 0 22px}
.pvd-login-titulo div{font-size:44px;font-weight:900;line-height:.92;text-transform:uppercase;color:#FFFFFF}
.pvd-login-titulo span{color:#27B4EA}
.pvd-total{background:#B5006A;border:3px solid #0B1530;box-shadow:7px 7px 0 #0B1530;padding:28px 24px;text-align:center;margin-top:12px}
.pvd-total small{display:block;font-size:14px;font-weight:800;letter-spacing:.16em;color:#FFFFFF}
.pvd-total b{display:block;font-size:76px;font-weight:900;line-height:1;color:#FFFFFF}
@media (max-width:640px){.pvd-seccion span{font-size:26px}.pvd-login-titulo div{font-size:36px}.pvd-total b{font-size:54px}}
</style>
"""


def _html(fragmento):
    """Pinta HTML propio en una sola línea (sin sangrías ni renglones vacíos, para que
    Markdown no lo convierta en bloque de código)."""
    st.markdown(" ".join(l.strip() for l in fragmento.strip().splitlines() if l.strip()),
                unsafe_allow_html=True)


def logo_html(oscuro=False):
    """Logo PVD: rombos en chevrón + PVD LOGÍSTICA."""
    c1, c2, c3 = (CIAN, "#FFFFFF", CIAN) if oscuro else (CIAN, AZUL, AZUL_BARRA)
    clase = "pvd-logo pvd-logo--oscuro" if oscuro else "pvd-logo"
    return (f'<div class="{clase}"><svg width="22" height="26" viewBox="0 0 34 40" aria-hidden="true">'
            f'<polygon points="10,3 15,8 10,13 5,8" fill="{c1}"/>'
            f'<polygon points="18,9 23,14 18,19 13,14" fill="{c2}"/>'
            f'<polygon points="26,15 31,20 26,25 21,20" fill="{c3}"/>'
            f'<polygon points="18,21 23,26 18,31 13,26" fill="{c2}"/>'
            f'<polygon points="10,27 15,32 10,37 5,32" fill="{c1}"/></svg>'
            '<div class="pvd-logo-texto"><b>PVD</b><small>LOGÍSTICA</small></div></div>')


_html(ESTILO_PVD)

# 2. SISTEMA DE ACCESO
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        _html(f"""
        <div style="margin-top:6vh">{logo_html()}</div>
        <div class="pvd-login-titulo" role="heading" aria-level="1">
        <div>Reporte de inventario y análisis de stock<span>.</span></div>
        </div>
        """)
        with st.container(key="tarjeta_login"):
            with st.form("form_login", border=False):
                clave = st.text_input("Contraseña", type="password", placeholder="Escribe tu clave de acceso")
                entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
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
    # Otras ciudades, para que un almacén nuevo se ubique solo
    "aguascalientes":  ("Aguascalientes",   "Aguascalientes",    21.88, -102.29),
    "cancun":          ("Cancún",           "Quintana Roo",      21.16,  -86.85),
    "chetumal":        ("Chetumal",         "Quintana Roo",      18.50,  -88.30),
    "playa del carmen": ("Playa del Carmen", "Quintana Roo",     20.63,  -87.08),
    "tuxtla":          ("Tuxtla Gutiérrez", "Chiapas",           16.75,  -93.12),
    "tapachula":       ("Tapachula",        "Chiapas",           14.90,  -92.26),
    "campeche":        ("Campeche",         "Campeche",          19.84,  -90.53),
    "ciudad del carmen": ("Ciudad del Carmen", "Campeche",       18.65,  -91.82),
    "ciudad juarez":   ("Ciudad Juárez",    "Chihuahua",         31.69, -106.42),
    "cd juarez":       ("Ciudad Juárez",    "Chihuahua",         31.69, -106.42),
    "saltillo":        ("Saltillo",         "Coahuila",          25.42, -101.00),
    "colima":          ("Colima",           "Colima",            19.24, -103.72),
    "manzanillo":      ("Manzanillo",       "Colima",            19.05, -104.32),
    "durango":         ("Durango",          "Durango",           24.02, -104.66),
    "celaya":          ("Celaya",           "Guanajuato",        20.52, -100.81),
    "irapuato":        ("Irapuato",         "Guanajuato",        20.67, -101.35),
    "chilpancingo":    ("Chilpancingo",     "Guerrero",          17.55,  -99.50),
    "pachuca":         ("Pachuca",          "Hidalgo",           20.10,  -98.76),
    "zapopan":         ("Zapopan",          "Jalisco",           20.72, -103.39),
    "gdl":             ("Guadalajara",      "Jalisco",           20.67, -103.35),
    "uruapan":         ("Uruapan",          "Michoacán",         19.42, -102.06),
    "tepic":           ("Tepic",            "Nayarit",           21.50, -104.89),
    "mty":             ("Monterrey",        "Nuevo León",        25.69, -100.32),
    "qro":             ("Querétaro",        "Querétaro",         20.59, -100.39),
    "slp":             ("San Luis Potosí",  "San Luis Potosí",   22.15, -100.98),
    "mazatlan":        ("Mazatlán",         "Sinaloa",           23.25, -106.41),
    "los mochis":      ("Los Mochis",       "Sinaloa",           25.79, -108.99),
    "ciudad obregon":  ("Ciudad Obregón",   "Sonora",            27.48, -109.93),
    "nogales":         ("Nogales",          "Sonora",            31.31, -110.94),
    "reynosa":         ("Reynosa",          "Tamaulipas",        26.09,  -98.28),
    "matamoros":       ("Matamoros",        "Tamaulipas",        25.87,  -97.50),
    "nuevo laredo":    ("Nuevo Laredo",     "Tamaulipas",        27.48,  -99.52),
    "ciudad victoria": ("Ciudad Victoria",  "Tamaulipas",        23.74,  -99.15),
    "tlaxcala":        ("Tlaxcala",         "Tlaxcala",          19.31,  -98.24),
    "xalapa":          ("Xalapa",           "Veracruz",          19.54,  -96.91),
    "coatzacoalcos":   ("Coatzacoalcos",    "Veracruz",          18.13,  -94.46),
    "zacatecas":       ("Zacatecas",        "Zacatecas",         22.77, -102.58),
    "la paz":          ("La Paz",           "Baja California Sur", 24.14, -110.31),
    "los cabos":       ("Los Cabos",        "Baja California Sur", 22.89, -109.91),
    "ensenada":        ("Ensenada",         "Baja California",   31.87, -116.60),
    "cdmx":            ("Ciudad de México", "Ciudad de México",  19.43,  -99.13),
}

# Si el almacén trae el ESTADO en el nombre (y no una ciudad de la lista), se ubica en el estado.
ESTADOS = {
    "Aguascalientes": (21.88, -102.28), "Baja California": (30.84, -115.28),
    "Baja California Sur": (26.04, -111.66), "Campeche": (19.83, -90.53),
    "Chiapas": (16.75, -93.12), "Chihuahua": (28.63, -106.06),
    "Ciudad de México": (19.43, -99.13), "Coahuila": (27.05, -101.70),
    "Colima": (19.24, -103.72), "Durango": (24.02, -104.65),
    "Estado de México": (19.35, -99.10), "Guanajuato": (21.01, -101.25),
    "Guerrero": (17.43, -99.54), "Hidalgo": (20.09, -98.76),
    "Jalisco": (20.65, -103.34), "Michoacán": (19.70, -101.18),
    "Morelos": (18.92, -99.23), "Nayarit": (21.50, -104.89),
    "Nuevo León": (25.68, -100.31), "Oaxaca": (17.07, -96.72),
    "Puebla": (19.04, -98.20), "Querétaro": (20.58, -100.38),
    "Quintana Roo": (19.18, -88.47), "San Luis Potosí": (22.15, -100.98),
    "Sinaloa": (24.80, -107.39), "Sonora": (29.07, -110.96),
    "Tabasco": (17.84, -92.61), "Tamaulipas": (23.73, -99.14),
    "Tlaxcala": (19.31, -98.23), "Veracruz": (19.17, -96.13),
    "Yucatán": (20.96, -89.59), "Zacatecas": (22.77, -102.58),
}
_SIN_UBICACION = (None, None, float("nan"), float("nan"))


def _norm(valor):
    """Texto comparable: sin acentos, minúsculas, sin espacios extra. Vacío -> ''."""
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode("ascii")
    return " ".join(texto.lower().split())


# Todas las claves (estados + ciudades). Una ciudad con el mismo nombre que su estado gana (Puebla, Oaxaca…).
_CLAVES = {_norm(e): (e, e, lat, lon) for e, (lat, lon) in ESTADOS.items()}
_CLAVES.update({"edomex": ("Estado de México", "Estado de México", 19.35, -99.10),
                "edo mex": ("Estado de México", "Estado de México", 19.35, -99.10)})
_CLAVES.update(UBICACIONES)
# La clave más larga se revisa primero: "nuevo leon" antes que "leon", "baja california sur" antes que "baja california"
_PATRONES = [(re.compile(rf"\b{re.escape(k)}\b"), v)
             for k, v in sorted(_CLAVES.items(), key=lambda kv: -len(kv[0]))]


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

# 4. TANQUE DE PORCENTAJE (agua que sube y se mueve, estilo neo brutalista PVD)
def draw_liquid_fill(percent):
    """El nivel del agua (magenta) es el % que la selección representa del inventario total.
    La ola en zigzag se desplaza como agua; la cifra va en una etiqueta para leerse a cualquier nivel."""
    nivel = max(0.0, min(100.0, percent))
    # Ola en zigzag: se repite cada 50 unidades, así al recorrerse medio ancho no se nota el corte
    cresta = " ".join(f"{x},{2 if (x // 25) % 2 else 8}" for x in range(0, 401, 25))
    return f"""
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@800;900&family=Space+Mono:wght@700&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:transparent;font-family:'Jost',sans-serif;color:{TINTA}}}
.envase{{display:flex;flex-direction:column;align-items:center;gap:14px;padding:8px 12px 14px}}
.fila{{display:flex;align-items:stretch;gap:16px}}
.tanque{{width:190px;height:220px;box-sizing:border-box;border:3px solid {TINTA};box-shadow:7px 7px 0 {TINTA};position:relative;overflow:hidden;background:#FFFFFF}}
.linea{{position:absolute;left:0;right:0;border-top:2px dashed #C3D0E2}}
.agua{{position:absolute;left:0;right:0;bottom:0;height:{nivel:.1f}%;background:{MAGENTA}}}
.ola{{position:absolute;left:0;top:-11px;width:200%;height:12px;animation:ola 2.8s linear infinite}}
.ola svg{{display:block;width:100%;height:12px}}
@keyframes ola{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
@media (prefers-reduced-motion:reduce){{.ola{{animation:none}}}}
.cifra{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-3deg);background:#FFFFFF;border:3px solid {TINTA};box-shadow:4px 4px 0 {TINTA};padding:4px 10px;font-size:38px;font-weight:900;line-height:1;white-space:nowrap;z-index:3}}
.escala{{display:flex;flex-direction:column;justify-content:space-between;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;margin:-6px 0}}
.rotulo{{background:{TINTA};color:#FFFFFF;font-size:12px;font-weight:800;letter-spacing:.14em;padding:4px 10px}}
</style>
<div class="envase">
<div class="fila">
<div class="tanque" role="img" aria-label="{percent:.1f}% del inventario total">
<div class="linea" style="top:25%"></div><div class="linea" style="top:50%"></div><div class="linea" style="top:75%"></div>
<div class="agua"><div class="ola"><svg viewBox="0 0 400 12" preserveAspectRatio="none" aria-hidden="true">
<polygon points="0,12 {cresta} 400,12" fill="{MAGENTA}"/>
<polyline points="{cresta}" fill="none" stroke="{TINTA}" stroke-width="3" vector-effect="non-scaling-stroke"/>
</svg></div></div>
<div class="cifra">{percent:.1f}%</div>
</div>
<div class="escala" aria-hidden="true"><span>100</span><span>75</span><span>50</span><span>25</span><span>0</span></div>
</div>
<div class="rotulo">DEL INVENTARIO TOTAL</div>
</div>
"""


def encabezado(seccion):
    """Barra superior de cada sección: logo, nombre de la sección y hora de la última carga."""
    hora = (f'<div class="pvd-hora"><small>ACTUALIZADO</small><b>{actualizado:%H:%M}</b></div>'
            if actualizado is not None else "")
    _html(f"""
    <div class="pvd-encabezado">
    {logo_html()}
    <div class="pvd-seccion" role="heading" aria-level="1"><small>REPORTE DE INVENTARIO Y ANÁLISIS DE STOCK</small><span>{seccion}</span></div>
    {hora}
    </div>
    """)


def etiqueta(texto):
    """Título de bloque: etiqueta negra con letras blancas."""
    _html(f'<div class="pvd-etiqueta">{texto}</div>')


def kpis(tarjetas):
    """Fila de indicadores: [(título, valor, variante)] con variante '', 'cian' o 'magenta'."""
    _html('<div class="pvd-kpis">' + "".join(
        f'<div class="pvd-kpi{" pvd-kpi--" + v if v else ""}"><small>{t}</small><b>{valor}</b></div>'
        for t, valor, v in tarjetas) + '</div>')


def estilo_grafica(fig):
    """Gráficas con la tipografía y colores PVD."""
    fig.update_layout(font=dict(family="Jost, sans-serif", color=TINTA, size=13),
                      paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                      margin=dict(l=8, r=8, t=8, b=8))
    fig.update_xaxes(gridcolor="#E4EBF4", zerolinecolor=TINTA)
    fig.update_yaxes(gridcolor="#E4EBF4", zerolinecolor=TINTA)
    return fig


def dibujar_cobertura(df):
    """Mapa de cobertura: cada almacén se ubica por la ciudad o el estado que trae en su nombre.
    Es un mapa dibujado por Plotly (sin Mapbox ni servicios de mapas externos)."""
    ubicados = df.dropna(subset=["lat_i", "lon_i"])
    sin_ubicar = sorted(df.loc[df["lat_i"].isna(), "Nombre"].dropna().astype(str).unique())
    kpis([("Estados", f"{ubicados['Estado'].nunique()}", "cian"),
          ("Ciudades", f"{ubicados['Ciudad'].nunique()}", ""),
          ("Almacenes", f"{ubicados['Nombre'].nunique()}", "")])
    if ubicados.empty:
        st.info("Ningún almacén de este filtro tiene ubicación.")
        return

    # Una burbuja por ciudad (Monterrey DTS + Monterrey PVD se suman)
    puntos = (ubicados.groupby(["Ciudad", "Estado", "lat_i", "lon_i"], as_index=False, dropna=False)
              .agg(Disponible=("Disponible", "sum"),
                   Almacenes=("Nombre", lambda s: ", ".join(sorted(s.astype(str).unique())))))
    # El tamaño no acepta negativos; 'sizemin' hace que hasta el almacén más chico se vea
    puntos["Tamaño"] = puntos["Disponible"].clip(lower=0)
    if puntos["Tamaño"].max() == 0:
        puntos["Tamaño"] = 1
    # Color por nivel (Vallejo es tan grande que una escala continua pintaría todo igual)
    if len(puntos) >= 3:
        puntos["Nivel"] = pd.qcut(puntos["Disponible"].rank(method="first"), 3,
                                  labels=["Bajo", "Medio", "Alto"]).astype(str)
    else:
        puntos["Nivel"] = "Alto"

    fig = px.scatter_geo(
        puntos, lat="lat_i", lon="lon_i", size="Tamaño", color="Nivel",
        color_discrete_map={"Alto": MAGENTA, "Medio": AZUL, "Bajo": CIAN},
        category_orders={"Nivel": ["Alto", "Medio", "Bajo"]},
        hover_name="Ciudad",
        hover_data={"Estado": True, "Almacenes": True, "Disponible": ":,.0f",
                    "Tamaño": False, "Nivel": False, "lat_i": False, "lon_i": False},
        size_max=34, height=400,
    )
    fig.update_traces(marker=dict(line=dict(color=TINTA, width=2), opacity=1, sizemin=8))
    # México en blanco con borde grueso; el resto del continente en gris
    mexico = go.Choropleth(locations=["MEX"], locationmode="ISO-3", z=[1],
                           colorscale=[[0, "#FFFFFF"], [1, "#FFFFFF"]], showscale=False,
                           marker_line_color=TINTA, marker_line_width=3, hoverinfo="skip")
    fig.add_trace(mexico)
    fig.data = (fig.data[-1],) + fig.data[:-1]  # México abajo, burbujas encima
    fig.update_geos(
        projection_type="mercator", lataxis_range=[13.5, 34], lonaxis_range=[-119, -85.5],
        resolution=50, showland=True, landcolor="#DCE4EE", showocean=True, oceancolor="#EEF3F9",
        showlakes=False, showcountries=True, countrycolor=TINTA, countrywidth=1.5,
        showcoastlines=True, coastlinecolor=TINTA, coastlinewidth=1.5,
        showframe=True, framecolor=TINTA, framewidth=3, bgcolor="#FFFFFF",
    )
    estilo_grafica(fig).update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(title_text="Inventario", orientation="h", yanchor="bottom", y=0.02,
                    xanchor="left", x=0.02, bgcolor="#FFFFFF", bordercolor=TINTA, borderwidth=2),
    )
    st.plotly_chart(fig, use_container_width=True)
    if sin_ubicar:
        st.caption("Sin ubicar (agrégalos a UBICACIONES): " + ", ".join(sin_ubicar))

# 5. FUNCIÓN AUXILIAR SELECTBOX
def get_options(df, column_name, first_option="Todas"):
    if column_name in df.columns:
        vals = sorted(df[column_name].dropna().unique().astype(str).tolist())
        return [first_option] + vals
    return [first_option]

# 5b. FOTO EN GRANDE (ventana encima de la app, sin abrir otra pestaña)
# Desde Streamlit 1.49 se puede dar clic directo a una celda; antes solo a la casilla del renglón.
CLIC_EN_CELDA = Version(st.__version__) >= Version("1.49.0")

# Camarita estilo PVD (cuerpo cian, contorno grueso en tinta, lente magenta) como imagen SVG
_SVG_CAMARITA = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 24">'
    '<rect x="11" y="2" width="10" height="5" fill="#0B1530"/>'
    '<rect x="2.5" y="5.5" width="27" height="16" fill="#27B4EA" stroke="#0B1530" stroke-width="3"/>'
    '<circle cx="16" cy="13.5" r="5" fill="#B5006A" stroke="#0B1530" stroke-width="3"/>'
    '<rect x="23" y="8.5" width="3" height="2.5" fill="#0B1530"/></svg>'
)
CAMARITA = "data:image/svg+xml;base64," + base64.b64encode(_SVG_CAMARITA.encode()).decode()


@st.dialog("Foto del producto", width="large")
def ver_foto(fila):
    st.image(fila["url_foto"])
    st.markdown(f"**{fila['código']}** · {fila['Descripción']}")
    st.caption(f"{fila['Nombre']} · {fila['Canal']} · Disponible: {fila['Disponible']:,.0f}")
    st.link_button("Abrir imagen original", fila["url_foto"])


def _al_seleccionar_foto():
    """Se ejecuta al dar clic en la tabla: anota qué foto abrir y limpia la selección,
    para que el mismo ◉ VER se pueda volver a abrir después de cerrar la ventana."""
    seleccion = st.session_state.get("tabla_inventario", {}).get("selection", {})
    celdas = [fila for fila, columna in seleccion.get("cells", []) if columna == "Foto"]
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
    if pd.notna(fila.get("url_foto")):
        ver_foto(fila)
    else:
        st.toast("Este producto no tiene foto en Logify.")

# 6. MENÚ LATERAL
SECCIONES = ["Gestión de inventario", "Nuevas campañas", "Análisis 360"]

with st.sidebar:
    _html(logo_html(oscuro=True))
    menu = st.radio("Menú", SECCIONES, format_func=lambda s: f"{SECCIONES.index(s) + 1:02d} · {s}")
    if actualizado is not None:
        st.caption(f"Inventario Logify · actualizado {actualizado:%d/%m/%Y %H:%M}")
    if st.button("Actualizar ahora", key="btn_actualizar", use_container_width=True):
        # Freno: entre actualizaciones deben pasar al menos ESPERA_BOTON (cuenta para todos los usuarios)
        siguiente = actualizado + timedelta(seconds=ESPERA_BOTON) if actualizado else None
        if siguiente and datetime.now(HORA_MX) < siguiente:
            st.toast(f"Los datos son de las {actualizado:%H:%M}. "
                     f"Puedes volver a actualizar a las {siguiente:%H:%M}.")
        else:
            load_data.clear()
            st.rerun()
    if st.button("Cerrar sesión", key="btn_salir", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# 7. VISTA: GESTIÓN DE INVENTARIO
if menu == SECCIONES[0]:
    encabezado("Gestión de inventario")

    if not df_master.empty:
        etiqueta("Filtros")
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

        etiqueta("Inventario")
        kpis([
            ("Renglones", f"{len(df_t):,}", ""),
            ("Productos", f"{df_t['código'].nunique():,}", ""),
            ("Disponible", f"{df_t['Disponible'].sum():,.0f}", "cian"),
            ("Apartados", f"{df_t['Apartados'].sum():,.0f}", "magenta"),
        ])

        cols_t =['código', 'Descripción', 'Foto', 'Disponible', 'Apartados', 'Total', 'Nombre', 'Ciudad', 'Estado', 'Canal', 'Clasificación', 'Campaña', 'Estado de material', 'AÑO', 'Unidad']
        cols_validas = [c for c in cols_t if c in df_t.columns]

        # En pantalla, la columna Foto solo dice "◉ VER" cuando hay foto; la liga queda oculta
        # (url_foto). El CSV de abajo sí incluye la liga.
        df_vista = df_t[cols_validas].reset_index(drop=True).rename(columns={'Foto': 'url_foto'})
        df_vista.insert(df_vista.columns.get_loc('url_foto'), 'Foto',
                        df_vista['url_foto'].notna().map({True: CAMARITA, False: None}))
        # Textos vacíos de Logify: una raya en lugar de "None"
        for col in ['Descripción', 'Nombre', 'Ciudad', 'Estado', 'Canal', 'Clasificación',
                    'Campaña', 'Estado de material']:
            if col in df_vista.columns:
                df_vista[col] = df_vista[col].fillna('—')

        # Toque PVD en las celdas: VER en azul, existencias en cero o negativas en magenta,
        # miles con coma. Si el servidor no tiene el motor de estilos, se muestra la tabla normal.
        try:
            tabla = (df_vista.style
                     .map(lambda v: f'color: {MAGENTA}; font-weight: 700' if pd.notna(v) and v <= 0 else '',
                          subset=['Disponible'])
                     .format('{:,.0f}', subset=[c for c in ['Disponible', 'Apartados', 'Total']
                                                if c in df_vista.columns])
                     .format(na_rep='—', subset=[c for c in ['AÑO'] if c in df_vista.columns]))
        except Exception:
            tabla = df_vista

        if CLIC_EN_CELDA:
            st.caption("Da clic en la camarita de un producto para ver su foto en grande.")
        else:
            st.caption("Marca la casilla de un producto (a la izquierda) para ver su foto en grande.")
        st.dataframe(
            tabla, use_container_width=True, hide_index=True,
            on_select=_al_seleccionar_foto, key="tabla_inventario",
            selection_mode=["single-row", "single-cell"] if CLIC_EN_CELDA else "single-row",
            column_config={
                "url_foto": None,
                "Foto": st.column_config.ImageColumn("Foto", width="small",
                                                     help="Da clic en la camarita para ver la foto en grande"),
            },
        )
        abrir_foto_pendiente(df_vista)
        st.download_button("Descargar CSV", df_t[cols_validas].to_csv(index=False).encode('utf-8'), "inventario.csv", "text/csv")

# 8. VISTA: NUEVAS CAMPAÑAS
elif menu == SECCIONES[1]:
    encabezado("Nuevas campañas")
    st.info("Sección en preparación.")

# 9. VISTA: ANÁLISIS 360
else:
    encabezado("Análisis 360")

    if not df_master.empty:
        etiqueta("Filtros")
        c1, c2 = st.columns(2)
        with c1: canal_d = st.selectbox("Canal Dashboard", get_options(df_master, 'Canal', "Todos"))
        with c2: camp_d = st.selectbox("Campaña Dashboard", get_options(df_master, 'Campaña'))

        df_d = df_master.copy()
        if canal_d not in ["Todos", "Todas"]: df_d = df_d[df_d['Canal'].astype(str) == canal_d]
        if camp_d != "Todas": df_d = df_d[df_d['Campaña'].astype(str) == camp_d]

        # KPIs
        etiqueta("Resumen")
        col_dash1, col_dash2 = st.columns([1, 2])
        with col_dash1:
            total_g = df_master['Disponible'].sum() if 'Disponible' in df_master.columns else 0
            total_f = df_d['Disponible'].sum() if 'Disponible' in df_d.columns else 0
            porc = (total_f / total_g * 100) if total_g > 0 else 0
            st.components.v1.html(draw_liquid_fill(porc), height=300)

        with col_dash2:
            _html(f'<div class="pvd-total"><small>INVENTARIO DISPONIBLE</small><b>{total_f:,.0f}</b></div>')

        # Mapa ancho (cobertura) + ranking de almacenes al lado; campañas abajo a todo lo ancho
        g1, g2 = st.columns([3, 2])

        with g1:
            etiqueta("Cobertura")
            with st.container(key="tarjeta_mapa"):
                try:
                    dibujar_cobertura(df_d)
                except Exception as e:
                    st.warning(f"No se pudo dibujar el mapa: {e}")

        with g2:
            etiqueta("Almacenes")
            tarjeta_alm = st.container(key="tarjeta_almacenes")
            if 'Nombre' in df_d.columns and not df_d.empty:
                df_rank = df_d.groupby('Nombre')['Disponible'].sum().reset_index().sort_values('Disponible')
                if not df_rank.empty:
                    fig_bar = px.bar(df_rank, x="Disponible", y="Nombre", orientation='h',
                                     height=max(360, 24 * len(df_rank)))
                    fig_bar.update_traces(marker_color=AZUL, marker_line_color=TINTA, marker_line_width=2)
                    tarjeta_alm.plotly_chart(estilo_grafica(fig_bar), use_container_width=True)
            else:
                tarjeta_alm.info("Sin datos para este filtro.")

        etiqueta("Campaña")
        tarjeta_camp = st.container(key="tarjeta_campana")
        if not df_d.empty and {'Campaña', 'Canal', 'Disponible'}.issubset(df_d.columns):
            # Un punto por Campaña + Canal con su total (en vez de un punto por renglón)
            df_camp = df_d.groupby(['Campaña', 'Canal'], as_index=False)['Disponible'].sum()
            # El tamaño no acepta negativos: sin existencia = sin burbuja
            df_camp['Tamaño'] = df_camp['Disponible'].clip(lower=0)
            if df_camp.empty:
                tarjeta_camp.info("Datos insuficientes para dispersión.")
            else:
                if df_camp['Tamaño'].max() == 0:
                    df_camp['Tamaño'] = 1
                try:
                    fig_scat = px.scatter(
                        df_camp, x="Campaña", y="Canal", size="Tamaño",
                        hover_data={"Disponible": True, "Tamaño": False},
                        color_discrete_sequence=[MAGENTA], size_max=30, height=340,
                    )
                    fig_scat.update_traces(marker=dict(line=dict(color=TINTA, width=2)))
                    tarjeta_camp.plotly_chart(estilo_grafica(fig_scat), use_container_width=True)
                except Exception as e:
                    tarjeta_camp.warning(f"No se pudo dibujar la gráfica: {e}")
        else:
            tarjeta_camp.info("Datos insuficientes para dispersión.")
