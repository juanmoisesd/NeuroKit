@echo off
echo Generando ejecutable de PDF Voice Reader...
pip install pyinstaller
pyinstaller --noconsole --name "PDF Voice Reader" main.py
echo Compilacion terminada. El ejecutable se encuentra en la carpeta dist/
