package com.udem.cloud.model;

import java.util.regex.Pattern;

/**
 * Representa una regla de clasificacion.
 * Cada regla es una expresion regular (Regex) asociada a un peso:
 * mientras mas especifica es la palabra clave, mayor es su peso.
 */
public class Regla {

    private final Pattern patron;   // Expresion regular ya compilada
    private final int peso;         // Puntos que aporta si el patron se encuentra
    private final String etiqueta;  // Nombre legible de la regla (se muestra al usuario)

    public Regla(String regex, int peso, String etiqueta) {
        // CASE_INSENSITIVE: no distingue mayusculas/minusculas
        this.patron = Pattern.compile(regex, Pattern.CASE_INSENSITIVE);
        this.peso = peso;
        this.etiqueta = etiqueta;
    }

    /** Indica si la expresion regular aparece al menos una vez en el texto. */
    public boolean coincide(String texto) {
        return patron.matcher(texto).find();
    }

    public int getPeso() {
        return peso;
    }

    public String getEtiqueta() {
        return etiqueta;
    }
}
