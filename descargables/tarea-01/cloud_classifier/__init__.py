"""
cloud_classifier
================

Clasificador de modelos de servicio en la nube (IaaS / PaaS / SaaS / FaaS)
a partir de una descripcion en lenguaje natural.

Capas del paquete:

    models.py      Estructuras de datos (dataclasses) y constantes
    exceptions.py  Excepciones del dominio
    nlp.py         Pipeline de NLP (minusculas, limpieza, tokenizacion,
                   stopwords, normalizacion, stemming)
    knowledge.py   Base de conocimiento: QUE se busca (conceptos + patrones)
    classifier.py  Motor: COMO se busca y se puntua
    validation.py  Validacion de entradas
    service.py     Orquestacion (validacion + clasificacion)

Las interfaces (gui.py y classifier_cli.py, en la raiz del proyecto) usan
unicamente ``service.analizar`` y no contienen logica de clasificacion.
"""

from .exceptions import (ClasificacionError, EntradaInvalidaError,
                         ErrorClasificador)
from .models import (FAAS, IAAS, MODELOS, NO_DETERMINADO, PAAS, SAAS,
                     ResultadoClasificacion, TextoProcesado)
from .service import Analisis, analizar

__all__ = [
    "analizar", "Analisis",
    "ResultadoClasificacion", "TextoProcesado",
    "IAAS", "PAAS", "SAAS", "FAAS", "MODELOS", "NO_DETERMINADO",
    "ErrorClasificador", "EntradaInvalidaError", "ClasificacionError",
]

__version__ = "1.0.0"
