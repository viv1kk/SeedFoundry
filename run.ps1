# SeedFoundry launcher for Windows, for machines where uv is blocked.
#
#   powershell -ExecutionPolicy Bypass -File .\run.ps1          start both processes
#   powershell -ExecutionPolicy Bypass -File .\run.ps1 -Dev     also install test packages
#   powershell -ExecutionPolicy Bypass -File .\run.ps1 -Dev test   run both test suites
#
# It makes backend\.venv with pip, installs the pinned requirements only when
# the file has changed, then hands over to run.py.

param(
    [switch]$Dev,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$backend = Join-Path $root 'backend'
$venv = Join-Path $backend '.venv'
$python = Join-Path $venv 'Scripts\python.exe'

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error 'npm is not on the path. Install Node.js 22.18 or newer.'
}

function Test-Native([string]$exe, [string[]]$arguments) {
    # True when the command runs and prints True. Never throws.
    try {
        $out = & $exe @arguments 2>$null
        return ($LASTEXITCODE -eq 0 -and "$out".Trim() -eq 'True')
    } catch {
        return $false
    }
}

function Find-Python {
    $check = @('-c', 'import sys; print(sys.version_info >= (3, 12))')
    foreach ($candidate in @(@('py', '-3'), @('python'), @('python3'))) {
        $exe = Get-Command $candidate[0] -ErrorAction SilentlyContinue
        if (-not $exe) { continue }
        $prefix = @($candidate | Select-Object -Skip 1)
        if (Test-Native $exe.Source ($prefix + $check)) { return @($exe.Source) + $prefix }
    }
    Write-Error 'Python 3.12 or newer was not found on the path.'
}

$healthy = (Test-Path $python) -and (Test-Native $python @('-c', 'print(True)'))
if (-not $healthy) {
    if (Test-Path $venv) { Remove-Item -Recurse -Force $venv }
    $base = @(Find-Python)
    $prefix = @($base | Select-Object -Skip 1)
    & $base[0] @prefix -m venv $venv
    if ($LASTEXITCODE -ne 0) { Write-Error 'Could not create backend\.venv.' }
}

$requirements = Join-Path $backend ($(if ($Dev) { 'requirements-dev.txt' } else { 'requirements.txt' }))
$stamp = Join-Path $venv ('.installed-' + [IO.Path]::GetFileName($requirements))
$hash = (Get-FileHash $requirements -Algorithm SHA256).Hash
if (-not (Test-Path $stamp) -or (Get-Content $stamp) -ne $hash) {
    # A venv that uv made has no pip of its own.
    if (-not (Test-Native $python @('-c', 'import pip; print(True)'))) { & $python -m ensurepip --upgrade | Out-Null }
    & $python -m pip install --upgrade pip --quiet
    & $python -m pip install -r $requirements --quiet
    if ($LASTEXITCODE -ne 0) { Write-Error 'pip install failed.' }
    Set-Content -Path $stamp -Value $hash -Encoding ascii
}

if (-not (Test-Native $python @('-c', 'import fastapi, uvicorn; print(True)'))) {
    Write-Error 'The backend packages installed but will not import. If Smart App Control blocks them, try another Python version and delete backend\.venv.'
}

& $python (Join-Path $root 'run.py') @Rest
exit $LASTEXITCODE
