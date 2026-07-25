param([string]$Output = 'compatibility-results/local.json')
$ErrorActionPreference = 'Stop'
python scripts/export_compatibility_result.py --output $Output

