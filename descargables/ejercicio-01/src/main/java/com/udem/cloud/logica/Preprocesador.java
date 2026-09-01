package com.udem.cloud.logica;

import com.udem.cloud.model.TextoProcesado;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Pipeline de Procesamiento de Lenguaje Natural (NLP) basico, aplicado antes
 * de que el texto llegue al motor de reglas/scoring. Cada paso pedido en la
 * practica es un metodo publico independiente (para poder probarlos por
 * separado), y {@link #procesar(String)} los encadena en orden:
 *
 *   1. aMinusculas       - conversion a minusculas
 *   2. limpiar           - limpieza de texto (quita signos de puntuacion)
 *   3. tokenizar         - tokenizacion (separa en palabras)
 *   4. quitarStopwords   - eliminacion de stopwords
 *   5. normalizarTokens  - normalizacion (quita acentos de cada token)
 *   6. aplicarStemming   - stemming ligero (agrupa variantes de una raiz)
 *
 * La identificacion de "palabras o conceptos relevantes" y la asignacion de
 * puntuaciones (los ultimos dos puntos del enunciado) se hacen despues, en
 * CloudServiceClassifier, comparando los tokens que produce este pipeline
 * contra un diccionario de conceptos por categoria.
 */
public final class Preprocesador {

    private Preprocesador() {
        // Clase de utilidad: no se instancia.
    }

    // ------------------------------------------------------------------
    // Lista de stopwords en espanol.
    //
    // DECISION DE DISENO IMPORTANTE: esta lista NO incluye palabras de
    // negacion ("sin", "no", "ni") ni palabras que forman disparadores
    // ("cada", "vez", "que"). Si las quitaramos, perderiamos justo la
    // senal que el clasificador necesita para reglas de contexto como
    // "sin administrar servidores" (PaaS) o "cada vez que" (FaaS). Por
    // eso, ademas, esas reglas de contexto se evaluan sobre el TEXTO
    // COMPLETO (ver TextoProcesado.textoParaPatrones) y no sobre la bolsa
    // de tokens sin stopwords.
    // ------------------------------------------------------------------
    private static final Set<String> STOPWORDS = new LinkedHashSet<>(Arrays.asList(
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
            "y", "o", "u", "que", "en", "con", "para", "por", "a", "se", "su", "sus",
            "es", "son", "como", "lo", "le", "les", "mi", "mis", "tu", "tus", "este",
            "esta", "estos", "estas", "ese", "esa", "esos", "esas", "muy", "mas",
            "pero", "porque", "cuando", "donde", "tambien", "ya", "solo", "segun",
            "the", "of", "in"
    ));

    // ------------------------------------------------------------------
    // 1. CONVERSION A MINUSCULAS
    // ------------------------------------------------------------------
    public static String aMinusculas(String texto) {
        return texto == null ? "" : texto.toLowerCase();
    }

    // ------------------------------------------------------------------
    // 2. LIMPIEZA DE TEXTO
    //    Se conservan letras, digitos (para no romper "k8s", "ec2",
    //    "office 365") y espacios; todo lo demas (puntuacion, simbolos)
    //    se reemplaza por espacio y se colapsan los espacios repetidos.
    // ------------------------------------------------------------------
    public static String limpiar(String texto) {
        if (texto == null) {
            return "";
        }
        String limpio = texto.replaceAll("[^\\p{L}\\p{N}\\s]", " ");
        limpio = limpio.replaceAll("\\s{2,}", " ").trim();
        return limpio;
    }

    // ------------------------------------------------------------------
    // 3. TOKENIZACION
    // ------------------------------------------------------------------
    public static List<String> tokenizar(String textoLimpio) {
        List<String> tokens = new ArrayList<>();
        if (textoLimpio == null || textoLimpio.isEmpty()) {
            return tokens;
        }
        for (String palabra : textoLimpio.split("\\s+")) {
            if (!palabra.isEmpty()) {
                tokens.add(palabra);
            }
        }
        return tokens;
    }

    // ------------------------------------------------------------------
    // 4. ELIMINACION DE STOPWORDS
    // ------------------------------------------------------------------
    public static List<String> quitarStopwords(List<String> tokens) {
        List<String> resultado = new ArrayList<>();
        for (String token : tokens) {
            if (!STOPWORDS.contains(token)) {
                resultado.add(token);
            }
        }
        return resultado;
    }

    // ------------------------------------------------------------------
    // 5. NORMALIZACION (quita acentos de cada token, ej. "máquina" -> "maquina")
    // ------------------------------------------------------------------
    public static String normalizarToken(String token) {
        String sinAcentos = Normalizer.normalize(token, Normalizer.Form.NFD);
        return sinAcentos.replaceAll("\\p{InCombiningDiacriticalMarks}+", "");
    }

    public static List<String> normalizarTokens(List<String> tokens) {
        List<String> resultado = new ArrayList<>();
        for (String token : tokens) {
            resultado.add(normalizarToken(token));
        }
        return resultado;
    }

    // ------------------------------------------------------------------
    // 6. STEMMING (ligero, heuristico)
    //
    //    No es un stemmer linguisticamente perfecto (eso requeriria una
    //    libreria como Snowball); es un recorte de sufijos comunes en
    //    espanol, suficiente para agrupar plurales/singulares y algunas
    //    formas verbales de las palabras que usa este dominio (ej.
    //    "contenedores" -> "contenedor", "funciones" -> "funcion").
    //    Se aplica UN SOLO sufijo (el mas largo que coincida) para evitar
    //    recortar de mas ("over-stemming").
    // ------------------------------------------------------------------
    private static final String[] SUFIJOS_ORDENADOS = {
            "amente", "aciones", "iciones", "ando", "iendo", "ciones", "mente", "es", "s"
    };

    public static String stem(String token) {
        if (token == null || token.length() <= 4) {
            return token;
        }
        for (String sufijo : SUFIJOS_ORDENADOS) {
            if (token.endsWith(sufijo) && token.length() - sufijo.length() >= 4) {
                return token.substring(0, token.length() - sufijo.length());
            }
        }
        return token;
    }

    public static List<String> aplicarStemming(List<String> tokens) {
        List<String> resultado = new ArrayList<>();
        for (String token : tokens) {
            resultado.add(stem(token));
        }
        return resultado;
    }

    // ------------------------------------------------------------------
    // PIPELINE COMPLETO
    // ------------------------------------------------------------------

    /**
     * Ejecuta los 6 pasos en orden y devuelve ambas representaciones del
     * texto que necesita el clasificador (ver {@link TextoProcesado}).
     */
    public static TextoProcesado procesar(String textoOriginal) {
        String minusculas = aMinusculas(textoOriginal);        // 1
        String limpio = limpiar(minusculas);                   // 2
        List<String> tokens = tokenizar(limpio);                // 3
        List<String> sinStopwords = quitarStopwords(tokens);    // 4
        List<String> normalizados = normalizarTokens(sinStopwords); // 5
        List<String> stems = aplicarStemming(normalizados);     // 6

        // Texto completo (minusculas + limpio + sin acentos) SIN tokenizar
        // ni quitar stopwords: lo usan los patrones de contexto/regex.
        String textoParaPatrones = normalizarToken(limpio);

        return new TextoProcesado(textoOriginal, textoParaPatrones, stems);
    }
}
