"""
Acceso a datos: conexión psycopg2 y los dos patrones de uso que exige
el Paso 12 — lectura simple, y transacción con COMMIT/ROLLBACK.

Sin ORM (decisión de ingeniería #4: psycopg2 directo). Este archivo es
la ÚNICA parte del módulo que sabe conectarse a PostgreSQL; el resto
del código (db/queries.py) recibe cursores ya abiertos, nunca abre
conexiones por su cuenta.
"""
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from config.settings import get_settings

_settings = get_settings()


def obtener_conexion():
    """Conexión nueva a la base compartida con el monolito. RealDictCursor."""
    return psycopg2.connect(
        host=_settings.DB_HOST,
        port=_settings.DB_PORT,
        dbname=_settings.DB_NAME,
        user=_settings.DB_USER,
        password=_settings.DB_PASS,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


@contextmanager
def cursor_lectura():
    """
    Para SELECTs que no modifican nada: abre, entrega un cursor, siempre
    cierra la conexión al salir (haya o no excepción). No necesita
    COMMIT/ROLLBACK explícito porque no escribe nada.
    """
    conn = obtener_conexion()
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


@contextmanager
def transaccion():
    """
    Para operaciones que escriben (Paso 12: "transacciones cuando una
    operación modifique varias tablas y rollback ante errores").

    `with conn:` es el manejador de transacción nativo de psycopg2:
    si el bloque termina sin excepción hace COMMIT; si se lanza
    cualquier excepción (una violación de UNIQUE, un RAISE EXCEPTION
    del stored procedure, lo que sea) hace ROLLBACK automático antes
    de dejar propagar la excepción hacia quien llamó. No hay que
    escribir conn.commit()/conn.rollback() a mano en ningún otro lado
    del código — así no hay riesgo de un commit accidental tras un
    error a medio camino.
    """
    conn = obtener_conexion()
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()
