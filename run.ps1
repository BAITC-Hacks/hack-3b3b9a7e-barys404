param([switch]$Retrain, [switch]$Validate)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$MedflowPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $MedflowPython)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' }
    & $MedflowPython -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
$MedflowArguments = @('-m', 'src.bootstrap')
if ($Retrain) { $MedflowArguments += '--retrain' }
if ($Validate) { $MedflowArguments += '--validate' }
& $MedflowPython @MedflowArguments
if ($LASTEXITCODE -ne 0) { throw 'Data/model preparation failed; see the error above.' }
& $MedflowPython -m streamlit run app.py
