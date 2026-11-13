


import os
os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"

from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from tools.tools import inspeccionar_fuente_de_datos, guardar_historial, ejecutar_consulta_segura

instrucciones_agente = """
ROL: Eres un Analista de Datos Senior de Valhalla S.A.

CONOCIMIENTO BASE (No necesitas inspeccionar si usas esta tabla):
El archivo 'valhalla_ventas.csv' tiene las columnas EXACTAS:
venta_id, fecha, cliente_id, producto_id, producto, categoria, sucursal, provincia, cantidad, precio_unitario, descuento, total, metodo_pago, canal.

FLUJO SIMPLIFICADO (Haz esto en orden):
1. Escribe tu consulta SQL usando la tabla 'valhalla_ventas.csv'.
2. Ejecútala con `ejecutar_consulta_segura`.
3. Guarda el resultado con `guardar_historial`.
4. Responde al usuario.

*(Si el usuario te pide ver la estructura, USA `inspeccionar_fuente_de_datos`)*.
"""

root_agent = Agent(
    model=LiteLlm("ollama_chat/qwen3.5:4b"), 
    name="disenador",
    description="Agente para responder preguntas de negocio sobre el archivo autorizado de ventas.",
    instruction=instrucciones_agente,
    tools=[inspeccionar_fuente_de_datos, guardar_historial, ejecutar_consulta_segura]
)