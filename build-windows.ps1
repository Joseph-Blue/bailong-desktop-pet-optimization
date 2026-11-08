#Requires -Version 5.1
# Keep this file encoded as UTF-8 with BOM for Windows PowerShell 5.1.
<#
.SYNOPSIS
检查并补齐 Windows 构建依赖，生成完整目录包，可选 ZIP。
.DESCRIPTION
自动选择 64 位 Python 3.11～3.13；缺少动画素材时自动下载，保留已有文件。
可运行目录与 ZIP 均放在仓库根目录的 dist-windows/。
使用独立虚拟环境，仅当依赖缺失、版本不符或 pip check 失败时安装依赖。
.PARAMETER Python
首次建环境所用的解释器路径或命令名；不传时检查 PATH 和 py 启动器登记的解释器。
.PARAMETER FFmpeg
可选的本机 FFmpeg 路径；不传时按 BUILDING.md 的优先级自动选择。
.PARAMETER SkipInstall
只检查已有环境；缺依赖时停止，不创建环境或安装依赖。
.PARAMETER Zip
生成完整 ZIP。
#>
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string]$Python = 'python',
    [string]$FFmpeg = '',
    [switch]$SkipInstall,
    [Alias('Archive')]
    [switch]$Zip
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
# Use explicit native exit-code checks consistently across 5.1 and 7.x.
$PSNativeCommandUseErrorActionPreference = $false
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw '请在 Windows PowerShell 5.1 或 Windows 上的 PowerShell 7+ 中运行此脚本。'
}

$PythonInstallHint = "手动安装 Python 3.13：`nwinget install --id Python.Python.3.13 --exact`n安装后重新打开终端。"

function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program 执行失败，退出码 $LASTEXITCODE" }
}

function Assert-BuildPython([string]$Program, [bool]$Existing = $false) {
    & $Program 'work/build_common.py'
    if ($LASTEXITCODE -ne 0) {
        $Message = "Python 不符合构建要求（退出码 $LASTEXITCODE）。`n$PythonInstallHint"
        if ($Existing) { $Message += "`n移走 .build/venvs/windows 后重新运行构建脚本。" }
        throw $Message
    }
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
    throw "未找到 64 位 Python 3.11～3.13。`n$PythonInstallHint`n已有合适版本时，用 -Python 指定 python.exe。"
}

$VenvPython = Join-Path $PSScriptRoot '.build/venvs/windows/Scripts/python.exe'
$HasVenv = Test-Path -LiteralPath $VenvPython -PathType Leaf
if (-not $HasVenv) {
    if ($SkipInstall) { throw '构建环境不存在；请先去掉 -SkipInstall 运行。' }
    if (-not $PSBoundParameters.ContainsKey('Python')) { $Python = Find-BuildPython }
    # Resolve before changing directory so caller-relative executable paths work.
    $PythonCommand = Get-Command -Name $Python -CommandType Application -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "找不到 Python：$Python`n$PythonInstallHint"
    }
    $Python = ($PythonCommand | Select-Object -First 1).Source
} elseif ($PSBoundParameters.ContainsKey('Python')) {
    Write-Host '复用 .build/venvs/windows；-Python 仅用于首次创建。'
}

if (-not $FFmpeg) { $FFmpeg = $env:BAILONG_BUILD_FFMPEG }
if ($FFmpeg) {
    $FFmpeg = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($FFmpeg)
}
$PreviousPythonUtf8 = $env:PYTHONUTF8
$PreviousPyInstallerConfig = $env:PYINSTALLER_CONFIG_DIR
$PreviousPythonCache = $env:PYTHONPYCACHEPREFIX
Push-Location -LiteralPath $PSScriptRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $PSScriptRoot '.build/cache/pyinstaller-windows'
    $env:PYTHONPYCACHEPREFIX = Join-Path $PSScriptRoot '.build/cache/python'
    if (-not $HasVenv) {
        Write-Host "创建构建环境，使用 Python：$Python"
        Assert-BuildPython $Python
        Invoke-Checked $Python @('-m', 'venv', '.build/venvs/windows')
    }
    Assert-BuildPython $VenvPython $true
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
    Write-Host '打包程序、素材和 FFmpeg...'
    $BuildArgs = @('work/build_windows_optimized.py')
    if ($FFmpeg) { $BuildArgs += @('--ffmpeg', $FFmpeg) }
    if ($Zip) { $BuildArgs += '--zip' }
    Invoke-Checked $VenvPython $BuildArgs
} finally {
    $env:PYTHONUTF8 = $PreviousPythonUtf8
    $env:PYINSTALLER_CONFIG_DIR = $PreviousPyInstallerConfig
    $env:PYTHONPYCACHEPREFIX = $PreviousPythonCache
    Pop-Location
}
