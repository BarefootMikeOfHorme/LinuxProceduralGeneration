# PowerShell script to build the C++ components of Vaultmind Forge

param (
    [string]$Configuration = "Debug"
)

# Get the script's directory
$ScriptPath = $PSScriptRoot

# Define the source and build directories based on the project structure
$SourceDir = Join-Path -Path $ScriptPath -ChildPath "..\vaultmind_forge\native\cpp\validator"
$BuildDir = Join-Path -Path $SourceDir -ChildPath "build"

# Create the build directory if it doesn't exist
if (-not (Test-Path -Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir
    Write-Host "Created build directory: $BuildDir"
}

# Configure the project with CMake
Write-Host "Configuring C++ project with CMake..."
cmake -S $SourceDir -B $BuildDir

# Build the project using the specified configuration
Write-Host "Building C++ project (Configuration: $Configuration)..."
cmake --build $BuildDir --config $Configuration

Write-Host "C++ build process completed."
