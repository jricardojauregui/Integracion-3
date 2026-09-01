@echo off
REM Compila (si hace falta) y ejecuta la CLI del clasificador (Windows).
chcp 65001 >nul
if not exist out mkdir out
dir /s /b src\main\*.java > sources.txt
javac -encoding UTF-8 -d out @sources.txt
del sources.txt
java -Dfile.encoding=UTF-8 -cp out CloudClassifier %*
