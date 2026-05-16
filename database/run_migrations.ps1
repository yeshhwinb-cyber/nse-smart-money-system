$ErrorActionPreference = "Stop"

$Database = $env:NSE_DB_NAME
if (-not $Database) {
  $Database = "nse_trading_system"
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Migrations = Join-Path $Root "migrations"

Write-Host "Running PostgreSQL migrations on database: $Database"

Get-ChildItem -LiteralPath $Migrations -Filter "*.sql" | Sort-Object Name | ForEach-Object {
  Write-Host "Applying $($_.Name)"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U Yeshhwin -d $Database -f $_.FullName
}

Write-Host "Database migration complete."
