#!/usr/bin/env bash
# Compila y ejecuta la GUI (Linux / macOS)
set -e
mkdir -p out
javac -encoding UTF-8 -d out $(find src/main -name "*.java")
java -Dfile.encoding=UTF-8 -cp out com.udem.cloud.Main
