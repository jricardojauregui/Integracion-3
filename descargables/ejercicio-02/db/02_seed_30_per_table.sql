-- =====================================================================
-- 02_seed_30_per_table.sql
-- Datos sintéticos - Librería en línea
-- Ejecutar después de 00_create_database.sql y 01_schema.sql
-- Orden de inserción respeta las FK: catálogos -> libros -> tablas puente
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. USUARIOS (30 filas — exactamente un administrador)
-- ---------------------------------------------------------------------
INSERT INTO usuarios (nombre, email, password_hash, es_administrador, activo) VALUES
    ('Ana María López',      'ana.admin@libreria.com',      '$2b$12$Yq1ZbXkq9nQpQwR3v0m1EOeK3lX1r9m1v0mR3v0m1EOeK3lX1r9', TRUE,  TRUE),
    ('Carlos Hernández',     'carlos.hdz@correo.com',       '$2b$12$4fJ2xW9dQnR8pL3zT6yV0uO2sA1bC5dE7fG9hI1jK3lM5nO7pQ9', FALSE, TRUE),
    ('Daniela Torres',       'daniela.torres@correo.com',   '$2b$12$8kM4nP6qS8uW0yA2cE4gI6kM8oQ0sU2wY4aC6eG8iK0mO2qS4u1', FALSE, TRUE),
    ('Jorge Ramírez',        'jorge.ramirez@correo.com',    '$2b$12$1aB3cD5eF7gH9iJ1kL3mN5oP7qR9sT1uV3wX5yZ7aB9cD1eF3g2', FALSE, TRUE),
    ('Fernanda Castillo',    'fernanda.c@correo.com',       '$2b$12$9pQ1rS3tU5vW7xY9zA1bC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1v3', FALSE, TRUE),
    ('Luis Medina',          'luis.medina@correo.com',      '$2b$12$5wE7rT9yU1iO3pA5sD7fG9hJ1kL3zX5cV7bN9mM1qW3eR5tY7u4', FALSE, FALSE),
    ('Patricia Gómez',       'patricia.gomez@correo.com',   '$2b$12$3rT5yU7iO9pA1sD3fG5hJ7kL9zX1cV3bN5mM7qW9eR1tY3u5w6', FALSE, TRUE),
    ('Miguel Ángel Rosas',   'miguel.rosas@correo.com',     '$2b$12$7uY9iO1pA3sD5fG7hJ9kL1zX3cV5bN7mM9qW1eR3tY5u7w9y8', FALSE, TRUE),
    ('Valeria Cruz',         'valeria.cruz@correo.com',     '$2b$12$2sD4fG6hJ8kL0zX2cV4bN6mM8qW0eR2tY4u6w8y0a2c4e6g9', FALSE, TRUE),
    ('Ricardo Salinas',      'ricardo.salinas@correo.com',  '$2b$12$6hJ8kL0zX2cV4bN6mM8qW0eR2tY4u6w8y0a2c4e6g8i0k2m4', FALSE, TRUE),
    ('Sofía Delgado',        'sofia.delgado@correo.com',    '$2b$12$0zX2cV4bN6mM8qW0eR2tY4u6w8y0a2c4e6g8i0k2m4o6q8s0', FALSE, TRUE),
    ('Andrés Peña',          'andres.pena@correo.com',      '$2b$12$4bN6mM8qW0eR2tY4u6w8y0a2c4e6g8i0k2m4o6q8s0u2w4y6', FALSE, TRUE),
    ('Camila Reyes',         'camila.reyes@correo.com',     '$2b$12$8qW0eR2tY4u6w8y0a2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2', FALSE, TRUE),
    ('Diego Fuentes',        'diego.fuentes@correo.com',    '$2b$12$2tY4u6w8y0a2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8', FALSE, TRUE),
    ('Mariana Ortiz',        'mariana.ortiz@correo.com',    '$2b$12$6w8y0a2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0o2q4', FALSE, FALSE),
    ('Emilio Vargas',        'emilio.vargas@correo.com',    '$2b$12$0a2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0o2q4s6u8', FALSE, TRUE),
    ('Lucía Navarro',        'lucia.navarro@correo.com',    '$2b$12$4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0o2q4s6u8w0y2', FALSE, TRUE),
    ('Roberto Aguilar',      'roberto.aguilar@correo.com',  '$2b$12$8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0o2q4s6u8w0y2a4c6', FALSE, TRUE),
    ('Paola Jiménez',        'paola.jimenez@correo.com',    '$2b$12$2m4o6q8s0u2w4y6a8c0e2g4i6k8m0o2q4s6u8w0y2a4c6e8g0', FALSE, TRUE),
    ('Héctor Morales',       'hector.morales@correo.com',   '$2b$12$6q8s0u2w4y6a8c0e2g4i6k8m0o2q4s6u8w0y2a4c6e8g0i2k4', FALSE, TRUE),
    ('Adriana Silva',        'adriana.silva@correo.com',    '$2b$12$0u2w4y6a8c0e2g4i6k8m0o2q4s6u8w0y2a4c6e8g0i2k4m6o8', FALSE, TRUE),
    ('Iván Castro',          'ivan.castro@correo.com',      '$2b$12$4y6a8c0e2g4i6k8m0o2q4s6u8w0y2a4c6e8g0i2k4m6o8q0s2', FALSE, TRUE),
    ('Renata Flores',        'renata.flores@correo.com',    '$2b$12$8c0e2g4i6k8m0o2q4s6u8w0y2a4c6e8g0i2k4m6o8q0s2u4w6', FALSE, FALSE),
    ('Sebastián Ríos',       'sebastian.rios@correo.com',   '$2b$12$2g4i6k8m0o2q4s6u8w0y2a4c6e8g0i2k4m6o8q0s2u4w6y8a0', FALSE, TRUE),
    ('Ximena Molina',        'ximena.molina@correo.com',    '$2b$12$6i8k0m2o4q6s8u0w2y4a6c8e0g2i4k6m8o0q2s4u6w8y0a2c4', FALSE, TRUE),
    ('Tomás Guerrero',       'tomas.guerrero@correo.com',   '$2b$12$0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0o2q4s6u8w0y2a4c6e8', FALSE, TRUE),
    ('Natalia Campos',       'natalia.campos@correo.com',   '$2b$12$4m6o8q0s2u4w6y8a0c2e4g6i8k0m2o4q6s8u0w2y4a6c8e0g2', FALSE, TRUE),
    ('Federico Vega',        'federico.vega@correo.com',    '$2b$12$8o0q2s4u6w8y0a2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6', FALSE, TRUE),
    ('Gabriela Soto',        'gabriela.soto@correo.com',    '$2b$12$2q4s6u8w0y2a4c6e8g0i2k4m6o8q0s2u4w6y8a0c2e4g6i8k0', FALSE, TRUE),
    ('Alejandro Núñez',      'alejandro.nunez@correo.com',  '$2b$12$6s8u0w2y4a6c8e0g2i4k6m8o0q2s4u6w8y0a2c4e6g8i0k2m4', FALSE, TRUE);

