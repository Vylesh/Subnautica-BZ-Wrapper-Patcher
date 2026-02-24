# Subnautica Below Zero - VR Fix Script
# Bu scripti SubnauticaZero.exe ile AYNI klasorde calistir
# Yani: C:\gaming\launchers\steam\steamapps\common\SubnauticaZero\

$gameDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$originalExe = Join-Path $gameDir "SubnauticaZero.exe"
$realExe     = Join-Path $gameDir "SubnauticaZeroReal.exe"

# 1. Eger daha once yapilmadiysa rename et
if (Test-Path $originalExe) {
    if (-not (Test-Path $realExe)) {
        Rename-Item -Path $originalExe -NewName "SubnauticaZeroReal.exe"
        Write-Host "[OK] SubnauticaZero.exe -> SubnauticaZeroReal.exe olarak yeniden adlandirildi"
    } else {
        Write-Host "[SKIP] SubnauticaZeroReal.exe zaten mevcut, rename atlandi"
    }
}

# 1b. _Data klasorunu de rename et (Unity exe adi ile eslesmeyi zorunlu killiyor)
$originalData = Join-Path $gameDir "SubnauticaZero_Data"
$realData      = Join-Path $gameDir "SubnauticaZeroReal_Data"
if (Test-Path $originalData) {
    if (-not (Test-Path $realData)) {
        Rename-Item -Path $originalData -NewName "SubnauticaZeroReal_Data"
        Write-Host "[OK] SubnauticaZero_Data -> SubnauticaZeroReal_Data olarak yeniden adlandirildi"
    } else {
        Write-Host "[SKIP] SubnauticaZeroReal_Data zaten mevcut, rename atlandi"
    }
}

# 2. Wrapper EXE kaynak kodunu olustur
$wrapperCs = Join-Path $gameDir "wrapper_temp.cs"
$wrapperCode = @"
using System;
using System.Diagnostics;
using System.IO;

class VRWrapper {
    static void Main(string[] args) {
        string gameDir = AppDomain.CurrentDomain.BaseDirectory;
        string realExe = Path.Combine(gameDir, "SubnauticaZeroReal.exe");

        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = realExe;
        psi.Arguments = "-vrmode openvr";
        psi.UseShellExecute = false;
        psi.WorkingDirectory = gameDir;

        Process.Start(psi);
    }
}
"@

Set-Content -Path $wrapperCs -Value $wrapperCode -Encoding UTF8

# 3. C# compiler bul ve derle
$cscPaths = @(
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)

$csc = $null
foreach ($path in $cscPaths) {
    if (Test-Path $path) { $csc = $path; break }
}

if ($null -eq $csc) {
    Write-Host "[HATA] csc.exe bulunamadi! .NET Framework 4.x yuklu degil mi?"
    Remove-Item $wrapperCs -ErrorAction SilentlyContinue
    exit 1
}

$outputExe = Join-Path $gameDir "SubnauticaZero.exe"
& $csc /out:"$outputExe" /target:winexe "$wrapperCs" 2>&1

if (Test-Path $outputExe) {
    Write-Host "[OK] Wrapper EXE olusturuldu: SubnauticaZero.exe"
    Write-Host ""
    Write-Host "Artik Steam'den normal baslatabilirsin!"
    Write-Host "Steam -vrmode none eklese bile wrapper onu yoksayip -vrmode openvr ile baslatacak."
} else {
    Write-Host "[HATA] EXE olusturulamadi!"
}

# 4. Gecici dosyayi temizle
Remove-Item $wrapperCs -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Islemi geri almak istersen: SubnauticaZeroReal.exe -> SubnauticaZero.exe, SubnauticaZeroReal_Data -> SubnauticaZero_Data yap, wrapper exe'yi sil."
Read-Host "Devam etmek icin Enter'a bas"
