#!/usr/bin/env python3
"""
Bateria de pruebas del clasificador.

Se escribio con ``unittest`` (biblioteca estandar) en vez de pytest para
que corra sin instalar dependencias:

    python -m unittest discover -s tests -v
    python tests/test_classifier.py          (equivalente)

Los casos de clasificacion EVITAN usar literalmente las siglas
IaaS/PaaS/SaaS/FaaS, tal como pide la practica: se describe el servicio en
lenguaje natural y se verifica el modelo detectado.
"""

import os
import subprocess
import sys
import unittest

# Permite ejecutar este archivo directamente (python tests/test_classifier.py)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from cloud_classifier import (FAAS, IAAS, NO_DETERMINADO, PAAS, SAAS,
                              ClasificacionError, EntradaInvalidaError,
                              analizar)
from cloud_classifier import classifier, nlp, validation


# ---------------------------------------------------------------------------
# Los 5+ casos documentados de la practica.
# (entrada, resultado esperado, descripcion corta)
# ---------------------------------------------------------------------------
CASOS = [
    ("Necesito máquinas virtuales, almacenamiento y redes configurables "
     "para instalar mi propio sistema operativo", IAAS,
     "Control total de infraestructura"),

    ("Quiero desplegar mi aplicación web sin administrar directamente "
     "servidores ni sistemas operativos", PAAS,
     "Despliegue con infraestructura abstraida"),

    ("Los empleados utilizan una aplicación de correo electrónico "
     "directamente desde el navegador y pagan una suscripción mensual", SAAS,
     "App lista para usuario final por suscripcion"),

    ("ejecutar una función cuando se suba una imagen", FAAS,
     "Ejecucion disparada por evento"),

    ("Necesito ejecutar una función automáticamente cada vez que un usuario "
     "suba una imagen al almacenamiento Cloud", FAAS,
     "Disparador explicito 'cada vez que'"),

    ("Necesitamos rentar servidores dedicados con acceso root para instalar "
     "nuestro propio hipervisor", IAAS,
     "Servidores dedicados / hipervisor"),

    ("Buscamos un entorno donde subir nuestro código y que la plataforma se "
     "encargue del runtime y el escalado automático", PAAS,
     "Plataforma gestiona runtime y escalado"),

    ("Quiero un espacio de trabajo colaborativo con hojas de cálculo y "
     "videollamadas, pagando una mensualidad por usuario", SAAS,
     "Suite colaborativa por suscripcion"),

    ("Todavía no sé qué necesito, quiero algo relacionado con la nube",
     NO_DETERMINADO,
     "Texto no concluyente"),
]


class PruebasClasificacion(unittest.TestCase):
    """Verifica que cada descripcion se clasifique en el modelo esperado."""

    def test_casos_documentados(self):
        for texto, esperado, etiqueta in CASOS:
            with self.subTest(caso=etiqueta):
                resultado = analizar(descripcion=texto).resultado
                self.assertEqual(
                    resultado.modelo, esperado,
                    f"\n  Texto:    {texto}"
                    f"\n  Esperado: {esperado}"
                    f"\n  Obtenido: {resultado.modelo}"
                    f"\n  Puntajes: {resultado.puntajes}",
                )

    def test_confianza_en_rango(self):
        """La confianza siempre debe estar entre 0 y 1."""
        for texto, _, etiqueta in CASOS:
            with self.subTest(caso=etiqueta):
                resultado = analizar(descripcion=texto).resultado
                self.assertGreaterEqual(resultado.confianza, 0.0)
                self.assertLessEqual(resultado.confianza, 1.0)

    def test_texto_sin_senales_no_es_concluyente(self):
        resultado = classifier.clasificar("hola que tal, buenos dias a todos")
        self.assertEqual(resultado.modelo, NO_DETERMINADO)
        self.assertFalse(resultado.es_concluyente)

    def test_identificadores_independientes(self):
        """Cada funcion identificar_* debe poder invocarse por separado."""
        procesado = nlp.procesar("maquinas virtuales con acceso root")
        puntaje_iaas, evidencia = classifier.identificar_iaas(procesado)
        puntaje_saas, _ = classifier.identificar_saas(procesado)

        self.assertGreater(puntaje_iaas, 0)
        self.assertGreater(len(evidencia), 0)
        self.assertEqual(puntaje_saas, 0)


