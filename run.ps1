# SeedFactory set-up and launcher for Windows (D-25, D-108).
#
#   powershell -ExecutionPolicy Bypass -File .\run.ps1 setup   set up everything, then stop
#   powershell -ExecutionPolicy Bypass -File .\run.ps1         set up what is missing, then start the app
#   powershell -ExecutionPolicy Bypass -File .\run.ps1 test    set up with the test packages, then run both test suites
#   -Dev                                                       also install the backend's test packages (setup and test always do)
#
# It assumes nothing is installed and skips every step that is already done:
#   1. Python 3.12 or newer, per user: winget, else the python.org installer. The Microsoft
#      Store's Python is passed over: Windows runs it in a package container whose children
#      break away from run.py's job object, so a killed launcher would leave the servers
#      running (D-78, D-108).
#   2. Node.js 22.18 or newer, per user: the official zip into %LOCALAPPDATA%\Programs\nodejs,
#      checked against nodejs.org's SHASUMS256.txt, and put on the user's PATH.
#   3. backend\.venv, made with pip (uv may be blocked by Windows Application Control).
#   4. The pinned Python packages, again only when the requirements file changes.
#   5. The frontend packages with npm ci, again only when package-lock.json changes.
# Then it hands over to run.py. Only the set-up needs the network; the app never does (NFR-2).
# Nothing needs admin rights.

param(
    [switch]$Dev,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # the progress bar slows Invoke-WebRequest down a great deal
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$venv = Join-Path $backend '.venv'
$python = Join-Path $venv 'Scripts\python.exe'

$PythonVersion = '3.12.10'          # the python.org installer used when winget is missing
$MinimumNode = [version]'22.18.0'   # the test runner and the rehearsal need 22.18 (operator-guide.md section 1)
$NodeHome = Join-Path $env:LOCALAPPDATA 'Programs\nodejs'

$command = if ($Rest -and $Rest.Count -gt 0) { $Rest[0] } else { '' }
$setupOnly = $command -eq 'setup'
if ($setupOnly -or $command -eq 'test') { $Dev = $true }
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'x64' }

function Write-Step([string]$message) {
    Write-Host "==> $message" -ForegroundColor Cyan
}

function Fail([string]$message) {
    Write-Host "Set-up stopped: $message" -ForegroundColor Red
    exit 1
}

function Update-SessionPath {
    # Pick up what an installer just added to PATH, keeping this session's own entries.
    $entries = @()
    foreach ($scope in @('Machine', 'User')) {
        $value = [Environment]::GetEnvironmentVariable('Path', $scope)
        if ($value) { $entries += $value -split ';' }
    }
    $entries += $env:Path -split ';'
    $env:Path = (@($entries | Where-Object { $_ } | Select-Object -Unique)) -join ';'
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

function Get-Download([string]$url, [string]$file) {
    try {
        Invoke-WebRequest -Uri $url -OutFile $file -UseBasicParsing
    } catch {
        Fail "could not download $url ($($_.Exception.Message)). The set-up needs the network once."
    }
}

# 1. Python

# Prints True for Python 3.12 or newer that is not the Microsoft Store's (D-108).
$PythonCheck = @('-c', "import sys; print(sys.version_info >= (3, 12) and 'WindowsApps' not in sys.base_prefix)")

function Find-Python {
    # The interpreter and its leading arguments, or $null. The Store's python.exe alias, and the
    # Store's Python itself, never pass the check.
    $check = $PythonCheck
    foreach ($candidate in @(@('py', '-3'), @('python'), @('python3'))) {
        $exe = Get-Command $candidate[0] -ErrorAction SilentlyContinue
        if (-not $exe) { continue }
        $prefix = @($candidate | Select-Object -Skip 1)
        if (Test-Native $exe.Source ($prefix + $check)) { return @($exe.Source) + $prefix }
    }
    # Installed but not on this session's PATH yet.
    $known = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python3*\python.exe'),
        (Join-Path $env:ProgramFiles 'Python3*\python.exe'),
        (Join-Path $env:APPDATA 'uv\python\cpython-3*\python.exe')
    )
    foreach ($pattern in $known) {
        foreach ($exe in @(Get-ChildItem $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)) {
            if (Test-Native $exe.FullName $check) { return @($exe.FullName) }
        }
    }
    return $null
}