-- ---------------------------------------------------------------------
-- 2. CATÁLOGOS INDEPENDIENTES: formatos (30) y géneros (30)
-- ---------------------------------------------------------------------
INSERT INTO formatos (nombre) VALUES
    ('Tapa dura'), ('Tapa blanda'), ('eBook'), ('Audiolibro'), ('Edición de bolsillo'),
    ('Edición de lujo'), ('Cómic'), ('Manga'), ('Novela gráfica'), ('Edición ilustrada'),
    ('Edición para niños'), ('Edición en braille'), ('Edición de coleccionista'),
    ('Edición digital interactiva'), ('Fascículo'), ('Edición bilingüe'), ('Edición anotada'),
    ('Edición facsímil'), ('Edición universitaria'), ('Edición de bolsillo grande'),
    ('Edición encuadernada en tela'), ('Edición encuadernada en piel'), ('Edición limitada'),
    ('Edición conmemorativa'), ('Edición escolar'), ('Edición de biblioteca'),
    ('Edición promocional'), ('Edición digital ePub'), ('Edición digital PDF'),
    ('Edición de autor firmada');

INSERT INTO generos (nombre) VALUES
    ('Novela'), ('Ciencia ficción'), ('Fantasía'), ('Realismo mágico'), ('Ensayo'),
    ('Distopía'), ('Historia'), ('Poesía'), ('Terror'), ('Misterio'),
    ('Policiaco'), ('Romance'), ('Aventura'), ('Biografía'), ('Autobiografía'),
    ('Filosofía'), ('Política'), ('Sociología'), ('Psicología'), ('Autoayuda'),
    ('Infantil'), ('Juvenil'), ('Cómic'), ('Manga'), ('Teatro'),
    ('Fábula'), ('Mitología'), ('Bélico'), ('Western'), ('Thriller');

