#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Module,

    [Parameter(Mandatory = $true)]
    [ValidateSet('not_started', 'ad_ready', 'dd_ready', 'tasks_ready', 'implementing', 'browser_verified', 'done')]
    [string]$State,

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

function Get-StateRank {
    param(
        [string[]]$StateOrder,
        [string]$Target
    )

    for ($index = 0; $index -lt $StateOrder.Count; $index++) {
        if ($StateOrder[$index] -eq $Target) {
            return $index
        }
    }

    return -1
}

$paths = Get-FeaturePathsEnv
$harnessDir = Join-Path $paths.REPO_ROOT '.specify/harness'
$rolloutPath = Join-Path $harnessDir 'module-rollout.json'
$statePath = Join-Path $harnessDir 'module-state.json'

$rollout = Read-JsonFile -Path $rolloutPath
$stateConfig = Read-JsonFile -Path $statePath

$targetModule = @($rollout.modules | Where-Object { $_.module_key -eq $Module }) | Select-Object -First 1
if (-not $targetModule) {
    throw "Module not found in rollout manifest: $Module"
}

$stateOrder = @($rollout.state_order)
$moduleStateMap = @{}
foreach ($entry in $stateConfig.module_states.PSObject.Properties) {
    $moduleStateMap[$entry.Name] = [string]$entry.Value
}

$currentState = if ($moduleStateMap.ContainsKey($Module)) {
    $moduleStateMap[$Module]
} else {
    'not_started'
}

$currentRank = Get-StateRank -StateOrder $stateOrder -Target $currentState
$targetRank = Get-StateRank -StateOrder $stateOrder -Target $State

if ($targetRank -lt 0) {
    throw "Unknown target state: $State"
}

if ($targetRank -gt ($currentRank + 1)) {
    throw "Illegal state transition: $currentState -> $State"
}

if ($State -eq 'implementing') {
    foreach ($otherModule in $moduleStateMap.Keys) {
        if ($otherModule -ne $Module -and $moduleStateMap[$otherModule] -eq 'implementing') {
            throw "Another module is already implementing: $otherModule"
        }
    }
}

foreach ($dependency in @($targetModule.depends_on)) {
    if ([string]::IsNullOrWhiteSpace([string]$dependency)) {
        continue
    }
    $dependencyState = if ($moduleStateMap.ContainsKey($dependency)) {
        $moduleStateMap[$dependency]
    } else {
        'not_started'
    }

    if ($targetRank -ge (Get-StateRank -StateOrder $stateOrder -Target 'implementing')) {
        if ($dependencyState -notin @('browser_verified', 'done')) {
            throw "Dependency not ready for ${Module}: $dependency is $dependencyState"
        }
    }
}

$moduleStateMap[$Module] = $State

$orderedStateMap = [ordered]@{}
foreach ($moduleItem in @($rollout.modules | Sort-Object order)) {
    $moduleKey = [string]$moduleItem.module_key
    $orderedStateMap[$moduleKey] = if ($moduleStateMap.ContainsKey($moduleKey)) {
        $moduleStateMap[$moduleKey]
    } else {
        'not_started'
    }
}

$newState = [ordered]@{
    version = $stateConfig.version
    updated_at = (Get-Date).ToUniversalTime().ToString('o')
    module_states = $orderedStateMap
}

$newState | ConvertTo-Json -Depth 6 | Set-Content -Path $statePath -Encoding UTF8

$result = [PSCustomObject]@{
    module_key = $Module
    previous_state = $currentState
    current_state = $State
    updated_at = $newState.updated_at
}

if ($Json) {
    $result | ConvertTo-Json -Depth 4
} else {
    Write-Output ("UPDATED: {0} {1} -> {2}" -f $Module, $currentState, $State)
    Write-Output ("UPDATED_AT: {0}" -f $newState.updated_at)
}
