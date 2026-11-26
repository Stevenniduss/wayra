@echo off
rem Crea la ejecucion de respaldo para la demo sin internet (RNF002).
cd /d "%~dp0.."
".venv\Scripts\python.exe" manage.py ejecutar_pronostico --gfs datos\respaldo\gfs_respaldo.npz --respaldo
