#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('ad', 'dd', 'tasks', 'implement', 'browser')]
    [string]$Stage,
    [string]$Module,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePathsEnv -Module $Module
$issues = New-Object System.Collections.Generic.List[object]

function Add-Issue {
    param(
        [string]$Code,
        [string]$Severity,
        [string]$Message,
        [string]$Path = '',
        [string]$Hint = ''
    )

    $issues.Add([PSCustomObject]@{
        code = $Code
        severity = $Severity
        message = $Message
        path = $Path
        hint = $Hint
    }) | Out-Null
}

function Read-TextFile {
    param([string]$Path)

    if (Test-Path $Path -PathType Leaf) {
        return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    }

    return ''
}

function Read-JsonFile {
    param([string]$Path)

    if (Test-Path $Path -PathType Leaf) {
        return Get-Content $Path -Raw | ConvertFrom-Json
    }

    return $null
}

function Get-ExistingFile {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-PdReadmes {
    param([string]$PdAllDir)

    if (-not (Test-Path $PdAllDir -PathType Container)) {
        return @()
    }

    return Get-ChildItem -Path $PdAllDir -Directory |
        ForEach-Object { Join-Path $_.FullName 'README.md' } |
        Where-Object { Test-Path $_ -PathType Leaf }
}

function Get-ModuleHtmlFiles {
    param([string]$ModuleDir)

    if (-not (Test-Path $ModuleDir -PathType Container)) {
        return @()
    }

    return @(Get-ChildItem -Path $ModuleDir -File -Filter '*.html' -ErrorAction SilentlyContinue)
}

function Get-ModuleStateValue {
    param(
        $StateConfig,
        [string]$ModuleKey
    )

    if (-not $StateConfig) {
        return ''
    }

    $entry = @($StateConfig.module_states.PSObject.Properties | Where-Object { $_.Name -eq $ModuleKey } | Select-Object -First 1)
    if ($entry.Count -eq 0) {
        return ''
    }

    return [string]$entry[0].Value
}

function Get-TargetTaskSlug {
    param(
        $TargetModuleConfig,
        [string]$RequestedModule,
        [string]$ActiveTaskSlug
    )

    if ($TargetModuleConfig -and $TargetModuleConfig.task_slug) {
        return [string]$TargetModuleConfig.task_slug
    }

    if (-not [string]::IsNullOrWhiteSpace($ActiveTaskSlug)) {
        return $ActiveTaskSlug
    }

    if (-not [string]::IsNullOrWhiteSpace($RequestedModule)) {
        return ($RequestedModule -replace '^pd-', '')
    }

    return ''
}

function Get-ModuleTasksPath {
    param(
        [string]$FeatureDir,
        [string]$TaskSlug
    )

    if ([string]::IsNullOrWhiteSpace($TaskSlug)) {
        return ''
    }

    $candidate = Join-Path (Join-Path $FeatureDir 'tasks') ("tasks-" + $TaskSlug + ".md")
    if (Test-Path $candidate -PathType Leaf) {
        return $candidate
    }

    return ''
}

function Get-ModuleAiPdPath {
    param(
        [string]$AiPdDir,
        [string]$TaskSlug
    )

    if ([string]::IsNullOrWhiteSpace($TaskSlug)) {
        return ''
    }

    $markdownCandidate = Join-Path $AiPdDir ("ai-" + $TaskSlug + ".md")
    if (Test-Path $markdownCandidate -PathType Leaf) {
        return $markdownCandidate
    }

    $yamlCandidate = Join-Path $AiPdDir ("ai-" + $TaskSlug + ".yaml")
    if (Test-Path $yamlCandidate -PathType Leaf) {
        return $yamlCandidate
    }

    return ''
}

function Get-ModuleAiPdChecklistPath {
    param(
        [string]$AiPdDir,
        [string]$TaskSlug
    )

    if ([string]::IsNullOrWhiteSpace($TaskSlug)) {
        return ''
    }

    $candidate = Join-Path $AiPdDir ("ai-" + $TaskSlug + ".checklist.md")
    if (Test-Path $candidate -PathType Leaf) {
        return $candidate
    }

    return ''
}

function Test-TasksReferencesPlan {
    param(
        [string]$TasksText,
        [string]$TaskSlug
    )

    if ([string]::IsNullOrWhiteSpace($TasksText) -or [string]::IsNullOrWhiteSpace($TaskSlug)) {
        return $false
    }

    $planFileName = "plan-$TaskSlug.md"
    return $TasksText -match [regex]::Escape($planFileName)
}

function Test-ReferencesModuleAiPd {
    param(
        [string]$Text,
        [string]$ModuleAiPdPath,
        [string]$TaskSlug
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $false
    }

    $candidates = New-Object System.Collections.Generic.List[string]

    if (-not [string]::IsNullOrWhiteSpace($TaskSlug)) {
        $candidates.Add(("ai-pd/ai-" + $TaskSlug + ".md")) | Out-Null
        $candidates.Add(("ai-pd/ai-" + $TaskSlug + ".yaml")) | Out-Null
        $candidates.Add(("ai-" + $TaskSlug + ".md")) | Out-Null
        $candidates.Add(("ai-" + $TaskSlug + ".yaml")) | Out-Null
    }

    if (-not [string]::IsNullOrWhiteSpace($ModuleAiPdPath)) {
        $fileName = [System.IO.Path]::GetFileName($ModuleAiPdPath)
        if (-not [string]::IsNullOrWhiteSpace($fileName)) {
            $candidates.Add($fileName) | Out-Null
        }
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if ($Text -match [regex]::Escape($candidate)) {
            return $true
        }
    }

    return $false
}

function Test-HasPageCapabilityChecklist {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $false
    }

    return (
        $Text -match '页面能力清单' -and
        $Text -match 'functional-hidden-ui|explanatory-only|interactive_containers|capability_checklist'
    )
}

