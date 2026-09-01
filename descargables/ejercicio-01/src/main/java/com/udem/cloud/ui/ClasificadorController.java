package com.udem.cloud.ui;

import com.udem.cloud.logica.ClasificacionException;
import com.udem.cloud.logica.CloudServiceClassifier;
import com.udem.cloud.logica.EntradaInvalidaException;
import com.udem.cloud.logica.ValidadorEntrada;
import com.udem.cloud.model.ResultadoClasificacion;

/**
 * Controlador (capa intermedia) entre la GUI (MainFrame) y la logica de
 * negocio (ValidadorEntrada + CloudServiceClassifier).
 *
 * ESTE ES EL LIMITE QUE SEPARA GUI Y LOGICA: MainFrame nunca llama
 * directamente a CloudServiceClassifier ni a ValidadorEntrada. Solo conoce
 * este controlador y el objeto {@link SolicitudClasificacion} que devuelve.
 * Gracias a esto:
 *   - La logica se puede probar sin levantar ninguna ventana (ver
 *     src/test/java/com/udem/cloud/PruebasClasificador.java).
 *   - Si un dia cambia la interfaz (por ejemplo, a JavaFX o a una API web),
 *     este controlador se reutiliza sin tocar una sola regla de negocio.
 */
public class ClasificadorController {

    /** Resultado ya listo para mostrarse: nombre completo + resultado del motor. */
    public static final class SolicitudClasificacion {
        private final String nombreCompleto;
        private final ResultadoClasificacion resultado;

        public SolicitudClasificacion(String nombreCompleto, ResultadoClasificacion resultado) {
            this.nombreCompleto = nombreCompleto;
            this.resultado = resultado;
        }

        public String getNombreCompleto() {
            return nombreCompleto;
        }

        public ResultadoClasificacion getResultado() {
            return resultado;
        }
    }

    /**
     * Valida los datos del formulario y ejecuta la clasificacion.
     *
     * @throws EntradaInvalidaException si nombre, apellido o descripcion no
     *         cumplen las reglas minimas (mensaje ya listo para el usuario).
     * @throws ClasificacionException si el motor de clasificacion falla de
     *         forma inesperada.
     */
    public SolicitudClasificacion procesar(String nombre, String apellido, String descripcion)
            throws EntradaInvalidaException, ClasificacionException {

        // 1. Validacion (capa de logica, reutilizable y probada por separado)
        String nombreValido = ValidadorEntrada.validarNombre(nombre, "Nombre");
        String apellidoValido = ValidadorEntrada.validarNombre(apellido, "Apellido");
        String descripcionValida = ValidadorEntrada.validarDescripcion(descripcion);

        // 2. Clasificacion
        ResultadoClasificacion resultado = CloudServiceClassifier.clasificar(descripcionValida);

        return new SolicitudClasificacion(nombreValido + " " + apellidoValido, resultado);
    }
}
