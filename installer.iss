; ClipboardAI — Inno Setup Installer Script
; Requires Inno Setup 6+ from https://jrsoftware.org/isinfo.php
; Run this AFTER building dist\ClipboardAI.exe with build.bat

[Setup]
AppName=ClipboardAI
AppVersion=1.0.0
AppPublisher=ClipboardAI
AppPublisherURL=https://github.com/Ysn-Ir/copy_paste_AI
AppSupportURL=https://github.com/Ysn-Ir/copy_paste_AI/issues
AppUpdatesURL=https://github.com/Ysn-Ir/copy_paste_AI

DefaultDirName={autopf}\ClipboardAI
DefaultGroupName=ClipboardAI
AllowNoIcons=yes

; Output
OutputDir=installer_output
OutputBaseFilename=ClipboardAI_Setup_v1.0.0
SetupIconFile=assets\icon.ico

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Appearance
WizardStyle=modern
WizardResizable=no

; Require admin only when needed
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Min Windows version: Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";         GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "startupicon";   Description: "Run ClipboardAI when Windows starts"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
; Main executable
Source: "dist\ClipboardAI.exe";  DestDir: "{app}"; Flags: ignoreversion

; Config & env template (only copy if not already present)
Source: "config.json";    DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: ".env.example";   DestDir: "{app}"; Flags: ignoreversion

; Icon
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\ClipboardAI";         Filename: "{app}\ClipboardAI.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall ClipboardAI"; Filename: "{uninstallexe}"

; Desktop (optional task)
Name: "{commondesktop}\ClipboardAI"; Filename: "{app}\ClipboardAI.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

; Startup (optional task)
Name: "{userstartup}\ClipboardAI";   Filename: "{app}\ClipboardAI.exe"; IconFilename: "{app}\icon.ico"; Tasks: startupicon; Comment: "Start ClipboardAI with Windows"

[Run]
; Offer to launch after install
Filename: "{app}\ClipboardAI.exe"; Description: "Launch ClipboardAI now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user-generated files on uninstall
Type: files; Name: "{app}\log.txt"
Type: files; Name: "{app}\.env"

[Code]
// Show a friendly message if .env doesn't exist after install
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    if not FileExists(ExpandConstant('{app}\.env')) then
      MsgBox(
        'ClipboardAI installed!' + #13#10 + #13#10 +
        'Before using, open ClipboardAI and go to the API Keys tab to add your API key.' + #13#10 + #13#10 +
        'Get a free Gemini key at: aistudio.google.com/app/apikey',
        mbInformation, MB_OK
      );
  end;
end;
