"""
WS-Security simplificado (Tarea 1 de trabajo en casa) — usuario/contraseña
en el Header del sobre SOAP, apropiado para el alcance del ejercicio (no
es WS-Security completo con firma digital ni PasswordDigest/Nonce).

Protege únicamente ObtenerEstadisticasPorModelo (la operación nueva de
esta tarea) — el resto del módulo sigue sin autenticación por diseño
(decisión de ingeniería #7): agregar seguridad aquí es una extensión
puntual sobre una operación sensible, no un cambio de esa decisión base.

La contraseña NUNCA se guarda en texto plano: se compara contra un hash
(werkzeug.security, ya viene con Flask) guardado en variables de entorno.
"""
import os

from werkzeug.security import check_password_hash

from soap import faults


def verificar_ws_security(credenciales: dict) -> None:
    """
    credenciales viene de soap/envelope.py: {"usuario": str, "password": str},
    extraído de <wsse:Security><wsse:UsernameToken> en el soap:Header.
    Lanza LibreriaFault(CREDENCIALES_INVALIDAS) si falta o no coincide.
    """
    usuario_esperado = os.getenv("WS_SECURITY_USERNAME", "")
    hash_esperado = os.getenv("WS_SECURITY_PASSWORD_HASH", "")

    if not usuario_esperado or not hash_esperado:
        # Server mal configurado (falta el .env) -- es un error del
        # servidor, no algo que el cliente pueda arreglar mandando otro dato.
        raise faults.LibreriaFault(
            faults.ERROR_INTERNO, "El servidor no tiene configurado WS-Security."
        )

    credenciales = credenciales or {}
    usuario = credenciales.get("usuario", "")
    password = credenciales.get("password", "")

    if not usuario or not password:
        raise faults.LibreriaFault(
            faults.CREDENCIALES_INVALIDAS,
            "Esta operación requiere credenciales en soap:Header (wsse:UsernameToken).",
        )

    if usuario != usuario_esperado or not check_password_hash(hash_esperado, password):
        raise faults.LibreriaFault(
            faults.CREDENCIALES_INVALIDAS, "Usuario o contraseña inválidos."
        )
