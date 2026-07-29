[CmdletBinding()]
param(
    [switch]$ForceInstall,
    [switch]$ForceFrontendBuild
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectDir

$EnvPath = Join-Path $ProjectDir ".env"
$RequirementsPath = Join-Path $ProjectDir "requirements.txt"
$BackendEntry = Join-Path $ProjectDir "backend\main.py"
$FrontendDir = Join-Path $ProjectDir "frontend"
$FrontendPackage = Join-Path $FrontendDir "package.json"
$FrontendLock = Join-Path $FrontendDir "package-lock.json"
$FrontendDistIndex = Join-Path $FrontendDir "dist\index.html"
$NodeModulesDir = Join-Path $FrontendDir "node_modules"
$NpmStamp = Join-Path $NodeModulesDir ".npm-installed.stamp"

$VenvDir = Join-Path $ProjectDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
$RequirementsStamp = Join-Path $VenvDir ".requirements-installed"

foreach ($RequiredFile in @(
    $EnvPath,
    $RequirementsPath,
    $BackendEntry,
    $FrontendPackage,
    $FrontendLock
)) {
    if (-not (Test-Path -LiteralPath $RequiredFile)) {
        throw "Missing required deployment file: $RequiredFile"
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "Creating Python virtual environment at $VenvDir ..."
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($Launcher) {
        & $Launcher.Source -3 -m venv $VenvDir
    }
    else {
        $Python = Get-Command python -ErrorAction Stop
        & $Python.Source -m venv $VenvDir
    }
}

if (-not (Test-Path -LiteralPath $ActivateScript)) {
    throw "Virtual environment activation script was not created: $ActivateScript"
}

. $ActivateScript

$NeedsPythonInstall = (
    $ForceInstall -or
    -not (Test-Path -LiteralPath $RequirementsStamp)
)
if (-not $NeedsPythonInstall) {
    $NeedsPythonInstall = (
        (Get-Item -LiteralPath $RequirementsPath).LastWriteTimeUtc -gt
        (Get-Item -LiteralPath $RequirementsStamp).LastWriteTimeUtc
    )
}

if ($NeedsPythonInstall) {
    Write-Host "Installing Python requirements ..."
    & $VenvPython -m pip install -r $RequirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw "Python dependency installation failed."
    }
    New-Item -ItemType File -Path $RequirementsStamp -Force | Out-Null
}
else {
    & $VenvPython -c "import fastapi, uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FastAPI/Uvicorn missing; reinstalling Python requirements ..."
        & $VenvPython -m pip install -r $RequirementsPath
        if ($LASTEXITCODE -ne 0) {
            throw "Python dependency installation failed."
        }
        New-Item -ItemType File -Path $RequirementsStamp -Force | Out-Null
    }
}

$Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $Npm) {
    throw "npm.cmd was not found. Install Node.js before deploying."
}

$NeedsNpmInstall = (
    $ForceInstall -or
    -not (Test-Path -LiteralPath $NodeModulesDir) -or
    -not (Test-Path -LiteralPath $NpmStamp)
)
if (-not $NeedsNpmInstall) {
    $NeedsNpmInstall = (
        (Get-Item -LiteralPath $FrontendLock).LastWriteTimeUtc -gt
        (Get-Item -LiteralPath $NpmStamp).LastWriteTimeUtc
    )
}

Push-Location -LiteralPath $FrontendDir
try {
    if ($NeedsNpmInstall) {
        Write-Host "Installing frontend dependencies with npm ci ..."
        & $Npm.Source ci
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend dependency installation failed."
        }
        New-Item -ItemType File -Path $NpmStamp -Force | Out-Null
    }

    $FrontendInputs = @(
        Get-ChildItem -LiteralPath (Join-Path $FrontendDir "src") -Recurse -File
    )
    $FrontendInputs += Get-Item -LiteralPath $FrontendPackage
    $FrontendInputs += Get-Item -LiteralPath $FrontendLock
    $FrontendInputs += Get-Item -LiteralPath (Join-Path $FrontendDir "index.html")
    $FrontendInputs += Get-Item -LiteralPath (Join-Path $FrontendDir "vite.config.js")
    $LatestInput = (
        $FrontendInputs |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    )

    $NeedsFrontendBuild = (
        $ForceFrontendBuild -or
        -not (Test-Path -LiteralPath $FrontendDistIndex)
    )
    if (-not $NeedsFrontendBuild) {
        $NeedsFrontendBuild = (
            $LatestInput.LastWriteTimeUtc -gt
            (Get-Item -LiteralPath $FrontendDistIndex).LastWriteTimeUtc
        )
    }

    if ($NeedsFrontendBuild) {
        Write-Host "Building React/Vite frontend ..."
        & $Npm.Source run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed."
        }
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $FrontendDistIndex)) {
    throw "Frontend build output missing: $FrontendDistIndex"
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Starting React/FastAPI application at http://127.0.0.1:8501"
& $VenvPython -m uvicorn backend.main:app `
    --host 127.0.0.1 `
    --port 8501
