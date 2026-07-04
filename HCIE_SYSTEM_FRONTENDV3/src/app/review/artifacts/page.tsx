'use client'

// Catalog of EVERY Bab 3-4 table & figure: verbatim caption + provenance (where
// the data comes from) + intent (why it exists) + use (what claim it supports)
// + where to see it live. Data-driven; captions are verbatim from the naskah.
import { useState } from 'react'
import Link from 'next/link'
import { Panel, Eyebrow } from '@/lib/ui/primitives'
import { t as tk } from '@/lib/ui/theme'
import { useT } from '@/contexts/language_context'

type Kind = 'tabel' | 'gambar'
type Item = {
  id: string          // "3.13"
  kind: Kind
  caption: string     // verbatim
  source: string      // provenance: where the data/diagram comes from
  intent: string      // why it exists / what question it answers
  use: string         // which claim/RQ it supports
  live?: string       // FE route (or external subpath) where the data is visible
  liveLabel?: string
}

const DESIGN = 'Rancangan Bab 3 (artefak desain — bukan pengukuran)'
const SEALED = 'Run tersegel run-94a3b8ba (anchor d2154070)'

const ITEMS: Item[] = [
  // ── BAB 3 — TABEL (design/planning artifacts) ─────────────────────────────
  { id: '3.1', kind: 'tabel', caption: 'Dimensi fungsi tata kelola',
    source: DESIGN + '; formulasi weighted-sum (Pers. 2.20)',
    intent: 'Mendefinisikan 6 dimensi J_t sebelum implementasi — apa saja pertimbangan keputusan adaptif.',
    use: 'Fondasi RM3 (observabilitas tata kelola); dieksekusi oleh Algoritma 3.7.',
    live: '/review/trace', liveLabel: 'dekomposisi live' },
  { id: '3.2', kind: 'tabel', caption: 'Deskripsi raw dataset',
    source: 'Dokumentasi dataset publik (Junyi, EdNet, ASSISTments, CSEDM, Statics)',
    intent: 'Transparansi bahan mentah sebelum praproses.',
    use: 'Dasar pemilihan ekologi evaluasi lintas-topologi.', live: '/review/cross-dataset' },
  { id: '3.3', kind: 'tabel', caption: 'Daftar model pembanding',
    source: 'Literatur KT (BKT/DKT/SAKT/GKT) — paradigma klasik, RNN, attention, graph',
    intent: 'Menetapkan pembanding SEBELUM hasil ada (anti cherry-picking).',
    use: 'Semua klaim komparatif Bab 4.', live: '/review/algo-compare' },
  { id: '3.4', kind: 'tabel', caption: 'Metrik evaluasi',
    source: DESIGN,
    intent: 'Mengunci metrik di muka: AUC (utama), akurasi, prefix performance, kalibrasi.',
    use: 'Protokol Tabel 4.8/4.10; menjawab "kenapa AUC".', live: '/review/baselines' },
  { id: '3.5', kind: 'tabel', caption: 'Matriks ketertelusuran penelitian',
    source: DESIGN,
    intent: 'Memetakan RM → metode → bukti, satu baris per rumusan masalah.',
    use: 'Navigasi penguji: setiap RM punya jalur bukti.', live: '/review/start-here' },
  { id: '3.6', kind: 'tabel', caption: 'Kebutuhan perangkat keras',
    source: DESIGN, intent: 'Spesifikasi minimal agar reproduksi realistis (tanpa GPU).',
    use: 'Klaim efisiensi: seluruh evaluasi CPU-only.', live: '/review/algo-compare' },
  { id: '3.7', kind: 'tabel', caption: 'Lingkungan pengembangan dan kerangka kerja',
    source: DESIGN, intent: 'Mencatat stack (FastAPI, Next.js, dsb.) untuk reproduktibilitas.',
    use: 'Realisasi §4.1.', live: '/review/architecture' },
  { id: '3.8', kind: 'tabel', caption: 'Basis data dan infrastruktur data',
    source: DESIGN, intent: 'Postgres = source of truth; Redis = cache; Kafka = bus — peran dipisah eksplisit.',
    use: 'Klaim event-sourcing & auditabilitas.', live: '/review/system-journey' },
  { id: '3.9', kind: 'tabel', caption: 'Library dan tools pendukung',
    source: DESIGN, intent: 'Dependensi tercatat (versi) demi reproduksi build.',
    use: 'Reproduktibilitas rekayasa.', live: '/dashboard/quality' },
  { id: '3.10', kind: 'tabel', caption: 'Daftar dataset evaluasi',
    source: 'Praproses dari raw dataset (T3.2) → registry evaluasi',
    intent: 'Dataset mana yang benar-benar dipakai evaluasi + perannya.',
    use: 'Ekologi lintas-topologi RM4/ADC.', live: '/review/cross-dataset' },
  { id: '3.11', kind: 'tabel', caption: 'Konfigurasi deployment',
    source: DESIGN + ' → docker-compose.final.yml',
    intent: 'Parameter deployment dikunci (port, layanan, profil).',
    use: 'Sistem berjalan = klaim, bukan janji.', live: '/review/system-journey' },
  { id: '3.12', kind: 'tabel', caption: 'Perbandingan karakteristik komputasi dan operasional antarmodel',
    source: 'Analisis kompleksitas per paradigma (literatur + derivasi)',
    intent: 'Posisi HCIE vs deep model SEBELUM angka AUC: biaya, pelatihan, auditabilitas.',
    use: 'Frame "kompetitif tanpa pelatihan" (G4.16).', live: '/review/algo-compare' },
  { id: '3.13', kind: 'tabel', caption: 'Evolusi kuantitas state penguasaan pada lintasan ilustratif (deret jawaban y = 1, 0, 1)',
    source: 'Perhitungan eksak Algoritma 3.1 (benih 0,5/0,25; Q=0,01; R=0,1)',
    intent: 'Contoh kerja bernomor: pembaca bisa cek tiap angka dengan kalkulator.',
    use: 'Bukti state eksplisit & dapat diaudit; dianimasikan di stepper.',
    live: '/review/algo-compare', liveLabel: 'stepper animasi (§4)' },
  { id: '3.14', kind: 'tabel', caption: 'Pemetaan komponen sistem ke rancangan realisasinya',
    source: DESIGN, intent: 'Jembatan desain → kode: tiap komponen konseptual punya realisasi bernama.',
    use: 'Fidelitas desain-implementasi.', live: '/review/architecture' },
  { id: '3.15', kind: 'tabel', caption: 'Statistik dataset knowledge tracing',
    source: 'Hitungan langsung atas dataset terpraproses (baris, pelajar, konsep)',
    intent: 'Skala & sparsitas tiap dataset — konteks kesulitan cold-start.',
    use: 'Kontekstualisasi hasil per-dataset.', live: '/review/cross-dataset' },
  { id: '3.16', kind: 'tabel', caption: 'Pemetaan dataset ke computational thinking (berbasis kerangka K-12)',
    source: 'Pemetaan manual pra-registrasi (kerangka CT K-12), sebelum evaluasi',
    intent: 'Menyatukan domain lintas-dataset ke satu taksonomi konsep.',
    use: 'Jawaban "subjektivitas pemetaan": ditetapkan di muka.', live: '/review/topology' },
  { id: '3.17', kind: 'tabel', caption: 'Log interaksi sistem',
    source: DESIGN + ' (skema event)', intent: 'Skema data interaksi: apa yang direkam per upaya.',
    use: 'Input Algoritma 3.5; dasar keterlacakan.', live: '/review/run-it-yourself' },
  { id: '3.18', kind: 'tabel', caption: 'Model pembanding dan keluarga paradigma',
    source: 'Literatur KT', intent: 'Tiap baseline mewakili satu keluarga (probabilistik/RNN/attention/graph).',
    use: 'Justifikasi pemilihan baseline (Q28/Q51).', live: '/review/algo-compare' },
  { id: '3.19', kind: 'tabel', caption: 'Mekanisme dan observabilitas enam dimensi tata kelola J_t',
    source: DESIGN, intent: 'Per dimensi: dari mana sinyalnya + bagaimana diamati.',
    use: 'Pra-registrasi verdikt ADC (dibandingkan hasil di T4.11).', live: '/review/trace' },
  { id: '3.20', kind: 'tabel', caption: 'Dua keluarga pembanding yang direncanakan',
    source: DESIGN, intent: 'Memisahkan pembanding prediktif vs operasional.',
    use: 'Struktur evaluasi §4.2.', live: '/review/baselines' },
  { id: '3.21', kind: 'tabel', caption: 'Skenario pengujian yang direncanakan',
    source: DESIGN, intent: 'Skenario uji dikunci sebelum implementasi (apa yang disebut lulus).',
    use: 'Anti moving-the-goalposts.', live: '/dashboard/method-grounding' },
  { id: '3.22', kind: 'tabel', caption: 'Tahapan evaluasi berdasarkan jumlah interaksi',
    source: DESIGN, intent: 'Definisi jendela cold-start (≤5/≤10/≤20/all) di muka.',
    use: 'Prefix performance & Tabel 4.8.', live: '/review/baselines' },
  { id: '3.23', kind: 'tabel', caption: 'Daftar metrik sistem',
    source: DESIGN, intent: 'Metrik operasional (latensi, throughput) selain metrik ilmiah.',
    use: 'Bukti §4 (p95 24 ms).', live: '/review/algo-compare', liveLabel: 'biaya terukur (§6)' },
  { id: '3.24', kind: 'tabel', caption: 'Kompleksitas komputasi model',
    source: 'Derivasi per algoritma (window konstan diverifikasi di kode)',
    intent: 'O() per tahap HCIE vs baseline — dasar klaim O(K).',
    use: 'RM1 efisiensi; slide 40/42.', live: '/review/algo-compare' },
  { id: '3.25', kind: 'tabel', caption: 'Lini masa pengerjaan tugas akhir',
    source: DESIGN, intent: 'Perencanaan waktu penelitian.', use: 'Administratif.' },

  // ── BAB 4 — TABEL (measurements) ──────────────────────────────────────────
  { id: '4.1', kind: 'tabel', caption: 'Parameter realisasi model penguasaan',
    source: 'kalman_learner.py + konfigurasi terdeploy (Q=0,01; R=0,1; init; clip)',
    intent: 'Parameter yang BENAR-BENAR jalan — bukan yang direncanakan.',
    use: 'Fidelitas kode-naskah; sensitivitas G4.18.', live: '/review/algo-compare' },
  { id: '4.2', kind: 'tabel', caption: 'Registry sumber data yang direalisasikan',
    source: 'DB: cohort_specs + experiment_runs',
    intent: 'Run mana memuat dataset apa — jejak provenance evaluasi.',
    use: 'Setiap AUC bisa ditelusuri ke run_id.', live: '/review/replay' },
  { id: '4.3', kind: 'tabel', caption: 'Perbandingan AUC implementasi sendiri vs pustaka pyKT',
    source: 'Probe paritas: DKT custom 0,589 ≈ pyKT 0,584; SAKT custom ≥ pyKT',
    intent: 'Menutup keraguan "baseline-mu lemah karena implementasi sendiri".',
    use: 'Fairness komparasi (Q62).', live: '/review/baselines' },
  { id: '4.4', kind: 'tabel', caption: 'Rekonstruksi jejak keputusan lima interaksi pertama (pelajar acuan)',
    source: SEALED + ' — baris trajektori pelajar acuan',
    intent: 'Bukti konkret: keputusan nyata bisa direkonstruksi baris demi baris.',
    use: 'Klaim auditabilitas (RM2).', live: '/review/run-it-yourself' },
  { id: '4.5', kind: 'tabel', caption: 'Kompleksitas komputasi per interaksi',
    source: 'Verifikasi kode: window konstan 10/100/100/50/20 (governance/fusion/bandit)',
    intent: 'O(K) bukan klaim teoretis — batas window ditunjuk di kode.',
    use: 'RM1; jawaban "buktikan O(K)".', live: '/review/algo-compare' },
  { id: '4.6', kind: 'tabel', caption: 'Validasi determinisme pemutaran ulang per permukaan keputusan',
    source: 'replay_determinism_layers (dua jalan, seed sama)',
    intent: 'Envelope per permukaan: exact / runtime 2,5e-3 / governance 4e-2.',
    use: 'Reproduktibilitas §4.10.5.', live: '/dashboard/reproducibility' },
  { id: '4.7', kind: 'tabel', caption: 'Ringkasan analisis statis kualitas kode (SonarQube)',
    source: 'Scan SonarQube terhadap repo (versi tercantum di naskah)',
    intent: 'Kualitas rekayasa terukur pihak-ketiga, bukan self-report.',
    use: 'Pendukung klaim sistem-nyata.', live: '/dashboard/quality' },
  { id: '4.8', kind: 'tabel', caption: 'AUC cold-start tercocok HCIE vs model pembanding (10 pelajar held-out)',
    source: SEALED + ' → dump_matched_eval_perrow.py (verifikasi ulang ≈2 dtk: 0,6051/0,5963/0,5892/0,5730/0,5711)',
    intent: 'HEADLINE: prediksi cold-start tercocok, tie-aware, bebas-bocor.',
    use: 'RM1/RM5; slide 11.', live: '/review/baselines' },
  { id: '4.9', kind: 'tabel', caption: 'AUC lintas-dataset (jendela ≤20): HCIE vs model pembanding — pembacaan m_K',
    source: 'regen lintas-dataset m_K (coldstart_mK_all_datasets.json)',
    intent: 'Generalisasi lintas ekologi + kejujuran flip deployed→m_K.',
    use: 'RM5; jawaban generalisasi.', live: '/review/cross-dataset' },
  { id: '4.10', kind: 'tabel', caption: 'Perbandingan tersegel terhadap warmed-BKT',
    source: SEALED + ' + warmed-BKT (ASSISTments overall +0,003)',
    intent: 'Uji keras: lawan BKT yang sudah "dipanaskan".',
    use: 'Kejujuran batas keunggulan.', live: '/review/baselines' },
  { id: '4.11', kind: 'tabel', caption: 'Klasifikasi observabilitas enam dimensi tata kelola (run tersegel, N=96.727)',
    source: SEALED + ' → Algoritma 3.3 (α_floor 0,01; rasio 0,08)',
    intent: 'Verdikt AKTIF/DORMAN per dimensi — hasil inti ADC.',
    use: 'RM3; slide 36.', live: '/dashboard/governance' },
  { id: '4.12', kind: 'tabel', caption: 'Penarikan lengan bandit per peringkat efektivitas (pilot live, 50 pelajar)',
    source: 'Pilot live 50 pelajar (berlabel; bandit modalitas real-learner-only)',
    intent: 'Bukti bandit modalitas bekerja pada trafik nyata.',
    use: 'RM2 personalisasi representasi.', live: '/dashboard/archetype-modality' },
  { id: '4.13', kind: 'tabel', caption: 'Validasi lintas-dataset klasifikasi ADC per kelas topologi',
    source: 'Run per-dataset + taksonomi topologi (explicit-DAG / flat / null)',
    intent: 'Kontrol positif-negatif: transfer AKTIF di DAG eksplisit, nol struktural di null-graph.',
    use: 'RM4; jawaban dorman-vs-signifikan.', live: '/review/topology' },
  { id: '4.14', kind: 'tabel', caption: 'AUC keseluruhan dan biaya pelatihan per model',
    source: 'Gabungan T4.8 + biaya pelatihan per paradigma',
    intent: 'Trade-off eksplisit: akurasi vs biaya (dasar G4.16 Pareto).',
    use: 'Klaim "kompetitif tanpa pelatihan".', live: '/review/baselines' },
  { id: '4.15', kind: 'tabel', caption: 'Perbandingan kapabilitas HCIE dan model knowledge tracing pembanding',
    source: 'Analisis kapabilitas 8-sumbu (auditabilitas, cold-start, biaya, dsb.)',
    intent: 'Sumbu non-prediktif tempat HCIE menang struktural.',
    use: 'Framing kontribusi (bukan cuma AUC).', live: '/review/start-here' },
  { id: '4.16', kind: 'tabel', caption: 'Ringkasan kontribusi penelitian, bukti empiris, dan temuan utama',
    source: 'Sintesis seluruh Bab 4',
    intent: 'Satu tabel = peta klaim→bukti untuk penguji.',
    use: 'Penutup; navigasi sidang.', live: '/review/start-here' },
  { id: '4.17', kind: 'tabel', caption: 'Keeksakan bit-demi-bit kuantitas keadaan pada pemutaran ulang',
    source: 'Replay dua-jalan atas run tersegel (bit-identik pada lapisan keputusan)',
    intent: 'Bukti terkuat reproduktibilitas: bukan "mirip", tapi bit-sama.',
    use: 'RM2/keterlacakan; slide 43.', live: '/dashboard/reproducibility' },

  // ── BAB 3 — GAMBAR ────────────────────────────────────────────────────────
  { id: '3.1g', kind: 'gambar', caption: 'Ikhtisar konseptual sistem yang diusulkan',
    source: DESIGN, intent: 'Peta besar sebelum detail: masalah → mesin → bukti.',
    use: 'Orientasi pembaca.', live: '/review/start-here' },
  { id: '3.2g', kind: 'gambar', caption: 'Arsitektur sistem',
    source: DESIGN + ' (diagram mermaid, sumber di repo)',
    intent: 'Gateway → runtime → persistensi → observabilitas.',
    use: 'Realisasi di G4.2.', live: '/review/architecture' },
  { id: '3.3g', kind: 'gambar', caption: 'Loop interaksi adaptif',
    source: DESIGN + ' — DIKOREKSI: bandit memilih; J_t = pandangan ADC',
    intent: 'Lingkar tertutup observe→update→govern→select→serve.',
    use: 'Visual Algoritma 3.5.', live: '/review/run-it-yourself' },
  { id: '3.4g', kind: 'gambar', caption: 'Kerangka model yang diusulkan',
    source: DESIGN + ' — DIKOREKSI (JT-stance)', intent: 'State [m,σ²,z] → bandit → reward; J_t mengaudit.',
    use: 'Kerangka RM1-RM3.', live: '/review/theory' },
  { id: '3.5g', kind: 'gambar', caption: 'Kerangka estimasi penguasaan: Kalman kanonik + ensemble sebagai sumber sinyal',
    source: DESIGN, intent: 'Kenapa m = m_K dan σ² = dispersi ensemble.',
    use: 'Justifikasi estimator (T4.3, 0,705-vs-0,644).', live: '/review/algo-compare' },
  { id: '3.6g', kind: 'gambar', caption: 'Alur eksperimen',
    source: DESIGN, intent: 'Sumber data → praproses → protokol → model → metrik.',
    use: 'Peta metodologi.', live: '/review/methods' },
  { id: '3.7g', kind: 'gambar', caption: 'Protokol eksperimen (evaluasi tercocok)',
    source: DESIGN, intent: 'Visual Algoritma 3.2: predict-before-observe.',
    use: 'Klaim bebas-bocor.', live: '/review/baselines' },
  { id: '3.8g', kind: 'gambar', caption: 'Diagram kelas: struktur perangkat lunak model dan kebijakan',
    source: 'Struktur kode 00_core (learners/ensemble/bandit)',
    intent: 'Pemisahan estimator vs kebijakan di tingkat kelas.',
    use: 'Jawaban "kenapa dipisah".', live: '/review/architecture' },
  { id: '3.9g', kind: 'gambar', caption: 'Diagram komponen sistem HCIE',
    source: DESIGN, intent: 'Komponen + antarmuka antar-layanan.',
    use: 'Realisasi §4.1.', live: '/review/architecture' },
  { id: '3.10g', kind: 'gambar', caption: 'Diagram deployment: node, artefak, dan port',
    source: 'docker-compose.final.yml', intent: 'Topologi deploy konkret (port, kontainer).',
    use: 'Sistem nyata; G4.2.', live: '/review/system-journey' },
  { id: '3.11g', kind: 'gambar', caption: 'Model data konseptual (CDM): entitas dan relasi',
    source: DESIGN + ' (8 entitas)', intent: 'Struktur data tingkat konsep.',
    use: 'Slide 28; dasar PDM.', live: '/review/architecture' },
  { id: '3.12g', kind: 'gambar', caption: 'Model data fisik (PDM): tabel, kolom, dan kunci',
    source: 'Skema Postgres terdeploy', intent: 'Realisasi CDM di DB nyata.',
    use: 'Slide 29; jawaban struktur data.', live: '/review/architecture' },
  { id: '3.13g', kind: 'gambar', caption: 'Struktur prasyarat konsep computational thinking K-12',
    source: 'Kurikulum CT K-12 (representatif; sisi dapat diekspor dari registry)',
    intent: 'Hierarki jenjang → dasar kata "Hierarchical" + gerbang DAG.',
    use: 'RM4; transfer.', live: '/review/topology' },
  { id: '3.14g', kind: 'gambar', caption: 'DAG prasyarat kurikulum Intro-Python',
    source: 'Registry konsep terdeploy', intent: 'DAG konkret yang dipakai runtime.',
    use: 'Gerbang Alg 3.5 baris 3.', live: '/review/topology' },
  { id: '3.15g', kind: 'gambar', caption: 'Detail strand Algoritma dan Pemrograman antarjenjang',
    source: 'Kurikulum CT K-12', intent: 'Zoom-in satu strand lintas jenjang.',
    use: 'Konteks kurikulum.', live: '/review/topology' },
  { id: '3.16g', kind: 'gambar', caption: 'Propagasi penguasaan prasyarat pada cold-start',
    source: DESIGN, intent: 'Bagaimana prediksi konsep baru melampaui base-rate via graf.',
    use: 'Mekanisme transfer (RM4).', live: '/review/methods' },
  { id: '3.17g', kind: 'gambar', caption: 'Siklus hidup kohort eksperimen',
    source: DESIGN + ' (state machine)', intent: 'Spec → run → attempting → finalized → audit-ready.',
    use: 'Provenance run.', live: '/review/replay' },
  { id: '3.18g', kind: 'gambar', caption: 'Alur instrumen observabilitas tata kelola (ADC)',
    source: DESIGN, intent: 'Snapshot → klasifikasi dimensi → verdikt → taksonomi.',
    use: 'Visual Algoritma 3.3/3.7.', live: '/review/adc-general' },
  { id: '3.19g', kind: 'gambar', caption: 'Alur evaluasi sistem',
    source: DESIGN, intent: 'Rangkaian evaluasi end-to-end.',
    use: 'Peta Bab 4.', live: '/review/methods' },

  // ── BAB 4 — GAMBAR ────────────────────────────────────────────────────────
  { id: '4.1g', kind: 'gambar', caption: 'Evolusi state pengetahuan dan ketidakpastian epistemic selama personalisasi cold-start',
    source: SEALED + ' (pelajar tersegel; m₁=0,143 Laplace-1/7; σ² puncak ~0,028 di i7 → ~0,010 di i20)',
    intent: 'Bukti state hidup sejak interaksi-1 dan σ² non-monoton (jujur).',
    use: 'RM1; jawaban σ².', live: '/dashboard/cold-start-journey' },
  { id: '4.2g', kind: 'gambar', caption: 'Topologi realisasi sistem HCIE',
    source: 'Stack terdeploy (kontainer live)', intent: 'Yang benar-benar berjalan vs yang dirancang (G3.2).',
    use: 'Sistem nyata.', live: '/review/system-journey' },
  { id: '4.3g', kind: 'gambar', caption: 'Antarmuka tutor adaptif dengan panel penjelas keputusan',
    source: 'Screenshot FE live (/learn)', intent: 'Keputusan + alasannya TERLIHAT oleh pelajar.',
    use: 'Auditabilitas ujung-pengguna.', live: '/learn' },
  { id: '4.4g', kind: 'gambar', caption: 'Monitor tata kelola (mode backend langsung)',
    source: 'Screenshot FE live', intent: 'J_t & dimensi dipantau real-time.',
    use: 'RM3 operasional.', live: '/dashboard/governance' },
  { id: '4.5g', kind: 'gambar', caption: 'Validasi determinisme melalui pemutaran ulang keputusan',
    source: 'Replay dua-jalan (T4.6/T4.17)', intent: 'Visual bukti bit-identik.',
    use: 'Reproduktibilitas.', live: '/dashboard/reproducibility' },
  { id: '4.6g', kind: 'gambar', caption: 'Dasbor Grafana HCIE System',
    source: 'Grafana live (read-only)', intent: 'Observabilitas operasional pihak-ketiga.',
    use: 'Sistem hidup.', live: '/grafana/', liveLabel: 'Grafana (live)' },
  { id: '4.7g', kind: 'gambar', caption: 'Kafka UI: grup konsumen stabil tanpa backlog',
    source: 'Kafka UI live', intent: 'Konsumen sehat = pipeline event jalan.',
    use: 'Event-sourcing nyata.', live: '/kafka-ui', liveLabel: 'Kafka UI (live)' },
  { id: '4.8g', kind: 'gambar', caption: 'AUC jendela cold-start terdingin (domain CSEDM)',
    source: 'Evaluasi m_K per jendela (CSEDM)', intent: 'Perilaku di jendela paling ekstrem.',
    use: 'Kejujuran cold-start.', live: '/review/cross-dataset' },
  { id: '4.9g', kind: 'gambar', caption: 'AUC cold-start tercocok per jendela (pola Simpson)',
    source: SEALED, intent: 'Mengungkap Simpson: agregat menang ≠ menang tiap sel.',
    use: 'Kejujuran per-jendela (slide 12).', live: '/review/baselines' },
  { id: '4.10g', kind: 'gambar', caption: 'Sapuan skala AUC terhadap ukuran sampel',
    source: 'Scale sweep atas run tersegel', intent: 'Stabilitas AUC terhadap N.',
    use: 'Robustness.', live: '/review/figures' },
  { id: '4.11g', kind: 'gambar', caption: 'Matriks lintas-dataset AUC HCIE vs model pembanding',
    source: 'coldstart_mK_all_datasets.json', intent: 'Satu pandangan semua dataset × model.',
    use: 'RM5 generalisasi.', live: '/review/cross-dataset' },
  { id: '4.12g', kind: 'gambar', caption: 'Ekologi kebijakan berdasarkan konsentrasi dan entropi tata kelola',
    source: SEALED, intent: 'Bagaimana ekologi memengaruhi konsentrasi keputusan.',
    use: 'RM3 konteks.', live: '/dashboard/governance' },
  { id: '4.13g', kind: 'gambar', caption: 'Dekomposisi kontribusi enam dimensi fungsi tata kelola J_t',
    source: SEALED + ' (porsi: Challenge 0,158 · Uncertainty 0,119 · ΔM 0,083 · ZPD 0,044 · T_realized 0,015)',
    intent: 'Dimensi mana yang benar-benar menggerakkan J_t.',
    use: 'RM3; input verdikt T4.11.', live: '/review/trace' },
  { id: '4.14g', kind: 'gambar', caption: 'Identifikasi transfer: efek durable, kontrol plasebo, dan null shuffled-DAG',
    source: 'prospective_probe_v3_full_K1000.json (0,091/0,038/0,053; p<0,001; N=1.976.020)',
    intent: 'Bukti kausal-residu dengan kontrol ganda.',
    use: 'RM4; slide 13.', live: '/review/methods', liveLabel: 'sandbox §H' },
  { id: '4.15g', kind: 'gambar', caption: 'Ablasi fungsi tata kelola (J_t)',
    source: 'Ablasi JT atas run tersegel', intent: 'Kontribusi komponen J_t saat dimatikan.',
    use: 'RM3.', live: '/review/ablation' },
  { id: '4.16g', kind: 'gambar', caption: 'Frontier biaya–kinerja: AUC vs kebutuhan data pelatihan luring',
    source: 'T4.14 (AUC + biaya pelatihan)', intent: 'Pareto: HCIE kompetitif di biaya ~nol.',
    use: 'Klaim inti efisiensi.', live: '/review/baselines' },
  { id: '4.17g', kind: 'gambar', caption: 'Diagram reliabilitas kalibrasi: HCIE mentah & Platt vs BKT',
    source: 'Kalibrasi pada run tercocok tersegel (ECE mentah → Platt)',
    intent: 'Probabilitas bermakna, bukan sekadar ranking.',
    use: 'Jawaban kalibrasi (Q60).', live: '/review/figures' },
  { id: '4.18g', kind: 'gambar', caption: 'Sensitivitas parameter derau Kalman (Q, R) terhadap AUC tercocok',
    source: 'Sweep eksak-pada-tersegel (kalman_learner.py riil; base 0,6049 ≈ 0,6051)',
    intent: 'Q/R dipilih di plateau, bukan puncak tuning; degradasi R besar DITAMPILKAN.',
    use: 'Jawaban "dari mana Q dan R".', live: '/review/figures' },
  { id: '4.19g', kind: 'gambar', caption: 'Tingkat kesalahan HCIE per kelompok struktural',
    source: 'Analisis mekanistik galat (per-baris CSV tersegel)',
    intent: 'DI MANA model salah (label/kedalaman/frekuensi/volatilitas).',
    use: 'Kejujuran mekanistik.', live: '/review/figures' },
  { id: '4.20g', kind: 'gambar', caption: 'Dekomposisi galat HCIE: false-positive optimis (carryover) dan under-prediction',
    source: 'Analisis per-baris tersegel: 67,1% FP optimis; 87,5% pasca-jawaban-benar',
    intent: 'MENGAPA model salah: carryover penguasaan.',
    use: 'Analisis kegagalan jujur.', live: '/review/figures' },
]

