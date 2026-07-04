# Production Deployment Runbook

Topology:

```
[End user] ──https──> [Vercel: hcie-frontend]
                                │
                                │  fetch NEXT_PUBLIC_BACKEND_URL
                                ▼
              [Cloudflare edge: *.cfargotunnel.com]
                                │
                                │  encrypted tunnel
                                ▼
              [This PC: cloudflared] ──> [nginx gateway :80] ──> [api :8000]
                                                                       │
                                                                       └── postgres / kafka / redis / consumers
```

Tailscale is kept for **private admin access only** (SSH into this box, hitting
Grafana / Kafka UI / Prometheus over `100.x.x.x` Tailscale IPs). None of that
infra is on the public tunnel.

---

## One-time setup

### 1. Install cloudflared on this PC

```powershell
# Windows: download the .msi installer
# https://github.com/cloudflare/cloudflared/releases/latest
# OR via winget:
winget install --id Cloudflare.cloudflared
```

Verify:

```powershell
cloudflared --version
```

### 2. Authenticate cloudflared to your Cloudflare account

```powershell
cloudflared tunnel login
```

This opens a browser. Sign in to Cloudflare (free account is fine), then pick
any zone (you do **not** need to own a domain for the auto `*.cfargotunnel.com`
URL, but cloudflared currently requires you to associate the tunnel with
*some* zone for the login flow). The token is written to
`%USERPROFILE%\.cloudflared\cert.pem`.

### 3. Create a named tunnel

```powershell
cloudflared tunnel create hcie-prod
```

This prints a tunnel ID (UUID) and writes credentials to
`%USERPROFILE%\.cloudflared\<UUID>.json`. Copy that path into
`config.yml`'s `credentials-file:` field (or rename the file to
`hcie-prod.json`).

### 4. Wire the tunnel to the local nginx gateway

The `config.yml` in this directory already routes the tunnel to
`http://localhost:80` (the nginx gateway). Copy it to the cloudflared config
directory:

```powershell
Copy-Item .\config.yml $env:USERPROFILE\.cloudflared\config.yml
```

### 5. Get the public URL

```powershell
cloudflared tunnel info hcie-prod
```

The URL looks like `https://<UUID>.cfargotunnel.com`. Save it — this is
`PUBLIC_BACKEND_URL` in subsequent steps.

### 6. Run cloudflared as a Windows service (so it survives reboots)

```powershell
# Run as administrator
cloudflared service install
Start-Service Cloudflared
```

Verify it's healthy:

```powershell
Get-Service Cloudflared
# Status should be: Running

curl https://<UUID>.cfargotunnel.com/gateway-healthz
# Expect: ok
```

---

## Backend changes needed before cutover

These changes touch the API container, so plan to apply them when no
research sweep is running.

### A. Set CORS_ORIGINS env var on the api service

Edit `05_deployment/00_docker/01_compose/docker-compose.final.yml`, find
the `api:` service `environment:` block, and add:

```yaml
- CORS_ORIGINS=["https://<your-vercel-app>.vercel.app","https://<UUID>.cfargotunnel.com","http://localhost:3001","http://127.0.0.1:3001"]
```

(Yes, JSON array as a single env value. The Pydantic field type is
`List[str]` and pydantic-settings parses JSON.)

Then:

```powershell
cd 05_deployment/00_docker/01_compose
docker compose -f docker-compose.final.yml up -d api
```

This is the only api-touching change. The new resume logic ensures any
in-flight cohort runs pick up where they left off after the restart.

### B. Verify CORS preflight from the public URL

```powershell
curl -I -X OPTIONS "https://<UUID>.cfargotunnel.com/v3/healthz" `
  -H "Origin: https://<your-vercel-app>.vercel.app" `
  -H "Access-Control-Request-Method: GET"
```

Expect `200` and headers including:
- `access-control-allow-origin: https://<your-vercel-app>.vercel.app`
- `access-control-allow-credentials: true`

---

## Frontend cutover (Vercel)

