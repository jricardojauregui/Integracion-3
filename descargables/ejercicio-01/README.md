# cloud_models_classifier

Aplicación que analiza una descripción escrita por el usuario y determina si corresponde principalmente a **IaaS**, **PaaS**, **SaaS** o **FaaS**. Disponible como interfaz gráfica (Swing) **y** como línea de comandos (CLI), ambas sobre la misma lógica.

**Versión 3:** pipeline de NLP básico + diccionario de conceptos + patrones de contexto (regex) para frases/negaciones/marcas, arquitectura por capas, validación de entradas, manejo de excepciones y una CLI que reutiliza el mismo motor que la GUI.

## Arquitectura

```
   GUI (Swing)                    CLI (consola)
MainFrame -> ClasificadorController     |
        \                               |
         \                              |
          v                             v
        CloudServiceClassifier.clasificar(texto)
                    |
                    v
        Preprocesador (pipeline NLP)
                    |
                    v
   Diccionario de conceptos + Patrones de contexto (regex)
                    |
                    v
         ResultadoClasificacion
        (IaaS | PaaS | SaaS | FaaS)
```

La GUI y la CLI son dos **entradas** distintas que terminan llamando exactamente al mismo método `CloudServiceClassifier.clasificar(String)`. Ninguna regla de clasificación está duplicada entre ambas.

## Estructura del proyecto

```
cloud_models_classifier/
├── pom.xml                     (opcional, para IntelliJ / Maven)
├── run.sh / run.bat            compilar y ejecutar la GUI
├── run-cli.sh / run-cli.bat    compilar y ejecutar la CLI
├── run-tests.sh                compilar y correr la bateria de pruebas
├── src/main/java/
│   ├── CloudClassifier.java               CLI (paquete por defecto, ver "Como ejecutar")
│   └── com/udem/cloud/
│       ├── Main.java                          Punto de entrada de la GUI
│       ├── ui/
│       │   ├── MainFrame.java                 GUI pura (Swing) — sin reglas de negocio
│       │   └── ClasificadorController.java    Conecta la GUI con la capa de logica
│       ├── logica/
│       │   ├── Preprocesador.java             Pipeline de NLP (6 pasos)
│       │   ├── DiccionarioConceptos.java      Diccionario stem→peso (auto-derivado)
│       │   ├── CloudServiceClassifier.java    Motor de clasificacion (4 metodos independientes)
│       │   ├── ValidadorEntrada.java          Validacion de nombre/apellido/descripcion
│       │   ├── EntradaInvalidaException.java  Excepcion de validacion
│       │   └── ClasificacionException.java    Excepcion del motor de clasificacion
│       └── model/
│           ├── Regla.java                     Regex + peso + etiqueta (patrones de contexto)
│           ├── TextoProcesado.java             Salida del pipeline de NLP
│           └── ResultadoClasificacion.java    Resultado (modelo, puntajes, confianza)
└── src/test/java/com/udem/cloud/
    └── PruebasClasificador.java               9 casos de prueba (incluye los 4 de la practica)
```

## Como ejecutar

**GUI**

```bash
./run.sh          # Linux / macOS
run.bat           # Windows
```

**CLI**

```bash
./run-cli.sh "máquinas virtuales almacenamiento redes"
# Modelo identificado: IaaS

./run-cli.sh -v "sin administrar servidores, solo despliego mi código"
# Modelo identificado: PaaS
# Confianza: 100%
# Puntajes: {IaaS=0, PaaS=6, SaaS=0, FaaS=0}
# ...
```

En Windows: `run-cli.bat "máquinas virtuales almacenamiento redes"`

Manual (sin script), en cualquier sistema:
```bash
javac -encoding UTF-8 -d out $(find src/main -name "*.java")
java -Dfile.encoding=UTF-8 -cp out CloudClassifier "máquinas virtuales almacenamiento redes"
java -Dfile.encoding=UTF-8 -cp out com.udem.cloud.Main   # para la GUI
```

> **Nota sobre acentos en la CLI:** si tu terminal no usa UTF-8 (poco comun, pero pasa en algunos Linux/CI), los acentos del argumento pueden llegar corruptos a Java y arruinar la clasificacion. Los scripts `run-cli.sh` / `run-cli.bat` ya fuerzan UTF-8 por ti; si ejecutas el comando manual y ves resultados raros con texto acentuado, agrega `LANG=C.UTF-8 LC_ALL=C.UTF-8` antes de `java`.

**Pruebas (sin GUI ni CLI)**

```bash
./run-tests.sh
```

## Pipeline de NLP

`Preprocesador` aplica, en este orden, los pasos que pide la practica:

1. **Conversion a minusculas**
2. **Limpieza de texto** (quita puntuacion; conserva letras/digitos para no romper cosas como "k8s" u "office 365")
3. **Tokenizacion** (separa en palabras)
4. **Eliminacion de stopwords** (articulos, preposiciones, pronombres...)
5. **Normalizacion** (quita acentos de cada token)
6. **Stemming** ligero (agrupa variantes de una raiz: "funciones"→"funcion", "contenedores"→"contenedor")

Ejemplo real (`Preprocesador` paso a paso):

