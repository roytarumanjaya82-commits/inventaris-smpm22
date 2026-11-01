@echo off
cd /d "%~dp0"
echo Membuat InventarisSMPM22.exe ...
call .venv\Scripts\activate.bat
pip install -q pyinstaller
pyinstaller --noconfirm inventaris.spec
echo.
echo Selesai. File ada di: dist\InventarisSMPM22\
echo Jalankan: dist\InventarisSMPM22\InventarisSMPM22.exe
pause
