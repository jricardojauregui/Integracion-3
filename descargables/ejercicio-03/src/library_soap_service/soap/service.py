"""
Lógica de negocio de cada operación SOAP. No sabe nada de XML (eso es
envelope.py) ni ejecuta SQL directamente (eso es db/queries.py) — solo
valida entrada (Paso 11) y traduce entre el vocabulario del contrato
(camelCase, ver wsdl/library-classifier.wsdl) y el de la base de datos
(snake_case, ver sql/soap_module.sql).
"""
import re

from db import queries
from soap import faults, security

_ISBN_RE = re.compile(r"^[0-9Xx-]{10,20}$")
_MODELOS_VALIDOS = {"IaaS", "PaaS", "SaaS", "FaaS"}


def despachar_operacion(operacion: str, datos: dict, credenciales: dict = None):
    """Enruta por nombre de operación (tal como aparece en el WSDL) al handler."""
    handlers = {
        "ObtenerConceptosPendientes": obtener_conceptos_pendientes,
        "RegistrarClasificacion": registrar_clasificacion,
        "ObtenerProgresoUsuario": obtener_progreso_usuario,
        "RegistrarClasificador": registrar_clasificador,
        "ObtenerEstadisticasPorModelo": obtener_estadisticas_por_modelo,
    }
    handler = handlers.get(operacion)
    if handler is None:
        raise faults.LibreriaFault(faults.DATOS_INVALIDOS, f"Operación desconocida: {operacion}")
    return handler(datos, credenciales)


# --------------------------------------------------------------------
# Validación de campos obligatorios y modelos permitidos (Paso 11).
# --------------------------------------------------------------------

def _campo_requerido(datos: dict, campo: str) -> str:
    valor = (datos.get(campo) or "").strip()
    if not valor:
        raise faults.LibreriaFault(faults.DATOS_INVALIDOS, f"Falta el campo obligatorio '{campo}'.")
    return valor


def _entero(datos: dict, campo: str) -> int:
    valor = _campo_requerido(datos, campo)
    try:
        return int(valor)
    except ValueError:
        raise faults.LibreriaFault(
            faults.DATOS_INVALIDOS, f"'{campo}' debe ser un entero, se recibió '{valor}'."
        )


def _isbn(datos: dict, campo: str = "isbn") -> str:
    valor = _campo_requerido(datos, campo)
    if not _ISBN_RE.match(valor):
        raise faults.LibreriaFault(faults.DATOS_INVALIDOS, f"'{valor}' no tiene formato de ISBN válido.")
    return valor


def _modelo_cloud(datos: dict, campo: str = "modeloCloud") -> str:
    valor = _campo_requerido(datos, campo)
    if valor not in _MODELOS_VALIDOS:
        raise faults.LibreriaFault(
            faults.DATOS_INVALIDOS,
            f"'{valor}' no es un modelo Cloud válido (debe ser IaaS, PaaS, SaaS o FaaS).",
        )
    return valor


# --------------------------------------------------------------------
# Operaciones (nombres exactos del WSDL, Paso 9 + Tarea 1)
# Todas reciben (datos, credenciales); credenciales solo lo usa la
# operación protegida por WS-Security -- el resto lo ignora.
# --------------------------------------------------------------------

def obtener_conceptos_pendientes(datos: dict, credenciales: dict = None):
    """isbn es opcional en este contrato — se valida el formato solo si vino."""
    isbn = (datos.get("isbn") or "").strip() or None
    if isbn is not None and not _ISBN_RE.match(isbn):
        raise faults.LibreriaFault(faults.DATOS_INVALIDOS, f"'{isbn}' no tiene formato de ISBN válido.")

    filas = queries.obtener_conceptos_pendientes(isbn)
    return [
        {
            "isbn": fila["isbn"],
            "tituloLibro": fila["titulo_libro"],
            "categoria": fila["categoria"] or "",
            "idConcepto": fila["id_concepto"],
            "nombreConcepto": fila["nombre_concepto"],
        }
        for fila in filas
    ]


def registrar_clasificacion(datos: dict, credenciales: dict = None):
    id_clasificador = _entero(datos, "idClasificador")
    isbn = _isbn(datos, "isbn")
    id_concepto = _entero(datos, "idConcepto")
    modelo_cloud = _modelo_cloud(datos, "modeloCloud")

    id_clasificacion = queries.registrar_clasificacion(id_clasificador, isbn, id_concepto, modelo_cloud)
    return {
        "idClasificacion": id_clasificacion,
        "mensaje": "Clasificación registrada correctamente.",
    }


def obtener_progreso_usuario(datos: dict, credenciales: dict = None):
    id_clasificador = _entero(datos, "idClasificador")
    progreso = queries.obtener_progreso_usuario(id_clasificador)
    return {
        "idClasificador": id_clasificador,
        "totalClasificados": progreso["total_clasificados"],
        "totalPendientes": progreso["total_pendientes"],
    }


def registrar_clasificador(datos: dict, credenciales: dict = None):
    """
    correo es OPCIONAL (Paso 14: la GUI lo captura, pero el módulo no lo
    usa para nada operativo -- se guarda solo como dato de contacto, sin
    validarlo como identidad; ver Tarea 5, pregunta de reflexión sobre
    confiar en el correo).
    """
    nombre = _campo_requerido(datos, "nombre")
    apellido = _campo_requerido(datos, "apellido")
    correo = (datos.get("correo") or "").strip() or None
    id_clasificador = queries.registrar_clasificador(nombre, apellido, correo)
    return {"idClasificador": id_clasificador}


def obtener_estadisticas_por_modelo(datos: dict, credenciales: dict = None):
    """Tarea 1: protegida con WS-Security -- credenciales viene del soap:Header."""
    security.verificar_ws_security(credenciales)

    filas = queries.obtener_estadisticas_por_modelo()
    conteos = {"IaaS": 0, "PaaS": 0, "SaaS": 0, "FaaS": 0}
    for fila in filas:
        conteos[fila["modelo_cloud"]] = fila["total"]
    return {
        "totalIaaS": conteos["IaaS"],
        "totalPaaS": conteos["PaaS"],
        "totalSaaS": conteos["SaaS"],
        "totalFaaS": conteos["FaaS"],
    }
