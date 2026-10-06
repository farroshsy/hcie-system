-- interactive_v2_seed.sql
-- Adds TWO new interactive study-material experiences to the HCIE ITS:
--   execution_trace  → k5_control, k2_algorithms   (EN + ID)
--   sort_race        → k8_algorithms, k5_algorithms (EN + ID)
--
-- These are ADDITIVE reading/practice materials. They ride the same integration
-- as the existing 5 interactive games: modality='interactive' with an
-- `@interactive <key>` marker in learning_materials.body, rendered by MaterialPane
-- via the INTERACTIVE_GAMES registry. No bandit / evaluation code is touched.
--
-- Idempotent: DELETE-then-INSERT by the exact ids below, wrapped in a transaction.
-- id pattern: <concept>_exectrace_<lang>_v2 / <concept>_sortrace_<lang>_v2

BEGIN;

DELETE FROM learning_materials WHERE id IN (
  'k5_control_exectrace_en_v2',    'k5_control_exectrace_id_v2',
  'k2_algorithms_exectrace_en_v2', 'k2_algorithms_exectrace_id_v2',
  'k8_algorithms_sortrace_en_v2',  'k8_algorithms_sortrace_id_v2',
  'k5_algorithms_sortrace_en_v2',  'k5_algorithms_sortrace_id_v2'
);

INSERT INTO learning_materials
  (id, concept_id, language, modality, archetype_tags, title, body, estimated_minutes, difficulty)
VALUES
  -- ── execution_trace → k5_control ──────────────────────────────────────────
  ('k5_control_exectrace_en_v2', 'k5_control', 'en', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Execution Trace: Find the Biggest Number',
   'Watch a tiny program actually run: it READS a list of numbers, PROCESSES them step by step with a loop that compares and stores, then OUTPUTS the answer. No syntax to memorize — press Run and see how a computer thinks.'
   || E'\n\n@interactive execution_trace',
   5, 0.5),

  ('k5_control_exectrace_id_v2', 'k5_control', 'id', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Jejak Program: Cari Angka Terbesar',
   'Amati sebuah program kecil berjalan sungguhan: ia MEMBACA daftar angka, MEMPROSES satu per satu dengan perulangan yang membandingkan dan menyimpan, lalu MENGELUARKAN jawabannya. Tanpa sintaks yang perlu dihafal — tekan Jalankan dan lihat cara komputer berpikir.'
   || E'\n\n@interactive execution_trace',
   5, 0.5),

  -- ── execution_trace → k2_algorithms ───────────────────────────────────────
  ('k2_algorithms_exectrace_en_v2', 'k2_algorithms', 'en', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Execution Trace: Input → Process → Output',
   'An algorithm is just steps a computer follows. Trace one live — it takes numbers in, works through them one at a time, and hands back a result. Watch the memory boxes change as the program finds the biggest number.'
   || E'\n\n@interactive execution_trace',
   5, 0.5),

  ('k2_algorithms_exectrace_id_v2', 'k2_algorithms', 'id', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Jejak Program: Masukan → Proses → Keluaran',
   'Algoritma hanyalah langkah-langkah yang diikuti komputer. Telusuri satu secara langsung — ia menerima angka, mengolahnya satu per satu, lalu memberi hasil. Amati kotak memori berubah saat program menemukan angka terbesar.'
   || E'\n\n@interactive execution_trace',
   5, 0.5),

  -- ── sort_race → k8_algorithms ─────────────────────────────────────────────
  ('k8_algorithms_sortrace_en_v2', 'k8_algorithms', 'en', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Sort Race: Two Ways, One Task',
   'The same bars, two sorting methods. Run each and watch the bars swap into order while the comparison counter climbs. Same result — but one method does noticeably less work. See efficiency, no code required.'
   || E'\n\n@interactive sort_race',
   5, 0.5),

  ('k8_algorithms_sortrace_id_v2', 'k8_algorithms', 'id', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Adu Urut: Dua Cara, Satu Tugas',
   'Batang yang sama, dua cara mengurutkan. Jalankan masing-masing dan amati batang bertukar posisi sambil penghitung perbandingan naik. Hasilnya sama — tetapi satu cara jelas bekerja lebih sedikit. Lihat efisiensi tanpa perlu menulis kode.'
   || E'\n\n@interactive sort_race',
   5, 0.5),

  -- ── sort_race → k5_algorithms ─────────────────────────────────────────────
  ('k5_algorithms_sortrace_en_v2', 'k5_algorithms', 'en', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Sort Race: Which Way Does Less Work?',
   'Two ways to solve one task: sort the bars from short to tall. Animate both, count the comparisons each needs, and discover that different algorithms can cost very different amounts of effort for the exact same job.'
   || E'\n\n@interactive sort_race',
   5, 0.5),

  ('k5_algorithms_sortrace_id_v2', 'k5_algorithms', 'id', 'interactive',
   '["vark_kinesthetic", "motiv_explorer"]'::jsonb,
   'Adu Urut: Cara Mana yang Lebih Hemat?',
   'Dua cara menyelesaikan satu tugas: urutkan batang dari pendek ke tinggi. Animasikan keduanya, hitung perbandingan yang dibutuhkan masing-masing, dan temukan bahwa algoritma berbeda bisa berbiaya sangat berbeda untuk pekerjaan yang sama persis.'
   || E'\n\n@interactive sort_race',
   5, 0.5);

COMMIT;
