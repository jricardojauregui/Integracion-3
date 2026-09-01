'use strict';

const multer = require('multer');
const path = require('path');
const crypto = require('crypto');

// Lista blanca cerrada: mimetype -> extensión FIJA que el servidor decide,
// nunca la extensión que venga en el nombre original del archivo del cliente.
const MIME_A_EXTENSION = {
  'image/jpeg': '.jpg',
  'image/png': '.png',
  'image/webp': '.webp'
};

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, '../../public/uploads'));
  },
  filename: (req, file, cb) => {
    // La extensión SIEMPRE sale de nuestra lista blanca según el mimetype ya
    // validado en fileFilter, nunca de file.originalname (dato del cliente).
    const ext = MIME_A_EXTENSION[file.mimetype];
    const nombreAleatorio = crypto.randomBytes(16).toString('hex');
    cb(null, `img_${Date.now()}_${nombreAleatorio}${ext}`);
  }
});

const fileFilter = (req, file, cb) => {
  if (Object.prototype.hasOwnProperty.call(MIME_A_EXTENSION, file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('Tipo de archivo no permitido. Solo se aceptan imágenes JPG, PNG o WebP.'), false);
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: 5 * 1024 * 1024 } // 5MB
});

module.exports = upload;
