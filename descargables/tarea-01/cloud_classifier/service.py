"""
Servicio de aplicacion: orquesta validacion + clasificacion.

ESTE ES EL LIMITE ENTRE LAS INTERFACES Y LA LOGICA. Ni la GUI ni la CLI
llaman directamente a ``classifier.clasificar`` ni a ``validation``: ambas
pasan por aqui. Asi, si manana cambia una regla de validacion o se agrega
un paso al pipeline, se modifica en un solo lugar y las dos interfaces lo
heredan automaticamente.
"""

from dataclasses import dataclass
from typing import Optional

from . import classifier, validation
from .models import ResultadoClasificacion


@dataclass(frozen=True)
class Analisis:
    """Resultado listo para presentarse: quien pregunto y que se detecto."""

    nombre_completo: Optional[str]
    descripcion: str
    resultado: ResultadoClasificacion


def analizar(descripcion: str,
             nombre: Optional[str] = None,
             apellido: Optional[str] = None) -> Analisis:
    """
    Valida y clasifica.

    ``nombre``/``apellido`` son opcionales porque la GUI si los pide (la
    practica lo exige) pero la CLI no: su ejemplo de uso solo recibe el
    texto. Cuando se envian, se validan; cuando no, se omiten.

    :raises EntradaInvalidaError: si algun dato no cumple las reglas.
    :raises ClasificacionError: si el motor falla inesperadamente.
    """
    nombre_completo = None
    if nombre is not None or apellido is not None:
        nombre_valido = validation.validar_nombre(nombre or "", "Nombre")
        apellido_valido = validation.validar_nombre(apellido or "", "Apellido")
        nombre_completo = f"{nombre_valido} {apellido_valido}"

    descripcion_valida = validation.validar_descripcion(descripcion)
    resultado = classifier.clasificar(descripcion_valida)

    return Analisis(
        nombre_completo=nombre_completo,
        descripcion=descripcion_valida,
        resultado=resultado,
    )
