# Agent ADK - Analista de Datos Valhalla S.A.

Este repositorio contiene la solución al trabajo final de la materia. Se trata de un **Agente de Inteligencia Artificial** desarrollado en Python con **Google Agent Development Kit (ADK)**. El agente actúa como un Analista de Datos Senior para la empresa ficticia Valhalla S.A., permitiendo a usuarios de negocio consultar información empresarial en lenguaje natural sin necesidad de saber SQL.

## Características Principales

* **Modelo Local**: Utiliza `qwen3.5:4b` ejecutado localmente a través de **Ollama**, garantizando privacidad y funcionamiento sin costos de API.
* **Motor de Base de Datos**: Emplea **DuckDB**, una base de datos analítica en memoria ultrarrápida que lee archivos `.csv` y `.parquet` directamente.
* **Seguridad de Nivel de Producción**: El agente está protegido contra **Prompt Injections** (por sus instrucciones) y **SQL Injections** (por el código de Python).

## Tecnologías Utilizadas

* **Python 3.10+**
* **Google ADK**: Framework de orquestación de agentes.
* **LiteLLM**: Adaptador para conectar ADK con Ollama.
* **Ollama**: Motor de inferencia local (`qwen3.5:4b`).
* **DuckDB**: Motor SQL en memoria.
* **Pandas**: Manipulación de datos y formateo de salida.

## Estructura del Proyecto

agent_adk_valhalla_tunombre/
│
├── agent/
│   ├── __init__.py
│   ├── agent.py          # Configuración del agente, rol y modelo
│   └── tools.py          # Código de las 3 herramientas de Python
│
├── valhalla_ventas.csv   # Archivo de datos
├── historial.json        # Se genera automáticamente al usar el agente
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Este archivo


## Estructura del Proyecto

git clone https://github.com/tu-usuario/agent_adk_valhalla_tunombre.git
cd agent_adk_valhalla_tunombre

# Crear entorno virtual (usando uv o venv)
uv venv env
# Activar entorno (Windows)
env\Scripts\activate
# Activar entorno (Linux/Mac)
source env/bin/activate

uv pip install google-adk litellm duckdb pandas

uv pip install google-adk litellm duckdb pandas
