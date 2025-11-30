[Setup]
AppName=VAT Calculator
AppVersion=4.1.0
AppPublisher=Overl1te
AppPublisherURL=https://github.com/Overl1te/VAT-CALC/
DefaultDirName=C:\VAT-CALC
DefaultGroupName=VAT Calculator
OutputBaseFilename=VAT_Calculator_Setup
Compression=lzma2/ultra64
SolidCompression=yes
LanguageDetectionMethod=none
DisableWelcomePage=no
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\VATCalculator.exe
LicenseFile=LICENSE

[Files]
Source: "VATCalculator.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\VAT Calculator"; Filename: "{app}\VATCalculator.exe"; IconFilename: "{app}\icon.ico"; WorkingDir: "{app}"
Name: "{autodesktop}\VAT Calculator"; Filename: "{app}\VATCalculator.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"

[UninstallDelete]
Type: dirifempty; Name: "{userdocs}\vat"
Type: filesandordirs; Name: "{userdocs}\vat"

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[Run]
Filename: "{app}\VATCalculator.exe"; Description: "Запустить VAT Calculator"; Flags: nowait postinstall skipifsilent
