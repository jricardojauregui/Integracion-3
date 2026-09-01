package com.udem.cloud.logica;

/**
 * Valida los datos capturados en el formulario antes de que lleguen al
 * clasificador. Vive en la capa de logica (no en la GUI) para que las
 * mismas reglas se puedan reutilizar desde una prueba unitaria, una API
 * futura, u otra interfaz, sin depender de Swing.
 */
public final class ValidadorEntrada {

    private static final int NOMBRE_MIN = 2;
    private static final int NOMBRE_MAX = 60;
    private static final int DESCRIPCION_MIN = 8;
    private static final int DESCRIPCION_MAX = 2000;

    // Letras (con acentos/ñ), espacios y guiones; nada de numeros ni simbolos.
    private static final String REGEX_NOMBRE = "^[\\p{L} '-]+$";

    private ValidadorEntrada() {
        // Clase de utilidad: no se instancia.
    }

    /**
     * Valida nombre o apellido. Se usa el mismo metodo para ambos campos
     * porque comparten exactamente las mismas reglas.
     *
     * @param valor       texto capturado por el usuario
     * @param nombreCampo nombre del campo, para construir el mensaje de error
     * @return el valor ya recortado (trim), listo para usarse
     */
    public static String validarNombre(String valor, String nombreCampo) throws EntradaInvalidaException {
        if (valor == null || valor.trim().isEmpty()) {
            throw new EntradaInvalidaException("El campo \"" + nombreCampo + "\" no puede estar vacio.");
        }
        String limpio = valor.trim();
        if (limpio.length() < NOMBRE_MIN || limpio.length() > NOMBRE_MAX) {
            throw new EntradaInvalidaException(
                    "El campo \"" + nombreCampo + "\" debe tener entre " + NOMBRE_MIN
                            + " y " + NOMBRE_MAX + " caracteres.");
        }
        if (!limpio.matches(REGEX_NOMBRE)) {
            throw new EntradaInvalidaException(
                    "El campo \"" + nombreCampo + "\" solo puede contener letras y espacios.");
        }
        return limpio;
    }

    /**
     * Valida la descripcion del servicio Cloud que se enviara al clasificador.
     */
    public static String validarDescripcion(String valor) throws EntradaInvalidaException {
        if (valor == null || valor.trim().isEmpty()) {
            throw new EntradaInvalidaException("Escribe una descripcion del servicio Cloud a clasificar.");
        }
        String limpio = valor.trim();
        if (limpio.length() < DESCRIPCION_MIN) {
            throw new EntradaInvalidaException(
                    "La descripcion es muy corta (minimo " + DESCRIPCION_MIN + " caracteres). "
                            + "Agrega mas contexto sobre el servicio.");
        }
        if (limpio.length() > DESCRIPCION_MAX) {
            throw new EntradaInvalidaException(
                    "La descripcion es demasiado larga (maximo " + DESCRIPCION_MAX + " caracteres).");
        }
        return limpio;
    }
}
