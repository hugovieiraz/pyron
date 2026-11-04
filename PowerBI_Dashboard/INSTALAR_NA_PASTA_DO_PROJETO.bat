@echo off
chcp 65001 > nul
title Instalador Automatico Pyron---Embrapii (Power BI)
color 0A

set "TARGET_DIR=D:\hd_central\Antigravity projetos\brain\Obisidian_G\04 - Machine Learning\Projetos\Pyron---Embrapii\PowerBI_Dashboard"

echo ==============================================================================
echo   INSTALADOR DO DASHBOARD POWER BI -> PASTA DO PROJETO PYRON---EMBRAPII
echo ==============================================================================
echo.
echo Pasta de destino configurada:
echo   "%TARGET_DIR%"
echo.

if not exist "%TARGET_DIR%" (
    echo [1/3] Criando pasta PowerBI_Dashboard no projeto Pyron---Embrapii...
    mkdir "%TARGET_DIR%" 2>nul
)

if exist "%TARGET_DIR%" (
    echo [2/3] Copiando todos os arquivos do Dashboard e Modelo de Dados...
    xcopy /E /I /Y "%~dp0*" "%TARGET_DIR%\" > nul
    echo   -> Arquivos instalados com sucesso em:
    echo      %TARGET_DIR%
    echo.
    echo [3/3] Abrindo o Dashboard Interativo e o Power BI Desktop...
    start "" "%TARGET_DIR%\Dashboard_Pyron_Interativo.html"
    start "" "%TARGET_DIR%\Pyron_Dashboard.pbip"
) else (
    echo [AVISO] A unidade D: ou o caminho nao foi encontrado neste momento.
    echo Executando diretamente da pasta atual...
    start "" "%~dp0Dashboard_Pyron_Interativo.html"
    start "" "%~dp0Pyron_Dashboard.pbip"
)

echo.
echo ==============================================================================
echo   IMPORTANTE NO POWER BI DESKTOP:
echo   Como todos os dados ja estao embutidos internamente no modelo (Zero-Path),
echo   assim que o Power BI abrir e exibir a barra amarela, basta clicar no
echo   botao "Aplicar alteracoes" ou "Atualizar" (Pagina Inicial -> Atualizar).
echo   Ele NAO vai pedir nenhum arquivo externo e carregara os 28 graficos na hora!
echo ==============================================================================
echo.
pause
