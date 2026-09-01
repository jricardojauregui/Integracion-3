# Tarea 1 — Implementación del clasificador Cloud en Python

**Alumno:** José Ricardo Jáuregui
**Matrícula:** 608995
**Universidad de Monterrey (UDEM)**

---

## 1. Descripción del ejercicio

El objetivo fue reimplementar en Python el clasificador de modelos de servicio en la nube desarrollado previamente en Java, mejorando su arquitectura y aplicando técnicas básicas de procesamiento de lenguaje natural.

La aplicación recibe una descripción escrita en lenguaje natural sobre un servicio de cómputo en la nube y determina a cuál de los cuatro modelos de servicio corresponde:

| Modelo | Significado | Qué describe |
|---|---|---|
| **IaaS** | Infrastructure as a Service | Cómputo, red y almacenamiento virtualizados; el cliente administra el sistema operativo |
| **PaaS** | Platform as a Service | Entorno gestionado para desarrollar y desplegar aplicaciones sin administrar servidores |
| **SaaS** | Software as a Service | Aplicaciones listas para el usuario final, normalmente por suscripción |
| **FaaS** | Function as a Service | Ejecución de funciones disparadas por eventos, sin gestionar servidores |

El requisito central del ejercicio no era solo que clasificara bien, sino que lo hiciera con una **arquitectura correctamente separada**: la interfaz gráfica y la interfaz de línea de comandos debían compartir exactamente la misma lógica, sin duplicar reglas.

Se entregan dos interfaces:

- **GUI** en Tkinter, con captura de nombre y apellido, área de texto, validación, barras de puntaje por modelo y evidencia detectada.
- **CLI** con `argparse`, que cumple el formato solicitado en el enunciado:

```bash
$ python classifier.py --text "ejecutar una función cuando se suba una imagen"
Modelo identificado: FaaS
```

---

## 2. Arquitectura

### 2.1 Diagrama

```
        GUI (gui.py)              CLI (classifier.py)
         Tkinter                      argparse
              \                         /
               \                       /
                v                     v
            cloud_classifier/service.py
              (valida + clasifica)
                        |
          +-------------+-------------+
          |                           |
    validation.py               classifier.py
    (reglas de entrada)         (motor y scoring)
                                      |
                          +-----------+-----------+
                          |                       |
                       nlp.py                knowledge.py
                  (pipeline NLP)        (conceptos + patrones)
                          |                       |
                          +-----------+-----------+
                                      |
                                  models.py
                          (dataclasses y constantes)
```

### 2.2 Responsabilidad de cada módulo

| Archivo | Capa | Responsabilidad |
|---|---|---|
| `gui.py` | Interfaz | Construir y actualizar widgets. Cero lógica de negocio. |
| `classifier.py` (raíz) | Interfaz | Leer argumentos de consola e imprimir. Cero lógica de negocio. |
| `service.py` | Aplicación | Orquesta: valida y luego clasifica. **Único punto de entrada** para ambas interfaces. |
| `validation.py` | Lógica | Reglas de validación de nombre, apellido y descripción. |
| `classifier.py` (paquete) | Lógica | Motor: **cómo** se busca la evidencia y cómo se puntúa. |
| `nlp.py` | Lógica | Pipeline de preprocesamiento de texto. |
| `knowledge.py` | Datos | Base de conocimiento: **qué** se busca (conceptos y patrones). |
| `models.py` | Datos | `dataclasses` y constantes compartidas. |
| `exceptions.py` | Datos | Excepciones propias del dominio. |

### 2.3 Decisiones de arquitectura y por qué

**Separación GUI / lógica mediante una capa de servicio.**
Ni `gui.py` ni `classifier.py` importan `validation` o el motor directamente: ambos llaman a `service.analizar()`. Esto garantiza por construcción que no puedan divergir. Si mañana cambia una regla de validación, se modifica en un solo archivo y las dos interfaces lo heredan automáticamente.

**Separación entre "qué se busca" y "cómo se busca".**
`knowledge.py` contiene solo datos (vocabulario y patrones); `classifier.py` contiene solo el algoritmo. Agregar vocabulario nuevo no requiere tocar el algoritmo, y viceversa. En la versión Java estos dos aspectos vivían en la misma clase.

**Nombre y apellido opcionales en la capa de servicio.**
La práctica pide que la GUI capture nombre y apellido, pero el ejemplo de la CLI solo recibe texto. En lugar de duplicar la función, `analizar()` los acepta como parámetros opcionales: si se envían, se validan; si no, se omiten. Una sola función sirve a ambos casos.