function Test-PdContainsHiddenInteractions {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $false
    }

    return $Text -match 'Drawer|抽屉|Modal|弹窗|Popover|Collapse|说明抽屉|说明按钮'
}

function Get-MissingPageSemanticAnchors {
    param(
        [string]$ReadmeText,
        [string[]]$HtmlFileNames
    )

    $missing = New-Object System.Collections.Generic.List[string]

    if ([string]::IsNullOrWhiteSpace($ReadmeText)) {
        foreach ($htmlFileName in @($HtmlFileNames)) {
            $missing.Add(($htmlFileName + ':missing-section')) | Out-Null
        }
        return @($missing.ToArray())
    }

    foreach ($htmlFileName in @($HtmlFileNames)) {
        if ([string]::IsNullOrWhiteSpace($htmlFileName)) {
            continue
        }

        $pattern = '(?s)###\s+' + [regex]::Escape($htmlFileName) + '\s*(.*?)(?=\r?\n###\s+[a-z0-9-]+\.html|\r?\n##\s+|\z)'
        $match = [regex]::Match($ReadmeText, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if (-not $match.Success) {
            $missing.Add(($htmlFileName + ':missing-section')) | Out-Null
            continue
        }

        $sectionText = $match.Groups[1].Value
        if ($sectionText -notmatch [regex]::Escape('`page_goal`')) {
            $missing.Add(($htmlFileName + ':page_goal')) | Out-Null
        }
        if ($sectionText -notmatch [regex]::Escape('`primary_user_flows`')) {
            $missing.Add(($htmlFileName + ':primary_user_flows')) | Out-Null
        }
    }

    return @($missing.ToArray())
}

$pdIndexPath = Join-Path $paths.PD_ALL_DIR 'pd-index.md'
$aiPdReadmePath = Join-Path $paths.AI_PD_DIR 'README.md'
$rulesPath = Join-Path $paths.REPO_ROOT '.cursor/rules/specify-rules.mdc'
$rolloutPath = Join-Path $paths.REPO_ROOT '.specify/harness/module-rollout.json'
$moduleStatePath = Join-Path $paths.REPO_ROOT '.specify/harness/module-state.json'
$planText = Read-TextFile -Path $paths.IMPL_PLAN
$rulesText = Read-TextFile -Path $rulesPath
$rolloutConfig = Read-JsonFile -Path $rolloutPath
$moduleStateConfig = Read-JsonFile -Path $moduleStatePath
$targetModuleConfig = $null
$targetModuleState = ''
$moduleReadmeText = ''
$moduleHtmlText = ''
$moduleAiPdPath = ''
$moduleAiPdChecklistPath = ''

if (-not (Test-Path $paths.FEATURE_SPEC -PathType Leaf)) {
    Add-Issue -Code 'GATE-COMMON-001' -Severity 'BLOCKER' -Message 'spec.md 缺失，无法进入下一阶段。' -Path $paths.FEATURE_SPEC -Hint '先运行 /speckit.specify 或补齐 spec.md'
}

if (-not (Test-Path $paths.PD_ALL_DIR -PathType Container)) {
    Add-Issue -Code 'GATE-COMMON-002' -Severity 'BLOCKER' -Message 'pd-all/ 缺失，无法进入设计与实现阶段。' -Path $paths.PD_ALL_DIR -Hint '先运行 /speckit.design-pd'
}

if (-not (Test-Path $pdIndexPath -PathType Leaf)) {
    Add-Issue -Code 'GATE-COMMON-003' -Severity 'BLOCKER' -Message 'pd-index.md 缺失，无法建立模块索引。' -Path $pdIndexPath -Hint '补齐 pd-all/pd-index.md'
}

if (-not (Test-Path $paths.AI_PD_DIR -PathType Container)) {
    Add-Issue -Code 'GATE-COMMON-005' -Severity 'BLOCKER' -Message 'ai-pd/ 缺失，无法把 HumanPD 转为 AI 主输入。' -Path $paths.AI_PD_DIR -Hint '先运行 /speckit.transform-pd 或补齐 ai-pd/'
}

if ((Test-Path $paths.AI_PD_DIR -PathType Container) -and -not (Test-Path $aiPdReadmePath -PathType Leaf)) {
    Add-Issue -Code 'GATE-COMMON-006' -Severity 'BLOCKER' -Message 'ai-pd/ 缺少 README.md，无法建立 AI-PD 模块索引。' -Path $aiPdReadmePath -Hint '补齐 ai-pd/README.md'
}

if ($rulesText -match 'PD_FEATURE_GAP_ROOT_CAUSE_ANALYSIS') {
    Add-Issue -Code 'GATE-COMMON-004' -Severity 'BLOCKER' -Message '规则文件仍引用已失效文档。' -Path $rulesPath -Hint '移除失效引用或改为当前有效规则来源'
}

$pdRiskFiles = @()
$pdReadmes = Get-PdReadmes -PdAllDir $paths.PD_ALL_DIR
foreach ($readmePath in $pdReadmes) {
    $content = Read-TextFile -Path $readmePath
    if ($content -match '部分覆盖|待补充|待确认|条件准入') {
        $pdRiskFiles += $readmePath
        if ($content -notmatch 'AD/DD 准入声明|条件准入') {
            Add-Issue -Code 'GATE-PD-001' -Severity 'BLOCKER' -Message 'PD README 含风险标记，但缺少显式准入声明。' -Path $readmePath -Hint '补充 AD/DD 准入声明'
        }
    }
}

$pdModuleDirs = Get-ChildItem -Path $paths.PD_ALL_DIR -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'pd-*' }
foreach ($pdModuleDir in @($pdModuleDirs)) {
    $moduleReadmePath = Join-Path $pdModuleDir.FullName 'README.md'
    if (-not (Test-Path $moduleReadmePath -PathType Leaf)) {
        continue
    }

    $moduleHtmlFiles = Get-ModuleHtmlFiles -ModuleDir $pdModuleDir.FullName
    if ($moduleHtmlFiles.Count -eq 0) {
        continue
    }

    $missingPageAnchors = Get-MissingPageSemanticAnchors -ReadmeText (Read-TextFile -Path $moduleReadmePath) -HtmlFileNames @($moduleHtmlFiles | ForEach-Object { $_.Name })
    if ($missingPageAnchors.Count -gt 0) {
        Add-Issue -Code 'GATE-PD-003' -Severity 'BLOCKER' -Message ('PD 页面能力清单缺少必填页面语义字段 `page_goal / primary_user_flows`: ' + ($missingPageAnchors -join ', ')) -Path $moduleReadmePath -Hint '为每个 HTML 页面补齐 README 中对应的 `page_goal` 与 `primary_user_flows`'
    }
}

