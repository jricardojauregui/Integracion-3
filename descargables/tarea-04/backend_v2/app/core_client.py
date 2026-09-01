"""
Adaptador hacia el core bancario on-premises.

CORRIGE [F-8], que era el problema mas grave de arquitectura en v1:
una llamada sincrona sin timeout al core. En una nube hibrida el enlace
hacia el datacenter es el componente mas lento y menos elastico de todo
el sistema; si la API depende de el sin proteccion, un core degradado
consume todos los workers de la API y provoca una caida total.

Tres defensas, en capas:

  1. TIMEOUT       nunca esperar indefinidamente.
  2. REINTENTOS    con backoff exponencial + jitter, solo en fallos
                   transitorios y solo en operaciones idempotentes.
  3. CIRCUIT BREAKER  tras N fallos consecutivos se deja de llamar al core
                   durante un periodo: se falla rapido y se libera capacidad
                   en vez de acumular peticiones colgadas.

El jitter (aleatoriedad en la espera) evita el "thundering herd": sin el,
todas las instancias reintentan exactamente al mismo tiempo y vuelven a
tumbar el core justo cuando se estaba recuperando.
"""

import asyncio
import logging
import random
import time
from enum import Enum
from typing import Optional, Protocol

log = logging.getLogger("banca.core")


class EstadoCircuito(str, Enum):
    CERRADO = "cerrado"        # operacion normal
    ABIERTO = "abierto"        # el core esta caido: se falla rapido
    SEMIABIERTO = "semiabierto"  # se deja pasar una prueba para ver si volvio


class CoreNoDisponible(Exception):
    """El core on-premises no respondio. La operacion queda PENDIENTE."""


class ClienteCore(Protocol):
    """
    Contrato del transporte hacia el core.

    Se define como Protocol para poder inyectar un doble de prueba sin
    levantar el core real: es lo que permite probar el circuit breaker y
    los reintentos de forma determinista en la suite de tests.
    """

    async def registrar_asiento(self, payload: dict) -> dict: ...


class CircuitBreaker:
    def __init__(self, umbral_fallos: int = 5, espera_s: float = 30.0):
        self.umbral_fallos = umbral_fallos
        self.espera_s = espera_s
        self.fallos = 0
        self.estado = EstadoCircuito.CERRADO
        self._abierto_desde: Optional[float] = None

    def permite_llamada(self) -> bool:
        if self.estado == EstadoCircuito.CERRADO:
            return True

        if self.estado == EstadoCircuito.ABIERTO:
            transcurrido = time.monotonic() - (self._abierto_desde or 0)
            if transcurrido >= self.espera_s:
                # Se pasa a semiabierto: se permite UNA llamada de sondeo.
                self.estado = EstadoCircuito.SEMIABIERTO
                return True
            return False

        return True  # SEMIABIERTO: se deja pasar la prueba

    def registrar_exito(self) -> None:
        self.fallos = 0
        self.estado = EstadoCircuito.CERRADO
        self._abierto_desde = None

    def registrar_fallo(self) -> None:
        self.fallos += 1
        if self.fallos >= self.umbral_fallos:
            if self.estado != EstadoCircuito.ABIERTO:
                log.warning(
                    "Circuito ABIERTO hacia el core tras %d fallos consecutivos",
                    self.fallos,
                )
            self.estado = EstadoCircuito.ABIERTO
            self._abierto_desde = time.monotonic()


class AdaptadorCoreBancario:
    """Envuelve al cliente del core con las tres defensas."""

    def __init__(self,
                 cliente: ClienteCore,
                 reintentos: int = 3,
                 timeout_s: float = 2.0,
                 umbral_fallos: int = 5,
                 espera_circuito_s: float = 30.0,
                 dormir=asyncio.sleep):
        self.cliente = cliente
        self.reintentos = reintentos
        self.timeout_s = timeout_s
        self.breaker = CircuitBreaker(umbral_fallos, espera_circuito_s)
        # Se inyecta para que las pruebas no tengan que esperar de verdad.
        self._dormir = dormir

    async def registrar_asiento(self, payload: dict) -> dict:
        if not self.breaker.permite_llamada():
            # Fallo rapido: no se consume un worker esperando a un core caido.
            raise CoreNoDisponible(
                "El core bancario no esta disponible (circuito abierto)."
            )

        ultimo_error: Optional[Exception] = None

        for intento in range(1, self.reintentos + 1):
            try:
                resultado = await asyncio.wait_for(
                    self.cliente.registrar_asiento(payload),
                    timeout=self.timeout_s,
                )
                self.breaker.registrar_exito()
                return resultado

            except (asyncio.TimeoutError, ConnectionError, OSError) as error:
                ultimo_error = error
                self.breaker.registrar_fallo()
                log.warning(
                    "Fallo al contactar el core (intento %d/%d): %s",
                    intento, self.reintentos, type(error).__name__,
                )

                if intento < self.reintentos and self.breaker.permite_llamada():
                    # Backoff exponencial con jitter completo.
                    base = 0.1 * (2 ** (intento - 1))
                    await self._dormir(random.uniform(0, base))
                else:
                    break

        raise CoreNoDisponible(
            f"El core bancario no respondio tras {self.reintentos} intentos."
        ) from ultimo_error


class ClienteCoreSimulado:
    """
    Doble del core on-premises para el prototipo y las pruebas.

    Permite simular latencia, fallos intermitentes y caidas totales, que es
    justamente lo que hay que poder reproducir para validar que la
    arquitectura hibrida tolera un core degradado.
    """

    def __init__(self, latencia_s: float = 0.01, fallar_siempre: bool = False,
                 fallar_n_veces: int = 0):
        self.latencia_s = latencia_s
        self.fallar_siempre = fallar_siempre
        self.fallar_n_veces = fallar_n_veces
        self.llamadas = 0

    async def registrar_asiento(self, payload: dict) -> dict:
        self.llamadas += 1

        if self.fallar_siempre:
            raise ConnectionError("core caido (simulado)")
        if self.fallar_n_veces > 0:
            self.fallar_n_veces -= 1
            raise ConnectionError("fallo transitorio (simulado)")

        await asyncio.sleep(self.latencia_s)
        return {
            "referencia": f"CORE-{payload.get('id', 'x')}",
            "estatus": "asentado",
        }
