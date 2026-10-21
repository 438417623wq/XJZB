# v2.43: syntax-check every app source file without a Gradle build.
#
# The tools/*.java harness cannot compile the app: those files are Android code.
# A full `gradle assembleRelease` takes minutes, so this compiles the whole
# source tree against android.jar into a throwaway directory -- a few seconds,
# and it catches exactly the class of error a big edit introduces (typos,
# missing imports, bad signatures) before a build cycle is spent.
#
# BuildConfig is stubbed because AGP generates it. javac's diagnostics are
# written to a log file and the exit code decides pass/fail, so neither the
# localized "uses deprecated API" note nor PowerShell's NativeCommandError
# wrapping can be mistaken for a real failure.
$root = "F:\KF\XJZB\AndroidPort\app\app\src\main\java"
$aj = "C:\Users\XiaoXin\AppData\Local\Android\Sdk\platforms\android-34\android.jar"
$out = "F:\KF\XJZB\AndroidPort\tools\out\synccheck"
$stub = "F:\KF\XJZB\AndroidPort\tools\out\synccheck_src"
$logPath = "F:\KF\XJZB\AndroidPort\tools\out\synccheck.log"

if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force -Path $out | Out-Null

$files = @()
$files += (Get-ChildItem $root -Recurse -Filter *.java | ForEach-Object { $_.FullName })
$files += (Get-ChildItem $stub -Recurse -Filter *.java | ForEach-Object { $_.FullName })

$args = @("-encoding", "UTF-8", "-nowarn", "-Xlint:none", "-cp", $aj, "-d", $out) + $files
$o = "$logPath.out"
$e = "$logPath.err"
$proc = Start-Process -FilePath "javac" -ArgumentList $args -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $o -RedirectStandardError $e
$code = $proc.ExitCode
$text = ((Get-Content $o -ErrorAction SilentlyContinue) + (Get-Content $e -ErrorAction SilentlyContinue)) -join "`r`n"
Set-Content -Encoding UTF8 -Path $logPath -Value $text

if ($code -eq 0) {
    "SYNC-OK $($files.Count) files"
} else {
    "SYNC-FAIL exit=$code"
    $text
}
