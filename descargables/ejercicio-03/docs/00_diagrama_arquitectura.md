# Paso 3: Macro-arquitectura

El diagrama se generó de forma interactiva en la conversación con Claude
(Visualizer). Flujo representado:

App de escritorio (Electron, cliente SOAP)
  --HTTP POST /soap (XML)-->
Módulo SOAP (Flask, Envelope armado a mano)
  --psycopg2-->
PostgreSQL (compartido)

En paralelo, e independiente, el Monolito Node.js sigue accediendo a
PostgreSQL vía su driver `pg` directo, sin relación directa con el
módulo SOAP -- el único punto de contacto es la base de datos compartida.

Fronteras y responsabilidades:
- Monolito Node.js (gris): dueño de la lógica web y del acceso directo a
  PostgreSQL. No se toca en esta etapa.
- App de escritorio (morado): dueña de la interacción con el usuario y
  de armar/enviar el sobre SOAP por HTTP POST.
- Módulo SOAP en Flask (verde): dueño de parsear el Envelope a mano,
  ejecutar la lógica de negocio y hablar con la base vía psycopg2.
- PostgreSQL (azul): recurso compartido, ambos procesos independientes.
