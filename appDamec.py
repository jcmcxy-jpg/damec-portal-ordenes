import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuración de la página web
st.set_page_config(page_title="Portal DAMEC - Control de Acceso", layout="wide")

# --- ESTILOS CSS Y COLORES CORPORATIVOS ---
st.markdown("""
    <style>
    .main {
        background-color: #F8F9FA;
    }
    h1, h2, h3 {
        color: #005F73;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS DESDE GOOGLE SHEETS EN LA NUBE ---
@st.cache_data(ttl=60)
def cargar_datos():
    sheet_id = "1ltNCZkGh1LNNDepLPmaZG0eY9RJ3gIaLmfyQzy3WTHs"
    url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(url_csv)
    df = df.dropna(how='all')
    return df

df_global = cargar_datos()

# Obtener lista de responsables limpios del Excel
lista_responsables = sorted(df_global["Responsable"].dropna().unique().tolist())

# --- DICIOnario DE CREDENCIALES ESTABLECIDAS ---
credenciales = {
    "Administrador (Global)": "Admin2026*",
    "AC": "Damec1*",
    "LM": "Damec9*",
    "GN": "Damec5*",
    "DEC": "Damec11*",
    "DSC": "Damec12*",
    "LV": "Damec7*",
    "JCM": "Damec10*",
    "JSV": "Damec2*"
}

# --- GESTIÓN DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""

# --- PANTALLA DE LOGIN (SI NO HA INICIADO SESIÓN) ---
if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            st.image('Logo DAMEC.png', width=220)
        except:
            st.markdown("<h1>DAMEC SAS</h1>", unsafe_allow_html=True)
        
        st.subheader("🔐 Inicio de Sesión - Portal HSEQ")
        st.markdown("Ingrese sus credenciales corporativas para acceder a las órdenes.")
        
        with st.form("form_login"):
            perfiles_disponibles = ["Administrador (Global)"] + lista_responsables
            usuario_ingreso = st.selectbox("Seleccione su Usuario / Perfil", perfiles_disponibles)
            password_ingreso = st.text_input("Contraseña", type="password")
            
            btn_login = st.form_submit_button("Ingresar al Portal", use_container_width=True)
            
            if btn_login:
                # Validar la contraseña correspondiente
                if usuario_ingreso in credenciales and credenciales[usuario_ingreso] == password_ingreso:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = usuario_ingreso
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta. Por favor verifique sus datos.")
    st.stop()

# --- APLICACIÓN PRINCIPAL (UNA VEZ AUTENTICADO) ---
usuario_actual = st.session_state.usuario_actual

# Encabezado y Logotipo
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("📊 Portal de Gestión de Órdenes - DAMEC SAS (Cloud)")
with col_head2:
    try:
        st.image('Logo DAMEC.png', width=160)
    except:
        st.write("DAMEC SAS")

st.markdown("---")

# --- BARRA LATERAL: CONTROL DE SESIÓN Y FILTRADO ---
st.sidebar.header(f"👤 Usuario: {usuario_actual}")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros Avanzados")

if usuario_actual == "Administrador (Global)":
    df_usuario = df_global.copy()
    lista_resp_filtro = ["Todos"] + lista_responsables
    resp_seleccionado = st.sidebar.selectbox("Filtrar por Responsable", lista_resp_filtro)
    if resp_seleccionado != "Todos":
        df_usuario = df_usuario[df_usuario["Responsable"] == resp_seleccionado]
else:
    df_usuario = df_global[df_global["Responsable"] == usuario_actual].copy()

lista_arl = ["Todas"] + sorted(df_usuario["ARL"].dropna().unique().tolist())
arl_seleccionada = st.sidebar.selectbox("Filtrar por ARL", lista_arl)

lista_empresa = ["Todas"] + sorted(df_usuario["Empresa"].dropna().unique().tolist())
empresa_seleccionada = st.sidebar.selectbox("Filtrar por Empresa", lista_empresa)

lista_estados = ["Todas"] + sorted(df_usuario["Estado de vencimiento"].dropna().unique().tolist())
estado_seleccionado = st.sidebar.selectbox("Filtrar por Estado de Vencimiento", lista_estados)

if arl_seleccionada != "Todas":
    df_usuario = df_usuario[df_usuario["ARL"] == arl_seleccionada]
if empresa_seleccionada != "Todas":
    df_usuario = df_usuario[df_usuario["Empresa"] == empresa_seleccionada]
if estado_seleccionado != "Todas":
    df_usuario = df_usuario[df_usuario["Estado de vencimiento"] == estado_seleccionado]

# Botón para sincronizar datos
if st.sidebar.button("🔄 Sincronizar con Google Sheets"):
    st.cache_data.clear()
    st.rerun()

# --- VALIDACIÓN DE DATOS ---
if df_usuario.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
else:
    # --- PANEL 1: MÉTRICAS PRINCIPALES ---
    titulo_panel = "Resumen Global (Administrador)" if usuario_actual == "Administrador (Global)" else f"Resumen de Gestión: {usuario_actual}"
    st.subheader(f"📈 {titulo_panel}")
    
    def calcular_metricas(df, estado):
        sub_df = df[df["Estado de vencimiento"].str.lower() == estado.lower()]
        return len(sub_df), sub_df["Horas"].sum()

    t_ordenes, t_horas = len(df_usuario), df_usuario["Horas"].sum()
    v_ordenes, v_horas = calcular_metricas(df_usuario, "Vencida")
    pv_ordenes, pv_horas = calcular_metricas(df_usuario, "Por vencerse")
    fac_ordenes, fac_horas = calcular_metricas(df_usuario, "Facturado")
    ent_ordenes, ent_horas = calcular_metricas(df_usuario, "En tiempos")
    can_ordenes, can_horas = calcular_metricas(df_usuario, "Cancelado")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Órdenes", t_ordenes, f"{t_horas} hrs")
    col2.metric("Vencidas", v_ordenes, f"{v_horas} hrs", delta_color="inverse")
    col3.metric("Por Vencerse", pv_ordenes, f"{pv_horas} hrs")
    col4.metric("Facturadas", fac_ordenes, f"{fac_horas} hrs")
    col5.metric("En Tiempos", ent_ordenes, f"{ent_horas} hrs")
    col6.metric("Canceladas", can_ordenes, f"{can_horas} hrs")

    st.markdown("---")

    # --- PANEL 2: CONSOLIDADO POR ARL ---
    st.subheader("🏢 Consolidado por ARL")
    df_arl = df_usuario.groupby("ARL").agg(
        Total_Ordenes=("Secuencia", "count"),
        Total_Horas=("Horas", "sum")
    ).reset_index()
    st.dataframe(df_arl, use_container_width=True)

    st.markdown("---")

    # --- GRÁFICAS DE GESTIÓN ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Estado de las Órdenes")
        color_map = {
            "Cancelado": "#000000",       # Negro
            "Facturado": "#1B4332",       # Verde oscuro
            "En tiempos": "#52B788",      # Verde claro
            "Vencida": "#9D0208",         # Rojo oscuro
            "Por vencerse": "#E56B6F"     # Rojo claro
        }
        fig_estado = px.pie(
            df_usuario, 
            names="Estado de vencimiento", 
            hole=0.4,
            color="Estado de vencimiento",
            color_discrete_map=color_map
        )
        st.plotly_chart(fig_estado, use_container_width=True)

    with col_g2:
        st.subheader("Distribución de Horas por Empresa y ARL")
        fig_empresa = px.bar(
            df_usuario, 
            x="Empresa", 
            y="Horas", 
            color="ARL",
            barmode="group",
            text="Horas",
            title="Horas por Empresa (Agrupado por ARL)"
        )
        fig_empresa.update_traces(textposition='inside', texttemplate='%{text}h')
        st.plotly_chart(fig_empresa, use_container_width=True)

    st.markdown("---")

    # --- TABLA DETALLADA Y DESCARGA ---
    st.subheader("📋 Detalle de Órdenes Filtradas")
    st.dataframe(df_usuario, use_container_width=True)

    def convertir_a_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Mis_Ordenes')
        return output.getvalue()

    excel_data = convertir_a_excel(df_usuario)
    st.download_button(
        label="📥 Descargar órdenes filtradas en Excel",
        data=excel_data,
        file_name=f"Reporte_Ordenes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
