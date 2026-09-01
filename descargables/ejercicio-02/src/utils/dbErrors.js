'use strict';

function mensajeAmigable(err) {
  switch (err.code) {
    case '23505': return 'Ya existe un registro con ese valor único (revisa el ISBN o el email).';
    case '23503': return 'La operación hace referencia a un registro que no existe.';
    case '23514': return 'Uno de los valores no cumple las reglas de negocio (revisa precio, stock o año).';
    case 'P0001': return err.message;
    default:
      console.error('Error de base de datos no mapeado:', err);
      return 'Ocurrió un error al procesar la operación. Intenta de nuevo.';
  }
}

module.exports = { mensajeAmigable };