**Excepciones propias en vez de `ValueError` genérico.**
`EntradaInvalidaError` y `ClasificacionError` heredan de `ErrorClasificador`. Esto permite que las interfaces distingan un error de dato (culpa del usuario, se muestra tal cual) de una falla interna (se reporta de otra forma), y que un `except ErrorClasificador` capture ambos cuando conviene.

**Sin dependencias externas.**
Se eligió Tkinter sobre CustomTkinter/PySide y `unittest` sobre pytest para que el proyecto corra con Python estándar, sin `pip install`. El NLP se implementó a mano en vez de usar NLTK o spaCy, que además requerirían descargar corpus.

---

## 3. Código fuente

El código completo está en la carpeta `cloud_classifier_py/`. Estructura:

```
cloud_classifier_py/
├── classifier.py                  CLI (argparse)
├── gui.py                         GUI (Tkinter)
├── cloud_classifier/
│   ├── __init__.py                API pública del paquete
│   ├── models.py                  Dataclasses y constantes
│   ├── exceptions.py              Excepciones del dominio
│   ├── nlp.py                     Pipeline de NLP (6 pasos)
│   ├── knowledge.py               Base de conocimiento
│   ├── classifier.py              Motor de clasificación
│   ├── validation.py              Validación de entradas
│   └── service.py                 Orquestación
├── tests/
│   └── test_classifier.py         31 pruebas
├── DOCUMENTACION.md               Este documento
└── README.md
```

### 3.1 Fragmentos representativos

**Funciones independientes por modelo** (`cloud_classifier/classifier.py`):

```python
def identificar_iaas(texto: TextoProcesado) -> Tuple[int, List[str]]:
    """Evalua que tanto el texto corresponde a Infraestructura como Servicio."""
    return _identificar(texto, IAAS)

def identificar_paas(texto: TextoProcesado) -> Tuple[int, List[str]]:
    """Evalua que tanto el texto corresponde a Plataforma como Servicio."""
    return _identificar(texto, PAAS)

# ... identificar_saas, identificar_faas

IDENTIFICADORES = {
    IAAS: identificar_iaas,
    PAAS: identificar_paas,
    SAAS: identificar_saas,
    FAAS: identificar_faas,
}
```

Se mantienen como funciones públicas separadas (aunque compartan `_identificar`) para poder invocarlas y probarlas de forma aislada, y el diccionario `IDENTIFICADORES` evita encadenar `if/elif` al recorrer las categorías.

**La capa que une GUI y CLI** (`cloud_classifier/service.py`):

```python
def analizar(descripcion, nombre=None, apellido=None) -> Analisis:
    nombre_completo = None
    if nombre is not None or apellido is not None:
        nombre_valido = validation.validar_nombre(nombre or "", "Nombre")
        apellido_valido = validation.validar_nombre(apellido or "", "Apellido")
        nombre_completo = f"{nombre_valido} {apellido_valido}"

    descripcion_valida = validation.validar_descripcion(descripcion)
    resultado = classifier.clasificar(descripcion_valida)
    return Analisis(nombre_completo, descripcion_valida, resultado)
```

**Manejo de errores en la GUI** (`gui.py`):

```python
try:
    analisis = analizar(
        descripcion=self.entrada_descripcion.get("1.0", "end"),
        nombre=self.entrada_nombre.get(),
        apellido=self.entrada_apellido.get(),
    )
    self._mostrar_resultado(analisis)
except EntradaInvalidaError as error:
    messagebox.showwarning("Datos incompletos", str(error))
except ClasificacionError as error:
    messagebox.showerror("Error al clasificar", str(error))
except Exception:
    messagebox.showerror("Error", "Ocurrio un error inesperado. Intenta de nuevo.")
```

**Manejo de errores en la CLI** (`classifier.py`):

```python
except EntradaInvalidaError as error:
    print(f"Entrada invalida: {error}", file=sys.stderr)
    return 2
except ClasificacionError as error:
    print(f"Error al clasificar: {error}", file=sys.stderr)
    return 3
```

Los códigos de salida distintos permiten que un script que invoque la CLI distinga el tipo de fallo.

---

## 4. Explicación del NLP

### 4.1 Los seis pasos

El módulo `nlp.py` implementa cada paso como una función independiente y pura (misma entrada → misma salida, sin efectos secundarios), lo que permite probarlas por separado.