```
Original:         Necesito ejecutar Funciones automáticamente, sin servidores, cada vez que suban un archivo.
1. Minúsculas:     necesito ejecutar funciones automáticamente, sin servidores, cada vez que suban un archivo.
2. Limpieza:       necesito ejecutar funciones automáticamente sin servidores cada vez que suban un archivo
3. Tokenización:   [necesito, ejecutar, funciones, automáticamente, sin, servidores, cada, vez, que, suban, un, archivo]
4. Sin stopwords:  [necesito, ejecutar, funciones, automáticamente, sin, servidores, cada, vez, suban, archivo]
5. Normalizados:   [necesito, ejecutar, funciones, automaticamente, sin, servidores, cada, vez, suban, archivo]
6. Stemming:       [necesito, ejecutar, funcion, automatic, sin, servidor, cada, vez, suban, archivo]
```

**Decision de diseño importante:** la lista de stopwords **no** incluye palabras de negacion ("sin", "no", "ni") ni las que forman disparadores ("cada", "vez", "que"). Si las quitaramos, perderiamos justo la señal que el clasificador necesita para detectar frases como *"sin administrar servidores"* (PaaS) o *"cada vez que"* (FaaS). Por eso el motor de clasificacion usa **dos representaciones** del mismo texto:

- **Bolsa de tokens con stemming** (pasos 1-6 completos) → para el diccionario de conceptos de una sola palabra (`funcion`, `contenedor`, `hipervisor`...).
- **Texto completo normalizado, sin tokenizar ni quitar stopwords** → para los patrones de contexto (regex) que necesitan el orden original de las palabras: frases, marcas conocidas (Heroku, AWS Lambda), siglas (CI/CD) y sobre todo negaciones.

## Como funciona la clasificacion (identificacion de conceptos + scoring)

Cada categoria (`identificarIaaS`, `identificarPaaS`, `identificarSaaS`, `identificarFaaS`) suma dos fuentes de puntaje:

- **A) Diccionario de conceptos** (`DiccionarioConceptos`): compara la bolsa de tokens ya con stemming contra palabras clave de una sola palabra (ej. "hipervisor", "middleware", "software", "funcion", "evento"). La raiz de cada palabra del diccionario se calcula con la **misma funcion** `Preprocesador.stem` que procesa el texto del usuario, asi que nunca hay un desajuste entre "como se guardo la palabra clave" y "como llego la palabra del usuario".
- **B) Patrones de contexto** (regex): frases, marcas y negaciones que no se pueden expresar como una sola palabra suelta.

`clasificar(texto)` ejecuta las cuatro identificaciones y compara puntajes: gana quien sume mas. La confianza es `puntaje_ganador / puntaje_total`. Si nadie suma puntos, el resultado es *No determinado*; si dos empatan, se marca como ambiguo.

## Casos de prueba (5+, sin usar las siglas literales)

Ejecutados por `PruebasClasificador` — **9/9 pasan**.

| # | Descripcion | Esperado | Obtenido |
|---|---|---|---|
| A | "Necesito máquinas virtuales, almacenamiento y redes configurables para instalar mi propio sistema operativo" | IaaS | IaaS (100%) |
| B | "Quiero desplegar mi aplicación web sin administrar directamente servidores ni sistemas operativos" | PaaS | PaaS (86%) |
| C | "Los empleados utilizan una aplicación de correo electrónico directamente desde el navegador y pagan una suscripción mensual" | SaaS | SaaS (100%) |
| D | "Necesito ejecutar una función automáticamente cada vez que un usuario suba una imagen al almacenamiento Cloud" | FaaS | FaaS (100%) |
| E | Espacio colaborativo con hojas de cálculo y videollamadas, acceso con usuario/contraseña, mensualidad | SaaS | SaaS (100%) |
| F | Servidores dedicados, acceso root, hipervisor propio | IaaS | IaaS (100%) |
| G | Subir código y que la plataforma administre runtime/balanceo/autoescalado | PaaS | PaaS (100%) |
| H | Procesar y generar miniatura "en cuanto" el cliente suba una imagen, pago por ejecución | FaaS | FaaS (100%) |
| I | "Todavía no sé qué necesito, quiero algo relacionado con la nube" | No determinado | No determinado |

Tambien verificado via CLI con el ejemplo exacto de la practica:
```
$ ./run-cli.sh "máquinas virtuales almacenamiento redes"
Modelo identificado: IaaS
```

## Validacion de entradas y manejo de errores

- `ValidadorEntrada` rechaza nombre/apellido vacios, con numeros/simbolos, o fuera de rango de longitud; y descripciones vacias, demasiado cortas (<8 caracteres) o demasiado largas (>2000). La GUI valida nombre + apellido + descripcion; la CLI solo valida la descripcion (no pide identidad, igual que en el ejemplo de uso de la practica).
- Los errores de validacion (`EntradaInvalidaException`) y los del motor de clasificacion (`ClasificacionException`) son excepciones **verificadas** (checked): el compilador obliga a manejarlas.
- La GUI captura ambas y muestra un `JOptionPane`; la CLI las captura e imprime a `stderr` con codigo de salida `1`. Ninguna de las dos se cae ni muestra un stack trace crudo al usuario.

## Limitaciones que quedan (a proposito, para la siguiente iteracion)

- El stemmer es heuristico, no un stemmer real de español (tipo Snowball): para un par de palabras (p. ej. "invocar"/"invocación", "trigger"/"triggers") no unifica la raiz automaticamente, asi que esas variantes se listan explicitamente en el diccionario en vez de depender del stemmer.
- Sigue sin entender negaciones en general — solo se cubrieron los patrones mas comunes ("sin administrar...") via regex, no negaciones arbitrarias.
- Los pesos siguen siendo asignados manualmente, no aprendidos de datos.

Estas limitaciones son el punto natural de mejora para una siguiente version con un modelo de aprendizaje automatico o un LLM.
