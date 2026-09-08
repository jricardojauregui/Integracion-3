# Tarea 4 — Interoperabilidad

## Herramienta y lenguaje

**`zeep`** (Python) — deliberadamente una tecnología *distinta* a cómo
está hecho el servidor: el servidor arma y parsea el `soap:Envelope` a
mano con `xml.etree.ElementTree` (decisión de ingeniería #6); `zeep` en
cambio genera el cliente completo **leyendo el WSDL**, sin que el
programador toque XML en ningún momento. Aunque ambos lados terminan en
Python, la forma de trabajar es opuesta — que es justo lo que esta tarea
pide demostrar: que el contrato (no el lenguaje ni la librería) es lo que
hace posible la interoperabilidad.

## Proceso de generación del cliente

```python
import zeep
cliente = zeep.Client(wsdl="http://<servidor>/wsdl")
servicio = cliente.create_service(
    "{urn:udem:iac:libreria:soap}LibraryClassifierBinding",
    "http://<servidor>/soap",
)
```

`zeep.Client` descarga el WSDL, resuelve los tipos XSD inline (Paso 9) y
genera automáticamente los objetos Python (`ObtenerConceptosPendientesRequest`,
etc.) y sus validaciones — nunca se le dice a mano qué campos tiene cada
operación. El código completo, reutilizable, está en
`interop_client_zeep.py` en esta misma carpeta.

## Evidencia de ejecución (real, contra el servidor corriendo)

`ObtenerConceptosPendientes()`:

```xml
<!-- request real (evidencia/xml/zeep_ObtenerConceptosPendientes_request.xml) -->
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns0="urn:udem:iac:libreria:soap">
  <soap:Body>
    <ns0:ObtenerConceptosPendientesRequest/>
  </soap:Body>
</soap:Envelope>
```

Resultado Python que `zeep` entregó (ya deserializado, tipado — `idConcepto`
llegó como `int`, no como string):

```python
[{
    'isbn': '978-0-14-118776-1',
    'tituloLibro': '1984',
    'categoria': 'Ciencia ficción',
    'idConcepto': 12,
    'nombreConcepto': 'Distopía'
}]
```

`RegistrarClasificacion(idClasificador=1, isbn="978-0-14-118776-1", idConcepto=12, modeloCloud="SaaS")`:

```python
{
    'idClasificacion': 2,
    'mensaje': 'Clasificación registrada correctamente.'
}
```

Los 4 archivos XML completos (request/response de cada llamada) están en
`evidencia/xml/zeep_*.xml`.

## Comparación: cliente manual (client01/src/soapClient.js) vs. cliente generado (zeep)

| | Cliente manual (Electron) | Cliente generado (zeep) |
|---|---|---|
| Cómo sabe qué operaciones existen | Hardcodeado en el código (`soapClient.js` conoce cada Request/Response a mano) | Leído del WSDL en tiempo de ejecución |
| Validación de tipos | Ninguna del lado cliente — confía en que el servidor valide (Paso 11) | `zeep` puede validar contra el XSD antes de enviar |
| Construcción del Envelope | Manual (funciones `campo()`/`construirEnvelope()`, con escape explícito) | Automática, invisible al programador |
| Costo de mantenimiento si cambia el contrato | Hay que editar `soapClient.js` a mano | Basta con volver a apuntar al WSDL nuevo — el cliente se regenera solo |
| Curva de aprendizaje | Requiere entender XML/SOAP a fondo | Se puede usar sin saber cómo se ve un Envelope por dentro |

La conclusión práctica: el cliente manual fue el ejercicio correcto para
*entender* SOAP (Parte 6 del ejercicio guiado); un cliente generado como
`zeep` es lo que se usaría en un proyecto real una vez que el contrato ya
está estable, porque reduce drásticamente el código a mantener del lado
cliente.
