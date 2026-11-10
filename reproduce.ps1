param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
python (Join-Path $PSScriptRoot 'code/test_event_rules.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python (Join-Path $PSScriptRoot 'code/demo_synthetic.py') --output $Output
exit $LASTEXITCODE