-- ---------------------------------------------------------------------
-- 3. AUTORES (30)
-- ---------------------------------------------------------------------
INSERT INTO autores (nombre) VALUES
    ('Gabriel García Márquez'), ('Jorge Luis Borges'), ('Isabel Allende'), ('George Orwell'),
    ('Aldous Huxley'), ('Julio Cortázar'), ('Mario Vargas Llosa'), ('Ursula K. Le Guin'),
    ('Neil Gaiman'), ('Terry Pratchett'), ('Yuval Noah Harari'), ('Octavio Paz'),
    ('Pablo Neruda'), ('Gabriela Mistral'), ('Carlos Fuentes'), ('Juan Rulfo'),
    ('Laura Esquivel'), ('Elena Poniatowska'), ('Roberto Bolaño'), ('Ernesto Sabato'),
    ('Alejo Carpentier'), ('Miguel Ángel Asturias'), ('José Saramago'), ('Fernando Pessoa'),
    ('Jorge Amado'), ('Clarice Lispector'), ('Ray Bradbury'), ('Philip K. Dick'),
    ('Margaret Atwood'), ('Kazuo Ishiguro');

-- ---------------------------------------------------------------------
-- 4. CONCEPTOS (30 — términos reutilizables entre libros)
-- ---------------------------------------------------------------------
INSERT INTO conceptos (nombre) VALUES
    ('Realismo mágico'), ('Distopía'), ('Utopía'), ('Sátira'), ('Bildungsroman'),
    ('Multiverso'), ('Estado totalitario'), ('Metaficción'), ('Alegoría'), ('Antihéroe'),
    ('Flashback'), ('Prolepsis (anticipación narrativa)'), ('Ironía dramática'), ('Monólogo interior'),
    ('Narrador no confiable'), ('Simbolismo'), ('Arquetipo'), ('Paralelismo narrativo'),
    ('Analepsis'), ('Epílogo'), ('Prólogo'), ('Clímax narrativo'), ('Anticlímax'),
    ('Deus ex machina'), ('Leitmotiv'), ('Sinécdoque'), ('Metonimia'),
    ('Hipérbole literaria'), ('Personificación'), ('Verosimilitud');

