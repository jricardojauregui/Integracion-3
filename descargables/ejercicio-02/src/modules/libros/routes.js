'use strict';

const express = require('express');
const router = express.Router();
const controller = require('./controller');
const { isAuthenticated, isAdmin } = require('../../middleware/auth');
const upload = require('../../middleware/upload');

// Book listing and detail (authenticated)
router.get('/', isAuthenticated, controller.getLista);
router.get('/nuevo', isAuthenticated, isAdmin, controller.getNuevo);
router.post('/', isAuthenticated, isAdmin, controller.postNuevo);
router.get('/:isbn', isAuthenticated, controller.getDetalle);
router.get('/:isbn/editar', isAuthenticated, isAdmin, controller.getEditar);
router.put('/:isbn', isAuthenticated, isAdmin, controller.putEditar);
router.delete('/:isbn', isAuthenticated, isAdmin, controller.deleteLibro);

// Images
router.post('/:isbn/imagenes', isAuthenticated, isAdmin, upload.single('imagen'), controller.postAddImagen);
router.delete('/:isbn/imagenes/:id', isAuthenticated, isAdmin, controller.deleteImagen);

// Concepts
router.post('/:isbn/conceptos', isAuthenticated, isAdmin, controller.postAddConcepto);
router.delete('/:isbn/conceptos/:id_concepto', isAuthenticated, isAdmin, controller.deleteConcepto);

module.exports = router;
