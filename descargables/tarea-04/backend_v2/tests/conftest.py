"""
Configuracion compartida de pytest.

Corrige un problema real detectado al ejecutar la suite por primera vez:
las pruebas de rate limiting agotaban el limite por IP y, como TestClient
usa siempre la misma IP de origen, las pruebas posteriores recibian 429 y
fallaban sin que hubiera nada malo en el codigo bajo prueba.

Es un buen recordatorio de que el estado global (aqui, el contador de
intentos en memoria) acopla pruebas que deberian ser independientes. En
produccion ese contador vive en Redis con TTL, pero el principio es el
mismo: si el estado no se aisla, las pruebas se vuelven dependientes del
orden de ejecucion y por lo tanto poco confiables.
"""

import pytest

from app.security import _INTENTOS, _TOKENS_REVOCADOS


@pytest.fixture(autouse=True)
def aislar_estado_global():
    """Limpia contadores y revocaciones antes y despues de cada prueba."""
    _INTENTOS.clear()
    _TOKENS_REVOCADOS.clear()
    yield
    _INTENTOS.clear()
    _TOKENS_REVOCADOS.clear()