-- ---------------------------------------------------------------------
-- 5. LIBROS (30)
-- ---------------------------------------------------------------------
INSERT INTO libros (isbn, titulo, anio_publicacion, precio, stock, id_formato) VALUES
    ('978-0-307-47472-8', 'Cien años de soledad',                              1967, 349.00, 40, 2),
    ('978-0-14-118776-4', 'Ficciones',                                          1944, 289.50, 25, 2),
    ('978-0-7432-7357-0', 'La casa de los espíritus',                          1982, 319.00, 18, 1),
    ('978-0-452-28423-4', '1984',                                              1949, 259.00, 60, 3),
    ('978-0-06-085052-4', 'Un mundo feliz',                                    1932, 249.00, 35, 2),
    ('978-84-376-0494-7', 'Rayuela',                                           1963, 329.00, 12, 1),
    ('978-0-374-27177-5', 'La ciudad y los perros',                            1963, 279.00, 22, 2),
    ('978-0-441-47812-7', 'La mano izquierda de la oscuridad',                 1969, 299.00, 15, 3),
    ('978-0-06-055812-9', 'American Gods',                                     2001, 359.00, 30, 4),
    ('978-0-06-220697-7', 'Mundodisco: ¡Guardias! ¡Guardias!',                 1989, 269.00, 20, 2),
    ('978-0-06-231609-7', 'Sapiens: de animales a dioses',                     2011, 399.00, 50, 1),
    ('978-968-411-090-1', 'El laberinto de la soledad',                        1950, 229.00, 16, 5),
    ('978-84-206-3141-5', 'Veinte poemas de amor y una canción desesperada',   1924, 179.00, 28, 1),
    ('978-956-13-1234-5', 'Desolación',                                        1922, 189.00, 14, 1),
    ('978-968-23-1002-0', 'La región más transparente',                        1958, 259.00, 10, 2),
    ('978-968-13-0001-1', 'Pedro Páramo',                                      1955, 219.00, 45, 2),
    ('978-968-06-0060-9', 'Como agua para chocolate',                          1989, 239.00, 33, 1),
    ('978-968-411-142-7', 'La noche de Tlatelolco',                            1971, 209.00, 9,  5),
    ('978-84-339-7196-9', '2666',                                              2004, 449.00, 17, 2),
    ('978-950-07-0100-3', 'El túnel',                                          1948, 199.00, 26, 2),
    ('978-84-8109-800-6', 'El reino de este mundo',                            1949, 229.00, 11, 1),
    ('978-968-16-0032-4', 'El señor presidente',                               1946, 219.00, 13, 2),
    ('978-0-15-100251-8', 'Ensayo sobre la ceguera',                           1995, 289.00, 21, 2),
    ('978-972-0-04292-4', 'El libro del desasosiego',                          1982, 259.00, 8,  5),
    ('978-85-01-06001-2', 'Gabriela, clavo y canela',                          1958, 229.00, 19, 2),
    ('978-85-01-05002-1', 'La hora de la estrella',                            1977, 189.00, 15, 2),
    ('978-0-345-34296-6', 'Fahrenheit 451',                                    1953, 249.00, 55, 3),
    ('978-0-345-40447-7', '¿Sueñan los androides con ovejas eléctricas?',      1968, 269.00, 24, 3),
    ('978-0-385-49081-8', 'El cuento de la criada',                            1985, 289.00, 38, 2),
    ('978-0-571-22414-4', 'Nunca me abandones',                                2005, 279.00, 20, 3);

-- ---------------------------------------------------------------------
-- 6. LIBRO_AUTOR (N:M — 30 relaciones base 1 libro:1 autor principal,
--    más 5 relaciones adicionales de coautoría/crédito compartido)
-- ---------------------------------------------------------------------
INSERT INTO libro_autor (isbn, id_autor) VALUES
    ('978-0-307-47472-8', 1),  ('978-0-14-118776-4', 2),   ('978-0-7432-7357-0', 3),
    ('978-0-452-28423-4', 4),  ('978-0-06-085052-4', 5),   ('978-84-376-0494-7', 6),
    ('978-0-374-27177-5', 7),  ('978-0-441-47812-7', 8),   ('978-0-06-055812-9', 9),
    ('978-0-06-220697-7', 10), ('978-0-06-231609-7', 11),  ('978-968-411-090-1', 12),
    ('978-84-206-3141-5', 13), ('978-956-13-1234-5', 14),  ('978-968-23-1002-0', 15),
    ('978-968-13-0001-1', 16), ('978-968-06-0060-9', 17),  ('978-968-411-142-7', 18),
    ('978-84-339-7196-9', 19), ('978-950-07-0100-3', 20),  ('978-84-8109-800-6', 21),
    ('978-968-16-0032-4', 22), ('978-0-15-100251-8', 23),  ('978-972-0-04292-4', 24),
    ('978-85-01-06001-2', 25), ('978-85-01-05002-1', 26),  ('978-0-345-34296-6', 27),
    ('978-0-345-40447-7', 28), ('978-0-385-49081-8', 29),  ('978-0-571-22414-4', 30),
    -- coautorías / créditos adicionales
    ('978-0-374-27177-5', 1),  ('978-968-06-0060-9', 3),   ('978-968-16-0032-4', 21),
    ('978-0-307-47472-8', 6),  ('978-0-345-34296-6', 28);

