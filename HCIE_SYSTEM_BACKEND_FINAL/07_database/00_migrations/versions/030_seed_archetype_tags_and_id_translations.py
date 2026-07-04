"""Tag every existing task with default archetype_tags, then seed Indonesian
sibling rows for the K-2 and K-5 gold MCQ tasks.

Revision ID: 030_seed_archetype_tags_and_id_translations
Revises: 029_add_language_archetype_and_materials
Create Date: 2026-06-02 00:00:00.000000

Two concerns folded into one migration because they share the same scan of
the ``tasks`` table:

1. **Archetype defaults by task_type.** Every existing task is tagged with a
   conservative default set derived from its task_type — a text MCQ is
   reading + logical, a code task is kinesthetic + logical + pathfinder, a
   video is visual + auditory + social, etc. Instructors can refine later
   via the dashboard. This makes the "Archetype × Concept" instructor
   analytics work on day 1 without waiting for hand-curation.

2. **Indonesian sibling rows.** The K-2 / K-5 gold MCQ tasks are
   hand-translated with cultural adaptation (units, idioms, Indonesian
   names already in use such as Rina/Budi/Siti are preserved; English
   technical terms get the canonical Indonesian rendering). Each ID sibling
   is inserted as an independent row keyed off ``{en_id}_id`` so the bandit
   can score variants independently and so an instructor can edit one
   without disturbing the other.

We do NOT translate the auto-generated media checkpoint tasks (``*_audio_q1``,
``*_video_q1``) in this migration — they're placeholder content from the
slice-4 media seed and will be re-authored properly in a follow-up. Their
generic ID translations would just be noise.
"""

from alembic import op
import sqlalchemy as sa
import json


revision = "030_seed_archetype_tags_and_id_translations"
down_revision = "029_add_language_archetype_and_materials"
branch_labels = None
depends_on = None


# ─── Archetype default tags by task_type ─────────────────────────────────────
# Conservative, multi-tag defaults. A single task often serves multiple
# learner archetypes; we record everything that's plausibly fit so the
# Archetype × Concept dashboard has signal day 1.

ARCHETYPE_DEFAULTS = {
    "multiple_choice": ["vark_reading", "motiv_logical", "behav_participant"],
    "text":            ["vark_reading", "motiv_solitary", "behav_pathfinder"],
    "code":            ["vark_kinesthetic", "motiv_logical", "behav_pathfinder"],
    "video_mcq":       ["vark_visual", "vark_auditory", "motiv_social"],
    "audio_mcq":       ["vark_auditory", "motiv_solitary"],
}


# ─── Indonesian translations (hand-authored, culturally adapted) ─────────────
# Keyed by the English task id. Each entry produces a sibling row with id
# ``{en_id}_id`` and language='id'. Where the English source already uses
# Indonesian names (Rina, Budi, Siti), those are preserved verbatim.
#
# archetype_tags override the per-task_type default when a translation has a
# stronger archetype signature than the type alone implies.

