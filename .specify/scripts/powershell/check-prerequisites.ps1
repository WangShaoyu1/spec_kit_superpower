#!/usr/bin/env pwsh

# Consolidated prerequisite checking script (PowerShell)
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -RequireTasks       Require tasks/ directory or tasks.md to exist (for implementation phase)
#   -IncludeTasks       Include tasks/ (or tasks.md) in AVAILABLE_DOCS list
#   -PathsOnly          Only output path variables (no validation)
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: check-prerequisites.ps1 [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  -Json               Output in JSON format
  -RequireTasks       Require tasks.md to exist (for implementation phase)
  -IncludeTasks       Include tasks/ (or tasks.md) in AVAILABLE_DOCS list
  -PathsOnly          Only output path variables (no prerequisite validation)
  -Help, -h           Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  .\check-prerequisites.ps1 -Json
  
  # Check implementation prerequisites (plan.md + tasks/ required)
  .\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  
  # Get feature paths only (no validation)
  .\check-prerequisites.ps1 -PathsOnly

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths and validate branch
$paths = Get-FeaturePathsEnv

if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) { 
    exit 1 
}

# If paths-only mode, output paths and exit (support combined -Json -PathsOnly)
if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT    = $paths.REPO_ROOT
            BRANCH       = $paths.CURRENT_BRANCH
            FEATURE_DIR  = $paths.FEATURE_DIR
            FEATURE_SPEC = $paths.FEATURE_SPEC
            IMPL_PLAN    = $paths.IMPL_PLAN
            TASKS        = $paths.TASKS
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
        Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
        Write-Output "TASKS: $($paths.TASKS)"
    }
    exit 0
}

# Validate required directories and files
if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Write-Output "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.specify first to create the feature structure."
    exit 1
}

if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
    Write-Output "ERROR: plan.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.plan first to create the implementation plan."
    exit 1
}

# Check for tasks/ directory (or legacy tasks.md) if required
if ($RequireTasks) {
    $hasTasksDir = Test-Path $paths.TASKS_DIR -PathType Container
    $hasTasksFile = Test-Path $paths.TASKS_FILE -PathType Leaf
    if (-not $hasTasksDir -and -not $hasTasksFile) {
        Write-Output "ERROR: tasks/ directory (or tasks.md) not found in $($paths.FEATURE_DIR)"
        Write-Output "Run /speckit.tasks first to create the task list."
        exit 1
    }
}

# Build list of available documents
$docs = @()

# Design documents (new workflow: pd-all/, ad/, dd/)
if (Test-Path $paths.PD_ALL_DIR -PathType Container) { $docs += 'pd-all/' }
if (Test-Path $paths.AD_DIR -PathType Container) { $docs += 'ad/' }
elseif (Test-Path $paths.AD_FILE -PathType Leaf) { $docs += 'ad.md' }
if (Test-Path $paths.DD_DIR -PathType Container) { $docs += 'dd/' }
elseif (Test-Path $paths.DD_FILE -PathType Leaf) { $docs += 'dd.md' }

# Include tasks directory (or legacy tasks.md) if requested and it exists
if ($IncludeTasks) {
    if (Test-Path $paths.TASKS_DIR -PathType Container) { $docs += 'tasks/' }
    elseif (Test-Path $paths.TASKS_FILE -PathType Leaf) { $docs += 'tasks.md' }
}

# Output results
if ($Json) {
    # JSON output
    [PSCustomObject]@{ 
        FEATURE_DIR = $paths.FEATURE_DIR
        AVAILABLE_DOCS = $docs 
    } | ConvertTo-Json -Compress
} else {
    # Text output
    Write-Output "FEATURE_DIR:$($paths.FEATURE_DIR)"
    Write-Output "AVAILABLE_DOCS:"
    
    # Show status of design documents
    Test-DirHasFiles -Path $paths.PD_ALL_DIR -Description 'pd-all/' | Out-Null
    if (Test-Path $paths.AD_DIR -PathType Container) {
        Test-DirHasFiles -Path $paths.AD_DIR -Description 'ad/' | Out-Null
    } else {
        Test-FileExists -Path $paths.AD_FILE -Description 'ad.md' | Out-Null
    }
    if (Test-Path $paths.DD_DIR -PathType Container) {
        Test-DirHasFiles -Path $paths.DD_DIR -Description 'dd/' | Out-Null
    } else {
        Test-FileExists -Path $paths.DD_FILE -Description 'dd.md' | Out-Null
    }
    
    if ($IncludeTasks) {
        if (Test-Path $paths.TASKS_DIR -PathType Container) {
            Test-DirHasFiles -Path $paths.TASKS_DIR -Description 'tasks/' | Out-Null
        } else {
            Test-FileExists -Path $paths.TASKS_FILE -Description 'tasks.md' | Out-Null
        }
    }
}
