@echo off
chcp 65001 > nul
python --version >nul 2>&1
if %errorlevel% == 0 goto run

echo [提示] 未检测到 Python，正在尝试自动安装...
echo.

:: ── 方式一：winget ──────────────────────────────────────────────────────────
winget --version >nul 2>&1
if not errorlevel 1 (
    echo [方式1] 检测到 winget，尝试通过 winget 安装 Python...
    winget install --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements && (
        echo.
        echo [成功] Python 已通过 winget 安装完成，请关闭此窗口并重新运行 tab_save_tool.bat。
        pause
        exit /b 0
    ) || (
        echo [警告] winget 安装失败，尝试下一种方式...
        echo.
    )
)

:: ── 方式二：Chocolatey (choco) ──────────────────────────────────────────────
choco --version >nul 2>&1
if not errorlevel 1 (
    echo [方式2] 检测到 Chocolatey，尝试通过 choco 安装 Python...
    choco install python --yes && (
        echo.
        echo [成功] Python 已通过 Chocolatey 安装完成，请关闭此窗口并重新运行 tab_save_tool.bat。
        pause
        exit /b 0
    ) || (
        echo [警告] Chocolatey 安装失败，尝试下一种方式...
        echo.
    )
)

:: ── 方式三：PowerShell 直接从 python.org 下载安装包 ────────────────────────
echo [方式3] 尝试通过 PowerShell 从 python.org 下载并安装 Python...
set "_PY_INSTALLER=%TEMP%\python_installer.exe"
set "_PY_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Invoke-WebRequest -Uri '%_PY_URL%' -OutFile '%_PY_INSTALLER%' -UseBasicParsing" 2>nul
if exist "%_PY_INSTALLER%" (
    echo [提示] 正在静默安装，请稍候...
    "%_PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    del /f /q "%_PY_INSTALLER%" >nul 2>&1
    echo.
    echo [成功] Python 安装程序已执行完毕。
    echo 请关闭此窗口并重新打开命令提示符后再运行 tab_save_tool.bat，
    echo 以使 PATH 环境变量更新生效。
    pause
    exit /b 0
)

:: ── 全部方式失败 ─────────────────────────────────────────────────────────────
echo.
echo [错误] 所有自动安装方式均失败，请手动前往以下地址下载并安装 Python：
echo   https://www.python.org/downloads/
pause
exit /b 1

:run
python "%~dp0tab_save_tool.py"
