@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   GRACE Downloader  v1.0.1  —  Release Build
echo ============================================================
echo.
echo   Source  : src\grace_downloader_gui_release.py
echo   Spec    : src\grace_downloader_release.spec
echo   Output  : dist\GRACE_Downloader_v1.0.1\
echo.

:: ── Python with PyInstaller ────────────────────────────────────────────────
:: A dedicated lean environment keeps the bundle small (44 packages instead of
:: the 419 of an Anaconda base environment):
::     conda create -n grace -y --no-default-packages python=3.13 pip
::     <env>\python.exe -m pip install earthaccess PyQt5 pyinstaller
set "GRACE_ENV=%USERPROFILE%\anaconda3\envs\grace\python.exe"
if not exist "%GRACE_ENV%" set "GRACE_ENV=%CONDA_PREFIX%\python.exe"

if defined GRACE_PYTHON (
    set "PY=%GRACE_PYTHON%"
) else if exist "%GRACE_ENV%" (
    set "PY=%GRACE_ENV%"
) else (
    set "PY=python"
)

echo   [0/4]  Python interpreter:  %PY%
"%PY%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo.
    echo   ERROR: PyInstaller is not available for "%PY%".
    echo          Install it with:   "%PY%" -m pip install pyinstaller
    echo          Or point GRACE_PYTHON at a Python that has it:
    echo              set GRACE_PYTHON=C:\Users\you\anaconda3\envs\grace\python.exe
    echo.
    pause
    exit /b 1
)

:: ── [1/4] Stage the run-time assets the spec bundles ───────────────────────
:: The screenshots live in docs\screenshots and the QR image in docs\.
:: They must sit next to the .spec when PyInstaller runs.
echo   [1/4]  Staging bundled assets ...
if not exist "help_docs" mkdir "help_docs"
if exist "..\docs\screenshots\*.png" copy /y "..\docs\screenshots\*.png" "help_docs\" >nul
if not exist "地球重力与人类生活TVGG.jpg" (
    if exist "..\docs\地球重力与人类生活TVGG.jpg" copy /y "..\docs\地球重力与人类生活TVGG.jpg" . >nul
)
echo       done.

:: ── Clean previous output ──────────────────────────────────────────────────
if exist "..\dist\GRACE_Downloader_v1.0.1" rmdir /s /q "..\dist\GRACE_Downloader_v1.0.1"
if exist "..\build_release" rmdir /s /q "..\build_release"

:: ── [2/4] PyInstaller ──────────────────────────────────────────────────────
echo.
echo   [2/4]  PyInstaller  —  freezing the application ...
"%PY%" -m PyInstaller --clean --noconfirm --distpath ..\dist --workpath ..\build_release grace_downloader_release.spec
if errorlevel 1 (
    echo.
    echo   ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

set "REL=..\dist\GRACE_Downloader_v1.0.1"
if not exist "%REL%\GRACE_Downloader.exe" (
    echo.
    echo   ERROR: %REL%\GRACE_Downloader.exe was not produced.
    pause
    exit /b 1
)

:: ── [3/4] Documentation, licence, source and the HTML guide ────────────────
:: GPL v3 requires the corresponding source of the distributed binary plus the
:: licence texts to travel with it (the installer packs this folder verbatim).
echo.
echo   [3/4]  Copying documentation, licence and source ...
copy /y "..\docs\使用说明.md"              "%REL%\" >nul
copy /y "..\docs\方法说明.md"              "%REL%\" >nul
copy /y "..\RELEASE_NOTES.md"             "%REL%\发行说明.md" >nul
copy /y "..\LICENSE"                      "%REL%\LICENSE.txt" >nul
if exist "..\许可说明.md"                  copy /y "..\许可说明.md" "%REL%\" >nul
if exist "..\第三方组件与许可声明.md"         copy /y "..\第三方组件与许可声明.md" "%REL%\" >nul
copy /y "grace_downloader_gui_release.py" "%REL%\" >nul
copy /y "grace_icon.ico"                  "%REL%\" >nul
if exist "grace_icon_preview.png"         copy /y "grace_icon_preview.png" "%REL%\" >nul
if exist "地球重力与人类生活TVGG.jpg"        copy /y "地球重力与人类生活TVGG.jpg" "%REL%\" >nul

:: Screenshots the program ships with, plus the ready-made HTML guide
if not exist "%REL%\help_docs" mkdir "%REL%\help_docs"
if exist "help_docs\*.png" copy /y "help_docs\*.png" "%REL%\help_docs\" >nul
"%PY%" make_help_html.py "%REL%\help_docs"
if errorlevel 1 (
    echo       WARNING: the HTML guide could not be generated -
    echo                the program writes it on first use instead.
)

echo       done.

:: ── [4/4] Optional Inno Setup installer ────────────────────────────────────
echo.
echo   [4/4]  Inno Setup  —  building the installer ...
set "ISCC="
for %%P in (
    "E:\Inno Setup 6\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
    "%ProgramFiles%\Inno Setup 7\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) do (
    if not defined ISCC if exist %%P set "ISCC=%%~P"
)

if not defined ISCC (
    echo       NOT INSTALLED - skipping.  Install it with:
    echo           winget install JRSoftware.InnoSetup
    echo       Then run:  ISCC.exe installer_release.iss
) else (
    echo       compiler: %ISCC%
    call "%ISCC%" installer_release.iss
    if errorlevel 1 (
        echo.
        echo   ERROR: Inno Setup build failed!
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo   Release build complete.
echo.
echo   Portable folder : %REL%\
echo   Executable      : %REL%\GRACE_Downloader.exe
if defined ISCC echo   Installer       : ..\dist\GRACE_Downloader_Setup_v1.0.1.exe
echo ============================================================
echo.
pause
