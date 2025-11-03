# PowerShell script to build the Rust components of Vaultmind Forge

param (
    [string]$Configuration = "Debug"
)

# Get the script's directory
$ScriptPath = $PSScriptRoot

# Define the source directory for the Rust project
$SourceDir = Join-Path -Path $ScriptPath -ChildPath "..\vaultmind_forge\native\rust\validator"

# Determine the build profile based on the configuration
$Profile = if ($Configuration -eq "Release") { "release" } else { "dev" }

# Build the Rust project with maturin
Write-Host "Building Rust project (Profile: $Profile)..."
Push-Location -Path $SourceDir
maturin develop --profile $Profile
Pop-Location

Write-Host "Rust build process completed."
