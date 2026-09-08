$ErrorActionPreference = 'Stop'
$copyRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'execution/project'))
$fixtureRoot = Join-Path $copyRoot '.elenchus/lab/R002/identity-research/junction-fixtures'
$linkPath = [IO.Path]::GetFullPath((Join-Path $fixtureRoot 'source/linked-target'))
$targetPath = (Resolve-Path -LiteralPath (Join-Path $fixtureRoot 'target')).Path
foreach ($scopedPath in @($linkPath, $targetPath)) {
    if (-not $scopedPath.StartsWith($copyRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Fixture path escaped execution copy: $scopedPath"
    }
}
if (Test-Path -LiteralPath $linkPath) { throw 'Refusing to replace an existing path.' }
New-Item -ItemType Junction -Path $linkPath -Target $targetPath | Out-Null
$junction = Get-Item -LiteralPath $linkPath -Force
$record = [ordered]@{
    command = 'New-Item -ItemType Junction -Path <linkPath> -Target <targetPath>'
    linkPath = $linkPath
    targetPath = $targetPath
    attributes = [string]$junction.Attributes
    linkType = $junction.LinkType
    source = 'Supplied identity-research/notes.md, junction reconstruction instructions'
    exit_code = 0
}
$record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence/junction-setup.json') -Encoding utf8
$record | ConvertTo-Json