$targetTaskSlug = ''
$moduleTasksPath = ''
$moduleTasksText = ''

$pdIndexText = Read-TextFile -Path $pdIndexPath
if ($pdIndexText -match '条件准入|部分覆盖') {
    $pdRiskFiles += $pdIndexPath
}

$pdRiskFiles = $pdRiskFiles | Select-Object -Unique
if ($pdRiskFiles.Count -gt 0) {
    Add-Issue -Code 'GATE-PD-002' -Severity 'WARNING' -Message ('当前存在条件准入模块: ' + ($pdRiskFiles -join '; ')) -Hint '下游文档必须显式继承风险，不得默认为已闭环'
}

if ($Module) {
    if (-not $rolloutConfig) {
        Add-Issue -Code 'GATE-MODULE-001' -Severity 'BLOCKER' -Message 'module-rollout.json 缺失，无法执行模块级主控。' -Path $rolloutPath -Hint '先补齐 .specify/harness/module-rollout.json'
    } else {
        $targetModuleConfig = @($rolloutConfig.modules | Where-Object { $_.module_key -eq $Module } | Select-Object -First 1)
        if (-not $targetModuleConfig) {
            Add-Issue -Code 'GATE-MODULE-001' -Severity 'BLOCKER' -Message '目标模块未登记到 module-rollout.json。' -Path $rolloutPath -Hint '先把目标模块加入 rollout manifest'
        }
    }

    if (-not $moduleStateConfig) {
        Add-Issue -Code 'GATE-MODULE-002' -Severity 'BLOCKER' -Message 'module-state.json 缺失，无法判断模块当前状态。' -Path $moduleStatePath -Hint '先初始化 .specify/harness/module-state.json'
    } else {
        $targetModuleState = Get-ModuleStateValue -StateConfig $moduleStateConfig -ModuleKey $Module
        if (-not $targetModuleState) {
            Add-Issue -Code 'GATE-MODULE-002' -Severity 'BLOCKER' -Message '目标模块未在 module-state.json 中登记状态。' -Path $moduleStatePath -Hint '先为目标模块补齐状态'
        }
    }

    $moduleDir = Join-Path $paths.PD_ALL_DIR $Module
    $moduleReadmePath = Join-Path $moduleDir 'README.md'
    $moduleHtmlFiles = Get-ModuleHtmlFiles -ModuleDir $moduleDir
    $moduleReadmeText = Read-TextFile -Path $moduleReadmePath
    $moduleHtmlText = ($moduleHtmlFiles | ForEach-Object { Read-TextFile -Path $_.FullName }) -join "`n"
    if (
        -not (Test-Path $moduleDir -PathType Container) -or
        -not (Test-Path $moduleReadmePath -PathType Leaf) -or
        $moduleHtmlFiles.Count -eq 0
    ) {
        Add-Issue -Code 'GATE-MODULE-003' -Severity 'BLOCKER' -Message '目标模块缺少 PD 目录、README 或 HTML 原型。' -Path $moduleDir -Hint '补齐 pd-all 目标模块的 README.md 与至少一个 HTML 原型'
    }

    if ($pdIndexText -and $pdIndexText -notmatch [regex]::Escape($Module)) {
        Add-Issue -Code 'GATE-MODULE-003' -Severity 'BLOCKER' -Message '目标模块未出现在 pd-index.md 中。' -Path $pdIndexPath -Hint '先把模块登记到 pd-index.md'
    }

    $targetTaskSlug = Get-TargetTaskSlug -TargetModuleConfig $targetModuleConfig -RequestedModule $Module -ActiveTaskSlug $paths.ACTIVE_TASK_SLUG
    $moduleTasksPath = Get-ModuleTasksPath -FeatureDir $paths.FEATURE_DIR -TaskSlug $targetTaskSlug
    $moduleTasksText = Read-TextFile -Path $moduleTasksPath
    $moduleAiPdPath = Get-ModuleAiPdPath -AiPdDir $paths.AI_PD_DIR -TaskSlug $targetTaskSlug
    $moduleAiPdChecklistPath = Get-ModuleAiPdChecklistPath -AiPdDir $paths.AI_PD_DIR -TaskSlug $targetTaskSlug

    if (-not $moduleAiPdPath) {
        Add-Issue -Code 'GATE-MODULE-006' -Severity 'BLOCKER' -Message '目标模块缺少 ai-<module>.md / yaml，无法作为 AI 主输入继续下游阶段。' -Path $paths.AI_PD_DIR -Hint '为目标模块生成 ai-pd/ai-<module>.md'
    }

    if (-not $moduleAiPdChecklistPath) {
        Add-Issue -Code 'GATE-MODULE-007' -Severity 'BLOCKER' -Message '目标模块缺少 ai-<module>.checklist.md，无法进入 AI-PD 人工校对约束链。' -Path $paths.AI_PD_DIR -Hint '为目标模块生成 ai-pd/ai-<module>.checklist.md'
    }

    if ($targetModuleConfig -and $moduleStateConfig -and $Stage -in @('implement', 'browser')) {
        $dependencyIssues = @()
        foreach ($dependency in @($targetModuleConfig.depends_on)) {
            if ([string]::IsNullOrWhiteSpace([string]$dependency)) {
                continue
            }
            $dependencyState = Get-ModuleStateValue -StateConfig $moduleStateConfig -ModuleKey $dependency
            if ($dependencyState -notin @('browser_verified', 'done')) {
                $dependencyIssues += ("{0}={1}" -f $dependency, $(if ($dependencyState) { $dependencyState } else { 'not_started' }))
            }
        }

        if ($dependencyIssues.Count -gt 0) {
            Add-Issue -Code 'GATE-MODULE-004' -Severity 'BLOCKER' -Message ('目标模块依赖尚未通过浏览器门禁: ' + ($dependencyIssues -join ', ')) -Path $moduleStatePath -Hint '先完成依赖模块的 implement + browser 阶段'
        }

        $otherImplementingModules = @(
            $moduleStateConfig.module_states.PSObject.Properties |
                Where-Object { $_.Name -ne $Module -and $_.Value -eq 'implementing' } |
                ForEach-Object { $_.Name }
        )
        if ($otherImplementingModules.Count -gt 0) {
            Add-Issue -Code 'GATE-MODULE-005' -Severity 'BLOCKER' -Message ('已有其它模块占用 implement 资源锁: ' + ($otherImplementingModules -join ', ')) -Path $moduleStatePath -Hint '等待当前 implementing 模块完成后再推进'
        }
    }
}

