@echo off
setlocal


set PYTHON_VERSION=3.12.0
set PYTHON_DOWNLOAD_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe


set INSTALL_DIR=%ProgramFiles%\Python


set MODULE_NAME=pyppeteer
set BS4=bs4
set REQUESTS=requests


reg query "HEKY_CURRENT_USER\Software\Python\PythonCore\3.12" > nul 2>&1
if %errorlevel% equ 0 (
    echo Python %PYTHON_VERSION% already installed
) else (
    echo Python %PYTHON_VERSION% not install，auto installing Python...
    bitsadmin /transfer "PythonInstaller" %PYTHON_DOWNLOAD_URL% "%TEMP%\python_installer.exe"
    "%TEMP%\python_installer.exe" /quiet TargetDir=%INSTALL_DIR%
    del /q "%TEMP%\python_installer.exe"
)


python -c "import %MODULE_NAME%" > nul 2>&1
if %errorlevel% equ 0 (
    echo %MODULE_NAME% already installed.
) else (
    echo %MODULE_NAME% not install，auto installing %MODULE_NAME%
    pip install %MODULE_NAME%
)


python -c "import %BS4%" > nul 2>&1
if %errorlevel% equ 0 (
    echo %BS4% already installed.
) else (
    echo %BS4% not install，auto installing %BS4%
    pip install %BS4%
)


python -c "import %REQUESTS%" > nul 2>&1
if %errorlevel% equ 0 (
    echo %REQUESTS% already installed.
) else (
    echo %REQUESTS% not install，auto installing %REQUESTS%
    pip install %REQUESTS%
)

python main.py

endlocal
