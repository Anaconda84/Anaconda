!define PRODUCT "SwarmVideo"
!define VERSION "0.9"
!define BG "bgprocess"
!define STARTUP "Software\Microsoft\Windows\CurrentVersion\Run"

!include "MUI.nsh"

var IsWindowsServer2008
var IsWindowsServer2008R2
var IsWindowsServer2012

;--------------------------------
;Configuration

;General
Name "${PRODUCT} ${VERSION}"
OutFile "${PRODUCT}_${VERSION}.exe"

;Folder selection page
InstallDir "$APPDATA\${PRODUCT}"
 
;Remember install folder
InstallDirRegKey HKCU "Software\${PRODUCT}" ""

;
; Uncomment for smaller file size
;
SetCompressor "lzma"
;
; Uncomment for quick built time
;
;SetCompress "off"

CompletedText "Installation completed. Thank you for choosing ${PRODUCT}"

BrandingText "${PRODUCT}"

;--------------------------------
;Modern UI Configuration

!define MUI_ABORTWARNING
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "heading.bmp"

;--------------------------------
;Pages

!define MUI_LICENSEPAGE_RADIOBUTTONS
!define MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_ACCEPT "I accept"
!define MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_DECLINE "I decline"
#!define MUI_FINISHPAGE_RUN "$INSTDIR\bgprocess\SwarmEngine.exe"

;!insertmacro MUI_PAGE_LICENSE "binary-LICENSE.txt"
;!insertmacro MUI_PAGE_COMPONENTS
;!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;!insertmacro MUI_DEFAULT UMUI_HEADERIMAGE_BMP heading.bmp"

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"
 
;--------------------------------
;Language Strings

;Description
;LangString DESC_SecMain ${LANG_ENGLISH} "Install ${PRODUCT}"
;LangString DESC_SecStart ${LANG_ENGLISH} "Create Start Menu Shortcuts"

;--------------------------------
;Installer Sections

Section "!Main EXE" SecMain
 SectionIn RO
 SetOutPath "$INSTDIR"
 File *.txt

 Processes::FindProcess "SwarmEngine"
 Pop $R0
 StrCmp $R0 "1" 0 next
;      Messagebox MB_OK "SwarmEngine.exe is found!!!"
      FileOpen $0 $APPDATA\${PRODUCT}\goodbay w
        FileWrite $0 "goodbay"
      FileClose $0

      StrCpy $0 "0"
      loop:
        IfFileExists $APPDATA\${PRODUCT}\goodbay 0 done
        StrCmp $0 "60" done
        IntOp $0 $0 + 1
;	Messagebox MB_OK "Counter = $0"
	Sleep 1000
	Goto loop
      done:

      Sleep 1000
      IfFileExists $APPDATA\${PRODUCT}\goodbay 0 +2
        Delete $APPDATA\${PRODUCT}\goodbay
next:
; Messagebox MB_OK "File SwarmEngine.exe is not found!!!"

