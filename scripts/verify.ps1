<#
.SYNOPSIS
    Verification gate: static analysis, then tests, then build.

.DESCRIPTION
    Runs the checks that can currently be enforced honestly, and ratchets the
    two that cannot.

    Static analysis is a ratchet rather than a pass/fail gate. mypy reports 431
    pre-existing errors that are not all defects, and black would reformat 220
    of 241 tracked files. Making either a blocking gate would either bury real
    work in formatting noise or pass while genuine problems remain. Instead the
    counts are recorded and the run fails only if either number has RISEN, so
    debt cannot silently grow. See docs/STATIC_ANALYSIS.md for the reasoning and
    for the defects the first run surfaced.

    The baseline values below are the contract. Lowering one is progress.
    Raising one is a decision to accept more debt and belongs in a commit
    message that says so. Never raise a baseline to make this script pass.

.PARAMETER EnforceFormat
    Additionally require that files touched by recent commits are black-clean.
    This is how new work avoids adding to the backlog while the existing backlog
    is worked down separately. It inspects files changed in the last N commits
    rather than the whole tree, so it is meaningful even while 220 files are
    non-conforming.

.PARAMETER RecentCommits
    How many commits back -EnforceFormat looks for changed files. Default 5.

.PARAMETER SkipTests
    Run only the static analysis. Useful for a fast loop while editing.

.EXAMPLE
    pwsh -NoProfile -File scripts/verify.ps1

.EXAMPLE
    pwsh -NoProfile -File scripts/verify.ps1 -EnforceFormat
#>
[CmdletBinding()]
param(
    [switch]$EnforceFormat,
    [int]$RecentCommits = 5,
    [switch]$SkipTests
)

# Continue on non-terminating errors so a non-zero exit from a child tool (mypy
# and black both exit non-zero when they find something) is reported rather than
# aborting the run.
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$python = Join-Path $repo '.venv312\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw "venv python not found at $python"
}

# --- Baselines -------------------------------------------------------------
# Measured 2026-09-27 on mypy 2.3.1 / black 26.5.1. Do not raise to silence a
# failure; fix the regression or lower the number if it genuinely improved.
$MYPY_ERROR_BASELINE = 431
# Lowered from 220 after formatting the files this tooling had touched. Crediting
# the improvement immediately stops the baseline hiding work already done.
$BLACK_FILE_BASELINE = 194

$failures = @()
Write-Host ('=' * 62)
Write-Host 'LPG verification'
Write-Host ('=' * 62)

# --- mypy ------------------------------------------------------------------
Write-Host "`n[1/3] mypy" -ForegroundColor Cyan
$mypyOutput = & $python -m mypy vaultmind_forge 2>&1
$mypyText = ($mypyOutput | Out-String)
$mypyErrors = 0
if ($mypyText -match 'Found (\d+) errors? in') {
    $mypyErrors = [int]$matches[1]
} elseif ($mypyText -match 'Success: no issues found') {
    $mypyErrors = 0
} else {
    # No summary line at all means mypy did not complete, so the count is
    # unknown rather than zero. Reporting 0 here would falsely credit a run as
    # a 431-error improvement.
    Write-Host "  could not parse a mypy summary; treating as unknown" -ForegroundColor Yellow
    $failures += 'mypy: no summary line in output, could not determine error count'
    $mypyErrors = $MYPY_ERROR_BASELINE + 1
}

if ($mypyErrors -gt $MYPY_ERROR_BASELINE) {
    $failures += "mypy: $mypyErrors errors, baseline is $MYPY_ERROR_BASELINE (rOSE by $($mypyErrors - $MYPY_ERROR_BASELINE))"
    Write-Host "  FAIL  $mypyErrors errors (baseline $MYPY_ERROR_BASELINE)" -ForegroundColor Red
} elseif ($mypyErrors -lt $MYPY_ERROR_BASELINE) {
    Write-Host "  OK    $mypyErrors errors (baseline $MYPY_ERROR_BASELINE, improved by $($MYPY_ERROR_BASELINE - $mypyErrors))" -ForegroundColor Green
    # Credit the improvement immediately so it cannot be lost.
    Write-Host "        consider lowering MYPY_ERROR_BASELINE to $mypyErrors in scripts/verify.ps1" -ForegroundColor DarkGray
} else {
    Write-Host "  OK    $mypyErrors errors (at baseline)" -ForegroundColor Green
}

