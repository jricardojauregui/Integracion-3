# cloud_classifier — versión Python

Clasificador de modelos de servicio en la nube (**IaaS / PaaS / SaaS / FaaS**) a partir de una descripción en lenguaje natural. Incluye **GUI (Tkinter)** y **CLI (argparse)**, ambas sobre la misma lógica de clasificación.

Reimplementación en Python del clasificador desarrollado originalmente en Java, aplicando separación de responsabilidades, NLP básico y reutilización de componentes.

## Requisitos

- Python 3.8 o superior
- **Sin dependencias externas** (solo biblioteca estándar)

`tkinter` viene incluido en la mayoría de instalaciones de Python. Si te falta:
- Ubuntu/Debian: `sudo apt install python3-tk`
- macOS (Homebrew): `brew install python-tk`
- Windows: viene incluido en el instalador oficial

## Uso

**GUI**
```bash
python gui.py
```

**CLI**
```bash
python classifier.py --text "ejecutar una función cuando se suba una imagen"
# Modelo identificado: FaaS
```

Opciones adicionales de la CLI:
```bash
python classifier.py --text "..." --verbose    # confianza, puntajes y evidencia
python classifier.py --text "..." --explicar   # muestra el pipeline de NLP paso a paso
python classifier.py --text "..." --json       # salida en JSON
python classifier.py --help
```

**Pruebas**
```bash
python -m unittest discover -s tests -v
```
31 pruebas: clasificación, pipeline de NLP, validación, manejo de errores e integración de la CLI.

## Arquitectura

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

La GUI y la CLI **no contienen ni una regla de clasificación**: ambas llaman a `service.analizar()`. Cambiar una regla o un paso del pipeline se hace en un solo lugar y las dos interfaces lo heredan.

```
cloud_classifier_py/
├── classifier.py                  CLI (argparse)
├── gui.py                         GUI (Tkinter)
├── cloud_classifier/
│   ├── __init__.py                API pública del paquete
│   ├── models.py                  Dataclasses y constantes
│   ├── exceptions.py              Excepciones del dominio
│   ├── nlp.py                     Pipeline de NLP (6 pasos)
│   ├── knowledge.py               Base de conocimiento (QUÉ se busca)
│   ├── classifier.py              Motor de clasificación (CÓMO se puntúa)
│   ├── validation.py              Validación de entradas
│   └── service.py                 Orquestación (validación + clasificación)
├── tests/
│   └── test_classifier.py         31 pruebas (unittest)
├── DOCUMENTACION.md               Reporte de la práctica
└── README.md
```

## Pipeline de NLP

`nlp.py` aplica seis pasos, cada uno como función independiente y pura:

1. **Conversión a minúsculas**
2. **Limpieza** — quita puntuación y símbolos (conserva dígitos para no romper `k8s`, `office 365`)
3. **Tokenización**
4. **Eliminación de stopwords**
5. **Normalización** — quita acentos (`máquina` → `maquina`)
6. **Stemming** ligero — agrupa variantes (`funciones` → `funcion`)

Ejemplo real (`python classifier.py --text "..." --explicar`):

```
0. Original          Necesito ejecutar una función cuando se suba una imagen
1. Minusculas        necesito ejecutar una función cuando se suba una imagen
2. Limpieza          necesito ejecutar una función cuando se suba una imagen
3. Tokenizacion      ['necesito','ejecutar','una','función','cuando','se','suba','una','imagen']
4. Sin stopwords     ['necesito', 'ejecutar', 'función', 'suba', 'imagen']
5. Normalizacion     ['necesito', 'ejecutar', 'funcion', 'suba', 'imagen']
6. Stemming          ['necesito', 'ejecutar', 'funcion', 'suba', 'imagen']
```

**Decisión clave:** la lista de stopwords **no** incluye negaciones (`sin`, `no`, `ni`) ni palabras de disparador (`cada`, `vez`, `que`), porque son justo la señal que distingue PaaS (*"sin administrar servidores"*) y FaaS (*"cada vez que"*). Por eso el motor conserva **dos representaciones** del texto: la bolsa de tokens (para conceptos sueltos) y el texto completo sin tokenizar (para patrones de contexto).

## Cómo clasifica

Cada categoría suma dos fuentes de evidencia:

- **Conceptos** (`knowledge.CONCEPTOS`): palabras sueltas comparadas contra los tokens ya procesados. La raíz de cada palabra clave se calcula con la misma función `nlp.stem` que procesa el texto del usuario, así que nunca hay desajuste.
- **Patrones** (`knowledge.PATRONES`): expresiones regulares sobre el texto completo, para frases, marcas (Heroku, AWS Lambda), siglas (CI/CD, VPC) y sobre todo **negaciones**, que una bolsa de palabras no puede expresar.

Gana la categoría con más puntos. La confianza es `puntaje_ganador / puntaje_total`. Si nadie suma, el resultado es *No determinado*; si dos empatan, se marca como ambiguo.

## Resultados de las pruebas

| # | Entrada (resumida) | Esperado | Obtenido | Correcto |
|---|---|---|---|---|
| 1 | máquinas virtuales, almacenamiento, redes configurables, instalar mi propio SO | IaaS | IaaS (100%) | ✔ |
| 2 | desplegar mi app web sin administrar directamente servidores ni SO | PaaS | PaaS (86%) | ✔ |
| 3 | correo electrónico desde el navegador, suscripción mensual | SaaS | SaaS (100%) | ✔ |
| 4 | ejecutar una función cuando se suba una imagen | FaaS | FaaS (100%) | ✔ |
| 5 | ejecutar una función cada vez que suban una imagen al almacenamiento | FaaS | FaaS (100%) | ✔ |
| 6 | servidores dedicados, acceso root, hipervisor propio | IaaS | IaaS (100%) | ✔ |
| 7 | subir código, la plataforma gestiona runtime y escalado automático | PaaS | PaaS (100%) | ✔ |
| 8 | espacio colaborativo, hojas de cálculo, mensualidad por usuario | SaaS | SaaS (100%) | ✔ |
| 9 | "todavía no sé qué necesito, algo relacionado con la nube" | No determinado | No determinado | ✔ |

**9/9 correctos.** Ver `DOCUMENTACION.md` para el detalle completo.

## Manejo de errores

| Situación | GUI | CLI |
|---|---|---|
| Nombre/apellido vacío o con números | `messagebox` de advertencia | (no aplica) |
| Descripción vacía o < 8 caracteres | `messagebox` de advertencia | stderr + código de salida `2` |
| Falla interna del motor | `messagebox` de error | stderr + código de salida `3` |
| Falta `--text` | (no aplica) | argparse + código `2` |

Ninguna de las dos interfaces muestra un traceback crudo al usuario.

## Limitaciones conocidas

- El stemmer es heurístico, no un stemmer real de español (tipo Snowball). Variantes como `invocar`/`invocación` no se unifican automáticamente, por lo que se listan explícitamente en el diccionario.
- El manejo de negaciones cubre los patrones más comunes (`sin administrar...`), no negaciones arbitrarias.
- Los pesos se asignan manualmente, no se aprenden de datos.
