@echo off
REM Compila y ejecuta la GUI (Windows). Se activa la consola UTF-8 (chcp 65001)
REM para que los acentos se muestren y se lean bien.
chcp 65001 >nul
if not exist out mkdir out
dir /s /b src\main\*.java > sources.txt
javac -encoding UTF-8 -d out @sources.txt
del sources.txt
java -Dfile.encoding=UTF-8 -cp out com.udem.cloud.Main