| Paso | Función | Qué hace | Ejemplo |
|---|---|---|---|
| 1 | `a_minusculas()` | Uniforma mayúsculas | `"Máquinas Virtuales"` → `"máquinas virtuales"` |
| 2 | `limpiar()` | Quita puntuación y símbolos | `"hola, mundo!"` → `"hola mundo"` |
| 3 | `tokenizar()` | Separa en palabras | `"una dos"` → `["una","dos"]` |
| 4 | `quitar_stopwords()` | Elimina palabras vacías | `["la","maquina"]` → `["maquina"]` |
| 5 | `normalizar()` | Quita acentos (Unicode NFD) | `"máquina"` → `"maquina"` |
| 6 | `stem()` | Recorta sufijos | `"contenedores"` → `"contenedor"` |

Ejecución real del pipeline (`python classifier.py --text "..." --explicar`):

```
0. Original          Necesito ejecutar una función cuando se suba una imagen
1. Minusculas        necesito ejecutar una función cuando se suba una imagen
2. Limpieza          necesito ejecutar una función cuando se suba una imagen
3. Tokenizacion      ['necesito','ejecutar','una','función','cuando','se','suba','una','imagen']
4. Sin stopwords     ['necesito', 'ejecutar', 'función', 'suba', 'imagen']
5. Normalizacion     ['necesito', 'ejecutar', 'funcion', 'suba', 'imagen']
6. Stemming          ['necesito', 'ejecutar', 'funcion', 'suba', 'imagen']
```

### 4.2 Detalles de implementación que valen la pena

**La limpieza conserva dígitos a propósito.** Un `[^a-z\s]` habría destruido términos reales del dominio: `k8s`, `ec2`, `office 365`. La expresión usada es `[^\w\s]`, que conserva letras y números.

**El stemmer exige una raíz mínima de 4 caracteres.** Sin esa restricción, `"redes"` se convertiría en `"rede"` y luego en algo inútil, y palabras cortas como `"vm"` se destruirían. Se recorta **un solo** sufijo (el más largo que coincida) para evitar *over-stemming*.

**La normalización usa descomposición Unicode NFD**, no un diccionario de reemplazos:

```python
def normalizar(texto):
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
```

Esto separa cada letra de su diacrítico y descarta los diacríticos (categoría `Mn` = *Mark, nonspacing*), lo que funciona para cualquier acento sin listarlos uno por uno.

### 4.3 La decisión más importante: qué NO es stopword

Una lista de stopwords típica en español incluye `sin`, `no`, `ni`, `cada`, `vez`, `que`. **Aquí se excluyeron a propósito**, porque son exactamente la señal que distingue dos de las cuatro categorías:

- *"desplegar mi app **sin administrar** servidores"* → **PaaS** (la negación es el dato)
- *"ejecutar una función **cada vez que** suban un archivo"* → **FaaS** (el disparador es el dato)

Si se eliminaran como palabras vacías, ambas frases perderían justo lo que las define. Hay una prueba automatizada que protege esta decisión:

```python
def test_stopwords_conserva_negaciones(self):
    for palabra in ("sin", "no", "ni", "cada", "vez"):
        self.assertNotIn(palabra, nlp.STOPWORDS)
```

### 4.4 Dos representaciones del mismo texto

Como consecuencia de lo anterior, el pipeline devuelve **dos** versiones del texto (`TextoProcesado`):

| Representación | Cómo se genera | Para qué sirve |
|---|---|---|
| `tokens` | Los 6 pasos completos | Diccionario de conceptos de una sola palabra (`funcion`, `hipervisor`) |
| `texto_para_patrones` | Minúsculas + limpieza + sin acentos, **sin** tokenizar ni quitar stopwords | Expresiones regulares de contexto: frases, marcas, negaciones |

Una bolsa de palabras no puede expresar *"sin administrar servidores"*, porque esa idea depende de que dos palabras aparezcan juntas y en cierto orden. Por eso los patrones se evalúan sobre el texto completo.

### 4.5 Asignación de puntuaciones (scoring)

Cada categoría acumula puntos de dos fuentes:

**A) Conceptos** — palabras sueltas contra la bolsa de tokens. La raíz de cada palabra clave se calcula con la **misma función** `nlp.stem` que procesa el texto del usuario:

```python
raiz = nlp.stem(nlp.normalizar(palabra.lower()))
```

Esto elimina por construcción el error más común de un stemmer artesanal: que alguien escriba la raíz a mano en el diccionario y no coincida con lo que produce el stemmer.

