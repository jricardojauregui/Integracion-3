package com.udem.cloud.logica;

/**
 * Excepcion verificada que se lanza cuando los datos capturados por el
 * usuario (nombre, apellido o descripcion) no cumplen las reglas minimas
 * de validacion. El mensaje ya viene listo para mostrarse al usuario.
 */
public class EntradaInvalidaException extends Exception {

    public EntradaInvalidaException(String mensaje) {
        super(mensaje);
    }
}
