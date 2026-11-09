@echo off
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  start "" "mira_personagem_3d.html"
  exit /b 0
)
echo Abrindo o Personagem 3D PYRON-01 (Mira-3D + HyperFrames) em http://localhost:8137/mira_personagem_3d.html
npx --yes http-server . -p 8137 -c-1 -o /mira_personagem_3d.html
