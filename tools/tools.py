import duckdb
import json
import os
import datetime

# Nombres exactos de tus archivos
ARCHIVOS_DISPONIBLES = ["valhalla_ventas.csv", "valhalla_clientes.parquet"]

def inspeccionar_fuente_de_datos(ruta_archivo: str) -> str:
    """
    Herramienta para inspeccionar la estructura de un archivo de datos.
    Devuelve los nombres de las columnas y sus tipos de datos.
    Args:
        ruta_archivo: str -> Nombre del archivo (ej. 'valhalla_ventas.csv').
    """
    if ruta_archivo not in ARCHIVOS_DISPONIBLES:
        return f"ERROR: El archivo '{ruta_archivo}' no está autorizado."
    
    try:
        conn = duckdb.connect(':memory:')
        # DuckDB 'DESCRIBE' que lee la estructura
        query = f"DESCRIBE SELECT * FROM '{ruta_archivo}'"
        resultado = conn.execute(query).df()
        
        # Respuesta Formateada
        columnas = resultado[['column_name', 'column_type']].to_string(index=False)
        return f"ÉXITO. Estructura del archivo '{ruta_archivo}':\n{columnas}"
    except Exception as e:
        return f"ERROR al inspeccionar: {str(e)}"

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