ID_TRANSLATIONS = {

    # ── k2_algorithms ────────────────────────────────────────────────────
    "k2_algo_q1": {
        "question": "Rina ingin memasak mi instan. Dia menulis: 1) Rebus air, 2) Buka bungkus, 3) Masukkan mi, 4) Tambahkan bumbu, 5) Tunggu 3 menit. Rencana berurutan ini disebut apa?",
        "choices": [
            "Resep yang bisa berubah kapan saja",
            "Algoritma — rencana langkah demi langkah yang jelas",
            "Daftar ide acak",
            "Gambar mi instan",
        ],
        "correct_answer": "Algoritma — rencana langkah demi langkah yang jelas",
        "explanation": "Algoritma adalah urutan langkah yang tepat untuk menyelesaikan masalah. Petunjuk memasak adalah contoh sehari-hari yang klasik.",
    },
    "k2_algo_q2": {
        "question": "Sebuah program punya dua langkah: Langkah 1: cetak 'Halo', Langkah 2: cetak 'Dunia'. Jika urutannya ditukar, apa yang berubah?",
        "choices": [
            "Tidak ada yang berubah",
            "'Dunia' tercetak sebelum 'Halo'",
            "Program error",
            "'Halo Dunia' tercetak di satu baris",
        ],
        "correct_answer": "'Dunia' tercetak sebelum 'Halo'",
        "explanation": "Pada algoritma, urutan itu penting. Membalik langkah berarti membalik hasilnya.",
    },
    "k2_algo_q3": {
        "question": "Manakah contoh algoritma yang paling tepat?",
        "choices": [
            "Suatu hari ada robot bernama Budi.",
            "Langkah 1: Ambil bola. Langkah 2: Jalan ke keranjang. Langkah 3: Lepaskan bola.",
            "Gambar berwarna sebuah taman bermain.",
            "Daftar semua anak di kelas.",
        ],
        "correct_answer": "Langkah 1: Ambil bola. Langkah 2: Jalan ke keranjang. Langkah 3: Lepaskan bola.",
        "explanation": "Algoritma punya langkah-langkah jelas dan berurutan menuju suatu tujuan. Cerita dan gambar bukanlah algoritma.",
    },

    # ── k5_algorithms ────────────────────────────────────────────────────
    "k5_algo_q1": {
        "question": "Sebuah loop menjalankan instruksi 'tambahkan 2 ke total' tepat 5 kali, dimulai dari total = 0. Berapa nilai akhir total?",
        "choices": ["5", "7", "10", "2"],
        "correct_answer": "10",
        "explanation": "Setiap iterasi menambah 2: 0→2→4→6→8→10. Setelah 5 iterasi totalnya 10.",
    },
    "k5_algo_q2": {
        "question": "Budi punya daftar 100 nama yang sudah terurut. Dia ingin mencari 'Zainul'. Pendekatan mana yang lebih cepat?",
        "choices": [
            "Periksa setiap nama dari awal (pencarian linier)",
            "Buka daftar di tengah, lalu persempit (pencarian biner)",
            "Acak dulu daftarnya, baru cari",
            "Minta teman untuk mencarikan",
        ],
        "correct_answer": "Buka daftar di tengah, lalu persempit (pencarian biner)",
        "explanation": "Pencarian biner berkompleksitas O(log n) — jauh lebih efisien dari O(n) pencarian linier pada data terurut.",
    },
    "k5_algo_q3": {
        "question": "Sebuah program harus menyapa 50 pengguna berbeda dengan namanya. Rancangan mana yang terbaik?",
        "choices": [
            "Tulis 50 baris 'cetak nama' terpisah",
            "Gunakan loop yang mengulang sapaan untuk setiap nama di daftar",
            "Cetak semua nama sekaligus dengan satu perintah cetak",
            "Minta pengguna mengetik setiap nama 50 kali",
        ],
        "correct_answer": "Gunakan loop yang mengulang sapaan untuk setiap nama di daftar",
        "explanation": "Loop menghindari kode berulang — penting untuk memproses kumpulan data.",
    },

    # ── k8_algorithms ────────────────────────────────────────────────────
    "k8_algo_q1": {
        "question": "Algoritma A selalu memakan 100 langkah berapapun ukuran input. Algoritma B memakan n langkah untuk input ukuran n. Untuk n = 50, mana yang lebih cepat?",
        "choices": [
            "Algoritma A (100 langkah vs 50)",
            "Algoritma B (50 langkah vs 100)",
            "Selalu sama",
            "Tidak bisa ditentukan",
        ],
        "correct_answer": "Algoritma B (50 langkah vs 100)",
        "explanation": "Algoritma B butuh n=50 langkah; Algoritma A selalu 100. B lebih cepat untuk n kecil, tapi A menang untuk n besar.",
    },
    "k8_algo_q2": {
        "question": "Sebuah loop bersarang memeriksa setiap pasangan item pada daftar n item. Bagaimana jumlah operasinya tumbuh terhadap n?",
        "choices": [
            "Linier (n)",
            "Kuadratik (n²)",
            "Logaritmik (log n)",
            "Konstan (1)",
        ],
        "correct_answer": "Kuadratik (n²)",
        "explanation": "Untuk setiap n item, loop dalam memeriksa n item: n × n = n² total perbandingan.",
    },
    "k8_algo_q3": {
        "question": "Sebuah algoritma berfungsi sempurna untuk 999 kasus uji, tapi gagal saat inputnya kosong. Apa istilahnya?",
        "choices": [
            "Runtime error",
            "Bug edge case",
            "Compile error",
            "Memory overflow",
        ],
        "correct_answer": "Bug edge case",
        "explanation": "Edge case (input kosong, nilai maksimum, kondisi batas) harus selalu ditangani secara eksplisit.",
    },

    # ── k2_control ───────────────────────────────────────────────────────
    "k2_ctrl_q1": {
        "question": "Kamu perlu menyiram 10 tanaman, dengan tindakan yang persis sama setiap kali. Pendekatan terbaik?",
        "choices": [
            "Tulis 10 langkah 'siram tanaman' terpisah",
            "Gunakan loop yang mengulang 'siram tanaman' 10 kali",
            "Siram hanya tanaman pertama",
            "Tulis cerita tentang menyiram tanaman",
        ],
        "correct_answer": "Gunakan loop yang mengulang 'siram tanaman' 10 kali",
        "explanation": "Loop menghilangkan pengulangan untuk tindakan identik berulang.",
    },
    "k2_ctrl_q2": {
        "question": "Sebuah program mengecek: 'JIKA hujan MAKA bawa payung'. Jenis instruksi apa ini?",
        "choices": [
            "Loop",
            "Kondisional (if-then)",
            "Variabel",
            "Fungsi",
        ],
        "correct_answer": "Kondisional (if-then)",
        "explanation": "Instruksi JIKA-MAKA mengeksekusi tindakan hanya saat kondisinya benar.",
    },
    "k2_ctrl_q3": {
        "question": "Pada instruksi 'ULANGI 3 KALI: ucapkan halo → lambaikan tangan', langkah mana yang ada di dalam loop?",
        "choices": [
            "Hanya 'ucapkan halo'",
            "Hanya 'lambaikan tangan'",
            "Keduanya 'ucapkan halo' dan 'lambaikan tangan'",
            "Tidak ada — badan loop kosong",
        ],
        "correct_answer": "Keduanya 'ucapkan halo' dan 'lambaikan tangan'",
        "explanation": "Semua yang menjorok di bawah ULANGI adalah badan loop — semua langkah berjalan di setiap iterasi.",
    },

    # ── k5_control ───────────────────────────────────────────────────────
    "k5_ctrl_q1": {
        "question": "Sebuah while loop berjalan selama score < 10. Mulai dari score = 7, berapa kali 'score = score + 1' dieksekusi?",
        "choices": ["7", "3", "10", "1"],
        "correct_answer": "3",
        "explanation": "score berubah 7→8→9→10. Loop berjalan saat 7, 8, 9 (3 kali), lalu score = 10 gagal memenuhi kondisi.",
    },
    "k5_ctrl_q2": {
        "question": "JIKA score >= 75 MAKA cetak 'Lulus' KALAU TIDAK cetak 'Tidak Lulus'. Jika score = 60, apa yang tercetak?",
        "choices": ["Lulus", "Tidak Lulus", "Tidak ada", "Lulus dan Tidak Lulus keduanya"],
        "correct_answer": "Tidak Lulus",
        "explanation": "60 tidak ≥ 75, jadi cabang KALAU TIDAK berjalan: 'Tidak Lulus' tercetak.",
    },
    "k5_ctrl_q3": {
        "question": "Jenis loop mana yang paling cocok ketika kamu sudah tahu persis berapa kali harus diulang?",
        "choices": [
            "While loop",
            "For loop",
            "Repeat-until loop",
            "Fungsi rekursif",
        ],
        "correct_answer": "For loop",
        "explanation": "For loop dirancang untuk jumlah iterasi yang sudah diketahui dan tetap.",
    },

    # ── k8_control ───────────────────────────────────────────────────────
    "k8_ctrl_q1": {
        "question": "Loop luar berjalan 4 kali; loop dalam berjalan 3 kali untuk setiap iterasi luar. Berapa total eksekusi loop dalam?",
        "choices": ["7", "12", "4", "3"],
        "correct_answer": "12",
        "explanation": "4 × 3 = 12. Loop bersarang mengalikan jumlah iterasinya.",
    },
    "k8_ctrl_q2": {
        "question": "Sebuah kondisi: (umur >= 13) DAN (punyaIzin = True). Untuk umur = 15 dan punyaIzin = False, hasilnya apa?",
        "choices": ["True", "False", "Error", "Tergantung bahasanya"],
        "correct_answer": "False",
        "explanation": "DAN mensyaratkan kedua kondisi True. punyaIzin False, jadi seluruh kondisinya False.",
    },
    "k8_ctrl_q3": {
        "question": "Pada program berbasis event, kapan kode di dalam handler 'onClick' dijalankan?",
        "choices": [
            "Saat program mulai",
            "Setiap detik otomatis",
            "Hanya saat pengguna mengklik elemen",
            "Hanya saat fungsi lain memanggilnya",
        ],
        "correct_answer": "Hanya saat pengguna mengklik elemen",
        "explanation": "Kode berbasis event berjalan sebagai respons terhadap event tertentu, bukan terus-menerus.",
    },

    # ── k2_variables ─────────────────────────────────────────────────────
    "k2_var_q1": {
        "question": "Dalam sebuah game, 'nyawa = 3' berarti pemain punya 3 nyawa. Jika pemain kehilangan satu, nyawa jadi 2. Apa itu 'nyawa' dalam pemrograman?",
        "choices": [
            "Fungsi",
            "Variabel yang menyimpan nilai yang bisa berubah",
            "Angka tetap yang tidak pernah berubah",
            "Jenis loop",
        ],
        "correct_answer": "Variabel yang menyimpan nilai yang bisa berubah",
        "explanation": "Variabel adalah wadah bernama yang nilainya bisa berubah selama program berjalan.",
    },
    "k2_var_q2": {
        "question": "x = 5 artinya apa dalam pemrograman?",
        "choices": [
            "'x' sama dengan 5 seperti di matematika — kedua sisi setara",
            "'Simpan nilai 5 ke variabel bernama x'",
            "'Cek apakah x dan 5 sama'",
            "'Kalikan x dengan 5'",
        ],
        "correct_answer": "'Simpan nilai 5 ke variabel bernama x'",
        "explanation": "Penugasan (=) menyimpan nilai. Arahnya satu arah: nilai MASUK ke variabel.",
    },

    # ── k5_variables ─────────────────────────────────────────────────────
    "k5_var_q1": {
        "question": "Tipe data mana yang tepat untuk menyimpan rata-rata nilai siswa seperti 85.5?",
        "choices": [
            "Integer (bilangan bulat)",
            "Float (bilangan desimal)",
            "Boolean (benar/salah)",
            "String (teks)",
        ],
        "correct_answer": "Float (bilangan desimal)",
        "explanation": "Float (atau double) merepresentasikan angka dengan koma. 85.5 tidak bisa disimpan sebagai integer.",
    },
    "k5_var_q2": {
        "question": "x = 10; x = x + 3; cetak(x). Apa yang tercetak?",
        "choices": ["10", "3", "13", "x + 3"],
        "correct_answer": "13",
        "explanation": "x mulai dari 10. x = x + 3 menghitung 10 + 3 = 13 dan menyimpannya kembali ke x.",
    },

    # ── k8_variables ─────────────────────────────────────────────────────
    "k8_var_q1": {
        "question": "Variabel yang dideklarasikan di dalam sebuah fungsi disebut apa, dan bisa diakses dimana?",
        "choices": [
            "Variabel global — bisa diakses dimana saja",
            "Variabel lokal — hanya bisa diakses di dalam fungsi tersebut",
            "Konstanta — nilainya tidak pernah berubah",
            "Parameter — hanya diteruskan saat memanggil fungsi",
        ],
        "correct_answer": "Variabel lokal — hanya bisa diakses di dalam fungsi tersebut",
        "explanation": "Variabel lokal cakupannya hanya di blok (fungsi) tempat ia dideklarasikan.",
    },
    "k8_var_q2": {
        "question": "nama = ['Adi', 'Budi', 'Citra']. Apa isi nama[1]?",
        "choices": ["Adi", "Budi", "Citra", "Index error"],
        "correct_answer": "Budi",
        "explanation": "Indeks list mulai dari 0. Indeks 1 mengembalikan elemen kedua: 'Budi'.",
    },

    # ── k2_modularity ────────────────────────────────────────────────────
    "k2_mod_q1": {
        "question": "Untuk membersihkan kamar kamu harus: rapikan meja, susun buku, sapu lantai. Ini contoh dari:",
        "choices": [
            "Mengompilasi kode",
            "Dekomposisi — memecah tugas besar menjadi langkah kecil",
            "Protokol jaringan",
            "Variabel",
        ],
        "correct_answer": "Dekomposisi — memecah tugas besar menjadi langkah kecil",
        "explanation": "Dekomposisi adalah keterampilan komputasional kunci: memecah masalah besar menjadi submasalah yang dapat dikelola.",
    },
    "k2_mod_q2": {
        "question": "Kamu mengajari robot untuk 'lambaikan halo'. Lalu kamu menggunakan 'lambaikan halo' 5 kali tanpa menulis ulang langkahnya. Konsep apa ini?",
        "choices": [
            "Menggunakan kembali prosedur bernama",
            "Loop",
            "Kondisional",
            "Penyimpanan data",
        ],
        "correct_answer": "Menggunakan kembali prosedur bernama",
        "explanation": "Mendefinisikan prosedur bernama sekali dan menggunakannya kembali adalah dasar dari modularitas.",
    },

    # ── k5_modularity ────────────────────────────────────────────────────
    "k5_mod_q1": {
        "question": "def greet(name): print('Halo', name). Saat kamu memanggil greet('Siti'), apa yang tercetak?",
        "choices": ["Halo name", "Halo Siti", "Halo", "Error"],
        "correct_answer": "Halo Siti",
        "explanation": "Parameter 'name' menerima nilai 'Siti' saat fungsi dipanggil.",
    },
    "k5_mod_q2": {
        "question": "def kuadrat(n): return n * n. Apa hasil kuadrat(4)?",
        "choices": ["4", "8", "16", "n*n"],
        "correct_answer": "16",
        "explanation": "Fungsi mengembalikan n*n = 4*4 = 16. Nilai kembali memungkinkan fungsi menghasilkan hasil.",
    },

    # ── k8_modularity ────────────────────────────────────────────────────
    "k8_mod_q1": {
        "question": "Programmu memiliki kode identik di tiga tempat berbeda. Pendekatan refaktor terbaik?",
        "choices": [
            "Biarkan tiga salinan — lebih jelas",
            "Ekstrak kode menjadi satu fungsi dan panggil dari masing-masing tempat",
            "Hapus dua salinan dan simpan satu",
            "Tambahkan komentar yang menjelaskan duplikasi",
        ],
        "correct_answer": "Ekstrak kode menjadi satu fungsi dan panggil dari masing-masing tempat",
        "explanation": "DRY (Don't Repeat Yourself): memusatkan kode mengurangi bug dan biaya pemeliharaan.",
    },

    # ── k2_computing_systems_devices ─────────────────────────────────────
    "k2_cs_q1": {
        "question": "Mana yang merupakan contoh perangkat lunak (software)?",
        "choices": [
            "Keyboard yang kamu ketik",
            "Layar yang kamu lihat",
            "Aplikasi kalkulator di HP",
            "Kabel USB yang kamu pasang",
        ],
        "correct_answer": "Aplikasi kalkulator di HP",
        "explanation": "Perangkat lunak adalah program — instruksi yang tersimpan secara digital. Perangkat keras bersifat fisik.",
    },
    "k2_cs_q2": {
        "question": "Saat kamu menekan tombol keyboard, ia mengirim informasi ke komputer. Keyboard adalah perangkat:",
        "choices": [
            "Output",
            "Input",
            "Penyimpanan",
            "Pemrosesan",
        ],
        "correct_answer": "Input",
        "explanation": "Perangkat input mengirim data ke komputer. Perangkat output (seperti monitor) menerima data darinya.",
    },

    # ── k5_computing_systems_devices ─────────────────────────────────────
    "k5_cs_q1": {
        "question": "Apa fungsi utama CPU (Central Processing Unit)?",
        "choices": [
            "Menyimpan file secara permanen",
            "Menampilkan gambar di layar",
            "Mengeksekusi instruksi program — 'otak' komputer",
            "Menghubungkan komputer ke internet",
        ],
        "correct_answer": "Mengeksekusi instruksi program — 'otak' komputer",
        "explanation": "CPU mengambil, mendekode, dan mengeksekusi instruksi — ia adalah inti komputasi.",
    },
    "k5_cs_q2": {
        "question": "Saat kamu menutup dokumen tanpa menyimpan, pekerjaanmu hilang. Ini karena ia hanya ada di:",
        "choices": [
            "Hard drive (penyimpanan permanen)",
            "RAM (memori sementara)",
            "Cache CPU",
            "Kartu grafis",
        ],
        "correct_answer": "RAM (memori sementara)",
        "explanation": "RAM bersifat volatil — kehilangan data saat daya mati. Penyimpanan permanen (SSD/HDD) menyimpan data.",
    },

    # ── k2_networks_communication ────────────────────────────────────────
    "k2_net_q1": {
        "question": "Tiga komputer di kelas terhubung agar bisa berbagi file. Apa ini disebut?",
        "choices": [
            "Basis data",
            "Loop",
            "Jaringan komputer",
            "Sistem operasi",
        ],
        "correct_answer": "Jaringan komputer",
        "explanation": "Jaringan adalah dua atau lebih perangkat yang terhubung yang bisa berkomunikasi dan berbagi sumber daya.",
    },
    "k2_net_q2": {
        "question": "Saat kamu mengunjungi sebuah situs web, komputermu berkomunikasi dengan komputer lain yang jauh. Apa yang memungkinkannya?",
        "choices": [
            "Keyboard mengirim permintaan langsung",
            "Internet menghubungkan komputer di seluruh dunia agar bisa bertukar data",
            "Layar mengunduh situs web",
            "RAM menyimpan situs web secara permanen",
        ],
        "correct_answer": "Internet menghubungkan komputer di seluruh dunia agar bisa bertukar data",
        "explanation": "Internet adalah jaringan global dari jaringan-jaringan yang memungkinkan komunikasi data di seluruh dunia.",
    },

    # ── k5_networks_communication ────────────────────────────────────────
    "k5_net_q1": {
        "question": "HTTP adalah seperangkat aturan yang diikuti browser dan server untuk berbagi halaman web. HTTP adalah contoh dari:",
        "choices": [
            "Bahasa pemrograman",
            "Protokol jaringan",
            "Basis data",
            "Komponen perangkat keras",
        ],
        "correct_answer": "Protokol jaringan",
        "explanation": "Protokol adalah aturan komunikasi yang disepakati. HTTP mendefinisikan bagaimana data web diminta dan dilayani.",
    },
    "k5_net_q2": {
        "question": "Mengapa internet memecah file besar menjadi 'paket' kecil sebelum mengirimnya?",
        "choices": [
            "Karena paket lebih sulit diretas",
            "Untuk routing efisien — setiap paket bisa mengambil jalur berbeda",
            "Karena komputer tidak bisa menangani file besar",
            "Untuk kompresi otomatis",
        ],
        "correct_answer": "Untuk routing efisien — setiap paket bisa mengambil jalur berbeda",
        "explanation": "Packet switching memungkinkan penggunaan jalur jaringan yang efisien dan ketahanan terhadap kegagalan.",
    },

    # ── k2_data_collection ───────────────────────────────────────────────
    "k2_data_q1": {
        "question": "Kelas kamu ingin tahu buah mana yang paling populer. Bagaimana cara mengumpulkan datanya?",
        "choices": [
            "Tanya satu siswa dan tebak sisanya",
            "Tanya setiap siswa buah favoritnya dan catat jawabannya",
            "Pilih buah yang paling kamu suka",
            "Cari di internet",
        ],
        "correct_answer": "Tanya setiap siswa buah favoritnya dan catat jawabannya",
        "explanation": "Pengumpulan data yang baik berarti mengumpulkan tanggapan dari semua subjek relevan secara sistematis.",
    },
    "k2_data_q2": {
        "question": "Grafik batang menunjukkan: Mangga = 8, Pisang = 5, Apel = 3. Buah mana yang paling populer?",
        "choices": ["Apel", "Pisang", "Mangga", "Semua sama"],
        "correct_answer": "Mangga",
        "explanation": "Mangga punya batang tertinggi (8 siswa), jadi paling populer.",
    },

    # ── k5_data_collection ───────────────────────────────────────────────
    "k5_data_q1": {
        "question": "Pembacaan suhu 7 hari: 28, 30, 29, 31, 30, 32, 31. Apa trennya?",
        "choices": [
            "Suhu turun",
            "Suhu cenderung naik",
            "Suhu konstan",
            "Tidak ada pola",
        ],
        "correct_answer": "Suhu cenderung naik",
        "explanation": "Meskipun fluktuasi harian, urutannya bergerak dari 28 ke 31 — tren naik.",
    },
    "k5_data_q2": {
        "question": "Data menunjukkan siswa yang sarapan punya nilai tes lebih tinggi. Apa yang bisa disimpulkan?",
        "choices": [
            "Sarapan langsung menyebabkan nilai lebih tinggi",
            "Ada korelasi, tapi butuh bukti lebih untuk membuktikan sebab-akibat",
            "Nilai tes menyebabkan siswa sarapan",
            "Datanya pasti salah",
        ],
        "correct_answer": "Ada korelasi, tapi butuh bukti lebih untuk membuktikan sebab-akibat",
        "explanation": "Korelasi berarti dua hal bergerak bersama. Sebab-akibat butuh eksperimen terkendali untuk dikonfirmasi.",
    },

    # ── k2_culture ───────────────────────────────────────────────────────
    "k2_dsi_q1": {
        "question": "Smartphone membantu orang berkomunikasi cepat, tapi sebagian orang terlalu sering memakainya dan mengabaikan orang sekitar. Ini menunjukkan teknologi bisa memberi:",
        "choices": [
            "Hanya efek positif",
            "Hanya efek negatif",
            "Efek positif dan negatif tergantung cara penggunaannya",
            "Tidak ada efek pada hidup sehari-hari",
        ],
        "correct_answer": "Efek positif dan negatif tergantung cara penggunaannya",
        "explanation": "Teknologi adalah alat — dampaknya tergantung bagaimana, kapan, dan seberapa banyak ia digunakan.",
    },
    "k2_dsi_q2": {
        "question": "Temanmu meminta kamu membagikan alamat rumahmu di postingan media sosial publik. Apa yang harus kamu lakukan?",
        "choices": [
            "Bagikan karena kamu percaya temanmu",
            "Tolak — informasi pribadi seperti alamat tidak boleh dibagikan publik",
            "Bagikan setengah alamat saja",
            "Tanya orang tua setelah memposting",
        ],
        "correct_answer": "Tolak — informasi pribadi seperti alamat tidak boleh dibagikan publik",
        "explanation": "Informasi pribadi yang dibagikan publik bisa dilihat orang asing dan disalahgunakan.",
    },
}


