import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuración de la página web
st.set_page_config(page_title="Portal DAMEC - Gestión de Órdenes", layout="wide")

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
@st.cache_data(ttl=600) # Se actualiza automáticamente cada 10 minutos o al presionar el botón
def cargar_datos_gsheet():
    # Reemplaza este enlace por el link de tu Google Sheet publicado o público
    # Truco de exportación directa a CSV desde Google Sheets:
    sheet_id = "TU_ID_DE_GOOGLE_SHEET_AQUÍ" # O la URL de exportación CSV
    sheet_name = "Planeacion"
    url = f" https://docs.google.com/spreadsheets/d/1ltNCZkGh1LNNDepLPmaZG0eY9RJ3gIaLmfyQzy3WTHs/edit?usp=sharing"
    
    df = pd.read_csv(url)
    df = df.dropna(how='all')
    return df

# O puedes usar directamente la URL pública de exportación CSV de tu Google Sheet:
@st.cache_data(ttl=300)
def cargar_datos():
    # Instrucción: En tu Google Sheet ve a Archivo > Compartir > Publicar en la web > Formato Valores separados por comas (.csv)
    # O usa el enlace directo de tu sheet con formato gviz:
    url_csv = " https://docs.google.com/spreadsheets/d/1ltNCZkGh1LNNDepLPmaZG0eY9RJ3gIaLmfyQzy3WTHs/edit?usp=sharing "
    df = pd.read_csv(url_csv)
    return df

# Para hacerlo aún más simple y robusto usando el enlace directo de compartición:
@st.cache_data(ttl=300)
def cargar_datos_nube():
    # Pega aquí el enlace de tu Google Sheet compartido como público (cualquier usuario con el enlace)
    url_compartida = https://docs.google.com/spreadsheets/d/1ltNCZkGh1LNNDepLPmaZG0eY9RJ3gIaLmfyQzy3WTHs/edit?usp=sharing
    # Convertimos el link de edición al link de exportación CSV automático:
    url_csv = url_compartida.replace("/edit?usp=sharing", "/export?format=csv")
    df = pd.read_csv(url_csv)
    df = df.dropna(how='all')
    return df

# *Nota:* Usaremos la función directa para tu archivo en la nube:
@st.cache_data(ttl=60)
def cargar_datos():
    # Reemplaza 'TU_LINK_COMPARTIDO_CSV' por el link directo de tu Google Sheet en CSV
    # Ejemplo: https://docs.google.com/spreadsheets/d/TU_ID/export?format=csv
    url = "https://docs.google.com/spreadsheets/d/1ltNCZkGh1LNNDepLPmaZG0eY9RJ3gIaLmfyQzy3WTHs/edit?usp=sharing"
    df = pd.read_csv(url)
    return df

df_global = cargar_datos_nube() # O la función que prefieras conectar

# --- ENCABEZADO Y LOGOTIPO ---
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("📊 Portal de Gestión de Órdenes - DAMEC SAS (Cloud)")
with col_head2:
    try:
        st.image('Logo DAMEC.png', width=160)
    except:
        st.write("DAMEC SAS")

st.markdown("---")

# --- BARRA LATERAL: CONTROL DE ACCESO Y FILTRADO ---
st.sidebar.header("🔑 Control de Acceso")

lista_responsables = sorted(df_global["Responsable"].dropna().unique().tolist())
perfiles_disponibles = ["Administrador (Global)"] + lista_responsables
usuario_actual = st.sidebar.selectbox("Seleccione su Usuario / Perfil", perfiles_disponibles)

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

# Botón para refrescar datos desde Google Sheets al instante
if st.sidebar.button("🔄 Sincronizar con Google Sheets"):
    st.cache_data.clear()
    st.rerun()

if df_usuario.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
else:
    st.subheader(f"📈 {'Resumen Global (Administrador)' if usuario_actual == 'Administrador (Global)' else f'Resumen de Gestión: {usuario_actual}'}")
    
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

    st.subheader("🏢 Consolidado por ARL")
    df_arl = df_usuario.groupby("ARL").agg(
        Total_Ordenes=("Secuencia", "count"),
        Total_Horas=("Horas", "sum")
    ).reset_index()
    st.dataframe(df_arl, use_container_width=True)

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Estado de las Órdenes")
        color_map = {
            "Cancelado": "#000000",
            "Facturado": "#1B4332",
            "En tiempos": "#52B788",
            "Vencida": "#9D0208",
            "Por vencerse": "#E56B6F"
        }
        fig_estado = px.pie(df_usuario, names="Estado de vencimiento", hole=0.4, color="Estado de vencimiento", color_discrete_map=color_map)
        st.plotly_chart(fig_estado, use_container_width=True)

    with col_g2:
        st.subheader("Distribución de Horas por Empresa y ARL")
        fig_empresa = px.bar(df_usuario, x="Empresa", y="Horas", color="ARL", barmode="group", text="Horas", title="Horas por Empresa (Agrupado por ARL)")
        fig_empresa.update_traces(textposition='inside', texttemplate='%{text}h')
        st.plotly_chart(fig_empresa, use_container_width=True)

    st.markdown("---")

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

