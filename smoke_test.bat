@echo off
echo.
echo  Iniciando FINOVA Smoke Test...
echo.

:: Criar venv se nao existir
if not exist ".venv\Scripts\activate.bat" (
    echo  Criando ambiente virtual...
    python -m venv .venv
)

:: Ativar venv
call .venv\Scripts\activate.bat

:: Instalar dependencias se httpx nao estiver instalado
python -c "import httpx" 2>nul || (
    echo  Instalando dependencias...
    pip install -r requirements.txt --quiet
)

:: Rodar smoke test
python scripts/smoke_test.py

pause
