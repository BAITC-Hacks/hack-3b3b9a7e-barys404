# Compatibility launcher: the legacy Streamlit workflow lives in scripts/.
param([switch]$Retrain, [switch]$Validate)
& (Join-Path $PSScriptRoot 'scripts/run.ps1') @PSBoundParameters