**B) Patrones** — expresiones regulares para frases, marcas (Heroku, AWS Lambda), siglas (CI/CD, VPC) y negaciones.

Escala de pesos:

| Peso | Tipo de evidencia | Ejemplo |
|---|---|---|
| 4 | Negación / contexto muy confiable | `sin administrar servidores` |
| 3 | Término inequívoco | `serverless`, `hipervisor`, `cada vez que` |
| 2 | Término fuerte | `balanceador de carga`, `suscripción` |
| 1 | Contextual (solo apoya) | `cpu`, `contenedor`, `software` |

Gana la categoría con más puntos. La **confianza** es `puntaje_ganador / puntaje_total`. Si ninguna suma, el resultado es *No determinado*; si dos empatan, se marca como ambiguo y se advierte al usuario.

---

## 5. Screenshots

*(Insertar aquí las capturas)*

**Figura 1 — GUI al iniciar.** Formulario vacío con los campos de nombre, apellido y descripción.

**Figura 2 — GUI con clasificación exitosa.** Resultado FaaS al 100%, con barras de puntaje por modelo y las palabras clave detectadas.

**Figura 3 — GUI con error de validación.** `messagebox` de advertencia al intentar clasificar con el campo de nombre vacío.

**Figura 4 — CLI, ejemplo del enunciado.**
```
$ python classifier.py --text "ejecutar una función cuando se suba una imagen"
Modelo identificado: FaaS
```

**Figura 5 — CLI en modo `--verbose`.**
```
$ python classifier.py --text "ejecutar una función cuando se suba una imagen" --verbose
Modelo identificado: FaaS
Funcion como Servicio: ejecucion por eventos, sin gestionar servidores.
Confianza: 100%
Puntajes: {'IaaS': 0, 'PaaS': 0, 'SaaS': 0, 'FaaS': 5}
Evidencia detectada:
  IaaS: (sin coincidencias)
  PaaS: (sin coincidencias)
  SaaS: (sin coincidencias)
  FaaS: funcion, disparador implicito ('cada vez que' / 'cuando se')
```

**Figura 6 — Suite de pruebas.**
```
$ python -m unittest discover -s tests -v
...
Ran 31 tests in 0.236s

OK
```

---

## 6. Tabla de casos de prueba

Los casos evitan usar literalmente las siglas IaaS/PaaS/SaaS/FaaS: describen el servicio en lenguaje natural, como lo haría un usuario real.

| # | Entrada | Resultado esperado | Resultado obtenido | Confianza | ¿Correcto? |
|---|---|---|---|---|---|
| 1 | "Necesito máquinas virtuales, almacenamiento y redes configurables para instalar mi propio sistema operativo" | IaaS | IaaS | 100% | ✔ Correcto |
| 2 | "Quiero desplegar mi aplicación web sin administrar directamente servidores ni sistemas operativos" | PaaS | PaaS | 86% | ✔ Correcto |
| 3 | "Los empleados utilizan una aplicación de correo electrónico directamente desde el navegador y pagan una suscripción mensual" | SaaS | SaaS | 100% | ✔ Correcto |
| 4 | "ejecutar una función cuando se suba una imagen" | FaaS | FaaS | 100% | ✔ Correcto |
| 5 | "Necesito ejecutar una función automáticamente cada vez que un usuario suba una imagen al almacenamiento Cloud" | FaaS | FaaS | 100% | ✔ Correcto |
| 6 | "Necesitamos rentar servidores dedicados con acceso root para instalar nuestro propio hipervisor" | IaaS | IaaS | 100% | ✔ Correcto |
| 7 | "Buscamos un entorno donde subir nuestro código y que la plataforma se encargue del runtime y el escalado automático" | PaaS | PaaS | 100% | ✔ Correcto |
| 8 | "Quiero un espacio de trabajo colaborativo con hojas de cálculo y videollamadas, pagando una mensualidad por usuario" | SaaS | SaaS | 100% | ✔ Correcto |
| 9 | "Todavía no sé qué necesito, quiero algo relacionado con la nube" | No determinado | No determinado | 0% | ✔ Correcto |

**Resultado global: 9 / 9 correctos.**

El caso 9 se incluyó a propósito para verificar que el clasificador **no adivina**: ante un texto sin señales técnicas, responde *No determinado* en vez de forzar una categoría.

### 6.1 Pruebas automatizadas adicionales

Además de los 9 casos de clasificación, la suite (`tests/test_classifier.py`) incluye **31 pruebas** en total:

