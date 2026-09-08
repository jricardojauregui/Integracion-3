"""
Configuración del módulo, leída de variables de entorno (.env).

Nada de credenciales en el código — mismo principio que
apps/web-monolith y apps/services/soap del monolito/Ejercicio03.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    PORT: int
    FLASK_DEBUG: bool
    WSDL_PATH: str


def get_settings() -> Settings:
    return Settings(
        DB_HOST=os.getenv("DB_HOST", "localhost"),
        DB_PORT=int(os.getenv("DB_PORT", "5432")),
        DB_NAME=os.getenv("DB_NAME", "library"),
        DB_USER=os.getenv("DB_USER", "soap_module_user"),
        DB_PASS=os.getenv("DB_PASS", ""),
        PORT=int(os.getenv("PORT", "5050")),
        FLASK_DEBUG=os.getenv("FLASK_DEBUG", "0") == "1",
        WSDL_PATH=str(_BASE_DIR / "wsdl" / "library-classifier.wsdl"),
    )
