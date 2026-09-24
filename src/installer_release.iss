; =============================================================================
;  Inno Setup script — GRACE Downloader v1.0.1  (release build)
; =============================================================================
;  Usage (run from this src\ folder, or simply call build_release.bat):
;    1. Install Inno Setup 6/7 from  https://jrsoftware.org/isinfo.php
;    2. Build the PyInstaller release:
;         pyinstaller --clean --noconfirm --distpath ..\dist --workpath ..\build_release grace_downloader_release.spec
;    3. Run:  ISCC.exe installer_release.iss
;    4. Output:  ..\dist\GRACE_Downloader_Setup_v1.0.1.exe
; =============================================================================

#define MyAppName       "GRACE Downloader"
#define MyAppVersion    "1.0.1"
#define MyAppPublisher  "彭桢燃  Zhenran Peng  (China University of Geosciences, Wuhan)"
#define MyAppURL        "https://github.com/pengzhenran/GRACE-Downloader"
#define MyAppExeName    "GRACE_Downloader.exe"
#define SourceDir       "..\dist\GRACE_Downloader_v1.0.1"
#define OutputDir       "..\dist"

[Setup]
; NOTE: Generate a new GUID for each release:  Tools -> Generate GUID in ISCC
AppId={{8F3A7C2D-5B1E-4A96-9D2E-0F4C8A3B6E71}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Per-user install by default (no admin prompt needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#OutputDir}
OutputBaseFilename=GRACE_Downloader_Setup_v{#MyAppVersion}
SetupIconFile=grace_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式 / Create a &desktop shortcut"; GroupDescription: "附加任务 / Additional shortcuts:"; Flags: checkedonce

[Files]
; PyInstaller output: exe + _internal runtime
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation shipped next to the executable
Source: "{#SourceDir}\使用说明.md";        DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\方法说明.md";        DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\发行说明.md";        DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\LICENSE.txt";       DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\许可说明.md";        DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\第三方组件与许可声明.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\grace_downloader_gui_release.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "{#SourceDir}\grace_icon.ico";     DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\grace_icon_preview.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\地球重力与人类生活TVGG.jpg"; DestDir: "{app}"; Flags: ignoreversion
; Screenshot-based HTML guide (also regenerated automatically if missing)
Source: "{#SourceDir}\help_docs\*"; DestDir: "{app}\help_docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\使用说明 (HTML)"; Filename: "{app}\help_docs\使用说明.html"
Name: "{group}\微信公众号简介 (HTML)"; Filename: "{app}\help_docs\公众号简介_单文件.html"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\help_docs\使用说明.html"; Description: "打开使用说明"; Flags: shellexec nowait postinstall skipifsilent unchecked
Filename: "{app}\help_docs\公众号简介_单文件.html"; Description: "打开公众号简介（图文）"; Flags: shellexec nowait postinstall skipifsilent unchecked

[UninstallDelete]
; Runtime-generated files (remembered credentials, regenerated screenshots)
Type: files; Name: "{app}\.grace_credentials.json"
Type: filesandordirs; Name: "{app}\help_docs"
