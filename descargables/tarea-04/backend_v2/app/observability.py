"""
Observabilidad: logs estructurados, correlacion y metricas.

CORRIGE [F-12] (datos sensibles en logs) y [F-13] (sin trazabilidad).

Los tres pilares y como se cubren aqui:

  LOGS     JSON estructurado con correlation_id, sin PII ni secretos.
  METRICAS contadores y latencias en formato Prometheus.
  TRAZAS   se propaga el correlation_id; en produccion se sustituye por
           OpenTelemetry, que ademas mide cada salto (movil -> gateway ->
           API -> core on-prem) y permite ver donde se va el tiempo.

Por que el correlation_id es imprescindible en hibrido: una transferencia
atraviesa la app movil, el API Gateway, varias instancias de la API, el
enlace privado y el core del datacenter. Sin un identificador comun, un
incidente obliga a correlacionar a mano registros de cuatro sistemas con
relojes distintos. Es el primer dato que pide un auditor cuando un cliente
reclama un cargo.
"""

import json
import logging
import time
import uuid
from collections import defaultdict
from contextvars import ContextVar
from typing import Dict, List

# ContextVar: cada peticion concurrente conserva su propio valor sin que
# se mezclen entre corrutinas.
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")
usuario_ctx: ContextVar[str] = ContextVar("usuario", default="-")


# Campos que NUNCA deben aparecer en un log. La redaccion es por lista de
# denegacion explicita y se aplica de forma centralizada, para no depender
# de que cada desarrollador se acuerde en cada llamada.
CAMPOS_PROHIBIDOS = {
    "password", "contrasena", "token", "authorization", "jwt",
    "pan", "tarjeta", "cvv", "nip", "curp", "rfc", "secret",
}


def redactar(datos: dict) -> dict:
    """Sustituye por '[REDACTADO]' cualquier campo sensible, recursivamente."""
    limpio = {}
    for clave, valor in datos.items():
        if clave.lower() in CAMPOS_PROHIBIDOS:
            limpio[clave] = "[REDACTADO]"
        elif isinstance(valor, dict):
            limpio[clave] = redactar(valor)
        else:
            limpio[clave] = valor
    return limpio


class FormateadorJSON(logging.Formatter):
    """
    Emite cada linea como JSON. Los logs se ingieren en CloudWatch/ELK y
    se consultan por campo; en texto libre habria que parsear con regex.
    """

    def format(self, record: logging.LogRecord) -> str:
        entrada = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "usuario": usuario_ctx.get(),
        }
        if hasattr(record, "extra_datos"):
            entrada.update(redactar(record.extra_datos))
        if record.exc_info:
            entrada["excepcion"] = self.formatException(record.exc_info)
        return json.dumps(entrada, ensure_ascii=False)


def configurar_logging(nivel: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(FormateadorJSON())
    raiz = logging.getLogger()
    raiz.handlers.clear()
    raiz.addHandler(handler)
    raiz.setLevel(nivel)


def nuevo_correlation_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Metricas
# ---------------------------------------------------------------------------
class Metricas:
    """
    Registro minimo compatible con el formato de exposicion de Prometheus.

    Se miden las cuatro senales doradas (Google SRE): latencia, trafico,
    errores y saturacion. Las alertas se definen sobre SLOs, no sobre
    umbrales de CPU: al usuario no le importa la CPU, le importa si su
    transferencia pasa y en cuanto tiempo.
    """

    def __init__(self):
        self.contadores: Dict[str, int] = defaultdict(int)
        self.latencias: Dict[str, List[float]] = defaultdict(list)

    def incrementar(self, nombre: str, valor: int = 1, **etiquetas) -> None:
        self.contadores[self._clave(nombre, etiquetas)] += valor

    def observar_latencia(self, nombre: str, segundos: float, **etiquetas) -> None:
        self.latencias[self._clave(nombre, etiquetas)].append(segundos)

    @staticmethod
    def _clave(nombre: str, etiquetas: dict) -> str:
        if not etiquetas:
            return nombre
        partes = ",".join(f'{k}="{v}"' for k, v in sorted(etiquetas.items()))
        return f"{nombre}{{{partes}}}"

    def percentil(self, clave: str, p: float) -> float:
        valores = sorted(self.latencias.get(clave, []))
        if not valores:
            return 0.0
        indice = min(int(len(valores) * p), len(valores) - 1)
        return valores[indice]

    def exponer(self) -> str:
        """Salida en texto plano para el endpoint /metrics."""
        lineas = []
        for clave, valor in sorted(self.contadores.items()):
            lineas.append(f"{clave} {valor}")
        for clave, valores in sorted(self.latencias.items()):
            if not valores:
                continue
            base = clave.split("{")[0]
            sufijo = clave[len(base):]
            lineas.append(f"{base}_count{sufijo} {len(valores)}")
            lineas.append(f"{base}_sum{sufijo} {sum(valores):.6f}")
            # p95 y p99: mucho mas informativos que el promedio, porque el
            # promedio esconde justamente a los usuarios peor atendidos.
            lineas.append(f"{base}_p95{sufijo} {self.percentil(clave, 0.95):.6f}")
            lineas.append(f"{base}_p99{sufijo} {self.percentil(clave, 0.99):.6f}")
        return "\n".join(lineas) + "\n"


metricas = Metricas()