| Grupo | Qué verifica |
|---|---|
| `PruebasClasificacion` | Los 9 casos, rango de confianza, funciones identificadoras independientes |
| `PruebasNLP` | Cada paso del pipeline por separado, incluida la regla de negaciones |
| `PruebasValidacion` | Nombres vacíos, con números, con acentos, compuestos; descripciones corta/larga |
| `PruebasCLI` | Ejecuta la CLI como proceso externo y verifica salida y códigos de retorno |
| `PruebasErrores` | Que una falla interna se envuelva en `ClasificacionError` y no escape cruda |

```
Ran 31 tests in 0.204s

OK
```

---

## 7. Errores encontrados

### 7.1 Heredados de la versión en Java (corregidos antes de portar)

**Error 1 — "aplicación web" clasificaba como SaaS lo que era PaaS.**
La frase *"desplegar mi aplicación web sin administrar servidores"* devolvía SaaS. Causa: una regla de SaaS hacía match con `aplicación web`, y cualquier app que se despliega también es una "aplicación web", así que competía injustamente con PaaS.
**Corrección:** se eliminó esa regla por demasiado genérica y se conservó solo la señal fuerte (`aplicación lista para usar`).

**Error 2 — La negación no se detectaba si había una palabra en medio.**
El patrón de PaaS exigía `sin administrar servidores` con las palabras pegadas, así que *"sin administrar **directamente** servidores"* no coincidía.
**Corrección:** se introdujo un comodín acotado `.{0,40}` entre la negación y el sustantivo, que tolera palabras intermedias sin volverse tan permisivo como para producir falsos positivos.

**Error 3 — FaaS no se detectaba sin las palabras "evento" o "trigger".**
El texto *"ejecutar una función cada vez que suban una imagen"* devolvía *No determinado*, porque describe un disparador sin nombrarlo.
**Corrección:** se agregaron `cada vez que`, `en cuanto` y `cuando se` como sinónimos de disparador implícito. Este fue justamente el caso del ejemplo del enunciado de esta tarea.

### 7.2 Encontrados durante la implementación en Python

**Error 4 — La limpieza destruía términos con dígitos.**
El primer intento usaba una expresión que eliminaba todo lo no alfabético, lo que convertía `k8s` en `ks` y `office 365` en `office`.
**Corrección:** se cambió a `[^\w\s]`, que conserva letras y dígitos. Quedó cubierto por la prueba `test_limpieza_conserva_digitos`.

**Error 5 — Riesgo de desajuste entre el diccionario y el stemmer.**
En la versión Java las palabras clave se escribían ya "en raíz" a mano. Eso es frágil: si alguien escribe la raíz equivocada, esa palabra clave nunca coincide y el fallo es silencioso (no hay error, simplemente no clasifica).
**Corrección:** en Python el diccionario se escribe con palabras normales y la raíz se deriva automáticamente al importar el módulo, aplicando la misma función `stem` que procesará el texto del usuario. Por construcción no puede haber desajuste.

**Error 6 — Sobre-recorte del stemmer en palabras cortas.**
La primera versión del stemmer convertía `redes` → `red` → y con otro paso hubiera seguido recortando. También destruía tokens de 2-3 letras.
**Corrección:** se recorta **un solo** sufijo por token y se exige que la raíz resultante tenga al menos 4 caracteres. Cubierto por `test_stemming_no_destruye_palabras_cortas`.

**Error 7 — Los patrones no coincidían tras la limpieza.**
Patrones escritos como `ci/?cd` o `multi-?tenant` dejaron de funcionar, porque el pipeline ya había convertido `/` y `-` en espacios antes de que las regex se evaluaran. El texto llegaba como `ci cd`.
**Corrección:** los separadores se reescribieron como espacio opcional (`ci ?cd`, `multi ?tenant`). Fue un error sutil porque no rompía nada visiblemente: simplemente esas reglas nunca activaban.

### 7.3 Sobre la validación de nombres

La expresión regular inicial `^[\p{L} '-]+$` no existe tal cual en el módulo `re` de Python (`\p{L}` es sintaxis de Java/PCRE). Se reescribió usando `[^\W\d_]` con la bandera `re.UNICODE`, que en Python significa "carácter alfanumérico que no sea dígito ni guion bajo", es decir, una letra — incluyendo acentuadas y `ñ`. Verificado con `test_nombre_con_acentos_es_valido`.

---

## 8. Mejoras realizadas respecto a la versión en Java

