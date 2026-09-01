import com.udem.cloud.logica.ClasificacionException;
import com.udem.cloud.logica.CloudServiceClassifier;
import com.udem.cloud.logica.EntradaInvalidaException;
import com.udem.cloud.logica.ValidadorEntrada;
import com.udem.cloud.model.ResultadoClasificacion;

/**
 * Version de linea de comandos (CLI) del clasificador de modelos Cloud.
 *
 * REUTILIZA EXACTAMENTE LA MISMA LOGICA que la GUI: llama a las mismas
 * clases del paquete com.udem.cloud.logica (ValidadorEntrada y
 * CloudServiceClassifier) que usa ClasificadorController desde MainFrame.
 * Ninguna regla de clasificacion esta duplicada aqui — esta clase es
 * solo una interfaz de entrada/salida distinta (texto por consola en vez
 * de una ventana), igual que en el diagrama de arquitectura: GUI y CLI
 * son dos entradas separadas hacia el mismo Clasificador.
 *
 * Uso:
 *   java CloudClassifier "máquinas virtuales almacenamiento redes"
 *   -&gt; Modelo identificado: IaaS
 *
 * Bandera opcional -v / --verbose para ver confianza, puntajes y las
 * palabras/conceptos que se detectaron en cada categoria.
 */
public final class CloudClassifier {

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Uso: java CloudClassifier \"descripcion del servicio\" [-v]");
            System.exit(1);
            return;
        }

        boolean verbose = false;
        StringBuilder textoBuilder = new StringBuilder();
        for (String arg : args) {
            if (arg.equals("-v") || arg.equals("--verbose")) {
                verbose = true;
                continue;
            }
            if (textoBuilder.length() > 0) {
                textoBuilder.append(' ');
            }
            textoBuilder.append(arg);
        }
        String descripcion = textoBuilder.toString();

        try {
            // Misma validacion que usa la GUI a traves de ClasificadorController.
            String descripcionValida = ValidadorEntrada.validarDescripcion(descripcion);

            // Mismo motor de clasificacion que usa la GUI.
            ResultadoClasificacion resultado = CloudServiceClassifier.clasificar(descripcionValida);

            System.out.println("Modelo identificado: " + resultado.getModelo());

            if (verbose) {
                System.out.printf("Confianza: %.0f%%%n", resultado.getConfianza() * 100);
                if (resultado.isEmpate()) {
                    System.out.println("Atencion: hay empate entre modelos, el texto es ambiguo.");
                }
                System.out.println("Puntajes: " + resultado.getPuntajes());
                resultado.getCoincidencias().forEach((modelo, terminos) ->
                        System.out.println("  " + modelo + " -> " + terminos));
            }

        } catch (EntradaInvalidaException error) {
            System.err.println("Entrada invalida: " + error.getMessage());
            System.exit(1);
        } catch (ClasificacionException error) {
            System.err.println("Error al clasificar: " + error.getMessage());
            System.exit(1);
        }
    }
}