function Install-Python {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Step 'Installing Python 3.12 for this user with winget'
        & winget install --exact --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
        Update-SessionPath
        if (Find-Python) { return }
        Write-Host 'winget did not give a working Python; trying the python.org installer.'
    }
    $suffix = if ($arch -eq 'arm64') { 'arm64' } else { 'amd64' }
    $installer = Join-Path $env:TEMP "python-$PythonVersion-$suffix.exe"
    Write-Step "Downloading Python $PythonVersion from python.org"
    Get-Download "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-$suffix.exe" $installer
    Write-Step "Installing Python $PythonVersion for this user"
    $process = Start-Process -FilePath $installer -Wait -PassThru -ArgumentList @(
        '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=1', 'InstallLauncherAllUsers=0', 'Include_test=0'
    )
    Remove-Item $installer -Force -ErrorAction SilentlyContinue
    if ($process.ExitCode -ne 0) { Fail "the Python installer exited with code $($process.ExitCode)." }
    Update-SessionPath
}

# 2. Node.js

function Get-NodeVersion {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) { return $null }
    try {
        $text = (& $node.Source --version 2>$null | Out-String).Trim().TrimStart('v')
        return [version]$text
    } catch {
        return $null
    }
}

function Install-Node {
    Write-Step 'Finding the current Node.js LTS release'
    try {
        $releases = Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json' -UseBasicParsing
    } catch {
        Fail "could not read https://nodejs.org/dist/index.json ($($_.Exception.Message)). The set-up needs the network once."
    }
    # index.json lists the newest release first; lts is false or the release line's name.
    $release = $releases | Where-Object { $_.lts -and ($_.files -contains "win-$arch-zip") } | Select-Object -First 1
    if (-not $release) { Fail "nodejs.org lists no LTS zip for win-$arch." }
    $version = $release.version
    $name = "node-$version-win-$arch"
    $zip = Join-Path $env:TEMP "$name.zip"
    $sums = Join-Path $env:TEMP "node-$version-SHASUMS256.txt"
    Write-Step "Downloading Node.js $version"
    Get-Download "https://nodejs.org/dist/$version/$name.zip" $zip
    Get-Download "https://nodejs.org/dist/$version/SHASUMS256.txt" $sums
    $expected = (Select-String -Path $sums -Pattern " $([regex]::Escape("$name.zip"))$" | Select-Object -First 1).Line -split '\s+' | Select-Object -First 1
    $actual = (Get-FileHash $zip -Algorithm SHA256).Hash
    if (-not $expected -or $actual -ne $expected.ToUpper()) {
        Remove-Item $zip, $sums -Force -ErrorAction SilentlyContinue
        Fail "the Node.js download does not match nodejs.org's checksum."
    }
    Write-Step "Installing Node.js $version into $NodeHome"
    $unpacked = Join-Path $env:TEMP "seedfactory-node-$version"
    if (Test-Path $unpacked) { Remove-Item -Recurse -Force $unpacked }
    Expand-Archive -Path $zip -DestinationPath $unpacked
    if (Test-Path $NodeHome) { Remove-Item -Recurse -Force $NodeHome }
    New-Item -ItemType Directory -Force (Split-Path $NodeHome) | Out-Null
    Move-Item (Join-Path $unpacked $name) $NodeHome
    Remove-Item $zip, $sums -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $unpacked -ErrorAction SilentlyContinue

    Add-UserPath $NodeHome
    $env:Path = "$NodeHome;$env:Path"
}

function Add-UserPath([string]$folder) {
    # First on the user's PATH for new windows. Written through the registry, not
    # [Environment]::SetEnvironmentVariable, so entries such as %USERPROFILE%\... stay unexpanded
    # and the value keeps its REG_EXPAND_SZ type.
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
    try {
        $raw = [string]$key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $entries = @($raw -split ';' | Where-Object { $_ })
        if ($entries -contains $folder) { return }
        $key.SetValue('Path', ((@($folder) + $entries) -join ';'), [Microsoft.Win32.RegistryValueKind]::ExpandString)
    } finally {
        $key.Close()
    }
    # Setting and clearing a variable this way tells open programs (Explorer) that the
    # environment changed, so new windows see the new PATH.
    [Environment]::SetEnvironmentVariable('SEEDFACTORY_SETUP', '1', 'User')
    [Environment]::SetEnvironmentVariable('SEEDFACTORY_SETUP', $null, 'User')
}

# Steps 1 and 2: the tools

Write-Step 'Checking Python 3.12 or newer (not the Microsoft Store one)'
# @(...) and the filter keep a one-item answer an array; PowerShell would unroll it into a string.
$base = @(Find-Python | Where-Object { $_ })
if ($base.Count -eq 0) {
    Install-Python
    $base = @(Find-Python | Where-Object { $_ })
    if ($base.Count -eq 0) { Fail 'Python 3.12 or newer is still not found. Install it from https://www.python.org/downloads/ and run this again.' }
}
Write-Host "    using $($base -join ' ')"

