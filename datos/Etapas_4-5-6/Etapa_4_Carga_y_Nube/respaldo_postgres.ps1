<#
.SYNOPSIS
    Genera un respaldo lógico comprimido (.dump) de la base PostgreSQL en la nube (Neon)
    y limpia respaldos antiguos fuera de la ventana de retención.

.DESCRIPTION
    Tarea 21 (Etapa 4): Copias de seguridad automatizadas de Caja Clara.
    Requiere tener PostgreSQL Client Tools (pg_dump) instalado y la variable
    de entorno DATABASE_URL definida (ej. postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require).

.EXAMPLE
    $env:DATABASE_URL = "postgresql://usuario:clave@ep-ejemplo.us-east-2.aws.neon.tech/neondb?sslmode=require"
    .\respaldo_postgres.ps1
#>

param(
    [string]$BackupDir = "$PSScriptRoot\backups",
    [int]$RetentionDays = 30
)

$ErrorActionPreference = "Stop"

if (-not $env:DATABASE_URL) {
    Write-Error "Falta la variable de entorno DATABASE_URL. Configúrala con la cadena de conexión de Neon (sslmode=require)."
    exit 1
}

if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    Write-Error "No se encontró 'pg_dump' en el PATH. Instala PostgreSQL Client Tools."
    exit 1
}

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupDir "cajaclara_backup_$timestamp.dump"

Write-Host "Iniciando respaldo hacia $backupFile ..."
& pg_dump "$env:DATABASE_URL" --format=custom --no-owner --no-privileges --file="$backupFile"

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $backupFile)) {
    Write-Error "Error al generar el respaldo con pg_dump."
    exit 1
}

$sizeMB = [math]::Round((Get-Item $backupFile).Length / 1MB, 2)
Write-Host "Respaldo completado con éxito ($sizeMB MB)."

# Limpieza de respaldos antiguos según retención
$cutoff = (Get-Date).AddDays(-$RetentionDays)
$deleted = Get-ChildItem -Path $BackupDir -Filter "cajaclara_backup_*.dump" | Where-Object { $_.LastWriteTime -lt $cutoff }
foreach ($f in $deleted) {
    Remove-Item $f.FullName -Force
    Write-Host "Respaldo antiguo eliminado por retención: $($f.Name)"
}
