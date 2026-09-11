param([switch]$Retrain)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$MedflowPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $MedflowPython)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' }
    & $MedflowPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
if ($Retrain) {
    & $MedflowPython -m src.train_waiting_model
} else {
    & $MedflowPython -m src.bootstrap
}
if ($LASTEXITCODE -ne 0) { throw 'Data/model preparation failed; see the error above.' }
& $MedflowPython -m streamlit run app.py
