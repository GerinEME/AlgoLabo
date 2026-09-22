@echo off
cd /d "%~dp0"
python -m PyInstaller --onefile --windowed --name "AlgoLabo" --icon "resources\favicon.ico" --add-data "resources\favicon.ico:resources" algolabo.py
pause
