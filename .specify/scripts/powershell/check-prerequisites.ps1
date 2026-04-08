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
#   -Module             Resolve plan paths for a specific module key/task slug
#   -RequirePlan        Require module plan to exist
#   -RequireTasks       Require tasks/ directory or tasks.md to exist (for implementation phase)
#   -IncludeTasks       Include tasks/ (or tasks.md) in AVAILABLE_DOCS list
#   -RequireDesign      Require pd-all/ + ai-pd/ + ad/ + dd/ (or ad.md / dd.md) to exist
#   -PathsOnly          Only output path variables (no validation)
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [string]$Module,
    [switch]$RequirePlan,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$RequireDesign,
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
  -Module             Resolve paths for a specific module key/task slug
  -RequirePlan        Require module plan to exist
  -RequireTasks       Require tasks.md to exist (for implementation phase)
  -IncludeTasks       Include tasks/ (or tasks.md) in AVAILABLE_DOCS list
  -RequireDesign      Require pd-all/ + ai-pd/ + ad/ + dd/ (or ad.md / dd.md) to exist
  -PathsOnly          Only output path variables (no prerequisite validation)
  -Help, -h           Show this help message

EXAMPLES:
  # Check a specific module plan
  .\check-prerequisites.ps1 -Json -RequirePlan -Module pd-intent-library

  # Check task prerequisites (spec.md + module plan + design docs required)
  .\check-prerequisites.ps1 -Json -RequirePlan -RequireDesign
  
  # Check implementation prerequisites (spec.md + module plan + design docs + tasks/ required)
  .\check-prerequisites.ps1 -Json -RequirePlan -RequireDesign -RequireTasks -IncludeTasks
  
  # Get feature paths only (no validation)
  .\check-prerequisites.ps1 -PathsOnly

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths and validate branch
$paths = Get-FeaturePathsEnv -Module $Module

if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) { 
    exit 1 
}

# If paths-only mode is used without validation requirements, output paths and exit
if ($PathsOnly -and -not ($RequirePlan -or $RequireTasks -or $RequireDesign)) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT    = $paths.REPO_ROOT
            BRANCH       = $paths.CURRENT_BRANCH
            ACTIVE_FEATURE = $paths.ACTIVE_FEATURE
            FEATURE_DIR  = $paths.FEATURE_DIR
            FEATURE_SPEC = $paths.FEATURE_SPEC
            IMPL_PLAN    = $paths.IMPL_PLAN
            LEGACY_PLAN  = $paths.LEGACY_PLAN
            PLANS_DIR    = $paths.PLANS_DIR
            MODULE_PLAN  = $paths.MODULE_PLAN
            REQUESTED_MODULE = $Module
            ACTIVE_MODULE = $paths.ACTIVE_MODULE
            ACTIVE_TASK_SLUG = $paths.ACTIVE_TASK_SLUG
            TASKS_DIR    = $paths.TASKS_DIR
            TASKS_FILE   = $paths.TASKS_FILE
            TASKS        = $paths.TASKS
            PD_ALL_DIR   = $paths.PD_ALL_DIR
            AI_PD_DIR  = $paths.AI_PD_DIR
            AD_DIR       = $paths.AD_DIR
            AD_FILE      = $paths.AD_FILE
            DD_DIR       = $paths.DD_DIR
            DD_FILE      = $paths.DD_FILE
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "ACTIVE_FEATURE: $($paths.ACTIVE_FEATURE)"
        Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
        Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
        Write-Output "LEGACY_PLAN: $($paths.LEGACY_PLAN)"
        Write-Output "PLANS_DIR: $($paths.PLANS_DIR)"
        Write-Output "MODULE_PLAN: $($paths.MODULE_PLAN)"
        Write-Output "REQUESTED_MODULE: $Module"
        Write-Output "ACTIVE_MODULE: $($paths.ACTIVE_MODULE)"
        Write-Output "ACTIVE_TASK_SLUG: $($paths.ACTIVE_TASK_SLUG)"
        Write-Output "TASKS_DIR: $($paths.TASKS_DIR)"
        Write-Output "TASKS_FILE: $($paths.TASKS_FILE)"
        Write-Output "TASKS: $($paths.TASKS)"
        Write-Output "PD_ALL_DIR: $($paths.PD_ALL_DIR)"
        Write-Output "AI_PD_DIR: $($paths.AI_PD_DIR)"
        Write-Output "AD_DIR: $($paths.AD_DIR)"
        Write-Output "AD_FILE: $($paths.AD_FILE)"
        Write-Output "DD_DIR: $($paths.DD_DIR)"
        Write-Output "DD_FILE: $($paths.DD_FILE)"
    }
    exit 0
}

# Validate required directories and files
if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Write-Output "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.specify first to create the feature structure."
    exit 1
}

if (-not (Test-Path $paths.FEATURE_SPEC -PathType Leaf)) {
    Write-Output "ERROR: spec.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.specify first to create the feature specification."
    exit 1
}

if ($RequirePlan) {
    if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
        $targetLabel = if ($Module) { $Module } else { 'active module' }
        Write-Output "ERROR: implementation plan not found for $targetLabel in $($paths.FEATURE_DIR)"
        Write-Output "Expected module plan path: $($paths.IMPL_PLAN)"
        Write-Output "Run /speckit.plan first to create the module implementation plan."
        exit 1
    }
}

if ($RequireDesign) {
    $hasPdAll = Test-Path $paths.PD_ALL_DIR -PathType Container
    $hasAiPd = Test-Path $paths.AI_PD_DIR -PathType Container
    $hasAd = (Test-Path $paths.AD_DIR -PathType Container) -or (Test-Path $paths.AD_FILE -PathType Leaf)
    $hasDd = (Test-Path $paths.DD_DIR -PathType Container) -or (Test-Path $paths.DD_FILE -PathType Leaf)

    if (-not $hasPdAll -or -not $hasAiPd -or -not $hasAd -or -not $hasDd) {
        Write-Output "ERROR: Required design documents are incomplete in $($paths.FEATURE_DIR)"
        Write-Output "Run /speckit.design-pd -> /speckit.transform-pd -> /speckit.design-ad -> /speckit.design-dd before continuing."
        exit 1
    }
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
if (Test-Path $paths.AI_PD_DIR -PathType Container) { $docs += 'ai-pd/' }
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
        BRANCH = $paths.CURRENT_BRANCH
        ACTIVE_FEATURE = $paths.ACTIVE_FEATURE
        FEATURE_DIR = $paths.FEATURE_DIR
        FEATURE_SPEC = $paths.FEATURE_SPEC
        IMPL_PLAN = $paths.IMPL_PLAN
        AI_PD_DIR = $paths.AI_PD_DIR
        REQUESTED_MODULE = $Module
        ACTIVE_MODULE = $paths.ACTIVE_MODULE
        ACTIVE_TASK_SLUG = $paths.ACTIVE_TASK_SLUG
        AVAILABLE_DOCS = $docs 
    } | ConvertTo-Json -Compress
} else {
    # Text output
    Write-Output "FEATURE_DIR:$($paths.FEATURE_DIR)"
    Write-Output "AI_PD_DIR:$($paths.AI_PD_DIR)"
    Write-Output "AVAILABLE_DOCS:"
    
    # Show status of design documents
    Test-DirHasFiles -Path $paths.PD_ALL_DIR -Description 'pd-all/' | Out-Null
    Test-DirHasFiles -Path $paths.AI_PD_DIR -Description 'ai-pd/' | Out-Null
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