-- ---------------------------------------------------------------------
-- 7. LIBRO_GENERO (N:M — un libro puede pertenecer a varios géneros)
-- ---------------------------------------------------------------------
INSERT INTO libro_genero (isbn, id_genero) VALUES
    ('978-0-307-47472-8', 1), ('978-0-307-47472-8', 4),
    ('978-0-14-118776-4', 1), ('978-0-14-118776-4', 2),
    ('978-0-7432-7357-0', 1), ('978-0-7432-7357-0', 4),
    ('978-0-452-28423-4', 2), ('978-0-452-28423-4', 6),
    ('978-0-06-085052-4', 2),
    ('978-84-376-0494-7', 1),
    ('978-0-374-27177-5', 1),
    ('978-0-441-47812-7', 2), ('978-0-441-47812-7', 3),
    ('978-0-06-055812-9', 3), ('978-0-06-055812-9', 2),
    ('978-0-06-220697-7', 3),
    ('978-0-06-231609-7', 5), ('978-0-06-231609-7', 7),
    ('978-968-411-090-1', 5),
    ('978-84-206-3141-5', 8),
    ('978-956-13-1234-5', 8),
    ('978-968-23-1002-0', 1),
    ('978-968-13-0001-1', 1), ('978-968-13-0001-1', 4),
    ('978-968-06-0060-9', 1), ('978-968-06-0060-9', 4), ('978-968-06-0060-9', 12),
    ('978-968-411-142-7', 5), ('978-968-411-142-7', 7),
    ('978-84-339-7196-9', 1),
    ('978-950-07-0100-3', 1), ('978-950-07-0100-3', 10),
    ('978-84-8109-800-6', 1), ('978-84-8109-800-6', 4),
    ('978-968-16-0032-4', 1), ('978-968-16-0032-4', 17),
    ('978-0-15-100251-8', 1), ('978-0-15-100251-8', 6),
    ('978-972-0-04292-4', 5), ('978-972-0-04292-4', 16),
    ('978-85-01-06001-2', 1), ('978-85-01-06001-2', 12),
    ('978-85-01-05002-1', 1),
    ('978-0-345-34296-6', 2), ('978-0-345-34296-6', 6),
    ('978-0-345-40447-7', 2), ('978-0-345-40447-7', 6),
    ('978-0-385-49081-8', 2), ('978-0-385-49081-8', 6),
    ('978-0-571-22414-4', 2), ('978-0-571-22414-4', 1);