1. Go to your Vercel project → Settings → Environment Variables.
2. Add (or update) `NEXT_PUBLIC_BACKEND_URL` to `https://<UUID>.cfargotunnel.com`.
3. Trigger a redeploy (Vercel does this automatically when you save the env var,
   OR push a no-op commit to the connected branch).
4. Open the Vercel deployment URL in a browser. Confirm:
   - Dashboard pages load data (no 503/CORS errors in DevTools).
   - WebSocket connections work — the gateway already proxies `/ws*` to
     `projection-stream-gateway`, and Cloudflare Tunnel handles WS natively.

If you later attach a custom domain to the tunnel, repeat step 2 with the
new URL.

---

## What stays private (Tailscale-only)

These should **never** be on the public tunnel:

| Service | Port | Why |
|---|---|---|
| Postgres | 5432 | Direct DB access |
| Kafka | 9092 | Internal message bus |
| Redis | 6379 | Session/cache |
| Grafana | 3000 (host) | Admin UI |
| Prometheus | 9090 | Admin UI |
| Kafka UI | varies | Admin UI |
| Dozzle | varies | Container log viewer |
| API direct port | 8011 | Only nginx (port 80) should be public |

Access these via Tailscale: `http://100.76.210.29:3000` for Grafana, etc.
This works automatically because the docker-compose port mappings bind to
`0.0.0.0`, and Tailscale is just another network interface.

---

## Production hardening to-do (separate from tunnel rollout)

Audit of current `docker-compose.final.yml`:

| Item | Status | Action |
|---|---|---|
| `restart: unless-stopped` | ✅ All 24 long-running services have it | None |
| `restart: "no"` on 2 init containers | ✅ Intentional | None |
| `logging:` driver/options | ❌ **Zero services** have log rotation configured | Add `json-file` driver with `max-size: 10m`, `max-file: 3` to every service. Logs grow unbounded today. |
| `mem_limit` / `cpus` | ❌ **Zero services** have resource caps | Cap api (4G), kafka (2G), postgres (2G), grafana (512M) at minimum. A runaway worker today could OOM the whole host. |
| Image pinning | ⚠️ `:latest` on 8 services (prometheus, grafana, postgres-exporter, redis-exporter, node-exporter, cadvisor, alertmanager, loki) | Pin to specific versions for reproducibility |
| Volume persistence | ✅ postgres, redis, kafka, grafana, prometheus all have named volumes | None |
| JWT secret | ⚠️ Verify it's loaded from env / secret file, not committed in defaults | Check `04_config/00_schemas/settings.py` for `jwt_secret_key` |
| Admin services public-binding | ⚠️ Grafana/Kafka-UI/Prometheus bind `0.0.0.0` — currently OK because home router blocks inbound, but Tailscale-only binding is safer | Change `ports: ["3000:3000"]` to `ports: ["100.76.210.29:3000:3000"]` (Tailscale IP) for admin UIs |

All of these are **deploy-time changes** that require container recreate, so
batch them into the same rollout where `CORS_ORIGINS` gets set. Suggested
template snippet to add to every service:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```

And on the api / kafka / postgres services:

```yaml
mem_limit: 4g       # api
cpus: 2.0
```

None of these are blockers for the Cloudflare Tunnel rollout itself.

---

## Cutover order (when ready)

1. ✅ Frontend Docker image rebuilt with launcher UI — already in progress.
2. Sweep A finishes (~7200/7200) — wait for it.
3. Edit docker-compose: add `CORS_ORIGINS` env var with Vercel + tunnel URLs.
4. `docker compose up -d api` — resume reaper picks up any in-flight cohort runs.
5. Install + start cloudflared on this PC (steps 1-6 above).
6. Test public URL: `curl https://<UUID>.cfargotunnel.com/gateway-healthz`.
7. Update Vercel `NEXT_PUBLIC_BACKEND_URL` → redeploy.
8. Smoke-test from the Vercel URL in a browser.
9. ✅ Done.

Total time end-to-end: ~30 min once Sweep A finishes, most of which is the
single API container recreate.
