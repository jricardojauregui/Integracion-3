"""
Verificación end-to-end de las 5 operaciones + WS-Security (Paso 15 / Parte 9).

Ejercita el servidor real (app.py -> envelope.py -> service.py -> faults.py)
con la capa de PostgreSQL (db/queries.py) sustituida por una base EN MEMORIA
con el mismo comportamiento de negocio, tal como describe docs/TEST_PLAN.md
("la única pieza reemplazada es la capa de PostgreSQL").

Cubre los 10 casos de docs/TEST_PLAN.md (4 positivos + 6 negativos). No
intenta reproducir byte a byte los XML de evidencia/ (esos ya se generaron
contra un servidor real); comprueba que el codigo portado a este repo
exhibe el MISMO comportamiento: status HTTP, faultcode y codigo de Fault.

Correr desde apps/services/library_soap_service/:  pytest tests/ -q
"""
import os

import pytest
from werkzeug.security import generate_password_hash

# WS-Security (Tarea 1): se leen con os.getenv EN CADA LLAMADA (soap/security.py),
# así que basta con fijarlas antes de invocar la operación protegida.
os.environ["WS_SECURITY_USERNAME"] = "admin-estadisticas"
# pbkdf2 explícito: portable en cualquier build de Python/OpenSSL (el default
# scrypt de werkzeug no está disponible en todos los entornos).
os.environ["WS_SECURITY_PASSWORD_HASH"] = generate_password_hash(
    "clave-secreta-2026", method="pbkdf2:sha256"
)

from app import app  # noqa: E402
from db import queries  # noqa: E402
from soap import faults  # noqa: E402


# ---------------------------------------------------------------------
# Base de datos en memoria — mismo contrato que db/queries.py real.
# ---------------------------------------------------------------------
class BDMemoria:
    def __init__(self):
        # Catalogo de solo lectura del monolito: (isbn, id_concepto) -> datos.
        self.catalogo = {
            ("978-0-307-47472-8", 7): {
                "titulo_libro": "1984",
                "categoria": "Distopía",
                "nombre_concepto": "Vigilancia masiva",
            },
            ("978-0-14-118776-1", 12): {
                "titulo_libro": "Un mundo feliz",
                "categoria": "Distopía",
                "nombre_concepto": "Condicionamiento social",
            },
        }
        self.clasificadores = {}          # id -> (nombre, apellido, correo)
        self.clasificaciones = []         # dicts: id_clasificador, isbn, id_concepto, modelo_cloud
        self._next_clasificador = 1
        self._next_clasificacion = 1

    # -- lecturas -----------------------------------------------------
    def obtener_conceptos_pendientes(self, isbn=None):
        ya = {(c["isbn"], c["id_concepto"]) for c in self.clasificaciones}
        filas = []
        for (cat_isbn, id_concepto), datos in self.catalogo.items():
            if isbn and cat_isbn != isbn:
                continue
            if (cat_isbn, id_concepto) in ya:
                continue
            filas.append(
                {
                    "isbn": cat_isbn,
                    "titulo_libro": datos["titulo_libro"],
                    "categoria": datos["categoria"],
                    "id_concepto": id_concepto,
                    "nombre_concepto": datos["nombre_concepto"],
                }
            )
        return sorted(filas, key=lambda f: (f["titulo_libro"], f["nombre_concepto"]))

    def obtener_progreso_usuario(self, id_clasificador):
        if id_clasificador not in self.clasificadores:
            raise faults.LibreriaFault(faults.CLASIFICADOR_NO_ENCONTRADO, "El clasificador no existe.")
        total = sum(1 for c in self.clasificaciones if c["id_clasificador"] == id_clasificador)
        return {"total_clasificados": total, "total_pendientes": len(self.obtener_conceptos_pendientes())}

    def obtener_estadisticas_por_modelo(self):
        conteo = {}
        for c in self.clasificaciones:
            conteo[c["modelo_cloud"]] = conteo.get(c["modelo_cloud"], 0) + 1
        return [{"modelo_cloud": m, "total": t} for m, t in conteo.items()]

    # -- escrituras -------------------------------------------------
    def registrar_clasificador(self, nombre, apellido, correo=None):
        nuevo = self._next_clasificador
        self._next_clasificador += 1
        self.clasificadores[nuevo] = (nombre, apellido, correo)
        return nuevo

    def registrar_clasificacion(self, id_clasificador, isbn, id_concepto, modelo_cloud):
        if id_clasificador not in self.clasificadores:
            raise faults.LibreriaFault(faults.CLASIFICADOR_NO_ENCONTRADO, "El clasificador no existe.")
        if not any(cat_isbn == isbn for (cat_isbn, _c) in self.catalogo):
            raise faults.LibreriaFault(faults.ISBN_NO_ENCONTRADO, "El ISBN no existe en el catálogo.")
        if (isbn, id_concepto) not in self.catalogo:
            raise faults.LibreriaFault(
                faults.CONCEPTO_NO_ENCONTRADO, "Ese concepto no está definido para ese libro."
            )
        for c in self.clasificaciones:
            if (c["id_clasificador"], c["isbn"], c["id_concepto"]) == (id_clasificador, isbn, id_concepto):
                raise faults.LibreriaFault(
                    faults.CLASIFICACION_DUPLICADA,
                    "Este clasificador ya registró una clasificación para ese concepto de ese libro.",
                )
        nuevo = self._next_clasificacion
        self._next_clasificacion += 1
        self.clasificaciones.append(
            {
                "id_clasificacion": nuevo,
                "id_clasificador": id_clasificador,
                "isbn": isbn,
                "id_concepto": id_concepto,
                "modelo_cloud": modelo_cloud,
            }
        )
        return nuevo


