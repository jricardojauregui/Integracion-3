#!/usr/bin/env python3
"""
Interfaz de linea de comandos (CLI) del clasificador de modelos Cloud.

Usa argparse y REUTILIZA LA MISMA LOGICA que la GUI: ambas llaman a
``cloud_classifier.service.analizar``. Aqui no hay ni una regla de
clasificacion; este archivo solo se encarga de leer argumentos e imprimir.

Uso:
    python classifier.py --text "ejecutar una funcion cuando se suba una imagen"
    -> Modelo identificado: FaaS

Opciones extra:
    -v / --verbose   muestra confianza, puntajes y evidencia por categoria
    --explicar       muestra paso a paso el pipeline de NLP
    --json           imprime el resultado en formato JSON
"""

import argparse
import json
import sys

from cloud_classifier import ClasificacionError, EntradaInvalidaError, analizar
from cloud_classifier import classifier as motor
from cloud_classifier import nlp


def construir_parser() -> argparse.ArgumentParser:
    """Define los argumentos aceptados por la CLI."""
    parser = argparse.ArgumentParser(
        prog="classifier.py",
        description="Clasifica una descripcion de un servicio Cloud "
                    "como IaaS, PaaS, SaaS o FaaS.",
        epilog='Ejemplo: python classifier.py --text "ejecutar una funcion '
               'cuando se suba una imagen"',
    )
    parser.add_argument(
        "-t", "--text",
        required=True,
        help="Descripcion del servicio Cloud a clasificar (entre comillas).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Muestra confianza, puntajes y las palabras clave detectadas.",
    )
    parser.add_argument(
        "--explicar",
        action="store_true",
        help="Muestra paso a paso como el pipeline de NLP transforma el texto.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime el resultado en formato JSON (util para automatizar).",
    )
    return parser


def imprimir_pipeline(texto: str) -> None:
    """Muestra el resultado de cada paso del preprocesamiento NLP."""
    print("--- Pipeline de NLP ---")
    for etiqueta, valor in nlp.describir_pipeline(texto):
        print(f"{etiqueta:<20} {valor}")
    print()


def imprimir_detalle(resultado) -> None:
    """Muestra confianza, puntajes y evidencia por categoria."""
    print(f"Confianza: {resultado.confianza * 100:.0f}%")
    if resultado.empate:
        print("Atencion: hay empate entre modelos, el texto es ambiguo.")
    print(f"Puntajes: {resultado.puntajes}")
    print("Evidencia detectada:")
    for modelo, terminos in resultado.coincidencias.items():
        detalle = ", ".join(terminos) if terminos else "(sin coincidencias)"
        print(f"  {modelo}: {detalle}")


def main(argv=None) -> int:
    """Punto de entrada. Devuelve el codigo de salida del proceso."""
    args = construir_parser().parse_args(argv)

    try:
        # Misma funcion que usa la GUI. La CLI no envia nombre/apellido.
        analisis = analizar(descripcion=args.text)
        resultado = analisis.resultado

        if args.json:
            print(json.dumps({
                "texto": analisis.descripcion,
                "modelo": resultado.modelo,
                "confianza": round(resultado.confianza, 4),
                "empate": resultado.empate,
                "puntajes": resultado.puntajes,
                "coincidencias": resultado.coincidencias,
            }, ensure_ascii=False, indent=2))
            return 0

        if args.explicar:
            imprimir_pipeline(analisis.descripcion)

        print(f"Modelo identificado: {resultado.modelo}")

        if args.verbose:
            print(motor.descripcion_modelo(resultado.modelo))
            imprimir_detalle(resultado)

        return 0

    except EntradaInvalidaError as error:
        # Error del dato capturado: se informa y se sale con codigo != 0
        # para que un script que invoque esta CLI pueda detectarlo.
        print(f"Entrada invalida: {error}", file=sys.stderr)
        return 2

    except ClasificacionError as error:
        print(f"Error al clasificar: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
