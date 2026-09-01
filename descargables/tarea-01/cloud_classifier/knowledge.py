"""
Base de conocimiento del clasificador: QUE se busca en el texto.

Se separa del motor (classifier.py, que define COMO se busca y se puntua)
para que agregar vocabulario nuevo no implique tocar el algoritmo.

Hay dos tipos de evidencia por categoria:

A) CONCEPTOS: palabras sueltas. Se comparan contra la bolsa de tokens que
   produce el pipeline de NLP (ya en minusculas, sin acentos y con
   stemming). La raiz de cada palabra clave se calcula AQUI con la misma
   funcion ``nlp.stem`` que procesa el texto del usuario, asi que por
   construccion nunca hay desajuste entre "como guarde la palabra clave" y
   "como llego la palabra del usuario". Esto evita el error tipico de
   escribir la raiz a mano y equivocarse.

B) PATRONES: expresiones regulares sobre el texto completo. Son para lo
   que un diccionario de una sola palabra NO puede expresar:
     - frases        ("almacenamiento en bloque")
     - marcas        ("heroku", "aws lambda")
     - siglas        ("ci cd", "vpc")
     - NEGACIONES    ("sin administrar servidores")  <- la mas importante
   Una negacion depende de que dos palabras aparezcan juntas y en cierto
   orden, algo imposible de capturar con una bolsa de palabras.

Pesos: 4 = negacion/contexto muy confiable | 3 = especifico | 2 = fuerte |
1 = contextual (solo suma como apoyo).

Nota tecnica sobre los patrones: el texto que reciben ya paso por la
limpieza del pipeline, donde la puntuacion se convirtio en espacios. Por eso
los separadores se escriben como espacio opcional (" ?") en vez de "-?" o
"/?": "ci/cd" llega a los patrones como "ci cd".
"""

import re
from typing import Dict, List, Tuple

from . import nlp
from .models import FAAS, IAAS, PAAS, SAAS

# ---------------------------------------------------------------------------
# A) CONCEPTOS (palabra -> peso)
# ---------------------------------------------------------------------------
# Se escriben en espanol normal; la raiz se deriva automaticamente abajo.
CONCEPTOS_CRUDOS: Dict[str, List[Tuple[Tuple[str, ...], int]]] = {
    IAAS: [
        (("hipervisor", "hypervisor"), 3),
        (("infraestructura",), 1),
        (("cpu", "ram", "memoria", "disco", "discos", "storage"), 1),
    ],
    PAAS: [
        (("middleware",), 2),
        (("contenedor", "contenedores", "docker"), 1),
    ],
    SAAS: [
        (("software", "aplicacion", "aplicaciones"), 1),
    ],
    FAAS: [
        (("funcion", "funciones"), 2),
        (("evento", "eventos"), 2),
        (("disparador", "disparadores"), 2),
        # "trigger(s)" e "invocar/invocacion" se listan explicitamente porque
        # el stemmer esta pensado para espanol y no unifica estas variantes
        # a una misma raiz.
        (("trigger", "triggers"), 2),
        (("invocacion", "invocaciones", "invocar"), 2),
    ],
}


def _construir_indice_conceptos() -> Dict[str, Dict[str, Tuple[int, str]]]:
    """
    Convierte CONCEPTOS_CRUDOS en {categoria: {raiz: (peso, etiqueta)}}.

    La raiz se obtiene aplicando el MISMO preprocesamiento (normalizar +
    stem) que se aplicara al texto del usuario.
    """
    indice: Dict[str, Dict[str, Tuple[int, str]]] = {}
    for categoria, grupos in CONCEPTOS_CRUDOS.items():
        mapa: Dict[str, Tuple[int, str]] = {}
        for palabras, peso in grupos:
            for palabra in palabras:
                raiz = nlp.stem(nlp.normalizar(palabra.lower()))
                # Si una raiz se repite, se conserva el peso mayor.
                if raiz not in mapa or mapa[raiz][0] < peso:
                    mapa[raiz] = (peso, palabra)
        indice[categoria] = mapa
    return indice


CONCEPTOS = _construir_indice_conceptos()


