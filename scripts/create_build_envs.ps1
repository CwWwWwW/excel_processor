param(
  [string]$ModernPython = 'py -3.11-64',
  [string]$LegacyX64Python = 'py -3.8-64',
  [string]$LegacyX86Python = 'py -3.8-32'
)
$ErrorActionPreference = 'Stop'
$envs = @(
  @{Name='modern-x64'; Python=$ModernPython},
  @{Name='legacy-x64'; Python=$LegacyX64Python},
  @{Name='legacy-x86'; Python=$LegacyX86Python}
)
New-Item -ItemType Directory -Force -Path '.build-env' | Out-Null
foreach ($e in $envs) {
  $target = Join-Path '.build-env' $e.Name
  if (-not (Test-Path $target)) {
    Invoke-Expression "$($e.Python) -m venv `"$target`""
  }
  & "$target\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
}

