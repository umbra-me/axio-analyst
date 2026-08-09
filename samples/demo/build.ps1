# Build the Axio Analyst demo as a 64-bit Windows Release executable.
# ASCII only: this file must work under Windows PowerShell 5.1.

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SourceDir = $PSScriptRoot
$BuildDir = Join-Path $SourceDir 'build'

cmake -S $SourceDir -B $BuildDir -G 'Visual Studio 17 2022' -A x64
if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed.' }

cmake --build $BuildDir --config Release
if ($LASTEXITCODE -ne 0) { throw 'CMake build failed.' }

$Executable = Join-Path $BuildDir 'Release/axio_analyst_demo.exe'
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
    throw "Build completed without the expected executable: $Executable"
}

Write-Output $Executable
