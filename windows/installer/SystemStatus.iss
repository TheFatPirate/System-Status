#define MyAppName "System Status"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "The Fat Pirate"
#define MyAppExeName "SystemStatus.exe"

[Setup]
AppId={{6EBD534B-BC28-48B1-9437-00F146E33981}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\System Status
DefaultGroupName=System Status
DisableProgramGroupPage=yes
OutputDir=..\..\dist\installer
OutputBaseFilename=SystemStatus-Windows-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=System Status for Windows
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCopyright=The Fat Pirate

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startup"; Description: "Start System Status automatically with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\..\dist\SystemStatus\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\THIRD-PARTY-NOTICES.md"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "..\licenses\LibreHardwareMonitor\LICENSE"; DestDir: "{app}\licenses\LibreHardwareMonitor"; Flags: ignoreversion
Source: "..\licenses\LibreHardwareMonitor\THIRD-PARTY-NOTICES.txt"; DestDir: "{app}\licenses\LibreHardwareMonitor"; Flags: ignoreversion

[Icons]
Name: "{group}\System Status"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\System Status"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\System Status"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch System Status"; Flags: nowait postinstall skipifsilent
