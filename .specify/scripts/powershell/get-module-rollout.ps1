#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$Module,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

function Read-JsonFile {
    param([string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) {
        throw "JSON file not found: $Path"
    }

    return Get-Content $Path -Raw | ConvertFrom-Json
}

$paths = Get-FeaturePathsEnv
$harnessDir = Join-Path $paths.REPO_ROOT '.specify/harness'
$rolloutPath = Join-Path $harnessDir 'module-rollout.json'
$statePath = Join-Path $harnessDir 'module-state.json'

$rollout = Read-JsonFile -Path $rolloutPath
$state = if (Test-Path $statePath -PathType Leaf) {
    Read-JsonFile -Path $statePath
} else {
    [PSCustomObject]@{
        version = 'bootstrap'
        module_states = [PSCustomObject]@{}
    }
}

$modules = @($rollout.modules | Sort-Object order)
$moduleStates = $state.module_states.PSObject.Properties
$moduleStateMap = @{}
foreach ($entry in $moduleStates) {
    $moduleStateMap[$entry.Name] = [string]$entry.Value
}

$mergedModules = foreach ($item in $modules) {
    $currentState = if ($moduleStateMap.ContainsKey($item.module_key)) {
        $moduleStateMap[$item.module_key]
    } else {
        'not_started'
    }

    $dependencyStates = @{}
    foreach ($dependency in @($item.depends_on)) {
        $dependencyStates[$dependency] = if ($moduleStateMap.ContainsKey($dependency)) {
            $moduleStateMap[$dependency]
        } else {
            'not_started'
        }
    }

    [PSCustomObject]@{
        module_key = $item.module_key
        task_slug = $item.task_slug
        display_name = $item.display_name
        order = [int]$item.order
        critical = [bool]$item.critical
        allow_parallel_design = [bool]$item.allow_parallel_design
        depends_on = @($item.depends_on)
        current_state = $currentState
        dependency_states = $dependencyStates
        browser_stage = $item.browser_stage
    }
}

$nextModule = $mergedModules |
    Where-Object { $_.current_state -notin @('browser_verified', 'done') } |
    Sort-Object order |
    Select-Object -First 1

if ($Module) {
    $selected = $mergedModules | Where-Object { $_.module_key -eq $Module }
    if (-not $selected) {
        throw "Module not found in rollout manifest: $Module"
    }

    if ($Json) {
        $selected | ConvertTo-Json -Depth 8
    } else {
        $selected | Format-List
    }

    exit 0
}

$summary = [PSCustomObject]@{
    active_feature = $paths.ACTIVE_FEATURE
    rollout_version = $rollout.version
    state_version = $state.version
    next_module = if ($nextModule) { $nextModule.module_key } else { $null }
    module_count = @($mergedModules).Count
    modules = @($mergedModules)
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 8
    exit 0
}

Write-Output "ACTIVE_FEATURE: $($summary.active_feature)"
Write-Output "NEXT_MODULE: $($summary.next_module)"
Write-Output "MODULE_COUNT: $($summary.module_count)"

foreach ($item in $mergedModules) {
    Write-Output ("- {0} state={1} deps=[{2}]" -f $item.module_key, $item.current_state, ($item.depends_on -join ', '))
}
