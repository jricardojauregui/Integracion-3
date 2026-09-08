"""
Catálogo de errores de negocio del módulo, reportados siempre como
soap:Fault (decisión de ingeniería #8) — nunca como error crudo de
PostgreSQL ni como código HTTP sin cuerpo interpretable.

Paso 13: cada código carga también su faultcode SOAP (Client/Server) y
su status HTTP, para que el cliente pueda distinguir programáticamente
errores de entrada, conflictos y errores internos — no solo leer un
texto genérico. Cada código de este catálogo debe reflejarse también
en el XSD (LibreriaFaultDetail) y en wsdl/library-classifier.wsdl.
"""


class LibreriaFault(Exception):
    """Se lanza desde db/queries.py o soap/service.py; app.py la atrapa y arma el Fault."""

    def __init__(self, codigo: str, descripcion: str):
        self.codigo = codigo
        self.descripcion = descripcion
        super().__init__(f"{codigo}: {descripcion}")


# Códigos de negocio (Paso 2, Paso 4, Paso 9).
ISBN_NO_ENCONTRADO = "ISBN_NO_ENCONTRADO"
CONCEPTO_NO_ENCONTRADO = "CONCEPTO_NO_ENCONTRADO"
CLASIFICADOR_NO_ENCONTRADO = "CLASIFICADOR_NO_ENCONTRADO"
CLASIFICACION_DUPLICADA = "CLASIFICACION_DUPLICADA"
DATOS_INVALIDOS = "DATOS_INVALIDOS"

# Códigos de infraestructura del propio sobre SOAP (Paso 11).
ENVELOPE_INVALIDO = "ENVELOPE_INVALIDO"
ERROR_INTERNO = "ERROR_INTERNO"

# Tarea 1 (WS-Security de trabajo en casa).
CREDENCIALES_INVALIDAS = "CREDENCIALES_INVALIDAS"

# ---------------------------------------------------------------------
# Paso 13 — tabla de diseño de errores:
#   Concepto inexistente          -> Fault de cliente
#   Modelo Cloud inválido         -> Fault de validación (cliente)
#   Clasificación duplicada       -> Fault de conflicto, 409
#   XML inválido                  -> Fault de cliente (nunca llega a SQL)
#   Falla de PostgreSQL no prevista -> Fault de servidor, detalle solo en log
# ---------------------------------------------------------------------
_SOAP_FAULTCODE = {
    ENVELOPE_INVALIDO: "soap:Client",
    DATOS_INVALIDOS: "soap:Client",
    ISBN_NO_ENCONTRADO: "soap:Client",
    CONCEPTO_NO_ENCONTRADO: "soap:Client",
    CLASIFICADOR_NO_ENCONTRADO: "soap:Client",
    CLASIFICACION_DUPLICADA: "soap:Client",  # es un conflicto, pero lo origina un pedido del cliente
    ERROR_INTERNO: "soap:Server",
    CREDENCIALES_INVALIDAS: "soap:Client",
}

_HTTP_STATUS = {
    ENVELOPE_INVALIDO: 400,
    DATOS_INVALIDOS: 400,
    ISBN_NO_ENCONTRADO: 400,
    CONCEPTO_NO_ENCONTRADO: 400,
    CLASIFICADOR_NO_ENCONTRADO: 400,
    CLASIFICACION_DUPLICADA: 409,
    ERROR_INTERNO: 500,
    CREDENCIALES_INVALIDAS: 401,
}


def soap_faultcode(codigo: str) -> str:
    """soap:Client para errores de entrada/conflicto, soap:Server para lo no anticipado."""
    return _SOAP_FAULTCODE.get(codigo, "soap:Server")


def http_status(codigo: str) -> int:
    """Código HTTP de la respuesta Flask — 400 validación, 409 conflicto, 500 servidor."""
    return _HTTP_STATUS.get(codigo, 500)
