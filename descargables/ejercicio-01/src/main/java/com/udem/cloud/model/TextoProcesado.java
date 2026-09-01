package com.udem.cloud.model;

import java.util.Collections;
import java.util.List;

/**
 * Resultado de pasar un texto por el pipeline de NLP (ver Preprocesador).
 * Guarda DOS representaciones del mismo texto porque cada una sirve a un
 * proposito distinto dentro del clasificador:
 *
 *  - tokensFinales: bolsa de palabras ya limpia, sin stopwords y con
 *    stemming. Se usa para el diccionario de "palabras o conceptos
 *    relevantes" (coincidencia de una sola palabra contra cada categoria).
 *
 *  - textoParaPatrones: el texto completo en minusculas, sin acentos y sin
 *    signos de puntuacion, PERO sin tokenizar y SIN quitar stopwords. Se
 *    usa para los patrones de contexto (regex) que necesitan el orden
 *    original de las palabras, por ejemplo para detectar negaciones como
 *    "sin administrar servidores" (si hubieramos quitado "sin" por ser
 *    stopword, perderiamos justo la senal que buscamos).
 */
public final class TextoProcesado {

    private final String textoOriginal;
    private final String textoParaPatrones;
    private final List<String> tokensFinales;

    public TextoProcesado(String textoOriginal, String textoParaPatrones, List<String> tokensFinales) {
        this.textoOriginal = textoOriginal;
        this.textoParaPatrones = textoParaPatrones;
        this.tokensFinales = Collections.unmodifiableList(tokensFinales);
    }

    public String getTextoOriginal() {
        return textoOriginal;
    }

    public String getTextoParaPatrones() {
        return textoParaPatrones;
    }

    public List<String> getTokensFinales() {
        return tokensFinales;
    }
}
