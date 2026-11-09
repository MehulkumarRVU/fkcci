param(
    [string]$EnvFile = ".env",
    [string]$ProjectName = "pocketcoach"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$resolvedEnvFile = Join-Path $repositoryRoot $EnvFile
if (-not (Test-Path -LiteralPath $resolvedEnvFile)) {
    throw "Compose environment file not found: $EnvFile"
}

$log = @{
    timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    level = "info"
    event = "backup_started"
} | ConvertTo-Json -Compress
Write-Output $log

Push-Location $repositoryRoot
try {
    & docker compose --project-directory $repositoryRoot --env-file $resolvedEnvFile `
        -p $ProjectName run --rm postgres-maintenance /scripts/backup_postgres.sh
    $backupExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($backupExitCode -ne 0) {
    Write-Output (@{
        timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
        level = "error"
        event = "backup_failed"
        exit_code = $backupExitCode
    } | ConvertTo-Json -Compress)

    $webhook = [Environment]::GetEnvironmentVariable("BACKUP_FAILURE_WEBHOOK_URL")
    if ($webhook) {
        try {
            Invoke-RestMethod -Uri $webhook -Method Post -ContentType "application/json" `
                -Body (@{ text = "PocketCoach PostgreSQL backup failed. Inspect the scheduled task logs." } | ConvertTo-Json -Compress) `
                -TimeoutSec 10 | Out-Null
        }
        catch {
            Write-Warning "Backup failure notification could not be delivered."
        }
    }

    exit $backupExitCode
}

Write-Output (@{
    timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    level = "info"
    event = "backup_completed"
} | ConvertTo-Json -Compress)
