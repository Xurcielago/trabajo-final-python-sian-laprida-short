import duckdb
import re
import json
import os
import datetime

CARPETA_DATOS = "datos"
EXTENSIONES_PERMITIDAS = (".csv", ".parquet", ".json")
ARCHIVO_HISTORIAL = "historial.json"

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


def _resolver_rutas_en_sql(consulta_sql: str) -> tuple[bool, str]:
    """Valida las referencias a archivos dentro del SQL y las apunta a CARPETA_DATOS."""
    tokens_entre_comillas = re.findall(r"'([^']*)'", consulta_sql)
    sql_procesado = consulta_sql

    for token in tokens_entre_comillas:
        parece_ruta = (
            ".." in token
            or token.startswith(("/", "\\"))
            or bool(re.match(r"^[a-zA-Z]:", token))
            or bool(re.search(r"\.[a-zA-Z0-9]{2,7}$", token))
        )
        if parece_ruta:
            es_valido, ruta_o_error = _validar_archivo(token)
            if not es_valido:
                return False, ruta_o_error
            ruta_duckdb = ruta_o_error.replace("\\", "/")
            sql_procesado = sql_procesado.replace(f"'{token}'", f"'{ruta_duckdb}'")

    return True, sql_procesado

def ejecutar_consulta_segura(consulta_sql: str) -> str:
    """
    Ejecuta consultas SQL de solo lectura (SELECT o WITH) sobre los archivos de datos.
    Args:
        consulta_sql: Consulta SQL usando el nombre del archivo (ej. 'valhalla_ventas.csv').
    """
    sql_limpio = consulta_sql.strip().rstrip(";")
    if ";" in sql_limpio:
        return "ERROR DE SEGURIDAD: No se permiten múltiples sentencias SQL."

    sql_upper = sql_limpio.upper()
    if not sql_upper.startswith(("SELECT", "WITH")):
        return "ERROR DE SEGURIDAD: La consulta debe comenzar con SELECT o WITH."

    comandos_prohibidos = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
        "CREATE", "COPY", "ATTACH", "DETACH", "EXPORT", "PRAGMA",
        "INSTALL", "LOAD", "GLOB", "READ_TEXT", "READ_BLOB"
    ]
    for comando in comandos_prohibidos:
        if re.search(rf"\b{comando}\b", sql_upper):
            return f"ERROR DE SEGURIDAD: El comando '{comando}' está prohibido."

    es_ruta_valida, sql_final = _resolver_rutas_en_sql(sql_limpio)
    if not es_ruta_valida:
        return sql_final

    try:
        conn = duckdb.connect(":memory:")
        resultado = conn.execute(sql_final).df()

        if resultado.empty:
            return "La consulta se ejecutó correctamente pero no devolvió ningún dato (0 filas)."

        if len(resultado) > 20:
            texto = resultado.head(20).to_string(index=False)
            return f"Resultado (Mostrando las primeras 20 de {len(resultado)} filas):\n{texto}"

        return f"Resultado ({len(resultado)} filas):\n{resultado.to_string(index=False)}"
    except Exception as e:
        return f"ERROR en la consulta SQL: {str(e)}. Verifica los nombres de archivos y columnas."

def guardar_historial(pregunta: str, fuentes_utilizadas: str, consulta_sql: str, respuesta: str) -> str:
    """
    Guarda la trazabilidad de una consulta en historial.json (RF08).
    Args:
        pregunta: Pregunta original del usuario.
        fuentes_utilizadas: Archivos consultados (ej. 'valhalla_ventas.csv').
        consulta_sql: Consulta SQL ejecutada.
        respuesta: Resumen de la respuesta entregada.
    """
    try:
        entrada = {
            "fecha": datetime.datetime.now().isoformat(),
            "pregunta": pregunta,
            "fuentes_utilizadas": fuentes_utilizadas,
            "sql_ejecutado": consulta_sql,
            "resultado": respuesta[:500]
        }

        historial = []
        if os.path.exists(ARCHIVO_HISTORIAL):
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                historial = json.load(f)

        historial.append(entrada)

        with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)

        return "ÉXITO: Consulta registrada en el historial de trazabilidad."
    except Exception as e:
        return f"ERROR al guardar el historial: {str(e)}"

def consultar_historial(limite: int = 5) -> str:
    """
    Consulta las últimas preguntas y resultados guardados en historial.json (RF10).
    Args:
        limite: Cantidad máxima de registros recientes a mostrar (por defecto 5).
    """
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return "Aún no existe un historial de consultas registradas."

    try:
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            historial = json.load(f)

        if not historial:
            return "El historial de consultas está vacío."

        ultimas = historial[-limite:]
        registros = []
        for i, item in enumerate(reversed(ultimas), start=1):
            registros.append(
                f"{i}. [{item.get('fecha', 'Sin fecha')}]\n"
                f"   Pregunta: {item.get('pregunta', '')}\n"
                f"   Fuentes: {item.get('fuentes_utilizadas', 'No registradas')}\n"
                f"   SQL: {item.get('sql_ejecutado', '')}\n"
                f"   Resultado: {item.get('resultado', '')}"
            )

        return "Últimas consultas registradas:\n\n" + "\n\n".join(registros)
    except Exception as e:
        return f"ERROR al leer el historial: {str(e)}"