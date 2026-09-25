#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifest = Join-Path $root 'al1scan\Cargo.toml'
$release = Join-Path $root 'al1scan\target\release\al1scan.exe'

if (Test-Path -LiteralPath $release) {
    & $release @args
    exit $LASTEXITCODE
}

$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if ($null -eq $cargo) {
    throw 'Cargo is required to run al1scan. Install/enable Rust or build the release binary first.'
}

& $cargo.Source run --quiet --manifest-path $manifest -- @args
exit $LASTEXITCODE
