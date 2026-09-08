$ErrorActionPreference = 'Stop'
$labPath = $PSScriptRoot
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = Join-Path $labPath 'tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
python -B -m pip --isolated install --target (Join-Path $labPath 'deps') --cache-dir (Join-Path $labPath 'pip-cache') --disable-pip-version-check --retries 0 --no-compile --only-binary=:all: --require-hashes -r (Join-Path $labPath 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
