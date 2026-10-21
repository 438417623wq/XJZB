# v2.43: (re)compile the app's pure-logic packages into tools/bin for the
# desktop harness.
#
# WHY THIS EXISTS
# ---------------
# The harness (GameDesktop) links against com.xjzb.rts.core.Game. For a long
# time bin/com/xjzb/rts/core/*.class was produced by hand, and `javac -cp bin
# -d bin GameDesktop.java` only ever recompiled GameDesktop itself -- so edits
# to Game.java were silently NOT exercised by the harness. That is a trap: the
# suite stays green while the simulation under test is a stale build.
#
# core/ + net/ are pure Java except SpriteBank.java (android.graphics), which
# is never referenced by the harness; compiling it against android.jar keeps
# this a single javac invocation.
#
# Run this BEFORE GameDesktop whenever app/core or app/net changed.
$src = "F:\KF\XJZB\AndroidPort\app\app\src\main\java"
$aj = "C:\Users\XiaoXin\AppData\Local\Android\Sdk\platforms\android-34\android.jar"
$bin = "F:\KF\XJZB\AndroidPort\tools\bin"
$lib = "$bin\lib\*"
$logPath = "F:\KF\XJZB\AndroidPort\tools\out\rebuild_bin.log"

$files = @()
$files += (Get-ChildItem "$src\com\xjzb\rts\core" -Filter *.java | ForEach-Object { $_.FullName })
$files += (Get-ChildItem "$src\com\xjzb\rts\net" -Filter *.java | ForEach-Object { $_.FullName })

$args = @("-encoding", "UTF-8", "-nowarn", "-Xlint:none",
          "-cp", "$aj;$lib", "-d", $bin) + $files
$o = "$logPath.out"
$e = "$logPath.err"
$proc = Start-Process -FilePath "javac" -ArgumentList $args -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $o -RedirectStandardError $e
$code = $proc.ExitCode
$text = ((Get-Content $o -ErrorAction SilentlyContinue) + (Get-Content $e -ErrorAction SilentlyContinue)) -join "`r`n"
Set-Content -Encoding UTF8 -Path $logPath -Value $text

if ($code -eq 0) {
    "BIN-OK $($files.Count) files"
} else {
    "BIN-FAIL exit=$code"
    $text
}
