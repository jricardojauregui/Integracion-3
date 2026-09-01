"""
Motor de clasificacion: COMO se busca la evidencia y como se puntua.

Capa de logica pura: no importa tkinter ni argparse. Tanto la GUI como la
CLI llaman a ``clasificar()``, por lo que no hay ni una sola regla
duplicada entre ambas interfaces.

Flujo:
    texto -> nlp.procesar() -> [identificar_iaas | identificar_paas |
                                identificar_saas | identificar_faas]
          -> comparacion de puntajes -> ResultadoClasificacion
"""

from typing import List, Tuple

from . import knowledge, nlp
from .exceptions import ClasificacionError
from .models import (FAAS, IAAS, MODELOS, NO_DETERMINADO, PAAS, SAAS,
                     ResultadoClasificacion, TextoProcesado)


def _identificar(texto: TextoProcesado, categoria: str) -> Tuple[int, List[str]]:
    """
    Logica comun de identificacion para una categoria.

    Suma dos fuentes de evidencia:
      A) conceptos: palabras sueltas contra la bolsa de tokens (NLP)
      B) patrones: regex de contexto sobre el texto completo
    Devuelve (puntaje, lista de etiquetas encontradas).
    """
    puntaje = 0
    encontradas: List[str] = []

    # A) Identificacion de palabras / conceptos relevantes.
    # Se usa un set para que buscar cada concepto sea O(1) en vez de recorrer
    # la lista de tokens una vez por concepto.
    tokens_presentes = set(texto.tokens)
    for raiz, (peso, etiqueta) in knowledge.CONCEPTOS.get(categoria, {}).items():
        if raiz in tokens_presentes:
            puntaje += peso
            encontradas.append(etiqueta)

    # B) Patrones de contexto (frases, marcas, siglas, negaciones).
    for patron, peso, etiqueta in knowledge.PATRONES.get(categoria, []):
        if patron.search(texto.texto_para_patrones):
            puntaje += peso
            encontradas.append(etiqueta)

    return puntaje, encontradas


# ---------------------------------------------------------------------------
# Una funcion independiente por modelo de servicio.
# Se mantienen como funciones publicas separadas (aunque compartan
# ``_identificar``) para poder invocarlas y probarlas de forma aislada.
# ---------------------------------------------------------------------------

def identificar_iaas(texto: TextoProcesado) -> Tuple[int, List[str]]:
    """Evalua que tanto el texto corresponde a Infraestructura como Servicio."""
    return _identificar(texto, IAAS)


def identificar_paas(texto: TextoProcesado) -> Tuple[int, List[str]]:
    """Evalua que tanto el texto corresponde a Plataforma como Servicio."""
    return _identificar(texto, PAAS)


def identificar_saas(texto: TextoProcesado) -> Tuple[int, List[str]]:
    """Evalua que tanto el texto corresponde a Software como Servicio."""
    return _identificar(texto, SAAS)


def identificar_faas(texto: TextoProcesado) -> Tuple[int, List[str]]:
    """Evalua que tanto el texto corresponde a Funcion como Servicio."""
    return _identificar(texto, FAAS)


# Mapa categoria -> funcion identificadora. Permite recorrer las cuatro
# categorias sin encadenar ifs y facilita agregar una quinta en el futuro.
IDENTIFICADORES = {
    IAAS: identificar_iaas,
    PAAS: identificar_paas,
    SAAS: identificar_saas,
    FAAS: identificar_faas,
}


def clasificar(texto_original: str) -> ResultadoClasificacion:
    """
    Pasa el texto por el pipeline de NLP, evalua las cuatro categorias y
    determina cual predomina.

    :raises ClasificacionError: ante cualquier fallo inesperado del motor.
        La entrada vacia la filtra ``validation`` antes de llegar aqui; aun
        asi se maneja de forma defensiva por si se llama desde otro lugar.
    """
    try:
        procesado = nlp.procesar(texto_original or "")
        resultado = ResultadoClasificacion()

        for modelo in MODELOS:
            puntaje, encontradas = IDENTIFICADORES[modelo](procesado)
            resultado.puntajes[modelo] = puntaje
            resultado.coincidencias[modelo] = encontradas

        mejor_puntaje = max(resultado.puntajes.values())

        # Si nadie sumo puntos, el texto no es concluyente.
        if mejor_puntaje == 0:
            resultado.modelo = NO_DETERMINADO
            resultado.confianza = 0.0
            return resultado

        ganadores = [m for m in MODELOS if resultado.puntajes[m] == mejor_puntaje]

        resultado.modelo = ganadores[0]
        resultado.empate = len(ganadores) > 1
        resultado.confianza = mejor_puntaje / resultado.total_puntos
        return resultado

    except ClasificacionError:
        raise
    except Exception as error:  # noqa: BLE001 - se re-lanza como error de dominio
        # Se envuelve cualquier falla no prevista en una excepcion del dominio
        # para que la GUI/CLI no reciban un traceback crudo.
        raise ClasificacionError(
            f"Ocurrio un error inesperado al analizar el texto: {error}"
        ) from error


def descripcion_modelo(modelo: str) -> str:
    """Definicion corta del modelo, para mostrar en la GUI o la CLI."""
    return {
        IAAS: "Infraestructura como Servicio: computo, red y almacenamiento virtualizados.",
        PAAS: "Plataforma como Servicio: entorno gestionado para desarrollar y desplegar apps.",
        SAAS: "Software como Servicio: aplicaciones listas para el usuario final.",
        FAAS: "Funcion como Servicio: ejecucion por eventos, sin gestionar servidores.",
    }.get(modelo, "Agrega mas detalles tecnicos para obtener una clasificacion.")
