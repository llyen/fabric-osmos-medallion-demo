# Tworzy workspace Osmos-Demo na wskazanej capacity Fabric, Lakehouse lh_retail
# i wgrywa pliki z ..\dane\raw do Files/raw/retail (OneLake DFS API).
# Wymaga: az login do tenanta z capacity Fabric.
param(
    [string]$WorkspaceName = "Osmos-Demo",
    [Parameter(Mandatory)][string]$CapacityName,
    [string]$LakehouseName = "lh_retail"
)
$ErrorActionPreference = "Stop"
$api = "https://api.fabric.microsoft.com/v1"
$h = "x-ms-fabric-skill=project-osmos"

function FabricGet($url) { az rest --method get --url $url --resource https://api.fabric.microsoft.com --headers $h | ConvertFrom-Json }
function FabricPost($url, $body) {
    $tmp = New-TemporaryFile
    $body | ConvertTo-Json -Compress | Set-Content $tmp -Encoding utf8
    $r = az rest --method post --url $url --resource https://api.fabric.microsoft.com --headers $h "Content-Type=application/json" --body "@$tmp"
    Remove-Item $tmp
    if ($r) { $r | ConvertFrom-Json }
}

$cap = (FabricGet "$api/capacities").value | Where-Object displayName -eq $CapacityName
if (-not $cap) { throw "Brak capacity $CapacityName" }

$ws = (FabricGet "$api/workspaces").value | Where-Object displayName -eq $WorkspaceName
if (-not $ws) {
    $ws = FabricPost "$api/workspaces" @{ displayName = $WorkspaceName; capacityId = $cap.id
        description = "Demo Project Osmos: surowe CSV retail -> medalion Bronze/Silver/Gold" }
    Write-Host "Utworzono workspace $($ws.id)"
} else { Write-Host "Workspace istnieje $($ws.id)" }

$lh = (FabricGet "$api/workspaces/$($ws.id)/lakehouses").value | Where-Object displayName -eq $LakehouseName
if (-not $lh) {
    FabricPost "$api/workspaces/$($ws.id)/lakehouses" @{ displayName = $LakehouseName
        description = "Domyslny lakehouse sesji Spark dla demo Osmos" } | Out-Null
    for ($i = 0; $i -lt 20 -and -not $lh; $i++) {
        Start-Sleep 3
        $lh = (FabricGet "$api/workspaces/$($ws.id)/lakehouses").value | Where-Object displayName -eq $LakehouseName
    }
    Write-Host "Utworzono lakehouse $($lh.id)"
} else { Write-Host "Lakehouse istnieje $($lh.id)" }

$token = az account get-access-token --resource https://storage.azure.com --query accessToken -o tsv
$auth = @{ Authorization = "Bearer $token"; "x-ms-version" = "2023-11-03" }
$root = Resolve-Path (Join-Path $PSScriptRoot "..\dane\raw")
Get-ChildItem $root -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($root.Path.Length + 1).Replace("\", "/")
    $url = "https://onelake.dfs.fabric.microsoft.com/$($ws.id)/$($lh.id)/Files/raw/retail/$rel"
    $bytes = [IO.File]::ReadAllBytes($_.FullName)
    Invoke-RestMethod -Method Put -Uri "$url`?resource=file" -Headers $auth | Out-Null
    Invoke-RestMethod -Method Patch -Uri "$url`?action=append&position=0" -Headers $auth -Body $bytes -ContentType "application/octet-stream" | Out-Null
    Invoke-RestMethod -Method Patch -Uri "$url`?action=flush&position=$($bytes.Length)" -Headers $auth | Out-Null
    Write-Host "Wgrano Files/raw/retail/$rel ($($bytes.Length) B)"
}
[pscustomobject]@{ workspaceId = $ws.id; lakehouseId = $lh.id } | ConvertTo-Json
