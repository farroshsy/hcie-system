# Tailscale Remote Access Setup

The Docker stack runs locally on Windows. Tailscale lets you (or a reviewer) reach
the API and frontend from any device on your Tailnet without port-forwarding or VPN.

## What you get after setup

| Service            | Local URL                  | Tailscale URL                        |
|--------------------|----------------------------|--------------------------------------|
| API (v3)           | http://localhost:8011      | http://100.x.y.z:8011                |
| Frontend           | http://localhost:3001      | http://100.x.y.z:3001                |
| Gateway (nginx)    | http://localhost:80        | http://100.x.y.z                     |
| ADC Review Portal  | http://localhost/review    | http://100.x.y.z/review              |

Replace `100.x.y.z` with your machine's Tailscale IP (shown in step 3 below).

---

## Step 1 — Install Tailscale on Windows

1. Download from https://tailscale.com/download/windows
2. Run the installer — it installs the system tray app and the `tailscale` CLI
3. Sign in with your Tailscale account (Google / GitHub / Microsoft / email)

---

## Step 2 — Verify the Tailscale IP

```powershell
tailscale ip -4
# Output: 100.x.y.z  ← this is your Tailnet IP
```

All devices on your Tailnet can now reach `100.x.y.z` directly.

---

## Step 3 — Allow the Docker ports through Windows Firewall

Docker Desktop on Windows creates an internal vEthernet adapter. Tailscale traffic
arrives on the main network adapter, not the Docker adapter, so Windows Firewall
needs to allow the ports:

```powershell
# Run as Administrator
netsh advfirewall firewall add rule `
  name="HCIE API (Tailscale)" `
  protocol=TCP dir=in action=allow `
  localport=8011

netsh advfirewall firewall add rule `
  name="HCIE Frontend (Tailscale)" `
  protocol=TCP dir=in action=allow `
  localport=3001

netsh advfirewall firewall add rule `
  name="HCIE Gateway (Tailscale)" `
  protocol=TCP dir=in action=allow `
  localport=80
```

---

## Step 4 — Update your .env

Edit `.env` in this directory:

```dotenv
NEXT_PUBLIC_API_URL=http://100.x.y.z
NEXT_PUBLIC_WS_URL=ws://100.x.y.z
NEXT_PUBLIC_BACKEND_URL=http://100.x.y.z
```

Then rebuild the frontend container so the build-time env vars are baked in:

```powershell
docker compose -f docker-compose.final.yml --profile frontend build frontend
docker compose -f docker-compose.final.yml --profile frontend up -d frontend gateway
```

---

## Step 5 — Test from another device

From any device on your Tailnet (phone, laptop, etc.):

```
http://100.x.y.z/review          # ADC Review Portal (no login)
http://100.x.y.z/review/replay   # Replay Explorer (live DB mode)
http://100.x.y.z:8011/healthz    # API health check
http://100.x.y.z:8011/docs       # FastAPI Swagger UI
```

---

## Optional: tailscale serve (HTTPS + named hostname)

If you want `https://your-machine-name.ts.net` instead of a raw IP, use
`tailscale serve`. This terminates TLS at the Tailscale daemon and proxies to
your local Docker port.

```powershell
# Expose the gateway on HTTPS (port 443 on your Tailnet hostname)
tailscale serve --bg https / http://localhost:80

# Expose the API directly (useful for reviewers hitting /v3/review/*)
tailscale serve --bg https:8011 / http://localhost:8011
```

Then the URLs become:
- `https://your-machine-name.ts.net/review`
- `https://your-machine-name.ts.net:8011/docs`

Check active serves:
```powershell
tailscale serve status
```

Remove a serve rule:
```powershell
tailscale serve --bg https:8011 off
```

---

## Seed the admin user over Tailscale

Once the stack is up and reachable, you can also seed the admin from another
machine:

```bash
# From any machine on the Tailnet
ADMIN_PASSWORD=yourpassword \
POSTGRES_HOST=100.x.y.z \
POSTGRES_PORT=55432 \
python 03_scripts/01_ops/seed_admin.py
```

Or exec into the running API container (still from this machine):

```powershell
$env:ADMIN_PASSWORD = "yourpassword"
docker exec -e ADMIN_PASSWORD=$env:ADMIN_PASSWORD hcie-final-api `
  python /app/03_scripts/01_ops/seed_admin.py
```

---

## Security note

Tailscale restricts access to authenticated Tailnet members only. The Docker
stack itself has no TLS — Tailscale provides the encrypted tunnel. If you use
`tailscale funnel` (public internet access), add auth to the review endpoints
first.
