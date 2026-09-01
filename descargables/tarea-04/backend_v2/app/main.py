"""
PROTOTIPO v2 — Backend de banca movil (version endurecida)
==========================================================

Version corregida tras las cinco iteraciones de revision documentadas en
DOCUMENTACION.md. Cada correccion esta marcada con [F-n] y referida a la
falla original de backend_v1/main.py.

Ejecutar:
    cd backend_v2
    uvicorn app.main:app --reload

Documentacion interactiva: http://localhost:8000/docs
"""

import time
from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from .config import config
from .core_client import (AdaptadorCoreBancario, ClienteCoreSimulado,
                          EstadoCircuito)
from .domain import (ErrorNegocio, a_decimal, CENTAVOS)
from .ledger import Ledger
from .observability import (configurar_logging, correlation_id_ctx, metricas,
                            nuevo_correlation_id, usuario_ctx)
from .security import (LimiteExcedido, TokenInvalido, decodificar_token,
                       emitir_access_token, emitir_refresh_token,
                       hash_password, limpiar_intentos, registrar_intento,
                       revocar_token, verificar_password)

import logging

configurar_logging()
log = logging.getLogger("banca.api")

app = FastAPI(
    title="Banca Movil API",
    version="2.0.0",
    description="Backend de banca movil sobre arquitectura de nube hibrida.",
)

# CORRIGE [F-14]: origenes explicitos, metodos y cabeceras acotados.
# Un "*" con allow_credentials=True (como en v1) permite que cualquier sitio
# haga peticiones autenticadas en nombre del usuario.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origenes,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID",
                   "Idempotency-Key"],
)

# --- Dependencias de infraestructura ---------------------------------------
# El cliente simulado se inyecta aqui; en produccion se sustituye por el
# cliente HTTP real hacia el core, sin tocar el resto del codigo.
cliente_core = ClienteCoreSimulado(latencia_s=0.01)
adaptador_core = AdaptadorCoreBancario(
    cliente=cliente_core,
    reintentos=config.core_reintentos,
    timeout_s=config.core_timeout_s,
    umbral_fallos=config.circuito_umbral_fallos,
    espera_circuito_s=config.circuito_espera_s,
)
ledger = Ledger(adaptador_core)

# Datos de ejemplo. CORRIGE [F-3]: contrasenas hasheadas, nunca en claro.
USUARIOS = {
    "ana": {"password_hash": hash_password("Sup3rSegura!2024"), "cuenta": "MX001"},
    "luis": {"password_hash": hash_password("Otra-Clave!2024"), "cuenta": "MX002"},
}
ledger.alta_cuenta("MX001", "ana", 1_500_050)    # $15,000.50 en centavos
ledger.alta_cuenta("MX002", "luis", 820_075)     # $8,200.75


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def middleware_observabilidad(request: Request, call_next):
    """
    CORRIGE [F-13]: asigna/propaga un correlation_id a cada peticion y mide
    latencia y resultado. Si el cliente ya envio uno (porque la app movil
    lo genero), se respeta: asi la traza cubre de punta a punta.
    """
    correlation_id = request.headers.get("X-Correlation-ID") or nuevo_correlation_id()
    correlation_id_ctx.set(correlation_id)
    usuario_ctx.set("-")

    inicio = time.perf_counter()
    try:
        respuesta = await call_next(request)
        codigo = respuesta.status_code
    except Exception:
        metricas.incrementar("http_errores_total", ruta=request.url.path)
        log.exception("Error no controlado")
        # Nunca se devuelve el detalle interno al cliente: un stack trace
        # revela rutas, versiones de librerias y estructura interna.
        respuesta = JSONResponse(
            status_code=500,
            content={"error": "error_interno",
                     "mensaje": "Ocurrio un error. Contacta a soporte.",
                     "correlation_id": correlation_id},
        )
        codigo = 500

    duracion = time.perf_counter() - inicio
    metricas.observar_latencia("http_duracion_segundos", duracion,
                               ruta=request.url.path)
    metricas.incrementar("http_peticiones_total",
                         ruta=request.url.path, codigo=str(codigo))

    respuesta.headers["X-Correlation-ID"] = correlation_id
    # Cabeceras de seguridad basicas.
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.exception_handler(ErrorNegocio)
async def manejar_error_negocio(request: Request, exc: ErrorNegocio):
    """
    Traduce errores de dominio a HTTP sin filtrar detalles internos.
    Los codigos son estables y legibles por maquina, para que la app movil
    reaccione distinto segun el caso sin parsear textos.
    """
    codigos_http = {
        "saldo_insuficiente": 409,
        "cuenta_no_encontrada": 404,
        "monto_invalido": 422,
        "no_autorizado": 403,
    }
    return JSONResponse(
        status_code=codigos_http.get(exc.codigo, 400),
        content={"error": exc.codigo, "mensaje": str(exc),
                 "correlation_id": correlation_id_ctx.get()},
    )


