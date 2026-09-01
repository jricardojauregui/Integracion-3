"""
Configuracion de la aplicacion.

CORRIGE [F-1]: ningun secreto vive en el codigo. Todo se lee de variables
de entorno, que en produccion son inyectadas por el gestor de secretos
(AWS Secrets Manager / HashiCorp Vault) mediante un sidecar o CSI driver,
nunca escritas en la imagen ni en el repositorio.

La aplicacion se NIEGA A ARRANCAR si falta un secreto obligatorio en
produccion (fail-fast). Es preferible que el despliegue falle de inmediato
y visiblemente a que arranque con un valor por defecto inseguro y nadie
lo note durante meses.
"""

import os
import secrets
from dataclasses import dataclass, field
from typing import List


class ConfiguracionInvalida(RuntimeError):
    """Falta configuracion obligatoria o tiene un valor no permitido."""


def _bool_env(nombre: str, defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "yes", "si"}


@dataclass
class Config:
    entorno: str = field(default_factory=lambda: os.getenv("APP_ENV", "desarrollo"))

    # Firma de tokens
    jwt_secret: str = ""
    jwt_algoritmo: str = "HS256"
    access_token_minutos: int = 10      # corto: limita la ventana de robo
    refresh_token_dias: int = 7

    # Origenes permitidos (CORRIGE [F-14]: lista explicita, no "*")
    cors_origenes: List[str] = field(default_factory=list)

    # Core bancario on-premises
    core_url: str = field(default_factory=lambda: os.getenv("CORE_URL", "http://core.local:8080"))
    core_timeout_s: float = 2.0
    core_reintentos: int = 3
    circuito_umbral_fallos: int = 5
    circuito_espera_s: float = 30.0

    # Limites de negocio y de abuso
    limite_login_intentos: int = 5
    limite_login_ventana_s: int = 300
    monto_maximo_sin_2fa: str = "10000.00"

    def __post_init__(self):
        es_produccion = self.entorno.lower() in {"produccion", "production", "prod"}

        secreto = os.getenv("JWT_SECRET", "")
        if not secreto:
            if es_produccion:
                # Fail-fast: nunca inventar un secreto en produccion.
                raise ConfiguracionInvalida(
                    "JWT_SECRET es obligatorio en produccion. "
                    "Debe inyectarse desde el gestor de secretos."
                )
            # En desarrollo/pruebas se genera uno efimero y aleatorio.
            # Al ser distinto en cada arranque, es inservible como puerta
            # trasera y ademas invalida tokens viejos.
            secreto = secrets.token_urlsafe(48)
        if len(secreto) < 32:
            raise ConfiguracionInvalida("JWT_SECRET debe tener al menos 32 caracteres.")
        self.jwt_secret = secreto

        origenes = os.getenv("CORS_ORIGENES", "")
        self.cors_origenes = [o.strip() for o in origenes.split(",") if o.strip()]
        if es_produccion and (not self.cors_origenes or "*" in self.cors_origenes):
            raise ConfiguracionInvalida(
                "CORS_ORIGENES debe listar dominios explicitos en produccion."
            )
        if not self.cors_origenes:
            self.cors_origenes = ["https://app.banco-ejemplo.mx"]

    @property
    def es_produccion(self) -> bool:
        return self.entorno.lower() in {"produccion", "production", "prod"}


config = Config()
