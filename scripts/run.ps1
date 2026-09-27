param([switch]$Retrain, [switch]$Validate)
$ErrorActionPreference = 'Stop'
$MedflowRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $MedflowRoot
$MedflowPython = Join-Path $MedflowRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $MedflowPython)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' }
}
$MedflowLock = Join-Path $MedflowRoot 'requirements-lock.txt'
$MedflowLockHash = (Get-FileHash -LiteralPath $MedflowLock -Algorithm SHA256).Hash
$MedflowDependencyStamp = Join-Path $MedflowRoot '.venv\.medflow-dependencies.sha256'
$MedflowInstalledHash = if (Test-Path -LiteralPath $MedflowDependencyStamp) { (Get-Content -LiteralPath $MedflowDependencyStamp -Raw).Trim() } else { '' }
if ($MedflowInstalledHash -ne $MedflowLockHash) {
    & $MedflowPython -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    Set-Content -LiteralPath $MedflowDependencyStamp -Value $MedflowLockHash -Encoding ASCII
}
$MedflowArguments = @('-m', 'scripts.bootstrap')
if ($Retrain) { $MedflowArguments += '--retrain' }
if ($Validate) { $MedflowArguments += '--validate' }
& $MedflowPython @MedflowArguments
if ($LASTEXITCODE -ne 0) { throw 'Data/model preparation failed; see the error above.' }
& $MedflowPython -m streamlit run app.py
