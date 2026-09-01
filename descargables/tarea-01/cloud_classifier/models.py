"""
Modelos de datos del clasificador.

Se usan dataclasses en lugar de diccionarios sueltos para que el tipo de
dato que viaja entre las capas (NLP -> clasificador -> GUI/CLI) sea
explicito y autodocumentado.
"""

from dataclasses import dataclass, field
from typing import Dict, List

# Constantes de los modelos de servicio soportados.
IAAS = "IaaS"
PAAS = "PaaS"
SAAS = "SaaS"
FAAS = "FaaS"
NO_DETERMINADO = "No determinado"

MODELOS = (IAAS, PAAS, SAAS, FAAS)


@dataclass(frozen=True)
class TextoProcesado:
    """
    Resultado de pasar un texto por el pipeline de NLP (ver nlp.py).

    Guarda DOS representaciones del mismo texto porque cada una sirve a un
    proposito distinto dentro del clasificador:

    - ``tokens``: bolsa de palabras ya limpia, sin stopwords y con stemming.
      Se usa para el diccionario de conceptos (coincidencia de una sola
      palabra contra cada categoria).

    - ``texto_para_patrones``: el texto completo en minusculas, sin acentos
      y sin puntuacion, PERO sin tokenizar y SIN quitar stopwords. Lo usan
      las expresiones regulares de contexto, que necesitan el orden original
      de las palabras para detectar frases como "sin administrar servidores"
      (si hubieramos quitado "sin" por ser stopword, perderiamos justo la
      senal que buscamos).
    """

    texto_original: str
    texto_para_patrones: str
    tokens: List[str]


@dataclass
class ResultadoClasificacion:
    """Resultado final: modelo ganador, puntajes y evidencia encontrada."""

    modelo: str = NO_DETERMINADO
    confianza: float = 0.0
    empate: bool = False
    puntajes: Dict[str, int] = field(default_factory=dict)
    coincidencias: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def total_puntos(self) -> int:
        """Suma de todos los puntajes; se usa para calcular porcentajes."""
        return sum(self.puntajes.values())

    def porcentaje(self, modelo: str) -> int:
        """Porcentaje (0-100) que representa un modelo sobre el total."""
        total = self.total_puntos
        if total == 0:
            return 0
        return round(self.puntajes.get(modelo, 0) * 100 / total)

    @property
    def es_concluyente(self) -> bool:
        return self.modelo != NO_DETERMINADO