class PruebasNLP(unittest.TestCase):
    """Verifica cada paso del pipeline de preprocesamiento por separado."""

    def test_a_minusculas(self):
        self.assertEqual(nlp.a_minusculas("MÁQUINA Virtual"), "máquina virtual")

    def test_limpieza_quita_puntuacion(self):
        self.assertEqual(nlp.limpiar("hola, mundo!"), "hola mundo")

    def test_limpieza_conserva_digitos(self):
        """No debe romper terminos del dominio como 'k8s' u 'office 365'."""
        self.assertEqual(nlp.limpiar("uso k8s y office 365."), "uso k8s y office 365")

    def test_tokenizar(self):
        self.assertEqual(nlp.tokenizar("una dos tres"), ["una", "dos", "tres"])

    def test_quitar_stopwords(self):
        tokens = ["la", "maquina", "es", "virtual"]
        self.assertEqual(nlp.quitar_stopwords(tokens), ["maquina", "virtual"])

    def test_stopwords_conserva_negaciones(self):
        """
        Regla critica: 'sin', 'no' y 'ni' NO son stopwords aqui, porque son
        justo la senal que distingue PaaS ('sin administrar servidores').
        """
        for palabra in ("sin", "no", "ni", "cada", "vez"):
            self.assertNotIn(palabra, nlp.STOPWORDS,
                             f"'{palabra}' no debe estar en STOPWORDS")

    def test_normalizacion_quita_acentos(self):
        self.assertEqual(nlp.normalizar("máquina"), "maquina")
        self.assertEqual(nlp.normalizar("función"), "funcion")

    def test_stemming_agrupa_variantes(self):
        self.assertEqual(nlp.stem("funciones"), nlp.stem("funcion"))
        self.assertEqual(nlp.stem("contenedores"), "contenedor")

    def test_stemming_no_destruye_palabras_cortas(self):
        self.assertEqual(nlp.stem("red"), "red")
        self.assertEqual(nlp.stem("vm"), "vm")

    def test_pipeline_completo(self):
        procesado = nlp.procesar("Las Máquinas Virtuales, con acceso root.")
        self.assertIn("maquina", procesado.tokens)
        self.assertNotIn("las", procesado.tokens)          # stopword eliminada
        self.assertNotIn(",", procesado.texto_para_patrones)  # limpieza aplicada
        self.assertEqual(procesado.texto_para_patrones,
                         "las maquinas virtuales con acceso root")

    def test_describir_pipeline_tiene_todos_los_pasos(self):
        pasos = nlp.describir_pipeline("Máquinas virtuales")
        self.assertEqual(len(pasos), 7)  # original + 6 pasos


class PruebasValidacion(unittest.TestCase):
    """Verifica que las entradas invalidas se rechacen con mensaje claro."""

    def test_nombre_vacio(self):
        with self.assertRaises(EntradaInvalidaError):
            validation.validar_nombre("", "Nombre")

    def test_nombre_con_numeros(self):
        with self.assertRaises(EntradaInvalidaError):
            validation.validar_nombre("Ricardo123", "Nombre")

    def test_nombre_valido_se_recorta(self):
        self.assertEqual(validation.validar_nombre("  Ricardo  "), "Ricardo")

    def test_nombre_con_acentos_es_valido(self):
        self.assertEqual(validation.validar_nombre("José"), "José")

    def test_nombre_compuesto_es_valido(self):
        self.assertEqual(validation.validar_nombre("Ana María"), "Ana María")

    def test_descripcion_vacia(self):
        with self.assertRaises(EntradaInvalidaError):
            validation.validar_descripcion("   ")

    def test_descripcion_muy_corta(self):
        with self.assertRaises(EntradaInvalidaError):
            validation.validar_descripcion("abc")

    def test_descripcion_muy_larga(self):
        with self.assertRaises(EntradaInvalidaError):
            validation.validar_descripcion("a" * 2001)

    def test_analizar_valida_nombre_cuando_se_envia(self):
        """La GUI si manda nombre/apellido: deben validarse."""
        with self.assertRaises(EntradaInvalidaError):
            analizar(descripcion="maquinas virtuales y redes",
                     nombre="", apellido="Jauregui")

    def test_analizar_sin_nombre_funciona(self):
        """La CLI no manda nombre/apellido: no debe exigirlos."""
        analisis = analizar(descripcion="maquinas virtuales y redes")
        self.assertIsNone(analisis.nombre_completo)
        self.assertEqual(analisis.resultado.modelo, IAAS)


class PruebasCLI(unittest.TestCase):
    """Verifica la CLI como proceso externo (integracion de punta a punta)."""

    def _ejecutar(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(RAIZ, "classifier.py"), *args],
            capture_output=True, text=True, encoding="utf-8",
        )

    def test_ejemplo_del_enunciado(self):
        proceso = self._ejecutar(
            "--text", "ejecutar una función cuando se suba una imagen")
        self.assertEqual(proceso.returncode, 0)
        self.assertIn("Modelo identificado: FaaS", proceso.stdout)

    def test_entrada_invalida_devuelve_codigo_2(self):
        proceso = self._ejecutar("--text", "abc")
        self.assertEqual(proceso.returncode, 2)
        self.assertIn("Entrada invalida", proceso.stderr)

    def test_falta_argumento_obligatorio(self):
        proceso = self._ejecutar()
        self.assertNotEqual(proceso.returncode, 0)

    def test_salida_json_es_parseable(self):
        import json
        proceso = self._ejecutar("--text", "maquinas virtuales y redes", "--json")
        self.assertEqual(proceso.returncode, 0)
        datos = json.loads(proceso.stdout)
        self.assertEqual(datos["modelo"], IAAS)


class PruebasErrores(unittest.TestCase):
    """Verifica el manejo de errores del motor."""

    def test_error_del_motor_se_envuelve(self):
        """
        Un fallo interno debe salir como ClasificacionError, no como una
        excepcion cruda, para que la GUI/CLI puedan manejarlo.
        """
        original = classifier.nlp.procesar
        try:
            def romper(_):
                raise RuntimeError("fallo simulado del pipeline")

            classifier.nlp.procesar = romper
            with self.assertRaises(ClasificacionError):
                classifier.clasificar("cualquier texto")
        finally:
            classifier.nlp.procesar = original

    def test_texto_vacio_no_truena_el_motor(self):
        """clasificar() debe ser defensivo aunque la validacion ya filtre esto."""
        resultado = classifier.clasificar("")
        self.assertEqual(resultado.modelo, NO_DETERMINADO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