| # | Mejora | Beneficio |
|---|---|---|
| 1 | **Capa de servicio** (`service.py`) como único punto de entrada | Garantiza por construcción que GUI y CLI no puedan divergir |
| 2 | **Separación datos / algoritmo** (`knowledge.py` vs `classifier.py`) | Agregar vocabulario no requiere tocar el motor |
| 3 | **Raíces derivadas automáticamente** en el diccionario | Elimina una clase entera de bugs silenciosos |
| 4 | **Jerarquía de excepciones** con clase base común | Permite capturar todos los errores del dominio con un solo `except` |
| 5 | **`dataclasses` en vez de diccionarios sueltos** | Tipos explícitos y autodocumentados entre capas |
| 6 | **Suite de 31 pruebas** (vs. 9 casos en Java) | Cubre NLP paso a paso, validación, errores e integración de la CLI |
| 7 | **Modo `--explicar` en la CLI** | Muestra el pipeline de NLP paso a paso; útil para depurar y documentar |
| 8 | **Salida `--json`** | Permite usar el clasificador desde otros scripts |
| 9 | **Códigos de salida diferenciados** (2 = dato inválido, 3 = falla interna) | Un script que invoque la CLI puede reaccionar distinto según el fallo |
| 10 | **Precompilación de regex** al importar | Se compilan una sola vez en vez de en cada clasificación |
| 11 | **`set` para búsqueda de conceptos** | Buscar cada concepto es O(1) en lugar de recorrer la lista de tokens |
| 12 | **Cero dependencias externas** | El proyecto corre con Python estándar, sin `pip install` |

---

## 9. Conclusiones

**Sobre la arquitectura.** El requisito de que GUI y CLI compartieran lógica resultó ser el más formativo del ejercicio. La solución ingenua —copiar las funciones de clasificación a ambos archivos— habría funcionado el primer día y se habría roto en la primera modificación. Introducir una capa de servicio como único punto de entrada convierte esa garantía en algo estructural: no depende de que uno recuerde actualizar los dos lados, porque solo hay un lado. La prueba concreta es que agregar `--json` y `--explicar` a la CLI no requirió tocar ni una línea de la lógica de clasificación.

**Sobre el NLP.** El hallazgo más interesante fue descubrir que **aplicar un paso estándar del pipeline puede destruir información esencial**. Eliminar stopwords es lo que "se debe hacer", pero en este dominio `sin`, `no` y `cada vez que` no son ruido: son precisamente lo que distingue PaaS de IaaS y lo que identifica a FaaS. Esto obligó a mantener dos representaciones paralelas del texto —bolsa de tokens para conceptos sueltos, texto completo para patrones de contexto— y a proteger la decisión con una prueba automatizada, porque es exactamente el tipo de detalle que alguien "corregiría" más adelante sin entender por qué estaba así.

**Sobre las limitaciones del enfoque.** Un clasificador basado en reglas y palabras clave es transparente y depurable: siempre se puede señalar exactamente qué disparó cada punto, algo que la GUI muestra explícitamente. Pero sus límites son estructurales:

- No entiende negaciones arbitrarias. Se cubrieron los patrones más comunes, pero *"no quiero máquinas virtuales"* sigue sumando puntos a IaaS.
- No detecta sinónimos fuera del diccionario. Cada forma de decir lo mismo debe agregarse a mano.
- Los pesos se asignaron por criterio propio, no aprendidos de datos, así que no hay garantía de que sean óptimos.

Estas tres limitaciones apuntan al mismo lugar: son el argumento natural para pasar a un clasificador entrenado con datos etiquetados o a un modelo de lenguaje, que generalizaría a formas de expresión no previstas. La contrapartida es que se perdería la trazabilidad —poder decir exactamente por qué el sistema respondió lo que respondió—, que en un ejercicio didáctico es justamente lo más valioso.

**Sobre Java vs Python.** Portar el proyecto expuso diferencias que no son solo de sintaxis. Las `dataclasses` eliminaron el código repetitivo de getters y setters; las tuplas como valor de retorno permitieron que las funciones identificadoras devolvieran puntaje y evidencia sin necesidad de una clase contenedora; y la construcción del índice de conceptos al importar el módulo no tiene un equivalente igual de directo en Java. En sentido contrario, el sistema de tipos de Java detectaba en tiempo de compilación errores que en Python solo aparecen al ejecutar —lo cual hizo que la suite de pruebas pasara de ser un extra a ser una necesidad real.
