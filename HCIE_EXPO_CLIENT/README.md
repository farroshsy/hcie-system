# HCIE Tutor — Expo client (student shell)

Klien seluler Expo/React Native yang menghadirkan antarmuka tutor HCIE pada perangkat seluler
**melalui API/gateway yang sama** (WebView atas Tailscale Funnel). Sesuai kalimat naskah §3.2.4:
klien lintas-platform di atas antarmuka web bersama — BUKAN UI native dari nol (itu future work §5.2.3).

## Menjalankan (Expo Go + QR — iPhone/Android, gratis, tanpa App Store)

Prasyarat sekali saja:
1. Install **Expo Go** dari App Store (iPhone) / Play Store.
2. Node.js ≥ 18 di mesin dev (Windows PC ini ATAU Mac Intel — dua-duanya bisa).

```bash
cd HCIE_EXPO_CLIENT
npm install                 # sekali saja (jika ada warning versi: npx expo install --fix)
npx expo start --tunnel     # --tunnel: QR bisa discan dari jaringan mana pun
```

Scan QR yang muncul dengan **kamera iPhone** → terbuka di Expo Go → app memuat
`https://farrospc.tailb58de0.ts.net/` (pastikan Funnel hidup; watchdog sudah terpasang).

Catatan:
- `--tunnel` memakai relay Expo sehingga iPhone TIDAK harus satu Wi-Fi dengan mesin dev.
- URL tutor dikonfigurasi di `app.json → expo.extra.tutorUrl` (ganti bila gateway pindah).
- Sesi login tersimpan (sharedCookiesEnabled); swipe-back iOS & tombol back Android didukung;
  layar error + retry bila server tak terjangkau.

## Build mandiri (opsional, nanti)
- **Android APK** (tanpa Play Store): `npx eas build -p android --profile preview` (perlu akun Expo gratis).
- **iOS standalone**: perlu Apple Developer Program berbayar + TestFlight — di luar cakupan prototipe;
  untuk sidang cukup Expo Go + QR.

## Posisi di tesis (jangan overclaim)
- §3.2.4: "klien seluler berbasis React Native/Expo yang menghadirkan antarmuka tutor bagi peran
  pelajar… mengonsumsi API yang sama melalui gateway."
- Bila ditanya penguji: kontribusi riset = mesin cold-start (backend); shell Expo lintas-platform
  di atas API yang sama adalah pilihan rekayasa yang tepat pada skala prototipe; UI native penuh
  (mode luring, sandbox kode) = pengembangan lanjutan (§5.2.3).
