'use strict';

const express = require('express');
const router = express.Router();
const controller = require('./controller');
const { isAuthenticated, isAdmin } = require('../../middleware/auth');

// Public routes
router.get('/login', controller.getLogin);
router.post('/login', controller.postLogin);
router.get('/logout', controller.getLogout);
router.get('/registro', controller.getRegistro);
router.post('/registro', controller.postRegistro);

// Admin routes
router.get('/', isAuthenticated, isAdmin, controller.getLista);
router.get('/:id/editar', isAuthenticated, isAdmin, controller.getEditar);
router.put('/:id', isAuthenticated, isAdmin, controller.putEditar);
router.delete('/:id', isAuthenticated, isAdmin, controller.deleteUsuario);

module.exports = router;