const CHIP = (active: boolean, color = '#1565C0') => ({
  padding: '5px 14px', borderRadius: 999, fontSize: 12, fontWeight: 700 as const, cursor: 'pointer',
  border: `1px solid ${active ? color : '#CBD5E0'}`,
  background: active ? color : '#fff', color: active ? '#fff' : '#4A5568',
})

export default function ArtifactsPage() {
  const { t } = useT()
  const [bab, setBab] = useState<'all' | '3' | '4'>('all')
  const [kind, setKind] = useState<'all' | Kind>('all')
  const [q, setQ] = useState('')
  const shown = ITEMS.filter(it =>
    (bab === 'all' || it.id.startsWith(bab)) &&
    (kind === 'all' || it.kind === kind) &&
    (!q || (it.caption + it.source + it.intent + it.use).toLowerCase().includes(q.toLowerCase())))
  const label = (it: Item) => `${it.kind === 'tabel' ? 'Tabel' : 'Gambar'} ${it.id.replace('g', '')}`
  return (
    <div style={{ maxWidth: 1080, margin: '0 auto', padding: tk.space.xl }}>
      <Eyebrow color="#1565C0">EVIDENCE MAP · BAB 3–4</Eyebrow>
      <h1 style={{ fontSize: tk.font.size.h2, fontWeight: tk.font.weight.heavy, color: tk.color.ink, marginBottom: 6 }}>
        Semua Tabel &amp; Gambar Naskah — Sumber, Intent, dan Bukti Hidupnya
      </h1>
      <p style={{ fontSize: 13.5, color: tk.color.body, lineHeight: 1.6, marginBottom: 16, maxWidth: 860 }}>
        Katalog lengkap {ITEMS.filter(i => i.kind === 'tabel').length} tabel + {ITEMS.filter(i => i.kind === 'gambar').length} gambar
        Bab 3–4: dari mana datanya, kenapa artefak itu ada, klaim apa yang ditopangnya, dan di mana melihat datanya
        hidup di sistem ini. Bab 3 = artefak rancangan (pra-registrasi); Bab 4 = pengukuran (run tersegel / DB / skrip).
      </p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 18 }}>
        <button style={CHIP(bab === 'all')} onClick={() => setBab('all')}>Semua bab</button>
        <button style={CHIP(bab === '3')} onClick={() => setBab('3')}>Bab 3 (rancangan)</button>
        <button style={CHIP(bab === '4')} onClick={() => setBab('4')}>Bab 4 (pengukuran)</button>
        <span style={{ width: 12 }} />
        <button style={CHIP(kind === 'all', '#1E8449')} onClick={() => setKind('all')}>Tabel + Gambar</button>
        <button style={CHIP(kind === 'tabel', '#1E8449')} onClick={() => setKind('tabel')}>Tabel</button>
        <button style={CHIP(kind === 'gambar', '#1E8449')} onClick={() => setKind('gambar')}>Gambar</button>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="cari… (mis. AUC, ADC, Kalman)"
          style={{ marginLeft: 'auto', padding: '6px 12px', borderRadius: 6, border: '1px solid #CBD5E0', fontSize: 13, minWidth: 220 }} />
        <span style={{ fontSize: 12, color: '#718096' }}>{shown.length}/{ITEMS.length}</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(480px, 1fr))', gap: 12 }}>
        {shown.map(it => (
          <Panel key={it.id} style={{ padding: 14 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 800, padding: '2px 8px', borderRadius: 4,
                             background: it.kind === 'tabel' ? '#E3F2FD' : '#E8F5E9',
                             color: it.kind === 'tabel' ? '#1565C0' : '#1E8449' }}>{label(it)}</span>
              <span style={{ fontSize: 13.5, fontWeight: 700, color: tk.color.ink, lineHeight: 1.35 }}>{it.caption}</span>
            </div>
            <div style={{ fontSize: 12, color: tk.color.body, lineHeight: 1.55 }}>
              <div><strong style={{ color: '#B7791F' }}>Sumber:</strong> {it.source}</div>
              <div><strong style={{ color: '#1565C0' }}>Intent:</strong> {it.intent}</div>
              <div><strong style={{ color: '#1E8449' }}>Menopang:</strong> {it.use}</div>
              {it.live && (
                <div style={{ marginTop: 6 }}>
                  {it.live.startsWith('/') && !it.live.startsWith('/grafana') && !it.live.startsWith('/kafka') ? (
                    <Link href={it.live} style={{ fontSize: 12, fontWeight: 700, color: '#1565C0' }}>
                      → {it.liveLabel ?? `lihat hidup: ${it.live}`}
                    </Link>
                  ) : (
                    <a href={it.live} style={{ fontSize: 12, fontWeight: 700, color: '#1565C0' }}>
                      → {it.liveLabel ?? it.live}
                    </a>
                  )}
                </div>
              )}
            </div>
          </Panel>
        ))}
      </div>
      <p style={{ fontSize: 11.5, color: '#94A3B8', marginTop: 18, lineHeight: 1.5 }}>
        Kapsi = verbatim naskah. Sumber tiap artefak Bab 4 menunjuk run tersegel / skrip / DB yang memproduksinya;
        angka kunci tercantum inline. Artefak yang berupa screenshot (G4.3–G4.7) menunjuk halaman live-nya langsung.
      </p>
    </div>
  )
}
