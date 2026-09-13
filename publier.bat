@echo off
chcp 65001 >nul
setlocal
title Publication de fedex-powerbi

echo.
echo   ================================================================
echo    Publication du depot fedex-powerbi sur GitHub
echo   ================================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo   Git n'est pas installe sur cette machine.
  echo.
  echo   Installe-le depuis https://git-scm.com/download/win
  echo   puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

cd /d "%~dp0"
if not exist "README.md" (
  echo   Ce fichier doit etre place DANS le dossier fedex-powerbi,
  echo   a cote de README.md. Deplace-le et relance.
  echo.
  pause
  exit /b 1
)

echo   Dossier : %CD%
echo.

if not exist ".git" (
  git init -b main
  git remote add origin https://github.com/abdoulhamiddiallo/fedex-powerbi.git
) else (
  git remote remove origin 2>nul
  git remote add origin https://github.com/abdoulhamiddiallo/fedex-powerbi.git
)

git add -A
git -c user.name="Abdoul Hamid Diallo" -c user.email="diallohamid10@gmail.com" commit -m "MERIDIAN: a seven-page Power BI report on FedEx, generated from Python"
git branch -M main
git push -u origin main

echo.
if errorlevel 1 (
  echo   Le push a echoue. Si une fenetre de connexion GitHub s'est ouverte,
  echo   connecte-toi puis relance ce fichier.
) else (
  echo   Termine. Le depot est en ligne :
  echo   https://github.com/abdoulhamiddiallo/fedex-powerbi
)
echo.
pause
