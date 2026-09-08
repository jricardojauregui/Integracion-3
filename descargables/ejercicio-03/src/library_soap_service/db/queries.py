"""
Capa de acceso a datos independiente (Paso 12) — la única parte del
módulo, junto con db/connection.py, que ejecuta SQL. Todo parametrizado
(%s vía psycopg2, nunca f-strings/concatenación con datos del usuario).

Usa la vista vw_conceptos_pendientes y el stored procedure
sp_registrar_clasificacion definidos en sql/soap_module_procedures.sql
("Utiliza consultas parametrizadas -- Stored Procedures y Vistas").

Traduce los SQLSTATE de PostgreSQL a soap.faults.LibreriaFault aquí
mismo, para que soap/service.py nunca tenga que saber qué es un
SQLSTATE ni cómo se ve un error de psycopg2 — solo ve LibreriaFault.
"""
import psycopg2

from db.connection import cursor_lectura, transaccion
from soap import faults

# SQLSTATE personalizados que usa sp_registrar_clasificacion, mismo
# patrón que el monolito (ver apps/web-monolith .../05_triggers.sql,
# ERRCODE 'P0001' para "segundo administrador").
_SQLSTATE_ISBN_NO_ENCONTRADO = "P0001"
_SQLSTATE_CONCEPTO_NO_ENCONTRADO = "P0002"
_SQLSTATE_CLASIFICADOR_NO_ENCONTRADO = "P0003"


def obtener_conceptos_pendientes(isbn):
    """isbn=None -> todo el catálogo pendiente; isbn dado -> solo ese libro."""
    with cursor_lectura() as cur:
        if isbn:
            cur.execute(
                "SELECT isbn, titulo_libro, categoria, id_concepto, nombre_concepto "
                "FROM vw_conceptos_pendientes WHERE isbn = %s "
                "ORDER BY titulo_libro, nombre_concepto",
                (isbn,),
            )
        else:
            cur.execute(
                "SELECT isbn, titulo_libro, categoria, id_concepto, nombre_concepto "
                "FROM vw_conceptos_pendientes "
                "ORDER BY titulo_libro, nombre_concepto"
            )
        return [dict(fila) for fila in cur.fetchall()]


def registrar_clasificacion(id_clasificador: int, isbn: str, id_concepto: int, modelo_cloud: str) -> int:
    """
    CALL a sp_registrar_clasificacion dentro de una transacción: si
    cualquiera de sus validaciones falla (RAISE EXCEPTION) o el INSERT
    choca con UNIQUE(id_clasificador, isbn, id_concepto), db.connection
    .transaccion() hace ROLLBACK solo — aquí solo traducimos el error
    ya revertido a un LibreriaFault legible.
    """
    try:
        with transaccion() as cur:
            cur.execute(
                "CALL sp_registrar_clasificacion(%s, %s, %s, %s, NULL)",
                (id_clasificador, isbn, id_concepto, modelo_cloud),
            )
            return cur.fetchone()["p_id_clasificacion"]
    except psycopg2.errors.UniqueViolation:
        raise faults.LibreriaFault(
            faults.CLASIFICACION_DUPLICADA,
            "Este clasificador ya registró una clasificación para ese concepto de ese libro.",
        )
    except psycopg2.Error as err:
        codigo = getattr(err.diag, "sqlstate", None)
        if codigo == _SQLSTATE_ISBN_NO_ENCONTRADO:
            raise faults.LibreriaFault(faults.ISBN_NO_ENCONTRADO, "El ISBN no existe en el catálogo.")
        if codigo == _SQLSTATE_CONCEPTO_NO_ENCONTRADO:
            raise faults.LibreriaFault(
                faults.CONCEPTO_NO_ENCONTRADO, "Ese concepto no está definido para ese libro."
            )
        if codigo == _SQLSTATE_CLASIFICADOR_NO_ENCONTRADO:
            raise faults.LibreriaFault(faults.CLASIFICADOR_NO_ENCONTRADO, "El clasificador no existe.")
        raise  # error de PostgreSQL no anticipado: sube tal cual, app.py lo vuelve ERROR_INTERNO


def obtener_progreso_usuario(id_clasificador: int) -> dict:
    with cursor_lectura() as cur:
        cur.execute("SELECT 1 FROM clasificadores WHERE id_clasificador = %s", (id_clasificador,))
        if cur.fetchone() is None:
            raise faults.LibreriaFault(faults.CLASIFICADOR_NO_ENCONTRADO, "El clasificador no existe.")

        cur.execute(
            "SELECT count(*) AS total FROM clasificaciones_cloud WHERE id_clasificador = %s",
            (id_clasificador,),
        )
        total_clasificados = cur.fetchone()["total"]

        cur.execute("SELECT count(*) AS total FROM vw_conceptos_pendientes")
        total_pendientes = cur.fetchone()["total"]

    return {"total_clasificados": total_clasificados, "total_pendientes": total_pendientes}


def registrar_clasificador(nombre: str, apellido: str, correo=None) -> int:
    """Insert simple de una sola tabla — no necesita stored procedure (ver Paso 12)."""
    with transaccion() as cur:
        cur.execute(
            "INSERT INTO clasificadores (nombre, apellido, correo) VALUES (%s, %s, %s) "
            "RETURNING id_clasificador",
            (nombre, apellido, correo),
        )
        return cur.fetchone()["id_clasificador"]


def obtener_estadisticas_por_modelo():
    """Tarea 1: conteo de clasificaciones por modelo Cloud, vía vw_estadisticas_por_modelo."""
    with cursor_lectura() as cur:
        cur.execute("SELECT modelo_cloud, total FROM vw_estadisticas_por_modelo")
        return [dict(fila) for fila in cur.fetchall()]