-- ---------------------------------------------------------------------
-- 8. LIBRO_IMAGEN (1 libro : N imágenes; exactamente una portada por
--    libro — 30 portadas + 10 imágenes secundarias = 40 filas)
-- ---------------------------------------------------------------------
INSERT INTO libro_imagen (isbn, url, alt_text, orden, es_portada) VALUES
    ('978-0-307-47472-8', 'https://cdn.libreria.com/img/cien-anos-portada.jpg',        'Portada de Cien años de soledad',            0, TRUE),
    ('978-0-307-47472-8', 'https://cdn.libreria.com/img/cien-anos-contra.jpg',         'Contraportada',                               1, FALSE),
    ('978-0-14-118776-4', 'https://cdn.libreria.com/img/ficciones-portada.jpg',        'Portada de Ficciones',                        0, TRUE),
    ('978-0-7432-7357-0', 'https://cdn.libreria.com/img/casa-espiritus-portada.jpg',   'Portada de La casa de los espíritus',         0, TRUE),
    ('978-0-452-28423-4', 'https://cdn.libreria.com/img/1984-portada.jpg',             'Portada de 1984',                             0, TRUE),
    ('978-0-452-28423-4', 'https://cdn.libreria.com/img/1984-lomo.jpg',                'Lomo del libro',                              1, FALSE),
    ('978-0-06-085052-4', 'https://cdn.libreria.com/img/mundo-feliz-portada.jpg',      'Portada de Un mundo feliz',                   0, TRUE),
    ('978-84-376-0494-7', 'https://cdn.libreria.com/img/rayuela-portada.jpg',          'Portada de Rayuela',                          0, TRUE),
    ('978-0-374-27177-5', 'https://cdn.libreria.com/img/ciudad-perros-portada.jpg',    'Portada de La ciudad y los perros',           0, TRUE),
    ('978-0-441-47812-7', 'https://cdn.libreria.com/img/mano-izquierda-portada.jpg',   'Portada de La mano izquierda de la oscuridad',0, TRUE),
    ('978-0-06-055812-9', 'https://cdn.libreria.com/img/american-gods-portada.jpg',    'Portada de American Gods',                    0, TRUE),
    ('978-0-06-055812-9', 'https://cdn.libreria.com/img/american-gods-back.jpg',       'Contraportada',                               1, FALSE),
    ('978-0-06-220697-7', 'https://cdn.libreria.com/img/guardias-portada.jpg',         'Portada de ¡Guardias! ¡Guardias!',            0, TRUE),
    ('978-0-06-231609-7', 'https://cdn.libreria.com/img/sapiens-portada.jpg',          'Portada de Sapiens',                          0, TRUE),
    ('978-968-411-090-1', 'https://cdn.libreria.com/img/laberinto-soledad-portada.jpg','Portada de El laberinto de la soledad',       0, TRUE),
    ('978-84-206-3141-5', 'https://cdn.libreria.com/img/veinte-poemas-portada.jpg',    'Portada de Veinte poemas de amor',            0, TRUE),
    ('978-956-13-1234-5', 'https://cdn.libreria.com/img/desolacion-portada.jpg',       'Portada de Desolación',                       0, TRUE),
    ('978-968-23-1002-0', 'https://cdn.libreria.com/img/region-transparente-portada.jpg','Portada de La región más transparente',     0, TRUE),
    ('978-968-13-0001-1', 'https://cdn.libreria.com/img/pedro-paramo-portada.jpg',     'Portada de Pedro Páramo',                     0, TRUE),
    ('978-968-13-0001-1', 'https://cdn.libreria.com/img/pedro-paramo-contra.jpg',      'Contraportada',                               1, FALSE),
    ('978-968-06-0060-9', 'https://cdn.libreria.com/img/agua-chocolate-portada.jpg',   'Portada de Como agua para chocolate',         0, TRUE),
    ('978-968-411-142-7', 'https://cdn.libreria.com/img/tlatelolco-portada.jpg',       'Portada de La noche de Tlatelolco',           0, TRUE),
    ('978-84-339-7196-9', 'https://cdn.libreria.com/img/2666-portada.jpg',             'Portada de 2666',                             0, TRUE),
    ('978-84-339-7196-9', 'https://cdn.libreria.com/img/2666-lomo.jpg',                'Lomo del libro',                              1, FALSE),
    ('978-950-07-0100-3', 'https://cdn.libreria.com/img/el-tunel-portada.jpg',         'Portada de El túnel',                         0, TRUE),
    ('978-84-8109-800-6', 'https://cdn.libreria.com/img/reino-mundo-portada.jpg',      'Portada de El reino de este mundo',           0, TRUE),
    ('978-968-16-0032-4', 'https://cdn.libreria.com/img/senor-presidente-portada.jpg', 'Portada de El señor presidente',              0, TRUE),
    ('978-0-15-100251-8', 'https://cdn.libreria.com/img/ceguera-portada.jpg',          'Portada de Ensayo sobre la ceguera',          0, TRUE),
    ('978-0-15-100251-8', 'https://cdn.libreria.com/img/ceguera-contra.jpg',           'Contraportada',                               1, FALSE),
    ('978-972-0-04292-4', 'https://cdn.libreria.com/img/desasosiego-portada.jpg',      'Portada de El libro del desasosiego',         0, TRUE),
    ('978-85-01-06001-2', 'https://cdn.libreria.com/img/gabriela-clavo-portada.jpg',   'Portada de Gabriela, clavo y canela',         0, TRUE),
    ('978-85-01-05002-1', 'https://cdn.libreria.com/img/hora-estrella-portada.jpg',    'Portada de La hora de la estrella',           0, TRUE),
    ('978-0-345-34296-6', 'https://cdn.libreria.com/img/fahrenheit-portada.jpg',       'Portada de Fahrenheit 451',                   0, TRUE),
    ('978-0-345-34296-6', 'https://cdn.libreria.com/img/fahrenheit-lomo.jpg',          'Lomo del libro',                              1, FALSE),
    ('978-0-345-40447-7', 'https://cdn.libreria.com/img/androides-portada.jpg',        'Portada de ¿Sueñan los androides...?',        0, TRUE),
    ('978-0-345-40447-7', 'https://cdn.libreria.com/img/androides-contra.jpg',         'Contraportada',                               1, FALSE),
    ('978-0-385-49081-8', 'https://cdn.libreria.com/img/cuento-criada-portada.jpg',    'Portada de El cuento de la criada',           0, TRUE),
    ('978-0-385-49081-8', 'https://cdn.libreria.com/img/cuento-criada-lomo.jpg',       'Lomo del libro',                              1, FALSE),
    ('978-0-571-22414-4', 'https://cdn.libreria.com/img/nunca-abandones-portada.jpg',  'Portada de Nunca me abandones',               0, TRUE),
    ('978-0-571-22414-4', 'https://cdn.libreria.com/img/nunca-abandones-contra.jpg',   'Contraportada',                               1, FALSE);

