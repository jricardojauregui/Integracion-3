"""
Pipeline de Procesamiento de Lenguaje Natural (NLP) basico.

Cada paso del pipeline es una funcion independiente y pura (misma entrada
-> misma salida, sin efectos secundarios), lo que permite probarlas por
separado. ``procesar()`` las encadena en orden:

    1. a_minusculas       - conversion a minusculas
    2. limpiar            - limpieza de texto (quita puntuacion/simbolos)
    3. tokenizar          - tokenizacion (separa en palabras)
    4. quitar_stopwords   - eliminacion de stopwords
    5. normalizar_tokens  - normalizacion (quita acentos)
    6. aplicar_stemming   - stemming ligero (agrupa variantes de una raiz)

La identificacion de conceptos relevantes y la asignacion de puntuaciones
se hacen despues, en classifier.py, usando la salida de este pipeline.

No se usan librerias externas (NLTK/spaCy) a proposito: el ejercicio pide
NLP *basico* y de esta forma el proyecto corre con Python estandar, sin
instalar dependencias ni descargar corpus.
"""

import re
import unicodedata
from typing import List

from .models import TextoProcesado

# ---------------------------------------------------------------------------
# Lista de stopwords en espanol.
#
# DECISION DE DISENO IMPORTANTE: esta lista NO incluye palabras de negacion
# ("sin", "no", "ni") ni las que forman disparadores ("cada", "vez", "que").
# Si las quitaramos, perderiamos justo la senal que el clasificador necesita
# para reglas de contexto como "sin administrar servidores" (PaaS) o
# "cada vez que" (FaaS). Ademas, por esa misma razon, esas reglas se evaluan
# sobre el texto COMPLETO y no sobre la bolsa de tokens (ver TextoProcesado).
# ---------------------------------------------------------------------------
STOPWORDS = frozenset({
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "y", "o", "u", "que", "en", "con", "para", "por", "a", "se", "su", "sus",
    "es", "son", "como", "lo", "le", "les", "mi", "mis", "tu", "tus", "este",
    "esta", "estos", "estas", "ese", "esa", "esos", "esas", "muy", "mas",
    "pero", "porque", "cuando", "donde", "tambien", "ya", "solo", "segun",
    "the", "of", "in",
})

# Sufijos ordenados del mas largo al mas corto: se recorta SOLO el primero
# que coincida, para evitar recortar de mas ("over-stemming").
_SUFIJOS = ("amente", "aciones", "iciones", "ando", "iendo", "ciones",
            "mente", "es", "s")

# Conserva letras, digitos y espacios. Los digitos se conservan a proposito
# para no romper terminos del dominio como "k8s", "ec2" u "office 365".
_RE_LIMPIEZA = re.compile(r"[^\w\s]", flags=re.UNICODE)
_RE_ESPACIOS = re.compile(r"\s+")


# --- 1. Conversion a minusculas -------------------------------------------
def a_minusculas(texto: str) -> str:
    return texto.lower() if texto else ""


# --- 2. Limpieza de texto --------------------------------------------------
def limpiar(texto: str) -> str:
    """Reemplaza puntuacion/simbolos por espacios y colapsa espacios repetidos."""
    if not texto:
        return ""
    limpio = _RE_LIMPIEZA.sub(" ", texto)
    limpio = limpio.replace("_", " ")  # \w incluye "_", aqui no lo queremos
    return _RE_ESPACIOS.sub(" ", limpio).strip()


# --- 3. Tokenizacion -------------------------------------------------------
def tokenizar(texto_limpio: str) -> List[str]:
    if not texto_limpio:
        return []
    return [t for t in texto_limpio.split(" ") if t]


# --- 4. Eliminacion de stopwords -------------------------------------------
def quitar_stopwords(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in STOPWORDS]


# --- 5. Normalizacion (quita acentos) --------------------------------------
def normalizar(texto: str) -> str:
    """'máquina' -> 'maquina'. Descompone en NFD y descarta los diacriticos."""
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalizar_tokens(tokens: List[str]) -> List[str]:
    return [normalizar(t) for t in tokens]


# --- 6. Stemming -----------------------------------------------------------
def stem(token: str) -> str:
    """
    Stemmer heuristico para espanol: recorta un solo sufijo comun.

    No es linguisticamente perfecto (eso requeriria Snowball/NLTK), pero
    basta para agrupar plurales/singulares del vocabulario de este dominio:
    'funciones' -> 'funcion', 'contenedores' -> 'contenedor'.

    Se exige una raiz minima de 4 caracteres para no destruir palabras
    cortas (ej. 'redes' -> 'rede', no ''), y no se toca nada de 4 letras
    o menos.
    """
    if not token or len(token) <= 4:
        return token
    for sufijo in _SUFIJOS:
        if token.endswith(sufijo) and len(token) - len(sufijo) >= 4:
            return token[: -len(sufijo)]
    return token


def aplicar_stemming(tokens: List[str]) -> List[str]:
    return [stem(t) for t in tokens]


# --- Pipeline completo -----------------------------------------------------
def procesar(texto_original: str) -> TextoProcesado:
    """Ejecuta los 6 pasos y devuelve ambas representaciones del texto."""
    minusculas = a_minusculas(texto_original)          # 1
    limpio = limpiar(minusculas)                        # 2
    tokens = tokenizar(limpio)                          # 3
    sin_stopwords = quitar_stopwords(tokens)            # 4
    normalizados = normalizar_tokens(sin_stopwords)     # 5
    stems = aplicar_stemming(normalizados)              # 6

    # Texto completo (minusculas + limpio + sin acentos) SIN tokenizar ni
    # quitar stopwords: lo usan los patrones de contexto (regex).
    texto_para_patrones = normalizar(limpio)

    return TextoProcesado(
        texto_original=texto_original,
        texto_para_patrones=texto_para_patrones,
        tokens=stems,
    )


def describir_pipeline(texto_original: str) -> List[tuple]:
    """
    Devuelve el resultado de cada paso, en orden, como (nombre, valor).

    Es una funcion de apoyo para documentacion/depuracion: permite mostrar
    en la GUI o en la CLI (--explicar) como se va transformando el texto.
    """
    minusculas = a_minusculas(texto_original)
    limpio = limpiar(minusculas)
    tokens = tokenizar(limpio)
    sin_stopwords = quitar_stopwords(tokens)
    normalizados = normalizar_tokens(sin_stopwords)
    stems = aplicar_stemming(normalizados)

    return [
        ("0. Original", texto_original),
        ("1. Minusculas", minusculas),
        ("2. Limpieza", limpio),
        ("3. Tokenizacion", tokens),
        ("4. Sin stopwords", sin_stopwords),
        ("5. Normalizacion", normalizados),
        ("6. Stemming", stems),
    ]
