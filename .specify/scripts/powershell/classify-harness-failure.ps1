#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('contract', 'ui', 'logic', 'performance', 'environment')]
    [string]$Source,

    [string]$Module = '',
    [string]$Summary = '',
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$classification = switch ($Source) {
    'contract' {
        [PSCustomObject]@{
            failure_type = 'contract_failure'
            route = 'AD/DD -> tasks -> implement'
            auto_fix_allowed = $false
            stop_reason = '契约类失败默认需要先确认设计口径'
        }
    }
    'ui' {
        [PSCustomObject]@{
            failure_type = 'ui_mismatch'
            route = 'PD/前端实现'
            auto_fix_allowed = $true
            stop_reason = ''
        }
    }
    'logic' {
        [PSCustomObject]@{
            failure_type = 'logic_failure'
            route = 'DD/服务实现'
            auto_fix_allowed = $true
            stop_reason = ''
        }
    }
    'performance' {
        [PSCustomObject]@{
            failure_type = 'performance_failure'
            route = '实现/索引/缓存/评估'
            auto_fix_allowed = $false
            stop_reason = '性能或准确率失败通常需要重新评估口径与策略'
        }
    }
    'environment' {
        [PSCustomObject]@{
            failure_type = 'env_failure'
            route = 'MasterAgent 编排层'
            auto_fix_allowed = $true
            stop_reason = ''
        }
    }
}

$result = [PSCustomObject]@{
    module = $Module
    summary = $Summary
    source = $Source
    failure_type = $classification.failure_type
    route = $classification.route
    auto_fix_allowed = $classification.auto_fix_allowed
    stop_reason = $classification.stop_reason
}

if ($Json) {
    $result | ConvertTo-Json -Depth 4
} else {
    Write-Output "MODULE: $($result.module)"
    Write-Output "SOURCE: $($result.source)"
    Write-Output "TYPE: $($result.failure_type)"
    Write-Output "ROUTE: $($result.route)"
    Write-Output "AUTO_FIX_ALLOWED: $($result.auto_fix_allowed)"
    if ($result.stop_reason) {
        Write-Output "STOP_REASON: $($result.stop_reason)"
    }
}
