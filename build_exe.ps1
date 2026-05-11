Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$python = 'd:/duifenyi/.venv/Scripts/python.exe'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name duidenyi `
  --collect-all bs4 `
  --collect-all lxml `
  main.py