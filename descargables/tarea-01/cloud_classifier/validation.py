"""
Validacion de los datos capturados por el usuario.

Vive en la capa de logica (no en la GUI) para que las mismas reglas se
reutilicen desde la CLI y desde las pruebas, sin depender de tkinter.
Cada funcion devuelve el valor ya limpio (con ``strip()``) o lanza
``EntradaInvalidaError`` con un mensaje listo para mostrarse.
"""

import re

from .exceptions import EntradaInvalidaError

NOMBRE_MIN = 2
NOMBRE_MAX = 60
DESCRIPCION_MIN = 8
DESCRIPCION_MAX = 2000

# Letras (incluye acentos y ñ gracias a re.UNICODE), espacios, apostrofes y
# guiones. Sin digitos ni simbolos.
_RE_NOMBRE = re.compile(r"^[^\W\d_][^\W\d_ '\-]*(?:[ '\-][^\W\d_][^\W\d_ '\-]*)*$",
                        re.UNICODE)


def validar_nombre(valor: str, campo: str = "Nombre") -> str:
    """
    Valida nombre o apellido (comparten reglas, por eso una sola funcion).

    :param campo: se usa para redactar el mensaje de error.
    """
    if valor is None or not valor.strip():
        raise EntradaInvalidaError(f'El campo "{campo}" no puede estar vacio.')

    limpio = valor.strip()

    if not (NOMBRE_MIN <= len(limpio) <= NOMBRE_MAX):
        raise EntradaInvalidaError(
            f'El campo "{campo}" debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres.'
        )

    if not _RE_NOMBRE.match(limpio):
        raise EntradaInvalidaError(
            f'El campo "{campo}" solo puede contener letras y espacios.'
        )

    return limpio


def validar_descripcion(valor: str) -> str:
    """Valida el texto que se enviara al clasificador."""
    if valor is None or not valor.strip():
        raise EntradaInvalidaError(
            "Escribe una descripcion del servicio Cloud a clasificar."
        )

    limpio = valor.strip()

    if len(limpio) < DESCRIPCION_MIN:
        raise EntradaInvalidaError(
            f"La descripcion es muy corta (minimo {DESCRIPCION_MIN} caracteres). "
            "Agrega mas contexto sobre el servicio."
        )

    if len(limpio) > DESCRIPCION_MAX:
        raise EntradaInvalidaError(
            f"La descripcion es demasiado larga (maximo {DESCRIPCION_MAX} caracteres)."
        )

    return limpio