@pytest.fixture
def bd(monkeypatch):
    memoria = BDMemoria()
    for nombre in (
        "obtener_conceptos_pendientes",
        "obtener_progreso_usuario",
        "obtener_estadisticas_por_modelo",
        "registrar_clasificador",
        "registrar_clasificacion",
    ):
        monkeypatch.setattr(queries, nombre, getattr(memoria, nombre))
    return memoria


@pytest.fixture
def client(bd):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


NS = 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="urn:udem:iac:libreria:soap"'
WSSE = 'xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"'


def _post(client, cuerpo):
    return client.post("/soap", data=cuerpo.encode("utf-8"), content_type="text/xml")


def _registrar_clasificador(client, nombre="Ricardo", apellido="Jáuregui"):
    r = _post(
        client,
        f'<soap:Envelope {NS}><soap:Body><tns:RegistrarClasificadorRequest>'
        f"<tns:nombre>{nombre}</tns:nombre><tns:apellido>{apellido}</tns:apellido>"
        f"</tns:RegistrarClasificadorRequest></soap:Body></soap:Envelope>",
    )
    assert r.status_code == 200
    return r


def _registrar_iaas(client):
    return _post(
        client,
        f"<soap:Envelope {NS}><soap:Body><tns:RegistrarClasificacionRequest>"
        f"<tns:idClasificador>1</tns:idClasificador><tns:isbn>978-0-307-47472-8</tns:isbn>"
        f"<tns:idConcepto>7</tns:idConcepto><tns:modeloCloud>IaaS</tns:modeloCloud>"
        f"</tns:RegistrarClasificacionRequest></soap:Body></soap:Envelope>",
    )


# ------------------------- PRUEBAS POSITIVAS -------------------------

def test_p01_conceptos_pendientes(client):
    _registrar_clasificador(client)
    r = _post(client, f'<soap:Envelope {NS}><soap:Body><tns:ObtenerConceptosPendientesRequest/></soap:Body></soap:Envelope>')
    assert r.status_code == 200
    assert r.data.count(b"<tns:concepto>") == 2  # 2 unidades concepto en el catalogo


def test_p02_registrar_iaas(client):
    _registrar_clasificador(client)
    r = _registrar_iaas(client)
    assert r.status_code == 200
    assert b"<tns:idClasificacion>1</tns:idClasificacion>" in r.data
    assert "Clasificación registrada correctamente.".encode() in r.data


def test_p03_progreso_usuario(client):
    _registrar_clasificador(client)
    _registrar_iaas(client)
    r = _post(
        client,
        f"<soap:Envelope {NS}><soap:Body><tns:ObtenerProgresoUsuarioRequest>"
        f"<tns:idClasificador>1</tns:idClasificador>"
        f"</tns:ObtenerProgresoUsuarioRequest></soap:Body></soap:Envelope>",
    )
    assert r.status_code == 200
    assert b"<tns:totalClasificados>1</tns:totalClasificados>" in r.data
    assert b"<tns:totalPendientes>1</tns:totalPendientes>" in r.data


