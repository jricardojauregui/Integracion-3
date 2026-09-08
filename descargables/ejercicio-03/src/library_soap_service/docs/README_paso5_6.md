# Paso 5-6: Estructura del módulo y ambiente Python

- Estructura creada tal como el árbol pedido (ver estructura_modulo/,
  copia de referencia -- el código fuente definitivo y actualizado con
  TODOS los pasos está en ../../codigo_fuente_completo/library_soap_service/).
- Ambiente Python verificado por el usuario en su Mac: venv creado,
  `pip install flask psycopg2-binary python-dotenv pytest` sin conflictos
  (Flask 3.1.3, psycopg2-binary 2.9.12), y confirmado también en un
  sandbox aislado por Claude antes de entregarlo (import limpio, /wsdl
  responde 200, pytest 1 passed).
- Importante: correr `python app.py` / `pytest` PARADO DENTRO de
  `apps/services/library_soap_service/`, no desde la raíz del repo
  (los imports de config/db/soap son paquetes de nivel superior).

(Se quitó una copia redundante del código aquí para no duplicar 65MB de
entorno virtual -- el código fuente vive una sola vez, en
codigo_fuente_completo/library_soap_service/.)
