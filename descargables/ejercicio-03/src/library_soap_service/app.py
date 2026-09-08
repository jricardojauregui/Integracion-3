#!/usr/bin/env python3
"""
library_soap_service — Módulo SOAP independiente (Ejercicio04)

Punto de entrada. Flask puro, sin blueprints. Un solo endpoint SOAP
(POST /soap): recibe el sobre, lo parsea (envelope.py), despacha la
operación (soap/service.py) y arma la respuesta o el Fault.
"""
from flask import Flask, request, Response

from config.settings import get_settings
from soap import envelope, faults
from soap.service import despachar_operacion

app = Flask(__name__)
settings = get_settings()


@app.get("/wsdl")
def servir_wsdl():
    """Publica el contrato. Un cliente SOAP descubre las operaciones aquí."""
    with open(settings.WSDL_PATH, "r", encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/xml")


@app.post("/soap")
def soap_endpoint():
    """
    Único punto de entrada SOAP (Paso 11): lee el Envelope, identifica
    la operación pedida, valida datos, ejecuta la lógica y construye
    la respuesta. Toda excepción de negocio (LibreriaFault) se traduce
    a un soap:Fault; cualquier otra excepción NO prevista también —
    nunca se deja escapar un traceback de Python ni un error crudo de
    PostgreSQL en la respuesta (decisión de ingeniería #8).
    """
    try:
        operacion, datos, credenciales = envelope.parsear_request(request.data)
        resultado = despachar_operacion(operacion, datos, credenciales)
        return Response(
            envelope.construir_response(operacion, resultado),
            mimetype="text/xml",
        )
    except faults.LibreriaFault as fault:
        # Paso 13: el status HTTP depende del tipo de error -- 400 para
        # entrada/no-encontrado, 409 para conflicto (duplicado), 500 solo
        # para lo que de verdad es un error de servidor.
        return Response(
            envelope.construir_fault(fault),
            status=faults.http_status(fault.codigo),
            mimetype="text/xml",
        )
    except Exception:
        # Falla no anticipada (PostgreSQL u otra): el detalle técnico
        # completo va SOLO al log del servidor; el cliente recibe un
        # Fault genérico de servidor, sin stack trace, sin SQL, sin
        # contraseñas ni rutas internas (Paso 13).
        app.logger.exception("Error inesperado procesando una petición SOAP")
        fault_generico = faults.LibreriaFault(
            faults.ERROR_INTERNO, "Ocurrió un error interno procesando la petición."
        )
        return Response(
            envelope.construir_fault(fault_generico),
            status=faults.http_status(faults.ERROR_INTERNO),
            mimetype="text/xml",
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT, debug=settings.FLASK_DEBUG)
