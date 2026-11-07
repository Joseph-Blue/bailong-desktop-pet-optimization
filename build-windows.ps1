#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Python = 'python',
    [string]$FFmpeg = '',
    [switch]$SkipInstall
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $IsWindows) { throw '请在 Windows 的 PowerShell 7+ 中运行此脚本。' }

function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program 执行失败，退出码 $LASTEXITCODE" }
}

Push-Location $PSScriptRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $PSScriptRoot '.build-windows/pyinstaller-cache'
    $VenvPython = Join-Path $PSScriptRoot '.venv-build-windows/Scripts/python.exe'
    if (-not (Test-Path $VenvPython)) {
        if ($SkipInstall) { throw '构建环境不存在；请先去掉 -SkipInstall 运行。' }
        Invoke-Checked $Python @('work/build_common.py')
        Invoke-Checked $Python @('-m', 'venv', '.venv-build-windows')
    }
    Invoke-Checked $VenvPython @('work/build_common.py')
    if (-not $SkipInstall) {
        Invoke-Checked $VenvPython @('-m', 'pip', 'install', '-r', 'requirements-build.txt')
    }
    $BuildArgs = @('work/build_windows.py')
    if ($FFmpeg) { $BuildArgs += @('--ffmpeg', $FFmpeg) }
    Invoke-Checked $VenvPython $BuildArgs
} finally {
    Pop-Location
}
