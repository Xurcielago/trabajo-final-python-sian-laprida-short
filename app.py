import os
import asyncio
import pandas as pd
import streamlit as st
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent.agent import root_agent
from tools.tools import (
    CARPETA_DATOS,
    EXTENSIONES_PERMITIDAS,
    ARCHIVO_ULTIMO_RESULTADO,
)

# 1. Configuración general de la página
st.set_page_config(
    page_title="Valhalla S.A. - Analista de Datos IA",
    layout="wide",
)

st.title("Valhalla S.A. — Sistema Inteligente de Análisis de Datos")
st.caption("Consulta información empresarial en lenguaje natural sin necesidad de SQL.")

# 2. Inicialización de sesión y Runner de Google ADK
if "session_service" not in st.session_state:
    st.session_state.session_service = InMemorySessionService()
    st.session_state.runner = Runner(
        agent=root_agent,
        app_name="valhalla_app",
        session_service=st.session_state.session_service,
    )
    st.session_state.user_id = "usuario_negocio"
    st.session_state.session_id = "sesion_principal"
    st.session_state.sesion_creada = False
    st.session_state.mensajes = []


async def consultar_agente(texto_pregunta: str) -> str:
    """Envía la pregunta al agente de ADK y recupera la respuesta final."""
    if not st.session_state.sesion_creada:
        await st.session_state.session_service.create_session(
            app_name="valhalla_app",
            user_id=st.session_state.user_id,
            session_id=st.session_state.session_id,
        )
        st.session_state.sesion_creada = True

    contenido = types.Content(
        role="user",
        parts=[types.Part.from_text(text=texto_pregunta)],
    )

    respuesta_final = "No se obtuvo respuesta del agente."
    async for evento in st.session_state.runner.run_async(
        user_id=st.session_state.user_id,
        session_id=st.session_state.session_id,
        new_message=contenido,
    ):
        if evento.is_final_response() and evento.content and evento.content.parts:
            respuesta_final = "".join(
                parte.text
                for parte in evento.content.parts
                if hasattr(parte, "text") and parte.text
            )

    return respuesta_final


def renderizar_visualizacion(registros: list[dict], clave_unica: str) -> None:
    """Genera indicadores, tablas y gráficos automáticamente según los datos devueltos (RF07)."""
    if not registros:
        return

    df = pd.DataFrame(registros)
    cols_numericas = df.select_dtypes(include=["number"]).columns.tolist()
    cols_categoricas = [c for c in df.columns if c not in cols_numericas]

    # A. Indicadores clave (KPIs) cuando el resultado es una única fila resumida
    if len(df) == 1 and cols_numericas:
        columnas_ui = st.columns(min(len(df.columns), 4))
        for idx, col in enumerate(df.columns[:4]):
            valor = df.iloc[0][col]
            if isinstance(valor, float):
                valor_formateado = f"{valor:,.2f}"
            elif isinstance(valor, int):
                valor_formateado = f"{valor:,}"
            else:
                valor_formateado = str(valor)
            columnas_ui[idx].metric(
                label=col.replace("_", " ").title(),
                value=valor_formateado,
            )
        return

    # B. Tabla interactiva cuando hay múltiples filas
    if len(df) > 1:
        st.dataframe(df, use_container_width=True, hide_index=True)

    # C. Gráfico automático cuando hay al menos una dimensión y una métrica numérica
    if 2 <= len(df) <= 30 and cols_categoricas and cols_numericas:
        col_x = cols_categoricas[0]
        col_y = cols_numericas[0]

        es_temporal = any(
            palabra in col_x.lower()
            for palabra in (
                "fecha",
                "mes",
                "anio",
                "año",
                "periodo",
                "dia",
                "semana",
                "trimestre",
            )
        )
        tipo_por_defecto = "Líneas" if es_temporal else "Barras"

        tipo_grafico = st.radio(
            "Tipo de gráfico:",
            options=["Barras", "Líneas", "Área"],
            index=["Barras", "Líneas", "Área"].index(tipo_por_defecto),
            horizontal=True,
            key=f"chart_{clave_unica}",
        )

        df_grafico = df.set_index(col_x)[[col_y]]
        if tipo_grafico == "Líneas":
            st.line_chart(df_grafico)
        elif tipo_grafico == "Área":
            st.area_chart(df_grafico)
        else:
            st.bar_chart(df_grafico)


# 3. Barra lateral: Incorporación dinámica de fuentes de datos (RF01)
with st.sidebar:
    st.header("Fuentes de Datos")
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    archivos_subidos = st.file_uploader(
        "Incorporar archivos (CSV, Parquet, JSON)",
        type=["csv", "parquet", "json"],
        accept_multiple_files=True,
    )

    if archivos_subidos:
        for archivo in archivos_subidos:
            ruta_destino = os.path.join(CARPETA_DATOS, archivo.name)
            with open(ruta_destino, "wb") as f:
                f.write(archivo.getbuffer())
        st.success("Archivo(s) incorporado(s) correctamente.")

    st.subheader("Archivos disponibles")
    disponibles = sorted(
        [
            f
            for f in os.listdir(CARPETA_DATOS)
            if f.lower().endswith(EXTENSIONES_PERMITIDAS)
            and os.path.isfile(os.path.join(CARPETA_DATOS, f))
        ]
    )
    if disponibles:
        for nombre in disponibles:
            st.text(f"• {nombre}")
    else:
        st.info("Sube un archivo para comenzar.")

    st.divider()
    if st.button("Limpiar conversación"):
        st.session_state.mensajes = []
        st.session_state.sesion_creada = False
        st.session_state.session_id = f"sesion_{os.urandom(4).hex()}"
        st.rerun()

# 4. Renderizado del historial de chat y sus visualizaciones
for i, msg in enumerate(st.session_state.mensajes):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("datos"):
            renderizar_visualizacion(msg["datos"], clave_unica=f"hist_{i}")

# 5. Entrada de consultas del usuario
if prompt := st.chat_input("Ej. ¿Qué categoría generó mayores ingresos durante el último trimestre?"):
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Elimina cualquier resultado temporal previo antes de ejecutar la nueva consulta
    if os.path.exists(ARCHIVO_ULTIMO_RESULTADO):
        os.remove(ARCHIVO_ULTIMO_RESULTADO)

    with st.chat_message("assistant"):
        with st.spinner("Analizando datos..."):
            respuesta = asyncio.run(consultar_agente(prompt))
            st.markdown(respuesta)

            datos_estructurados = []
            if os.path.exists(ARCHIVO_ULTIMO_RESULTADO):
                datos_estructurados = pd.read_json(ARCHIVO_ULTIMO_RESULTADO).to_dict(
                    orient="records"
                )
                os.remove(ARCHIVO_ULTIMO_RESULTADO)
                renderizar_visualizacion(
                    datos_estructurados,
                    clave_unica=f"nuevo_{len(st.session_state.mensajes)}",
                )

    st.session_state.mensajes.append(
        {
            "role": "assistant",
            "content": respuesta,
            "datos": datos_estructurados,
        }
    )