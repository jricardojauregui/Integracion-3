"""
Excepciones propias del dominio.

Se definen excepciones especificas (en vez de lanzar ValueError generico)
para que la GUI y la CLI puedan distinguir *que tipo* de problema ocurrio
y reaccionar distinto: un error de validacion es culpa del dato capturado
y se le muestra al usuario tal cual; un error de clasificacion es una falla
interna y se reporta de otra forma.
"""


class ErrorClasificador(Exception):
    """Clase base: permite capturar cualquier error del dominio con un solo except."""


class EntradaInvalidaError(ErrorClasificador):
    """Los datos capturados por el usuario no cumplen las reglas de validacion.

    El mensaje ya viene redactado para mostrarse directamente al usuario.
    """


class ClasificacionError(ErrorClasificador):
    """Fallo inesperado dentro del motor de clasificacion."""