switch ($Stage) {
    'dd' {
        $adEntry = Get-ExistingFile -Candidates @($paths.AD_FILE, $paths.AD_DIR)
        if (-not $adEntry) {
            Add-Issue -Code 'GATE-DD-001' -Severity 'BLOCKER' -Message '进入 DD 前缺少 AD 产物。' -Path $paths.AD_DIR -Hint '先运行 /speckit.design-ad'
        }
    }
    'tasks' {
        $adEntry = Get-ExistingFile -Candidates @($paths.AD_FILE, $paths.AD_DIR)
        $ddEntry = Get-ExistingFile -Candidates @($paths.DD_FILE, $paths.DD_DIR)

        if (-not $adEntry) {
            Add-Issue -Code 'GATE-DD-001' -Severity 'BLOCKER' -Message '生成 tasks 前缺少 AD 产物。' -Path $paths.AD_DIR -Hint '先运行 /speckit.design-ad'
        }

        if (-not $ddEntry) {
            Add-Issue -Code 'GATE-DD-001' -Severity 'BLOCKER' -Message '生成 tasks 前缺少 DD 产物。' -Path $paths.DD_DIR -Hint '先运行 /speckit.design-dd'
        }

        if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
            $planIssueCode = if ($Module) { 'GATE-PLAN-001' } else { 'GATE-TASKS-001' }
            Add-Issue -Code $planIssueCode -Severity 'BLOCKER' -Message '当前模块实施计划缺失，无法生成任务。' -Path $paths.IMPL_PLAN -Hint '先运行 /speckit.plan 生成 plans/plan-<module>.md'
        } elseif ($planText -notmatch '核心业务链路|真实成功信号') {
            Add-Issue -Code 'GATE-TASKS-001' -Severity 'BLOCKER' -Message '当前模块实施计划未显式定义核心业务链路或真实成功信号。' -Path $paths.IMPL_PLAN -Hint '在模块 plan 中补齐核心业务链路与真实成功信号'
        }

        if ($Module) {
            if (-not $moduleTasksPath) {
                Add-Issue -Code 'GATE-PLAN-002' -Severity 'BLOCKER' -Message '当前模块缺少与目标 plan 对应的 tasks-<module>.md 文件。' -Path (Join-Path $paths.TASKS_DIR ("tasks-$targetTaskSlug.md")) -Hint '先生成模块级 tasks 文件，再继续实现'
            } elseif (-not (Test-TasksReferencesPlan -TasksText $moduleTasksText -TaskSlug $targetTaskSlug)) {
                Add-Issue -Code 'GATE-PLAN-002' -Severity 'BLOCKER' -Message '模块 tasks 未显式引用对应的模块 plan，计划链路不可追踪。' -Path $moduleTasksPath -Hint '在 tasks 文件头部补齐 plans/plan-<module>.md 输入引用'
            }

            if (-not (Test-ReferencesModuleAiPd -Text $planText -ModuleAiPdPath $moduleAiPdPath -TaskSlug $targetTaskSlug)) {
                Add-Issue -Code 'GATE-AIPD-001' -Severity 'BLOCKER' -Message '当前模块 plan 未显式引用 AI-PD，无法保证下游基于 AI 主输入规划。' -Path $paths.IMPL_PLAN -Hint '在 plan 中补齐 ai-pd/ai-<module>.md 输入引用'
            }

            if (-not (Test-ReferencesModuleAiPd -Text $moduleTasksText -ModuleAiPdPath $moduleAiPdPath -TaskSlug $targetTaskSlug)) {
                Add-Issue -Code 'GATE-AIPD-002' -Severity 'BLOCKER' -Message '模块 tasks 未显式引用 AI-PD，任务拆解仍停留在直接读 HumanPD。' -Path $moduleTasksPath -Hint '在 tasks 文件中补齐 ai-pd/ai-<module>.md 输入引用'
            }

            if ((Test-PdContainsHiddenInteractions -Text ($moduleReadmeText + "`n" + $moduleHtmlText)) -and (-not (Test-HasPageCapabilityChecklist -Text $planText))) {
                Add-Issue -Code 'GATE-PLAN-003' -Severity 'BLOCKER' -Message '当前模块 plan 缺少页面能力清单或未显式标记 functional-hidden-ui / explanatory-only。' -Path $paths.IMPL_PLAN -Hint '在模块 plan 中补齐页面能力清单，并显式区分隐藏交互分类'
            }

            if ((Test-PdContainsHiddenInteractions -Text ($moduleReadmeText + "`n" + $moduleHtmlText)) -and (-not (Test-HasPageCapabilityChecklist -Text $moduleTasksText))) {
                Add-Issue -Code 'GATE-PLAN-004' -Severity 'BLOCKER' -Message '模块 tasks 未显式继承页面能力清单中的 functional-hidden-ui。' -Path $moduleTasksPath -Hint '在 tasks 文件中补齐页面能力承接矩阵与隐藏交互任务'
            }
        }

        if ($pdRiskFiles.Count -gt 0 -and $planText -notmatch 'FR-050|部分覆盖|条件准入|Deferred|Out of Scope|Blocked By|Partial|待补齐|显式未完成') {
            Add-Issue -Code 'GATE-TASKS-002' -Severity 'BLOCKER' -Message 'PD 条件准入/部分覆盖尚未在当前模块 plan 中显式继承。' -Path $paths.IMPL_PLAN -Hint '把 PD 风险写入模块 plan 的风险/未完成声明'
        }
    }
    'implement' {
        $adEntry = Get-ExistingFile -Candidates @($paths.AD_FILE, $paths.AD_DIR)
        $ddEntry = Get-ExistingFile -Candidates @($paths.DD_FILE, $paths.DD_DIR)
        $tasksEntry = Get-ExistingFile -Candidates @($paths.TASKS_DIR, $paths.TASKS_FILE)

        if (-not $adEntry) {
            Add-Issue -Code 'GATE-DD-001' -Severity 'BLOCKER' -Message '进入实现前缺少 AD 产物。' -Path $paths.AD_DIR -Hint '先运行 /speckit.design-ad'
        }

        if (-not $ddEntry) {
            Add-Issue -Code 'GATE-DD-001' -Severity 'BLOCKER' -Message '进入实现前缺少 DD 产物。' -Path $paths.DD_DIR -Hint '先运行 /speckit.design-dd'
        }

        if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
            $planIssueCode = if ($Module) { 'GATE-PLAN-001' } else { 'GATE-TASKS-001' }
            Add-Issue -Code $planIssueCode -Severity 'BLOCKER' -Message '进入实现前缺少当前模块实施计划。' -Path $paths.IMPL_PLAN -Hint '先运行 /speckit.plan 生成 plans/plan-<module>.md'
        }

        if (-not $tasksEntry) {
            Add-Issue -Code 'GATE-IMPL-001' -Severity 'BLOCKER' -Message '进入实现前缺少 tasks/ 或 tasks.md。' -Path $paths.TASKS_DIR -Hint '先运行 /speckit.tasks'
        }

        if ($Module) {
            if (-not $moduleTasksPath) {
                Add-Issue -Code 'GATE-PLAN-002' -Severity 'BLOCKER' -Message '当前模块缺少与目标 plan 对应的 tasks-<module>.md 文件。' -Path (Join-Path $paths.TASKS_DIR ("tasks-$targetTaskSlug.md")) -Hint '先生成模块级 tasks 文件，再继续实现'
            } elseif (-not (Test-TasksReferencesPlan -TasksText $moduleTasksText -TaskSlug $targetTaskSlug)) {
                Add-Issue -Code 'GATE-PLAN-002' -Severity 'BLOCKER' -Message '模块 tasks 未显式引用对应的模块 plan，计划链路不可追踪。' -Path $moduleTasksPath -Hint '在 tasks 文件头部补齐 plans/plan-<module>.md 输入引用'
            }

            if (-not (Test-ReferencesModuleAiPd -Text $planText -ModuleAiPdPath $moduleAiPdPath -TaskSlug $targetTaskSlug)) {
                Add-Issue -Code 'GATE-AIPD-001' -Severity 'BLOCKER' -Message '进入实现前，当前模块 plan 未显式引用 AI-PD。' -Path $paths.IMPL_PLAN -Hint '先在 plan 中补齐 ai-pd/ai-<module>.md 输入引用'
            }

            if (-not (Test-ReferencesModuleAiPd -Text $moduleTasksText -ModuleAiPdPath $moduleAiPdPath -TaskSlug $targetTaskSlug)) {
                Add-Issue -Code 'GATE-AIPD-002' -Severity 'BLOCKER' -Message '进入实现前，模块 tasks 未显式引用 AI-PD。' -Path $moduleTasksPath -Hint '先在 tasks 中补齐 ai-pd/ai-<module>.md 输入引用'
            }

            if ((Test-PdContainsHiddenInteractions -Text ($moduleReadmeText + "`n" + $moduleHtmlText)) -and (-not (Test-HasPageCapabilityChecklist -Text $planText))) {
                Add-Issue -Code 'GATE-PLAN-003' -Severity 'BLOCKER' -Message '进入实现前，当前模块 plan 缺少页面能力清单或未显式标记 functional-hidden-ui / explanatory-only。' -Path $paths.IMPL_PLAN -Hint '先补齐页面能力清单，再进入实现'
            }

            if ((Test-PdContainsHiddenInteractions -Text ($moduleReadmeText + "`n" + $moduleHtmlText)) -and (-not (Test-HasPageCapabilityChecklist -Text $moduleTasksText))) {
                Add-Issue -Code 'GATE-PLAN-004' -Severity 'BLOCKER' -Message '进入实现前，模块 tasks 未显式继承页面能力清单中的 functional-hidden-ui。' -Path $moduleTasksPath -Hint '先在 tasks 中补齐页面能力承接矩阵与隐藏交互任务'
            }
        }

        $tasksText = ''
        if ($moduleTasksPath) {
            $tasksText = $moduleTasksText
        } elseif (Test-Path $paths.TASKS_FILE -PathType Leaf) {
            $tasksText = Read-TextFile -Path $paths.TASKS_FILE
        } elseif (Test-Path $paths.TASKS_DIR -PathType Container) {
            $taskFiles = Get-ChildItem -Path $paths.TASKS_DIR -File -Filter '*.md' -ErrorAction SilentlyContinue
            $tasksText = ($taskFiles | ForEach-Object { Read-TextFile -Path $_.FullName }) -join "`n"
        }

        $combinedText = $planText + "`n" + $tasksText
        $hasRealBlocker =
            ($combinedText -match '(?m)^\|[^\r\n]*\|\s*BLOCKER\s*\|') -or
            ($combinedText -match '(?m)^\s*-\s*BLOCKER\s*:') -or
            ($combinedText -match '(?m)^\s*BLOCKER\s*:')

        if ($hasRealBlocker) {
            Add-Issue -Code 'GATE-IMPL-002' -Severity 'BLOCKER' -Message 'plan/tasks 中仍存在未处理 BLOCKER。' -Path $paths.FEATURE_DIR -Hint '先处理 BLOCKER，再进入实现'
        }

        if ($combinedText -match 'Stub|Blocked By|Deferred|Out of Scope') {
            Add-Issue -Code 'GATE-IMPL-003' -Severity 'WARNING' -Message 'plan/tasks 中存在显式未完成声明。进入实现前需确认风险范围。' -Path $paths.FEATURE_DIR -Hint '仅在用户接受风险或限定范围后继续'
        }
    }
    'browser' {
        if (-not $Module) {
            Add-Issue -Code 'GATE-BROWSER-001' -Severity 'BLOCKER' -Message 'browser 阶段必须指定目标模块。' -Path $rolloutPath -Hint '使用 -Module pd-<module> 运行模块级浏览器 gate'
        }

        if ($targetModuleState -and $targetModuleState -notin @('implementing', 'browser_verified', 'done')) {
            Add-Issue -Code 'GATE-BROWSER-001' -Severity 'BLOCKER' -Message ('目标模块当前状态不允许进入 browser 阶段: ' + $targetModuleState) -Path $moduleStatePath -Hint '先把模块推进到 implementing'
        }

        if ($targetModuleConfig) {
            $browserStage = $targetModuleConfig.browser_stage
            $qualityProbes = @()
            if ($browserStage) {
                $qualityProbes = @($browserStage.quality_probes)
            }

            if (
                -not $browserStage -or
                -not $browserStage.required -or
                -not $browserStage.ui_smoke -or
                -not $browserStage.business_e2e -or
                $qualityProbes.Count -eq 0
            ) {
                Add-Issue -Code 'GATE-BROWSER-002' -Severity 'BLOCKER' -Message '目标模块缺少完整 browser stage 配置。' -Path $rolloutPath -Hint '补齐 ui_smoke / business_e2e / quality_probes'
            }

            if ($targetModuleConfig.critical -and (-not $browserStage.performance_targets)) {
                Add-Issue -Code 'GATE-BROWSER-003' -Severity 'WARNING' -Message '重点模块尚未配置性能/准确率探针。' -Path $rolloutPath -Hint '为 critical 模块补齐 performance_targets'
            }

            if ($targetModuleConfig.critical) {
                $requiredIaProbes = @('page_boundary_parity', 'route_navigation_chain')
                $missingIaProbes = @($requiredIaProbes | Where-Object { $_ -notin $qualityProbes })
                if ($missingIaProbes.Count -gt 0) {
                    Add-Issue -Code 'GATE-BROWSER-004' -Severity 'BLOCKER' -Message ('重点模块缺少页面边界/路由矩阵探针: ' + ($missingIaProbes -join ', ')) -Path $rolloutPath -Hint '为 critical 模块补齐 page_boundary_parity 与 route_navigation_chain'
                }

                if ('capability_parity' -notin $qualityProbes) {
                    Add-Issue -Code 'GATE-BROWSER-005' -Severity 'BLOCKER' -Message '重点模块缺少 capability_parity 探针，无法证明 functional-hidden-ui 与页面能力清单一致。' -Path $rolloutPath -Hint '为 critical 模块补齐 capability_parity'
                }
            }
        }
    }
}

