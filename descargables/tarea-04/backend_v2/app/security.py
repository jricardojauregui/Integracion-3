"""
Seguridad: hashing de contrasenas, emision/validacion de tokens y
limitacion de intentos.

Corrige [F-2] (tokens eternos), [F-3] (contrasenas en claro) y
[F-11] (fuerza bruta sin limite).
"""

import hashlib
import hmac
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Set

import jwt

from .config import config


# ---------------------------------------------------------------------------
# Contrasenas
# ---------------------------------------------------------------------------
# CORRIGE [F-3]. En produccion se usa bcrypt/argon2 (passlib). Aqui se
# implementa con PBKDF2-HMAC-SHA256 de la biblioteca estandar para que el
# prototipo corra sin dependencias nativas, pero el esquema es el mismo:
# sal aleatoria por usuario + funcion de derivacion lenta + comparacion en
# tiempo constante.
#
# Lo esencial que v1 violaba: la contrasena NUNCA se almacena ni se compara
# en claro, y la comparacion no debe cortocircuitar (== filtra informacion
# por tiempo de respuesta).
_ITERACIONES = 200_000


def hash_password(password: str, sal: Optional[bytes] = None) -> str:
    if sal is None:
        sal = uuid.uuid4().bytes
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode(), sal, _ITERACIONES)
    return f"pbkdf2${_ITERACIONES}${sal.hex()}${derivada.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    """Comparacion en tiempo constante (hmac.compare_digest)."""
    try:
        _, iteraciones, sal_hex, esperado_hex = almacenado.split("$")
        derivada = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(sal_hex), int(iteraciones)
        )
        return hmac.compare_digest(derivada.hex(), esperado_hex)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
# CORRIGE [F-2]. El access token de v1 no expiraba y no se podia revocar:
# si alguien lo robaba, tenia acceso permanente. Ahora:
#   - 'exp' corto (10 min): limita la ventana de uso de un token robado.
#   - 'jti' unico: permite revocar un token concreto (logout, fraude).
#   - 'typ': distingue access de refresh, para que un refresh token no
#     sirva para llamar endpoints de negocio.
#   - 'aud'/'iss': evita que un token de otro sistema sea aceptado aqui.

_TOKENS_REVOCADOS: Set[str] = set()   # en produccion: Redis con TTL = exp


class TokenInvalido(Exception):
    pass


def emitir_access_token(usuario: str, cuenta: str, roles=("cliente",)) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario,
        "cuenta": cuenta,
        "roles": list(roles),
        "typ": "access",
        "jti": str(uuid.uuid4()),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=config.access_token_minutos),
        "iss": "banca-movil-api",
        "aud": "banca-movil-app",
    }
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algoritmo)


def emitir_refresh_token(usuario: str) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario,
        "typ": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": ahora,
        "exp": ahora + timedelta(days=config.refresh_token_dias),
        "iss": "banca-movil-api",
        "aud": "banca-movil-app",
    }
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algoritmo)


def decodificar_token(token: str, tipo_esperado: str = "access") -> dict:
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            # Lista blanca de algoritmos: evita el ataque de confusion de
            # algoritmo (p.ej. forzar "none" o cambiar RS256 por HS256).
            algorithms=[config.jwt_algoritmo],
            audience="banca-movil-app",
            issuer="banca-movil-api",
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenInvalido("El token expiro.")
    except jwt.InvalidTokenError:
        raise TokenInvalido("Token invalido.")

    if payload.get("typ") != tipo_esperado:
        raise TokenInvalido("Tipo de token incorrecto.")
    if payload.get("jti") in _TOKENS_REVOCADOS:
        raise TokenInvalido("El token fue revocado.")

    return payload


def revocar_token(jti: str) -> None:
    _TOKENS_REVOCADOS.add(jti)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
# CORRIGE [F-11]. Ventana deslizante en memoria; en produccion se mueve a
# Redis (para que el limite sea global entre instancias) y ademas se
# refuerza en el WAF/API Gateway, que frena el trafico antes de que llegue
# a la aplicacion.

_INTENTOS: Dict[str, deque] = defaultdict(deque)


class LimiteExcedido(Exception):
    def __init__(self, espera_s: int):
        super().__init__("Demasiados intentos. Intenta mas tarde.")
        self.espera_s = espera_s


def registrar_intento(clave: str,
                      maximo: Optional[int] = None,
                      ventana_s: Optional[int] = None) -> None:
    maximo = maximo or config.limite_login_intentos
    ventana_s = ventana_s or config.limite_login_ventana_s

    ahora = time.monotonic()
    cola = _INTENTOS[clave]

    while cola and ahora - cola[0] > ventana_s:
        cola.popleft()

    if len(cola) >= maximo:
        espera = int(ventana_s - (ahora - cola[0]))
        raise LimiteExcedido(max(espera, 1))

    cola.append(ahora)


def limpiar_intentos(clave: str) -> None:
    """Se llama tras un login exitoso: el usuario legitimo no queda penalizado."""
    _INTENTOS.pop(clave, None)


def enmascarar(valor: str, visibles: int = 4) -> str:
    """
    CORRIGE [F-12]. v1 escribia el PAN y el token completos en los logs.
    Un log con datos de tarjeta es un incidente de cumplimiento PCI-DSS por
    si solo, porque los logs se replican a sistemas de terceros.
    """
    if not valor:
        return ""
    if len(valor) <= visibles:
        return "*" * len(valor)
    return "*" * (len(valor) - visibles) + valor[-visibles:]
