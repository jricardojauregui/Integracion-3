"""
Cliente de interoperabilidad (Tarea 4) — generado a partir del WSDL con
`zeep`, una tecnología DISTINTA a la implementación manual del servidor
(el servidor arma/parsea el Envelope a mano con xml.etree; este cliente
nunca toca XML directamente, zeep lo hace todo desde el contrato).

Uso contra tu servidor real:
    pip install zeep
    python interop_client_zeep.py http://TU_VM:5050/wsdl http://TU_VM:5050/soap
"""
import sys

import zeep


def main():
    wsdl_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5050/wsdl"
    soap_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5050/soap"

    cliente = zeep.Client(wsdl=wsdl_url)
    # El WSDL trae una dirección de ejemplo (localhost:5050); si tu
    # servidor real está en otra URL, se puede apuntar el servicio
    # generado sin tocar el archivo WSDL:
    servicio = cliente.create_service(
        "{urn:udem:iac:libreria:soap}LibraryClassifierBinding", soap_url
    )

    print("== ObtenerConceptosPendientes ==")
    pendientes = servicio.ObtenerConceptosPendientes()
    print(pendientes)

    print("\n== RegistrarClasificacion ==")
    if pendientes:
        primero = pendientes[0]
        resultado = servicio.RegistrarClasificacion(
            idClasificador=1,  # ajustar a un id de clasificador real ya registrado
            isbn=primero.isbn,
            idConcepto=primero.idConcepto,
            modeloCloud="PaaS",
        )
        print(resultado)
    else:
        print("No hay conceptos pendientes para probar el registro.")


if __name__ == "__main__":
    main()
