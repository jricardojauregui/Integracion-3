"""
Libro mayor (ledger) de cuentas y movimientos.

Concentra las correcciones de correctitud transaccional:
  [F-5] atomicidad
  [F-6] idempotencia
  [F-7] concurrencia
  [F-10] autorizacion a nivel de recurso

En produccion esto seria PostgreSQL y las garantias vendrian del motor
(``BEGIN ... COMMIT``, ``SELECT ... FOR UPDATE``, restriccion UNIQUE sobre
la clave de idempotencia). Aqui se implementan en memoria de forma
equivalente para que el prototipo sea ejecutable, y cada punto indica cual
seria su contraparte en SQL.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from .core_client import AdaptadorCoreBancario, CoreNoDisponible
from .domain import (Cuenta, CuentaNoEncontrada, EstadoMovimiento, Movimiento,
                     NoAutorizado, SaldoInsuficiente)

log = logging.getLogger("banca.ledger")


class Ledger:
    def __init__(self, adaptador_core: AdaptadorCoreBancario):
        self.adaptador_core = adaptador_core
        self.cuentas: Dict[str, Cuenta] = {}
        self.movimientos: Dict[str, Movimiento] = {}

        # CORRIGE [F-6]: indice de claves de idempotencia -> id de movimiento.
        # En SQL: UNIQUE (usuario, clave_idempotencia).
        self._idempotencia: Dict[str, str] = {}

        # CORRIGE [F-7]: un lock por cuenta. Equivale a SELECT ... FOR UPDATE.
        # v1 leia el saldo y lo escribia despues sin proteccion, asi que dos
        # transferencias simultaneas desde la misma cuenta podian ambas ver
        # saldo suficiente y dejar la cuenta en negativo (lost update).
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    # ------------------------------------------------------------------
    def alta_cuenta(self, numero: str, titular: str, saldo_centavos: int) -> Cuenta:
        cuenta = Cuenta(numero=numero, titular=titular, saldo_centavos=saldo_centavos)
        self.cuentas[numero] = cuenta
        return cuenta

    def obtener_cuenta(self, numero: str, usuario: str) -> Cuenta:
        """
        CORRIGE [F-10] (IDOR). v1 devolvia cualquier cuenta a cualquier
        usuario autenticado. Aqui la autorizacion se verifica en la capa de
        datos, no solo en el endpoint: aunque un router nuevo olvide
        revisarlo, la propiedad se sigue comprobando aqui.

        Se lanza el mismo error para "no existe" y "no es tuya", para no
        permitir enumerar numeros de cuenta validos.
        """
        cuenta = self.cuentas.get(numero)
        if cuenta is None:
            raise CuentaNoEncontrada()
        if cuenta.titular != usuario:
            raise NoAutorizado()
        return cuenta

    def movimientos_de(self, usuario: str, limite: int = 50) -> List[Movimiento]:
        """CORRIGE [F-10]: v1 devolvia los movimientos de todos los usuarios."""
        propias = {c.numero for c in self.cuentas.values() if c.titular == usuario}
        movimientos = [
            m for m in self.movimientos.values()
            if m.cuenta_origen in propias or m.cuenta_destino in propias
        ]
        movimientos.sort(key=lambda m: m.creado_en, reverse=True)
        return movimientos[:limite]

    # ------------------------------------------------------------------
    async def transferir(self,
                         usuario: str,
                         origen: str,
                         destino: str,
                         monto_centavos: int,
                         concepto: str,
                         clave_idempotencia: str,
                         correlation_id: str) -> Movimiento:
        """
        Ejecuta una transferencia de forma atomica, idempotente y segura
        ante concurrencia.

        Orden de los pasos (importa mucho):
          1. Idempotencia: si la clave ya se uso, devolver el MISMO resultado.
          2. Autorizacion y validacion.
          3. Bloqueo ordenado de ambas cuentas.
          4. Registrar el movimiento como PENDIENTE y mover el saldo.
          5. Confirmar contra el core on-premises.
          6. Marcar APLICADO, o dejar PENDIENTE para reconciliacion.
        """

        # --- 1. Idempotencia [F-6] -------------------------------------
        # v1 no tenia esto: si el celular perdia la senal tras enviar la
        # peticion y el usuario reintentaba, la transferencia se ejecutaba
        # dos veces. Con red movil esto no es un caso raro, es lo normal.
        clave = f"{usuario}:{clave_idempotencia}"
        if clave in self._idempotencia:
            existente = self.movimientos[self._idempotencia[clave]]
            log.info("Reintento idempotente correlation_id=%s movimiento=%s",
                     correlation_id, existente.id)
            return existente

        # --- 2. Autorizacion y validacion ------------------------------
        cuenta_origen = self.obtener_cuenta(origen, usuario)  # valida propiedad
        cuenta_destino = self.cuentas.get(destino)
        if cuenta_destino is None:
            raise CuentaNoEncontrada()
        if origen == destino:
            raise NoAutorizado()

        # --- 3. Bloqueo ordenado [F-7] ---------------------------------
        # Los locks se toman SIEMPRE en orden alfabetico de numero de cuenta.
        # Si no se ordenaran, dos transferencias cruzadas (A->B y B->A
        # simultaneas) podrian tomar los locks en orden inverso y quedar en
        # deadlock. Ordenar los recursos es la forma estandar de evitarlo.
        primero, segundo = sorted([origen, destino])

        async with self._locks[primero], self._locks[segundo]:
            # Se re-verifica dentro del lock: entre el chequeo previo y este
            # punto pudo cambiar el saldo (check-then-act).
            if cuenta_origen.saldo_centavos < monto_centavos:
                raise SaldoInsuficiente()

            # --- 4. Persistir PENDIENTE y mover saldo [F-5] ------------
            movimiento = Movimiento(
                id=str(uuid.uuid4()),
                cuenta_origen=origen,
                cuenta_destino=destino,
                monto_centavos=monto_centavos,
                concepto=concepto[:140],
                estado=EstadoMovimiento.PENDIENTE,
                clave_idempotencia=clave_idempotencia,
                correlation_id=correlation_id,
            )
            self.movimientos[movimiento.id] = movimiento
            self._idempotencia[clave] = movimiento.id

            # Ambos lados se afectan bajo el mismo lock: nunca existe un
            # instante observable en que el dinero no este ni en una cuenta
            # ni en la otra. En SQL esto seria una sola transaccion.
            cuenta_origen.saldo_centavos -= monto_centavos
            cuenta_destino.saldo_centavos += monto_centavos
            cuenta_origen.version += 1
            cuenta_destino.version += 1

        # --- 5. Confirmar con el core (fuera del lock) -----------------
        # Se sale del lock a proposito: la llamada al core puede tardar
        # cientos de milisegundos y mantener bloqueada la cuenta todo ese
        # tiempo serializaria las operaciones y destruiria el rendimiento.
        try:
            respuesta = await self.adaptador_core.registrar_asiento({
                "id": movimiento.id,
                "origen": origen,
                "destino": destino,
                "monto_centavos": monto_centavos,
                "correlation_id": correlation_id,
            })
            movimiento.referencia_core = respuesta.get("referencia")
            movimiento.estado = EstadoMovimiento.APLICADO

        except CoreNoDisponible:
            # NO se revierte el saldo automaticamente ni se pierde el
            # registro: el movimiento queda PENDIENTE y persistido. Un
            # proceso de reconciliacion (ver DOCUMENTACION, seccion DR)
            # consulta el core despues y decide confirmar o compensar.
            #
            # Esta es la diferencia clave con v1: alli un core caido dejaba
            # el dinero movido en la nube sin rastro en el core y sin forma
            # de detectarlo.
            log.error(
                "Core no disponible; movimiento %s queda PENDIENTE "
                "para reconciliacion. correlation_id=%s",
                movimiento.id, correlation_id,
            )

        return movimiento

    # ------------------------------------------------------------------
    async def reconciliar_pendientes(self) -> dict:
        """
        Proceso de reconciliacion (se ejecutaria como job periodico o
        funcion serverless disparada por calendario).

        Reintenta confirmar contra el core los movimientos que quedaron
        PENDIENTE. Es idempotente: reenvia el mismo id de movimiento, asi
        que si el core ya lo habia asentado, responde con la misma
        referencia en vez de duplicarlo.
        """
        resumen = {"revisados": 0, "confirmados": 0, "siguen_pendientes": 0}

        for movimiento in list(self.movimientos.values()):
            if movimiento.estado != EstadoMovimiento.PENDIENTE:
                continue
            resumen["revisados"] += 1
            try:
                respuesta = await self.adaptador_core.registrar_asiento({
                    "id": movimiento.id,
                    "origen": movimiento.cuenta_origen,
                    "destino": movimiento.cuenta_destino,
                    "monto_centavos": movimiento.monto_centavos,
                    "correlation_id": movimiento.correlation_id,
                    "reconciliacion": True,
                })
                movimiento.referencia_core = respuesta.get("referencia")
                movimiento.estado = EstadoMovimiento.APLICADO
                resumen["confirmados"] += 1
            except CoreNoDisponible:
                resumen["siguen_pendientes"] += 1

        return resumen
