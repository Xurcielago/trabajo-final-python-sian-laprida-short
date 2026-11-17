import os
import re
import json
import datetime
import duckdb

CARPETA_DATOS = "datos"
EXTENSIONES_PERMITIDAS = (".csv", ".parquet", ".json")
ARCHIVO_HISTORIAL = "historial.json"
ARCHIVO_ULTIMO_RESULTADO = "ultimo_resultado.json"

def _validar_archivo(nombre_archivo: str) -> tuple[bool, str]:
    """Verifica que el archivo exista dentro de CARPETA_DATOS y tenga una extensión permitida."""
    if os.path.basename(nombre_archivo) != nombre_archivo:
        return False, "ERROR DE SEGURIDAD: Solo se permite el nombre del archivo, sin rutas."

    if not nombre_archivo.lower().endswith(EXTENSIONES_PERMITIDAS):
        return False, f"ERROR: Formato no soportado. Usa {EXTENSIONES_PERMITIDAS}."

    ruta_completa = os.path.join(CARPETA_DATOS, nombre_archivo)
    if not os.path.isfile(ruta_completa):
        return False, f"ERROR: El archivo '{nombre_archivo}' no existe en '{CARPETA_DATOS}'."

    return True, ruta_completa


def _resolver_rutas_en_sql(consulta_sql: str) -> tuple[bool, str, list[str]]:
    """Valida archivos referenciados en el SQL, los apunta a CARPETA_DATOS y devuelve los nombres usados."""
    tokens_entre_comillas = re.findall(r"'([^']*)'", consulta_sql)
    sql_procesado = consulta_sql
    fuentes_detectadas = []

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
                return False, ruta_o_error, []
            ruta_duckdb = ruta_o_error.replace("\\", "/")
            sql_procesado = sql_procesado.replace(f"'{token}'", f"'{ruta_duckdb}'")
            if token not in fuentes_detectadas:
                fuentes_detectadas.append(token)

    return True, sql_procesado, fuentes_detectadas


def _registrar_historial_interno(pregunta: str, fuentes: list[str], consulta_sql: str, respuesta: str) -> None:
    """Guarda automáticamente la trazabilidad en historial.json sin gastar un turno del LLM."""
    try:
        entrada = {
            "fecha": datetime.datetime.now().isoformat(),
            "pregunta": pregunta.strip() if pregunta else "Consulta sin descripción",
            "fuentes_utilizadas": ", ".join(fuentes) if fuentes else "No identificadas",
            "sql_ejecutado": consulta_sql,
            "resultado": respuesta[:500],
        }

        historial = []
        if os.path.exists(ARCHIVO_HISTORIAL):
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                historial = json.load(f)

        historial.append(entrada)

        with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def obtener_esquema_datos() -> str:
    """
    Lista todos los archivos de datos disponibles (CSV, Parquet, JSON) junto con sus columnas y tipos.
    Úsala siempre como primer paso antes de redactar cualquier consulta SQL.
    """
    if not os.path.exists(CARPETA_DATOS):
        os.makedirs(CARPETA_DATOS)
        return f"La carpeta '{CARPETA_DATOS}' estaba vacía y fue creada. Agrega archivos allí."

    archivos = sorted([
        f for f in os.listdir(CARPETA_DATOS)
        if f.lower().endswith(EXTENSIONES_PERMITIDAS) and os.path.isfile(os.path.join(CARPETA_DATOS, f))
    ])

    if not archivos:
        return f"No hay fuentes de datos disponibles en '{CARPETA_DATOS}'."

    conn = duckdb.connect(":memory:")
    esquemas = []

    for archivo in archivos:
        ruta = os.path.join(CARPETA_DATOS, archivo).replace("\\", "/")
        try:
            df = conn.execute(f"DESCRIBE SELECT * FROM '{ruta}'").df()
            columnas = ", ".join(f"{fila['column_name']} ({fila['column_type']})" for _, fila in df.iterrows())
            esquemas.append(f"- {archivo}: {columnas}")
        except Exception as e:
            esquemas.append(f"- {archivo}: ERROR al inspeccionar ({str(e)})")

    return "Fuentes y estructuras disponibles:\n" + "\n".join(esquemas)


def ejecutar_consulta_segura(consulta_sql: str, pregunta_usuario: str = "") -> str:
    """
    Ejecuta una consulta SQL de solo lectura (SELECT o WITH) y registra automáticamente la trazabilidad.
    Args:
        consulta_sql: Consulta SQL válida para DuckDB usando el nombre del archivo (ej. 'valhalla_ventas.csv').
        pregunta_usuario: Pregunta original del usuario para registrar en el historial.
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

    es_ruta_valida, sql_final, fuentes_usadas = _resolver_rutas_en_sql(sql_limpio)
    if not es_ruta_valida:
        return sql_final

    try:
        conn = duckdb.connect(":memory:")
        resultado = conn.execute(sql_final).df()

        if resultado.empty:
            salida = "La consulta se ejecutó correctamente pero no devolvió ningún dato (0 filas)."
        else:
            # Guarda los datos estructurados para que Streamlit los grafique
            resultado.to_json(ARCHIVO_ULTIMO_RESULTADO, orient="records", date_format="iso")

            if len(resultado) > 20:
                texto = resultado.head(20).to_string(index=False)
                salida = f"Resultado (Mostrando las primeras 20 de {len(resultado)} filas):\n{texto}"
            else:
                salida = f"Resultado ({len(resultado)} filas):\n{resultado.to_string(index=False)}"

        _registrar_historial_interno(pregunta_usuario, fuentes_usadas, sql_limpio, salida)
        return salida
    except Exception as e:
        return f"ERROR en la consulta SQL: {str(e)}. Revisa los nombres de archivos y columnas."


def consultar_historial(limite: int = 5) -> str:
    """
    Muestra las últimas preguntas y resultados guardados en historial.json.
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