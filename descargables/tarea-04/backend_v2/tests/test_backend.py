"""
Suite de pruebas del backend v2.

Cada prueba esta ligada a una falla concreta de v1 ([F-n]), de modo que la
suite sirve como evidencia verificable de que la correccion existe y
funciona: no basta con afirmar en el reporte que "se corrigio la
concurrencia", hay que poder ejecutarlo.

Ejecutar:
    cd backend_v2
    python -m pytest tests/ -v
"""

import asyncio
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core_client import (AdaptadorCoreBancario, ClienteCoreSimulado,
                             CoreNoDisponible, EstadoCircuito)
from app.domain import (EstadoMovimiento, MontoInvalido, NoAutorizado,
                        SaldoInsuficiente, a_decimal)
from app.ledger import Ledger
from app.main import app, USUARIOS
from app.security import (hash_password, verificar_password, emitir_access_token,
                          decodificar_token, TokenInvalido, registrar_intento,
                          LimiteExcedido, enmascarar)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def token_ana(cliente):
    respuesta = cliente.post("/auth/login",
                             json={"usuario": "ana", "password": "Sup3rSegura!2024"})
    assert respuesta.status_code == 200
    return respuesta.json()["access_token"]


def nuevo_ledger(cliente_core=None):
    """Ledger aislado por prueba, para que no compartan estado."""
    adaptador = AdaptadorCoreBancario(
        cliente=cliente_core or ClienteCoreSimulado(latencia_s=0),
        reintentos=2, timeout_s=0.5, umbral_fallos=3, espera_circuito_s=0.2,
        dormir=lambda _: asyncio.sleep(0),   # sin esperas reales en pruebas
    )
    ledger = Ledger(adaptador)
    ledger.alta_cuenta("MX001", "ana", 1_500_050)
    ledger.alta_cuenta("MX002", "luis", 820_075)
    return ledger


# ---------------------------------------------------------------------------
# [F-3] Contrasenas
# ---------------------------------------------------------------------------
class TestPasswords:
    def test_password_no_se_almacena_en_claro(self):
        almacenado = USUARIOS["ana"]["password_hash"]
        assert "Sup3rSegura!2024" not in almacenado
        assert almacenado.startswith("pbkdf2$")

    def test_verificacion_correcta(self):
        h = hash_password("MiClave123!")
        assert verificar_password("MiClave123!", h)
        assert not verificar_password("MiClave123", h)

    def test_misma_password_produce_hashes_distintos(self):
        """La sal aleatoria evita que dos usuarios con igual clave se delaten."""
        assert hash_password("igual") != hash_password("igual")


# ---------------------------------------------------------------------------
# [F-2] Tokens
# ---------------------------------------------------------------------------
class TestTokens:
    def test_token_incluye_expiracion_y_jti(self):
        payload = decodificar_token(emitir_access_token("ana", "MX001"))
        for campo in ("exp", "iat", "jti", "sub", "aud", "iss"):
            assert campo in payload

    def test_refresh_no_sirve_como_access(self):
        from app.security import emitir_refresh_token
        with pytest.raises(TokenInvalido):
            decodificar_token(emitir_refresh_token("ana"), tipo_esperado="access")

    def test_token_manipulado_se_rechaza(self):
        token = emitir_access_token("ana", "MX001")
        with pytest.raises(TokenInvalido):
            decodificar_token(token[:-4] + "AAAA")

    def test_logout_revoca_el_token(self, cliente, token_ana):
        cabeceras = {"Authorization": f"Bearer {token_ana}"}
        assert cliente.post("/auth/logout", headers=cabeceras).status_code == 200
        # El mismo token ya no debe servir.
        assert cliente.get("/cuentas/MX001", headers=cabeceras).status_code == 401

    def test_sin_token_no_hay_acceso(self, cliente):
        assert cliente.get("/cuentas/MX001").status_code == 401


