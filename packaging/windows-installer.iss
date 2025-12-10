; VaultMind Forge - Inno Setup Installer Script
; Requires: Inno Setup 6.x (https://jrsoftware.org/isdl.php)

#define MyAppName "VaultMind Forge"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Michael Shortland"
#define MyAppURL "https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration"
#define MyAppExeName "vaultmind-forge.exe"

[Setup]
AppId={{8F3A5B2C-1D4E-4F6A-9C8B-2E7D3F1A5C9E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.md
OutputDir=.\dist
OutputBaseFilename=VaultMindForge-{#MyAppVersion}-Setup
SetupIconFile=..\web_ui\public\favicon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startservice"; Description: "Start VaultMind Forge service after installation"; GroupDescription: "Service Options:"; Flags: checked
Name: "installpython"; Description: "Install Python 3.12 (required)"; GroupDescription: "Dependencies:"; Flags: checkedonce
Name: "installnodejs"; Description: "Install Node.js 18 LTS (required for web UI)"; GroupDescription: "Dependencies:"; Flags: checkedonce

[Files]
; Application files
Source: "..\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\vaultmind_forge\*"; DestDir: "{app}\vaultmind_forge"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\web_ui\dist\*"; DestDir: "{app}\web_ui\dist"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration files
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs

; Windows service wrapper
Source: ".\windows-service-wrapper.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\install-service.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\uninstall-service.bat"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\output"; Permissions: users-modify
Name: "{app}\models"; Permissions: users-modify
Name: "{app}\checkpoints"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "http://localhost:8000"; IconFilename: "{app}\web_ui\dist\favicon.ico"
Name: "{group}\{#MyAppName} Documentation"; Filename: "{app}\docs\DEPLOYMENT.md"
Name: "{group}\Start {#MyAppName} Service"; Filename: "{app}\install-service.bat"; IconFilename: "{sys}\shell32.dll"; IconIndex: 77
Name: "{group}\Stop {#MyAppName} Service"; Filename: "{app}\uninstall-service.bat"; IconFilename: "{sys}\shell32.dll"; IconIndex: 131
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "http://localhost:8000"; IconFilename: "{app}\web_ui\dist\favicon.ico"; Tasks: desktopicon

[Run]
; Install Python if selected
Filename: "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1"; Flags: shellexec waituntilterminated; Tasks: installpython; StatusMsg: "Installing Python 3.12..."

; Install Node.js if selected
Filename: "https://nodejs.org/dist/v18.18.0/node-v18.18.0-x64.msi"; Flags: shellexec waituntilterminated; Tasks: installnodejs; StatusMsg: "Installing Node.js 18 LTS..."

; Create virtual environment and install Python dependencies
Filename: "python"; Parameters: "-m venv ""{app}\.venv312"""; WorkingDir: "{app}"; Flags: runhidden waituntilterminated; StatusMsg: "Creating Python virtual environment..."
Filename: "{app}\.venv312\Scripts\pip.exe"; Parameters: "install --upgrade pip"; WorkingDir: "{app}"; Flags: runhidden waituntilterminated; StatusMsg: "Upgrading pip..."
Filename: "{app}\.venv312\Scripts\pip.exe"; Parameters: "install -r requirements.txt"; WorkingDir: "{app}"; Flags: runhidden waituntilterminated; StatusMsg: "Installing Python dependencies..."

; Copy environment template
Filename: "cmd.exe"; Parameters: "/c if not exist ""{app}\.env"" copy ""{app}\.env.example"" ""{app}\.env"""; Flags: runhidden waituntilterminated

; Install and start service
Filename: "{app}\install-service.bat"; WorkingDir: "{app}"; Flags: runhidden waituntilterminated; Tasks: startservice; StatusMsg: "Installing VaultMind Forge service..."

; Open configuration guide
Filename: "notepad.exe"; Parameters: "{app}\.env"; Description: "Configure VaultMind Forge (set API key)"; Flags: postinstall nowait skipifsilent shellexec

; Open browser to app
Filename: "http://localhost:8000"; Description: "Launch VaultMind Forge in browser"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
Filename: "{app}\uninstall-service.bat"; WorkingDir: "{app}"; Flags: runhidden waituntilterminated

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // Check if Python is installed
  if not FileExists(ExpandConstant('{pf}\Python312\python.exe')) and
     (Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) = False) then
  begin
    if MsgBox('Python 3.12 is required but not found. Do you want to download and install it?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Result := True;
    end else
    begin
      MsgBox('VaultMind Forge requires Python 3.12 to function.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;
