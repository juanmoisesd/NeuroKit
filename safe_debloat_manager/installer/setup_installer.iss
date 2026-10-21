; Script de Instalación Inno Setup para Safe Debloat Manager v1.0

[Setup]
AppId={{8F12B2A3-4C9D-4E11-9A3B-8C91D3F7A21E}
AppName=Safe Debloat Manager
AppVersion=1.0.0
AppPublisher=Safe Debloat Software
DefaultDirName={autopf}\SafeDebloatManager
DefaultGroupName=Safe Debloat Manager
UninstallDisplayIcon={app}\SafeDebloatManager.exe
Compression=lzma2
SolidCompression=yes
OutputDir=Output
OutputBaseFilename=SafeDebloatManager_Setup_x64
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SafeDebloatManager.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Safe Debloat Manager"; Filename: "{app}\SafeDebloatManager.exe"
Name: "{autodesktop}\Safe Debloat Manager"; Filename: "{app}\SafeDebloatManager.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SafeDebloatManager.exe"; Description: "Ejecutar Safe Debloat Manager"; Flags: nowait postinstall skipifsilent