# --- black -----------------------------------------------------------------
Write-Host "`n[2/3] black" -ForegroundColor Cyan
$tracked = git ls-files '*.py' | Where-Object { $_ -notlike 'study-copies/*' }
$nonConforming = @()
foreach ($file in $tracked) {
    & $python -m black --check --quiet $file 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $nonConforming += $file }
}
$blackCount = $nonConforming.Count

if ($blackCount -gt $BLACK_FILE_BASELINE) {
    $failures += "black: $blackCount non-conforming files, baseline is $BLACK_FILE_BASELINE"
    Write-Host "  FAIL  $blackCount of $($tracked.Count) files would be reformatted (baseline $BLACK_FILE_BASELINE)" -ForegroundColor Red
} elseif ($blackCount -lt $BLACK_FILE_BASELINE) {
    Write-Host "  OK    $blackCount of $($tracked.Count) files non-conforming (baseline $BLACK_FILE_BASELINE, improved by $($BLACK_FILE_BASELINE - $blackCount))" -ForegroundColor Green
    Write-Host "        consider lowering BLACK_FILE_BASELINE to $blackCount in scripts/verify.ps1" -ForegroundColor DarkGray
} else {
    Write-Host "  OK    $blackCount of $($tracked.Count) files non-conforming (at baseline)" -ForegroundColor Green
}

if ($EnforceFormat) {
    # Only files this tooling has touched recently must be clean. Applying black
    # to the whole tree would rewrite 220 files and the user's untracked work.
    $recent = @()
    for ($i = 0; $i -lt $RecentCommits; $i++) {
        $recent += git diff-tree --no-commit-id --name-only -r "HEAD~$i" 2>$null
    }
    $recentPy = $recent |
        Where-Object { $_ -like '*.py' -and $_ -notlike 'study-copies/*' -and (Test-Path $_) } |
        Sort-Object -Unique

    if ($recentPy.Count -gt 0) {
        $recentBad = @()
        foreach ($file in $recentPy) {
            & $python -m black --check --quiet $file 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) { $recentBad += $file }
        }
        if ($recentBad.Count -gt 0) {
            $failures += "black -EnforceFormat: $($recentBad.Count) recently changed file(s) are not formatted"
            Write-Host "  FAIL  recently changed files not black-clean:" -ForegroundColor Red
            $recentBad | ForEach-Object { Write-Host "          $_" -ForegroundColor Red }
        } else {
            Write-Host "  OK    all $($recentPy.Count) recently changed files are black-clean" -ForegroundColor Green
        }
    } else {
        Write-Host "  SKIP  no recently changed Python files" -ForegroundColor DarkGray
    }
}

# --- tests -----------------------------------------------------------------
Write-Host "`n[3/3] tests" -ForegroundColor Cyan
if ($SkipTests) {
    Write-Host "  SKIP  -SkipTests supplied" -ForegroundColor DarkGray
} else {
    $testLogDir = 'logs\test-reports\logs'
    & pwsh -NoProfile -File 'scripts/run-test-suite.ps1' -TimeoutSec 300
    if ($LASTEXITCODE -ne 0) {
        $failures += 'test suite reported a failure or timeout'
    }
}

# --- summary ---------------------------------------------------------------
Write-Host ''
Write-Host ('=' * 62)
if ($failures.Count -eq 0) {
    Write-Host "VERIFICATION PASSED" -ForegroundColor Green
    Write-Host "  mypy $mypyErrors / baseline $MYPY_ERROR_BASELINE   (advisory, ratcheted)"
    Write-Host "  black $blackCount / baseline $BLACK_FILE_BASELINE files non-conforming (advisory, ratcheted)"
    Write-Host "  See docs/STATIC_ANALYSIS.md for why these are ratchets and not gates."
    exit 0
} else {
    Write-Host "VERIFICATION FAILED" -ForegroundColor Red
    $failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}