# ---------------------------------------------------------------------------
# [F-4] [F-9] Dinero y validacion de montos
# ---------------------------------------------------------------------------
class TestMontos:
    def test_precision_decimal_exacta(self):
        """0.1 + 0.2 == 0.3 exacto con Decimal (con float no lo seria)."""
        assert a_decimal("0.10") + a_decimal("0.20") == Decimal("0.30")

    @pytest.mark.parametrize("valor", ["-100.00", "0", "0.00", "abc", "", None])
    def test_montos_invalidos_se_rechazan(self, valor):
        with pytest.raises(MontoInvalido):
            a_decimal(valor)

    def test_rechaza_mas_de_dos_decimales(self):
        with pytest.raises(MontoInvalido):
            a_decimal("10.999")

    def test_rechaza_infinito_y_nan(self):
        for valor in ["Infinity", "NaN", "-Infinity"]:
            with pytest.raises(MontoInvalido):
                a_decimal(valor)

    def test_monto_negativo_por_api_se_rechaza(self, cliente, token_ana):
        """v1 permitia esto: era robo por transferencia de monto negativo."""
        respuesta = cliente.post(
            "/transferencias",
            headers={"Authorization": f"Bearer {token_ana}",
                     "Idempotency-Key": "test-negativo-001"},
            json={"origen": "MX001", "destino": "MX002", "monto": "-5000.00"},
        )
        assert respuesta.status_code == 422


# ---------------------------------------------------------------------------
# [F-10] Autorizacion a nivel de recurso (IDOR)
# ---------------------------------------------------------------------------
class TestAutorizacion:
    def test_no_puede_ver_cuenta_ajena(self, cliente, token_ana):
        respuesta = cliente.get("/cuentas/MX002",
                                headers={"Authorization": f"Bearer {token_ana}"})
        assert respuesta.status_code == 403

    def test_no_puede_transferir_desde_cuenta_ajena(self, cliente, token_ana):
        respuesta = cliente.post(
            "/transferencias",
            headers={"Authorization": f"Bearer {token_ana}",
                     "Idempotency-Key": "test-idor-001"},
            json={"origen": "MX002", "destino": "MX001", "monto": "100.00"},
        )
        assert respuesta.status_code == 403

    @pytest.mark.asyncio
    async def test_movimientos_solo_muestran_los_propios(self):
        ledger = nuevo_ledger()
        await ledger.transferir("ana", "MX001", "MX002", 10_000, "x", "k1", "c1")
        assert len(ledger.movimientos_de("ana")) == 1
        # Luis participa como destino, asi que tambien lo ve; pero un tercero no.
        assert len(ledger.movimientos_de("carlos")) == 0


# ---------------------------------------------------------------------------
# [F-6] Idempotencia
# ---------------------------------------------------------------------------
class TestIdempotencia:
    def test_falta_clave_devuelve_400(self, cliente, token_ana):
        respuesta = cliente.post(
            "/transferencias",
            headers={"Authorization": f"Bearer {token_ana}"},
            json={"origen": "MX001", "destino": "MX002", "monto": "100.00"},
        )
        assert respuesta.status_code == 400

    @pytest.mark.asyncio
    async def test_misma_clave_no_duplica_el_cargo(self):
        """El escenario real: el celular pierde senal y el usuario reintenta."""
        ledger = nuevo_ledger()
        saldo_inicial = ledger.cuentas["MX001"].saldo_centavos

        m1 = await ledger.transferir("ana", "MX001", "MX002", 50_000, "", "k-dup", "c1")
        m2 = await ledger.transferir("ana", "MX001", "MX002", 50_000, "", "k-dup", "c2")

        assert m1.id == m2.id                       # mismo movimiento
        assert ledger.cuentas["MX001"].saldo_centavos == saldo_inicial - 50_000

    @pytest.mark.asyncio
    async def test_claves_distintas_si_generan_dos_movimientos(self):
        ledger = nuevo_ledger()
        m1 = await ledger.transferir("ana", "MX001", "MX002", 10_000, "", "k-a", "c1")
        m2 = await ledger.transferir("ana", "MX001", "MX002", 10_000, "", "k-b", "c2")
        assert m1.id != m2.id


