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


## Instalación y uso

git clone https://github.com/Xurcielago/trabajo-final-python-sian-laprida-short.git

## Crear entorno virtual
uv venv env
## Activar entorno y dependencias (Windows)
env\Scripts\activate  
uv pip install google-adk litellm duckdb pandas  
ollama pull qwen3.5:4b  
adk web  


## Herramientas del Agente
El agente tiene a su disposición 3 herramientas con responsabilidades específicas:

- inspeccionar_fuente_de_datos(ruta_archivo: str)  
Responsabilidad: Cumple el RF02. Utiliza el comando DESCRIBE de DuckDB para leer la estructura del archivo y devolver las columnas y tipos de datos al agente.
- ejecutar_consulta_segura(consulta_sql: str)  
Responsabilidad: Cumple el RF05, RF06 y la Seguridad. Valida que el SQL empiece con SELECT y bloquea comandos destructivos. Ejecuta la consulta en una conexión :memory: para aislar el archivo original.
- guardar_historial(pregunta, consulta_sql, respuesta)  
Responsabilidad: Cumple el RF08 y RF10. Guarda la trazabilidad completa en un archivo historial.json.