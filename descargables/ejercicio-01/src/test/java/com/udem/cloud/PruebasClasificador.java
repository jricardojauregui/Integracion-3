package com.udem.cloud;

import com.udem.cloud.logica.ClasificacionException;
import com.udem.cloud.logica.CloudServiceClassifier;
import com.udem.cloud.model.ResultadoClasificacion;

import java.util.ArrayList;
import java.util.List;

/**
 * Bateria de pruebas manual para CloudServiceClassifier.
 *
 * No usa JUnit a proposito: el entorno de este proyecto no tiene acceso a
 * un repositorio Maven para descargar dependencias, y esta clase corre con
 * el mismo `javac`/`java` que el resto del proyecto, sin configuracion
 * adicional. Si el curso permite agregar JUnit via el IDE, estos mismos
 * casos se pueden migrar a @Test sin cambiar la logica de aserciones.
 *
 * Cada caso EVITA usar literalmente las palabras IaaS/PaaS/SaaS/FaaS,
 * tal como pide la practica: se describe el servicio en lenguaje natural
 * y se compara el modelo detectado contra el esperado.
 *
 * Ejecutar con:  java -cp out com.udem.cloud.PruebasClasificador
 */
public class PruebasClasificador {

    private static int total = 0;
    private static int aprobadas = 0;

    public static void main(String[] args) {
        System.out.println("=== Pruebas del clasificador Cloud (sin usar las siglas literales) ===\n");

        // --- Los 4 ejemplos de la practica ---
        probar("Ejemplo A",
                "Necesito máquinas virtuales, almacenamiento y redes configurables para instalar mi propio sistema operativo",
                CloudServiceClassifier.IAAS);

        probar("Ejemplo B",
                "Quiero desplegar mi aplicación web sin administrar directamente servidores ni sistemas operativos",
                CloudServiceClassifier.PAAS);

        probar("Ejemplo C",
                "Los empleados utilizan una aplicación de correo electrónico directamente desde el navegador y pagan una suscripción mensual",
                CloudServiceClassifier.SAAS);

        probar("Ejemplo D",
                "Necesito ejecutar una función automáticamente cada vez que un usuario suba una imagen al almacenamiento Cloud",
                CloudServiceClassifier.FAAS);

        // --- Casos adicionales, tambien en lenguaje natural ---
        probar("Ejemplo E",
                "Quiero un espacio de trabajo colaborativo con hojas de cálculo y videollamadas al que mis clientes entren solo con su usuario y contraseña, pagando una mensualidad",
                CloudServiceClassifier.SAAS);

        probar("Ejemplo F",
                "Necesitamos rentar servidores dedicados con acceso root para instalar nuestro propio hipervisor y administrar todo el hardware",
                CloudServiceClassifier.IAAS);

        probar("Ejemplo G",
                "Buscamos un entorno donde subir nuestro codigo y que la plataforma se encargue del runtime, el balanceo y el escalado automatico",
                CloudServiceClassifier.PAAS);

        probar("Ejemplo H",
                "Queremos que se procese la imagen y se genere una miniatura automaticamente en cuanto el cliente la suba, pagando solo por cada ejecucion",
                CloudServiceClassifier.FAAS);

        // --- Caso de texto ambiguo / no clasificable ---
        probar("Ejemplo I (no concluyente)",
                "Todavia no se que necesito, quiero algo relacionado con la nube",
                ResultadoClasificacion.NO_DETERMINADO);

        System.out.println("\n=== Resumen: " + aprobadas + " / " + total + " pruebas aprobadas ===");

        if (aprobadas != total) {
            // Codigo de salida distinto de cero: util si esto se conecta a un pipeline de CI.
            System.exit(1);
        }
    }

    /** Ejecuta un caso de prueba y compara el modelo esperado contra el obtenido. */
    private static void probar(String nombreCaso, String descripcion, String modeloEsperado) {
        total++;
        try {
            ResultadoClasificacion resultado = CloudServiceClassifier.clasificar(descripcion);
            boolean aprobo = modeloEsperado.equals(resultado.getModelo());
            if (aprobo) {
                aprobadas++;
            }

            System.out.printf("[%s] %s%n", aprobo ? "PASA" : "FALLA", nombreCaso);
            System.out.printf("  Texto:    %s%n", descripcion);
            System.out.printf("  Esperado: %-14s Obtenido: %-14s Confianza: %.0f%%%n",
                    modeloEsperado, resultado.getModelo(), resultado.getConfianza() * 100);
            System.out.printf("  Puntajes: %s%n", resultado.getPuntajes());
            if (!aprobo) {
                System.out.println("  >>> Revisar reglas para esta categoria <<<");
            }
            System.out.println();

        } catch (ClasificacionException error) {
            total--; // no cuenta como aprobada ni reprobada: es un fallo del propio motor
            System.out.printf("[ERROR] %s -> %s%n%n", nombreCaso, error.getMessage());
        }
    }
}