-- ---------------------------------------------------------------------
-- 9. LIBRO_CONCEPTO (definición propia por combinación libro+concepto;
--    31 filas — el mismo concepto aparece en varios libros con
--    definiciones distintas, demostrando la DF sobre clave compuesta)
-- ---------------------------------------------------------------------
INSERT INTO libro_concepto (isbn, id_concepto, definicion) VALUES
    ('978-0-307-47472-8', 1,  'En esta novela, el realismo mágico se manifiesta al narrar eventos sobrenaturales (levitaciones, lluvias de flores, fantasmas) como parte natural de la vida cotidiana de Macondo.'),
    ('978-0-14-118776-4', 8,  'En "Ficciones", Borges construye relatos que reflexionan sobre la propia naturaleza de la escritura y la ficción, un ejemplo temprano de metaficción.'),
    ('978-0-7432-7357-0', 1,  'Allende emplea el realismo mágico a través de dones como la clarividencia y la telequinesis de sus personajes, entrelazados con la historia política de Chile.'),
    ('978-0-452-28423-4', 2,  'La distopía de Orwell retrata un régimen de vigilancia total, manipulación del lenguaje (neolengua) y control absoluto del pasado por parte del Partido.'),
    ('978-0-452-28423-4', 7,  'El Estado totalitario en 1984 se sostiene mediante la Policía del Pensamiento, la propaganda constante y la figura omnipresente del Gran Hermano.'),
    ('978-0-06-085052-4', 2,  'La distopía de Huxley presenta una sociedad estable gracias al condicionamiento genético y al uso de soma, en lugar del terror explícito.'),
    ('978-84-376-0494-7', 8,  'Rayuela rompe la linealidad narrativa e invita al lector a elegir el orden de lectura, comentando su propia estructura como obra literaria.'),
    ('978-0-374-27177-5', 5,  'La novela sigue la formación moral y militar de sus jóvenes protagonistas en el colegio Leoncio Prado, un caso claro de Bildungsroman latinoamericano.'),
    ('978-0-441-47812-7', 6,  'Le Guin explora un multiverso cultural mediante planetas con organizaciones sociales y de género radicalmente distintas a las humanas conocidas.'),
    ('978-0-06-055812-9', 6,  'American Gods plantea un multiverso de deidades antiguas y nuevas que coexisten ocultas en la sociedad estadounidense contemporánea.'),
    ('978-0-06-220697-7', 4,  'Pratchett satiriza las estructuras de poder y la burocracia a través del humor absurdo de la Guardia de la Ciudad de Ankh-Morpork.'),
    ('978-0-06-231609-7', 3,  'Harari discute la utopía tecnológica y sus riesgos al analizar el futuro posible de la especie humana.'),
    ('978-968-411-090-1', 9,  'Paz utiliza la soledad como alegoría de la identidad mexicana y su relación histórica con la conquista y la modernidad.'),
    ('978-84-206-3141-5', 16, 'Neruda emplea un simbolismo intenso ligado a la naturaleza (mar, noche, viento) para expresar estados emocionales del amor y la pérdida.'),
    ('978-956-13-1234-5', 16, 'Mistral recurre a símbolos maternales y telúricos para expresar el dolor y la ternura en su poesía.'),
    ('978-968-23-1002-0', 17, 'Fuentes construye personajes que funcionan como arquetipos de las distintas clases sociales de la Ciudad de México en expansión.'),
    ('978-968-13-0001-1', 15, 'Rulfo utiliza un narrador no confiable y fragmentado, mezclando voces de vivos y muertos sin distinción explícita.'),
    ('978-968-06-0060-9', 1,  'Esquivel combina el realismo mágico con la cocina como vehículo de expresión emocional y sensorial.'),
    ('978-968-411-142-7', 18, 'Poniatowska emplea un paralelismo narrativo entre testimonios reales para reconstruir la masacre de Tlatelolco desde múltiples voces.'),
    ('978-84-339-7196-9', 14, 'Bolaño usa extensos monólogos interiores y digresiones para explorar la violencia y el mal en el norte de México.'),
    ('978-950-07-0100-3', 15, 'Sabato construye un narrador no confiable, obsesivo, cuya versión de los hechos se revela progresivamente distorsionada.'),
    ('978-84-8109-800-6', 1,  'Carpentier presenta lo "real maravilloso" caribeño, antecedente directo del realismo mágico latinoamericano.'),
    ('978-968-16-0032-4', 7,  'Asturias retrata un Estado totalitario latinoamericano sostenido por el culto a la personalidad del dictador.'),
    ('978-0-15-100251-8', 9,  'Saramago utiliza la ceguera colectiva como alegoría de la deshumanización social ante una crisis extrema.'),
    ('978-972-0-04292-4', 14, 'Pessoa, a través de su heterónimo Bernardo Soares, construye un extenso monólogo interior fragmentario y contemplativo.'),
    ('978-85-01-06001-2', 10, 'Gabriela funciona como una antiheroína que desafía las convenciones sociales de Ilhéus a través de su libertad personal.'),
    ('978-85-01-05002-1', 14, 'Lispector desarrolla un monólogo interior minimalista para narrar la conciencia precaria de su protagonista, Macabéa.'),
    ('978-0-345-34296-6', 2,  'Bradbury imagina una distopía donde los libros están prohibidos y quemados por bomberos del Estado.'),
    ('978-0-345-40447-7', 2,  'Dick plantea una distopía poblada por androides casi indistinguibles de humanos, cuestionando la empatía como rasgo definitorio.'),
    ('978-0-385-49081-8', 2,  'Atwood construye una distopía teocrática donde las mujeres fértiles son reducidas a su función reproductiva.'),
    ('978-0-571-22414-4', 10, 'Ishiguro presenta protagonistas que aceptan pasivamente su destino, funcionando como antihéroes trágicos de una distopía silenciosa.');

COMMIT;
