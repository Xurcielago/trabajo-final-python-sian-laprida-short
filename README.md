# Agent ADK - Analista de Datos Valhalla S.A.

Agente de Inteligencia Artificial desarrollado en Python con **Google Agent Development Kit (ADK)** para resolver la democratización del acceso a datos empresariales de **Valhalla S.A.** Permite a usuarios de negocio consultar información en lenguaje natural sin necesidad de conocimientos de programación o SQL.

## Características Principales

- **Modelo Local:** Utiliza `qwen3.5:4b` ejecutado localmente mediante **Ollama**, garantizando privacidad de los datos y ejecución sin costos de API.
- **Motor Analítico Multi-formato:** Emplea **DuckDB** en memoria para inspeccionar y consultar dinámicamente archivos `.csv`, `.parquet` y `.json` alojados en la carpeta `datos/`.
- **Seguridad de Solo Lectura:** Restringe las consultas a sentencias `SELECT` y `WITH`, bloquea comandos de escritura o acceso al sistema de archivos mediante expresiones regulares, aísla las rutas dentro de `datos/` e incluye directivas anti-_Prompt Injection_.
- **Trazabilidad e Historial:** Expone al usuario las fuentes y consultas SQL ejecutadas en cada respuesta y registra la auditoría completa en `historial.json`.

## Tecnologías Utilizadas

- **Python 3.10+**
- **Google ADK:** Framework de orquestación de agentes.
- **LiteLLM:** Adaptador para conectar Google ADK con modelos locales de Ollama.
- **Ollama:** Motor de inferencia local (`qwen3.5:4b`).
- **DuckDB:** Motor SQL analítico en memoria.
- **Pandas:** Formateo de resultados tabulares.

## Estructura del Proyecto

```text
trabajo-final-python-sian-laprida-short/
├── agent/
│   ├── __init__.py
│   └── agent.py              # Configuración del agente, instrucciones y herramientas
├── tools/
│   └── tools.py              # Implementación de las 5 herramientas en Python
├── datos/                    # Carpeta con las fuentes de datos (.csv, .parquet, .json)
│   ├── valhalla_ventas.csv
│   └── valhalla_clientes.parquet
├── historial.json            # Registro de trazabilidad generado automáticamente
├── requirements.txt          # Dependencias del proyecto
├── .gitignore
└── README.md


## Instalación y uso

git clone https://github.com/Xurcielago/trabajo-final-python-sian-laprida-short.git

## Crear entorno virtual
uv venv env
## Activar entorno y dependencias (Windows)
env\Scripts\activate
uv pip install -r requirements.txt
ollama pull qwen3.5:4b
adk web
streamlit run app.py

## Herramientas del Agente
El agente tiene a su disposición 3 herramientas con responsabilidades específicas:

- inspeccionar_fuente_de_datos(ruta_archivo: str)
Responsabilidad: Cumple el RF02. Utiliza el comando DESCRIBE de DuckDB para leer la estructura del archivo y devolver las columnas y tipos de datos al agente.
- ejecutar_consulta_segura(consulta_sql: str)
Responsabilidad: Cumple el RF05, RF06 y la Seguridad. Valida que el SQL empiece con SELECT y bloquea comandos destructivos. Ejecuta la consulta en una conexión :memory: para aislar el archivo original.
- guardar_historial(pregunta, consulta_sql, respuesta)
Responsabilidad: Cumple el RF08 y RF10. Guarda la trazabilidad completa en un archivo historial.json.
```
