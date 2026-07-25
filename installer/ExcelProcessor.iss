; Inno Setup script for Excel Processor v1.0.1 full offline installer
#define MyAppName "Excel Processor"
#define MyAppVersion "1.0.1"
[Setup]
AppId={{C7B71C14-2B93-4B2E-A7BC-1234567890AB}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\ExcelProcessor
DefaultGroupName=Excel Processor
OutputBaseFilename=ExcelProcessor-1.0.1-Full-Offline
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
[Files]
Source: "..\dist\payload-modern-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: IsModern64
Source: "..\dist\payload-legacy-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: IsLegacy64
Source: "..\dist\payload-legacy-x86\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: IsX86
[Icons]
Name: "{group}\Excel Processor"; Filename: "{app}\ExcelProcessor.exe"
[Run]
Filename: "{app}\ExcelProcessor.exe"; Parameters: "--self-check"; Flags: runhidden waituntilterminated
[Code]
function IsWin7WithoutSP1(): Boolean;
begin
  Result := (GetWindowsVersion shr 24 = 6) and (((GetWindowsVersion shr 16) and $FF) = 1) and (GetWindowsServicePackMajorVersion < 1);
end;
function InitializeSetup(): Boolean;
begin
  if IsWin7WithoutSP1() then begin MsgBox('Windows 7 requires SP1 to install Excel Processor.', mbCriticalError, MB_OK); Result := False; end else Result := True;
end;
function IsX86(): Boolean; begin Result := not Is64BitInstallMode; end;
function IsModern64(): Boolean; begin Result := Is64BitInstallMode and (GetWindowsVersion >= $0A004563); end;
function IsLegacy64(): Boolean; begin Result := Is64BitInstallMode and not IsModern64(); end;
