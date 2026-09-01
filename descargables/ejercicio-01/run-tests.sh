#!/usr/bin/env bash
# Compila y corre la bateria de pruebas del clasificador (sin GUI).
set -e
mkdir -p out
javac -encoding UTF-8 -d out $(find src/main -name "*.java") $(find src/test -name "*.java")
LANG=C.UTF-8 LC_ALL=C.UTF-8 java -Dfile.encoding=UTF-8 -cp out com.udem.cloud.PruebasClasificador
