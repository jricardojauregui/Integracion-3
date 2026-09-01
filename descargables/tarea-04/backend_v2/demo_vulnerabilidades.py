"""Demuestra la race condition de v1 vs la correccion de v2."""
import asyncio, sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 68)
print("DEMO 1 — Race condition: 30 transferencias simultaneas de $100")
print("         desde una cuenta con solo $1,000 (solo caben 10)")
print("=" * 68)

# --- Simulacion del comportamiento de v1 (sin lock) ---
CUENTAS_V1 = {"MX001": {"saldo": 1000.0}, "MX002": {"saldo": 0.0}}
async def transferir_v1(monto):
    o = CUENTAS_V1["MX001"]
    if o["saldo"] < monto:
        return "rechazada"
    await asyncio.sleep(0)          # cede el control: simula I/O real
    o["saldo"] -= monto
    CUENTAS_V1["MX002"]["saldo"] += monto
    return "ok"

async def main():
    r = await asyncio.gather(*[transferir_v1(100.0) for _ in range(30)])
    print(f"\n  v1  exitosas={r.count('ok'):>2}  rechazadas={r.count('rechazada'):>2}")
    print(f"      saldo final MX001 = ${CUENTAS_V1['MX001']['saldo']:,.2f}   <-- NEGATIVO")
    print(f"      total en el sistema = ${CUENTAS_V1['MX001']['saldo']+CUENTAS_V1['MX002']['saldo']:,.2f}")

    from app.core_client import AdaptadorCoreBancario, ClienteCoreSimulado
    from app.ledger import Ledger
    from app.domain import SaldoInsuficiente
    led = Ledger(AdaptadorCoreBancario(ClienteCoreSimulado(latencia_s=0),
                 dormir=lambda _: asyncio.sleep(0)))
    led.alta_cuenta("MX001", "ana", 100_000); led.alta_cuenta("MX002", "luis", 0)
    res = await asyncio.gather(*[
        led.transferir("ana","MX001","MX002",10_000,"",f"k{i}",f"c{i}") for i in range(30)],
        return_exceptions=True)
    ok = sum(1 for x in res if not isinstance(x, Exception))
    rech = sum(1 for x in res if isinstance(x, SaldoInsuficiente))
    print(f"\n  v2  exitosas={ok:>2}  rechazadas={rech:>2}")
    print(f"      saldo final MX001 = ${led.cuentas['MX001'].saldo:,.2f}   <-- CORRECTO")
    tot = led.cuentas['MX001'].saldo + led.cuentas['MX002'].saldo
    print(f"      total en el sistema = ${tot:,.2f}  (se conserva)")

    print("\n" + "=" * 68)
    print("DEMO 2 — Precision: 1000 sumas de $0.10")
    print("=" * 68)
    from decimal import Decimal
    f = 0.0
    for _ in range(1000): f += 0.10
    d = sum((Decimal("0.10") for _ in range(1000)), Decimal("0"))
    print(f"\n  v1 (float)   = {f!r}")
    print(f"  v2 (Decimal) = {d}")
    print(f"  Descuadre v1 = {abs(f - 100.0):.20f}")

    print("\n" + "=" * 68)
    print("DEMO 3 — Idempotencia: usuario reintenta tras perder senal")
    print("=" * 68)
    led2 = Ledger(AdaptadorCoreBancario(ClienteCoreSimulado(latencia_s=0),
                  dormir=lambda _: asyncio.sleep(0)))
    led2.alta_cuenta("MX001","ana",100_000); led2.alta_cuenta("MX002","luis",0)
    for i in range(3):
        m = await led2.transferir("ana","MX001","MX002",50_000,"","MISMA-CLAVE",f"c{i}")
        print(f"  Intento {i+1}: movimiento={m.id[:8]}  saldo=${led2.cuentas['MX001'].saldo:,.2f}")
    print("  -> 3 envios, 1 solo cargo. En v1 habrian sido 3 cargos.")

asyncio.run(main())
