# Security — Tunnel-Reachable Surfaces & Credentials

What ports the FINAL stack publishes, their auth state, and the policy for exposing them over a tunnel (e.g. Tailscale). **No plaintext default admin credentials for dashboards are committed in this repo** — they come from a gitignored `.env` (see `.env.example`).

## Published surfaces (`docker-compose.final.yml`)
| Service | Host port | Auth | Tunnel-safe? |
|---|---|---|---|
| Gateway (app + API + WS) | 80 | app login (JWT) | ✅ intended public entry |
| Frontend (direct) | 3001 | app login | ✅ |
| **Grafana** | 3000 | admin user + **required** `GRAFANA_ADMIN_PASSWORD` (no default) | ⚠️ only with a strong password set |
| **kafka-ui** | 8080 | **none** | ❌ do not tunnel-expose without a proxy |
| **Dozzle** (logs) | 9999 | **none** | ❌ do not tunnel-expose without a proxy |
| **Postgres** | 55432 | `hcie_user` / `${POSTGRES_PASSWORD}` (dev default `hcie_password`) | ❌ datastore — keep off the tunnel |
| **Redis** | 56379 | **none** (no `requirepass`) | ❌ datastore — keep off the tunnel |
| Prometheus / Loki / Tempo / Pyroscope / exporters | 9090 / 3100 / 3200 / 4040 / 9187 / 9121 | none (read-only telemetry) | ❌ keep internal |
| SonarQube (`docker-compose.sonar.yml`, ad-hoc) | 9000 | first-login `admin/admin` (change on first login) | ❌ dev tool — keep local |

## Credential policy
- **Grafana** admin password is **REQUIRED** — the compose has **no committed default** (`${GRAFANA_ADMIN_PASSWORD:?…}` fails fast if unset). Set it in `.env` (gitignored). `.env.example` documents it.
- **Postgres** password is `${POSTGRES_PASSWORD:-hcie_password}` everywhere (the bare hardcoded values in `connect`/`cutover` were removed). The dev default `hcie_password` is documented in `.env.example`; set a strong `POSTGRES_PASSWORD` **before first DB init** for any non-local deployment (changing it after the volume exists requires `ALTER USER`).
- `.env` is gitignored (`RealSystem/.gitignore`: `.env`, `.env.*`, `!.env.example`); the archived `snapshots/` compose backups are untracked + redacted.

## Exposing over Tailscale — recommended
1. **Expose only what needs it:** the gateway (`:80`). That carries the app + API + WS behind JWT login.
2. **Grafana over the tunnel:** only with a strong `GRAFANA_ADMIN_PASSWORD` set.
3. **Never tunnel-expose the no-auth surfaces** (kafka-ui, Dozzle, Redis, Postgres, the metrics endpoints) without one of:
   - a Tailscale ACL restricting them to your own device, **or**
   - an authenticating reverse proxy in front, **or**
   - binding their host ports to `127.0.0.1` (so only local/forwarded access works), **or**
   - simply not publishing them (drop the `ports:` mapping) when remote review isn't needed.
4. **SonarQube**: change the `admin/admin` first-login password immediately; keep it local.

## What was hardened (2026-06-24)
- Grafana: removed the committed `admin/admin` default → required env var.
- `connect`/`cutover` compose: 9 hardcoded `hcie_password` occurrences → `${POSTGRES_PASSWORD:-…}`.
- `.env.example`: documents Grafana creds + the no-auth-surface warning.
- Archived snapshot: redacted hardcoded Grafana password; `snapshots/` untracked + gitignored.
- `sonar.yml`: comment now flags the `admin/admin` default + caveat.
- No-auth surfaces (kafka-ui/Dozzle/Redis): documented here as not-for-tunnel-exposure (adding auth to each is the remaining optional hardening).