Write-Step "Checking Node.js $MinimumNode or newer"
$nodeVersion = Get-NodeVersion
if (-not $nodeVersion -and (Test-Path (Join-Path $NodeHome 'node.exe'))) {
    # Installed by an earlier run but not on this session's PATH yet.
    $env:Path = "$NodeHome;$env:Path"
    $nodeVersion = Get-NodeVersion
}
if (-not $nodeVersion -or $nodeVersion -lt $MinimumNode) {
    if ($nodeVersion) { Write-Host "    Node.js $nodeVersion is too old" }
    Install-Node
    $nodeVersion = Get-NodeVersion
    if (-not $nodeVersion -or $nodeVersion -lt $MinimumNode) {
        Fail "Node.js $MinimumNode or newer is still not first on the PATH. Remove the older Node.js, or put $NodeHome before it, and run this again."
    }
}
Write-Host "    using Node.js $nodeVersion"
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue)
if (-not $npm) { Fail 'npm was not found next to Node.js.' }

# Step 3: backend\.venv

Write-Step 'Checking backend\.venv'
# A venv made from the Store's Python is remade from the one found above (D-108).
$healthy = (Test-Path $python) -and (Test-Native $python $PythonCheck)
if (-not $healthy) {
    if (Test-Path $venv) {
        Write-Host '    backend\.venv does not work, or was made from the Microsoft Store Python; making it again'
        Remove-Item -Recurse -Force $venv
    }
    Write-Step 'Making backend\.venv'
    $prefix = @($base | Select-Object -Skip 1)
    & $base[0] @prefix -m venv $venv
    if ($LASTEXITCODE -ne 0) { Fail 'could not create backend\.venv.' }
}

# Step 4: the Python packages

$requirements = Join-Path $backend ($(if ($Dev) { 'requirements-dev.txt' } else { 'requirements.txt' }))
$stamp = Join-Path $venv ('.installed-' + [IO.Path]::GetFileName($requirements))
$hash = (Get-FileHash $requirements -Algorithm SHA256).Hash
if (-not (Test-Path $stamp) -or (Get-Content $stamp) -ne $hash) {
    Write-Step "Installing the Python packages ($([IO.Path]::GetFileName($requirements)))"
    # A venv that uv made has no pip of its own.
    if (-not (Test-Native $python @('-c', 'import pip; print(True)'))) { & $python -m ensurepip --upgrade | Out-Null }
    & $python -m pip install --upgrade pip --quiet --disable-pip-version-check
    & $python -m pip install -r $requirements --quiet --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { Fail 'pip install failed.' }
    Set-Content -Path $stamp -Value $hash -Encoding ascii
} else {
    Write-Host "    the Python packages are up to date"
}

if (-not (Test-Native $python @('-c', 'import fastapi, uvicorn; print(True)'))) {
    Fail 'the backend packages installed but will not import. If Smart App Control blocks them, try another Python version and delete backend\.venv.'
}

# Step 5: the frontend packages

$lock = Join-Path $frontend 'package-lock.json'
$modules = Join-Path $frontend 'node_modules'
$npmStamp = Join-Path $modules '.installed-package-lock'
$lockHash = (Get-FileHash $lock -Algorithm SHA256).Hash
if (-not (Test-Path $npmStamp) -or (Get-Content $npmStamp) -ne $lockHash) {
    Write-Step 'Installing the frontend packages (npm ci)'
    Push-Location $frontend
    try {
        & $npm.Source ci --no-audit --no-fund
        $npmExit = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($npmExit -ne 0) { Fail 'npm ci failed.' }
    Set-Content -Path $npmStamp -Value $lockHash -Encoding ascii
} else {
    Write-Host "    the frontend packages are up to date"
}

# Optional: Chrome or Edge, for the rehearsal only (operator-guide.md section 6)

$browsers = @(
    $env:CHROME,
    (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe')
) | Where-Object { $_ -and (Test-Path $_) }
if (-not $browsers) {
    Write-Host '    note: no Chrome or Edge found. Only the rehearsal (npm run rehearse) needs one; set CHROME to its path.' -ForegroundColor Yellow
}

if ($setupOnly) {
    Write-Host ''
    Write-Host 'SeedFactory is set up. Start it with:  powershell -ExecutionPolicy Bypass -File .\run.ps1' -ForegroundColor Green
    exit 0
}

& $python (Join-Path $root 'run.py') @Rest
exit $LASTEXITCODE
