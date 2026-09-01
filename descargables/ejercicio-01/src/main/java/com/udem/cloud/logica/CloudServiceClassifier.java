package com.udem.cloud.logica;

import com.udem.cloud.model.Regla;
import com.udem.cloud.model.ResultadoClasificacion;
import com.udem.cloud.model.TextoProcesado;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Motor de clasificacion (version 3).
 *
 * Combina DOS fuentes de evidencia por categoria, calculadas sobre el
 * resultado del pipeline de NLP ({@link Preprocesador}):
 *
 *  A) DICCIONARIO DE CONCEPTOS (identificarXxxPorConcepto): compara la
 *     bolsa de tokens ya procesados (minusculas, limpios, sin stopwords,
 *     normalizados y con stemming) contra un diccionario de palabras
 *     clave de una sola palabra por categoria. Esta es la parte
 *     "NLP" propiamente dicha del clasificador.
 *
 *  B) PATRONES DE CONTEXTO (REGLAS_CONTEXTO_*): expresiones regulares
 *     para frases, nombres de marca (Heroku, AWS Lambda...), siglas
 *     (IaaS, CI/CD...) y sobre todo NEGACIONES ("sin administrar
 *     servidores"), que necesitan el texto completo y en orden -- un
 *     diccionario de una sola palabra no puede expresar "sin X" porque
 *     eso depende de que dos palabras aparezcan juntas y en ese orden.
 *     Por eso estas reglas se evaluan sobre el texto normalizado
 *     COMPLETO (sin tokenizar, sin quitar stopwords).
 *
 * Esta clase pertenece exclusivamente a la capa de LOGICA: no conoce
 * Swing ni la CLI. Tanto MainFrame (via ClasificadorController) como
 * CloudClassifier (CLI) llaman a {@link #clasificar(String)}.
 */
public final class CloudServiceClassifier {

    public static final String IAAS = "IaaS";
    public static final String PAAS = "PaaS";
    public static final String SAAS = "SaaS";
    public static final String FAAS = "FaaS";

    public static final String[] MODELOS = { IAAS, PAAS, SAAS, FAAS };

    private CloudServiceClassifier() {
        // Clase de utilidad: no se instancia.
    }

    // ------------------------------------------------------------------
    // A) DICCIONARIOS DE CONCEPTOS (palabras sueltas -> peso)
    //    Los pesos se mantienen bajos (1-2) porque una sola palabra nunca
    //    es tan concluyente como una frase completa.
    // ------------------------------------------------------------------

    private static final DiccionarioConceptos CONCEPTOS_IAAS = new DiccionarioConceptos()
            .agregar(3, "hipervisor", "hypervisor")
            .agregar(1, "infraestructura")
            .agregar(1, "cpu", "ram", "memoria", "disco", "discos", "storage");

    private static final DiccionarioConceptos CONCEPTOS_PAAS = new DiccionarioConceptos()
            .agregar(2, "middleware")
            .agregar(1, "contenedor", "contenedores", "docker");

    private static final DiccionarioConceptos CONCEPTOS_SAAS = new DiccionarioConceptos()
            .agregar(1, "software", "aplicacion", "aplicaciones");

    private static final DiccionarioConceptos CONCEPTOS_FAAS = new DiccionarioConceptos()
            .agregar(2, "funcion", "funciones")
            .agregar(2, "evento", "eventos")
            .agregar(2, "disparador", "disparadores")
            // "trigger"/"triggers" se listan por separado porque el stemmer
            // (pensado para espanol) no las normaliza a la misma raiz.
            .agregar(2, "trigger", "triggers")
            // Igual aqui: "invocar" (verbo) e "invocacion" (sustantivo) no
            // comparten sufijo, asi que se listan las dos formas.
            .agregar(2, "invocacion", "invocaciones", "invocar");

    // ------------------------------------------------------------------
    // B) PATRONES DE CONTEXTO (regex sobre el texto completo)
    //    Peso 4 = negacion/contexto muy confiable | 3 = especifico |
    //    2 = fuerte | 1 = contextual.
    //
    //    Nota tecnica: como el texto ya paso por limpieza (los signos de
    //    puntuacion se convirtieron en espacios, ver Preprocesador.limpiar),
    //    los patrones usan " ?" (espacio opcional) en vez de "-?" o "/?"
    //    para separadores como guiones o diagonales (ej. "ci/cd" llega
    //    aqui como "ci cd").
    // ------------------------------------------------------------------

    private static final List<Regla> REGLAS_CONTEXTO_IAAS = Arrays.asList(
            new Regla("\\biaas\\b", 3, "IaaS"),
            new Regla("\\binfraestructura como servicio\\b", 3, "infraestructura como servicio"),
            new Regla("\\binfrastructure as a service\\b", 3, "infrastructure as a service"),
            new Regla("\\bmaquinas? virtuales?\\b|\\bvirtual machines?\\b|\\bvms?\\b", 3, "maquina virtual / VM"),
            new Regla("\\bec2\\b|\\bcompute engine\\b|\\bazure vm\\b|\\bdroplet\\b", 3, "servicio de computo (EC2 / Compute Engine)"),
            new Regla("\\bbare metal\\b|\\bservidor(es)? (fisico|dedicado)s?\\b", 3, "bare metal / servidor dedicado"),
            // Instalar tu propio sistema operativo = control total tipico de IaaS
            new Regla("\\binstalar\\b.{0,30}\\bsistemas?\\s+operativos?\\b", 3, "instalar tu propio sistema operativo"),
            new Regla("\\bservidor(es)? virtual(es)?\\b", 2, "servidor virtual"),
            new Regla("\\balmacenamiento (en )?bloque\\b|\\bblock storage\\b|\\bebs\\b", 2, "almacenamiento en bloque"),
            new Regla("\\bred(es)? (virtual(es)?|configurables?)\\b|\\bvpc\\b|\\bsubred(es)?\\b|\\bvlan\\b", 2, "red virtual / configurable / VPC"),
            new Regla("\\bbalanceador de carga\\b|\\bload balancer\\b", 2, "balanceador de carga"),
            new Regla("\\bfirewall\\b|\\bgrupo de seguridad\\b|\\bsecurity group\\b", 2, "firewall / grupo de seguridad"),
            new Regla("\\bopenstack\\b|\\bvmware\\b|\\bvsphere\\b|\\bproxmox\\b", 2, "plataforma de virtualizacion"),
            new Regla("\\bsistema operativo\\b|\\bimagen del sistema\\b|\\bami\\b", 1, "sistema operativo / imagen"),
            new Regla("\\bsnapshots?\\b|\\bcopia de seguridad\\b|\\bbackup\\b", 1, "snapshot / backup"),
            new Regla("\\bescalamiento vertical\\b|\\bredimensionar\\b", 1, "escalamiento vertical"),
            new Regla("\\badministrar el servidor\\b|\\bcontrol total\\b|\\bacceso root\\b|\\bssh\\b", 1, "administracion del servidor")
    );

    private static final List<Regla> REGLAS_CONTEXTO_PAAS = Arrays.asList(
            new Regla("\\bpaas\\b", 3, "PaaS"),
            new Regla("\\bplataforma como servicio\\b", 3, "plataforma como servicio"),
            new Regla("\\bplatform as a service\\b", 3, "platform as a service"),
            new Regla("\\bheroku\\b|\\bapp engine\\b|\\belastic beanstalk\\b|\\bapp service\\b|\\bopenshift\\b|\\bcloud foundry\\b|\\brailway\\b|\\brender\\b", 3, "plataforma gestionada (Heroku / App Engine / etc.)"),
            new Regla("\\bbuildpacks?\\b|\\bruntime gestionado\\b", 3, "buildpack / runtime gestionado"),
            // Patron de CONTEXTO mas importante de todo el motor: "sin administrar
            // (...) servidores/infraestructura/SO" es la forma natural en que la
            // gente describe PaaS sin usar la sigla. El comodin .{0,40} tolera
            // palabras intermedias como "directamente".
            new Regla("\\b(sin|no)\\b.{0,40}\\b(administrar|gestionar|preocuparte por|preocuparse por)\\b.{0,40}\\b(servidor(es)?|infraestructura|sistemas?\\s+operativos?)\\b",
                    4, "sin administrar servidores/infraestructura/SO (abstraccion tipica de PaaS)"),
            new Regla("\\bentorno de (ejecucion|desarrollo)\\b|\\bruntime\\b", 2, "entorno de ejecucion"),
            new Regla("\\bdesplegar\\b|\\bdespliegue\\b|\\bdeploy(ar|ment)?\\b", 2, "despliegue de aplicaciones"),
            new Regla("\\bci ?cd\\b|\\bpipelines?\\b|\\bintegracion continua\\b", 2, "CI/CD"),
            new Regla("\\bkubernetes\\b|\\bk8s\\b|\\baks\\b|\\beks\\b|\\bgke\\b|\\borquestacion de contenedores\\b", 2, "orquestacion gestionada"),
            new Regla("\\bbase de datos (gestionada|administrada)\\b|\\brds\\b|\\bcloud sql\\b", 2, "base de datos gestionada"),
            new Regla("\\bframeworks?\\b|\\bsdk\\b|\\bapis? de desarrollo\\b", 1, "framework / SDK"),
            new Regla("\\bdesarrollador(es)?\\b|\\bequipo de desarrollo\\b", 1, "enfoque en desarrolladores"),
            new Regla("\\bescalado automatico\\b|\\bautoescalado\\b|\\bauto ?scaling\\b", 1, "escalado automatico"),
            new Regla("\\bciclo de vida de (la )?aplicacion\\b|\\bpruebas\\b|\\btesting\\b", 1, "ciclo de vida de la aplicacion")
    );

    private static final List<Regla> REGLAS_CONTEXTO_SAAS = Arrays.asList(
            new Regla("\\bsaas\\b", 3, "SaaS"),
            new Regla("\\bsoftware como servicio\\b", 3, "software como servicio"),
            new Regla("\\bsoftware as a service\\b", 3, "software as a service"),
            new Regla("\\bgmail\\b|\\boffice ?365\\b|\\bmicrosoft ?365\\b|\\bgoogle (docs|workspace|drive)\\b|\\bdropbox\\b|\\bslack\\b|\\bzoom\\b|\\bnetflix\\b|\\bspotify\\b|\\btrello\\b|\\bcanva\\b|\\bshopify\\b|\\bhubspot\\b|\\bsalesforce\\b", 3, "aplicacion SaaS conocida"),
            new Regla("\\bcrm\\b|\\berp\\b|\\bsuite ofimatica\\b", 3, "CRM / ERP / suite ofimatica"),
            new Regla("\\bsuscripcion\\b|\\bmensualidad\\b|\\bpago mensual\\b|\\blicencia por usuario\\b", 2, "modelo de suscripcion"),
            new Regla("\\busuario(s)? final(es)?\\b|\\bcliente final\\b", 2, "usuario final"),
            new Regla("\\bsin instalar\\b|\\bno requiere instalacion\\b|\\bsin descargar\\b", 2, "sin instalacion"),
            // Se dejo solo la senal fuerte (app ya lista para el usuario final);
            // "aplicacion web" se quito porque era demasiado generica y competia
            // injustamente con PaaS (cualquier app que se "despliega" tambien es
            // una "aplicacion web").
            new Regla("\\baplicacion lista para usar\\b|\\bapp lista\\b", 2, "aplicacion lista para usar"),
            new Regla("\\bdesde el navegador\\b|\\bnavegador web\\b|\\bbrowser\\b", 2, "acceso desde el navegador"),
            new Regla("\\bmulti ?inquilino\\b|\\bmulti ?tenant\\b", 2, "multi-tenant"),
            new Regla("\\bcorreo electronico\\b|\\bvideollamadas?\\b|\\bhojas? de calculo\\b|\\bfacturacion\\b", 1, "software de uso final"),
            new Regla("\\bno (me )?preocupo por (nada|el mantenimiento)\\b|\\bel proveedor (lo )?administra todo\\b", 1, "el proveedor administra todo")
    );

    private static final List<Regla> REGLAS_CONTEXTO_FAAS = Arrays.asList(
            new Regla("\\bfaas\\b", 3, "FaaS"),
            new Regla("\\bfuncion(es)? como servicio\\b", 3, "funcion como servicio"),
            new Regla("\\bfunctions? as a service\\b", 3, "function as a service"),
            new Regla("\\bserverless\\b|\\bsin servidor(es)?\\b", 3, "serverless / sin servidor"),
            new Regla("\\blambda\\b|\\bazure functions\\b|\\bcloud functions\\b|\\bcloudflare workers\\b|\\bstep functions\\b", 3, "servicio FaaS conocido"),
            // Patron de CONTEXTO: cubre "pago por ejecucion" y variantes
            // naturales como "pagando solo por cada ejecucion".
            new Regla("\\bpag(o|a|as|amos|ando)\\b.{0,30}\\b(por cada )?(ejecucion(es)?|invocacion(es)?|uso real)\\b|\\bpay per (use|execution)\\b",
                    3, "pago por ejecucion/invocacion"),
            new Regla("\\bcold ?start\\b|\\barranque en frio\\b", 3, "cold start"),
            // "cada vez que" / "en cuanto" describen un disparador sin usar
            // literalmente "evento" ni "trigger" -- es como se describe FaaS
            // en lenguaje natural.
            new Regla("\\bcada vez que\\b|\\ben cuanto\\b", 3, "disparador implicito ('cada vez que' / 'en cuanto')"),
            new Regla("\\borientad[oa] a eventos\\b|\\bevent ?driven\\b", 2, "orientado a eventos"),
            new Regla("\\befimer[oa]s?\\b|\\bcorta duracion\\b|\\bsegundos de ejecucion\\b", 2, "ejecucion efimera"),
            new Regla("\\bmicroservicios?\\b|\\bapi gateway\\b", 1, "microservicio / API Gateway"),
            new Regla("\\bsin aprovisionar\\b|\\bno gestionar servidores\\b|\\bescala a cero\\b", 2, "sin aprovisionamiento")
    );

    // ------------------------------------------------------------------
    // METODOS INDEPENDIENTES POR CATEGORIA (identificarXxx)
    //
    // Cada uno recibe el TextoProcesado ya generado por el pipeline de NLP
    // y suma: (A) puntaje del diccionario de conceptos + (B) puntaje de los
    // patrones de contexto. Siguen siendo independientes y probables por
    // separado, como pedia la version anterior del ejercicio.
    // ------------------------------------------------------------------

    public static int identificarIaaS(TextoProcesado texto, List<String> coincidenciasEncontradas) {
        return identificar(texto, CONCEPTOS_IAAS, REGLAS_CONTEXTO_IAAS, coincidenciasEncontradas);
    }

    public static int identificarPaaS(TextoProcesado texto, List<String> coincidenciasEncontradas) {
        return identificar(texto, CONCEPTOS_PAAS, REGLAS_CONTEXTO_PAAS, coincidenciasEncontradas);
    }

    public static int identificarSaaS(TextoProcesado texto, List<String> coincidenciasEncontradas) {
        return identificar(texto, CONCEPTOS_SAAS, REGLAS_CONTEXTO_SAAS, coincidenciasEncontradas);
    }

    public static int identificarFaaS(TextoProcesado texto, List<String> coincidenciasEncontradas) {
        return identificar(texto, CONCEPTOS_FAAS, REGLAS_CONTEXTO_FAAS, coincidenciasEncontradas);
    }

    /** Logica comun: suma diccionario de conceptos + patrones de contexto. */
    private static int identificar(TextoProcesado texto, DiccionarioConceptos diccionario,
                                    List<Regla> reglasContexto, List<String> encontradas) {
        int puntaje = 0;

        // A) Identificacion de palabras/conceptos relevantes (bolsa de tokens con stemming)
        java.util.Set<String> tokensPresentes = new java.util.HashSet<>(texto.getTokensFinales());
        for (var entrada : diccionario.getPesosPorStem().entrySet()) {
            if (tokensPresentes.contains(entrada.getKey())) {
                puntaje += entrada.getValue();
                encontradas.add(diccionario.etiquetaDe(entrada.getKey()));
            }
        }

        // B) Patrones de contexto (frases, marcas, negaciones) sobre el texto completo
        for (Regla regla : reglasContexto) {
            if (regla.coincide(texto.getTextoParaPatrones())) {
                puntaje += regla.getPeso();
                encontradas.add(regla.getEtiqueta());
            }
        }

        return puntaje;
    }

    // ------------------------------------------------------------------
    // CLASIFICACION FINAL
    // ------------------------------------------------------------------

    /**
     * Pasa el texto por el pipeline de NLP y despues por las cuatro
     * identificaciones independientes, comparando puntajes.
     *
     * @throws ClasificacionException si ocurre un error inesperado. La
     *         entrada nula/vacia la filtra ValidadorEntrada antes de llegar
     *         aqui; aun asi se maneja de forma defensiva.
     */
    public static ResultadoClasificacion clasificar(String textoOriginal) throws ClasificacionException {
        try {
            TextoProcesado textoProcesado = Preprocesador.procesar(textoOriginal);
            ResultadoClasificacion resultado = new ResultadoClasificacion();

            for (String modelo : MODELOS) {
                List<String> encontradas = new ArrayList<>();
                int puntaje;

                switch (modelo) {
                    case IAAS: puntaje = identificarIaaS(textoProcesado, encontradas); break;
                    case PAAS: puntaje = identificarPaaS(textoProcesado, encontradas); break;
                    case SAAS: puntaje = identificarSaaS(textoProcesado, encontradas); break;
                    case FAAS: puntaje = identificarFaaS(textoProcesado, encontradas); break;
                    default:   puntaje = 0;
                }

                resultado.getPuntajes().put(modelo, puntaje);
                resultado.getCoincidencias().put(modelo, encontradas);
            }

            String ganador = null;
            int mejorPuntaje = 0;
            int repetidos = 0;

            for (String modelo : MODELOS) {
                int puntaje = resultado.getPuntajes().get(modelo);
                if (puntaje > mejorPuntaje) {
                    mejorPuntaje = puntaje;
                    ganador = modelo;
                    repetidos = 1;
                } else if (puntaje == mejorPuntaje && puntaje > 0) {
                    repetidos++;
                }
            }

            if (ganador == null || mejorPuntaje == 0) {
                resultado.setModelo(ResultadoClasificacion.NO_DETERMINADO);
                resultado.setConfianza(0.0);
                return resultado;
            }

            resultado.setModelo(ganador);
            resultado.setEmpate(repetidos > 1);
            resultado.setConfianza((double) mejorPuntaje / resultado.getTotalPuntos());
            return resultado;

        } catch (RuntimeException errorInesperado) {
            throw new ClasificacionException(
                    "Ocurrio un error inesperado al analizar el texto.", errorInesperado);
        }
    }
}
