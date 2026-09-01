package com.udem.cloud.ui;

import com.udem.cloud.logica.ClasificacionException;
import com.udem.cloud.logica.CloudServiceClassifier;
import com.udem.cloud.logica.EntradaInvalidaException;
import com.udem.cloud.model.ResultadoClasificacion;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.List;
import java.util.Map;

/**
 * Ventana principal de la aplicacion (interfaz grafica con Swing).
 *
 * IMPORTANTE: esta clase SOLO construye y actualiza componentes visuales.
 * No contiene reglas de clasificacion ni de validacion: toda esa logica
 * vive en el paquete com.udem.cloud.logica y se invoca a traves de
 * {@link ClasificadorController}. Si el controlador lanza una excepcion,
 * la GUI se limita a mostrarla en un dialogo; nunca decide "que es SaaS".
 *
 * Se divide en tres zonas:
 *   - Encabezado: titulo de la aplicacion.
 *   - Formulario: nombre, apellido y descripcion del servicio Cloud.
 *   - Resultados: modelo detectado, barras de puntaje y palabras clave.
 */
public class MainFrame extends JFrame {

    // Paleta de colores de la interfaz
    private static final Color AZUL       = new Color(0x1B3A8C);
    private static final Color AZUL_CLARO = new Color(0x398EF4);
    private static final Color FONDO      = new Color(0xF4F6FB);
    private static final Color TEXTO      = new Color(0x1F2430);
    private static final Color GRIS       = new Color(0x6B7280);

    // El controlador es la UNICA puerta de entrada a la logica de negocio.
    private final ClasificadorController controlador = new ClasificadorController();

    // Componentes del formulario
    private final JTextField txtNombre = new JTextField();
    private final JTextField txtApellido = new JTextField();
    private final JTextArea txtDescripcion = new JTextArea(6, 30);

    // Componentes del panel de resultados
    private final JLabel lblSaludo = new JLabel(" ");
    private final JLabel lblModelo = new JLabel("Esperando descripcion...");
    private final JLabel lblConfianza = new JLabel(" ");
    private final JLabel lblDescripcionModelo = new JLabel(" ");
    private final JTextArea txtCoincidencias = new JTextArea(5, 30);
    private final JProgressBar[] barras = new JProgressBar[CloudServiceClassifier.MODELOS.length];
    private final JLabel[] etiquetasBarra = new JLabel[CloudServiceClassifier.MODELOS.length];

    public MainFrame() {
        setTitle("Cloud Models Classifier - IaaS / PaaS / SaaS / FaaS");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setMinimumSize(new Dimension(940, 660));
        setLocationRelativeTo(null);

        JPanel raiz = new JPanel(new BorderLayout(0, 0));
        raiz.setBackground(FONDO);

        raiz.add(crearEncabezado(), BorderLayout.NORTH);

        JPanel centro = new JPanel(new GridLayout(1, 2, 16, 0));
        centro.setBackground(FONDO);
        centro.setBorder(new EmptyBorder(16, 20, 20, 20));
        centro.add(crearPanelFormulario());
        centro.add(crearPanelResultados());

        raiz.add(centro, BorderLayout.CENTER);
        setContentPane(raiz);
    }

    // ------------------------------------------------------------------
    // ENCABEZADO
    // ------------------------------------------------------------------
    private JComponent crearEncabezado() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(AZUL);
        panel.setBorder(new EmptyBorder(18, 24, 18, 24));

        JLabel titulo = new JLabel("Clasificador de Modelos de Servicio en la Nube");
        titulo.setFont(new Font("SansSerif", Font.BOLD, 20));
        titulo.setForeground(Color.WHITE);

        JLabel subtitulo = new JLabel("Version 3 - Clasificador con NLP y CLI + validacion de entradas");
        subtitulo.setFont(new Font("SansSerif", Font.PLAIN, 12));
        subtitulo.setForeground(new Color(0xC8D6F5));

        JPanel textos = new JPanel(new GridLayout(2, 1));
        textos.setOpaque(false);
        textos.add(titulo);
        textos.add(subtitulo);

