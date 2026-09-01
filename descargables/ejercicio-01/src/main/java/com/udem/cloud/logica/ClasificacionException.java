package com.udem.cloud.logica;

/**
 * Excepcion de dominio para errores durante el proceso de clasificacion
 * (por ejemplo, si el motor de reglas recibe un estado inconsistente).
 *
 * Se declara como excepcion verificada (checked) a proposito: obliga a quien
 * use el clasificador (la GUI u otra capa) a decidir explicitamente como
 * manejar una falla, en lugar de dejar que la aplicacion truene sin control.
 */
public class ClasificacionException extends Exception {

    public ClasificacionException(String mensaje) {
        super(mensaje);
    }

    public ClasificacionException(String mensaje, Throwable causa) {
        super(mensaje, causa);
    }
}
