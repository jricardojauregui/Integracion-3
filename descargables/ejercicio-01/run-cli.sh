#!/usr/bin/env bash
# Compila (si hace falta) y ejecuta la version CLI del clasificador.
# Se fuerza LANG/LC_ALL a UTF-8 para evitar que acentos en el argumento
# lleguen corruptos si la terminal usa otra configuracion regional.
set -e
if [ ! -d out ] || [ -z "$(find out -name '*.class' 2>/dev/null)" ]; then
  mkdir -p out
  javac -encoding UTF-8 -d out $(find src/main -name "*.java")
fi
LANG=C.UTF-8 LC_ALL=C.UTF-8 java -Dfile.encoding=UTF-8 -cp out CloudClassifier "$@"
