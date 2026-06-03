; Script de Inno Setup para FODA S5 Command Center
; Diseñado para empaquetar el binario autocontenido y sus recursos en un instalador Windows premium.

[Setup]
AppId={{C78A4D2E-B930-4C9D-A3D9-FA60ED40D0E2}
AppName=FODA S5 Command Center
AppVersion=1.0
AppPublisher=StratCom S5
AppSupportURL=https://github.com/beto/FODA
AppUpdatesURL=https://github.com/beto/FODA
DefaultDirName={localappdata}\FODA_S5_Command_Center
DefaultGroupName=FODA S5 Command Center
DisableProgramGroupPage=yes
LicenseFiles=
; Icono del instalador
SetupIconFile=my_foda_s5.ico
UninstallDisplayIcon={app}\my_foda_s5.ico
; Ubicación y nombre del instalador generado
OutputDir=dist
OutputBaseFilename=Setup_FODA_S5_Command_Center
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; No requiere privilegios de administrador (instalación limpia en Local AppData)
PrivilegesRequired=lowest

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Archivo ejecutable compilado
Source: "dist\FODA_S5_Command_Center\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Icono de la aplicación para el acceso directo
Source: "my_foda_s5.ico"; DestDir: "{app}"; Flags: ignoreversion
; Archivo de base de datos inicial (si existe en desarrollo)
Source: "stratcom_analyses.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
; Hoja de estilos CSS
Source: "styles.css"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FODA S5 Command Center"; Filename: "{app}\FODA_S5_Command_Center.exe"; IconFilename: "{app}\my_foda_s5.ico"
Name: "{group}\{cm:UninstallProgram,FODA S5 Command Center}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\FODA S5 Command Center"; Filename: "{app}\FODA_S5_Command_Center.exe"; IconFilename: "{app}\my_foda_s5.ico"; Tasks: desktopicon

[Run]
; Opción para iniciar la aplicación inmediatamente al finalizar la instalación
Filename: "{app}\FODA_S5_Command_Center.exe"; Description: "{cm:LaunchProgram,FODA S5 Command Center}"; Flags: nowait postinstall skipifsilent

[Code]
// Función personalizada para verificar si Ollama está instalado en el sistema
function IsOllamaInstalled(): Boolean;
begin
  // Busca el ejecutable en las rutas por defecto de Windows
  Result := FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')) or
            FileExists(ExpandConstant('{commonpf}\Ollama\ollama.exe')) or
            FileExists(ExpandConstant('{commonpf64}\Ollama\ollama.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Si Ollama no está instalado, advertimos al usuario y le sugerimos descargarlo
    if not IsOllamaInstalled() then
    begin
      if MsgBox('FODA S5 Command Center utiliza "Ollama" localmente para las funciones de Inteligencia Artificial (Llama 3).' + #13#10#13#10 +
                'No se ha detectado Ollama en su sistema.' + #13#10#13#10 +
                '¿Desea abrir el sitio web de Ollama para descargarlo e instalarlo ahora?', 
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://ollama.com/download', '', '', SW_SHOWNORMAL, errNoWait, ErrorCode);
      end;
    end;
  end;
end;
