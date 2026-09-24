param([switch]$Retrain, [switch]$Validate)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$MedflowPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $MedflowPython)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' }
}
$MedflowLock = Join-Path $PSScriptRoot 'requirements-lock.txt'
$MedflowLockHash = (Get-FileHash -LiteralPath $MedflowLock -Algorithm SHA256).Hash
$MedflowDependencyStamp = Join-Path $PSScriptRoot '.venv\.medflow-dependencies.sha256'
$MedflowInstalledHash = if (Test-Path -LiteralPath $MedflowDependencyStamp) { (Get-Content -LiteralPath $MedflowDependencyStamp -Raw).Trim() } else { '' }
if ($MedflowInstalledHash -ne $MedflowLockHash) {
    & $MedflowPython -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    Set-Content -LiteralPath $MedflowDependencyStamp -Value $MedflowLockHash -Encoding ASCII
}
$MedflowArguments = @('-m', 'src.bootstrap')
if ($Retrain) { $MedflowArguments += '--retrain' }
if ($Validate) { $MedflowArguments += '--validate' }
& $MedflowPython @MedflowArguments
if ($LASTEXITCODE -ne 0) { throw 'Data/model preparation failed; see the error above.' }
& $MedflowPython -m streamlit run app.py
