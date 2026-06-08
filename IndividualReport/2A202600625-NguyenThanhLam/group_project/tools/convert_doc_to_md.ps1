param(
    [string]$InputDir = "data\standardized",
    [switch]$ListStreams
)

$ErrorActionPreference = "Stop"

function Get-U16($bytes, $offset) {
    return [BitConverter]::ToUInt16($bytes, $offset)
}

function Get-U32($bytes, $offset) {
    return [BitConverter]::ToUInt32($bytes, $offset)
}

function Get-SectorOffset($sector, $sectorSize) {
    return [int](512 + ([int64]$sector * [int64]$sectorSize))
}

function Read-Sector($bytes, $sector, $sectorSize) {
    $offset = Get-SectorOffset $sector $sectorSize
    $out = New-Object byte[] $sectorSize
    [Array]::Copy($bytes, $offset, $out, 0, $sectorSize)
    return ,$out
}

function Read-Chain($bytes, $fat, $startSector, $sectorSize) {
    $chunks = New-Object System.Collections.Generic.List[byte]
    $sector = [uint32]$startSector
    $seen = @{}
    while ($sector -lt ([uint32]4294967280)) {
        if ($seen.ContainsKey($sector)) { break }
        $seen[$sector] = $true
        [byte[]]$chunk = Read-Sector $bytes $sector $sectorSize
        $chunks.AddRange($chunk)
        if ($sector -ge $fat.Count) { break }
        $sector = [uint32]$fat[$sector]
    }
    return ,[byte[]]$chunks.ToArray()
}

function Read-CfbStreams($path) {
    $bytes = [IO.File]::ReadAllBytes((Resolve-Path $path))
    $magic = ($bytes[0..7] | ForEach-Object { $_.ToString("X2") }) -join " "
    if ($magic -ne "D0 CF 11 E0 A1 B1 1A E1") {
        throw "Not a compound Word .doc file: $path"
    }

    $sectorSize = [int][Math]::Pow(2, (Get-U16 $bytes 0x1E))
    $numFatSectors = Get-U32 $bytes 0x2C
    $firstDirSector = Get-U32 $bytes 0x30

    $difat = New-Object System.Collections.Generic.List[uint32]
    for ($i = 0; $i -lt 109; $i++) {
        $entry = Get-U32 $bytes (0x4C + ($i * 4))
        if ($entry -ne [uint32]::MaxValue) { $difat.Add($entry) }
    }
    if ($difat.Count -gt $numFatSectors) {
        $difat = $difat.GetRange(0, $numFatSectors)
    }

    $fat = New-Object System.Collections.Generic.List[uint32]
    foreach ($fatSector in $difat) {
        [byte[]]$sectorBytes = Read-Sector $bytes $fatSector $sectorSize
        for ($i = 0; $i -lt $sectorSize; $i += 4) {
            $fat.Add((Get-U32 $sectorBytes $i))
        }
    }

    [byte[]]$dirBytes = Read-Sector $bytes $firstDirSector $sectorSize
    $streams = @{}
    for ($offset = 0; $offset + 128 -le $dirBytes.Length; $offset += 128) {
        $nameLen = Get-U16 $dirBytes ($offset + 64)
        if ($nameLen -lt 2) { continue }
        $nameBytes = New-Object byte[] ($nameLen - 2)
        [Array]::Copy($dirBytes, $offset, $nameBytes, 0, $nameLen - 2)
        $name = [Text.Encoding]::Unicode.GetString($nameBytes)
        $type = $dirBytes[$offset + 66]
        if ($type -ne 2) { continue }
        $start = Get-U32 $dirBytes ($offset + 116)
        $sizeLow = Get-U32 $dirBytes ($offset + 120)
        [byte[]]$streamBytes = Read-Chain $bytes $fat $start $sectorSize
        if ($sizeLow -lt $streamBytes.Length) {
            $trimmed = New-Object byte[] $sizeLow
            [Array]::Copy($streamBytes, 0, $trimmed, 0, $sizeLow)
            $streamBytes = $trimmed
        }
        $streams[$name] = $streamBytes
    }
    return ,$streams
}

