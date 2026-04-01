#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # Fall back to script location for non-git repos
    return (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
}

function Get-CurrentBranch {
    # Resolve the actual git branch first. SPECIFY_FEATURE is handled separately
    # as the active spec workspace selector.
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # For non-git repos, try to find the latest feature directory
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot "specs"
    
    if (Test-Path $specsDir) {
        $featureDirs = Get-ChildItem -Path $specsDir -Directory |
            Where-Object { $_.Name -match '^(\d{3})-' }
        $latestFeature = $featureDirs |
            Sort-Object -Property @{ Expression = { [int]($_.Name -replace '^(\d+)-.*$', '$1') } } -Descending |
            Select-Object -First 1

        if ($latestFeature) {
            return $latestFeature.Name
        }
    }
    
    # Final fallback
    return "main"
}

function Resolve-ActiveFeatureName {
    param(
        [string]$RepoRoot,
        [string]$CurrentBranch
    )

    if ($env:SPECIFY_FEATURE) {
        return $env:SPECIFY_FEATURE
    }

    $specsDir = Join-Path $RepoRoot "specs"
    $branchFeatureDir = Join-Path $specsDir $CurrentBranch
    if ($CurrentBranch -and (Test-Path $branchFeatureDir -PathType Container)) {
        return $CurrentBranch
    }

    $masterFeatureDir = Join-Path $specsDir "master"
    if (Test-Path $masterFeatureDir -PathType Container) {
        return "master"
    }

    return $CurrentBranch
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[specify] Warning: Git repository not detected; skipped branch validation"
        return $true
    }
    
    $allowedPatterns = @(
        '^[0-9]{3}-',
        '^\d{4}-\d{2}-\d{2}-',
        '^(main|master)$'
    )

    $isAllowed = $false
    foreach ($pattern in $allowedPatterns) {
        if ($Branch -match $pattern) {
            $isAllowed = $true
            break
        }
    }

    if (-not $isAllowed) {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: 001-feature-name or 2026-03-05-feature-name"
        Write-Output "If the active spec workspace is not tied to the current git branch, set SPECIFY_FEATURE explicitly."
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot "specs/$Branch"
}

function Get-ModuleRolloutPath {
    param([string]$RepoRoot)
    Join-Path $RepoRoot '.specify/harness/module-rollout.json'
}

function Get-ModuleStatePath {
    param([string]$RepoRoot)
    Join-Path $RepoRoot '.specify/harness/module-state.json'
}

function Resolve-CurrentPlanModule {
    param(
        [string]$RepoRoot
    )

    $rolloutPath = Get-ModuleRolloutPath -RepoRoot $RepoRoot
    $statePath = Get-ModuleStatePath -RepoRoot $RepoRoot

    if (-not (Test-Path $rolloutPath -PathType Leaf) -or -not (Test-Path $statePath -PathType Leaf)) {
        return $null
    }

    try {
        $rollout = Get-Content -LiteralPath $rolloutPath -Raw -Encoding utf8 | ConvertFrom-Json
        $stateDoc = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    } catch {
        return $null
    }

    $orderedModules = @($rollout.modules | Sort-Object -Property order)
    foreach ($module in $orderedModules) {
        $moduleState = $stateDoc.module_states.PSObject.Properties[$module.module_key].Value
        if (-not $moduleState) {
            $moduleState = 'not_started'
        }

        if ($moduleState -notin @('browser_verified', 'done')) {
            return [PSCustomObject]@{
                MODULE_KEY = $module.module_key
                TASK_SLUG  = $module.task_slug
                STATE      = $moduleState
            }
        }
    }

    $lastModule = $orderedModules | Select-Object -Last 1
    if ($lastModule) {
        return [PSCustomObject]@{
            MODULE_KEY = $lastModule.module_key
            TASK_SLUG  = $lastModule.task_slug
            STATE      = $stateDoc.module_states.PSObject.Properties[$lastModule.module_key].Value
        }
    }

    return $null
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $activeFeature = Resolve-ActiveFeatureName -RepoRoot $repoRoot -CurrentBranch $currentBranch
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $activeFeature
    $plansDir = Join-Path $featureDir 'plans'
    $legacyPlan = Join-Path $featureDir 'plan.md'
    $currentModule = Resolve-CurrentPlanModule -RepoRoot $repoRoot
    $modulePlan = $null
    if ($currentModule -and $currentModule.TASK_SLUG) {
        $modulePlan = Join-Path $plansDir ("plan-" + $currentModule.TASK_SLUG + ".md")
    }
    $implPlan = if ($modulePlan) { $modulePlan } else { $legacyPlan }
    $activeModuleKey = $null
    $activeTaskSlug = $null
    if ($currentModule) {
        $activeModuleKey = $currentModule.MODULE_KEY
        $activeTaskSlug = $currentModule.TASK_SLUG
    }
    
    [PSCustomObject]@{
        REPO_ROOT      = $repoRoot
        CURRENT_BRANCH = $currentBranch
        ACTIVE_FEATURE = $activeFeature
        HAS_GIT        = $hasGit
        FEATURE_DIR    = $featureDir
        FEATURE_SPEC   = Join-Path $featureDir 'spec.md'
        IMPL_PLAN      = $implPlan
        LEGACY_PLAN    = $legacyPlan
        PLANS_DIR      = $plansDir
        MODULE_PLAN    = $modulePlan
        ACTIVE_MODULE  = $activeModuleKey
        ACTIVE_TASK_SLUG = $activeTaskSlug
        TASKS_DIR      = Join-Path $featureDir 'tasks'
        TASKS_FILE     = Join-Path $featureDir 'tasks.md'
        TASKS          = Join-Path $featureDir 'tasks'
        PD_ALL_DIR     = Join-Path $featureDir 'pd-all'
        AD_DIR         = Join-Path $featureDir 'ad'
        AD_FILE        = Join-Path $featureDir 'ad.md'
        DD_DIR         = Join-Path $featureDir 'dd'
        DD_FILE        = Join-Path $featureDir 'dd.md'
    }
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

