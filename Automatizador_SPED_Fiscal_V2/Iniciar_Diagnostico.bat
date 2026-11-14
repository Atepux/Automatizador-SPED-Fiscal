@echo off
setlocal
cd /d "%~dp0"
set "SPED_PYTHON="
for /f "usebackq delims=" %%P in (`powershell.exe -NoProfile -Command "$c=ConvertFrom-Json -InputObject (Get-Content -LiteralPath '.\config\programa.json' -Raw -Encoding UTF8); Write-Output $c.python_executavel"`) do set "SPED_PYTHON=%%P"
if not exist "%SPED_PYTHON%" (
  echo Python configurado nao encontrado.
  pause
  exit /b 1
)
"%SPED_PYTHON%" "%~dp0principal.py"
set "SPED_RESULT=%ERRORLEVEL%"
pause
exit /b %SPED_RESULT%
