@echo off
rem Corre una ejecucion de WAYRA. El Programador de tareas de Windows lo llama cada 6 horas.
cd /d "%~dp0.."
if not exist salidas mkdir salidas
".venv\Scripts\python.exe" manage.py ejecutar_pronostico >> salidas\ejecuciones.log 2>&1
