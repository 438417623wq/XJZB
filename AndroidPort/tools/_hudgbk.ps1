# Recover the cp936-corrupted Chinese literals in HudPreview.java using .NET's
# GBK codec (Python's cp936 maps the PUA range differently, which is why the
# pure-Python attempt failed). Emits one line per literal: index, GBK bytes as
# hex, and the literal itself for cross-checking against the class constants.
$ErrorActionPreference = 'Stop'
$path = "$env:TEMP\HudPreview.damaged.java"
$src = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
if ($src[0] -eq [char]0xFEFF) { $src = $src.Substring(1) }

$gbk = [System.Text.Encoding]::GetEncoding(936)
$rx = [regex]'"[^"\r\n]*"'
$i = 0
foreach ($m in $rx.Matches($src)) {
    $body = $m.Value.Substring(1, $m.Value.Length - 2)
    $hasHigh = $false
    foreach ($ch in $body.ToCharArray()) { if ([int]$ch -gt 127) { $hasHigh = $true; break } }
    if (-not $hasHigh) { continue }
    $bytes = $gbk.GetBytes($body)
    $hex = ($bytes | ForEach-Object { '{0:X2}' -f $_ }) -join ''
    $line = '{0}|{1}|{2}' -f $i, $hex, $body
    [System.IO.File]::AppendAllText("$env:TEMP\hud_gbk.txt", $line + "`n",
        (New-Object System.Text.UTF8Encoding($false)))
    $i++
}
"emitted $i literals"
