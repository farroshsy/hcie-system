# Jalankan Expo (SDK 54)

SDK 54 WAJIB Node 20+ (Node 18 → error `configs.toReversed is not a function`).

```bash
# pakai Node 20 (nvm)
export PATH="/Users/farros/.nvm/versions/node/v20.20.0/bin:$PATH"   # atau: nvm use 20
cd ~/HCIE/hcie-system/HCIE_EXPO_CLIENT
npx expo start --lan          # HP di WiFi sama, scan QR
```

- tutorUrl (app.json) = http://192.168.100.170:8080/ (IP Mac; update kalau DHCP ganti).
- QR = exp://<IP>:8081. HP: Expo Go (SDK 54) → scan.
- Di dalam app: login siswa demo (demo.learner@hcie.local / DemoLearner!2026) → /learn → game jalan.
