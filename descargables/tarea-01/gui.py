#!/usr/bin/env python3
"""
Interfaz grafica (GUI) del clasificador de modelos Cloud, con Tkinter.

Se eligio Tkinter porque viene en la biblioteca estandar de Python: el
proyecto corre sin instalar dependencias externas. (CustomTkinter o PySide
darian un aspecto mas moderno, pero obligarian a un ``pip install``.)

IMPORTANTE: esta clase SOLO construye y actualiza widgets. No contiene
reglas de clasificacion ni de validacion; toda esa logica vive en el
paquete ``cloud_classifier`` y se invoca a traves de ``service.analizar``,
exactamente la misma funcion que usa la CLI.

Uso:
    python gui.py
"""

import tkinter as tk
from tkinter import messagebox, ttk

from cloud_classifier import (MODELOS, ClasificacionError, EntradaInvalidaError,
                              analizar)
from cloud_classifier import classifier as motor
from cloud_classifier.models import NO_DETERMINADO

# Paleta de colores de la interfaz
AZUL = "#1B3A8C"
AZUL_CLARO = "#398EF4"
FONDO = "#F4F6FB"
BLANCO = "#FFFFFF"
TEXTO = "#1F2430"
GRIS = "#6B7280"
NARANJA = "#B4531A"


