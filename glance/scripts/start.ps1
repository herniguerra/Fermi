# Cortex Dashboard — Startup Script
# Launches Glance dashboard + Express API sidecar

$ErrorActionPreference = "Continue"
$glanceDir = "D:\dev\Fermi\glance"

Write-Host ""
Write-Host "  ◈  CORTEX — Starting up..." -ForegroundColor Magenta
Write-Host ""

# Start API sidecar in background
Write-Host "  → Starting API sidecar on port 8099..." -ForegroundColor Cyan
$apiProcess = Start-Process -NoNewWindow -PassThru -FilePath "node" -ArgumentList "server.js" -WorkingDirectory "$glanceDir\api"
Write-Host "    PID: $($apiProcess.Id)" -ForegroundColor DarkGray

# Wait a moment for API to initialize
Start-Sleep -Seconds 2

# Start Glance
Write-Host "  → Starting Glance on port 8080..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  ◈  Dashboard ready at http://localhost:8080" -ForegroundColor Green
Write-Host "  ◈  API sidecar at http://localhost:8099" -ForegroundColor Green
Write-Host ""
Write-Host "  Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host ""

try {
    & "$glanceDir\glance.exe" --config "$glanceDir\glance.yml"
}
finally {
    # Cleanup: stop API sidecar when Glance exits
    Write-Host ""
    Write-Host "  → Stopping API sidecar (PID: $($apiProcess.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $apiProcess.Id -ErrorAction SilentlyContinue
    Write-Host "  ◈  Cortex shut down." -ForegroundColor Magenta
}