# ---------------------------------------------------------------------------
# [F-5] [F-7] Atomicidad y concurrencia
# ---------------------------------------------------------------------------
class TestConcurrencia:
    @pytest.mark.asyncio
    async def test_no_se_pierde_ni_se_crea_dinero(self):
        """Invariante contable: la suma total debe conservarse siempre."""
        ledger = nuevo_ledger()
        total_inicial = sum(c.saldo_centavos for c in ledger.cuentas.values())

        await asyncio.gather(*[
            ledger.transferir("ana", "MX001", "MX002", 1_000, "", f"k{i}", f"c{i}")
            for i in range(20)
        ])

        total_final = sum(c.saldo_centavos for c in ledger.cuentas.values())
        assert total_final == total_inicial

    @pytest.mark.asyncio
    async def test_transferencias_concurrentes_no_dejan_saldo_negativo(self):
        """
        En v1 esto fallaba: 30 peticiones simultaneas leian el mismo saldo
        antes de que ninguna lo escribiera, todas veian fondos suficientes
        y la cuenta terminaba en negativo (lost update).
        """
        ledger = nuevo_ledger()
        ledger.cuentas["MX001"].saldo_centavos = 100_000   # $1,000.00

        resultados = await asyncio.gather(*[
            ledger.transferir("ana", "MX001", "MX002", 10_000, "", f"c{i}", f"x{i}")
            for i in range(30)
        ], return_exceptions=True)

        exitosas = [r for r in resultados if not isinstance(r, Exception)]
        rechazadas = [r for r in resultados if isinstance(r, SaldoInsuficiente)]

        assert ledger.cuentas["MX001"].saldo_centavos >= 0
        assert len(exitosas) == 10        # exactamente las que caben
        assert len(rechazadas) == 20

    @pytest.mark.asyncio
    async def test_transferencias_cruzadas_no_producen_deadlock(self):
        """A->B y B->A simultaneas: el orden de locks debe evitar el bloqueo."""
        ledger = nuevo_ledger()
        resultado = await asyncio.wait_for(
            asyncio.gather(
                ledger.transferir("ana", "MX001", "MX002", 1_000, "", "ka", "ca"),
                ledger.transferir("luis", "MX002", "MX001", 1_000, "", "kb", "cb"),
            ),
            timeout=5.0,   # si hubiera deadlock, esto expiraria
        )
        assert len(resultado) == 2


# ---------------------------------------------------------------------------
# [F-8] Resiliencia del enlace hibrido
# ---------------------------------------------------------------------------
class TestResilienciaCore:
    @pytest.mark.asyncio
    async def test_reintenta_ante_fallo_transitorio(self):
        core = ClienteCoreSimulado(latencia_s=0, fallar_n_veces=1)
        adaptador = AdaptadorCoreBancario(core, reintentos=3, timeout_s=0.5,
                                          dormir=lambda _: asyncio.sleep(0))
        resultado = await adaptador.registrar_asiento({"id": "m1"})
        assert resultado["estatus"] == "asentado"
        assert core.llamadas == 2      # fallo una vez, tuvo exito a la segunda

    @pytest.mark.asyncio
    async def test_circuito_se_abre_tras_fallos_repetidos(self):
        core = ClienteCoreSimulado(fallar_siempre=True)
        adaptador = AdaptadorCoreBancario(core, reintentos=1, timeout_s=0.2,
                                          umbral_fallos=3, espera_circuito_s=10,
                                          dormir=lambda _: asyncio.sleep(0))
        for _ in range(3):
            with pytest.raises(CoreNoDisponible):
                await adaptador.registrar_asiento({"id": "m"})

        assert adaptador.breaker.estado == EstadoCircuito.ABIERTO

        # Con el circuito abierto ya no se llama al core: se falla rapido.
        llamadas_antes = core.llamadas
        with pytest.raises(CoreNoDisponible):
            await adaptador.registrar_asiento({"id": "m"})
        assert core.llamadas == llamadas_antes

    @pytest.mark.asyncio
    async def test_core_caido_deja_movimiento_pendiente_no_lo_pierde(self):
        """
        La diferencia clave con v1: alli un core caido dejaba el sistema
        inconsistente y sin rastro. Aqui queda registro auditable.
        """
        ledger = nuevo_ledger(ClienteCoreSimulado(fallar_siempre=True))
        movimiento = await ledger.transferir(
            "ana", "MX001", "MX002", 10_000, "", "k-core-caido", "c1")

        assert movimiento.estado == EstadoMovimiento.PENDIENTE
        assert movimiento.id in ledger.movimientos      # persistido

    @pytest.mark.asyncio
    async def test_reconciliacion_confirma_pendientes(self):
        core = ClienteCoreSimulado(fallar_siempre=True)
        ledger = nuevo_ledger(core)
        await ledger.transferir("ana", "MX001", "MX002", 10_000, "", "k-r", "c1")

        core.fallar_siempre = False          # el core vuelve
        ledger.adaptador_core.breaker.registrar_exito()   # se cierra el circuito

        resumen = await ledger.reconciliar_pendientes()
        assert resumen["confirmados"] == 1
        assert resumen["siguen_pendientes"] == 0


