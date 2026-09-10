#!/usr/bin/env bash
# ---------------------------------------------------------------------
# tomar_capturas.sh — reproduce en TU VM la salida de los pasos 1-6 de
# la galería del Ejercicio 03 (módulo SOAP), con banners para que sepas
# qué PNG capturar en cada bloque. Los pasos 7 (GUI Electron) son
# manuales: ver LEEME.txt.
#
# Requiere: PostgreSQL con el esquema del Ej2 + el módulo SOAP cargado,
# el servicio corriendo (python app.py) y `curl` / `psql` en el PATH.
#
# Uso:
#   cd apps/services/library_soap_service
#   BASE_URL=http://localhost:5050 \
#   PGURL="postgresql://library_user:PASS@localhost/library" \
#   SOAP_PGURL="postgresql://soap_module_user:PASS@localhost/library" \
#   bash evidencia/capturas/tomar_capturas.sh
# ---------------------------------------------------------------------
set -u

BASE_URL="${BASE_URL:-http://localhost:5050}"
PGURL="${PGURL:-postgresql://library_user@localhost/library}"
SOAP_PGURL="${SOAP_PGURL:-postgresql://soap_module_user@localhost/library}"
XML_DIR="$(cd "$(dirname "$0")/../xml" && pwd)"
SVC_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

banner() { printf '\n\n============================================================\n>>> CAPTURA: %s\n============================================================\n' "$1"; }
post()   { curl -s -i -X POST "$BASE_URL/soap" -H 'Content-Type: text/xml' --data-binary "@$XML_DIR/$1"; }

banner "paso1-archivos-en-vm.png"
( cd "$SVC_DIR" && ls -R . | sed -n '1,80p' )

banner "paso2-pip-install.png"
echo "# ejecuta manualmente y captura:  pip install -r requirements.txt"

banner "paso3-sql-create-table.png"
# privilegios AL FINAL: otorga sobre las vistas / stored procedure de los
# tres archivos anteriores. PGURL_OWNER (superusuario/owner) para privileges.
PGURL_OWNER="${PGURL_OWNER:-$PGURL}"
for f in soap_module.sql soap_module_procedures.sql soap_module_migracion_correo_estadisticas.sql; do
  echo "--- psql -f sql/$f ---"
  psql "$PGURL" -v ON_ERROR_STOP=1 -f "$SVC_DIR/sql/$f"
done
echo "--- psql -f sql/soap_module_privileges.sql (como owner) ---"
psql "$PGURL_OWNER" -v ON_ERROR_STOP=1 -f "$SVC_DIR/sql/soap_module_privileges.sql" || echo "(corre este archivo como el superusuario/owner de la base)"

banner "paso4-verif-clasificadores.png";  psql "$PGURL" -c '\d clasificadores'
banner "paso4-verif-clasificaciones.png"; psql "$PGURL" -c '\d clasificaciones_cloud'
banner "paso4-verif-clientes.png";        psql "$PGURL" -c '\d clientes_servidos'
banner "paso4-verif-duplicados.png"
psql "$PGURL" -c "SELECT id_clasificador, isbn, id_concepto, count(*) FROM clasificaciones_cloud GROUP BY 1,2,3 HAVING count(*) > 1;"
echo "-> 0 filas esperado (lo garantiza el UNIQUE)"

banner "paso4-soap-user-denegado.png  /  paso6-soap-user-en-usuarios.png"
psql "$SOAP_PGURL" -c "SELECT * FROM usuarios LIMIT 1;" || true
psql "$SOAP_PGURL" -c "INSERT INTO libros (isbn,titulo,anio_publicacion,precio,stock,id_formato) VALUES ('000-TEST','no',2024,1,1,1);" || true
echo "-> ambas deben fallar con: permission denied for table ..."

banner "paso5-servidor-corriendo.png"
echo "# deja 'python app.py' corriendo en otra terminal y captura su log de arranque"

banner "paso5-wsdl-respondiendo.png"
curl -s -i "$BASE_URL/wsdl" | sed -n '1,20p'

banner "paso6-p01-conceptos-pendientes.png";   post P01_conceptos_pendientes_request.xml
banner "paso6-p02-registro-exitoso.png";       post P02_registrar_iaas_request.xml
banner "paso6-p03-progreso.png";               post P03_progreso_usuario_request.xml
banner "paso6-n01-409-duplicado.png";          post N01_repetir_clasificacion_request.xml
banner "paso6-n02-concepto-inexistente.png";   post N02_concepto_inexistente_request.xml
banner "paso6-n03-modelo-invalido.png";        post N03_modelo_invalido_request.xml
banner "paso6-n04-xml-invalido.png";           post N04_xml_invalido_request.xml
banner "paso6-t1-estadisticas-ws-security.png"
echo "# ajusta la contraseña en el XML a la real de tu .env antes de enviarlo"
post T1b_estadisticas_credenciales_correctas_request.xml

printf '\n\nListo. Paso 7 (GUI Electron) es manual: cd apps/client01 && npm start\n'
