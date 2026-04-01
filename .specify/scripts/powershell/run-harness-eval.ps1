#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$Fixture = 'current-workspace',
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$evalSetPath = Join-Path $PSScriptRoot '../../harness/harness-eval-set.json'
$gateScriptPath = Join-Path $PSScriptRoot 'validate-stage-gates.ps1'

$cases = Get-Content $evalSetPath -Raw | ConvertFrom-Json
$selectedCases = @($cases | Where-Object { $_.fixture -eq $Fixture })

if ($selectedCases.Count -eq 0) {
    throw "No eval cases found for fixture: $Fixture"
}

$results = foreach ($case in $selectedCases) {
    $gateArgs = @{
        Stage = $case.stage
        Json = $true
    }
    if ($case.PSObject.Properties.Name -contains 'module' -and $case.module) {
        $gateArgs.Module = $case.module
    }

    $raw = & $gateScriptPath @gateArgs
    $gate = $raw | ConvertFrom-Json
    $actualCodes = @($gate.issues | ForEach-Object { $_.code })
    $missingCodes = @($case.expected_codes | Where-Object { $_ -notin $actualCodes })
    $passed = ($gate.status -eq $case.expected_status) -and ($missingCodes.Count -eq 0)

    [PSCustomObject]@{
        id = $case.id
        stage = $case.stage
        expected_status = $case.expected_status
        actual_status = $gate.status
        expected_codes = @($case.expected_codes)
        actual_codes = $actualCodes
        missing_codes = $missingCodes
        passed = $passed
    }
}

$resultArray = @($results)
$summary = [PSCustomObject]@{
    fixture = $Fixture
    total = $resultArray.Count
    passed = @($resultArray | Where-Object { $_.passed }).Count
    failed = @($resultArray | Where-Object { -not $_.passed }).Count
    results = $resultArray
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 6 -Compress
    exit 0
}

Write-Output "FIXTURE: $Fixture"
Write-Output "TOTAL: $($summary.total)"
Write-Output "PASSED: $($summary.passed)"
Write-Output "FAILED: $($summary.failed)"

foreach ($result in $resultArray) {
    $icon = if ($result.passed) { 'PASS' } else { 'FAIL' }
    Write-Output "[$icon] $($result.id) stage=$($result.stage) expected=$($result.expected_status) actual=$($result.actual_status)"
    if ($result.missing_codes.Count -gt 0) {
        Write-Output "  missing_codes: $($result.missing_codes -join ', ')"
    }
}