        panel.add(textos, BorderLayout.WEST);
        return panel;
    }

    // ------------------------------------------------------------------
    // PANEL IZQUIERDO: DATOS DEL USUARIO Y DESCRIPCION
    // ------------------------------------------------------------------
    private JComponent crearPanelFormulario() {
        JPanel panel = crearTarjeta("Datos del usuario y descripcion");
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.add(Box.createVerticalStrut(6));

        panel.add(crearEtiqueta("Nombre"));
        configurarCampo(txtNombre);
        panel.add(txtNombre);
        panel.add(Box.createVerticalStrut(10));

        panel.add(crearEtiqueta("Apellido"));
        configurarCampo(txtApellido);
        panel.add(txtApellido);
        panel.add(Box.createVerticalStrut(10));

        panel.add(crearEtiqueta("Describe el servicio de Cloud Computing"));
        txtDescripcion.setLineWrap(true);
        txtDescripcion.setWrapStyleWord(true);
        txtDescripcion.setFont(new Font("SansSerif", Font.PLAIN, 13));
        txtDescripcion.setBorder(new EmptyBorder(8, 8, 8, 8));

        JScrollPane scroll = new JScrollPane(txtDescripcion);
        scroll.setAlignmentX(Component.LEFT_ALIGNMENT);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(0xD5DBE7)));
        panel.add(scroll);
        panel.add(Box.createVerticalStrut(6));

        JLabel ayuda = new JLabel("<html><i>Ejemplo: \"Necesito maquinas virtuales con acceso root y almacenamiento en bloque\"</i></html>");
        ayuda.setFont(new Font("SansSerif", Font.PLAIN, 11));
        ayuda.setForeground(GRIS);
        ayuda.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(ayuda);
        panel.add(Box.createVerticalStrut(14));

        JPanel botones = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        botones.setOpaque(false);
        botones.setAlignmentX(Component.LEFT_ALIGNMENT);
        botones.setMaximumSize(new Dimension(Integer.MAX_VALUE, 44));

        JButton btnClasificar = new JButton("Clasificar");
        btnClasificar.setBackground(AZUL_CLARO);
        btnClasificar.setForeground(Color.WHITE);
        btnClasificar.setFocusPainted(false);
        btnClasificar.setFont(new Font("SansSerif", Font.BOLD, 13));
        btnClasificar.setPreferredSize(new Dimension(140, 36));
        btnClasificar.addActionListener(e -> ejecutarClasificacion());

        JButton btnLimpiar = new JButton("Limpiar");
        btnLimpiar.setFocusPainted(false);
        btnLimpiar.setPreferredSize(new Dimension(110, 36));
        btnLimpiar.addActionListener(e -> limpiarFormulario());

        botones.add(btnClasificar);
        botones.add(btnLimpiar);
        panel.add(botones);

        getRootPane().setDefaultButton(btnClasificar);
        return envolver(panel);
    }

    // ------------------------------------------------------------------
    // PANEL DERECHO: RESULTADO DE LA CLASIFICACION
    // ------------------------------------------------------------------
    private JComponent crearPanelResultados() {
        JPanel panel = crearTarjeta("Resultado de la clasificacion");
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.add(Box.createVerticalStrut(6));

        lblSaludo.setFont(new Font("SansSerif", Font.PLAIN, 12));
        lblSaludo.setForeground(GRIS);
        lblSaludo.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(lblSaludo);
        panel.add(Box.createVerticalStrut(8));

        lblModelo.setFont(new Font("SansSerif", Font.BOLD, 34));
        lblModelo.setForeground(AZUL);
        lblModelo.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(lblModelo);

        lblDescripcionModelo.setFont(new Font("SansSerif", Font.PLAIN, 12));
        lblDescripcionModelo.setForeground(TEXTO);
        lblDescripcionModelo.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(lblDescripcionModelo);

        lblConfianza.setFont(new Font("SansSerif", Font.PLAIN, 12));
        lblConfianza.setForeground(GRIS);
        lblConfianza.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(lblConfianza);
        panel.add(Box.createVerticalStrut(14));

        for (int i = 0; i < CloudServiceClassifier.MODELOS.length; i++) {
            String modelo = CloudServiceClassifier.MODELOS[i];

            JLabel etiqueta = new JLabel(modelo + ": 0% (0 pts)");
            etiqueta.setFont(new Font("SansSerif", Font.PLAIN, 12));
            etiqueta.setForeground(TEXTO);
            etiqueta.setAlignmentX(Component.LEFT_ALIGNMENT);
            etiquetasBarra[i] = etiqueta;
            panel.add(etiqueta);

            JProgressBar barra = new JProgressBar(0, 100);
            barra.setValue(0);
            barra.setForeground(AZUL_CLARO);
            barra.setAlignmentX(Component.LEFT_ALIGNMENT);
            barra.setMaximumSize(new Dimension(Integer.MAX_VALUE, 14));
            barras[i] = barra;
            panel.add(barra);
            panel.add(Box.createVerticalStrut(8));
        }

        panel.add(Box.createVerticalStrut(6));
        panel.add(crearEtiqueta("Palabras clave detectadas"));

        txtCoincidencias.setEditable(false);
        txtCoincidencias.setLineWrap(true);
        txtCoincidencias.setWrapStyleWord(true);
        txtCoincidencias.setFont(new Font("Monospaced", Font.PLAIN, 12));
        txtCoincidencias.setBackground(new Color(0xF9FAFC));
        txtCoincidencias.setBorder(new EmptyBorder(8, 8, 8, 8));

        JScrollPane scroll = new JScrollPane(txtCoincidencias);
        scroll.setAlignmentX(Component.LEFT_ALIGNMENT);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(0xD5DBE7)));
        panel.add(scroll);

        return envolver(panel);
    }

    // ------------------------------------------------------------------
    // LOGICA DE LA INTERFAZ (orquestacion de eventos, no de negocio)
    // ------------------------------------------------------------------

    /**
     * Pide al controlador que valide y clasifique; la GUI solo pinta el
     * resultado o el mensaje de error. Aqui es donde se manejan las
     * excepciones que vienen de la capa de logica.
     */
    private void ejecutarClasificacion() {
        try {
            ClasificadorController.SolicitudClasificacion solicitud = controlador.procesar(
                    txtNombre.getText(), txtApellido.getText(), txtDescripcion.getText());

            mostrarResultado(solicitud.getNombreCompleto(), solicitud.getResultado());

        } catch (EntradaInvalidaException errorValidacion) {
            // Datos del formulario incorrectos: el mensaje ya viene listo para el usuario.
            JOptionPane.showMessageDialog(this, errorValidacion.getMessage(),
                    "Datos incompletos", JOptionPane.WARNING_MESSAGE);

        } catch (ClasificacionException errorClasificacion) {
            // Fallo dentro del motor de clasificacion: se informa sin tumbar la app.
            JOptionPane.showMessageDialog(this,
                    "No fue posible clasificar el texto: " + errorClasificacion.getMessage(),
                    "Error al clasificar", JOptionPane.ERROR_MESSAGE);

        } catch (RuntimeException errorNoPrevisto) {
            // Ultima red de seguridad: cualquier otra falla no debe cerrar la ventana.
            JOptionPane.showMessageDialog(this,
                    "Ocurrio un error inesperado. Intenta de nuevo.",
                    "Error", JOptionPane.ERROR_MESSAGE);
        }
    }

    /** Pinta en pantalla un resultado ya calculado por el controlador. */
    private void mostrarResultado(String nombreCompleto, ResultadoClasificacion resultado) {
        lblSaludo.setText("Analisis para: " + nombreCompleto);
        lblModelo.setText(resultado.getModelo());
        lblDescripcionModelo.setText(describirModelo(resultado.getModelo()));

        if (ResultadoClasificacion.NO_DETERMINADO.equals(resultado.getModelo())) {
            lblModelo.setForeground(new Color(0xB4531A));
            lblConfianza.setText("No se encontraron terminos suficientes para clasificar el texto.");
        } else {
            lblModelo.setForeground(AZUL);
            String confianza = String.format("Confianza: %.0f%%", resultado.getConfianza() * 100);
            if (resultado.isEmpate()) {
                confianza += "  |  Atencion: hay empate entre modelos, el texto es ambiguo.";
            }
            lblConfianza.setText(confianza);
        }

        for (int i = 0; i < CloudServiceClassifier.MODELOS.length; i++) {
            String modelo = CloudServiceClassifier.MODELOS[i];
            int porcentaje = resultado.getPorcentaje(modelo);
            int puntos = resultado.getPuntajes().getOrDefault(modelo, 0);

            barras[i].setValue(porcentaje);
            barras[i].setForeground(modelo.equals(resultado.getModelo()) ? AZUL : new Color(0xA9BEE0));
            etiquetasBarra[i].setText(modelo + ": " + porcentaje + "% (" + puntos + " pts)");
        }

        StringBuilder detalle = new StringBuilder();
        for (Map.Entry<String, List<String>> entrada : resultado.getCoincidencias().entrySet()) {
            List<String> terminos = entrada.getValue();
            detalle.append(entrada.getKey()).append(" -> ");
            detalle.append(terminos.isEmpty() ? "(sin coincidencias)" : String.join(", ", terminos));
            detalle.append("\n");
        }
        txtCoincidencias.setText(detalle.toString());
        txtCoincidencias.setCaretPosition(0);
    }

    /** Devuelve una definicion corta del modelo detectado (texto de presentacion, no logica). */
    private String describirModelo(String modelo) {
        switch (modelo) {
            case CloudServiceClassifier.IAAS:
                return "<html>Infraestructura como Servicio: computo, red y almacenamiento virtualizados.</html>";
            case CloudServiceClassifier.PAAS:
                return "<html>Plataforma como Servicio: entorno gestionado para desarrollar y desplegar apps.</html>";
            case CloudServiceClassifier.SAAS:
                return "<html>Software como Servicio: aplicaciones listas para el usuario final.</html>";
            case CloudServiceClassifier.FAAS:
                return "<html>Funcion como Servicio: ejecucion de funciones por eventos, sin gestionar servidores.</html>";
            default:
                return "<html>Agrega mas detalles tecnicos para obtener una clasificacion.</html>";
        }
    }

    /** Restablece el formulario y el panel de resultados. */
    private void limpiarFormulario() {
        txtNombre.setText("");
        txtApellido.setText("");
        txtDescripcion.setText("");
        txtCoincidencias.setText("");
        lblSaludo.setText(" ");
        lblModelo.setText("Esperando descripcion...");
        lblModelo.setForeground(AZUL);
        lblDescripcionModelo.setText(" ");
        lblConfianza.setText(" ");
        for (int i = 0; i < barras.length; i++) {
            barras[i].setValue(0);
            barras[i].setForeground(AZUL_CLARO);
            etiquetasBarra[i].setText(CloudServiceClassifier.MODELOS[i] + ": 0% (0 pts)");
        }
        txtNombre.requestFocus();
    }

    // ------------------------------------------------------------------
    // METODOS AUXILIARES DE ESTILO
    // ------------------------------------------------------------------

    private JPanel crearTarjeta(String titulo) {
        JPanel panel = new JPanel();
        panel.setBackground(Color.WHITE);
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createTitledBorder(
                        BorderFactory.createLineBorder(new Color(0xDCE2ED)), titulo),
                new EmptyBorder(10, 14, 14, 14)));
        return panel;
    }

    private JComponent envolver(JPanel panel) {
        JPanel contenedor = new JPanel(new BorderLayout());
        contenedor.setBackground(FONDO);
        contenedor.add(panel, BorderLayout.CENTER);
        return contenedor;
    }

    private JLabel crearEtiqueta(String texto) {
        JLabel etiqueta = new JLabel(texto);
        etiqueta.setFont(new Font("SansSerif", Font.BOLD, 12));
        etiqueta.setForeground(TEXTO);
        etiqueta.setAlignmentX(Component.LEFT_ALIGNMENT);
        etiqueta.setBorder(new EmptyBorder(0, 0, 4, 0));
        return etiqueta;
    }

    private void configurarCampo(JTextField campo) {
        campo.setAlignmentX(Component.LEFT_ALIGNMENT);
        campo.setMaximumSize(new Dimension(Integer.MAX_VALUE, 32));
        campo.setFont(new Font("SansSerif", Font.PLAIN, 13));
        campo.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(0xD5DBE7)),
                new EmptyBorder(4, 8, 4, 8)));
    }
}