function Convert-WordDocToText($path) {
    $streams = Read-CfbStreams $path
    if (-not $streams.ContainsKey("WordDocument")) {
        return ""
    }
    $word = $streams["WordDocument"]
    $flags = Get-U16 $word 0x0A
    $tableName = if (($flags -band 0x0200) -ne 0) { "1Table" } else { "0Table" }
    if (-not $streams.ContainsKey($tableName)) {
        $tableName = if ($streams.ContainsKey("0Table")) { "0Table" } else { "1Table" }
    }
    if (-not $streams.ContainsKey($tableName)) {
        return [Text.Encoding]::Unicode.GetString($word)
    }
    $table = $streams[$tableName]
    $fcClx = Get-U32 $word 0x01A2
    $lcbClx = Get-U32 $word 0x01A6
    if ($fcClx -le 0 -or $lcbClx -le 0 -or ($fcClx + $lcbClx) -gt $table.Length) {
        return [Text.Encoding]::Unicode.GetString($word)
    }

    $pos = $fcClx
    $end = $fcClx + $lcbClx
    $textParts = New-Object System.Collections.Generic.List[string]
    while ($pos -lt $end) {
        $marker = $table[$pos]
        $pos++
        if ($marker -eq 0x01) {
            $skip = Get-U16 $table $pos
            $pos += 2 + $skip
            continue
        }
        if ($marker -ne 0x02) { continue }
        $pieceTableSize = Get-U32 $table $pos
        $pos += 4
        $pieceTableStart = $pos
        $pieceCount = [int](($pieceTableSize - 4) / 12)
        if ($pieceCount -le 0) { break }

        for ($i = 0; $i -lt $pieceCount; $i++) {
            $cpStart = Get-U32 $table ($pieceTableStart + ($i * 4))
            $cpEnd = Get-U32 $table ($pieceTableStart + (($i + 1) * 4))
            $charCount = [int]($cpEnd - $cpStart)
            if ($charCount -le 0) { continue }

            $pcdOffset = $pieceTableStart + (($pieceCount + 1) * 4) + ($i * 8)
            $fcValue = Get-U32 $table ($pcdOffset + 2)
            $isCompressed = (($fcValue -band 0x40000000) -ne 0)
            $fc = [int]($fcValue -band 0x3FFFFFFF)
            if ($isCompressed) {
                $fc = [int]($fc / 2)
                $byteCount = $charCount
                if ($fc + $byteCount -le $word.Length) {
                    $pieceBytes = New-Object byte[] $byteCount
                    [Array]::Copy($word, $fc, $pieceBytes, 0, $byteCount)
                    $textParts.Add([Text.Encoding]::UTF8.GetString($pieceBytes))
                }
            }
            else {
                $byteCount = $charCount * 2
                if ($fc + $byteCount -le $word.Length) {
                    $pieceBytes = New-Object byte[] $byteCount
                    [Array]::Copy($word, $fc, $pieceBytes, 0, $byteCount)
                    $textParts.Add([Text.Encoding]::Unicode.GetString($pieceBytes))
                }
            }
        }
        break
    }
    return ($textParts -join "")
}

function Convert-ToMarkdown($text, $title) {
    $text = $text -replace "`0", ""
    $text = $text -replace "`a", "`n"
    $text = $text -replace "`r`n", "`n"
    $text = $text -replace "`r", "`n"
    $lines = $text -split "`n"
    $clean = New-Object System.Collections.Generic.List[string]
    foreach ($line in $lines) {
        $line = ($line -replace "\s+", " ").Trim()
        if ($line.Length -eq 0) {
            if ($clean.Count -gt 0 -and $clean[$clean.Count - 1] -ne "") { $clean.Add("") }
            continue
        }
        if ($line -match "^(CHƯƠNG|Chương|ĐIỀU|Điều)\s+") {
            $clean.Add("")
            $clean.Add("## $line")
        }
        else {
            $clean.Add($line)
        }
    }
    return "# $title`n`n" + (($clean -join "`n").Trim()) + "`n"
}

$docs = Get-ChildItem -LiteralPath $InputDir -Filter *.doc
foreach ($doc in $docs) {
    if ($ListStreams) {
        $streams = Read-CfbStreams $doc.FullName
        Write-Host "Streams in $($doc.Name):"
        Write-Host "  type=$($streams.GetType().FullName) count=$($streams.Count)"
        $streams.Keys | Sort-Object | ForEach-Object { Write-Host "  $_ ($($streams[$_].Length) bytes)" }
        continue
    }
    $text = Convert-WordDocToText $doc.FullName
    if ([string]::IsNullOrWhiteSpace($text)) {
        Write-Warning "No text extracted from $($doc.Name)"
        continue
    }
    $markdown = Convert-ToMarkdown $text $doc.BaseName
    $outPath = Join-Path $doc.DirectoryName ($doc.BaseName + ".md")
    [IO.File]::WriteAllText($outPath, $markdown, [Text.UTF8Encoding]::new($false))
    Write-Host "Converted $($doc.Name) -> $([IO.Path]::GetFileName($outPath))"
}