# ---------------------------------------------------------------------------
# B) PATRONES DE CONTEXTO (regex, peso, etiqueta legible)
# ---------------------------------------------------------------------------
PATRONES_CRUDOS: Dict[str, List[Tuple[str, int, str]]] = {
    IAAS: [
        (r"\biaas\b", 3, "IaaS"),
        (r"\binfraestructura como servicio\b", 3, "infraestructura como servicio"),
        (r"\binfrastructure as a service\b", 3, "infrastructure as a service"),
        (r"\bmaquinas? virtuales?\b|\bvirtual machines?\b|\bvms?\b", 3, "maquina virtual / VM"),
        (r"\bec2\b|\bcompute engine\b|\bazure vm\b|\bdroplet\b", 3, "servicio de computo (EC2 / Compute Engine)"),
        (r"\bbare metal\b|\bservidor(?:es)? (?:fisico|dedicado)s?\b", 3, "bare metal / servidor dedicado"),
        # Instalar tu propio sistema operativo = control total tipico de IaaS.
        (r"\binstalar\b.{0,30}\bsistemas? +operativos?\b", 3, "instalar tu propio sistema operativo"),
        (r"\bservidor(?:es)? virtual(?:es)?\b", 2, "servidor virtual"),
        (r"\balmacenamiento (?:en )?bloque\b|\bblock storage\b|\bebs\b", 2, "almacenamiento en bloque"),
        (r"\bred(?:es)? (?:virtual(?:es)?|configurables?)\b|\bvpc\b|\bsubred(?:es)?\b|\bvlan\b", 2, "red virtual / configurable / VPC"),
        (r"\bbalanceador de carga\b|\bload balancer\b", 2, "balanceador de carga"),
        (r"\bfirewall\b|\bgrupo de seguridad\b|\bsecurity group\b", 2, "firewall / grupo de seguridad"),
        (r"\bopenstack\b|\bvmware\b|\bvsphere\b|\bproxmox\b", 2, "plataforma de virtualizacion"),
        (r"\bsistema operativo\b|\bimagen del sistema\b|\bami\b", 1, "sistema operativo / imagen"),
        (r"\bsnapshots?\b|\bcopia de seguridad\b|\bbackup\b", 1, "snapshot / backup"),
        (r"\bescalamiento vertical\b|\bredimensionar\b", 1, "escalamiento vertical"),
        (r"\badministrar el servidor\b|\bcontrol total\b|\bacceso root\b|\bssh\b", 1, "administracion del servidor"),
    ],
    PAAS: [
        (r"\bpaas\b", 3, "PaaS"),
        (r"\bplataforma como servicio\b", 3, "plataforma como servicio"),
        (r"\bplatform as a service\b", 3, "platform as a service"),
        (r"\bheroku\b|\bapp engine\b|\belastic beanstalk\b|\bapp service\b|\bopenshift\b|\bcloud foundry\b|\brailway\b", 3, "plataforma gestionada (Heroku / App Engine / etc.)"),
        (r"\bbuildpacks?\b|\bruntime gestionado\b", 3, "buildpack / runtime gestionado"),
        # EL PATRON MAS IMPORTANTE DEL MOTOR: es la forma natural en que la
        # gente describe PaaS sin usar la sigla. El comodin .{0,40} tolera
        # palabras intermedias como "directamente".
        (r"\b(?:sin|no)\b.{0,40}\b(?:administrar|gestionar|preocuparte por|preocuparse por)\b.{0,40}\b(?:servidor(?:es)?|infraestructura|sistemas? +operativos?)\b",
         4, "sin administrar servidores/infraestructura/SO (abstraccion tipica de PaaS)"),
        (r"\bentorno de (?:ejecucion|desarrollo)\b|\bruntime\b", 2, "entorno de ejecucion"),
        (r"\bdesplegar\b|\bdespliegue\b|\bdeploy(?:ar|ment)?\b", 2, "despliegue de aplicaciones"),
        (r"\bci ?cd\b|\bpipelines?\b|\bintegracion continua\b", 2, "CI/CD"),
        (r"\bkubernetes\b|\bk8s\b|\baks\b|\beks\b|\bgke\b|\borquestacion de contenedores\b", 2, "orquestacion gestionada"),
        (r"\bbase de datos (?:gestionada|administrada)\b|\brds\b|\bcloud sql\b", 2, "base de datos gestionada"),
        (r"\bframeworks?\b|\bsdk\b|\bapis? de desarrollo\b", 1, "framework / SDK"),
        (r"\bdesarrollador(?:es)?\b|\bequipo de desarrollo\b", 1, "enfoque en desarrolladores"),
        (r"\bescalado automatico\b|\bautoescalado\b|\bauto ?scaling\b", 1, "escalado automatico"),
        (r"\bciclo de vida de (?:la )?aplicacion\b|\btesting\b", 1, "ciclo de vida de la aplicacion"),
    ],
    SAAS: [
        (r"\bsaas\b", 3, "SaaS"),
        (r"\bsoftware como servicio\b", 3, "software como servicio"),
        (r"\bsoftware as a service\b", 3, "software as a service"),
        (r"\bgmail\b|\boffice ?365\b|\bmicrosoft ?365\b|\bgoogle (?:docs|workspace|drive)\b|\bdropbox\b|\bslack\b|\bzoom\b|\bnetflix\b|\bspotify\b|\btrello\b|\bcanva\b|\bshopify\b|\bhubspot\b|\bsalesforce\b", 3, "aplicacion SaaS conocida"),
        (r"\bcrm\b|\berp\b|\bsuite ofimatica\b", 3, "CRM / ERP / suite ofimatica"),
        (r"\bsuscripcion\b|\bmensualidad\b|\bpago mensual\b|\blicencia por usuario\b", 2, "modelo de suscripcion"),
        (r"\busuario(?:s)? final(?:es)?\b|\bcliente final\b", 2, "usuario final"),
        (r"\bsin instalar\b|\bno requiere instalacion\b|\bsin descargar\b", 2, "sin instalacion"),
        # Se dejo solo la senal fuerte. "aplicacion web" se descarto porque
        # era demasiado generica y competia injustamente con PaaS: cualquier
        # app que se "despliega" tambien es una "aplicacion web".
        (r"\baplicacion lista para usar\b|\bapp lista\b", 2, "aplicacion lista para usar"),
        (r"\bdesde el navegador\b|\bnavegador web\b|\bbrowser\b", 2, "acceso desde el navegador"),
        (r"\bmulti ?inquilino\b|\bmulti ?tenant\b", 2, "multi-tenant"),
        (r"\bcorreo electronico\b|\bvideollamadas?\b|\bhojas? de calculo\b|\bfacturacion\b", 1, "software de uso final"),
        (r"\bel proveedor (?:lo )?administra todo\b", 1, "el proveedor administra todo"),
    ],
    FAAS: [
        (r"\bfaas\b", 3, "FaaS"),
        (r"\bfuncion(?:es)? como servicio\b", 3, "funcion como servicio"),
        (r"\bfunctions? as a service\b", 3, "function as a service"),
        (r"\bserverless\b|\bsin servidor(?:es)?\b", 3, "serverless / sin servidor"),
        (r"\blambda\b|\bazure functions\b|\bcloud functions\b|\bcloudflare workers\b|\bstep functions\b", 3, "servicio FaaS conocido"),
        (r"\bpag(?:o|a|as|amos|ando)\b.{0,30}\b(?:por cada )?(?:ejecucion(?:es)?|invocacion(?:es)?|uso real)\b|\bpay per (?:use|execution)\b",
         3, "pago por ejecucion/invocacion"),
        (r"\bcold ?start\b|\barranque en frio\b", 3, "cold start"),
        # "cada vez que" / "cuando" / "en cuanto" describen un disparador sin
        # usar literalmente "evento" ni "trigger": es como se describe FaaS en
        # lenguaje natural ("ejecutar una funcion cuando se suba una imagen").
        (r"\bcada vez que\b|\ben cuanto\b|\bcuando se\b", 3, "disparador implicito ('cada vez que' / 'cuando se')"),
        (r"\borientad[oa] a eventos\b|\bevent ?driven\b", 2, "orientado a eventos"),
        (r"\befimer[oa]s?\b|\bcorta duracion\b|\bsegundos de ejecucion\b", 2, "ejecucion efimera"),
        (r"\bsin aprovisionar\b|\bno gestionar servidores\b|\bescala a cero\b", 2, "sin aprovisionamiento"),
        (r"\bmicroservicios?\b|\bapi gateway\b", 1, "microservicio / API Gateway"),
    ],
}


def _compilar_patrones() -> Dict[str, List[Tuple[re.Pattern, int, str]]]:
    """Precompila las regex una sola vez, al importar el modulo."""
    compilados: Dict[str, List[Tuple[re.Pattern, int, str]]] = {}
    for categoria, reglas in PATRONES_CRUDOS.items():
        compilados[categoria] = [
            (re.compile(patron, re.IGNORECASE), peso, etiqueta)
            for patron, peso, etiqueta in reglas
        ]
    return compilados


PATRONES = _compilar_patrones()
