# Tarea 4 — Arquitectura Cloud híbrida para banca móvil

Diseño de arquitectura asistido por IA, con prototipo de backend ejecutable.

## Contenido

| Archivo | Descripción |
|---|---|
| `DOCUMENTACION.md` | **Documento de entrega** con las 12 secciones solicitadas |
| `prompts/historial_prompts.md` | Prompts literales (inicial + 6 de mejora) |
| `diagramas/arquitectura_v1.svg` | Primera arquitectura (sin iterar) |
| `diagramas/arquitectura_final.svg` | Arquitectura final |
| `backend_v1/main.py` | Prototipo inicial **sin corregir** (evidencia de las fallas) |
| `backend_v2/` | Prototipo endurecido + 43 pruebas |

## Ejecutar

```bash
pip install fastapi "uvicorn[standard]" pyjwt httpx pytest pytest-asyncio

cd backend_v2
python -m pytest tests/ -v        # 43 pruebas
python demo_vulnerabilidades.py   # demuestra v1 vs v2
uvicorn app.main:app --reload     # API en http://localhost:8000/docs
```

## Resumen

- **15 vulnerabilidades** catalogadas (F-1 a F-15) y corregidas
- **6 iteraciones** de refinamiento documentadas
- **43 pruebas** automatizadas, cada una ligada a una falla concreta
- Demostración ejecutable: v1 permite sobregiro de $2.000 sobre una cuenta de $1.000