$issueArray = @($issues.ToArray())
$blockers = @($issueArray | Where-Object { $_.severity -eq 'BLOCKER' })
$warnings = @($issueArray | Where-Object { $_.severity -eq 'WARNING' })
$status = if ($blockers.Count -gt 0) { 'blocked' } elseif ($warnings.Count -gt 0) { 'warning' } else { 'pass' }

if ($Json) {
    [PSCustomObject]@{
        stage = $Stage
        branch = $paths.CURRENT_BRANCH
        active_feature = $paths.ACTIVE_FEATURE
        feature_dir = $paths.FEATURE_DIR
        status = $status
        blocker_count = $blockers.Count
        warning_count = $warnings.Count
        issues = $issueArray
    } | ConvertTo-Json -Depth 6 -Compress
    exit 0
}

Write-Output "STAGE: $Stage"
Write-Output "STATUS: $status"
Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
Write-Output "ACTIVE_FEATURE: $($paths.ACTIVE_FEATURE)"
Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"

foreach ($issue in $issueArray) {
    Write-Output "[$($issue.severity)] $($issue.code) $($issue.message)"
    if ($issue.path) {
        Write-Output "  PATH: $($issue.path)"
    }
    if ($issue.hint) {
        Write-Output "  HINT: $($issue.hint)"
    }
}
