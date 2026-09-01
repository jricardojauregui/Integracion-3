package com.udem.cloud.logica;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Diccionario de "palabras o conceptos relevantes" para una categoria.
 *
 * Se construye a partir de palabras en espanol tal como se escribirian
 * normalmente (ej. "funcion", "contenedores"); la clave real que se usa
 * para comparar contra los tokens del usuario es SIEMPRE el resultado de
 * aplicarles {@link Preprocesador#stem}, calculado aqui mismo en el
 * momento de agregarlas. Esto evita el error mas comun de un stemmer
 * artesanal: que alguien "adivine" a mano la raiz y se equivoque: la
 * raiz siempre sale de la MISMA funcion que se usa despues para
 * procesar el texto del usuario, asi que por construccion siempre
 * coinciden.
 */
public final class DiccionarioConceptos {

    private final Map<String, Integer> pesosPorStem = new LinkedHashMap<>();
    private final Map<String, String> etiquetaPorStem = new LinkedHashMap<>();

    /** Agrega una palabra (o varias variantes) con el mismo peso. */
    public DiccionarioConceptos agregar(int peso, String... palabras) {
        for (String palabra : palabras) {
            String raiz = Preprocesador.stem(Preprocesador.normalizarToken(palabra.toLowerCase()));
            pesosPorStem.merge(raiz, peso, Math::max);
            etiquetaPorStem.putIfAbsent(raiz, palabra);
        }
        return this;
    }

    public Map<String, Integer> getPesosPorStem() {
        return pesosPorStem;
    }

    public String etiquetaDe(String stem) {
        return etiquetaPorStem.getOrDefault(stem, stem);
    }
}
