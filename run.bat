@echo off
setlocal

REM 设置 Python 版本和下载链接
set PYTHON_VERSION=3.12.0
set PYTHON_DOWNLOAD_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe

REM 设置安装目录 在 C 盘下的 Program File 文件夹下
set INSTALL_DIR=%ProgramFiles%\Python

REM 设置需要检查的模块
set MODULE_NAME=pyppeteer
set BS4=bs4

REM 检查是否已安装 Python
reg query "HKLM\Software\Python\PythonCore\%PYTHON_VERSION%" > nul 2>&1
if %errorlevel% equ 0 (
    echo Python %PYTHON_VERSION% 已安装, 检查是否安装模块 %MODULE_NAME%...
) else (
    echo Python %PYTHON_VERSION% 未安装，自动安装 Python...
    bitsadmin /transfer "PythonInstaller" %PYTHON_DOWNLOAD_URL% "%TEMP%\python_installer.exe"
    "%TEMP%\python_installer.exe" /quiet TargetDir=%INSTALL_DIR%
    del /q "%TEMP%\python_installer.exe"
)

REM 检查是否安装模块
python -c "import %MODULE_NAME%" > nul 2>&1
if %errorlevel% equ 0 (
    echo %MODULE_NAME% 模块已安装.
) else (
    echo %MODULE_NAME% 模块未安装，自动安装 %MODULE_NAME% 模块...
    pip install %MODULE_NAME%
)

REM 检查是否安装模块
python -c "import %MODULE_NAME%" > nul 2>&1
if %errorlevel% equ 0 (
    echo %BS4% 模块已安装.
) else (
    echo %BS4% 模块未安装，自动安装 %BS4% 模块...
    pip install %BS4%
)


endlocal
