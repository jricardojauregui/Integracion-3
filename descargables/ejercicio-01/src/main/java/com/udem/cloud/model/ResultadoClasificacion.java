package com.udem.cloud.model;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Objeto de transferencia (DTO) que guarda el resultado del analisis:
 * el modelo ganador, el puntaje obtenido por cada modelo, el nivel de
 * confianza y las palabras clave que se detectaron en el texto.
 */
public class ResultadoClasificacion {

    public static final String NO_DETERMINADO = "No determinado";

    private String modelo = NO_DETERMINADO;
    private double confianza = 0.0;                 // Valor entre 0.0 y 1.0
    private boolean empate = false;                 // true si dos modelos quedaron igualados
    private final Map<String, Integer> puntajes = new LinkedHashMap<>();
    private final Map<String, List<String>> coincidencias = new LinkedHashMap<>();

    public String getModelo() {
        return modelo;
    }

    public void setModelo(String modelo) {
        this.modelo = modelo;
    }

    public double getConfianza() {
        return confianza;
    }

    public void setConfianza(double confianza) {
        this.confianza = confianza;
    }

    public boolean isEmpate() {
        return empate;
    }

    public void setEmpate(boolean empate) {
        this.empate = empate;
    }

    public Map<String, Integer> getPuntajes() {
        return puntajes;
    }

    public Map<String, List<String>> getCoincidencias() {
        return coincidencias;
    }

    /** Suma de todos los puntajes; se usa para calcular porcentajes. */
    public int getTotalPuntos() {
        int total = 0;
        for (int p : puntajes.values()) {
            total += p;
        }
        return total;
    }

    /** Devuelve el porcentaje (0-100) que representa un modelo sobre el total. */
    public int getPorcentaje(String modelo) {
        int total = getTotalPuntos();
        if (total == 0) {
            return 0;
        }
        return (int) Math.round(puntajes.getOrDefault(modelo, 0) * 100.0 / total);
    }
}
