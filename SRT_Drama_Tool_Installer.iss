; ============================================================================
; Inno Setup Script for SRT Drama Tool
; Developer: Nou Sarat
; Version: 1.0.3
; ============================================================================

#define MyAppName "SRT Drama Tool"
#define MyAppVersion "1.0.3"
#define MyAppPublisher "Nou Sarat"
#define MyAppURL "https://github.com/saratboy1988-a11y/SRT-Drama-Tool/releases/latest"
#define MyAppExeName "SRT Drama Tool.exe"
#define MyAppContact "096 22 11 947"

[Setup]
; Basic Setup Information
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion} PRO
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
VersionInfoVersion=1.0.3.0
VersionInfoCopyright=Copyright © 2024-2026 {#MyAppPublisher}
VersionInfoDescription=Professional SRT Subtitle and Voice Tool with AI RVC
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.0.3

; Installation Settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
OutputDir=installer_output
OutputBaseFilename=SRT_Drama_Tool_v{#MyAppVersion}_Setup
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
CompressionThreads=auto

; User Interface
WizardStyle=modern
WizardSizePercent=100,100
SetupIconFile=logo.ico
WizardImageFile=
WizardSmallImageFile=
DisableWelcomePage=no
ShowLanguageDialog=no

; Privileges and Architecture
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=6.1sp1

; Other Settings
DisableDirPage=auto
DisableProgramGroupPage=auto
DisableReadyPage=no
CreateAppDir=yes
CreateUninstallRegKey=yes
UsePreviousAppDir=yes
UsePreviousGroup=yes
UsePreviousSetupType=yes
UsePreviousTasks=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main Application
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Configuration Files (will be preserved on update)
Source: "app_settings.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall
Source: "role_configs.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall
Source: "rvc_config.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "srt_drama_tool.png"; DestDir: "{app}"; Flags: ignoreversion

; Helper Scripts
Source: "install_ffmpeg.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_pytorch.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "verify_installation.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "test_gpu.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "download_models.py"; DestDir: "{app}"; Flags: ignoreversion

; Documentation (if exists)
Source: "*.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
; Start Menu Icons
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{group}\Documentation"; Filename: "{app}\docs"; Check: DirExists(ExpandConstant('{app}\docs'))

; Desktop Icon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch Icon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data on uninstall
Type: filesandordirs; Name: "{app}\docs"
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\__pycache__"

[Registry]
; Register file associations (optional - for .dtp files)
; Root: HKA; Subkey: "Software\Classes\.dtp"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName}.Project"; Flags: uninsdeletevalue
; Root: HKA; Subkey: "Software\Classes\{#MyAppName}.Project"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName} Project File"; Flags: uninsdeletekey
; Root: HKA; Subkey: "Software\Classes\{#MyAppName}.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
; Root: HKA; Subkey: "Software\Classes\{#MyAppName}.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Code]
var
  DownloadPage: TDownloadWizardPage;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  if Progress = ProgressMax then
    Log(Format('Successfully downloaded file to {tmp}: %s', [FileName]));
  Result := True;
end;

procedure InitializeWizard;
begin
  // Create download page for FFmpeg if needed
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), @OnDownloadProgress);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Check if minimum Windows version is met
  if not IsWin64 then
  begin
    MsgBox('This application requires 64-bit Windows 7 or later.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Set permissions for the installation folder
    if not IsAdminLoggedOn then
    begin
      // For non-admin installs, ensure user has write permissions
      Log('Setting folder permissions for user access');
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserChoice: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Ask user if they want to keep their settings
    UserChoice := MsgBox('Do you want to keep your settings and configurations?' + #13#10 +
                         '(សូមរក្សាទុកការកំណត់របស់អ្នក?)', 
                         mbConfirmation, MB_YESNO or MB_DEFBUTTON1);
    
    if UserChoice = IDYES then
    begin
      // Keep configuration files
      Log('User chose to keep settings');
      // Files marked with uninsneveruninstall will be preserved
    end
    else
    begin
      Log('User chose to delete all settings');
      // Remove the uninsneveruninstall flag by deleting manually
      DeleteFile(ExpandConstant('{app}\app_settings.json'));
    end;
  end;
  
  if CurUninstallStep = usPostUninstall then
  begin
    // Clean up any remaining files
    Log('Uninstallation completed');
  end;
end;

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then
  begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end
  else
    Result := 1;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpReady then
  begin
    // Check for previous installation
    if IsUpgrade() then
    begin
      if MsgBox('A previous version is detected. It will be uninstalled before continuing.' + #13#10 +
                '(មាន version ចាស់។ វានឹងត្រូវបាន uninstall មុនពេល install ថ្មី)',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON1) = IDYES then
      begin
        UnInstallOldVersion();
      end;
    end;
  end;
end;