class VentanaPrincipal(tk.Tk):
    """Ventana principal: formulario a la izquierda, resultados a la derecha."""

    def __init__(self):
        super().__init__()
        self.title("Cloud Models Classifier - IaaS / PaaS / SaaS / FaaS")
        self.geometry("980x680")
        self.minsize(880, 620)
        self.configure(bg=FONDO)

        # Widgets de resultado que se actualizan tras cada clasificacion.
        self._barras = {}
        self._etiquetas_barra = {}

        self._construir_encabezado()

        cuerpo = tk.Frame(self, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=12)
        cuerpo.columnconfigure(0, weight=1, uniform="col")
        cuerpo.columnconfigure(1, weight=1, uniform="col")
        cuerpo.rowconfigure(0, weight=1)

        self._construir_formulario(cuerpo)
        self._construir_resultados(cuerpo)

    # ------------------------------------------------------------------
    # CONSTRUCCION DE LA INTERFAZ
    # ------------------------------------------------------------------

    def _construir_encabezado(self):
        encabezado = tk.Frame(self, bg=AZUL)
        encabezado.pack(fill="x")

        tk.Label(
            encabezado,
            text="Clasificador de Modelos de Servicio en la Nube",
            bg=AZUL, fg=BLANCO,
            font=("Helvetica", 17, "bold"),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 0))

        tk.Label(
            encabezado,
            text="Version Python - NLP basico + reglas, GUI y CLI comparten la misma logica",
            bg=AZUL, fg="#C8D6F5",
            font=("Helvetica", 10),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(2, 14))

    def _construir_formulario(self, padre):
        marco = tk.LabelFrame(
            padre, text=" Datos del usuario y descripcion ",
            bg=BLANCO, fg=TEXTO, font=("Helvetica", 10, "bold"),
            bd=1, relief="solid", padx=14, pady=12,
        )
        marco.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(marco, text="Nombre", bg=BLANCO, fg=TEXTO,
                 font=("Helvetica", 10, "bold"), anchor="w").pack(fill="x")
        self.entrada_nombre = tk.Entry(marco, font=("Helvetica", 11),
                                       relief="solid", bd=1)
        self.entrada_nombre.pack(fill="x", ipady=4, pady=(2, 10))

        tk.Label(marco, text="Apellido", bg=BLANCO, fg=TEXTO,
                 font=("Helvetica", 10, "bold"), anchor="w").pack(fill="x")
        self.entrada_apellido = tk.Entry(marco, font=("Helvetica", 11),
                                         relief="solid", bd=1)
        self.entrada_apellido.pack(fill="x", ipady=4, pady=(2, 10))

        tk.Label(marco, text="Describe el servicio de Cloud Computing",
                 bg=BLANCO, fg=TEXTO, font=("Helvetica", 10, "bold"),
                 anchor="w").pack(fill="x")
        self.entrada_descripcion = tk.Text(marco, height=8, wrap="word",
                                           font=("Helvetica", 11),
                                           relief="solid", bd=1)
        self.entrada_descripcion.pack(fill="both", expand=True, pady=(2, 4))

        tk.Label(
            marco,
            text='Ejemplo: "Necesito maquinas virtuales con acceso root\ny almacenamiento en bloque"',
            bg=BLANCO, fg=GRIS, font=("Helvetica", 9, "italic"),
            justify="left", anchor="w",
        ).pack(fill="x", pady=(0, 10))

        botones = tk.Frame(marco, bg=BLANCO)
        botones.pack(fill="x")

        tk.Button(botones, text="Clasificar", command=self._al_clasificar,
                  bg=AZUL_CLARO, fg=BLANCO, font=("Helvetica", 11, "bold"),
                  relief="flat", cursor="hand2", padx=22, pady=7,
                  activebackground=AZUL, activeforeground=BLANCO
                  ).pack(side="left")

        tk.Button(botones, text="Limpiar", command=self._al_limpiar,
                  font=("Helvetica", 11), relief="solid", bd=1,
                  cursor="hand2", padx=18, pady=6
                  ).pack(side="left", padx=8)

    def _construir_resultados(self, padre):
        marco = tk.LabelFrame(
            padre, text=" Resultado de la clasificacion ",
            bg=BLANCO, fg=TEXTO, font=("Helvetica", 10, "bold"),
            bd=1, relief="solid", padx=14, pady=12,
        )
        marco.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.etiqueta_saludo = tk.Label(marco, text=" ", bg=BLANCO, fg=GRIS,
                                        font=("Helvetica", 10), anchor="w")
        self.etiqueta_saludo.pack(fill="x")

        self.etiqueta_modelo = tk.Label(marco, text="Esperando descripcion...",
                                        bg=BLANCO, fg=AZUL,
                                        font=("Helvetica", 28, "bold"), anchor="w")
        self.etiqueta_modelo.pack(fill="x", pady=(6, 0))

        self.etiqueta_definicion = tk.Label(
            marco, text=" ", bg=BLANCO, fg=TEXTO, font=("Helvetica", 10),
            anchor="w", justify="left", wraplength=400,
        )
        self.etiqueta_definicion.pack(fill="x")

        self.etiqueta_confianza = tk.Label(
            marco, text=" ", bg=BLANCO, fg=GRIS, font=("Helvetica", 10),
            anchor="w", justify="left", wraplength=400,
        )
        self.etiqueta_confianza.pack(fill="x", pady=(2, 12))

        # Una barra de progreso por cada modelo de servicio.
        for modelo in MODELOS:
            etiqueta = tk.Label(marco, text=f"{modelo}: 0% (0 pts)", bg=BLANCO,
                                fg=TEXTO, font=("Helvetica", 10), anchor="w")
            etiqueta.pack(fill="x")
            self._etiquetas_barra[modelo] = etiqueta

            barra = ttk.Progressbar(marco, maximum=100, value=0)
            barra.pack(fill="x", pady=(1, 7))
            self._barras[modelo] = barra

        tk.Label(marco, text="Palabras clave detectadas", bg=BLANCO, fg=TEXTO,
                 font=("Helvetica", 10, "bold"), anchor="w").pack(fill="x", pady=(6, 2))

        contenedor = tk.Frame(marco, bg=BLANCO)
        contenedor.pack(fill="both", expand=True)

        scroll = tk.Scrollbar(contenedor)
        scroll.pack(side="right", fill="y")

        self.texto_evidencia = tk.Text(
            contenedor, height=7, wrap="word", font=("Courier", 9),
            bg="#F9FAFC", relief="solid", bd=1, state="disabled",
            yscrollcommand=scroll.set,
        )
        self.texto_evidencia.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.texto_evidencia.yview)

    # ------------------------------------------------------------------
    # EVENTOS (orquestacion, no logica de negocio)
    # ------------------------------------------------------------------

    def _al_clasificar(self):
        """
        Pide al servicio que valide y clasifique; la GUI solo pinta el
        resultado o el mensaje de error. Aqui es donde se manejan las
        excepciones que vienen de la capa de logica.
        """
        try:
            analisis = analizar(
                descripcion=self.entrada_descripcion.get("1.0", "end"),
                nombre=self.entrada_nombre.get(),
                apellido=self.entrada_apellido.get(),
            )
            self._mostrar_resultado(analisis)

        except EntradaInvalidaError as error:
            # Dato del formulario incorrecto: el mensaje ya viene redactado.
            messagebox.showwarning("Datos incompletos", str(error))

        except ClasificacionError as error:
            # Fallo del motor: se informa sin cerrar la aplicacion.
            messagebox.showerror("Error al clasificar", str(error))

        except Exception:  # noqa: BLE001 - ultima red de seguridad
            messagebox.showerror(
                "Error",
                "Ocurrio un error inesperado. Intenta de nuevo.",
            )

    def _mostrar_resultado(self, analisis):
        """Pinta en pantalla un resultado ya calculado por la capa de logica."""
        resultado = analisis.resultado

        self.etiqueta_saludo.config(text=f"Analisis para: {analisis.nombre_completo}")
        self.etiqueta_modelo.config(text=resultado.modelo)
        self.etiqueta_definicion.config(text=motor.descripcion_modelo(resultado.modelo))

        if resultado.modelo == NO_DETERMINADO:
            self.etiqueta_modelo.config(fg=NARANJA)
            self.etiqueta_confianza.config(
                text="No se encontraron terminos suficientes para clasificar el texto."
            )
        else:
            self.etiqueta_modelo.config(fg=AZUL)
            mensaje = f"Confianza: {resultado.confianza * 100:.0f}%"
            if resultado.empate:
                mensaje += "  |  Atencion: hay empate entre modelos, el texto es ambiguo."
            self.etiqueta_confianza.config(text=mensaje)

        for modelo in MODELOS:
            porcentaje = resultado.porcentaje(modelo)
            puntos = resultado.puntajes.get(modelo, 0)
            self._barras[modelo]["value"] = porcentaje
            self._etiquetas_barra[modelo].config(
                text=f"{modelo}: {porcentaje}% ({puntos} pts)",
                fg=AZUL if modelo == resultado.modelo else TEXTO,
                font=("Helvetica", 10, "bold" if modelo == resultado.modelo else "normal"),
            )

        lineas = []
        for modelo, terminos in resultado.coincidencias.items():
            detalle = ", ".join(terminos) if terminos else "(sin coincidencias)"
            lineas.append(f"{modelo} -> {detalle}")

        self.texto_evidencia.config(state="normal")
        self.texto_evidencia.delete("1.0", "end")
        self.texto_evidencia.insert("1.0", "\n\n".join(lineas))
        self.texto_evidencia.config(state="disabled")

    def _al_limpiar(self):
        """Restablece el formulario y el panel de resultados."""
        self.entrada_nombre.delete(0, "end")
        self.entrada_apellido.delete(0, "end")
        self.entrada_descripcion.delete("1.0", "end")

        self.etiqueta_saludo.config(text=" ")
        self.etiqueta_modelo.config(text="Esperando descripcion...", fg=AZUL)
        self.etiqueta_definicion.config(text=" ")
        self.etiqueta_confianza.config(text=" ")

        for modelo in MODELOS:
            self._barras[modelo]["value"] = 0
            self._etiquetas_barra[modelo].config(
                text=f"{modelo}: 0% (0 pts)", fg=TEXTO,
                font=("Helvetica", 10, "normal"),
            )

        self.texto_evidencia.config(state="normal")
        self.texto_evidencia.delete("1.0", "end")
        self.texto_evidencia.config(state="disabled")

        self.entrada_nombre.focus_set()


def main():
    VentanaPrincipal().mainloop()


if __name__ == "__main__":
    main()