def upgrade():
    bind = op.get_bind()

    # ── Step 1: Tag all existing tasks with per-task_type archetype defaults
    # Done via individual UPDATEs keyed on task_type so the SQL is short and
    # we can run it idempotently.
    for task_type, tags in ARCHETYPE_DEFAULTS.items():
        bind.execute(
            sa.text(
                "UPDATE tasks SET archetype_tags = CAST(:tags AS jsonb) "
                "WHERE task_type = :ttype AND archetype_tags = '[]'::jsonb"
            ),
            {"tags": json.dumps(tags), "ttype": task_type},
        )

    # ── Step 2: Insert Indonesian sibling rows for hand-translated tasks ──
    # We mirror difficulty, cognitive_level, concept_type, and task_type from
    # the EN source row so the bandit treats the ID variant as a peer arm.
    for en_id, translation in ID_TRANSLATIONS.items():
        src = bind.execute(
            sa.text(
                "SELECT concept_id, concept_type, difficulty, cognitive_level, "
                "task_type, content, solution, hints, metadata, archetype_tags "
                "FROM tasks WHERE id = :id"
            ),
            {"id": en_id},
        ).mappings().first()

        if src is None:
            # Source task missing — skip rather than fail the migration; the
            # ID seed catches up whenever the EN row is added.
            continue

        id_task_id = f"{en_id}_id"

        # Skip if already seeded (idempotent re-run).
        exists = bind.execute(
            sa.text("SELECT 1 FROM tasks WHERE id = :id"), {"id": id_task_id}
        ).first()
        if exists:
            continue

        new_content = {
            "question": translation["question"],
            "choices": translation["choices"],
            "correct_answer": translation["correct_answer"],
            "explanation": translation["explanation"],
        }

        bind.execute(
            sa.text(
                """
                INSERT INTO tasks (
                    id, concept_id, concept_type, difficulty, cognitive_level,
                    task_type, content, solution, hints, metadata,
                    language, archetype_tags
                ) VALUES (
                    :id, :concept_id, :concept_type, :difficulty, :cognitive_level,
                    :task_type, CAST(:content AS jsonb),
                    CAST(:solution AS jsonb), CAST(:hints AS jsonb),
                    CAST(:metadata AS jsonb),
                    'id', CAST(:archetype_tags AS jsonb)
                )
                """
            ),
            {
                "id": id_task_id,
                "concept_id": src["concept_id"],
                "concept_type": src["concept_type"],
                "difficulty": src["difficulty"],
                "cognitive_level": src["cognitive_level"],
                "task_type": src["task_type"],
                "content": json.dumps(new_content),
                "solution": json.dumps(src["solution"] or {}),
                "hints": json.dumps(src["hints"] or []),
                "metadata": json.dumps(
                    {
                        **(src["metadata"] or {}),
                        "translated_from": en_id,
                        "cultural_adaptation": "id_ID",
                    }
                ),
                "archetype_tags": json.dumps(src["archetype_tags"] or ["vark_reading", "motiv_logical"]),
            },
        )


def downgrade():
    bind = op.get_bind()
    # Drop ID sibling rows we inserted.
    for en_id in ID_TRANSLATIONS:
        bind.execute(
            sa.text("DELETE FROM tasks WHERE id = :id"),
            {"id": f"{en_id}_id"},
        )
    # Clear archetype tags we set as defaults.
    bind.execute(sa.text("UPDATE tasks SET archetype_tags = '[]'::jsonb"))
