# Comandos de Infraestructura — GCP

Universidad de Monterrey · Integración de Aplicaciones Computacionales

⚠️ Este documento **no incluye llaves privadas, tokens ni contraseñas**, conforme a lo exigido
por el ejercicio.

## 1. Instancia de Compute Engine

**Nota sobre el comando original de creación:** el comando exacto de `gcloud compute instances
create` usado para crear la instancia no quedó registrado en el historial de shell disponible al
momento de escribir este documento. La configuración real vigente se reconstruyó y verificó con
`gcloud compute instances describe`, mostrada a continuación, por lo que este documento refleja
el **estado actual confirmado** de la infraestructura en vez de un comando reconstruido de
memoria.

| Parámetro | Valor |
|---|---|
| Nombre de instancia | `iac608995` |
| Proyecto | `proyecto-personal-14082026` |
| Región / Zona | `northamerica-south1` / `northamerica-south1-c` |
| Tipo de máquina | `e2-standard-2` (2 vCPU, 8 GB RAM) |
| Sistema operativo | CentOS Stream 10 |
| IP interna | `10.224.0.2` |
| IP externa | Efímera (PREMIUM tier), cambia si la instancia se detiene y reinicia — **no es estática** |
| Estado | `RUNNING` |

**Justificación del dimensionamiento (`e2-standard-2`):** para un entorno de práctica con un
solo usuario administrador desarrollando y probando la aplicación, 2 vCPU y 8 GB de RAM son
suficientes para correr simultáneamente PostgreSQL, el proceso Node.js, y herramientas de
desarrollo (git, npm) sin cuellos de botella. Una instancia más pequeña (`e2-small` o
`e2-medium`) habría sido viable para solo servir la app, pero se prefirió margen adicional para
evitar que PostgreSQL compita por memoria durante las pruebas de carga masiva de datos (seed).

**Comando de verificación usado para reconstruir esta tabla:**
```bash
gcloud compute instances describe iac608995 --zone=northamerica-south1-c \
  --format="yaml(machineType,disks[0].initializeParams,networkInterfaces)"
```

## 2. Reglas de firewall

```bash
gcloud compute firewall-rules list --format="table(name,sourceRanges.list(),allowed[].map().firewall_rule().list(),targetTags.list())"
```

| Regla | Origen | Permite | Alcance |
|---|---|---|---|
| `default-allow-ssh` | `0.0.0.0/0` | `tcp:22` | Todas las instancias del proyecto |
| `default-allow-icmp` | `0.0.0.0/0` | `icmp` | Todas las instancias del proyecto |
| `default-allow-internal` | `10.128.0.0/9` | `tcp:0-65535, udp:0-65535, icmp` | Red interna del proyecto |
| `default-allow-rdp` | `0.0.0.0/0` | `tcp:3389` | Todas las instancias del proyecto (no usado; el SO es Linux) |
| `iac608995` | `0.0.0.0/0` | `tcp:3000` | Instancia `iac608995` |

### ⚠️ Hallazgo pendiente de resolver en la Parte 8

La regla `iac608995` deja el puerto **3000 abierto a todo Internet**, y `src/server.js` llama
`app.listen(PORT, callback)` **sin especificar host**, lo que en Node.js hace que el proceso
escuche en todas las interfaces (`0.0.0.0`) por defecto. La combinación de ambas cosas significa
que la aplicación Node.js está **actualmente accesible de forma directa desde Internet**, sin
pasar por ningún reverse proxy — exactamente lo que la Parte 8 del ejercicio exige evitar
("La aplicación Node.js deberá escuchar en 127.0.0.1:3000 y no exponerse directamente a
Internet").

Se mantiene así intencionalmente por ahora porque el puerto fue configurado explícitamente por
el profesor para las pruebas guiadas de esta etapa. **Antes de la entrega final**, se debe:
1. Modificar `app.listen(PORT, '127.0.0.1', callback)` para restringir el binding a localhost.
2. Eliminar o restringir la regla de firewall `iac608995` (puerto 3000) al completar la Parte 8.
3. Abrir el puerto 80 (`tcp:80`) para el reverse proxy Apache/NGINX, que será el único punto de
   entrada público.

Este hallazgo se documenta también en `SECURITY_REVIEW.md`.

## 3. Instalación y configuración de PostgreSQL

Comandos ejecutados en la instancia (ver historial de shell):

```bash
sudo dnf -y install postgresql-server
sudo postgresql-setup --initdb
sudo systemctl start postgresql.service
sudo systemctl enable postgresql.service
```

Configuración de autenticación (`pg_hba.conf`) ajustada manualmente vía `sudo vi
/var/lib/pgsql/data/pg_hba.conf` para permitir la conexión del usuario de aplicación
`library_user` a la base `library`.

Creación de base de datos y usuario de aplicación con privilegios mínimos: ver
`db/00_create_database.sql` (no se ejecuta la aplicación con el superusuario `postgres`).

## 4. Herramientas de desarrollo instaladas en la instancia

```bash
sudo dnf install git -y
sudo dnf install gh -y
sudo dnf install 'dnf-command(config-manager)'
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install npm -y
sudo dnf install nodejs -y
sudo dnf install tree -y
```

## 5. Repositorio y despliegue del código

```bash
ssh-keygen -t ed25519 -C "jose.jauregui@udem.edu"
gh auth login
git clone git@github.com:jricardojauregui/Integracion.git
cd Integracion/apps/web-monolith
npm install
```

---
*Documento generado como parte de la evidencia de la Parte 4 del ejercicio. No contiene
contraseñas, tokens ni llaves privadas.*
