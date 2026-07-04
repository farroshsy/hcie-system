# Deploy HCIE di Mac (Intel) — migrasi data, TANPA re-seal

Tujuan: menjalankan stack + SELURUH data tersegel di Mac tanpa mengulang replay 3,5 jam.
Prinsip: **kode dari repo ini · data dari dump Postgres · image dibangun ulang di Mac.**

## Berapa storage yang dibutuhkan Mac

| Komponen | Ukuran | Catatan |
|---|---|---|
| Clone repo ini | ≈ 40 MB | kode BE+FE+Expo terkurasi + artefak data kunci |
| File dump DB (transfer) | **1,71 GB terukur** (full, `D:\HCIE_MIGRATION\hcie_full.dump`, terverifikasi pg_restore -l: 284 entri, 43 tabel) / ≈ 0,8–1 GB (science-only) | boleh dihapus setelah restore |
| DB ter-restore (volume Postgres) | ≈ 13 GB (full) / ≈ 5 GB (science-only) | full = SEMUA tabel; science-only = tanpa 2 tabel transport |
| Docker images (build di Mac) | ≈ 8–10 GB | api 3,5 GB + base konsumen 2,2 GB (layer dibagi) + infra |
| Docker Desktop + cache build | ≈ 2–3 GB | sekali |
| Expo client `node_modules` | ≈ 0,6 GB | hanya jika menjalankan klien Expo dari Mac |
| **TOTAL (full data)** | **≈ 26–30 GB** | rekomendasi: siapkan **40 GB** lega |
| **TOTAL (science-only)** | **≈ 17–20 GB** | siapkan **25 GB** |

Science-only = full MINUS `outbox_event_envelopes` (6,4 GB raw — arsip transport event) dan
`learning_traces` (1,3 GB — log turunan). SEMUA bukti sains tetap utuh: `experiment_trajectories`
(2,7 GB), `tasks`, `external_log_attempts`, `kt_baseline_predictions`, `learner_projections`, dst.
Catatan jujur: tanpa envelope, halaman system-journey menghitung outbox lebih kecil — sains tidak
terpengaruh (semua AUC/ADC/transfer membaca trajektori & prediksi, bukan envelope).

## Langkah (sekali jalan)

```bash
# 0) prasyarat Mac: Docker Desktop (alokasikan ≥ 6 GB RAM), git, node ≥ 18
git clone https://github.com/farroshsy/hcie-system.git && cd hcie-system

# 1) bawa file dump dari PC (AirDrop / disk / scp) — dibuat di PC: D:\HCIE_MIGRATION\hcie_full.dump
#    (versi science-only, jika mau lebih ringan — jalankan di PC:
#     docker exec hcie-final-postgres pg_dump -U hcie_user -d hcie -Fc -Z 6 \
#       --exclude-table-data=outbox_event_envelopes --exclude-table-data=learning_traces \
#       > hcie_science.dump )

# 2) nyalakan stack minimal (postgres dulu)
cd HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose
docker compose -f docker-compose.final.yml up -d postgres
sleep 15

# 3) restore data (masuk ke volume postgres Mac)
docker cp /path/ke/hcie_full.dump $(docker compose -f docker-compose.final.yml ps -q postgres):/tmp/h.dump
docker compose -f docker-compose.final.yml exec postgres \
  pg_restore -U hcie_user -d hcie --clean --if-exists --no-owner -j 4 /tmp/h.dump
docker compose -f docker-compose.final.yml exec postgres rm /tmp/h.dump

# 4) nyalakan sisanya (api, kafka, konsumen, frontend, gateway)
docker compose -f docker-compose.final.yml up -d
docker compose -f docker-compose.final.yml --profile frontend up -d frontend
docker restart hcie-final-gateway   # gateway perlu bounce setelah FE hidup

# 5) verifikasi 2 menit
curl -s localhost:80/healthz                          # 200
curl -s localhost:80/review | grep -o 0.6051 | head -1  # headline tampil
#    verifikasi sains 2 detik (CSV tersegel ada di repo):
python3 - <<'EOF'
import csv; from sklearn.metrics import roc_auc_score
r = list(csv.DictReader(open('docs/figures/data/matched_eval_perrow_run-94a3b8ba.csv')))
print(round(roc_auc_score([int(x['y_true']) for x in r], [float(x['p_hcie']) for x in r]), 4))  # 0.6051
EOF
```

## Yang TIDAK perlu di Mac
- **Re-seal / replay penuh** — datanya sudah di dump (itulah migrasi ini).
- Tailscale Funnel (opsional; hanya jika Mac mau jadi host publik).
- research_validation penuh (4,7 GB di PC) — artefak kuncinya sudah dikurasi di `docs/figures/data/`.

## Expo client dari Mac
```bash
cd HCIE_EXPO_CLIENT && npm install && npx expo start --tunnel
```
Scan QR dengan iPhone (Expo Go). `tutorUrl` di `app.json` menunjuk Funnel PC; ganti ke
`http://<ip-mac>:80/` bila mau menunjuk stack lokal Mac (lalu gunakan LAN, bukan --tunnel).