# ---------------------------------------------------------------------------
# Autenticacion
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    usuario: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=8, max_length=128)


class TransferenciaRequest(BaseModel):
    origen: str = Field(min_length=3, max_length=20)
    destino: str = Field(min_length=3, max_length=20)
    # Se recibe como cadena y se valida con Decimal: aceptar float aqui
    # reintroduciria [F-4] en la frontera del sistema.
    monto: str = Field(description="Monto con dos decimales, ej. '1500.00'")
    concepto: str = Field(default="", max_length=140)


async def usuario_autenticado(authorization: Optional[str] = Header(None)) -> dict:
    """
    Valida el access token. CORRIGE [F-2]: verifica firma, expiracion,
    emisor, audiencia, tipo y revocacion.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta el token de acceso.")
    try:
        payload = decodificar_token(authorization[7:], tipo_esperado="access")
    except TokenInvalido as error:
        raise HTTPException(status_code=401, detail=str(error))

    usuario_ctx.set(payload["sub"])
    return payload


@app.post("/auth/login", tags=["auth"])
async def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "desconocida"

    # CORRIGE [F-11]: limite por IP y por usuario. El limite por usuario
    # evita que un atacante rote IPs para atacar una cuenta concreta.
    try:
        registrar_intento(f"ip:{ip}")
        registrar_intento(f"usuario:{req.usuario}")
    except LimiteExcedido as error:
        metricas.incrementar("login_bloqueado_total")
        return JSONResponse(
            status_code=429,
            content={"error": "demasiados_intentos", "mensaje": str(error)},
            headers={"Retry-After": str(error.espera_s)},
        )

    usuario = USUARIOS.get(req.usuario)

    # CORRIGE [F-3]: verificacion contra hash y en tiempo constante.
    # Se ejecuta el hash aunque el usuario no exista, para que el tiempo de
    # respuesta no revele si la cuenta existe (enumeracion de usuarios).
    hash_referencia = usuario["password_hash"] if usuario else hash_password("dummy")
    valido = verificar_password(req.password, hash_referencia)

    if not usuario or not valido:
        metricas.incrementar("login_fallido_total")
        log.warning("Login fallido", extra={"extra_datos": {"usuario": req.usuario}})
        # Mensaje generico: no se distingue "usuario no existe" de
        # "contrasena incorrecta".
        raise HTTPException(status_code=401, detail="Credenciales invalidas.")

    limpiar_intentos(f"usuario:{req.usuario}")
    metricas.incrementar("login_exitoso_total")
    log.info("Login exitoso", extra={"extra_datos": {"usuario": req.usuario}})

    return {
        "access_token": emitir_access_token(req.usuario, usuario["cuenta"]),
        "refresh_token": emitir_refresh_token(req.usuario),
        "token_type": "Bearer",
        "expires_in": config.access_token_minutos * 60,
    }


@app.post("/auth/logout", tags=["auth"])
async def logout(payload: dict = Depends(usuario_autenticado)):
    """CORRIGE [F-2]: en v1 no habia forma de invalidar un token."""
    revocar_token(payload["jti"])
    return {"mensaje": "Sesion cerrada."}


# ---------------------------------------------------------------------------
# Cuentas y transferencias
# ---------------------------------------------------------------------------
@app.get("/cuentas/{numero}", tags=["cuentas"])
async def consultar_cuenta(numero: str, payload: dict = Depends(usuario_autenticado)):
    # CORRIGE [F-10]: el ledger valida que la cuenta sea del usuario.
    cuenta = ledger.obtener_cuenta(numero, payload["sub"])
    return {"numero": cuenta.numero, "saldo": str(cuenta.saldo), "moneda": "MXN"}


@app.get("/movimientos", tags=["cuentas"])
async def listar_movimientos(payload: dict = Depends(usuario_autenticado),
                             limite: int = 50):
    limite = max(1, min(limite, 100))   # acota el costo de la consulta
    movimientos = ledger.movimientos_de(payload["sub"], limite)
    return {"movimientos": [m.to_dict() for m in movimientos]}


@app.post("/transferencias", tags=["transferencias"], status_code=201)
async def transferir(req: TransferenciaRequest,
                     payload: dict = Depends(usuario_autenticado),
                     idempotency_key: Optional[str] = Header(
                         None, alias="Idempotency-Key")):
    """
    CORRIGE [F-6]: exige cabecera Idempotency-Key.

    Se hace obligatoria a proposito. Podria generarse en el servidor, pero
    entonces no serviria: la clave debe venir del cliente y ser la MISMA en
    el reintento, porque justamente lo que se quiere detectar es "esta es la
    peticion que ya te mande, no una nueva".
    """
    if not idempotency_key or len(idempotency_key) < 8:
        raise HTTPException(
            status_code=400,
            detail="Se requiere la cabecera 'Idempotency-Key' (min. 8 caracteres).",
        )

    monto = a_decimal(req.monto)                     # CORRIGE [F-4] y [F-9]
    monto_centavos = int((monto * 100).to_integral_value())

    inicio = time.perf_counter()
    movimiento = await ledger.transferir(
        usuario=payload["sub"],
        origen=req.origen,
        destino=req.destino,
        monto_centavos=monto_centavos,
        concepto=req.concepto,
        clave_idempotencia=idempotency_key,
        correlation_id=correlation_id_ctx.get(),
    )
    metricas.observar_latencia("transferencia_duracion_segundos",
                               time.perf_counter() - inicio)
    metricas.incrementar("transferencias_total", estado=movimiento.estado.value)

    log.info("Transferencia procesada",
             extra={"extra_datos": {"movimiento_id": movimiento.id,
                                    "estado": movimiento.estado.value}})

    respuesta = movimiento.to_dict()
    if movimiento.estado.value == "pendiente":
        # Honestidad con el cliente: la operacion se acepto y el dinero se
        # movio, pero la confirmacion del core esta pendiente.
        respuesta["aviso"] = ("La operacion se registro y sera confirmada en "
                              "breve por el sistema central.")
    return respuesta


# ---------------------------------------------------------------------------
# Operacion: salud, metricas, reconciliacion
# ---------------------------------------------------------------------------
@app.get("/health/live", tags=["operacion"])
async def liveness():
    """
    Liveness: "el proceso esta vivo". Debe ser trivial y NO consultar
    dependencias: si fallara por un core caido, Kubernetes reiniciaria en
    bucle pods que estan perfectamente sanos, empeorando la caida.
    """
    return {"status": "vivo"}


@app.get("/health/ready", tags=["operacion"])
async def readiness(response: Response):
    """
    Readiness: "puedo atender trafico". Aqui si se miran las dependencias.
    Si el circuito hacia el core esta abierto se responde 503 y el load
    balancer deja de enviar trafico a esta instancia.
    """
    estado_circuito = adaptador_core.breaker.estado
    listo = estado_circuito != EstadoCircuito.ABIERTO
    if not listo:
        response.status_code = 503
    return {
        "status": "listo" if listo else "degradado",
        "circuito_core": estado_circuito.value,
        "fallos_consecutivos": adaptador_core.breaker.fallos,
    }


@app.get("/metrics", response_class=PlainTextResponse, tags=["operacion"])
async def exponer_metricas():
    """Endpoint de scraping para Prometheus."""
    return metricas.exponer()


@app.post("/operacion/reconciliar", tags=["operacion"])
async def reconciliar(payload: dict = Depends(usuario_autenticado)):
    """
    Dispara la reconciliacion de movimientos PENDIENTE.

    En produccion NO seria un endpoint publico: seria una funcion
    serverless invocada por calendario, con un rol de ejecucion propio.
    Se expone aqui solo para poder demostrarlo en el prototipo.
    """
    if "operador" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Requiere rol de operador.")
    return await ledger.reconciliar_pendientes()
