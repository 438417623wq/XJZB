# v2.43 section 2: build a "before" copy of core/ with the four v2.43
# optimisations backed out, so the plan's step-0 baseline table can carry a real
# before/after pair instead of an estimate.
#
# The reverted sources are compiled into tools\bin_before, and the bench is run
# with bin_before ahead of bin on the classpath, so core.Game resolves to the
# reverted build while GameDesktop still comes from bin.
#
# Nothing here touches app\app\src -- the reverted tree lives only under
# tools\bench_before_src and is regenerated on every run.

$ErrorActionPreference = "Stop"

$root = "F:\KF\XJZB\AndroidPort"
$tools = "$root\tools"
$src = "$root\app\app\src\main\java"
$aj = "C:\Users\XiaoXin\AppData\Local\Android\Sdk\platforms\android-34\android.jar"
$lib = "$tools\bin\lib"
$rev = "$tools\bench_before_src"
$out = "$tools\bin_before"

if (Test-Path $rev) { Remove-Item -Recurse -Force $rev }
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force -Path $rev, $out | Out-Null

Copy-Item -Recurse -Force "$src\com" "$rev\com"

$py = "C:\Users\XiaoXin\AppData\Local\Programs\Python\Python312\python.exe"
& $py "$tools\bench_before_revert.py" "$rev\com\xjzb\rts\core\Game.java"
if ($LASTEXITCODE -ne 0) { Write-Output "REVERT-FAIL"; exit 1 }

$files = Get-ChildItem -Recurse -Filter *.java "$rev\com\xjzb\rts\core" |
    ForEach-Object { $_.FullName }
$files += Get-ChildItem -Recurse -Filter *.java "$rev\com\xjzb\rts\net" |
    ForEach-Object { $_.FullName }

$log = "$tools\out\bench_before_build.log"
& javac -encoding UTF-8 -nowarn -Xlint:none -cp "$aj;$lib" -d $out @files `
    1> "$log.out" 2> "$log.err"
Get-Content "$log.out", "$log.err" -ErrorAction SilentlyContinue |
    Set-Content $log
if ($LASTEXITCODE -ne 0) {
    Write-Output "BEFORE-JAVAC-FAIL"
    Get-Content $log | Select-Object -Last 20
    exit 1
}
Write-Output "BEFORE-BUILD-OK $($files.Count) files"
