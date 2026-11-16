import duckdb
import re
import json
import os
import datetime

CARPETA_DATOS = "datos"
EXTENSIONES_PERMITIDAS = (".csv", ".parquet", ".json")

def _validar_archivo(nombre_archivo: str) -> tuple[bool, str]:
    """Verifica que el archivo exista dentro de CARPETA_DATOS y tenga una extensión permitida."""
    # Evita que se acceda a rutas fuera de la carpeta datos (ej. '../agent/agent.py')
    if os.path.basename(nombre_archivo) != nombre_archivo:
        return False, "ERROR DE SEGURIDAD: Solo se permite el nombre del archivo, sin rutas."

    if not nombre_archivo.lower().endswith(EXTENSIONES_PERMITIDAS):
        return False, f"ERROR: Formato no soportado. Usa {EXTENSIONES_PERMITIDAS}."

    ruta_completa = os.path.join(CARPETA_DATOS, nombre_archivo)
    if not os.path.isfile(ruta_completa):
        return False, f"ERROR: El archivo '{nombre_archivo}' no existe en la carpeta '{CARPETA_DATOS}'."

    return True, ruta_completa

def listar_fuentes_disponibles() -> str:
    """
    Lista los archivos de datos disponibles (CSV, Parquet, JSON) en la carpeta de datos.
    """
    if not os.path.exists(CARPETA_DATOS):
        os.makedirs(CARPETA_DATOS)
        return f"La carpeta '{CARPETA_DATOS}' estaba vacía y acaba de crearse. Agrega archivos allí."

    archivos = [
        f for f in os.listdir(CARPETA_DATOS)
        if f.lower().endswith(EXTENSIONES_PERMITIDAS) and os.path.isfile(os.path.join(CARPETA_DATOS, f))
    ]

    if not archivos:
        return f"No hay fuentes de datos disponibles en '{CARPETA_DATOS}'."

    lista_formateada = "\n".join(f"- {archivo}" for archivo in sorted(archivos))
    return f"Fuentes de datos disponibles:\n{lista_formateada}"

def inspeccionar_fuente_de_datos(nombre_archivo: str) -> str:
    """
    Inspecciona la estructura de un archivo de datos (CSV, Parquet o JSON).
    Devuelve los nombres de las columnas y sus tipos de datos.
    Args:
        nombre_archivo: Nombre del archivo (ej. 'valhalla_ventas.csv').
    """
    es_valido, resultado_ruta = _validar_archivo(nombre_archivo)
    if not es_valido:
        return resultado_ruta

    try:
        conn = duckdb.connect(":memory:")
        query = f"DESCRIBE SELECT * FROM '{resultado_ruta}'"
        resultado = conn.execute(query).df()

        columnas = resultado[["column_name", "column_type"]].to_string(index=False)
        return f"ÉXITO. Estructura de '{nombre_archivo}':\n{columnas}"
    except Exception as e:
        return f"ERROR al inspeccionar '{nombre_archivo}': {str(e)}"

def ejecutar_consulta_segura(consulta_sql: str) -> str:
    """
    Herramienta para ejecutar consultas SQL de solo lectura (SELECT) sobre los datos.
    Args:
        consulta_sql: str -> La consulta SQL generada.
    """
    # 1. SEGURIDAD
    sql_upper = consulta_sql.upper()
    comandos_prohibidos = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
    
    for comando in comandos_prohibidos:
        if comando in sql_upper:
            return f"ERROR DE SEGURIDAD: El comando '{comando}' está prohibido. Solo se permiten consultas SELECT."
            
    if not sql_upper.strip().startswith("SELECT") and not sql_upper.strip().startswith("WITH"):
        return "ERROR DE SEGURIDAD: La consulta debe comenzar con SELECT o WITH."

    # 2. EJECUCIÓN
    try:
        conn = duckdb.connect(':memory:')
        resultado = conn.execute(consulta_sql).df()
        
        if resultado.empty:
            return "La consulta se ejecutó correctamente pero no devolvió ningún dato (0 filas)."
            
        # Máximo 20 filas
        if len(resultado) > 20:
            texto = resultado.head(20).to_string(index=False)
            return f"Resultado (Mostrando las primeras 20 de {len(resultado)} filas):\n{texto}"
        else:
            return f"Resultado ({len(resultado)} filas):\n{resultado.to_string(index=False)}"
            
    except Exception as e:
        return f"ERROR en la consulta SQL: {str(e)}. Revisa los nombres de las tablas y columnas."

def guardar_historial(pregunta: str, consulta_sql: str, respuesta: str) -> str:
    """Guarda la trazabilidad de la consulta en un archivo JSON."""
    try:
        entrada = {
            "fecha": datetime.datetime.now().isoformat(),
            "pregunta": pregunta,
            "sql_ejecutado": consulta_sql,
            "resultado": respuesta[:500]
        }
        
        historial = []
        if os.path.exists("historial.json"):
            with open("historial.json", "r", encoding="utf-8") as f:
                historial = json.load(f)
                
        historial.append(entrada)
        
        with open("historial.json", "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
            
        return "ÉXITO: La consulta ha sido registrada en el historial de trazabilidad."
    except Exception as e:
        return f"ERROR al guardar el historial: {str(e)}"