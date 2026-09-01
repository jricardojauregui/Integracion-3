package com.udem.cloud;

import com.udem.cloud.ui.MainFrame;

import javax.swing.SwingUtilities;
import javax.swing.UIManager;

/**
 * Punto de entrada de la aplicacion cloud_models_classifier.
 * Levanta la interfaz grafica dentro del hilo de eventos de Swing (EDT).
 */
public class Main {

    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
            // Si falla, se usa la apariencia por defecto de Swing (no es un error fatal).
        }

        SwingUtilities.invokeLater(() -> new MainFrame().setVisible(true));
    }
}
