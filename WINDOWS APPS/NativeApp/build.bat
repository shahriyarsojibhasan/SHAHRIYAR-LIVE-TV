@echo off
echo ====================================================
echo  Building SHAHRIYAR LIVE TV Native Windows App
echo ====================================================
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /out:"SHAHRIYAR-LIVE-TV.exe" /win32icon:"icon.ico" /reference:"Microsoft.Web.WebView2.Core.dll" /reference:"Microsoft.Web.WebView2.WinForms.dll" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.dll "Program.cs"
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] SHAHRIYAR-LIVE-TV.exe built successfully (Size: ~270 KB)!
) else (
    echo [ERROR] Build failed.
)
pause
