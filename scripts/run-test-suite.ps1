# Per-module test runner that writes a machine-readable report.
# The full suite cannot be run as a single pytest invocation here: one module
# blocks for a very long time, so a single run yields no per-module signal and
# no partial results if it is interrupted. This runs each module separately with
# its own timeout, records the outcome, and prints a summary table plus a
# machine-readable JSON report.
#
# Usage:
#   pwsh -NoProfile -File run-suite.ps1 [-OutDir <path>] [-TimeoutSec <n>]

param(
    [string]$OutDir = "logs\test-reports",
    [int]$TimeoutSec = 300
)

$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$python = Join-Path $repo '.venv312\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw "venv python not found at $python"
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$logDir = Join-Path $OutDir 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$modules = Get-ChildItem 'vaultmind_forge\tests' -Filter 'test_*.py' -File |
    Sort-Object Name |
    ForEach-Object { "vaultmind_forge/tests/$($_.Name)" }

$results = @()
$startedAll = Get-Date

foreach ($module in $modules) {
    $name = Split-Path $module -Leaf
    $log = Join-Path $logDir "$name.log"
    $start = Get-Date

    Write-Host "==> $name"

    # Start the child, wait with a timeout, and kill the whole tree if it
    # overruns. A bare `pytest` call cannot be interrupted, so a hanging module
    # would otherwise stall the report indefinitely.
    $proc = Start-Process -FilePath $python `
        -ArgumentList @('-m', 'pytest', $module, '-q', '-p', 'no:cacheprovider',
                        '--no-header', '-rf') `
        -NoNewWindow -PassThru `
        -RedirectStandardOutput $log `
        -RedirectStandardError "$log.err"

    $finished = $proc.WaitForExit($TimeoutSec * 1000)
    if (-not $finished) {
        Write-Warning "$name exceeded ${TimeoutSec}s; terminating"
        try { & taskkill /PID $proc.Id /T /F | Out-Null } catch { }
        $proc.WaitForExit(10000)
        $outcome = 'timeout'
        $code = $null
    }
    else {
        $code = $proc.ExitCode
        $outcome = if ($code -eq 0) { 'pass' } else { 'fail' }
    }

    $elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    $tail = @()
    foreach ($path in @($log, "$log.err")) {
        if (Test-Path $path) {
            $tail += Get-Content $path -Tail 25 -ErrorAction SilentlyContinue
        }
    }
    $summary = ($tail | Where-Object { $_ -match '\d+ (passed|failed|error)' } |
        Select-Object -Last 1)
    if (-not $summary) { $summary = ($tail | Where-Object { $_.Trim() } | Select-Object -Last 1) }

    $results += [pscustomobject]@{
        module    = $name
        outcome   = $outcome
        exit_code = $code
        seconds   = $elapsed
        log       = (Resolve-Path -Relative $log -ErrorAction SilentlyContinue)
        summary   = "$summary".Trim()
    }
}

$report = [pscustomobject]@{
    started  = $startedAll.ToString('o')
    finished = (Get-Date).ToString('o')
    timeout_seconds = $TimeoutSec
    python   = $python
    total    = $results.Count
    passed   = @($results | Where-Object outcome -eq 'pass').Count
    failed   = @($results | Where-Object outcome -eq 'fail').Count
    timedout = @($results | Where-Object outcome -eq 'timeout').Count
    results  = $results
}

$json = Join-Path $OutDir 'report.json'
$report | ConvertTo-Json -Depth 5 | Set-Content $json -Encoding utf8

Write-Host ''
Write-Host '================ PER-MODULE RESULTS ================'
$results | ForEach-Object {
    $flag = switch ($_.outcome) {
        'pass'    { 'PASS' }
        'fail'    { 'FAIL' }
        'timeout' { 'TIME' }
    }
    '{0,-5} {1,8}s  {2}' -f $flag, $_.seconds, $_.module
}
Write-Host '==================================================='
Write-Host ("passed {0}  failed {1}  timeout {2}  total {3}" -f
    $report.passed, $report.failed, $report.timedout, $report.total)
Write-Host "json report: $json"
Write-Host "per-module logs: $logDir"
