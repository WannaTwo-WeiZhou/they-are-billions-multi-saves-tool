@echo off
chcp 65001 > nul
python --version >nul 2>&1
if %errorlevel% == 0 goto run

echo [提示] 未检测到 Python，正在尝试自动安装...

winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 winget，无法自动安装。
    echo 请手动前往以下地址下载并安装 Python：
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

winget install --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo.
    echo [错误] 自动安装失败，请手动前往以下地址安装 Python：
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [成功] Python 已安装完成，请关闭此窗口并重新运行 tab_save_tool.bat。
pause
exit /b 0

:run
python "%~dp0tab_save_tool.py"
