#Requires -Version 5.1
# Keep this file encoded as UTF-8 with BOM for Windows PowerShell 5.1.
<#
.SYNOPSIS
检查并补齐 Windows 构建依赖，生成完整目录包，可选 ZIP。
.DESCRIPTION
自动寻找已安装的 64 位 Python 3.11～3.13；不下载 Python，不修改系统执行策略。
使用独立虚拟环境，仅当依赖缺失、版本不符或 pip check 失败时安装依赖。
.PARAMETER Python
首次建环境所用的解释器路径或命令名；不传时检查 PATH 和 py 启动器登记的解释器。
.PARAMETER FFmpeg
可选的本机 FFmpeg 路径；不传时按 BUILDING.md 的优先级自动选择。
.PARAMETER SkipInstall
只检查已有环境；缺依赖时停止，不创建环境或安装依赖。
.PARAMETER Zip
构建成功后生成完整 ZIP 和 SHA256 校验文件；不上传。
#>
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string]$Python = 'python',
    [string]$FFmpeg = '',
    [switch]$SkipInstall,
    [switch]$Zip
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
# Use explicit native exit-code checks consistently across 5.1 and 7.x.
$PSNativeCommandUseErrorActionPreference = $false
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw '请在 Windows PowerShell 5.1 或 Windows 上的 PowerShell 7+ 中运行此脚本。'
}

function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program 执行失败，退出码 $LASTEXITCODE" }
}

function Find-BuildPython {
    $Candidates = @()
    $OnPath = Get-Command -Name python.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($OnPath) { $Candidates += $OnPath.Source }
    $Launcher = Get-Command -Name py.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($Launcher) {
        try {
            # Listing installed interpreters does not download or install Python.
            $Installed = & ($Launcher | Select-Object -First 1).Source -0p 2>$null
            foreach ($Line in $Installed) {
                if ($Line -match '^\s*-\S+\s+\*?\s*(.+?python\.exe)\s*$') {
                    $Candidates += $Matches[1]
                }
            }
        } catch { Write-Verbose '无法读取 py 启动器列表，继续检查 PATH。' }
    }
    foreach ($Candidate in ($Candidates | Select-Object -Unique)) {
        # Avoid launching a Microsoft Store app execution alias.
        if ($Candidate -like '*\Microsoft\WindowsApps\*') { continue }
        try {
            & $Candidate -c 'import sys; sys.exit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) and sys.maxsize > 2**32 else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { return $Candidate }
        } catch { Write-Verbose "解释器不可用：$Candidate" }
    }
    throw '未找到可用的 64 位 Python 3.11～3.13；请安装后重试，或用 -Python 指定 python.exe。'
}

$VenvPython = Join-Path $PSScriptRoot '.venv-build-windows/Scripts/python.exe'
$HasVenv = Test-Path -LiteralPath $VenvPython -PathType Leaf
if (-not $HasVenv) {
    if ($SkipInstall) { throw '构建环境不存在；请先去掉 -SkipInstall 运行。' }
    if (-not $PSBoundParameters.ContainsKey('Python')) { $Python = Find-BuildPython }
    # Resolve before changing directory so caller-relative executable paths work.
    $PythonCommand = Get-Command -Name $Python -CommandType Application -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "找不到 Python：$Python；请用 -Python 指定 64 位 Python 3.11～3.13 的 python.exe。"
    }
    $Python = ($PythonCommand | Select-Object -First 1).Source
} elseif ($PSBoundParameters.ContainsKey('Python')) {
    Write-Warning '-Python 只用于创建环境；本次复用 .venv-build-windows。更换解释器请先移走该目录。'
}

if (-not $FFmpeg) { $FFmpeg = $env:BAILONG_BUILD_FFMPEG }
if ($FFmpeg) {
    $FFmpeg = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($FFmpeg)
}
$PreviousPythonUtf8 = $env:PYTHONUTF8
$PreviousPyInstallerConfig = $env:PYINSTALLER_CONFIG_DIR
Push-Location -LiteralPath $PSScriptRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $PSScriptRoot '.build-windows/pyinstaller-cache'
    if (-not $HasVenv) {
        Write-Host "创建构建环境，使用 Python：$Python"
        Invoke-Checked $Python @('work/build_common.py')
        Invoke-Checked $Python @('-m', 'venv', '.venv-build-windows')
    }
    Invoke-Checked $VenvPython @('work/build_common.py')
    Write-Host '检查构建依赖及版本...'
    & $VenvPython 'work/check_build_dependencies.py'
    $DependencyExit = $LASTEXITCODE
    if ($DependencyExit -notin @(0, 10)) { throw "依赖检查失败，退出码 $DependencyExit" }
    $NeedsInstall = $DependencyExit -eq 10
    if (-not $NeedsInstall) {
        & $VenvPython -m pip check
        $NeedsInstall = $LASTEXITCODE -ne 0
    }
    if ($NeedsInstall) {
        if ($SkipInstall) { throw '构建依赖缺失、版本不符或存在冲突；去掉 -SkipInstall 可自动补齐。' }
        & $VenvPython -m pip --version
        if ($LASTEXITCODE -ne 0) { Invoke-Checked $VenvPython @('-m', 'ensurepip', '--upgrade') }
        Write-Host '补齐构建依赖...'
        Invoke-Checked $VenvPython @('-m', 'pip', 'install', '-r', 'requirements-build.txt')
        Invoke-Checked $VenvPython @('work/check_build_dependencies.py')
        Invoke-Checked $VenvPython @('-m', 'pip', 'check')
    } else {
        Write-Host '依赖已满足，跳过安装。'
    }
    Write-Host '开始打包程序、素材和 FFmpeg...'
    $BuildArgs = @('work/build_windows.py')
    if ($FFmpeg) { $BuildArgs += @('--ffmpeg', $FFmpeg) }
    if ($Zip) { $BuildArgs += '--zip' }
    Invoke-Checked $VenvPython $BuildArgs
} finally {
    $env:PYTHONUTF8 = $PreviousPythonUtf8
    $env:PYINSTALLER_CONFIG_DIR = $PreviousPyInstallerConfig
    Pop-Location
}
