@echo off
chcp 65001 >nul
echo ============================================================
echo   Pyron MVP - Apresentação Executiva Obsidian Frost
echo ============================================================
echo.
echo Abrindo visualizador web interativo e arquivo PowerPoint...
echo.
start "" "%~dp0visualizar_apresentacao.html"
start "" "%~dp0pyron_mvp_obsidian_frost.pptx"
exit
