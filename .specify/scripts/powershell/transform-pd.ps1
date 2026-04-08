#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$Feature,
    [string]$Module,
    [string]$OutputDir,
    [switch]$Stdout
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

$repoRoot = Get-RepoRoot
$currentBranch = Get-CurrentBranch
$activeFeature = if ($Feature) { $Feature } else { Resolve-ActiveFeatureName -RepoRoot $repoRoot -CurrentBranch $currentBranch }

$arguments = @(
    (Join-Path $repoRoot 'scripts/transform_pd.py')
    '--feature'
    $activeFeature
)

if ($Module) {
    $arguments += @('--module', $Module)
}

if ($OutputDir) {
    $arguments += @('--output-dir', $OutputDir)
}

if ($Stdout) {
    $arguments += '--stdout'
}

& python @arguments
exit $LASTEXITCODE