# ---------------------------------------------------------------------------
# [F-11] Rate limiting
# ---------------------------------------------------------------------------
class TestRateLimiting:
    def test_bloquea_tras_demasiados_intentos(self):
        clave = "prueba:fuerza-bruta"
        for _ in range(5):
            registrar_intento(clave, maximo=5, ventana_s=60)
        with pytest.raises(LimiteExcedido):
            registrar_intento(clave, maximo=5, ventana_s=60)

    def test_login_repetido_devuelve_429(self, cliente):
        for _ in range(10):
            respuesta = cliente.post("/auth/login",
                                     json={"usuario": "objetivo",
                                           "password": "incorrecta123"})
            if respuesta.status_code == 429:
                assert "Retry-After" in respuesta.headers
                return
        pytest.fail("Nunca se aplico el limite de intentos")


# ---------------------------------------------------------------------------
# [F-12] [F-13] Observabilidad
# ---------------------------------------------------------------------------
class TestObservabilidad:
    def test_enmascarar_oculta_datos_sensibles(self):
        assert enmascarar("4111111111111111") == "************1111"

    def test_redaccion_de_campos_prohibidos(self):
        from app.observability import redactar
        limpio = redactar({"usuario": "ana", "password": "secreta",
                           "anidado": {"token": "abc"}})
        assert limpio["usuario"] == "ana"
        assert limpio["password"] == "[REDACTADO]"
        assert limpio["anidado"]["token"] == "[REDACTADO]"

    def test_respuesta_incluye_correlation_id(self, cliente):
        respuesta = cliente.get("/health/live")
        assert "X-Correlation-ID" in respuesta.headers

    def test_correlation_id_del_cliente_se_respeta(self, cliente):
        propio = "mi-id-de-traza-123"
        respuesta = cliente.get("/health/live",
                                headers={"X-Correlation-ID": propio})
        assert respuesta.headers["X-Correlation-ID"] == propio

    def test_endpoint_de_metricas_expone_contadores(self, cliente):
        cliente.get("/health/live")
        cuerpo = cliente.get("/metrics").text
        assert "http_peticiones_total" in cuerpo


# ---------------------------------------------------------------------------
# [F-14] Cabeceras y CORS
# ---------------------------------------------------------------------------
class TestCabeceras:
    def test_no_permite_origen_arbitrario(self):
        from app.config import config
        assert "*" not in config.cors_origenes

    def test_cabeceras_de_seguridad_presentes(self, cliente):
        cabeceras = cliente.get("/health/live").headers
        assert cabeceras["X-Content-Type-Options"] == "nosniff"
        assert "Strict-Transport-Security" in cabeceras
        assert cabeceras["Cache-Control"] == "no-store"


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------
class TestSalud:
    def test_liveness_no_depende_del_core(self, cliente):
        """Debe responder 200 aunque el core este caido."""
        assert cliente.get("/health/live").status_code == 200

    def test_readiness_reporta_estado_del_circuito(self, cliente):
        cuerpo = cliente.get("/health/ready").json()
        assert "circuito_core" in cuerpo


# ---------------------------------------------------------------------------
# Flujo completo
# ---------------------------------------------------------------------------
class TestFlujoCompleto:
    def test_login_consulta_transfiere_y_verifica(self, cliente, token_ana):
        cabeceras = {"Authorization": f"Bearer {token_ana}"}

        saldo_inicial = Decimal(
            cliente.get("/cuentas/MX001", headers=cabeceras).json()["saldo"])

        respuesta = cliente.post(
            "/transferencias",
            headers={**cabeceras, "Idempotency-Key": "flujo-completo-001"},
            json={"origen": "MX001", "destino": "MX002",
                  "monto": "250.75", "concepto": "Pago de prueba"},
        )
        assert respuesta.status_code == 201
        assert respuesta.json()["monto"] == "250.75"

        saldo_final = Decimal(
            cliente.get("/cuentas/MX001", headers=cabeceras).json()["saldo"])
        assert saldo_inicial - saldo_final == Decimal("250.75")
