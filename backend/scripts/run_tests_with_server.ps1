Param()

Write-Output "Starting backend for tests..."
$pythonExe = Resolve-Path "$PSScriptRoot\..\..\.venv\Scripts\python.exe"
Write-Output "Using python: $pythonExe"
$proc = Start-Process -FilePath $pythonExe -ArgumentList '-m','uvicorn','backend.main:app','--app-dir','backend','--host','0.0.0.0','--port','8080' -PassThru
Write-Output "Started uvicorn PID $($proc.Id)"

for ($i=0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri http://127.0.0.1:8080/health -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { Write-Output "Server healthy"; break }
    } catch {
    }
    Start-Sleep -Seconds 1
}

try {
    Invoke-RestMethod -Uri http://127.0.0.1:8080/health -ErrorAction Stop | Out-Null
} catch {
    Write-Error "Server did not become healthy"
    Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
    exit 1
}

Write-Output "Running pytest..."
& $pythonExe -m pytest -q

Write-Output "Stopping server..."
Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