; ExecWait "taskkill /F /IM SwarmEngine.exe"

 File /r bgprocess

 WriteRegStr HKCU "Software\${PRODUCT}" "BGProcessPath" "$INSTDIR\bgprocess\SwarmEngine.exe"
 WriteRegStr HKCU "Software\${PRODUCT}" "InstallDir" "$INSTDIR"

 WriteRegStr HKCU "${STARTUP}" "SwarmVideo" "$INSTDIR\bgprocess\SwarmEngine.exe"

 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "DisplayName" "${PRODUCT}"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "UninstallString" "$INSTDIR\Uninstall.exe"

 WriteUninstaller "$INSTDIR\Uninstall.exe"


 ; Add an application to the firewall exception list - All Networks - All IP Version - Enabled
 SimpleFC::AddApplication "SwarmEngine" "$INSTDIR\bgprocess\SwarmEngine.exe" 0 2 "" 1
 Pop $0 ; return error(1)/success(0)

 ; Add the port 37/TCP to the firewall exception list - All Networks - All IP Version - Enabled
 ;SimpleFC::AddPort 37 "My Application" 6 0 2 "" 1
 ;Pop $0 ; return error(1)/success(0)

 Version::IsWindowsServer2008
 Pop $IsWindowsServer2008
 Version::IsWindowsServer2008R2
 Pop $IsWindowsServer2008R2
 Version::IsWindowsServer2012
 Pop $IsWindowsServer2012
 ${if} $IsWindowsServer2008 == "1"
   ExecWait "bitsadmin  /transfer dwnl /download /priority normal http://193.105.240.206:8000/vcredist_x86.exe $TEMP\vcredist_x86.exe"
   ExecWait "$TEMP\vcredist_x86.exe /q"
 ${EndIf}
 ${if} $IsWindowsServer2008R2 == "1"
   ExecWait "bitsadmin  /transfer dwnl /download /priority normal http://193.105.240.206:8000/vcredist_x86.exe $TEMP\vcredist_x86.exe"
   ExecWait "$TEMP\vcredist_x86.exe /q"
 ${EndIf}
 ${if} $IsWindowsServer2012 == "1"
   ExecWait "bitsadmin  /transfer dwnl /download /priority normal http://193.105.240.206:8000/vcredist_x86.exe $TEMP\vcredist_x86.exe"
   ExecWait "$TEMP\vcredist_x86.exe /q"
 ${EndIf}

 
SectionEnd


;Section "Startmenu Icons" SecStart
;   SetShellVarContext all
;   CreateDirectory "$SMPROGRAMS\${PRODUCT}"
;   CreateShortCut "$SMPROGRAMS\${PRODUCT}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
;SectionEnd

Section -Post
   Exec "$APPDATA\${PRODUCT}\bgprocess\SwarmEngine.exe"
SectionEnd


;--------------------------------
;Descriptions

;!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
;!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
;!insertmacro MUI_DESCRIPTION_TEXT ${SecStart} $(DESC_SecStart)
;!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"
 Processes::FindProcess "SwarmEngine"
 Pop $R0
 StrCmp $R0 "1" 0 next
;      Messagebox MB_OK "SwarmEngine.exe is found!!!"
      FileOpen $0 $APPDATA\${PRODUCT}\goodbay w
        FileWrite $0 "goodbay"
      FileClose $0

      StrCpy $0 "0"
      loop:
        IfFileExists $APPDATA\${PRODUCT}\goodbay 0 done
        StrCmp $0 "60" done
        IntOp $0 $0 + 1
;	Messagebox MB_OK "Counter = $0"
	Sleep 1000
	Goto loop
      done:

      Sleep 1000
      IfFileExists $APPDATA\${PRODUCT}\goodbay 0 +2
        Delete $APPDATA\${PRODUCT}\goodbay
next:

 RMDir /r "$INSTDIR"

 SetShellVarContext all
 RMDir "$SMPROGRAMS\${PRODUCT}"
 RMDir /r "$SMPROGRAMS\${PRODUCT}"

 ReadEnvStr $R0 "HOMEDRIVE" 
 ReadEnvStr $R1 "HOMEPATH" 

 ;messageBox MB_OK "$R0$R1\AppData\Roaming\.SwarmVideo"
 RMDir /r "$R0$R1\AppData\Roaming\.SwarmVideo"

 DeleteRegKey HKCU "SOFTWARE\${PRODUCT}"
 DeleteRegKey HKCU "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}"

 DeleteRegValue HKCU "${STARTUP}" "${PRODUCT}"
 SimpleFC::RemoveApplication "$INSTDIR\bgprocess\SwarmEngine.exe"
 Pop $0 ; return error(1)/success(0)


SectionEnd

;--------------------------------
;Functions Section

Function .onInit
  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "SwarmVideo") i .r1 ?e' 

  Pop $R0 

  StrCmp $R0 0 +3 

  MessageBox MB_OK "The installer is already running."

  Abort 
FunctionEnd
