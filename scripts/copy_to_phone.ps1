# Copy a file to an Android phone's Download folder over USB and prove it arrived intact:
#     powershell.exe -STA -NoProfile -ExecutionPolicy Bypass -File scripts\copy_to_phone.ps1 -Source <face.tbwf> -Phone <part of its name>
#
# The phone must be unlocked, in File transfer mode, and listed under This PC. Windows Shell is the
# only way into MTP storage, and it stalled from PowerShell 7, so run this in powershell.exe -STA.
param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$Phone
)

$ErrorActionPreference = 'Stop'
$Source = (Resolve-Path -LiteralPath $Source).Path
$size = (Get-Item -LiteralPath $Source).Length
$name = [IO.Path]::GetFileName($Source)
$stem = [IO.Path]::GetFileNameWithoutExtension($Source)  # Windows may hide the extension on MTP names.
$noDialogs = 4 + 16 + 1024  # No progress window, yes to all, no error window.
$thisPc = 17

$shell = New-Object -ComObject Shell.Application
$device = $shell.NameSpace($thisPc).Items() |
    Where-Object { -not $_.IsFileSystem -and $_.Name.IndexOf($Phone, [StringComparison]::OrdinalIgnoreCase) -ge 0 } |
    Select-Object -First 1
if (-not $device) { "No phone matching '$Phone' under This PC. Set File transfer on it."; exit 1 }

$storage = $device.GetFolder.Items() | Select-Object -First 1
if (-not $storage) { "$($device.Name) shows no storage. Unlock it and try again."; exit 1 }
$folder = $storage.GetFolder.Items() | Where-Object { $_.Name -eq 'Download' } | Select-Object -First 1
if (-not $folder) { "No Download folder in $($storage.Name)."; exit 1 }
$download = $folder.GetFolder

function Find-File {
    $download.Items() | Where-Object { $_.Name -eq $name -or $_.Name -eq $stem } | Select-Object -First 1
}

function Get-Sha256($Path) {
    # Get-FileHash can be missing here when started from PowerShell 7.
    $sha = [Security.Cryptography.SHA256]::Create()
    [BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($Path)))
}

function Wait-For($Check) {
    foreach ($try in 1..40) {
        $found = & $Check
        if ($found) { return $found }
        Start-Sleep -Milliseconds 500
    }
}

$file = Find-File
if ($file) { "$($device.Name): already has $name, checking it" } else {
    $download.CopyHere($Source, $noDialogs)
    $file = Wait-For { Find-File }
    if (-not $file) { 'The copy never appeared on the phone.'; exit 1 }
    "$($device.Name): copied $name"
}

# Read it back, because the phone's listing shows a size of 0.
$check = Join-Path $env:TEMP ([IO.Path]::GetRandomFileName())
New-Item -ItemType Directory $check | Out-Null
try {
    $shell.NameSpace($check).CopyHere($file, $noDialogs)
    $back = Wait-For { Get-ChildItem -LiteralPath $check -File | Where-Object { $_.Length -eq $size } | Select-Object -First 1 }
    if (-not $back) { 'Could not read back a full copy. If the file on the phone is old, delete it and try again.'; exit 1 }
    Start-Sleep -Milliseconds 500  # CopyHere can still hold the file open.
    if ((Get-Sha256 $back.FullName) -eq (Get-Sha256 $Source)) { 'Identical to the original.'; exit 0 }
    'The file on the phone differs from the original: delete it there and run this again.'
    exit 1
} finally {
    Remove-Item -LiteralPath $check -Recurse -Force
}
