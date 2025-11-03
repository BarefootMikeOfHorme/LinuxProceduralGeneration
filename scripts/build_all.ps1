# PowerShell script to build all native components of Vaultmind Forge

param (
    [string]$Configuration = "Debug"
)

# Get the script's directory
$ScriptPath = $PSScriptRoot

# Build the C++ components
Write-Host "--- Building C++ Components ---"
& "$ScriptPath\build_cpp.ps1" -Configuration $Configuration

# Build the Rust components
Write-Host "--- Building Rust Components ---"
& "$ScriptPath\build_rust.ps1" -Configuration $Configuration

Write-Host "All native builds completed."
