"""
Pruebas del módulo SOAP. Placeholder — se llenan en el paso de pruebas
(normales y de error, según el objetivo del ejercicio).

Correr con: pytest tests/
"""
import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_wsdl_se_publica(client):
    """El contrato debe estar accesible — condición mínima para interoperar."""
    respuesta = client.get("/wsdl")
    assert respuesta.status_code == 200
    assert b"LibraryClassifierService" in respuesta.data


# TODO (paso de pruebas): casos normales (registrar clasificación válida,
# consultar pendientes, consultar progreso) y casos de error (ISBN
# inexistente, clasificación duplicada -> Fault, datos inválidos -> Fault).
