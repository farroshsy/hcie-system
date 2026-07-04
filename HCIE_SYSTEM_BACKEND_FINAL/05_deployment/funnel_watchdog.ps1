# Funnel watchdog — keeps https://farrospc.tailb58de0.ts.net alive.
# Root cause it guards against: Docker Desktop host port-proxy wedge (com.docker.backend keeps :80
# open but resets connections after an unclean reboot/sleep) — container looks healthy, funnel 502s.
# Fix = bounce the gateway container, which re-establishes the host port binding.
# Install (Scheduled Task, every 5 min):
#   schtasks /Create /TN "HCIE Funnel Watchdog" /SC MINUTE /MO 5 /RU SYSTEM ^
#     /TR "powershell -NoProfile -ExecutionPolicy Bypass -File \"D:\Code\cld-main\cld-main\ProjectHCIE\RealSystem\HCIE_SYSTEM_BACKEND_FINAL\05_deployment\funnel_watchdog.ps1\""
# Remove: schtasks /Delete /TN "HCIE Funnel Watchdog" /F

$log = "$env:TEMP\hcie_funnel_watchdog.log"
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Add-Content $log }

try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:80/healthz" -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
    if ($r.StatusCode -eq 200) { exit 0 }   # healthy — stay silent
    Log "healthz returned $($r.StatusCode) — bouncing gateway"
} catch {
    Log "port 80 unreachable ($($_.Exception.Message)) — bouncing gateway"
}

docker restart hcie-final-gateway 2>&1 | Out-Null
Start-Sleep -Seconds 8
try {
    $r2 = Invoke-WebRequest -Uri "http://127.0.0.1:80/healthz" -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
    Log "after gateway restart: $($r2.StatusCode)"
} catch {
    Log "still down after gateway restart — restarting Docker port proxy is needed (manual: restart Docker Desktop)"
}
