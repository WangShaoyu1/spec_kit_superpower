#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [switch]$Launch,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

function Resolve-ExistingDir {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (Test-Path $candidate -PathType Container) {
            return $candidate
        }
    }

    return $Candidates[0]
}

function Resolve-BackendEntrypoint {
    param([string]$BackendDir)

    $mainPath = Join-Path $BackendDir 'app/main.py'
    if (Test-Path $mainPath -PathType Leaf) {
        $content = Get-Content $mainPath -Raw
        if ($content -match 'def\s+create_app') {
            return [PSCustomObject]@{
                target = 'app.main:create_app'
                args = @('-m', 'uvicorn', 'app.main:create_app', '--factory', '--reload')
                command = 'python -m uvicorn app.main:create_app --factory --reload'
            }
        }
    }

    return [PSCustomObject]@{
        target = 'app.main:app'
        args = @('-m', 'uvicorn', 'app.main:app', '--reload')
        command = 'python -m uvicorn app.main:app --reload'
    }
}

function Read-JsonFile {
    param([string]$Path)

    if (Test-Path $Path -PathType Leaf) {
        return Get-Content $Path -Raw | ConvertFrom-Json
    }

    return $null
}

$paths = Get-FeaturePathsEnv
$repoRoot = $paths.REPO_ROOT
$backendDir = Resolve-ExistingDir -Candidates @(
    (Join-Path $repoRoot 'backend')
)
$frontendDir = Resolve-ExistingDir -Candidates @(
    (Join-Path $repoRoot 'frontend')
)
$backendEntrypoint = Resolve-BackendEntrypoint -BackendDir $backendDir
$rollout = Read-JsonFile -Path (Join-Path $repoRoot '.specify/harness/module-rollout.json')
$state = Read-JsonFile -Path (Join-Path $repoRoot '.specify/harness/module-state.json')
$nextModule = if (-not $rollout) {
    throw "module-rollout.json not found. Cannot assemble rollout stack without the harness manifest."
}

$moduleStates = @{}
if ($state) {
    foreach ($entry in $state.module_states.PSObject.Properties) {
        $moduleStates[$entry.Name] = [string]$entry.Value
    }
}

$nextModule = @($rollout.modules | Sort-Object order | Where-Object {
    -not $moduleStates.ContainsKey($_.module_key) -or $moduleStates[$_.module_key] -notin @('browser_verified', 'done')
} | Select-Object -First 1).module_key | Select-Object -First 1

$backendPython = Join-Path $backendDir 'venv/Scripts/python.exe'
if (-not (Test-Path $backendPython -PathType Leaf)) {
    $backendPython = 'python'
}

$steps = @(
    [PSCustomObject]@{
        name = 'local-postgres'
        cwd = (Join-Path $repoRoot 'temp_data')
        command = 'python manage_services.py start'
    },
    [PSCustomObject]@{
        name = 'backend'
        cwd = $backendDir
        command = if ($backendPython -eq 'python') { $backendEntrypoint.command } else { "$backendPython $($backendEntrypoint.command.Substring(7))" }
    },
    [PSCustomObject]@{
        name = 'frontend'
        cwd = $frontendDir
        command = 'npm run dev'
    },
    [PSCustomObject]@{
        name = 'browser-stage-manual'
        cwd = $repoRoot
        command = "/speckit.smoke $nextModule"
        launch_supported = $false
    }
)

if ($Json) {
    [PSCustomObject]@{
        repo_root = $repoRoot
        launch = [bool]$Launch
        steps = $steps
    } | ConvertTo-Json -Depth 5
    exit 0
}

Write-Output "ROLLOUT STACK:"
foreach ($step in $steps) {
    Write-Output ("- {0}" -f $step.name)
    Write-Output ("  cwd: {0}" -f $step.cwd)
    Write-Output ("  command: {0}" -f $step.command)
}

if (-not $Launch) {
    Write-Output "TIP: add -Launch to start the local postgres/backend/frontend processes."
    exit 0
}

$pgScript = Join-Path $repoRoot 'temp_data/manage_services.py'
Start-Process -FilePath 'python' -ArgumentList @($pgScript, 'start') -WorkingDirectory (Join-Path $repoRoot 'temp_data') | Out-Null
Start-Process -FilePath $backendPython -ArgumentList $backendEntrypoint.args -WorkingDirectory $backendDir | Out-Null
Start-Process -FilePath 'pwsh' -ArgumentList @('-NoLogo', '-NoProfile', '-Command', 'npm run dev') -WorkingDirectory $frontendDir | Out-Null

Write-Output "STARTED: local-postgres, backend, frontend"
