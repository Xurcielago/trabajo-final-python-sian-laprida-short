import os
import asyncio
import streamlit as st
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent.agent import root_agent
from tools.tools import CARPETA_DATOS, EXTENSIONES_PERMITIDAS

# 1. Configuración de la página
st.set_page_config(
    page_title="Valhalla S.A. - Analista de Datos IA",
    layout="wide",
)

st.title("Valhalla S.A. — Sistema Inteligente de Análisis de Datos")
st.caption("Consulta información empresarial en lenguaje natural sin necesidad de SQL.")

# 2. Inicializar el servicio de sesiones y el Runner de Google ADK en Streamlit
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
                parte.text for parte in evento.content.parts if hasattr(parte, "text") and parte.text
            )

    return respuesta_final


# 3. Barra lateral: Carga dinámica de fuentes de datos (RF01)
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
    disponibles = sorted([
        f for f in os.listdir(CARPETA_DATOS)
        if f.lower().endswith(EXTENSIONES_PERMITIDAS)
    ])
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

# 4. Historial visual del chat
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Entrada de preguntas del usuario
if prompt := st.chat_input("Ej. ¿Cuál fue el producto más vendido durante septiembre?"):
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analizando datos..."):
            respuesta = asyncio.run(consultar_agente(prompt))
            st.markdown(respuesta)

    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})