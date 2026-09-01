"""
Modelos de dominio.

CORRIGE [F-4]: el dinero se representa con ``Decimal`` y se opera en
centavos enteros, nunca con ``float``.

Por que importa: 0.1 + 0.2 en punto flotante da 0.30000000000000004. En un
sistema bancario ese error se acumula transaccion tras transaccion hasta
que el balance general no cuadra, y en auditoria un descuadre de centavos
es un hallazgo grave. Decimal con cuantizacion explicita a 2 decimales y
redondeo ROUND_HALF_UP (el criterio contable habitual) elimina el problema.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Optional

CENTAVOS = Decimal("0.01")


class ErrorNegocio(Exception):
    """Error esperado de negocio; se traduce a un HTTP 4xx especifico."""

    def __init__(self, mensaje: str, codigo: str = "error_negocio"):
        super().__init__(mensaje)
        self.codigo = codigo


class SaldoInsuficiente(ErrorNegocio):
    def __init__(self):
        super().__init__("Saldo insuficiente.", "saldo_insuficiente")


class CuentaNoEncontrada(ErrorNegocio):
    def __init__(self):
        super().__init__("Cuenta no encontrada.", "cuenta_no_encontrada")


class MontoInvalido(ErrorNegocio):
    def __init__(self, detalle: str):
        super().__init__(detalle, "monto_invalido")


class NoAutorizado(ErrorNegocio):
    def __init__(self):
        # Mensaje deliberadamente generico: no revelamos si la cuenta existe
        # o solo no es del usuario, para no filtrar informacion.
        super().__init__("Operacion no permitida.", "no_autorizado")


def a_decimal(valor) -> Decimal:
    """
    Convierte a Decimal validando estrictamente.

    CORRIGE [F-9]: rechaza negativos, cero, NaN, infinitos y valores con
    mas de dos decimales. Un monto negativo en v1 invertia el sentido de la
    transferencia, lo que equivale a permitir robo.
    """
    try:
        # Se convierte desde str para evitar heredar el error binario del float.
        monto = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise MontoInvalido("El monto no es un numero valido.")

    if not monto.is_finite():
        raise MontoInvalido("El monto no es un numero finito.")
    if monto <= 0:
        raise MontoInvalido("El monto debe ser mayor que cero.")
    if monto.as_tuple().exponent < -2:
        raise MontoInvalido("El monto no puede tener mas de dos decimales.")
    if monto > Decimal("1000000.00"):
        raise MontoInvalido("El monto excede el limite por operacion.")

    return monto.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


class EstadoMovimiento(str, Enum):
    """
    Estados del ciclo de vida de una transferencia.

    CORRIGE [F-5]: v1 movia el saldo y despues avisaba al core; si el core
    fallaba, los sistemas quedaban inconsistentes sin registro. Aqui el
    movimiento se persiste PRIMERO como PENDIENTE, y solo pasa a APLICADO
    cuando el core confirma. Si el core no responde, queda en PENDIENTE
    y un proceso de reconciliacion lo reintenta o lo compensa.
    """

    PENDIENTE = "pendiente"
    APLICADO = "aplicado"
    REVERSADO = "reversado"
    FALLIDO = "fallido"


@dataclass
class Cuenta:
    numero: str
    titular: str
    # Se guardan CENTAVOS como entero: aritmetica exacta, sin redondeo.
    saldo_centavos: int
    version: int = 0          # control de concurrencia optimista, ver [F-7]

    @property
    def saldo(self) -> Decimal:
        return (Decimal(self.saldo_centavos) / 100).quantize(CENTAVOS)


@dataclass
class Movimiento:
    id: str
    cuenta_origen: str
    cuenta_destino: str
    monto_centavos: int
    concepto: str
    estado: EstadoMovimiento
    clave_idempotencia: str
    correlation_id: str
    creado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    referencia_core: Optional[str] = None

    @property
    def monto(self) -> Decimal:
        return (Decimal(self.monto_centavos) / 100).quantize(CENTAVOS)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "origen": self.cuenta_origen,
            "destino": self.cuenta_destino,
            "monto": str(self.monto),
            "concepto": self.concepto,
            "estado": self.estado.value,
            "fecha": self.creado_en.isoformat(),
            "referencia_core": self.referencia_core,
        }
