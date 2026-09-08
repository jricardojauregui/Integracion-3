"""
Construcción y parseo MANUAL del sobre SOAP con xml.etree.ElementTree
(decisión de ingeniería #6 — nada de Spyne/Zeep).

Único lugar del módulo que conoce los namespaces SOAP (soap:Envelope,
soap:Header, soap:Body, soap:Fault) y el namespace propio del contrato
(tns). Todo el armado usa SubElement + .text — ElementTree escapa
automáticamente cualquier valor (&, <, >, comillas), así que en ningún
punto de este archivo se concatena XML a mano con f-strings/format
sobre datos que vengan del cliente (Paso 11: "no concatenes XML sin
escapar valores").
"""
from xml.etree import ElementTree as ET

from soap import faults as faults_mod
from soap.faults import ENVELOPE_INVALIDO, LibreriaFault

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "urn:udem:iac:libreria:soap"
WSSE_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"

ET.register_namespace("soap", SOAP_NS)
ET.register_namespace("tns", TNS)
ET.register_namespace("wsse", WSSE_NS)


def _q(tag: str) -> str:
    """Nombre calificado en el namespace del contrato (elementFormDefault=qualified)."""
    return f"{{{TNS}}}{tag}"


def _local(tag: str) -> str:
    """Nombre local de un elemento, sin el namespace: '{ns}Tag' -> 'Tag'."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def _extraer_credenciales_wsse(header_elem) -> dict:
    """
    Lee <wsse:Security><wsse:UsernameToken><wsse:Username>/<wsse:Password>
    del soap:Header. Devuelve {} si no hay Header, no hay Security, o no
    hay UsernameToken -- eso es válido para toda operación que no
    requiera WS-Security; solo la protegida se queja de credenciales
    vacías (soap/security.py).
    """
    if header_elem is None:
        return {}
    security = header_elem.find(f"{{{WSSE_NS}}}Security")
    if security is None:
        return {}
    token = security.find(f"{{{WSSE_NS}}}UsernameToken")
    if token is None:
        return {}
    usuario_elem = token.find(f"{{{WSSE_NS}}}Username")
    password_elem = token.find(f"{{{WSSE_NS}}}Password")
    return {
        "usuario": (usuario_elem.text or "").strip() if usuario_elem is not None else "",
        "password": (password_elem.text or "").strip() if password_elem is not None else "",
    }


def parsear_request(raw_xml: bytes):
    """
    Lee <soap:Envelope>[<soap:Header/>]<soap:Body><OpRequest>...</Body>,
    diferenciando explícitamente Envelope/Header/Body (Paso 11).

    El Header es opcional y, por ahora, se ignora a propósito: la
    decisión de ingeniería #7 es que el módulo no tiene autenticación
    de sesión en esta etapa, así que no hay nada que leer de ahí. Se
    deja localizado (no solo omitido) para que quede explícito que se
    consideró, no que se pasó por alto.

    Devuelve (nombre_operacion, datos, credenciales): datos es un dict
    plano {nombre_campo: texto} con los hijos directos del elemento de
    request -- la validación de tipos/formato vive en soap/service.py,
    no aquí. credenciales es {} salvo que el Header traiga un
    <wsse:Security><wsse:UsernameToken> (Tarea 1, WS-Security); solo lo
    usa la operación protegida, las demás lo ignoran sin problema.
    """
    try:
        envelope = ET.fromstring(raw_xml)
    except ET.ParseError as err:
        raise LibreriaFault(ENVELOPE_INVALIDO, f"XML mal formado: {err}")

    if _local(envelope.tag) != "Envelope":
        raise LibreriaFault(
            ENVELOPE_INVALIDO, "La raíz del mensaje debe ser <soap:Envelope>."
        )

    header_elem = envelope.find(f"{{{SOAP_NS}}}Header")  # opcional
    credenciales = _extraer_credenciales_wsse(header_elem)

    body = envelope.find(f"{{{SOAP_NS}}}Body")
    if body is None:
        raise LibreriaFault(ENVELOPE_INVALIDO, "El Envelope no tiene <soap:Body>.")

    hijos = list(body)
    if not hijos:
        raise LibreriaFault(ENVELOPE_INVALIDO, "<soap:Body> está vacío.")

    request_elem = hijos[0]
    tag_local = _local(request_elem.tag)
    if not tag_local.endswith("Request"):
        raise LibreriaFault(
            ENVELOPE_INVALIDO,
            f"Se esperaba un elemento '*Request' dentro de Body; se recibió '{tag_local}'.",
        )
    operacion = tag_local[: -len("Request")]

    datos = {_local(hijo.tag): (hijo.text or "").strip() for hijo in request_elem}
    return operacion, datos, credenciales


def _envelope_con_body(*hijos_de_body) -> ET.Element:
    envelope = ET.Element(f"{{{SOAP_NS}}}Envelope")
    body = ET.SubElement(envelope, f"{{{SOAP_NS}}}Body")
    for hijo in hijos_de_body:
        body.append(hijo)
    return envelope


def _dict_a_elemento(tag: str, datos: dict) -> ET.Element:
    """Un elemento con hijos planos tag:valor, en el orden del dict (== orden del XSD)."""
    elem = ET.Element(_q(tag))
    for campo, valor in datos.items():
        ET.SubElement(elem, _q(campo)).text = "" if valor is None else str(valor)
    return elem


def _respuesta_conceptos_pendientes(resultado: list) -> ET.Element:
    """Único caso con forma de lista: 0..N <tns:concepto> dentro del Response."""
    elem = ET.Element(_q("ObtenerConceptosPendientesResponse"))
    for concepto in resultado:
        elem.append(_dict_a_elemento("concepto", concepto))
    return elem


# RegistrarClasificacion, ObtenerProgresoUsuario y RegistrarClasificador
# devuelven todos un único elemento con campos planos — mismo constructor
# genérico, solo cambia el nombre del tag y el dict de datos.
_CONSTRUCTORES_RESPUESTA = {
    "ObtenerConceptosPendientes": _respuesta_conceptos_pendientes,
}


def construir_response(operacion: str, resultado) -> bytes:
    constructor = _CONSTRUCTORES_RESPUESTA.get(operacion)
    elemento = (
        constructor(resultado)
        if constructor
        else _dict_a_elemento(f"{operacion}Response", resultado)
    )
    envelope = _envelope_con_body(elemento)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def construir_fault(fault: LibreriaFault) -> bytes:
    """
    faultcode es soap:Client o soap:Server según el catálogo de
    soap/faults.py (Paso 13) -- nunca hardcodeado a Server como antes,
    así el cliente puede distinguir programáticamente error de entrada
    vs. error interno solo con el faultcode, sin parsear el detail.
    """
    soap_fault = ET.Element(f"{{{SOAP_NS}}}Fault")
    ET.SubElement(soap_fault, "faultcode").text = faults_mod.soap_faultcode(fault.codigo)
    ET.SubElement(soap_fault, "faultstring").text = fault.descripcion
    detail = ET.SubElement(soap_fault, "detail")
    detalle = ET.SubElement(detail, _q("LibreriaFaultDetail"))
    ET.SubElement(detalle, _q("codigo")).text = fault.codigo
    ET.SubElement(detalle, _q("descripcion")).text = fault.descripcion
    envelope = _envelope_con_body(soap_fault)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)