def test_p04_estadisticas_credenciales_correctas(client):
    _registrar_clasificador(client)
    _registrar_iaas(client)
    r = _post(
        client,
        f"<soap:Envelope {NS} {WSSE}><soap:Header><wsse:Security><wsse:UsernameToken>"
        f"<wsse:Username>admin-estadisticas</wsse:Username><wsse:Password>clave-secreta-2026</wsse:Password>"
        f"</wsse:UsernameToken></wsse:Security></soap:Header>"
        f"<soap:Body><tns:ObtenerEstadisticasPorModeloRequest/></soap:Body></soap:Envelope>",
    )
    assert r.status_code == 200
    assert b"<tns:totalIaaS>1</tns:totalIaaS>" in r.data
    assert b"<tns:totalPaaS>0</tns:totalPaaS>" in r.data


# ------------------------- PRUEBAS NEGATIVAS -------------------------

def test_n01_clasificacion_duplicada_409(client):
    _registrar_clasificador(client)
    _registrar_iaas(client)
    r = _registrar_iaas(client)
    assert r.status_code == 409
    assert b"<faultcode>soap:Client</faultcode>" in r.data
    assert b"<tns:codigo>CLASIFICACION_DUPLICADA</tns:codigo>" in r.data


def test_n02_concepto_inexistente_400(client):
    _registrar_clasificador(client)
    r = _post(
        client,
        f"<soap:Envelope {NS}><soap:Body><tns:RegistrarClasificacionRequest>"
        f"<tns:idClasificador>1</tns:idClasificador><tns:isbn>978-0-307-47472-8</tns:isbn>"
        f"<tns:idConcepto>9999</tns:idConcepto><tns:modeloCloud>PaaS</tns:modeloCloud>"
        f"</tns:RegistrarClasificacionRequest></soap:Body></soap:Envelope>",
    )
    assert r.status_code == 400
    assert b"<tns:codigo>CONCEPTO_NO_ENCONTRADO</tns:codigo>" in r.data


def test_n03_modelo_invalido_400(client):
    _registrar_clasificador(client)
    r = _post(
        client,
        f"<soap:Envelope {NS}><soap:Body><tns:RegistrarClasificacionRequest>"
        f"<tns:idClasificador>1</tns:idClasificador><tns:isbn>978-0-14-118776-1</tns:isbn>"
        f"<tns:idConcepto>12</tns:idConcepto><tns:modeloCloud>Xaas</tns:modeloCloud>"
        f"</tns:RegistrarClasificacionRequest></soap:Body></soap:Envelope>",
    )
    assert r.status_code == 400
    assert b"<tns:codigo>DATOS_INVALIDOS</tns:codigo>" in r.data


def test_n04_xml_invalido_400(client):
    r = _post(client, "<soap:Envelope><soap:Body>")
    assert r.status_code == 400
    assert b"<tns:codigo>ENVELOPE_INVALIDO</tns:codigo>" in r.data


def test_n05_estadisticas_sin_credenciales_401(client):
    r = _post(client, f'<soap:Envelope {NS}><soap:Body><tns:ObtenerEstadisticasPorModeloRequest/></soap:Body></soap:Envelope>')
    assert r.status_code == 401
    assert b"<tns:codigo>CREDENCIALES_INVALIDAS</tns:codigo>" in r.data


def test_n06_estadisticas_password_incorrecta_401(client):
    r = _post(
        client,
        f"<soap:Envelope {NS} {WSSE}><soap:Header><wsse:Security><wsse:UsernameToken>"
        f"<wsse:Username>admin-estadisticas</wsse:Username><wsse:Password>clave-mala</wsse:Password>"
        f"</wsse:UsernameToken></wsse:Security></soap:Header>"
        f"<soap:Body><tns:ObtenerEstadisticasPorModeloRequest/></soap:Body></soap:Envelope>",
    )
    assert r.status_code == 401
    assert b"<tns:codigo>CREDENCIALES_INVALIDAS</tns:codigo>" in r.data
