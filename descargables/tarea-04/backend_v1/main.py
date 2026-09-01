"""
PROTOTIPO v1 — Backend de banca movil
=====================================

Esta es la PRIMERA version, tal como la produjo el asistente de IA a partir
del prompt inicial. Se conserva intencionalmente SIN CORREGIR para poder
documentar, en el reporte, que problemas tenia y como se detectaron.

NO USAR. Ver backend_v2/ para la version corregida.

Fallas detectadas durante la revision (analizadas en DOCUMENTACION.md,
seccion 7). Cada una esta marcada abajo con [F-n]:

  [F-1]  Secreto JWT embebido en el codigo (hardcoded).
  [F-2]  Tokens sin expiracion ni refresh; no hay forma de revocarlos.
  [F-3]  Contrasenas comparadas en texto plano.
  [F-4]  Saldos y montos en float -> error de redondeo en dinero.
  [F-5]  Transferencia sin transaccion atomica: si falla a medias, el
         dinero desaparece o se duplica.
  [F-6]  Sin idempotencia: un reintento del cliente duplica la transferencia.
  [F-7]  Sin control de concurrencia: dos transferencias simultaneas
         producen "lost update" (race condition).
  [F-8]  Llamada al core bancario sin timeout ni reintentos: un core lento
         agota el pool de conexiones y tumba toda la API.
  [F-9]  Sin validacion de monto (acepta negativos -> robo por transferencia
         de monto negativo).
  [F-10] Sin autorizacion a nivel de recurso: cualquier usuario autenticado
         puede consultar/mover la cuenta de otro (IDOR).
  [F-11] Sin rate limiting -> fuerza bruta sobre /login.
  [F-12] Logs con datos sensibles (PAN, saldo, token).
  [F-13] Sin trazabilidad: no hay correlation id ni auditoria.
  [F-14] CORS totalmente abierto.
  [F-15] Estado en memoria del proceso -> no escala horizontalmente.
"""

import logging
from datetime import datetime

import jwt
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Banca Movil API", version="1.0.0")

# [F-14] CORS abierto a cualquier origen, con credenciales.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [F-1] Secreto en el codigo fuente, versionado en git.
SECRET_KEY = "banca-secreto-2024"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("banca")

# [F-15] Estado en memoria: se pierde al reiniciar y no se comparte
# entre instancias, asi que la API no puede escalar horizontalmente.
# [F-3] Contrasenas en texto plano.
# [F-4] Saldos como float.
USUARIOS = {
    "ana": {"password": "1234", "cuenta": "MX001", "pan": "4111111111111111"},
    "luis": {"password": "abcd", "cuenta": "MX002", "pan": "4222222222222222"},
}

CUENTAS = {
    "MX001": {"saldo": 15000.50, "titular": "ana"},
    "MX002": {"saldo": 8200.75, "titular": "luis"},
}

MOVIMIENTOS = []


class LoginRequest(BaseModel):
    usuario: str
    password: str


class TransferenciaRequest(BaseModel):
    origen: str
    destino: str
    monto: float          # [F-4] float para dinero
    concepto: str = ""


def usuario_actual(authorization: str = Header(None)):
    """Decodifica el JWT. [F-2] No valida expiracion porque no la emite."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta token")
    token = authorization.replace("Bearer ", "")
    try:
        datos = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return datos["usuario"]
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalido")


@app.post("/login")
def login(req: LoginRequest):
    # [F-11] Sin rate limiting: se puede hacer fuerza bruta sin limite.
    usuario = USUARIOS.get(req.usuario)

    # [F-3] Comparacion en texto plano y no constante en tiempo.
    if not usuario or usuario["password"] != req.password:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    # [F-2] Token sin 'exp', sin 'iat', sin 'jti': vive para siempre y no
    # se puede revocar.
    token = jwt.encode({"usuario": req.usuario}, SECRET_KEY, algorithm="HS256")

    # [F-12] Se registra el token completo en los logs.
    log.info(f"Login exitoso usuario={req.usuario} token={token}")

    return {"token": token}


@app.get("/cuentas/{numero}")
def consultar_cuenta(numero: str, usuario: str = usuario_actual):
    # [F-10] IDOR: no se verifica que la cuenta pertenezca al usuario
    # autenticado. Cualquiera con un token valido lee cualquier cuenta.
    cuenta = CUENTAS.get(numero)
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # [F-12] Log con saldo y PAN completo (dato de tarjeta).
    log.info(f"Consulta cuenta={numero} saldo={cuenta['saldo']}")

    return {"numero": numero, "saldo": cuenta["saldo"]}


def notificar_core_bancario(payload):
    """
    [F-8] Llamada sincrona al core on-premises SIN timeout, sin reintentos
    y sin circuit breaker. Si el core tarda, cada request se queda colgado
    y el pool de workers se agota: el core arrastra a toda la API.
    """
    import httpx
    respuesta = httpx.post("http://core-bancario.interno:8080/asiento", json=payload)
    return respuesta.json()


@app.post("/transferencias")
def transferir(req: TransferenciaRequest, usuario: str = usuario_actual):
    origen = CUENTAS.get(req.origen)
    destino = CUENTAS.get(req.destino)

    if not origen or not destino:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # [F-9] No se valida que el monto sea positivo. Un monto negativo
    # invierte el sentido de la transferencia: robo directo.
    if origen["saldo"] < req.monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")

    # [F-5] [F-7] Sin transaccion ni bloqueo. Entre el read y el write puede
    # entrar otra peticion (lost update). Y si el proceso muere entre las dos
    # lineas, el dinero se destruye.
    origen["saldo"] -= req.monto
    destino["saldo"] += req.monto

    # [F-6] Sin clave de idempotencia: si el celular reintenta por timeout,
    # la transferencia se ejecuta dos veces.
    movimiento = {
        "id": len(MOVIMIENTOS) + 1,
        "origen": req.origen,
        "destino": req.destino,
        "monto": req.monto,
        "fecha": datetime.now().isoformat(),
    }
    MOVIMIENTOS.append(movimiento)

    # [F-8] Si esto falla, el dinero YA se movio en memoria pero el core
    # nunca se entera: los sistemas quedan inconsistentes y no hay
    # compensacion ni reintento.
    notificar_core_bancario(movimiento)

    return {"estatus": "ok", "movimiento": movimiento}


@app.get("/movimientos")
def movimientos(usuario: str = usuario_actual):
    # [F-10] Devuelve los movimientos de TODOS los usuarios.
    return MOVIMIENTOS


@app.get("/health")
def health():
    return {"status": "ok"}
