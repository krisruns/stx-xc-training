@echo off
:: deploy.bat
:: Double-click this to deploy the STX XC site to GitHub Pages
:: Place this file in the same folder as deploy.py and your git repo

cd /d "%~dp0"
python deploy.py
