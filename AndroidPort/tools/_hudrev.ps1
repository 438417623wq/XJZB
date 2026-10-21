# Reverse the cp936 corruption on the WHOLE file at once.
#
# The damage was: original UTF-8 bytes B -> decoded as cp936 -> string S ->
# written back as UTF-8. ASCII survives either way, so the inverse applies to
# the whole file: read UTF-8 -> S, encode cp936 -> B, decode UTF-8 -> original.
# .NET's GBK is required (Python's cp936 maps the PUA range differently).
# Bytes that cp936 could not map became '?' (0x3F) and are unrecoverable, so
# those spots are decoded leniently and patched from the compiled class after.
$ErrorActionPreference = 'Stop'

$src = [System.IO.File]::ReadAllText("$env:TEMP\HudPreview.damaged.java",
    [System.Text.Encoding]::UTF8)
if ($src[0] -eq [char]0xFEFF) { $src = $src.Substring(1) }

$gbk = [System.Text.Encoding]::GetEncoding(936)
$bytes = $gbk.GetBytes($src)
[System.IO.File]::WriteAllBytes("$env:TEMP\hud_rev.bin", $bytes)
"reversed bytes: $($bytes.Length)"

# strict decode to count the unrecoverable spots
$strict = New-Object System.Text.UTF8Encoding($false, $true)
$bad = 0
try { $null = $strict.GetString($bytes) } catch { $bad = 1 }
"strict decode ok: $($bad -eq 0)"
