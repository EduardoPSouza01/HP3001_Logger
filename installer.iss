; Instalador do HP3001 Logger (Inno Setup 6)
; Gere com:  build_installer.bat   ->   installer_out\HP3001-Setup.exe

#define AppName "HP3001 Logger"
#define AppVersion "1.0.0"
#define AppPublisher "Eduardo Souza"
#define AppExe "HP3001.exe"

[Setup]
AppId={{7C1B6E52-3F0A-4D58-9B7E-5A1D2C3E4F60}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
; Instala por usuario: a pasta fica gravavel (banco, config e settings ficam ao lado do exe) e nao pede administrador
PrivilegesRequired=lowest
DefaultDirName={autopf}\HP3001
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=installer_out
OutputBaseFilename=HP3001-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExe}
CloseApplications=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"
Name: "autostart"; Description: "Iniciar a coleta automaticamente com o Windows (em segundo plano)"; GroupDescription: "Coleta:"

[Files]
; Programa (nunca inclui dados do desenvolvedor)
Source: "dist\HP3001\*"; DestDir: "{app}"; Excludes: "config.ini,hp3001.db,settings.json,hp3001.log,logs"; Flags: recursesubdirs ignoreversion
; Configuracao padrao: so e gravada na primeira instalacao (atualizar nao sobrescreve)
Source: "config.ini"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "HP3001"; ValueData: """{app}\{#AppExe}"" --background"; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir o {#AppName} agora"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#AppExe}"; Flags: runhidden; RunOnceId: "StopHP3001"

[UninstallDelete]
; Banco, config e settings sao mantidos de proposito (dados de auditoria). Apague a pasta manualmente se quiser remove-los.
Type: files; Name: "{app}\hp3001.log"
