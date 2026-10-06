BEGIN;
DELETE FROM learning_materials WHERE concept_id = 'k12_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k12_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k12_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_control' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_modularity' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_modularity' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_program_development' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_variables' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_variables' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_control' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_modularity' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_modularity' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_variables' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_variables' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_control' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_modularity' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_modularity' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_variables' AND language = 'en';
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_reading_intro_en_v2', 'k12_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Algorithms That Stay Fast When the Data Gets Huge', 'Every time you search your camera roll, get instant autocomplete, or ask a maps app for the fastest route, an algorithm is answering in milliseconds over millions of data items. The difference between an app that feels instant and one that freezes is rarely the hardware — it is almost always the design of the algorithm.

## Judge an algorithm by how it scales

By now you can write algorithms that work. The engineering question at this level is different: **how does the cost grow as the input grows?** We measure cost as the number of basic steps, and we focus on the **worst case** — the input of size n that forces the most work — because the worst case is the only performance guarantee you can actually promise.

Three growth rates cover a huge amount of real software:

- **O(n)** — double the input, double the work (a single scan).
- **O(n²)** — double the input, quadruple the work (nested loops over the same data).
- **O(log n)** — double the input, add only *one* extra step (repeated halving).

Designing at this level means sketching a solution in pseudocode, finding its worst case, then redesigning toward a slower-growing curve — the practice described by the CSTA 3A-AP-10 standard.

### Worked example: is this username taken?

A game server stores 1,000,000 usernames in a **sorted** array. A linear scan might check all 1,000,000 entries in the worst case (the name isn''t there). Binary search exploits the sorted order:

```
low = 0
high = n - 1
while low <= high:
    mid = (low + high) / 2   # integer division
    if names[mid] == target:
        return FOUND
    else if names[mid] < target:
        low = mid + 1
    else:
        high = mid - 1
return NOT_FOUND
```

Every pass halves the remaining range: 1,000,000 → 500,000 → 250,000 → ... → 1. Since 2²⁰ ≈ 1,000,000, the worst case is about 20 comparisons instead of 1,000,000. The tradeoff: the array must be kept sorted, which makes inserting new names more expensive. Fast lookups are bought with slower insertions — a classic engineering trade.

::: check
Q: In the worst case, about how many comparisons does binary search make on a sorted list of 1,000,000,000 items?
A: About 30 — each comparison halves the remaining range, and 2³⁰ is roughly one billion.
Q: Why do engineers measure the worst case instead of the best case?
A: The best case can be luck (the target happens to be first). The worst case is a guarantee that holds for every possible input, which is what you must design and promise around.
:::

Next, the deeper dive takes a genuinely slow O(n²) algorithm apart and rebuilds it into a one-pass O(n) design — and exposes the misconception that trips up most beginners.', NULL, NULL, 5, 0.3, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_diagram_en_v2', 'k12_algorithms', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Doubling Test: Reading Growth Rates at a Glance', 'The fastest way to feel what complexity classes mean is a doubling experiment: double the input size and watch what happens to the work. This diagram runs that test on three classic algorithms.

```
     DOUBLING TEST:  n = 1,000  ==>  n = 2,000
                        |
                        v
+-------------------+----------------------------+
| O(log n)          |  ~10 steps --> ~11 steps   |
| binary search     |  work: +1 step             |
+-------------------+----------------------------+
| O(n)              |  1,000 --> 2,000           |
| single scan       |  work: x2                  |
+-------------------+----------------------------+
| O(n^2)            |  ~500,000 --> ~2,000,000   |
| compare all pairs |  work: x4                  |
+-------------------+----------------------------+
```

Legend

- `==>` : the input size n doubles
- `-->` : how that algorithm''s step count changes
- `O(...)` : worst-case complexity class (growth rate)
- `+1 / x2 / x4` : how much the total work increases
- Each box row : one algorithm and its cost behavior

How to read it

1. Start at the top line: the same doubling experiment is applied to all three algorithms below.
2. Row 1: binary search halves its range each step, so doubling n costs only one extra step.
3. Row 2: a single scan grows in lockstep with the input — double the data, double the work.
4. Row 3: comparing all pairs quadruples, since n = 1,000 gives about 500,000 pairs but n = 2,000 gives about 2,000,000.
5. The reading rule: whatever happens to the work when n doubles identifies the complexity class.

::: tip
You can run the doubling test on real code: time your program on an input of size n, then on 2n. If the time roughly quadruples, suspect a hidden nested loop — an O(n²) core — and hunt for a data structure or a pre-sort that removes it.
:::', NULL, NULL, 3, 0.4, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_audio_en_v2', 'k12_algorithms', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Why Engineers Plan for the Worst Case', NULL, NULL, 'Here''s a situation every programmer eventually faces. You write a program, you test it on a small example, it works, and it''s fast. Then real users show up with real data, and the same program grinds to a halt. Nothing is broken. The algorithm just doesn''t scale.

At this level, designing algorithms means asking a sharper question than "does it work?" The question is: how does the amount of work grow as the input grows? And engineers are pessimists about it. We plan for the worst case, the input arrangement that forces the most steps, because that''s the only guarantee we can promise users.

Let''s make it concrete. Suppose your playlist app needs to check whether a playlist contains any duplicate songs. The obvious algorithm compares every song with every other song, using two nested loops. For a playlist of ten songs, that''s about forty-five comparisons. No problem. But for a library of one hundred thousand songs, comparing every pair means roughly five billion comparisons. Double the library and the work quadruples, because the work grows with the square of the input size. That squared growth is the real enemy, not the computer''s speed.

Now redesign it. Walk through the songs once, and keep the ones you''ve already seen in a data structure that can answer "have I seen this?" almost instantly, like a hash set. For each song, ask if it''s already in the set. If yes, you''ve found a duplicate. If no, add it and move on. One pass. One hundred thousand songs now means about one hundred thousand steps instead of five billion. You paid for that speed with extra memory for the set, and that''s the trade-off. Optimization is rarely free. You''re trading one resource, memory, for another resource, time.

That''s the craft: find the worst case, name the growth rate, then redesign, often with a smarter data structure, to bend the curve down.

So here''s your recap question. If an algorithm''s running time roughly quadruples every time you double the input size, what growth rate does it have, and why? The answer: it grows with the square of the input, order n squared, because doubling n makes n squared four times bigger. When you can hear that pattern in an algorithm''s behavior, you''re starting to think like an engineer.', 4, 0.45, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_reading_deep_en_v2', 'k12_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'From Brute Force to One Pass: Optimizing Worst-Case Cost', 'Quick recap: an algorithm''s quality is measured by how its worst-case step count grows with input size n — and optimization means redesigning for a slower-growing curve, not shaving a line of code.

## Worked example: two-sum, from O(n²) to O(n)

**Problem.** You have a gift card worth exactly T and a list of n item prices. Decide whether two different items use up the card exactly.

**Design 1 — brute force.** Check every pair:

```
for i from 0 to n-2:
    for j from i+1 to n-1:
        if price[i] + price[j] == T:
            return (i, j)
return NONE
```

Worst case: no valid pair exists, so all n(n-1)/2 pairs get checked — that is O(n²). For n = 100,000 prices, that is about five billion comparisons.

**The key insight.** While scanning, a price p is useful exactly when its partner T − p has already been seen. So remember what we have seen in a **hash set**, which answers "is x in here?" in roughly constant time.

**Design 2 — one pass.**

```
seen = empty hash set
for each p in prices:
    if (T - p) is in seen:
        return FOUND
    add p to seen
return NONE
```

**Trace** with prices = [4, 9, 7, 2] and T = 11:

1. p = 4: is 7 in {}? No. Add 4 → seen = {4}
2. p = 9: is 2 in {4}? No. Add 9 → seen = {4, 9}
3. p = 7: is 4 in {4, 9}? Yes → FOUND (4 + 7 = 11)

One scan: O(n) time, O(n) extra memory. Check the edge cases before trusting it: an empty list falls through to NONE; a no-solution input finishes the loop safely; duplicates work too (T = 8 with two 4s — the second 4 finds the first one in the set). We bought speed by spending memory. Optimization is a trade, not a free upgrade.

## The misconception that trips people up

::: misconception
Wrong belief: "Big-O tells you how many seconds an algorithm takes, so the O(n) version is always faster than the O(n²) one."
Correction: Big-O describes how the step count *grows* as n increases; it deliberately ignores constant factors. On a 20-item list, brute-force two-sum may actually beat the hash-set version, because hashing has setup overhead. The real guarantee is about scale: beyond some input size, the O(n) design wins on every input — including the worst case — and the gap then widens without limit.
:::

## Where this leads

This is the final stop in this curriculum''s algorithms track, but the reasoning transfers everywhere code has to survive real workloads. College courses on data structures and algorithms begin exactly here, with rigorous arguments about growth rates. Coding interviews are largely this one move — "here''s a brute force; now bend the curve." And production engineering, from database indexes to pathfinding in games, is a long series of the same three questions: what is the worst case, what is its growth rate, and what resource can I trade to lower it?

::: check
Q: Brute-force two-sum runs on n = 2,000 prices that contain no valid pair. About how many comparisons happen, and what complexity does that match?
A: n(n-1)/2 = 1,999,000 — about two million comparisons, matching the O(n²) worst case.
Q: An algorithm sorts its input in about n log n steps, then does one n-step scan. What is its worst-case complexity?
A: O(n log n). The n log n term dominates as n grows, so the lower-order n term is dropped.
:::', NULL, NULL, 8, 0.6, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_reading_intro_id_v2', 'k12_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Merancang Algoritma yang Tetap Cepat Saat Data Membesar', 'Saat kamu mengetik nama teman di kolom pencarian sebuah aplikasi, hasilnya muncul dalam sekejap — padahal penggunanya jutaan. Itu bukan sihir server, melainkan hasil rancangan algoritma yang jumlah langkahnya nyaris tidak bertambah walaupun datanya meledak. Di tingkat ini, tantanganmu bukan lagi sekadar menulis algoritma yang *benar*, tetapi algoritma yang tetap masuk akal pada **kasus terburuk**.

## Ide besar: ukur pertumbuhan langkah, bukan detik

Komputer yang berbeda punya kecepatan yang berbeda, jadi mengukur efisiensi dengan stopwatch tidak adil. Ilmuwan komputer mengukurnya dengan cara lain: hitung berapa banyak **langkah** yang dilakukan algoritma sebagai fungsi dari ukuran data, biasanya dilambangkan *n*. Yang paling penting adalah **kasus terburuk** (worst case): skenario input yang memaksa algoritma bekerja paling keras. Mengapa? Karena kasus terburuk adalah jaminan — batas atas yang bisa kamu janjikan kepada pengguna. Kebiasaan menganalisis lalu menyempurnakan algoritma seperti ini sejalan dengan standar AP-K12-3.

Pencarian sekuensial (memeriksa satu per satu) pada daftar berukuran *n* butuh sampai *n* langkah di kasus terburuk — target ada di posisi terakhir, atau tidak ada sama sekali. Bisakah lebih baik? Bisa, asalkan datanya **terurut**.

### Contoh kecil: pencarian biner

Perhatikan larik terurut berisi 8 angka dan target 31:

```
A = [3, 8, 12, 17, 23, 31, 40, 55]

fungsi cariBiner(A, target):
    kiri  <- 0
    kanan <- panjang(A) - 1
    selama kiri <= kanan:
        tengah <- (kiri + kanan) div 2
        jika A[tengah] = target: kembalikan tengah
        jika A[tengah] < target: kiri  <- tengah + 1
        jika tidak:              kanan <- tengah - 1
    kembalikan -1
```

Jalankan sendiri:

1. kiri = 0, kanan = 7, tengah = 3. A[3] = 17 dan 17 < 31, jadi kiri = 4.
2. kiri = 4, kanan = 7, tengah = 5. A[5] = 31 — ketemu dalam 2 langkah!

Setiap perbandingan membuang **setengah** sisa data. Kasus terburuknya hanya sekitar log2(n) langkah: untuk n = 1.000.000, cukup kira-kira 20 perbandingan, bukan sejuta. Itulah kekuatan memilih algoritma yang tepat — sekaligus *tradeoff* pertamamu: pencarian biner supercepat, tetapi menuntut data sudah terurut lebih dulu.

::: check
Q: Mengapa efisiensi algoritma diukur dari jumlah langkah terhadap n, bukan dari waktu di stopwatch?
A: Karena waktu bergantung pada perangkat kerasnya; jumlah langkah sebagai fungsi n menggambarkan pertumbuhan kerja algoritma itu sendiri, di komputer mana pun.
Q: Apa kasus terburuk pencarian sekuensial pada daftar berukuran n, dan berapa langkahnya?
A: Target berada di posisi terakhir atau tidak ada di daftar, sehingga algoritma memeriksa semua n elemen.
:::

Di materi pendalaman, kamu akan membedah cara menghitung kompleksitas kasus terburuk langkah demi langkah — lalu mengoptimalkan algoritma yang boros menjadi jauh lebih cepat.', NULL, NULL, 5, 0.3, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_diagram_id_v2', 'k12_algorithms', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Alur Analisis Kasus Terburuk dan Peta Pertumbuhannya', 'Diagram ini merangkum cara menganalisis kompleksitas kasus terburuk sebuah algoritma, lalu membandingkan laju pertumbuhan kelas-kelas kompleksitas yang paling sering muncul. Bacalah dari kiri ke kanan, kemudian turun ke grafik pembanding.

```
          ALUR ANALISIS KASUS TERBURUK
+-----------+   +--------------+   +--------------+
| Algoritma |-->| Hitung f(n)  |-->| Suku dominan |
| (pseudo-  |   | = langkah    |   | => Big-O     |
| kode)     |   | maksimum     |   |              |
+-----------+   +--------------+   +--------------+
                                          |
                                          v
        PERBANDINGAN PERTUMBUHAN (n = 1.000)
   O(log n)   |#                 ~10
   O(n)       |##                1.000
   O(n log n) |#####             ~10.000
   O(n^2)     |################  1.000.000
```

Legend:

- Kotak: satu tahap dalam proses analisis.
- Tanda "-->" dan "v": urutan membaca, dari kiri ke kanan lalu ke bawah.
- f(n): jumlah langkah maksimum sebagai fungsi ukuran data n.
- Tanda "#": batang pembanding — makin panjang, makin banyak langkah (panjangnya ilustratif, bukan skala persis).
- Tanda "~": nilai kira-kira hasil pembulatan.

Cara membaca:

1. Mulai dari kotak kiri: tuliskan algoritmamu dalam pseudokode agar setiap langkahnya terlihat jelas.
2. Cari input yang memaksa kerja terbanyak, lalu hitung f(n), jumlah langkah maksimum itu.
3. Buang konstanta dan suku kecil; suku yang tumbuh paling cepat menentukan kelas Big-O.
4. Turun ke grafik: temukan kelas algoritmamu dan bandingkan panjang batangnya dengan kelas lain.
5. Renungkan angkanya: pada n = 1.000, jarak antara ~10 langkah dan 1.000.000 langkah adalah jarak antara "instan" dan "terasa berat" — dan jurang itu makin lebar saat n bertambah.

::: tip
Saat menghitung f(n), fokuslah pada perulangan terdalam. Satu loop yang berjalan n kali menyumbang O(n); loop di dalam loop yang sama-sama sampai n berarti dikalikan, menjadi O(n²). Latihan cepatnya: setiap bertemu kode baru, tebak dulu kelas Big-O-nya sebelum menghitung — lama-lama tebakanmu makin tajam.
:::', NULL, NULL, 3, 0.4, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_audio_id_v2', 'k12_algorithms', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Berpikir Kasus Terburuk: Cara Menilai Algoritma', NULL, NULL, 'Pernahkah kamu bertanya-tanya kenapa aplikasi peta bisa menemukan rute di antara jutaan ruas jalan dalam hitungan detik? Jawabannya ada pada satu kebiasaan berpikir para perancang algoritma: selalu bertanya, berapa banyak langkah yang dibutuhkan pada kasus terburuk, dan apa yang terjadi kalau datanya membesar.

Begini idenya. Kecepatan komputer berbeda-beda, jadi kita tidak menilai algoritma dengan stopwatch. Kita menghitung langkahnya. Kalau datamu berisi n item, berapa langkah maksimum yang mungkin terjadi? Kasus terburuk itu penting karena dialah jaminan yang bisa kamu pegang. Program yang biasanya cepat tetapi sesekali macet total tetap saja program yang bermasalah.

Ambil contoh sederhana: mencari siswa tertinggi di sekolah. Cara pertama, bariskan semua siswa lalu urutkan dari yang terpendek sampai yang tertinggi, dan ambil yang paling ujung. Bisa, tetapi mengurutkan itu pekerjaan besar. Cara kedua, telusuri barisan satu kali saja sambil mengingat siapa yang tertinggi sejauh ini. Setiap siswa cukup dibandingkan satu kali. Seratus siswa berarti seratus perbandingan. Sejuta siswa berarti sejuta perbandingan. Pertumbuhannya lurus dan mudah diprediksi.

Sekarang bandingkan dengan algoritma yang membandingkan setiap siswa dengan setiap siswa lain, berpasang-pasangan. Seratus siswa berarti sekitar lima ribu perbandingan. Tetapi gandakan jumlah siswanya, dan kerjanya bukan dua kali lipat, melainkan sekitar empat kali lipat. Itulah bahaya pertumbuhan kuadratik: di data kecil tidak terasa, di data besar meledak.

Perancang algoritma yang baik juga sadar akan tradeoff. Kadang kamu bisa memangkas waktu dengan mengorbankan memori tambahan. Kadang algoritma tercepat menuntut data yang sudah terurut lebih dulu. Tidak ada pilihan yang gratis; yang ada hanyalah pilihan yang diambil secara sadar.

Dan jangan lupakan kasus tepi: data kosong, data berisi satu item, atau target yang tidak ada sama sekali. Algoritma yang tangguh tetap benar di situasi-situasi aneh seperti itu.

Sekarang pertanyaan penutup. Kalau sebuah algoritma memakai perulangan bersarang, dan keduanya berjalan sebanyak n kali, apa yang terjadi pada jumlah langkahnya saat datamu digandakan?

Jawabannya: kerjanya melonjak sekitar empat kali lipat, karena jumlah langkah tumbuh sebanding dengan n kuadrat. Karena itu, sebelum datamu membesar, biasakan bertanya: seperti apa kasus terburukku, dan adakah cara yang lebih cerdas?', 4, 0.45, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_reading_deep_id_v2', 'k12_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menganalisis Kasus Terburuk dan Mengoptimalkan Algoritma', 'Inti yang perlu kamu pegang: efisiensi algoritma dinilai dari pertumbuhan jumlah langkah terhadap ukuran data *n*, dengan kasus terburuk sebagai patokan jaminan. Sekarang kita praktikkan analisis itu secara utuh, lalu gunakan hasilnya untuk mengoptimalkan.

## Contoh utuh: mendeteksi NIS ganda

Misalkan sekolah menyimpan daftar Nomor Induk Siswa dan kamu harus memastikan tidak ada yang ganda. Versi paling lugas: bandingkan setiap pasangan.

```
fungsi adaGanda(A):                // n = panjang(A)
    untuk i dari 0 hingga n-2:
        untuk j dari i+1 hingga n-1:
            jika A[i] = A[j]:
                kembalikan benar
    kembalikan salah
```

Analisis kasus terburuknya, langkah demi langkah:

1. Kasus terburuk terjadi saat **tidak ada** yang ganda (atau pasangan ganda baru bertemu paling akhir), karena semua pasangan harus diperiksa.
2. Saat i = 0, loop dalam berjalan n-1 kali; saat i = 1, sebanyak n-2 kali; begitu seterusnya sampai tersisa 1 kali.
3. Totalnya (n-1) + (n-2) + ... + 1 = n(n-1)/2 perbandingan.
4. Untuk n besar, suku n² mendominasi — kita sebut kompleksitasnya **O(n²)**.
5. Uji nyata: n = 10.000 siswa berarti sekitar 50 juta perbandingan. Gandakan menjadi n = 20.000, dan kerjanya melonjak kira-kira empat kali lipat menjadi sekitar 200 juta.

Sekarang optimasinya: korbankan sedikit memori untuk memangkas waktu. Simpan NIS yang sudah dilihat dalam *himpunan* (hash set), struktur yang bisa menjawab "apakah x sudah ada?" dalam waktu hampir konstan.

```
fungsi adaGandaCepat(A):
    terlihat <- himpunan kosong
    untuk setiap x dalam A:
        jika x ada di terlihat:
            kembalikan benar
        tambahkan x ke terlihat
    kembalikan salah
```

Telusuri dengan A = [12, 7, 19, 7]: angka 12 belum terlihat, simpan; 7 belum, simpan; 19 belum, simpan; 7 sudah ada — kembalikan benar dalam 4 iterasi. Setiap elemen ditangani sekali, jadi kompleksitasnya sekitar **O(n)**: dari 50 juta perbandingan menjadi 10.000 operasi. Harganya? Memori tambahan O(n) untuk himpunan — inilah *tradeoff* waktu-versus-ruang yang klasik. Jangan lupakan kasus tepi: daftar kosong dan daftar satu elemen harus mengembalikan salah, dan duplikat yang bersebelahan maupun berjauhan harus sama-sama tertangkap.

## Miskonsepsi yang sering muncul

::: misconception
Keliru: "Programku terasa instan waktu diuji, berarti algoritmanya sudah efisien."
Faktanya, hampir semua algoritma terasa instan pada data kecil — O(n²) dengan n = 100 hanya sekitar 5.000 perbandingan. Masalahnya adalah pertumbuhan: pada n = 1.000.000, algoritma O(n²) butuh sekitar 500 miliar perbandingan, sementara O(n) cukup sejuta. Efisiensi dinilai dari bagaimana jumlah langkah tumbuh saat n membesar, bukan dari kesan cepat pada data uji yang mungil.
:::

## Ke mana kemampuan ini membawamu

Analisis kasus terburuk dan optimasi adalah keterampilan puncak di jenjang ini, dan transfernya langsung terasa di luar kurikulum: mata kuliah struktur data dan algoritma di perguruan tinggi, lomba pemrograman kompetitif, sampai pekerjaan rekayasa perangkat lunak sungguhan — mengindeks basis data, merutekan peta, atau menyaring jutaan transaksi. Ke mana pun kamu melangkah setelah ini, kebiasaan bertanya "berapa langkah di kasus terburuk, dan apa yang kukorbankan untuk mempercepatnya?" akan terus terpakai.

::: check
Q: Daftar 2.000 NIS diperiksa dengan adaGanda versi loop bersarang. Kira-kira berapa kali lipat kerjanya dibanding daftar 1.000 NIS, dan mengapa?
A: Sekitar empat kali lipat, karena jumlah perbandingan tumbuh sebanding n² — menggandakan n berarti mengalikan kerja dengan 2 kuadrat, yaitu 4.
Q: Kapan versi O(n²) yang "lambat" justru bisa menjadi pilihan yang wajar?
A: Saat n dijamin kecil, atau saat memori sangat terbatas sehingga himpunan tambahan O(n) tidak terjangkau — memilih algoritma selalu soal tradeoff, bukan sekadar angka kompleksitas.
:::', NULL, NULL, 8, 0.6, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_reading_intro_id_v2', 'k12_control', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Loop Bersarang: Saat Kerja Program Berlipat Ganda', 'Pernah penasaran kenapa sebuah aplikasi terasa gesit saat datanya sedikit, tapi mendadak lambat begitu datanya ribuan? Sering kali penyebabnya bukan perangkatnya yang lemah, melainkan struktur kontrol di dalam programnya — khususnya loop di dalam loop. Kalau kamu bisa membaca struktur itu, kamu bisa memperkirakan berat-ringannya sebuah algoritma bahkan sebelum menjalankannya.

## Loop Bersarang: Kerja yang Dikalikan, Bukan Dijumlahkan

Satu loop yang berjalan n kali berarti badan loop dieksekusi n kali — itu mudah. Tetapi begitu kamu menaruh loop di dalam loop (disebut *loop bersarang*), aturannya berubah total: setiap satu putaran loop luar memicu **seluruh** putaran loop dalam dari awal. Kerjanya tidak dijumlahkan, melainkan **dikalikan**.

Ikuti pseudocode pencetak denah kursi bioskop berikut:

```
untuk baris dari 1 sampai 5
    untuk kolom dari 1 sampai 8
        tampilkan "Kursi", baris, kolom
```

Telusuri jalannya. Saat baris = 1, loop dalam berjalan penuh dari kolom 1 sampai 8 — tercetak 8 kursi. Lalu baris naik ke 2, dan loop dalam mengulang lagi dari awal: 8 cetakan lagi. Begitu seterusnya sampai baris = 5. Totalnya 5 × 8 = 40 baris keluaran, bukan 5 + 8 = 13.

Sekarang generalisasikan: dengan n baris dan m kolom, total kerjanya n × m. Kalau keduanya sama-sama n, kerjanya n². Menganalisis struktur kontrol untuk menalar dampaknya pada kinerja seperti ini adalah inti standar AP-K12-4. Konsekuensinya serius: pada pola n², menggandakan ukuran data membuat kerja menjadi empat kali lipat. Dari 100 data ke 200 data, kerja melonjak dari 10.000 menjadi 40.000 langkah. Itulah kenapa program yang lancar saat diuji dengan data kecil bisa tersedak di dunia nyata.

Ada tradeoff yang perlu kamu hargai juga: loop bersarang sering kali merupakan solusi paling sederhana dan paling mudah dibaca. Untuk data kecil, itu pilihan yang sepenuhnya masuk akal. Analisis struktur membantumu tahu kapan kesederhanaan itu mulai terlalu mahal harganya.

::: check
Q: Sebuah loop luar berjalan 6 kali, dan di dalamnya ada loop yang berjalan 10 kali. Berapa kali badan loop paling dalam dieksekusi?
A: 60 kali — setiap putaran loop luar menjalankan loop dalam secara penuh, jadi 6 × 10, bukan 6 + 10.
Q: Program berpola n² membutuhkan sekitar 2.500 langkah untuk 50 data. Berapa perkiraan langkahnya untuk 100 data?
A: Sekitar 10.000 langkah — pada pola kuadratik, menggandakan n melipatempatkan jumlah kerja.
:::

Di materi pendalaman, kamu akan membedah loop bersarang yang lebih licik — yang batas loop dalamnya berubah-ubah — dan belajar menghitung kasus terburuknya dengan presisi.', NULL, NULL, 5, 0.3, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_diagram_id_v2', 'k12_control', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Alur Eksekusi Loop Bersarang', 'Diagram ini memetakan alur dua loop bersarang: loop luar dengan pencacah i (n putaran) dan loop dalam dengan pencacah j (m putaran). Perhatikan dua jalur yang berputar kembali ke atas — jalur kecil berputar m kali untuk setiap satu putaran jalur besar.

```
        +-----------+
        |   i = 0   |
        +-----+-----+
              v
        +-----------+  tidak   +-----------+
  +---->|  i < n ?  |--------->|  SELESAI  |
  |     +-----+-----+          +-----------+
  |           | ya
  |           v
  |     +-----------+
  |     |   j = 0   |
  |     +-----+-----+
  |           v
  |     +-----------+  tidak   +-----------+
  |  +->|  j < m ?  |--------->| i = i + 1 |--+
  |  |  +-----+-----+          +-----------+  |
  |  |        | ya                            |
  |  |        v                               |
  |  |  +-----------+                         |
  |  |  | kerjakan  |                         |
  |  |  | tugas i,j |                         |
  |  |  +-----+-----+                         |
  |  |        v                               |
  |  |  +-----------+                         |
  |  +--| j = j + 1 |                         |
  |     +-----------+                         |
  +-------------------------------------------+
```

**Legenda**

- Kotak berisi pernyataan (misal `i = 0`): langkah proses, dieksekusi sekali setiap dilewati.
- Kotak berisi tanda tanya (misal `i < n ?`): pemeriksaan kondisi dengan dua jalur keluar.
- Label `ya` / `tidak`: jalur yang diambil sesuai hasil kondisi.
- Panah `--->` dan `v`: arah alur eksekusi.
- Garis yang kembali ke pemeriksaan kondisi: jalur perulangan (loop).

**Cara membaca**

1. Mulai dari `i = 0`, lalu alur tiba di pemeriksaan `i < n ?`.
2. Jika ya, loop dalam disiapkan: `j = 0`, lalu masuk pemeriksaan `j < m ?`.
3. Selama `j < m` benar, kerjakan tugas (i, j) lalu naikkan j — putaran kecil ini terjadi m kali.
4. Begitu `j < m` gagal, `i = i + 1` dieksekusi dan alur kembali ke `i < n ?` lewat jalur terluar — satu putaran besar tuntas.
5. Begitu `i < n` gagal, program selesai; kotak "kerjakan tugas" total dieksekusi n × m kali.

::: tip
Saat menganalisis kode berloop, beri label setiap loop dengan jumlah putarannya, lalu kalikan label dari lapisan terluar ke terdalam. Jika batas loop dalam bergantung pada pencacah loop luar, jumlahkan deretnya — jangan langsung mengalikan.
:::', NULL, NULL, 3, 0.4, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_audio_id_v2', 'k12_control', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Mengalikan Kerja: Cerita Loop Bersarang', NULL, NULL, 'Bayangkan kamu jadi panitia turnamen futsal antarkelas dengan enam tim, dan setiap tim harus bertanding melawan setiap tim lain tepat satu kali. Bagaimana sebuah program menyusun daftar pertandingannya? Jawabannya adalah loop di dalam loop, yang biasa disebut loop bersarang.

Begini cara kerjanya. Loop luar memilih tim pertama, satu per satu, dari tim satu sampai tim enam. Lalu, setiap kali loop luar memilih satu tim, loop dalam berjalan penuh untuk memilih lawannya. Di sinilah ide terpentingnya: kerja pada loop bersarang itu dikalikan, bukan dijumlahkan. Kalau loop luar berjalan enam kali dan setiap putarannya menjalankan loop dalam enam kali, maka badan loop dieksekusi tiga puluh enam kali.

Tapi tunggu, tiga puluh enam itu terlalu banyak untuk turnamen kita. Tim satu melawan tim satu jelas tidak masuk akal, dan pertandingan tim satu lawan tim dua sama saja dengan tim dua lawan tim satu. Maka kita ubah strukturnya: loop dalam mulai dari tim setelah tim yang sedang dipilih loop luar. Sekarang hitung bersama. Tim satu bertemu lima lawan. Tim dua bertemu empat lawan tersisa. Tim tiga bertemu tiga, lalu dua, lalu satu. Lima tambah empat tambah tiga tambah dua tambah satu sama dengan lima belas pertandingan. Perhatikan bahwa mengubah struktur loop langsung mengubah jumlah kerjanya.

Sekarang bagian yang paling penting untuk diingat. Kalau pesertanya digandakan menjadi dua belas tim, jumlah pertandingannya bukan tiga puluh, melainkan enam puluh enam. Data hanya dua kali lipat, tapi kerjanya melonjak lebih dari empat kali lipat. Pola pertumbuhan seperti ini disebut kuadratik, dan inilah alasan sebuah program yang terasa cepat saat diuji dengan data kecil bisa melambat parah saat dipakai dengan data sungguhan. Karena itu, seorang perancang algoritma selalu bertanya: pada kasus terburuk, berapa kali baris paling dalam ini dieksekusi?

Pertanyaan penutup untukmu. Sebuah loop luar berjalan sepuluh kali, dan setiap putarannya menjalankan loop dalam sebanyak dua puluh kali. Berapa kali badan loop paling dalam dieksekusi?

Jawabannya dua ratus kali. Setiap satu putaran loop luar memicu seluruh dua puluh putaran loop dalam, jadi kita mengalikan sepuluh dengan dua puluh, bukan menjumlahkannya.', 4, 0.45, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_reading_deep_id_v2', 'k12_control', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Membedah Loop Bersarang dan Menghitung Kasus Terburuk', 'Kamu sudah tahu bahwa loop bersarang mengalikan kerja. Sekarang kita naik satu level: menganalisis loop bersarang yang batas loop dalamnya berubah-ubah, lalu menghitung kasus terburuknya secara presisi.

## Bedah Kasus: Mencari Pasangan Berjumlah Target

Diberikan sebuah daftar angka, kita ingin tahu apakah ada dua angka pada posisi berbeda yang jumlahnya sama dengan target. Pendekatan paling lugas: bandingkan setiap pasangan.

```
fungsi cariPasangan(data, target)
    n = panjang(data)
    untuk i dari 0 sampai n - 2
        untuk j dari i + 1 sampai n - 1
            jika data[i] + data[j] == target
                kembalikan (i, j)
    kembalikan "tidak ada"
```

Jalankan dengan data = [3, 5, 2, 7] dan target = 9, langkah demi langkah:

| i | j | Perbandingan | Hasil |
| --- | --- | --- | --- |
| 0 | 1 | 3 + 5 = 8 | bukan 9, lanjut |
| 0 | 2 | 3 + 2 = 5 | bukan 9, lanjut |
| 0 | 3 | 3 + 7 = 10 | bukan 9, lanjut |
| 1 | 2 | 5 + 2 = 7 | bukan 9, lanjut |
| 1 | 3 | 5 + 7 = 12 | bukan 9, lanjut |
| 2 | 3 | 2 + 7 = 9 | ketemu! kembalikan (2, 3) |

Perhatikan strukturnya: loop dalam **tidak** selalu berjalan n kali. Saat i = 0 ia berjalan 3 kali, saat i = 1 hanya 2 kali, saat i = 2 tinggal 1 kali. Pada kasus terburuk — pasangan tidak pernah ditemukan — total perbandingannya adalah deret 3 + 2 + 1 = 6, atau secara umum (n - 1) + (n - 2) + ... + 1 = n(n - 1) / 2.

Angka ini penting. Untuk n = 1.000, kasus terburuknya 499.500 perbandingan. Memang "hanya setengah" dari n², tetapi kelas pertumbuhannya tetap kuadratik: gandakan datanya, kerjanya tetap membengkak sekitar empat kali lipat. Sebaliknya, kasus terbaiknya cuma 1 perbandingan — ketika pasangan pertama langsung cocok dan perintah kembalikan menghentikan semuanya. Jangan lupakan edge case: daftar kosong atau berisi satu elemen membuat loop dalam tak pernah berjalan, dan fungsi langsung menjawab "tidak ada" — perilaku yang benar tanpa penanganan khusus.

## Miskonsepsi yang Sering Muncul

::: misconception
Keliru: "Dua loop bersarang berarti kerjanya pasti n × n, tiga loop berarti n³ — tinggal hitung berapa lapis loopnya."
Yang benar: jumlah kerja ditentukan oleh berapa kali baris paling dalam benar-benar dieksekusi, bukan oleh banyaknya lapisan loop di kode. Loop dalam yang mulai dari i + 1 menghasilkan n(n - 1)/2 langkah, bukan n². Loop dalam yang batasnya konstan — misalnya selalu tepat 10 putaran — menghasilkan 10n langkah, yang tumbuh linear meski kodenya tampak bersarang. Analisislah batas setiap loop, jangan sekadar menghitung lapisannya.
:::

## Ke Mana Kemampuan Ini Membawamu

Menalar dari struktur kontrol ke jumlah kerja adalah fondasi analisis algoritma — keterampilan inti yang akan terus kamu pakai di kuliah informatika, kompetisi pemrograman, dan rekayasa perangkat lunak profesional. Kemampuan yang sama menjadi dasar keputusan tradeoff nyata: mempertahankan loop bersarang yang sederhana dan mudah dibaca untuk data kecil, atau menggantinya dengan struktur data dan algoritma yang lebih cerdas begitu skalanya membesar. Perancang yang baik tidak menebak; ia menghitung kasus terburuknya lebih dulu.

::: check
Q: Loop luar berjalan untuk i dari 1 sampai n, dan loop dalam berjalan untuk j dari 1 sampai i. Berapa total eksekusi badan loop dalam, dan bagaimana kelas pertumbuhannya?
A: Totalnya 1 + 2 + ... + n = n(n + 1)/2, dan kelas pertumbuhannya kuadratik — setara n² untuk n yang besar.
Q: Jika kita menambahkan perintah berhenti (break) begitu jawaban ditemukan, kasus mana yang membaik: terbaik, rata-rata, atau terburuk?
A: Kasus terbaik dan rata-rata membaik, tetapi kasus terburuk tidak berubah — kasus terburuk justru terjadi saat jawaban tidak pernah ditemukan, sehingga break tidak pernah dieksekusi.
:::', NULL, NULL, 8, 0.6, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_reading_intro_en_v2', 'k2_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Steps in Order: Your First Algorithms', 'You already follow steps every day. You wash your hands before you eat. You put on socks before shoes. When the steps go in the right order, things work!

## The Big Idea: Steps in Order

A list of steps has a special name. It is called an **algorithm**. That is a big word for a simple thing. An algorithm is just steps you follow, one at a time, in order.

A recipe is an algorithm. It tells you what to do first, next, and last. Lining up for lunch has steps too. Stand up. Push in your chair. Walk to the line. Steps, steps, steps!

Good steps follow two rules:

- The steps are **clear**. Anyone can follow them.
- The steps are **in order**. First things first!

If the steps are clear and in order, anyone who follows them gets the same happy ending. You, your friend, your grandma — everyone!

## Follow Along: Brushing Your Teeth

Let''s try one together. Here is a tooth-brushing algorithm:

1. Pick up your toothbrush.
2. Put a little toothpaste on the brush.
3. Brush your teeth, up and down.
4. Spit into the sink.
5. Rinse your brush and put it away.

Pretend to do each step right now. Pick up... squeeze... brush, brush, brush... spit... rinse. You did it!

Now let''s be silly. What if we swapped step 2 and step 4? You would spit into the sink *before* you even brushed. And you would put toothpaste on the brush at the very end, for nobody! Silly, right? The steps only work when they stay in order.

::: check
Q: What is an algorithm?
A: A list of clear steps you follow in order to get something done.
Q: In the tooth-brushing algorithm, what must happen before you brush?
A: You put toothpaste on the brush first. That step comes before brushing.
:::

You know the big idea now. Next, we will build a whole algorithm together — and hunt for a sneaky missing step!', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_diagram_en_v2', 'k2_algorithms', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'A Step Map for Washing Your Hands', 'Here is a picture of an algorithm for washing your hands. Each box holds one step. The arrows show what comes next. Read it from top to bottom.

```
+----------------------+
| 1. Turn on the water |
+----------------------+
           |
           v
+----------------------+
| 2. Get some soap     |
+----------------------+
           |
           v
+----------------------+
| 3. Scrub and sing    |
|    the ABC song      |
+----------------------+
           |
           v
+----------------------+
| 4. Rinse your hands  |
+----------------------+
           |
           v
+----------------------+
| 5. Dry with a towel  |
+----------------------+
```

Legend:

- A **box** holds one step to do.
- The **arrow** (the line with a v) means "then do this next."
- The **numbers** show the order, from 1 to 5.

How to read the step map:

1. Start at the very top box. That is step 1: turn on the water.
2. Do what the box says.
3. When you finish, slide down the arrow to the next box.
4. Do that step, then follow the next arrow down.
5. Keep going, box by box, until you reach the last box.
6. After box 5, you are done — clean, dry hands!

::: tip
Point at each box with your finger. When you finish a step, slide your finger down the arrow to the next box. Your finger keeps your place, just like when you read a book!
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_audio_en_v2', 'k2_algorithms', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Let''s Talk About Steps in Order', NULL, NULL, 'Hi there, friend! Today we are going to talk about something you already do every single day. You follow steps. Little steps, one after another, that help you get things done.

Think about making a bowl of cereal. You do not do it all at once. You do it in steps. First, you get a bowl. Next, you pour in the cereal. Then, you pour in the milk. Last, you grab a spoon and take a bite. Four little steps, and breakfast is ready.

Now let''s be silly for a second. What if you poured the milk first, before you got the bowl? Splash! Milk all over the table. Or what if you grabbed the spoon first and tried to eat, with no cereal and no bowl? You would just be nibbling air! That shows us something important. The order of the steps really matters.

When you make a list of steps to get something done, that list has a special name. It is called an algorithm. Say it with me. Al-go-rith-um. It sounds like a big fancy word, but it just means a list of steps in order.

A good algorithm needs two things. First, the steps must be clear, so anyone can follow them. Second, the steps must be in order, so first things come first and last things come last. If your steps are clear and in order, then you, your friend, or even a robot could follow them and get the very same yummy bowl of cereal.

You follow algorithms all day long. When you line up for lunch, that is steps in order. When you get ready for bed, that is steps in order too. Once you start noticing, you will find steps hiding everywhere.

Here is your question before we say goodbye. Are you ready? What is an algorithm?

Did you say it? Here is the answer. An algorithm is a list of clear steps that you follow in order to get something done. That is it! You use algorithms every day, and now you know their name. Great job, step-by-step superstar!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_reading_deep_en_v2', 'k2_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Building an Algorithm, Step by Step', 'Quick reminder: an algorithm is a list of clear steps in order. When the steps are clear and in order, anyone can follow them and get the same result.

## A Sandwich, Step by Step

Let''s build an algorithm for making a jam sandwich. Read each step. Pretend your hands are doing it!

1. Get two slices of bread.
2. Open the jam jar.
3. Scoop some jam with a spoon.
4. Spread the jam on one slice.
5. Put the other slice on top.
6. Take a big bite. Yum!

Now let''s test it, like real problem-solvers do. We will pretend a robot friend follows our steps. The robot does *exactly* what we say — nothing more, nothing less.

- Step 1: The robot gets two slices. Good.
- Step 2: The robot opens the jar. Good.
- Step 3: Scoop. Step 4: Spread. Step 5: Stack. Step 6: Munch!

It worked! But what if we forgot step 2? The robot tries to scoop the jam... and bonk! The jar is still closed. The robot is stuck. One tiny missing step can break the whole plan. Finding that missing step and adding it back is called **fixing** your algorithm. It feels great when it finally works!

## A Sneaky Wrong Idea

::: misconception
Wrong idea: "If I know what I want, I do not need to say every step. My helper will just know what I mean."
The truth: A helper following an algorithm only does what the steps say. It cannot guess. If you skip a step, like opening the jar, the helper gets stuck. Great step-writers say every step, even the tiny ones, and put them in order.
:::

Try this at home: ask a grown-up to be your robot. Give them steps for something simple. If they get stuck, hooray — you found a step to fix!

## Where These Steps Take You

What you learn here transfers to bigger adventures. In later grades, you will write longer algorithms and compare two plans to see which one is better. After that, you will draw your plans as pictures and give your steps to real computers, which follow them exactly like our robot friend. Big kids even learn to pick the fastest steps for really big problems. It all starts with what you can do right now: clear steps, in order. Teachers sometimes call this skill by its standard name, CSTA 1A-AP-08 — but you can just call it making great steps!

::: check
Q: A friend writes these steps for a robot: "Color in the circle. Draw a circle." What is wrong, and how do you fix it?
A: The steps are out of order. You cannot color a circle that is not drawn yet. Swap them: draw first, then color.
Q: Your sandwich steps never say "Open the jar." What happens when the robot follows them, and what is the fix?
A: The robot gets stuck at scooping because the jar is closed. Add the missing step "Open the jam jar" before the scooping step.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_reading_intro_id_v2', 'k2_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Algoritma: Urutan Langkah Seperti Resep', 'Pernahkah kamu membantu Ibu membuat kue? Ada urutannya, kan? Telur dulu, baru tepung, lalu diaduk. Nah, hari ini kita belajar rahasia di balik semua urutan langkah itu.

## Ide Besarnya: Urutan Langkah

Setiap hari kamu melakukan banyak hal. Bangun tidur. Mandi. Memakai seragam. Sarapan. Semuanya punya urutan.

Urutan langkah untuk menyelesaikan sesuatu punya nama keren. Namanya **algoritma**.

Algoritma itu seperti resep. Resep memberi tahu kita apa yang harus dilakukan. Satu per satu. Dari awal sampai selesai.

Ada dua aturan penting:

- Langkahnya harus **jelas**. Tidak boleh membuat bingung.
- Urutannya harus **benar**. Tidak boleh melompat-lompat.

Kalau dua aturan ini dipatuhi, siapa pun yang mengikuti langkahmu akan berhasil. Hasilnya pun sama!

## Ayo Coba: Menggosok Gigi

Ayo kita susun algoritma menggosok gigi. Ikuti pelan-pelan, ya.

1. Ambil sikat gigi.
2. Beri pasta gigi sedikit.
3. Gosok gigi atas dan bawah.
4. Berkumur dengan air.
5. Cuci sikat dan simpan kembali.

Mudah, kan? Lima langkah kecil, dan gigimu bersih berkilau.

Sekarang coba bayangkan urutannya terbalik. Berkumur dulu, baru memberi pasta gigi. Wah, aneh sekali! Giginya tidak jadi bersih.

Itulah kekuatan algoritma. Langkah yang jelas, urutan yang benar, hasil yang bagus. Kamu sudah memakai algoritma setiap hari tanpa sadar, lho!

*Materi ini selaras dengan capaian belajar BK-K2-1.*

::: check
Q: Apa itu algoritma?
A: Algoritma adalah urutan langkah yang jelas untuk menyelesaikan sesuatu, seperti resep kue atau langkah menggosok gigi.
Q: Mengapa urutan langkah tidak boleh terbalik?
A: Kalau terbalik, hasilnya jadi salah atau aneh. Contohnya berkumur dulu sebelum menggosok gigi membuat gigi tetap kotor.
:::

Masih penasaran? Di bacaan berikutnya, kita akan menyusun langkah membuat camilan lezat dan mencari tahu kesalahan yang paling sering terjadi!', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_diagram_id_v2', 'k2_algorithms', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Langkah dari Mulai sampai Selesai', 'Algoritma bisa digambar seperti peta jalan. Peta di bawah ini menunjukkan urutan langkah mencuci tangan, dari awal sampai selesai.

```
+--------------------------+
| MULAI: tangan kotor      |
+--------------------------+
             |
             v
+--------------------------+
| 1. Basahi tangan         |
+--------------------------+
             |
             v
+--------------------------+
| 2. Pakai sabun           |
+--------------------------+
             |
             v
+--------------------------+
| 3. Gosok sampai berbusa  |
+--------------------------+
             |
             v
+--------------------------+
| 4. Bilas dengan air      |
+--------------------------+
             |
             v
+--------------------------+
| 5. Keringkan tangan      |
+--------------------------+
             |
             v
+--------------------------+
| SELESAI: tangan bersih   |
+--------------------------+
```

**Legenda**

- Kotak = satu langkah yang harus dikerjakan.
- Panah ( | dan v ) = artinya "lalu", lanjut ke langkah berikutnya.
- MULAI = keadaan awal, sebelum langkah pertama.
- SELESAI = hasil akhir, setelah semua langkah selesai.

**Cara membaca petanya**

1. Mulai dari kotak paling atas, MULAI. Tanganmu masih kotor.
2. Ikuti panah ke bawah menuju langkah 1, lalu kerjakan langkahnya.
3. Setiap selesai satu kotak, ikuti panah ke kotak berikutnya.
4. Jangan melompati kotak. Setiap langkah penting!
5. Berhenti saat sampai di kotak SELESAI. Tanganmu kini bersih.

::: tip
Saat menyusun langkahmu sendiri, buat satu kotak untuk satu langkah kecil saja. Lalu tunjuk kotaknya satu per satu sambil mengerjakannya, seperti berjalan di petak ular tangga!
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_audio_id_v2', 'k2_algorithms', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Si Kucing Lapar dan Urutan Langkah', NULL, NULL, 'Halo! Hari ini kita akan berkenalan dengan sesuatu yang keren. Namanya algoritma. Wah, katanya panjang, ya? Tenang saja. Artinya sederhana sekali. Algoritma adalah urutan langkah untuk menyelesaikan sesuatu.

Kamu sudah sering memakai algoritma, lho. Saat kamu berbaris masuk kelas, itu ada urutannya. Saat kamu memakai baju, itu juga ada urutannya. Kaus dulu, baru jaket. Bukan jaket dulu, baru kaus. Lucu sekali kalau terbalik, kan?

Sekarang, ayo kita coba satu contoh. Bayangkan kamu punya kucing yang lapar. Namanya Belang. Belang mengeong terus. Dia minta makan. Apa saja langkah untuk memberinya makan? Ayo kita susun pelan-pelan.

Langkah pertama, ambil mangkuk makan Belang. Langkah kedua, buka wadah makanan kucing. Langkah ketiga, tuang makanan ke dalam mangkuk. Langkah keempat, letakkan mangkuk di lantai. Langkah kelima, panggil Belang. Belang datang berlari. Dia makan dengan lahap. Hore, berhasil!

Coba pikirkan. Bagaimana kalau urutannya kita balik? Misalnya, kita tuang makanan dulu, padahal mangkuknya belum diambil. Wah, makanannya tumpah ke lantai! Berantakan, deh. Jadi, urutan itu penting sekali. Langkah yang benar harus datang di waktu yang benar.

Ada satu hal lagi yang penting. Langkah-langkahnya harus jelas. Kalau kita hanya bilang, beri makan kucing, adik kecil mungkin bingung. Makanannya di mana? Mangkuknya yang mana? Tapi kalau langkahnya jelas dan urut, siapa pun bisa mengikutinya. Hasilnya pun sama. Belang kenyang dan senang.

Nah, itulah algoritma. Urutan langkah yang jelas untuk menyelesaikan sesuatu. Kamu bisa menemukannya di mana-mana. Di dapur, di kamar mandi, bahkan di sekolah saat berbaris.

Sebelum selesai, ada satu pertanyaan untukmu. Apa dua hal yang membuat urutan langkah kita berhasil? Coba jawab dulu di dalam hati, ya.

Jawabannya: langkahnya harus jelas, dan urutannya harus benar. Kalau dua hal itu ada, siapa pun yang mengikuti langkahmu akan berhasil. Sampai jumpa di petualangan berikutnya!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_algorithms_reading_deep_id_v2', 'k2_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menyusun Langkah yang Jelas dan Urut', 'Kamu sudah tahu ide besarnya: algoritma adalah urutan langkah yang jelas untuk menyelesaikan sesuatu. Sekarang kita berlatih menyusun langkah seperti juru masak cilik.

## Contoh Lengkap: Membuat Roti Selai

Perutmu berbunyi. Kamu ingin roti selai. Ayo susun algoritmanya bersama-sama.

1. Siapkan dua lembar roti di atas piring.
2. Buka tutup stoples selai.
3. Ambil selai sedikit dengan sendok.
4. Oleskan selai di satu lembar roti.
5. Tutup dengan lembar roti satunya.
6. Roti selai siap dimakan. Nyam!

Ayo kita jalan pelan-pelan.

Langkah 1 menyiapkan semuanya. Tanpa roti, tidak ada yang bisa diolesi. Langkah 2 harus terjadi sebelum langkah 3, karena stoples yang tertutup tidak bisa diambil isinya. Langkah 4 baru bisa dilakukan setelah selai ada di sendok. Langkah 5 menutup rotinya. Dan langkah 6 adalah hadiahnya!

Sekarang coba kita nakal sedikit. Kita tukar langkah 4 dan 5. Rotinya ditutup dulu, baru diolesi selai. Apa yang terjadi? Selainya menempel di luar roti! Tangan jadi lengket. Meja jadi kotor. Langkahnya sama, tetapi urutannya salah. Hasilnya pun kacau.

Satu hal lagi. Perhatikan setiap langkah di atas. Semuanya jelas. "Oleskan selai di satu lembar roti" mudah diikuti siapa saja. Kalau kita hanya menulis "buat rotinya enak", teman kita pasti bingung. Langkah yang jelas membuat siapa pun bisa berhasil.

## Hati-Hati, Ini Sering Keliru

::: misconception
Banyak teman berpikir: yang penting semua langkah dikerjakan, urutannya bebas saja.
Itu keliru, ya. Urutan sama pentingnya dengan langkah itu sendiri. Coba pakai sepatu dulu, baru kaus kaki. Tidak bisa, kan? Langkahnya sama, urutannya berbeda, hasilnya gagal. Algoritma yang baik punya langkah yang jelas dan urutan yang benar.
:::

## Ke Mana Ilmu Ini Membawamu

Kemampuan menyusun langkah yang urut akan terus kamu pakai sampai besar. Di jenjang berikutnya, kamu akan menyusun langkah yang lebih panjang dan mengenal langkah yang diulang-ulang, namanya loop atau perulangan. Naik lagi, kamu belajar menuliskan langkah supaya bisa dijalankan komputer dan memperbaiki langkah yang keliru. Semua itu dimulai dari sini: langkah kecil yang jelas dan urut.

::: check
Q: Dina menulis langkah membuat es sirup: tuang sirup, ambil gelas, aduk, tuang air. Apa yang keliru dari urutan Dina?
A: Gelas harus diambil paling awal. Urutan yang benar: ambil gelas, tuang sirup, tuang air, lalu aduk. Kalau gelas belum ada, sirupnya tumpah.
Q: Langkah menyiram bunga: ambil gembor, lalu siram bunga. Ada satu langkah penting yang hilang. Langkah apa itu?
A: Mengisi gembor dengan air. Tanpa langkah itu, tidak ada air yang keluar dan bunganya tetap kering.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_reading_intro_en_v2', 'k2_control', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Again and Again, or Make a Choice?', 'Do you put on one shoe and then walk away? No way! You put on the other shoe too. Your whole day is full of steps you do again and again, and full of little choices you make without even noticing. Today you get to be a step detective and catch them in action.

## The Big Idea: Repeats and Choices

You already know how to make a list of steps for a job. Now meet two very special kinds of steps.

- **A repeat** is a step you do again and again. Hop, hop, hop. Stir, stir, stir.
- **A choice** is when you check something first, and then pick what to do. If it is raining, take your raincoat. If it is sunny, leave it home.

Repeats are great helpers. Without them, your list of steps would have to say "brush, brush, brush, brush" a hundred times! With a repeat, you just say "keep brushing until you are done." Choices are great helpers too. They let the same list of steps work on rainy days AND sunny days.

## Follow Along: Teeth Time

Let''s find a repeat and a choice hiding in your bathroom. Here are the steps for brushing your teeth:

1. Put toothpaste on your brush.
2. Brush one spot.
3. Brush the next spot.
4. Keep brushing, again and again, until your toothbrush song ends.
5. Smile at the mirror. If you spot a messy tooth, brush that spot one more time.

Did you catch them? Step 4 is a **repeat** — you brush again and again, and the song tells you when to stop. Step 5 is a **choice** — first you check your smile, then you pick what to do.

::: check
Q: You hop across the room: hop, hop, hop, hop. Is that a repeat or a choice?
A: A repeat! You do the same hop again and again until you get across the room.
Q: "If it is cold outside, wear your mittens." Is that a repeat or a choice?
A: A choice. First you check something — is it cold? — and then you pick what to do.
:::

Great detective work! Next, we will play a whole game made of repeats and choices, and see where this superpower takes you.', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_diagram_en_v2', 'k2_control', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'See the Repeat: The Pancake Batter Picture', 'Step detectives sometimes draw a picture of their steps so the repeat is easy to see. Here is a picture for stirring pancake batter.

```
        +---------------------+
        | START: make batter  |
        +---------------------+
                   |
                   v
        +---------------------+
  +---> |    Stir one time    |
  |     +---------------------+
  |                |
  |                v
  |     +---------------------+
  |     | Is the batter       |
  |     | smooth yet?         |
  |     +---------------------+
  |          |          |
  |         no         yes
  |          |          |
  +----------+          v
              +------------------+
              | STOP: pour and   |
              | cook the pancake |
              +------------------+
```

Legend:
- A box is one step, or one question to check.
- The arrows (v and --->) show where to go next.
- The "no" path climbs back up. That means: stir again!
- The "yes" path goes down. That means: the repeat is over.

How to read it:
1. Start at the top box: you are making pancake batter.
2. Follow the arrow down and stir one time.
3. Answer the question box: is the batter smooth yet?
4. If the answer is no, follow the line back up to "Stir one time" and stir again.
5. If the answer is yes, follow the arrow down to STOP and pour your pancake.

::: tip
Act it out in your kitchen! Say each box out loud while a grown-up stirs, and shout "Again!" every time you take the "no" path. When the batter is smooth, shout "Stop!" — you just followed a repeat with your own eyes and ears.
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_audio_en_v2', 'k2_control', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cleanup Time Tricks: Repeat and Choose', NULL, NULL, 'Hi, friend! Let''s talk about two tricks your brain uses all day long. The first trick is doing something again and again. The second trick is making a choice. Ready? Let''s go.

Think about cleanup time in your room. The floor is covered with toys. You do not pick up one toy and walk away. You pick up a toy. You put it in the bin. Then you do it again. Pick up, put in. Pick up, put in. Again and again. That is called a repeat. And here is the clever part. You know when to stop. You stop when the floor is clear. A repeat does not go on forever. It keeps going until the job is done.

Now for the second trick. While you clean, you make little choices. Maybe you pick up something and it is a book. A book does not belong in the toy bin. So you ask yourself a quick question. Is this a book? If yes, it goes on the shelf. If no, it goes in the bin. That is a choice. First you check something. Then you pick what to do.

Repeats and choices are hiding everywhere. You chew your food again and again until it is soft. You check the sky, and if it looks dark, you play inside. When you start to notice these tricks and say them out loud, you are thinking the same way people think when they plan steps for computers. Computers use the exact same two tricks. They repeat steps, and they make choices, millions of times, super fast. But you learned the idea first, right in your own room.

Here is your recap question. At cleanup time, what is the repeat, and when do you stop? Think about it for a moment. Here is the answer. The repeat is picking up a toy and putting it away, again and again. And you stop when the floor is clear and every toy is home. You did it. Happy repeating, and happy choosing!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_reading_deep_en_v2', 'k2_control', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Red Light, Green Light: A Game of Repeats and Choices', 'Quick recap of the big idea: a **repeat** is a step you do again and again until the job is done, and a **choice** is when you check something first, then pick what to do.

## A Whole Game Made of Steps

Let''s play Red Light, Green Light with our detective eyes open. Here are the steps for a player:

1. Stand at the start line.
2. Listen to the caller.
3. If the caller says "green light," walk forward.
4. If the caller says "red light," freeze like a statue.
5. Not at the finish line yet? Go back to step 2 and listen again.
6. At the finish line? You win — stop!

Now let''s watch one pretend round, step by step.

- The caller shouts "Green light!" You check the words. Green! So you walk, walk, walk.
- The caller shouts "Red light!" You check again. Red! You freeze. Not even a wiggle.
- "Green light!" You check, then walk again. You are getting close.
- You touch the finish line. The repeating stops. You win!

See what happened? Steps 3 and 4 are **choices** — you check the caller''s words first, then pick walk or freeze. Steps 2 to 5 make one big **repeat** — listen, choose, move, and do it all again. The finish line is the stopping point that ends the repeat.

## Do Repeats Go On Forever?

::: misconception
The wrong idea: "A repeat means doing something forever and ever, with no way to stop."
The truth: every good repeat has a stopping point. In the game, you repeat "listen and move" only until you touch the finish line. A repeat without a stopping point would keep you playing until bedtime! When you make a repeat, always ask: "When do I stop?"
:::

## Where This Leads

The spotting you did today is a superpower that grows with you. In the next level of control structures, you will tell a computer to repeat steps an exact number of times, like "do this 10 times." After that, you will learn to tuck choices inside repeats to build real games and apps, and to stop or skip steps at just the right moment. It all starts with catching repeats and choices in your own day — which is exactly what you practiced here. (A little note for grown-ups: this lesson matches the CSTA 1A-AP-10 standard.)

::: check
Q: You hang up 6 coats, one at a time. What do you repeat, and when do you stop?
A: You repeat "hang up one coat." You stop when there are zero coats left to hang.
Q: Your teacher says, "If you hear the bell, line up." What do you check, and what do you do?
A: You check for the bell sound. If you hear it, you line up. If you do not, you keep playing.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_reading_intro_id_v2', 'k2_control', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Dua Kata Ajaib: Ulangi dan Kalau', 'Setiap pagi kamu melakukan banyak hal hebat. Kamu menggosok gigi, memakai baju, dan menyiapkan tas. Tahukah kamu? Di dalam kegiatan itu ada dua kata ajaib yang juga dipakai komputer!

## Dua Kata Ajaib: "Ulangi" dan "Kalau"

Kamu sudah kenal algoritma. Algoritma itu urutan langkah yang jelas. Nah, di dalam urutan langkah, sering muncul dua kata ajaib.

Kata ajaib pertama: **ulangi**. Artinya, lakukan hal yang sama lagi dan lagi, sampai selesai. Seperti melompat tali. Lompat, lompat, lompat, sampai hitungan sepuluh!

Kata ajaib kedua: **kalau**. Artinya, pilih langkah sesuai keadaan. Kalau hujan, bawa payung. Kalau cerah, tidak perlu.

Komputer bekerja seperti itu juga. Komputer suka mengulang. Komputer juga suka memilih dengan kata "kalau". Kamu dan komputer ternyata mirip!

### Ayo Coba: Menggosok Gigi

Ikuti langkah ini pelan-pelan:

1. Ambil sikat gigi.
2. Beri pasta gigi sedikit.
3. Sikat gigi bagian atas. **Ulangi** gerakannya sepuluh kali.
4. Sikat gigi bagian bawah. **Ulangi** sepuluh kali juga.
5. **Kalau** masih ada sisa makanan, sikat lagi bagian itu.
6. Kumur-kumur. Selesai!

Lihat! Ada kata "ulangi" di langkah 3 dan 4. Ada kata "kalau" di langkah 5. Kamu baru saja memakai dua kata ajaib. Hore!

Coba perhatikan lagi. Kata "ulangi" membuat langkahnya jadi pendek. Kita tidak perlu menulis "sikat, sikat, sikat" sepuluh kali. Cukup satu kalimat: ulangi sepuluh kali. Hemat sekali, kan?

::: check
Q: Kata apa yang kita pakai saat menyikat gigi sepuluh kali?
A: Kata "ulangi", karena gerakan yang sama dilakukan lagi dan lagi sampai hitungan sepuluh.
Q: Kapan kita memakai kata "kalau"?
A: Saat harus memilih langkah sesuai keadaan. Misalnya, kalau masih ada sisa makanan, kita sikat lagi bagian itu.
:::

Di bacaan berikutnya, kita berlatih lebih seru lagi: menyiram bunga di teras dengan dua kata ajaib ini!', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_diagram_id_v2', 'k2_control', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Langkah Membereskan Mainan', 'Ini peta langkah untuk membereskan mainan di lantai. Ikuti panahnya dari MULAI sampai SELESAI, ya.

```
          MULAI
            |
            v
   +------------------+
   | Ambil 1 mainan   |<------+
   +------------------+       |
            |                 |
            v                 |
   +------------------+       |
   | Taruh di kotak   |       |
   +------------------+       |
            |                 |
            v               YA|
   ( Masih ada mainan? )------+
            |
          TIDAK
            |
            v
         SELESAI
```

Legend:

- Kotak bergaris = langkah yang harus dilakukan
- ( ... ) = pertanyaan dengan jawaban YA atau TIDAK
- Panah dan garis = jalan yang harus diikuti
- YA / TIDAK = jawaban dari pertanyaan
- MULAI dan SELESAI = awal dan akhir kegiatan

Cara membaca petanya:

1. Mulai dari kata MULAI di paling atas.
2. Ikuti panah ke bawah: ambil satu mainan, lalu taruh di kotak.
3. Sampailah kamu di pertanyaan: masih ada mainan di lantai?
4. Kalau jawabannya YA, ikuti garis yang naik ke atas. Ulangi lagi dari "ambil satu mainan".
5. Kalau jawabannya TIDAK, turun ke SELESAI. Lantai sudah rapi!

Jalan yang berputar naik itu seperti kata ajaib "ulangi". Pertanyaannya seperti kata ajaib "kalau". Dua-duanya ada di satu peta!

::: tip
Coba gambar peta seperti ini untuk kegiatanmu sendiri, misalnya memasukkan buku ke dalam tas. Ingat: setiap pertanyaan harus punya dua jalan keluar, satu untuk YA dan satu untuk TIDAK.
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_audio_id_v2', 'k2_control', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Semangkuk Sup dan Kata Ajaib Ulangi', NULL, NULL, 'Hai, teman kecil! Hari ini kita ngobrol tentang dua kata ajaib. Kata pertama adalah ulangi. Kata kedua adalah kalau. Dua kata ini kamu pakai setiap hari, lho. Komputer juga memakainya setiap saat.

Ayo kita mulai dari kata ulangi. Ulangi artinya melakukan hal yang sama, lagi dan lagi, sampai selesai. Coba ingat waktu kamu makan sup ayam kesukaanmu. Kamu ambil sendok, kamu suap, kamu telan. Lalu apa? Kamu ambil sendok lagi, suap lagi, telan lagi. Begitu terus, berulang-ulang, sampai mangkuknya kosong. Kamu tidak perlu berpikir ulang di setiap suapan. Kamu hanya mengulang langkah yang sama sampai supnya habis.

Sekarang kata kedua, yaitu kalau. Kata kalau membantu kita memilih. Masih ingat sup tadi? Kalau supnya masih panas, apa yang kamu lakukan? Betul sekali, kamu tiup dulu sendoknya. Tapi kalau supnya sudah hangat, kamu boleh langsung makan. Langkahnya berubah sesuai keadaan. Itulah gunanya kata kalau.

Nah, dua kata ini sering bekerja sama. Dengarkan baik-baik, ya. Ambil satu sendok sup. Kalau masih panas, tiup dulu. Lalu suap. Ulangi sampai mangkuk kosong. Hanya empat kalimat pendek, tapi bisa mengatur seluruh acara makanmu sampai selesai. Keren, kan?

Komputer bekerja dengan cara yang sama. Komputer bisa mengulang pekerjaan yang sama ribuan kali tanpa bosan. Komputer juga terus memilih dengan kata kalau. Kalau tombol ditekan, mainkan musik. Kalau tidak, diam menunggu. Jadi setiap kali kamu mengulang dan memilih, kamu sedang berpikir seperti komputer.

Satu hal penting sebelum kita selesai. Setiap pengulangan harus punya tanda berhenti. Makan sup berhenti saat mangkuk kosong. Naik tangga berhenti saat kakimu sampai di atas. Tanpa tanda berhenti, kita akan mengulang terus sampai malam. Lucu sekali, ya.

Sekarang pertanyaan penutup untukmu. Saat makan sup, kata apa yang kita pakai untuk terus menyuap sampai mangkuk kosong? Coba jawab dulu dalam hati. Sudah? Jawabannya adalah ulangi. Kita mengulang suapan yang sama sampai ada tanda berhenti, yaitu mangkuk yang kosong. Hebat sekali! Sampai jumpa di petualangan berikutnya.', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_control_reading_deep_id_v2', 'k2_control', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menyiram Bunga dengan Kata Ulangi dan Kalau', 'Ingat dua kata ajaib kita? **Ulangi** berarti melakukan hal yang sama sampai selesai. **Kalau** berarti memilih langkah sesuai keadaan.

## Ayo Berlatih: Menyiram Bunga

Bayangkan ada tiga pot bunga di teras. Tugasmu menyiramnya. Tapi awas! Bunga tidak boleh kebanyakan air.

Ini urutan langkahnya:

1. Isi teko siram dengan air.
2. Berdiri di depan pot pertama.
3. Sentuh tanahnya. **Kalau** tanahnya kering, siram. **Kalau** tanahnya basah, jangan disiram.
4. Pindah ke pot berikutnya.
5. **Ulangi** langkah 3 dan 4 sampai semua pot selesai.

Sekarang kita jalankan sama-sama:

- **Pot satu.** Sentuh tanahnya. Kering! Jadi... siram. Pindah ke pot dua.
- **Pot dua.** Sentuh tanahnya. Basah! Jadi... jangan disiram. Pindah ke pot tiga.
- **Pot tiga.** Sentuh tanahnya. Kering! Siram. Semua pot sudah dicek. Berhenti.

Hebat! Kamu mengulang langkah yang sama tiga kali. Tapi hasilnya beda-beda. Pot satu dan tiga disiram, pot dua tidak. Kata "kalau" yang membantumu memilih. Kata "ulangi" yang membuatmu tidak lupa satu pot pun.

## Awas, Jangan Keliru!

::: misconception
Ada yang bilang: "Mengulang itu ribet. Kita harus menyebut langkah yang sama berkali-kali. Panjaaang sekali!"
Itu keliru. Kita cukup bilang satu kalimat pendek: "Ulangi sampai selesai." Satu kalimat itu sudah mengatur semuanya. Yang penting, harus ada tanda berhentinya. Misalnya: sampai semua pot dicek, atau sampai hitungan sepuluh.
:::

Ingat baik-baik: pengulangan yang baik selalu tahu kapan berhenti. Kalau tidak ada tanda berhenti, kita bisa menyiram bunga sampai malam. Bunganya kebanjiran!

## Ke Mana Ilmu Ini Membawamu?

Kata "ulangi" dan "kalau" adalah bibit dari dua ide besar: perulangan dan pemilihan. Di kelas yang lebih tinggi nanti, kamu akan memakai keduanya untuk menyusun balok perintah di layar, lalu suatu hari menulis program sungguhan. Semua permainan dan aplikasi kesukaanmu dibangun dari dua ide ini. Latihan hari ini sesuai capaian belajar BK-K2-2 dan menjadi bekalmu naik ke jenjang berikutnya.

::: check
Q: Pada latihan menyiram bunga, kapan pengulangan berhenti?
A: Saat semua pot sudah dicek. Itulah tanda berhentinya.
Q: Pot satu disiram, tapi pot dua tidak. Padahal langkahnya sama. Kata apa yang membuat hasilnya berbeda?
A: Kata "kalau". Pilihannya tergantung keadaan tanah: kalau kering disiram, kalau basah tidak disiram.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_intro_en_v2', 'k2_modularity', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Big Jobs, Little Pieces', 'Have you ever looked at your messy room and thought, "This is too big! I can''t do it!"? Big jobs can feel that way. But there is a secret trick, and big kids and computer scientists use it every day.

## The Big Idea: Break It Into Pieces

Think about eating a big cookie. You do not swallow it in one gulp. You take small bites. One bite at a time, and soon the cookie is gone!

Big jobs work the same way. A big job is made of smaller jobs hiding inside it. When you find the small jobs, the big job stops being scary.

You already know how to follow steps in order, like a recipe. Now you will learn to chop a big job into small jobs first. Then each small job gets its own easy steps.

Here is the trick in three parts:

1. Say the big job out loud.
2. Find the small jobs hiding inside.
3. Do the small jobs one at a time.

## Let''s Try It Together

The big job: **clean your room**. Whoa. That sounds big. Let''s find the small jobs hiding inside it.

- Put the toys in the toy box.
- Put the books on the shelf.
- Put the dirty clothes in the basket.

See? Three small jobs. Each one is easy. You do the toys. Done! You do the books. Done! You do the clothes. Done! And look — the big job finished itself, piece by piece.

::: check
Q: What can you do when a big job feels too hard?
A: Break it into small jobs, then do the small jobs one at a time.
Q: What is one small job hiding inside "clean your room"?
A: Putting the toys in the toy box. (Books on the shelf or clothes in the basket are great answers too!)
:::

When you are ready, the next reading shows you how to find the hiding small jobs all by yourself.', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_diagram_en_v2', 'k2_modularity', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Job Tree: How Big Jobs Split Apart', 'A picture can show how one big job breaks into small jobs. The big job sits at the top. The small jobs hang under it, like apples on a tree.

```
          +--------------------------+
          |   BIG JOB: Have a picnic |
          +--------------------------+
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
 +------------+ +------------+ +------------+
 | Pack the   | | Grab the   | | Pick a     |
 | snacks     | | blanket    | | shady spot |
 +------------+ +------------+ +------------+
```

**Legend**

- A box holds one job.
- The top box is the **big job**.
- The three bottom boxes are the **small jobs** hiding inside.
- The lines show the big job splitting into pieces.
- The little **v** arrows point to each small job.

**How to read it**

1. Start at the top box. The big job is "Have a picnic."
2. Follow the line going down. It splits into three paths.
3. Each arrow lands on one small job.
4. Do the small jobs one at a time: pack the snacks, grab the blanket, pick a shady spot.
5. When all three bottom boxes are done, the top box is done too. Picnic time!

::: tip
Next time a job feels too big, draw your own job tree! Put the big job in a box at the top. Draw a small box for each piece below it. Cross off each small box when you finish it. Watching the boxes fill up feels great.
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_audio_en_v2', 'k2_modularity', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Secret Trick for Big Jobs', NULL, NULL, 'Hi, friend! Today I want to share a secret trick with you. It is a trick that helps with any big job, and computer scientists use it all the time.

Sometimes a job feels way too big. Maybe it feels like a mountain. Your brain says, I can''t do all of that! Here is the trick. Big jobs are not really one giant thing. They are lots of little things hiding together in a bundle. When you find the little pieces, you can do them one at a time. Little piece by little piece, the big job gets done.

Let me tell you about making a pizza with a grown-up. If someone says, make a pizza, that might sound huge. But let''s find the small jobs hiding inside. First, pat the dough flat. Second, spread the sauce. Third, sprinkle the cheese. Fourth, add your favorite toppings. Then a grown-up puts it in the oven. Did you hear that? Making a pizza is really five little jobs standing in a line, like friends waiting for the slide.

And here is something cool. Each little job has its own tiny steps. Think about spreading the sauce. You scoop the sauce. You pour it on the dough. You spread it around in circles with a spoon. You already know all about steps in order. Now you know the trick that comes first. Break the big job into pieces, then give each piece its own steps.

You can use this trick everywhere. A big pile of blocks to put away? Put away the red ones, then the blue ones, then the rest. A long story to draw? Draw the beginning, then the middle, then the end. One piece at a time. That is the whole secret.

Here is your question. When a job feels too big, what can you do?

And here is the answer. You can break the big job into small pieces, and do the pieces one at a time. Small pieces make big jobs easy. You''ve got this!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_deep_en_v2', 'k2_modularity', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Finding the Small Jobs Hiding Inside', 'Here is the big idea again: a big job is made of small jobs hiding inside. Find the pieces, then do them one at a time.

## A Big Job, Piece by Piece

Let''s break a real big job together: **get ready for school**.

**Step 1: Say the big job.** "I need to get ready for school." Take a breath. It sounds big, but it is really a bundle of little jobs.

**Step 2: Find the pieces.** Ask yourself: "What parts are hiding inside?" Let''s list them:

1. Get dressed.
2. Eat breakfast.
3. Brush your teeth.
4. Pack your backpack.

**Step 3: Look closer at one piece.** Each small job is like a tiny recipe with its own steps. Take "get dressed":

- Put on your shirt.
- Put on your pants.
- Put on your socks.
- Put on your shoes.

You already know this part — steps in order! Every small job hides its own little list of steps.

**Step 4: Do the pieces one at a time.** Dressed? Done. Breakfast? Done. Teeth? Done. Backpack? Done. Four small wins, and the big job is finished. High five!

**Step 5: Check your work.** Ask: "Did I finish every piece?" If one piece is missing — maybe the backpack — the big job is not done yet. Every piece matters.

## Watch Out for This Mix-Up

::: misconception
Wrong idea: "Breaking a job into pieces makes MORE work."
The truth: It is the same job! The pieces do not add any work. They just make the work easier to see and easier to finish. One giant job can feel impossible. Four small jobs feel like four easy wins.
:::

## Where This Trick Takes You

This trick has a fancy grown-up name: breaking problems into parts. *(Grown-up note: this matches CSTA standard 1A-AP-14.)* When you are a little older, you will use the very same trick on bigger projects — like planning a story with a beginning, a middle, and an end, where each part gets built on its own. Later still, you will learn how big computer programs are split into small parts that different people can build and share. What you practice here — spotting the small jobs inside a big one — carries straight into all of that. Same trick, bigger jobs.

::: check
Q: Your class is putting on a puppet show. What are three small jobs hiding inside that big job?
A: Ideas: make the puppets, practice the story, and set up chairs for the audience. Any three sensible pieces work!
Q: You break "make fruit salad" into three pieces: wash the fruit, cut the fruit with a grown-up, mix it in a bowl. Could you do the mixing piece first?
A: No! Some pieces must come before others. You cannot mix fruit that is not washed and cut yet. Even with pieces, order still matters — just like steps in a recipe.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_intro_id_v2', 'k2_modularity', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Tugas Besar Jadi Potongan Kecil', 'Pernahkah kamu melihat kamarmu penuh mainan dan berpikir, "Wah, berantakan sekali!"? Tugas besar memang bisa terasa berat. Tapi tenang, ada trik rahasia: pecah tugas besar menjadi bagian-bagian kecil!

## Ide Besar: Potong Tugas Menjadi Bagian Kecil

Bayangkan sebuah semangka utuh. Terlalu besar untuk sekali gigit, kan? Makanya semangka dipotong-potong dulu. Setelah dipotong kecil, semangka jadi mudah dimakan. Satu potong, dua potong, habis deh!

Tugas juga begitu. Tugas besar terasa sulit kalau dikerjakan sekaligus. Tapi kalau dipecah menjadi bagian-bagian kecil, setiap bagian jadi mudah dan ringan.

Kamu sudah pernah belajar tentang urutan langkah. Nah, sekarang kita belajar satu hal baru: sebelum mulai, potong dulu tugas besarmu menjadi bagian-bagian kecil. Baru kerjakan satu per satu.

Para pembuat komputer juga bekerja seperti ini, lho. Mereka tidak membuat semuanya sekaligus. Mereka membagi pekerjaan menjadi bagian-bagian kecil, lalu menyelesaikannya satu demi satu.

## Contoh: Merapikan Kamar

Ayo kita coba bersama. Tugas besarnya: merapikan kamar.

Kalau dipikirkan sekaligus, pusing! Jadi kita potong dulu menjadi tiga bagian:

1. Kumpulkan mainan ke dalam kotak mainan.
2. Susun buku di rak.
3. Taruh baju kotor di keranjang.

Sekarang kerjakan satu bagian saja dulu. Mainan dulu! Selesai? Hebat! Lanjut ke buku. Selesai lagi? Keren! Terakhir, baju kotor. Nah, lihat! Tiga bagian kecil selesai, dan... seluruh kamar jadi rapi! Tugas besar selesai tanpa terasa berat.

::: check
Q: Apa trik untuk mengerjakan tugas yang besar dan terasa berat?
A: Pecah tugas besar itu menjadi bagian-bagian kecil, lalu kerjakan satu per satu.
Q: Saat merapikan kamar, sebutkan satu bagian kecil yang bisa dikerjakan lebih dulu.
A: Misalnya mengumpulkan mainan ke kotak mainan. Boleh juga menyusun buku di rak atau menaruh baju kotor di keranjang.
:::

Di bacaan berikutnya, kita akan memecah satu tugas seru selangkah demi selangkah. Sampai jumpa di sana!', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_diagram_id_v2', 'k2_modularity', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Memecah Tugas Besar', 'Gambar ini menunjukkan cara memecah satu tugas besar menjadi tiga bagian kecil. Ayo kita baca dari atas ke bawah, seperti menuruni tangga.

```
        +--------------------------+
        |       TUGAS BESAR        |
        |  Menyiapkan tas sekolah  |
        +------------+-------------+
                     |
       +-------------+------------+
       |             |            |
       v             v            v
  +----------+ +----------+ +----------+
  | Bagian 1 | | Bagian 2 | | Bagian 3 |
  | Masukkan | | Masukkan | | Masukkan |
  | buku     | | bekal    | | botol    |
  +----------+ +----------+ +----------+
       |             |            |
       +-------------+------------+
                     |
                     v
          +--------------------+
          |  Hore! Tas siap!   |
          +--------------------+
```

Legend

- Kotak (dibuat dari tanda +, -, dan |): satu tugas. Kotak paling atas adalah tugas besar, kotak tengah adalah bagian-bagian kecilnya.
- Tanda panah (v): artinya "lanjut ke sini".
- Garis tegak (|) dan garis datar (-): jalan yang menghubungkan kotak satu dengan kotak lainnya.
- Tanda tambah (+): sudut kotak atau tempat garis-garis bertemu.

Cara membaca

1. Mulai dari kotak paling atas. Tugas besarnya: menyiapkan tas sekolah.
2. Ikuti garis ke bawah. Tugas besar itu terbagi menjadi tiga kotak kecil.
3. Kerjakan Bagian 1 dulu: masukkan buku ke dalam tas.
4. Lanjut ke Bagian 2, lalu Bagian 3: masukkan bekal, lalu botol minum.
5. Semua garis bertemu lagi di kotak paling bawah. Tas siap dibawa. Hore!

::: tip
Coba buat "peta bagian" seperti ini di kertas untuk tugasmu sendiri, misalnya membereskan meja belajar. Tulis tugas besarnya di kotak atas, lalu gambar satu kotak kecil untuk setiap bagiannya. Centang setiap kotak yang sudah selesai!
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_audio_id_v2', 'k2_modularity', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Trik Rahasia Menyelesaikan Tugas Besar', NULL, NULL, 'Halo, teman kecil! Hari ini kita akan belajar satu trik hebat. Trik ini dipakai oleh anak-anak, orang dewasa, bahkan para pembuat komputer. Triknya begini. Kalau ada tugas besar, jangan kerjakan sekaligus. Pecah dulu menjadi bagian-bagian kecil.

Kenapa begitu? Coba bayangkan kamu minum segelas air yang besar. Kamu tidak menelannya sekali teguk, kan? Kamu meminumnya seteguk demi seteguk, sampai habis. Tugas juga sama. Tugas besar terasa berat kalau dilihat sekaligus. Tapi kalau dipecah menjadi bagian-bagian kecil, setiap bagian terasa ringan dan mudah.

Ayo kita coba dengan satu contoh. Misalnya ibu berkata, tolong siapkan meja makan. Wah, itu tugas besar. Mulai dari mana, ya? Tenang. Kita pecah dulu. Bagian pertama, taruh piring untuk semua orang. Bagian kedua, taruh sendok dan garpu di samping piring. Bagian ketiga, taruh gelas. Sekarang kerjakan satu per satu. Piring dulu. Satu, dua, tiga, empat. Selesai! Lalu sendok dan garpu. Selesai juga! Terakhir, gelas. Selesai! Nah, tiga bagian kecil sudah beres, dan meja makan pun siap. Tugas besar selesai, dan rasanya tidak berat sama sekali.

Trik ini bisa kamu pakai di mana saja. Saat merapikan mainan. Saat menggambar. Saat membantu ayah dan ibu di rumah. Kalau tugasnya terasa besar, tarik napas dulu, lalu tanya pada dirimu sendiri. Bagian-bagian kecilnya apa saja, ya? Kerjakan satu bagian dulu sampai selesai. Setelah itu, lanjut ke bagian berikutnya. Sedikit demi sedikit, tugas besar pun selesai.

Ada satu hal seru lagi. Kalau ada bagian yang salah, kamu tidak perlu mengulang semuanya dari awal. Cukup perbaiki bagian yang salah itu saja. Hemat tenaga, kan?

Sekarang, pertanyaan penutup untukmu. Kalau kamu mendapat tugas besar yang terasa berat, apa yang harus kamu lakukan lebih dulu? Coba jawab dalam hati. Jawabannya, pecah tugas besar itu menjadi bagian-bagian kecil, lalu kerjakan satu per satu sampai semuanya selesai. Kamu hebat! Sampai jumpa di petualangan belajar berikutnya.', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_deep_id_v2', 'k2_modularity', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Memecah Tugas Selangkah demi Selangkah', 'Ingat trik kita? Tugas besar jadi mudah kalau dipecah menjadi bagian-bagian kecil. Sekarang ayo kita pakai trik itu pelan-pelan, sampai tuntas.

## Contoh Lengkap: Menggambar Rumah

Bu Guru berkata, "Ayo gambar sebuah rumah!" Wah, rumah itu besar. Mulai dari mana, ya?

Jangan panik. Kita pecah dulu.

**Langkah 1: Pikirkan bagian-bagiannya.**
Rumah punya apa saja? Ada dinding. Ada atap. Ada pintu. Ada jendela. Nah, itu empat bagian kecil!

**Langkah 2: Gambar dinding.**
Buat satu kotak besar di tengah kertas. Selesai! Satu bagian sudah jadi.

**Langkah 3: Gambar atap.**
Buat segitiga di atas kotak tadi. Selesai lagi!

**Langkah 4: Gambar pintu.**
Buat kotak kecil memanjang di bagian bawah dinding. Tambahkan satu titik untuk gagangnya.

**Langkah 5: Gambar jendela.**
Buat dua kotak kecil di kiri dan kanan pintu.

Sekarang pandangi kertasmu. Empat bagian kecil sudah bergabung menjadi... satu rumah yang utuh! Kamu tidak pernah menggambar "rumah" sekaligus. Kamu menggambar bagian demi bagian, dan rumahnya jadi dengan sendirinya.

Ada bonusnya juga. Misalnya jendelanya terlalu besar. Apakah semua gambar harus diulang? Tidak! Cukup hapus dan perbaiki jendelanya saja. Bagian yang lain tetap aman.

## Awas, Ada yang Suka Keliru!

::: misconception
Ada yang berpikir, "Memecah tugas menjadi bagian kecil itu membuat pekerjaan tambah banyak dan tambah lama."
Itu keliru, lho. Bagian-bagian kecil itu bukan tugas baru. Semuanya memang isi dari tugas besar tadi. Dengan memecahnya, kamu jadi tahu harus mulai dari mana, kepalamu tidak pusing, dan kalau ada yang salah kamu cukup memperbaiki satu bagian saja. Jadi kerjamu malah lebih cepat dan lebih rapi.
:::

## Ke Mana Ilmu Ini Membawamu

Trik memecah tugas ini adalah bekal penting di sekolah (capaian belajar BK-K2-3). Di kelas yang lebih tinggi nanti, kamu akan memakainya untuk memecah masalah yang lebih besar, misalnya membuat cerita bergambar atau permainan sederhana di komputer. Kamu juga akan belajar bahwa bagian-bagian kecil itu bisa diberi nama dan dipakai berulang-ulang, seperti balok mainan yang bisa disusun menjadi apa saja. Semuanya dimulai dari kebiasaan kecil yang kamu latih hari ini.

::: check
Q: Temanmu ingin menggambar kebun binatang, tapi bingung harus mulai dari mana. Apa saranmu?
A: Pecah dulu gambarnya menjadi bagian-bagian kecil, misalnya kandang, gajah, pohon, dan jalan. Lalu gambar satu bagian sampai selesai, baru lanjut ke bagian berikutnya.
Q: Gambar rumahmu hampir jadi, tapi pintunya terlalu kecil. Haruskah kamu mengulang seluruh gambar? Mengapa?
A: Tidak perlu. Karena gambar dibuat bagian demi bagian, cukup perbaiki bagian pintunya saja. Bagian lain tetap bagus dan tidak berubah.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_reading_intro_en_v2', 'k2_program_development', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Try It, Fix It: How Programs Get Better', 'Have you ever built a tall block tower that fell down? You did not cry and quit forever. You looked, found the wobbly block, and built it again. Guess what: that is exactly how people make computer programs!

## What Is a Program?

You already know about steps. A list of steps for doing a job is an algorithm. A **program** is a list of steps you give to a computer or a robot.

Here is the tricky part. Computers follow steps *exactly*. They do not guess. If a step is missing or mixed up, the computer does the silly thing anyway!

So programmers do three things, over and over:

1. **Try it out.** This is called *testing*. It is like tasting your soup while you cook.
2. **Find the mistake.** A mistake hiding in the steps is called a **bug**. Bug hunting is like finding the one wobbly block in your tower.
3. **Fix it and try again.**

### A Sandwich for Robot Grandpa

Let''s pretend Grandpa is a robot. He only does what your steps say. Here is your jam sandwich program:

1. Get two pieces of bread.
2. Spread the jam on the bread.
3. Put the two pieces together.

Time to test! Grandpa gets the bread. Then he rubs the closed jam jar on the bread. Ew! What happened?

We forgot a step: **open the jar**! That missing step is a bug. Add it in, test again, and, yum, it works. You did not start over. You fixed one step.

One more trick: you can *change* a program to make something new. Swap "jam" for "honey" and you have a honey sandwich program. Changing a program that already works is a big part of what programmers do.

::: check
Q: What do we call a mistake hiding in a program''s steps?
A: A bug. You find it, fix it, and try the steps again.
Q: How do you test a program?
A: You try it out and watch carefully to see if the steps do what you wanted.
:::

Ready for more? Next, we will go on a real bug hunt, step by step, with a dance you can try with a friend.', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_diagram_en_v2', 'k2_program_development', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Try-It, Fix-It Loop', 'When a program does not work, programmers do not panic. They go around a loop, again and again, until it works. Here is that loop as a picture.

```
        +------------------+
        |  MAKE THE STEPS  |
        +------------------+
                 |
                 v
        +------------------+
   +--> |    TRY IT OUT    |
   |    +------------------+
   |             |
   |             v
   |       Did it work?
   |        /        \
   |      YES         NO
   |       |           |
   |       v           v
   |   +-------+  +------------------+
   |   | DONE! |  | FIND THE MISTAKE |
   |   +-------+  +------------------+
   |                       |
   |                       v
   |              +------------------+
   +--------------|      FIX IT      |
                  +------------------+
```

Legend

- Boxes with words inside = a job for you to do
- Lines and arrows (| v /) = the path to the next job
- "Did it work?" = the testing question you ask yourself
- YES and NO = the two paths your answer can take
- The long line from FIX IT back up = try it again!

How to read it

1. Start at the top. Make your steps. That is your program.
2. Follow the arrow down and try it out. That is testing.
3. Ask the question: did it work? If YES, follow that path. You are done. Celebrate!
4. If NO, follow the other path and find the mistake. That is the bug.
5. Fix it, then follow the long line back up to TRY IT OUT.
6. Go around the loop as many times as you need. Every trip around makes your program better.

::: tip
Fix only one step at a time, then test right away. If you change lots of steps at once, you will not know which change fixed the bug!
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_audio_en_v2', 'k2_program_development', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Robot, the Flower, and the Sneaky Bug', NULL, NULL, 'Have you ever helped someone do a job by telling them the steps? First do this, then do that. Today I want to tell you a secret about how computer programs are made. A program is a list of steps that tells a computer or a robot what to do. And here is the secret. Almost no program works perfectly on the very first try. Not even the ones made by grown-ups. And that is completely okay, because programmers have a plan for it.

Let me tell you a story. Imagine you have a toy robot, and you want it to water a flower. So you give it three steps. Step one, pick up the cup. Step two, walk to the flower. Step three, pour the water on the flower.

Now you try it out. Trying your program to see if it works is called testing. So you press go. The robot picks up the cup. Good. It walks to the flower. Good. It tips the cup over and... nothing comes out. The flower stays dry. The cup was empty!

Did you catch the problem? We never told the robot to fill the cup with water. A sneaky missing step like that is called a bug. Funny name, right? It is like a tiny bug hiding inside your steps. Finding the bug and fixing it is called debugging. So we add one new step, right after picking up the cup. Fill the cup with water. Then we test again. The robot picks up the cup. It fills it with water. It walks to the flower. It pours. The flower gets a nice big drink. Hooray!

Here is what I want you to remember. A mistake is not a bad thing. A mistake is a clue. It tells you exactly where to look. You do not throw everything away. You keep the steps that work, and you fix the one step that needs help. And once your program works, you can even change it to do something new, like watering two flowers instead of one.

Time for one quick question. What should you do when your program does not work? Here is the answer. You test it, you find the bug, you fix that one step, and you try it again. That is what real programmers do every single day. And now you can do it too.', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_reading_deep_en_v2', 'k2_program_development', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Bug Hunters: Finding and Fixing Sneaky Mistakes', 'Quick reminder: a program is a list of steps for a computer or robot, and computers follow steps exactly. When something goes wrong, we test, find the bug, and fix it.

## Bug Hunt: The Wiggle Dance

Grab a friend and pretend they are a robot named Rosa. Rosa only does what the steps say. Here is your dance program:

1. Clap two times.
2. Jump one time.
3. Spin around.
4. Take a bow.

**Test number one.** Say the steps. Rosa claps, claps. Rosa jumps. Rosa spins... and spins... and spins! She never stops. Uh oh.

**Find the bug.** Watch where things went wrong. The clapping worked. The jumping worked. The trouble started at step 3. Look closely: "Spin around" never says *how many times*. Rosa is doing exactly what we said. The bug is a step that is not clear enough.

**Fix one step.** Change step 3 to: "Spin around one time." Do not touch the steps that already work!

**Test number two.** Clap, clap. Jump. One spin. A big bow. It works! Take a bow yourself, bug hunter.

**Now make it yours.** Add a new step 5: "Wiggle like a noodle." Changing a program that works, to make it bigger or better or sillier, is called *modifying* it. Test again after every change. And when you can say what you tried, what went wrong, and how you fixed it, you are talking like a real programmer. Teachers even have a name for that skill: CSTA 1A-AP-15.

## The Mistake About Mistakes

::: misconception
Wrong idea: "My program has a bug. That means I am bad at this, and I should throw it all away and start over."
The truth: every programmer finds bugs, even grown-ups who program every single day. A bug means one step needs help, not the whole program. Keep the steps that work. Find the one wobbly step. Fix just that one, and test again.
:::

Bugs are not failures. They are clues. Each one points to exactly where you should look next.

## Where This Leads

The moves you practiced today, test, find the bug, fix one step, test again, are the same moves programmers use forever. In your next step with program development, you will plan bigger programs before you build them and test them piece by piece. Later on, you will break giant problems into small parts and make your programs better version by version. The bug hunting never changes. Only the programs get bigger.

::: check
Q: Rosa claps two times but never jumps. Where should you look for the bug first?
A: Right where the trouble started. Check the jump step and the step just before it. Watching where a program goes wrong points you straight to the bug.
Q: You change one step in your dance so it ends with a twirl instead of a bow. What is the very next thing to do?
A: Test it! After every change, try the whole program again to make sure it still works.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_intro_en_v2', 'k2_variables', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Boxes That Remember: How Computers Hold On to Things', 'Do you have a favorite cup at home? Maybe yesterday it held milk, and today it holds juice. Same cup, different drink — and believe it or not, that little switcheroo is one of the biggest ideas in all of computers!

## A Box With a Name

Computers need to remember things. A game needs to remember your score. A drawing app needs to remember your favorite color. But computers do not have brains like yours. So they use something simpler: little boxes.

Every remembering box has two parts:

- A **name** on the outside. The name never changes.
- One **thing** on the inside. The thing inside can change!

Think about the cubby at school with your name on it. The label always says your name. But what is inside? In the morning, your coat. After lunch, maybe your library book. The cubby stays the same. The stuff inside changes.

Here is the most important rule: **a box holds only one thing at a time.** When you put something new in, the old thing comes out. It does not pile up like a toy bin. It swaps, like trading stickers.

## Try It: The Snack Cup

Let''s follow one box together. Pretend you have a cup with a label that says **Snack**.

1. In the morning, you drop in a cracker. Now if anyone asks, "What is in the Snack cup?" the answer is: a cracker.
2. After recess, you are tired of crackers. You take the cracker out and put in a banana.
3. Ask again: "What is in the Snack cup?" The answer is: a banana. Not a cracker. The cracker is gone.

The label said **Snack** the whole time. Only the food inside changed. That is exactly how a computer''s remembering boxes work.

::: check
Q: A box has the name **Pet** on it, and a toy dog inside. Can the name change? Can the toy change?
A: The name stays the same — it will always say Pet. But the toy inside can be swapped for something new anytime.
Q: The Snack cup held a cracker. Then you put in a banana. What is in the cup now?
A: Just the banana. When something new goes in, the old thing comes out. The box holds one thing at a time.
:::

Next up, we will follow one remembering box through a whole school week — and catch a sneaky mix-up that fools lots of kids (and grown-ups too!).', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_diagram_en_v2', 'k2_variables', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Score Box: A Picture of a Remembering Box', 'A remembering box has a name on the outside and one thing inside. This picture shows a score box during a bean bag toss game — watch what changes and what stays exactly the same.

```
         THE SCORE BOX GAME

   name on the box (it never changes)
                |
                v
       +-----------------+
       |      SCORE      |
       |    +-------+    |
       |    |   0   |    |  <- the thing inside
       |    +-------+    |
       +-----------------+
                |
                | a bean bag lands in!
                v
       +-----------------+
       |      SCORE      |
       |    +-------+    |
       |    |   1   |    |  <- new thing, swapped in
       |    +-------+    |
       +-----------------+
```

Legend

- **Big box**: the remembering box the computer uses
- **SCORE**: the box''s name — it stays the same the whole time
- **Small box with a number**: the one thing inside right now
- **| and v arrows**: time moving forward, from top to bottom
- **<- notes**: little pointers that tell you what a part is

How to read it

1. Start at the top and read the box''s name: SCORE.
2. Peek in the small box. It holds 0 — no points yet.
3. Follow the arrow down. Something happens: a bean bag lands in the basket!
4. The old number comes out, and 1 goes in its place.
5. Now ask the box for the score. It says 1 — only the newest number. And the name never moved.

::: tip
Build a real score box! Tape the word SCORE on a bowl and make number cards. Every time someone scores in a game, swap the card — old card out, new card in, one card at a time. That is exactly how a computer keeps score.
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_audio_en_v2', 'k2_variables', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Lunchbox Trick: How Computers Remember', NULL, NULL, 'Hi there, friend. Today I want to tell you a secret about computers. Computers seem so smart, right? They remember your game score. They remember your name. But here is the secret. Computers do not have brains like yours. They remember with boxes. Little pretend boxes.

Every box has a name written on the outside. That name never, ever changes. And inside the box, there is room for one thing. Just one. That thing can change anytime.

Let me show you with something you know. Think about your lunchbox. It is the same lunchbox every single day. Maybe it has your name on it. Maybe it has a dinosaur on it. On Monday, your grown-up puts a sandwich inside. So if a friend asks what is in your lunchbox, you say, a sandwich. But on Tuesday, your grown-up packs pasta instead. Now what is in your lunchbox? Pasta. Is the sandwich still in there too? No way. The sandwich came out when the pasta went in. The box holds one meal at a time. The newest thing wins.

That is exactly how a computer remembers. When you play a game and your score goes from three to four, the computer takes the three out of its score box and puts a four in. The three is gone. The box''s name still says score. Only the number inside changed.

So remember two things. First, the name on the box stays the same. Second, the thing inside can change, and the new thing takes the old thing''s place.

Now, here is your question. Are you ready? On Monday, your lunchbox held a sandwich. On Tuesday, your grown-up packed pasta. So on Tuesday, what is inside the lunchbox? The sandwich, the pasta, or both?

Take a second and think about it.

The answer is, just the pasta. The lunchbox holds one thing at a time. When the pasta went in, the sandwich came out. Same box, same name, new thing inside. And that, my friend, is how a computer remembers. Nice work today.', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_deep_en_v2', 'k2_variables', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'One Box, One Thing: Swapping What Is Inside', 'You know the big idea now: a remembering box has a name that stays the same, and one thing inside that can change.

## A Whole Week With One Box

Let''s watch one box very closely. In Room 4, there is a pocket chart on the wall. The pocket''s label says **Line Leader**. Inside the pocket goes one name card.

1. **Monday.** The teacher slides in a card that says *Mia*. Question: who is the line leader? Look in the pocket. The card says Mia. So Mia leads the line to lunch.
2. **Tuesday.** The teacher pulls Mia''s card out and slides in a card that says *Sam*. The pocket''s label did not change. It still says Line Leader.
3. Question: who is the line leader now? Look in the pocket. Sam. Mia''s card is not in there anymore.
4. **Wednesday.** Out comes Sam''s card. In goes *Ava*. Ask the pocket again — it says Ava.

Did you notice? The pocket never remembers Monday or Tuesday. It only knows *right now*. One pocket, one card, and the newest card wins. Computers use boxes just like this to remember your game score, your player name, and even which color crayon you picked in a drawing app.

## The Sneaky Mix-Up

::: misconception
Some kids think the box keeps everything you ever put in it — like a treasure chest that gets fuller and fuller. So they think the Line Leader pocket holds Mia and Sam and Ava, all squished together. That is not how it works! A remembering box is like a parking spot: one car at a time. When a new card goes in, the old card comes out and is gone from the box. If you want to keep the old thing too, you need a second box with its own name.
:::

## Where This Takes You

The pocket-chart trick you just learned is the seed of something big. Grown-up coders call these remembering boxes **variables**. Soon, in Variables for grades K-5, you will make your own — giving boxes names and putting numbers and words inside them in real programs. Later, in Variables for grades K-8, you will juggle many boxes at once and change what is inside using math. Using a name to stand for something that can change is a real school skill too — teachers call it standard CSTA 1A-AP-09.

::: check
Q: The Line Leader pocket held Mia, then Sam, then Ava. Who does the pocket say is line leader now — and where did the other names go?
A: Ava. The pocket holds only one card, so each new card pushed the old one out. Mia and Sam are not saved in the pocket at all.
Q: Two boxes are named **Pet One** and **Pet Two**, and right now both hold a cat picture. If you swap Pet One''s picture for a fish, what happens to Pet Two?
A: Nothing! They are two different boxes with different names — they just happened to hold the same thing. Pet Two still holds the cat picture.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_intro_id_v2', 'k2_variables', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Kotak Ajaib yang Isinya Bisa Berganti', 'Coba lihat kotak pensilmu. Kemarin isinya krayon merah. Hari ini kamu isi pensil biru. Kotaknya tetap sama, tapi isinya berganti! Di dalam komputer juga ada "kotak" seperti itu, dan komputer memakainya setiap saat.

## Kotak Penyimpan yang Hebat

Komputer perlu tempat untuk menyimpan hal-hal penting. Misalnya angka, nama, atau kata. Tempat penyimpan itu punya nama keren: **variabel**.

Bayangkan variabel seperti kotak dengan label nama. Labelnya ditulis satu kali dan tidak berubah. Tapi isinya? Isinya boleh diganti kapan saja!

- Labelnya tetap. Misalnya kotak bernama "Skor".
- Isinya bisa berganti. Tadi angka 0, nanti angka 5.

Kenapa ini penting? Karena banyak hal di sekitar kita suka berubah. Umurmu bertambah setiap ulang tahun. Cuaca berganti setiap hari. Komputer perlu cara untuk mengingat hal-hal yang berubah itu. Variabel adalah jawabannya. Saat kamu bermain di tablet, komputer mengingat skormu dengan variabel. Saat kamu menonton video, komputer mengingat sudah sampai mana kamu menonton. Semuanya disimpan di kotak-kotak kecil itu.

## Ayo Coba Bersama

Kita main lempar bola ke keranjang, yuk!

1. Ambil selembar kertas. Tulis label besar: **Skor**. Ini kotak variabel kita.
2. Belum ada bola yang masuk. Tulis angka **0** di bawah label.
3. Hore, satu bola masuk! Hapus angka 0. Tulis angka **1**.
4. Bola masuk lagi! Hapus angka 1. Tulis angka **2**.

Lihat, kan? Kertasnya tetap satu. Labelnya tetap "Skor". Yang berganti hanyalah angkanya. Begitulah cara variabel bekerja di dalam komputer: satu kotak, satu nama, isi yang bisa berganti-ganti.

::: check
Q: Pada kotak variabel, bagian mana yang boleh berganti: label namanya atau isinya?
A: Isinya. Label nama kotak selalu tetap, tapi isinya bisa diganti kapan saja.
Q: Kotak "Skor" berisi angka 2. Lalu satu bola masuk lagi ke keranjang. Sekarang isi kotaknya berapa?
A: Angka 3. Angka 2 dihapus dan diganti dengan angka 3.
:::

Kalau kamu sudah siap, ayo lanjut ke bacaan berikutnya untuk mengikuti cerita celengan Nina dan mengintip variabel lebih dekat lagi!', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_diagram_id_v2', 'k2_variables', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Satu Kotak, Isi Berganti-ganti', 'Variabel itu seperti kotak bernama. Gambar di bawah menunjukkan satu kotak bernama "Buah" yang isinya sedang diganti.

```
  nama kotak: Buah          nama kotak: Buah
 +--------------+          +--------------+
 |     apel     |  ganti   |    pisang    |
 |              | -------> |              |
 +--------------+          +--------------+
   isi sekarang               isi baru
```

**Legenda**

- Kotak dari tanda +, -, dan | : kotak variabel, tempat menyimpan isi.
- Tulisan "nama kotak: Buah" di atas : label kotak. Label ini tidak pernah berubah.
- Kata di dalam kotak (apel, pisang) : isi kotak pada saat itu.
- Panah -------> dengan kata "ganti" : isi lama dikeluarkan, isi baru dimasukkan.
- Tulisan "isi sekarang" dan "isi baru" di bawah : keterangan isi kotak sebelum dan sesudah diganti.

**Cara membaca gambarnya:**

1. Mulai dari kotak kiri. Namanya "Buah", isinya "apel".
2. Ikuti panah "ganti" ke arah kanan.
3. Saat diganti, "apel" dikeluarkan dan "pisang" dimasukkan.
4. Lihat kotak kanan. Namanya masih "Buah", tapi isinya sekarang "pisang".
5. Kalau ada yang bertanya, "Kotak Buah isinya apa?", jawabannya selalu isi yang paling baru: pisang.

::: tip
Coba di rumah! Ambil kardus kecil dan tempel label bertuliskan "Mainanku". Setiap pagi, ganti isinya dengan satu mainan yang berbeda. Labelnya tetap, isinya berganti. Persis seperti variabel!
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_audio_id_v2', 'k2_variables', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cerita Papan Hari dan Kotak Penyimpan', NULL, NULL, 'Halo, teman kecil! Hari ini kita akan berkenalan dengan sesuatu yang seru. Namanya variabel. Wah, kedengarannya seperti kata yang sulit, ya? Tenang saja. Variabel itu sebenarnya mirip benda yang kamu lihat setiap hari di kelas.

Variabel adalah tempat untuk menyimpan sesuatu. Bisa menyimpan angka. Bisa juga menyimpan kata. Yang paling istimewa, isinya boleh diganti. Tempatnya tetap sama. Namanya tetap sama. Tapi isinya bisa berubah-ubah.

Coba ingat papan hari di kelasmu. Papan itu selalu menempel di tempat yang sama, di dekat pintu. Tugasnya cuma satu, yaitu memberi tahu hari apa sekarang. Pada hari Senin, papan itu bertuliskan Senin. Besok paginya, ibu guru mengganti tulisannya menjadi Selasa. Papannya tidak dibuang. Papannya juga tidak pindah. Hanya tulisannya yang berganti.

Nah, variabel di dalam komputer bekerja persis seperti papan hari itu. Komputer punya banyak tempat penyimpan kecil. Setiap tempat punya nama sendiri. Nama itu tidak pernah berubah. Tapi isi di dalamnya boleh diganti kapan saja. Isi yang lama keluar, isi yang baru masuk.

Kenapa komputer butuh tempat seperti itu? Karena banyak hal suka berubah. Saat kamu bermain, jumlah bintang yang kamu kumpulkan terus bertambah. Komputer harus mengingatnya. Setiap kali bintangmu bertambah, komputer mengganti isi tempat penyimpannya dengan angka yang baru. Jadi komputer selalu tahu jumlah bintangmu yang paling baru.

Ada satu hal penting lagi. Variabel hanya menyimpan isi yang terbaru. Kalau papan hari sudah bertuliskan Selasa, tulisan Senin sudah tidak ada lagi di sana. Yang kita lihat selalu isi yang paling baru.

Sekarang, ada pertanyaan untukmu. Pada sebuah variabel, bagian mana yang bisa berubah? Dan bagian mana yang selalu tetap? Coba pikirkan sebentar.

Sudah? Ini jawabannya. Isinya bisa berubah, tapi namanya selalu tetap. Persis seperti papan hari di kelasmu. Papannya tetap di sana, tulisannya berganti setiap hari.

Hebat sekali! Sekarang kamu sudah mengenal variabel. Sampai jumpa di petualangan belajar berikutnya!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_deep_id_v2', 'k2_variables', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Mengintip Isi Kotak Variabel Lebih Dekat', 'Masih ingat kotak berlabel dari bacaan pertama? Variabel itu seperti kotak bernama: labelnya tetap, tapi isinya boleh berganti-ganti.

## Contoh Lengkap: Celengan Nina

Nina punya celengan bening. Di depannya ada label besar: **Koinku**. Ayo kita ikuti celengan itu selama tiga hari.

1. **Hari Senin.** Nina memasukkan 2 koin. Sekarang isi "Koinku" adalah **2**.
2. **Hari Selasa.** Nenek datang dan memberi 1 koin lagi. Nina memasukkannya. Isi "Koinku" berganti menjadi **3**. Angka 2 sudah bukan jawabannya lagi.
3. **Hari Rabu.** Nina membeli stiker lucu dengan 1 koin. Isi "Koinku" berganti lagi menjadi **2**.

Kapan pun Ibu bertanya, "Koinmu ada berapa, Nina?", Nina tidak perlu mengingat-ingat. Dia tinggal melihat isi celengannya sekarang. Itulah hebatnya variabel: dia selalu menyimpan isi yang **paling baru**.

Perhatikan juga: celengannya tetap satu. Labelnya tetap "Koinku". Nina tidak butuh celengan baru setiap kali jumlah koinnya berubah. Cukup ganti isinya saja.

## Hati-hati, Jangan Sampai Keliru

::: misconception
Ada yang mengira: "Kalau kotak variabel sudah diisi, isinya terkunci selamanya. Tidak boleh diganti lagi."
Itu keliru! Isi variabel justru boleh diganti berkali-kali. Itulah gunanya variabel. Isi lama keluar, isi baru masuk. Yang tidak pernah berganti hanyalah nama labelnya.
:::

Ada satu lagi yang sering bikin bingung: variabel tidak menyimpan semua isi lamanya. Saat isi "Koinku" menjadi 3, angka 2 tidak disimpan di sana lagi. Yang tersisa di kotak hanyalah isi yang terbaru.

## Ke Mana Ilmu Ini Membawamu

Kemampuan mengenal kotak penyimpan ini adalah bekal capaian belajar AP-K2-2, dan akan terus kamu pakai nanti. Di Variabel (K-5), kamu akan membuat kotakmu sendiri: memberinya nama yang pas dan memakainya di dalam program sederhana. Lalu di Variabel (K-8), kamu akan belajar menyimpan macam-macam data dan menggantinya dengan cara yang lebih pintar. Semuanya tumbuh dari satu ide yang sudah kamu kuasai hari ini: kotak bernama yang isinya bisa berganti.

::: check
Q: Isi kotak "Koinku" tadinya 3, lalu Nina menggantinya menjadi 5. Kalau kita melihat kotak itu sekarang, angka berapa yang kita temukan? Ke mana angka 3?
A: Kita menemukan angka 5, isi yang paling baru. Angka 3 sudah tidak ada di kotak karena sudah diganti.
Q: Bolehkah kotak bernama "Hewan" berisi kata "kucing" hari ini dan kata "kelinci" besok? Mengapa?
A: Boleh. Nama kotak tetap "Hewan", tapi isinya bebas diganti kapan saja. Yang selalu tetap adalah namanya, bukan isinya.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_reading_intro_en_v2', 'k5_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Step Lists and Loops: Your First Real Algorithms', 'Have you ever taught someone the rules of your favorite game, or shown a little cousin how to feed a pet? If you have, you were already doing computer science. Every "first do this, then do that" list you make is an algorithm — and today you''ll learn a trick that makes algorithms shorter and smarter.

## The Big Idea: Sequences and Loops

An **algorithm** is a list of steps so clear and so exact that anyone — even a robot — could follow it and get the same result.

You already know the first rule of algorithms: **order matters**. Steps that happen one after another, in order, are called a **sequence**. Sock on before shoe: great. Shoe before sock: disaster.

Here is the new idea. Sometimes an algorithm asks you to do the *same thing* again and again. Instead of writing that step over and over, you can wrap it in a **loop**. A loop is an instruction that says: "repeat these steps."

Loops don''t change what happens. They just make the algorithm shorter and easier to read — like saying "clap 10 times" instead of writing the word *clap* ten times.

## Try It: Feed the Class Goldfish

Imagine your teacher picks you to feed Bubbles, the class goldfish. Here is one algorithm:

1. Open the food jar.
2. Shake one tiny pinch into the tank.
3. Shake one tiny pinch into the tank.
4. Shake one tiny pinch into the tank.
5. Close the jar.

It works, but steps 2, 3, and 4 are exactly the same. Time for a loop:

1. Open the food jar.
2. Repeat 3 times: shake one tiny pinch into the tank.
3. Close the jar.

Now **trace** it — act it out in your head. Open the jar. Loop trip 1: pinch. Trip 2: pinch. Trip 3: pinch. Close the jar. Bubbles still gets exactly three pinches. Same result, shorter list. When you compare two algorithms like this and pick the better one, you are doing real computer science.

::: check
Q: In the loop version of the goldfish algorithm, how many pinches of food land in the tank?
A: Three. The loop repeats the pinch step 3 times, so it''s pinch, pinch, pinch — exactly like the long version.
Q: What does a loop do in an algorithm?
A: It repeats one or more steps a set number of times, so you don''t have to write the same step over and over. It doesn''t change the result — it just makes the list shorter.
:::

Ready for more? In the deeper read, you''ll trace a trickier loop that mixes walking and turning — and dodge the number one trap that catches loop beginners.', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_diagram_en_v2', 'k5_algorithms', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'One Picture of a Loop at Work', 'An algorithm can be drawn as a picture, where boxes are steps and arrows show which step comes next. This diagram shows a loop for watering the classroom plants — following the arrows with your finger is the same as tracing the algorithm.

```
            +---------------------+
            |        START        |
            +---------------------+
                       |
                       v
            +---------------------+
   +------->|   Water one plant   |
   |        +---------------------+
   |                   |
   |                   v
   |        +---------------------+
   |  yes   |  Any thirsty plants |
   +--------|  left to water?     |
            +---------------------+
                       |
                       | no
                       v
            +---------------------+
            |        DONE         |
            +---------------------+
```

Legend

- Box with words = one step (a single instruction)
- Box ending in "?" = a question the algorithm asks
- Arrows pointing down (v) = go to the next step
- The arrow marked "yes" going back up = the loop
- The path marked "no" = leave the loop and finish

How to read it

1. Begin at the START box at the top.
2. Follow the arrow down and do the step: water one plant.
3. At the question box, check: any thirsty plants left?
4. If yes, ride the "yes" arrow back up and water the next plant — that''s one more trip around the loop.
5. If no, drop down to DONE. The algorithm stops.

::: tip
Keep count on your fingers while you trace: raise one finger for each trip around the loop. If there were 4 thirsty plants, you should have exactly 4 fingers up when you reach DONE — if not, trace again and find where you slipped.
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_audio_en_v2', 'k5_algorithms', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Sequences and Loops, from Handshakes to Jumping Jacks', NULL, NULL, 'Have you ever made up a secret handshake with a friend? Maybe it goes fist bump, then high five, then wiggle your fingers like a jellyfish. If your friend does the jellyfish first and the fist bump last, it is not your handshake anymore. That is because a handshake is really a list of steps in an exact order. In computer science, we call a list like that an algorithm, and steps done one after another are called a sequence.

You already know that the order of steps matters. This year there is a new trick to learn: spotting steps that repeat, and folding them into a loop. A loop is a shortcut that says, do these steps again and again, a certain number of times.

Here is an example. Imagine your gym teacher wants you to warm up with two jumping jacks and one toe touch, five times in a row. She could call out fifteen separate moves, one at a time. That would take forever. Instead she just says, repeat five times: two jumping jacks, then one toe touch. That one sentence is a loop, and it holds all fifteen moves inside it.

Now let''s trace it, which means acting it out carefully in our heads. Trip one around the loop: jack, jack, toe touch. Trip two: jack, jack, toe touch. Keep going until you finish trip five. If you count everything up, you did ten jumping jacks and five toe touches. Tracing like this is how you check an algorithm before you trust it, the same way you might taste soup before serving it to your family.

So remember three things. An algorithm is an exact, ordered list of steps. A sequence means the steps happen one after another, in order. And a loop repeats steps so you do not have to say them over and over.

Here is your recap question. Suppose an algorithm says, repeat three times: touch your head, then clap two times. How many claps happen in total?

The answer is six. Each trip around the loop has two claps, and you go around three times. Two claps, three trips, six claps. Nice tracing!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_reading_deep_en_v2', 'k5_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Tracing Loops Like a Detective', 'Quick recap: an algorithm is an exact, ordered list of steps, and a loop is a shortcut that repeats steps. Now let''s trace a loop that has more than one step inside it — that''s where things get interesting.

## Worked Example: Walking a Square

Pretend the playground is covered in chalk tiles. Here is the algorithm:

1. Stand on the START tile, facing north.
2. Repeat 4 times: walk 4 steps forward, then turn right.
3. Shout "Done!"

Notice the loop holds **two** steps bundled together: *walk*, then *turn*. To trace it, we act out every trip around the loop, one at a time:

| Trip | What you do | Now facing |
| --- | --- | --- |
| 1 | walk 4 steps north, turn right | east |
| 2 | walk 4 steps east, turn right | south |
| 3 | walk 4 steps south, turn right | west |
| 4 | walk 4 steps west, turn right | north |

After trip 4, the loop is finished. You are back on the START tile, facing north again — you walked a perfect square! Then step 3 runs once, and you shout "Done!" Tracing every trip like this is how you *prove* an algorithm works before you trust it.

## The Trap That Catches Almost Everyone

::: misconception
Wrong idea: "Repeat 4 times: walk, then turn" means you do all the walking first (walk, walk, walk, walk) and all the turning after (turn, turn, turn, turn).
The truth: a loop repeats the whole bundle of steps, in order, on every single trip around. Each trip is walk THEN turn. If you did all the walks first, you would march straight off the playground instead of walking a square!
:::

When you trace a loop, say the steps for each trip out loud: "Trip 1: walk, turn. Trip 2: walk, turn..." That habit keeps the bundle together and catches mistakes fast.

## Where This Takes You

The skills you just used — designing step lists, folding repeats into loops, and tracing to check your work — are exactly what you''ll need when you start programming with blocks or code in middle school. Comparing two algorithms for the same job and choosing the better one is such an important skill that it has its own official name in school standards (CSTA 1B-AP-08). And tracing transfers far beyond computers: it''s how you double-check a recipe, a game plan, or directions to a friend''s house before anything goes wrong.

::: check
Q: Trace this algorithm: "Repeat 3 times: hop 2 times, then clap once." How many hops and how many claps happen in total?
A: 6 hops and 3 claps. Each trip around the loop is hop, hop, clap — and there are 3 trips.
Q: One algorithm has "stack a chair" written 10 times in a row. Another says "Repeat 10 times: stack a chair." Do they end with the same number of stacked chairs, and which algorithm is better?
A: Both stack exactly 10 chairs — the result is identical. The loop version is better because it''s shorter, easier to read, and easier to change: if you need 20 chairs tomorrow, you only change one number.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_reading_intro_id_v2', 'k5_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Algoritma Makin Pintar dengan Perulangan', 'Bayangkan kamu menitipkan kucing kesayanganmu kepada teman selama liburan. Supaya kucingmu tetap senang, kamu menulis daftar langkah: apa saja yang harus dilakukan, dan urutannya bagaimana. Daftar langkah yang jelas dan berurutan seperti itu punya nama keren: **algoritma** — dan hari ini kamu akan belajar membuatnya jadi lebih pintar lagi.

## Ide Besar: Urutan Rapi Ditambah Perulangan Cerdas

Di kelas sebelumnya, kamu sudah tahu bahwa algoritma adalah daftar langkah yang urut dan jelas. Sekarang kita naik satu tingkat dengan dua kemampuan baru:

1. **Merancang** algoritma sendiri, bukan hanya mengikuti yang sudah ada.
2. **Mengenali perulangan (loop)** — bagian langkah yang dikerjakan berulang-ulang.

Perulangan itu seperti tombol ajaib. Daripada menulis langkah yang sama berkali-kali, cukup tulis satu kali lalu tambahkan kata "ulangi ... kali". Algoritmamu jadi lebih pendek, tetapi hasilnya tetap sama persis. Kemampuan menyusun dan membandingkan algoritma seperti ini adalah bagian dari standar belajar AP-K5-1.

Ada satu lagi kemampuan penting: **menelusuri** algoritma. Artinya, membaca langkah demi langkah sambil membayangkan hasilnya, seperti detektif yang mengikuti jejak. Dengan menelusuri, kamu bisa menemukan kesalahan sebelum algoritmanya dijalankan sungguhan.

## Contoh Kecil: Menyiram Bunga di Teras

Misalnya kamu diminta menyiram 3 pot bunga di teras. Versi panjangnya begini:

1. Ambil alat penyiram.
2. Siram pot pertama.
3. Siram pot kedua.
4. Siram pot ketiga.
5. Kembalikan alat penyiram.

Perhatikan langkah 2, 3, dan 4 — sebenarnya sama, hanya potnya yang berganti. Kita bisa merapikannya dengan perulangan:

1. Ambil alat penyiram.
2. Ulangi 3 kali: siram satu pot, lalu pindah ke pot berikutnya.
3. Kembalikan alat penyiram.

Lima langkah menjadi tiga, dan semua bunga tetap kebagian air! Coba telusuri sendiri: putaran pertama menyiram pot 1, putaran kedua pot 2, putaran ketiga pot 3. Pas, tidak ada yang terlewat.

::: check
Q: Apa keuntungan menulis "Ulangi 3 kali: siram satu pot" dibanding menulis langkah siram tiga kali berturut-turut?
A: Algoritma jadi lebih pendek dan mudah dibaca, tetapi hasilnya tetap sama karena langkahnya tetap dikerjakan tiga kali.
Q: Kalau langkah "Ambil alat penyiram" dipindah ke urutan paling akhir, apa yang terjadi?
A: Algoritmanya gagal — kita disuruh menyiram padahal belum memegang alat penyiram. Urutan langkah sangat penting.
:::

Di bacaan berikutnya, kita akan menelusuri sebuah algoritma langkah demi langkah seperti detektif sungguhan — siapkan kaca pembesarmu!', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_diagram_id_v2', 'k5_algorithms', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Alur Perulangan: Sampai Meja Kosong', 'Algoritma dengan perulangan bisa digambar sebagai peta alur. Diagram di bawah ini menunjukkan algoritma merapikan buku: memasukkan buku ke tas satu per satu sampai meja benar-benar kosong.

```
             +-----------+
             |   MULAI   |
             +-----+-----+
                   |
                   v
        +--------------------+
  +---->|  Masih ada buku    |
  |     |  di atas meja?     |
  |     +-----+--------+-----+
  |           |        |
  |         [YA]    [TIDAK]
  |           v        v
  |  +--------------+ +---------+
  |  | Masukkan satu| | SELESAI |
  |  | buku ke tas  | +---------+
  |  +------+-------+
  |         |
  +---------+
```

Legend:

- Kotak: satu langkah atau satu pertanyaan dalam algoritma.
- Panah (v, >, dan garis |): jalur yang harus diikuti saat membaca.
- [YA] / [TIDAK]: dua kemungkinan jawaban dari kotak pertanyaan.
- Panah yang berbelok naik kembali ke kotak pertanyaan: itulah perulangan (loop).

Cara membacanya:

1. Mulai dari kotak MULAI, lalu ikuti panah ke bawah.
2. Kamu tiba di kotak pertanyaan: "Masih ada buku di atas meja?"
3. Jika jawabannya YA, masukkan satu buku ke tas, lalu ikuti panah yang naik kembali ke pertanyaan — itu satu putaran perulangan.
4. Setiap putaran, jumlah buku di meja berkurang satu, jadi perulangan pasti akan berhenti.
5. Jika jawabannya TIDAK, ikuti panah ke kotak SELESAI. Meja bersih, semua buku ada di tas!

::: tip
Kalau bingung membaca peta alur, letakkan jarimu di kotak MULAI dan geser mengikuti panah sambil menghitung putaran. Misalnya dengan 3 buku, jarimu akan melewati kotak "Masukkan satu buku ke tas" tepat 3 kali sebelum sampai di SELESAI.
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_audio_id_v2', 'k5_algorithms', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Perulangan, Rahasia Algoritma yang Ringkas', NULL, NULL, 'Halo! Hari ini kita akan mengobrol tentang algoritma, yaitu daftar langkah yang urut dan jelas untuk menyelesaikan sesuatu. Sebenarnya kamu sudah sering membuat algoritma tanpa sadar. Waktu kamu menjelaskan cara bermain petak umpet kepada teman baru, kamu sedang menyusun algoritma dengan kata-katamu sendiri.

Nah, sekarang ada ide baru yang seru, namanya perulangan, atau sering disebut loop. Perulangan dipakai kalau ada langkah yang harus dikerjakan berkali-kali. Daripada menyebut langkah yang sama berulang-ulang sampai bosan, kita cukup mengatakan, ulangi sekian kali, lalu sebutkan langkahnya satu kali saja.

Ayo kita coba dengan sebuah contoh. Bayangkan kamu membantu melipat empat helai baju dari jemuran. Versi panjang algoritmanya begini. Ambil baju pertama, lipat, taruh di tumpukan. Ambil baju kedua, lipat, taruh di tumpukan. Ambil baju ketiga, lipat, taruh di tumpukan. Ambil baju keempat, lipat, taruh di tumpukan. Panjang sekali, padahal langkahnya itu-itu saja.

Sekarang dengarkan versi pintarnya. Ulangi empat kali. Ambil satu baju, lipat dengan rapi, lalu taruh di tumpukan. Selesai. Hasilnya sama persis, tetapi algoritmanya jauh lebih singkat dan mudah diingat.

Supaya yakin algoritmanya benar, kita bisa menelusurinya, artinya mengikuti langkahnya satu per satu di dalam kepala. Putaran pertama, baju pertama terlipat. Putaran kedua, baju kedua terlipat. Putaran ketiga, baju ketiga. Putaran keempat, baju keempat. Empat putaran, empat baju rapi, tidak ada yang terlewat. Menelusuri seperti ini membantumu menemukan kesalahan sebelum algoritma benar-benar dijalankan.

Oh iya, satu hal penting. Setiap perulangan harus punya aturan berhenti yang jelas, misalnya ulangi empat kali, atau ulangi sampai keranjang cucian kosong. Tanpa aturan berhenti, perulangan akan berjalan terus tanpa akhir, dan itu bisa bikin kacau.

Sebelum kita tutup, coba jawab pertanyaan ini. Kalau kamu ingin menulis langkah pantulkan bola sebanyak sepuluh kali dalam sebuah algoritma, bagaimana cara menulisnya dengan perulangan? Coba pikirkan sebentar. Jawabannya, ulangi sepuluh kali, pantulkan bola. Satu kalimat pendek, sepuluh pantulan. Itulah kekuatan perulangan. Sampai jumpa di petualangan algoritma berikutnya!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_algorithms_reading_deep_id_v2', 'k5_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menelusuri Algoritma Langkah demi Langkah', 'Algoritma adalah daftar langkah yang urut dan jelas, dan perulangan membuatnya lebih ringkas tanpa mengubah hasil. Sekarang saatnya berlatih menelusuri algoritma langkah demi langkah, persis seperti komputer menjalankannya.

## Contoh Lengkap: Robot Pembagi Kue

Bayangkan sebuah robot bertugas membagikan kue kepada 4 teman di kelompokmu: Sari, Bima, Tono, dan Rara. Ini algoritmanya:

1. Ambil piring berisi 4 kue.
2. Ulangi 4 kali: ambil satu kue dari piring, lalu berikan kepada teman berikutnya yang belum kebagian.
3. Ucapkan "Selamat makan!"

Mari kita telusuri. Aturan mainnya: ikuti langkah persis seperti tertulis, jangan menebak-nebak.

| Putaran | Kue tersisa di piring | Teman yang menerima |
| --- | --- | --- |
| 1 | 3 kue | Sari |
| 2 | 2 kue | Bima |
| 3 | 1 kue | Tono |
| 4 | 0 kue | Rara |

Setelah putaran keempat, hitungan "ulangi 4 kali" selesai, jadi robot lanjut ke langkah 3 dan berkata "Selamat makan!" Piring kosong, semua teman kebagian, tidak ada yang dapat dua kali. Algoritmanya terbukti berhasil — dan kita membuktikannya dengan penelusuran, bukan dengan menebak.

Sekarang pikirkan: bagaimana kalau temannya 6 orang? Kamu tidak perlu menulis ulang semuanya. Cukup siapkan 6 kue dan ganti angkanya menjadi "ulangi 6 kali". Itulah kekuatan merancang algoritma dengan perulangan: mudah diubah untuk masalah yang lebih besar.

## Awas, Jebakan Pikiran!

::: misconception
Keliru: "Kalau ada perulangan, kita tidak perlu memikirkan kapan berhenti — nanti juga berhenti sendiri."
Yang benar: setiap perulangan butuh aturan berhenti yang jelas, misalnya "ulangi 4 kali" atau "ulangi sampai piring kosong". Coba bayangkan algoritma "ulangi: tuangkan air ke gelas" tanpa aturan berhenti — airnya akan meluber ke mana-mana! Jadi, setiap kali merancang perulangan, selalu tanyakan pada dirimu: berhentinya kapan?
:::

## Ke Mana Ilmu Ini Membawamu

Kemampuan merancang dan menelusuri algoritma adalah bekal utamamu untuk jenjang berikutnya. Saat nanti kamu mulai menyusun program dengan blok kode, perulangan yang hari ini kamu tulis dengan kata-kata akan berubah menjadi blok "ulangi" yang bisa dijalankan komputer sungguhan. Kebiasaan menelusuri langkah demi langkah juga akan menjadi senjatamu untuk menemukan kesalahan di program apa pun. Bahkan di luar komputer, kamu jadi lebih jago menyusun rencana yang rapi — dari jadwal piket kelas sampai strategi permainan.

::: check
Q: Sebuah algoritma berbunyi "Ulangi 5 kali: masukkan satu kelereng ke toples." Kalau toples awalnya sudah berisi 2 kelereng, berapa isinya setelah algoritma selesai?
A: 7 kelereng. Telusuri saja: dari 2 menjadi 3, 4, 5, 6, lalu 7 — perulangan menambahkan tepat 5 kelereng.
Q: Tulis ulang langkah "lompat, tepuk, lompat, tepuk, lompat, tepuk" menggunakan perulangan.
A: "Ulangi 3 kali: lompat, lalu tepuk." Pasangan lompat-tepuk muncul tiga kali, jadi itulah bagian yang diulang.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_reading_intro_en_v2', 'k5_control', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Loops and Ifs: Two Superpowers for Your Programs', 'Think about your favorite video game. The background music plays again and again, your character jumps *only* when you press a button, and coins get collected every single time you touch one. Somebody taught the computer to do all of that — and they used two amazing tools you are about to learn: **loops** and **conditionals**.

## The Big Idea: Repeat and Decide

You already know that an **algorithm** is a list of exact steps. Now your step-lists get two superpowers:

- A **loop** says: *do these steps again and again.* Instead of writing "clap, clap, clap, clap, clap," you can write "repeat 5 times: clap." Shorter — and the computer never loses count.
- A **conditional** (an **if**) says: *only do this step when something is true.* Like "**if** it is your birthday, wear the birthday crown." On regular days, that step just gets skipped.

When you follow the steps one at a time, exactly like a computer would, that is called **tracing**. Tracing is like being the computer for a minute — it is the best trick for figuring out what a program will really do.

## A Worked Example: The Plant-Watering Program

Your class has 4 plants on the windowsill. Here is a program for taking care of them:

```
1. Pick up the watering can.
2. Repeat 4 times (once per plant):
     a. Touch the soil with one finger.
     b. If the soil feels dry,
        pour in one small cup of water.
3. Put the watering can back.
```

Now let''s trace it. Pretend that today the soil is: **dry, wet, dry, wet**.

1. You pick up the can.
2. **Turn 1:** touch the soil — dry! The *if* is true, so you pour water.
3. **Turn 2:** touch the soil — wet. The *if* is false, so you skip the pouring and move on.
4. **Turn 3:** dry again — pour water.
5. **Turn 4:** wet — skip.
6. The loop has run 4 times, so it stops. You put the can back.

Notice something cool: the loop ran **4** times, but the watering only happened **2** times. The loop decides *how many turns* there are. The *if* decides *what happens on each turn*.

::: check
Q: In the plant program, what job does the loop do?
A: It makes the touch-and-check steps repeat 4 times, once for each plant, without writing them out 4 separate times.
Q: On turn 2 the soil feels wet. What does the program do next?
A: The if is false, so it skips the pouring step and goes on to the next turn of the loop.
:::

Ready for more? In the next reading you will trace a clean-up robot turn by turn and discover the sneaky mistake almost everyone makes with ifs.', NULL, NULL, 5, 0.3, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_diagram_en_v2', 'k5_control', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Sock-Sorting Robot: Follow the Path', 'A program is like a path the computer walks, and loops and ifs are the places where the path bends or circles back. This map shows a robot sorting a pile of socks.

```
            +-----------+
            |   START   |
            +-----+-----+
                  |
                  v
       +--------------------+
  +--->| Any socks in pile? |--no--> +------+
  |    +---------+----------+        | STOP |
  |              | yes               +------+
  |              v
  |      +---------------+
  |      | Take one sock |
  |      +-------+-------+
  |              |
  |              v
  |       +--------------+     +----------------+
  |       | Is it dirty? |-no->| Put in drawer  |
  |       +------+-------+     +--------+-------+
  |              | yes                  |
  |              v                      |
  |      +----------------+             |
  |      | Put in laundry |             |
  |      +-------+--------+             |
  |              |                      |
  +--------------+----------------------+
```

**Legend**

- **Boxes with plain words** (like "Take one sock") are action steps — the robot just does them.
- **Boxes with a question** are decisions (ifs) — you must leave on the *yes* path or the *no* path.
- **Arrows and lines** show the direction the computer travels.
- **The tall line on the far left** carries you back up to the first question — that circling path is the **loop**.
- **START** and **STOP** mark where the program begins and ends.

**How to read it**

1. Put your finger on START and slide down to the first question: "Any socks in pile?"
2. If yes, take one sock and slide down to the next question: "Is it dirty?"
3. Dirty sock? Follow the *yes* path into the laundry. Clean sock? Take the *no* path to the drawer.
4. Either way, follow the line down, across to the left, and back **up** to "Any socks in pile?" — that is one full trip around the loop.
5. Keep circling until the pile is empty. Then the *no* arrow finally fires, and you land on STOP.

::: tip
Try it for real! Grab 5 socks, put your finger on START, and walk the map once for each sock. If you can predict where every sock will end up before your finger gets there, you are officially tracing like a computer.
:::', NULL, NULL, 3, 0.4, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_audio_en_v2', 'k5_control', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Repeat and Decide: How Programs Flow', NULL, NULL, 'Here is something fun to notice: you already think like a programmer every single day. Let me show you what I mean.

Computer programs are lists of instructions, and those lists have two special powers. The first power is the loop. A loop tells the computer to do something again and again. Imagine your gym teacher says, do ten jumping jacks. She does not say jump, jump, jump, ten times in a row. She says it once, with a number. That is a loop: repeat ten times, do a jumping jack. Loops save us from saying the same step over and over, and the computer never loses count.

The second power is the conditional, which most coders just call an if. An if tells the computer, only do this step when something is true. Think about getting ready for school. If it is raining, you put on rain boots. If it is sunny, you do not. The instruction is always there, waiting, but it only happens when the condition is true.

Now let''s put both powers together in one little program for getting ready. Step one: repeat three times, put one book in your backpack. Step two: if it is raining, pack your umbrella. Step three: walk out the door. Suppose today is sunny. Let''s trace the program, which means we follow it exactly like a computer would. Book one goes in. Book two goes in. Book three goes in. The loop has run three times, so it stops. Next comes the umbrella step. Is it raining? No. So we skip it. Skipping is not a mistake. It is the if doing its job. Finally, we walk out the door, and the program is done.

So remember: the loop controlled how many times something happened. The if controlled whether something happened at all. That is the difference between them, and it is the heart of every program ever written.

Here is your question. A program says: repeat four times, hop once. Then it says: if your shoelace is untied, tie it. Your shoelaces are already tied. How many hops do you do, and do you stop to tie your shoes?

The answer: you hop four times, because the loop says repeat four times. And you skip the shoe-tying step completely, because the condition is false. Nice work. For a minute there, you were the computer.', 4, 0.45, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_reading_deep_en_v2', 'k5_control', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Be the Computer: Tracing Loops and Ifs', 'Quick recap: a **loop** repeats steps so you don''t have to write them over and over, and an **if** runs a step only when its condition is true. Tracing means following the steps exactly like the computer would — no guessing, no skipping ahead.

## Worked Example: The Clean-Up Robot

After art class, 4 things are left on the floor. Imagine a little robot with this program:

```
1. Repeat 4 times:
     a. Pick up the next item.
     b. If the item is trash,
        drop it in the recycling bin.
     c. If the item is NOT trash,
        put it in the lost-and-found box.
2. Say "All done!"
```

Today the floor has: a ripped paper scrap, a blue glove, an empty juice pouch, and a pencil. Let''s be the robot and trace every turn:

| Turn | Item | Trash? | What the robot does |
| --- | --- | --- | --- |
| 1 | ripped paper | yes | drops it in the recycling bin |
| 2 | blue glove | no | puts it in the lost-and-found box |
| 3 | juice pouch | yes | drops it in the recycling bin |
| 4 | pencil | no | puts it in the lost-and-found box |

After turn 4, the loop has repeated 4 times, so it ends. The robot moves to step 2 and says "All done!"

Look closely: the robot followed the *same* instructions on every turn, but it did *different things*, because the ifs checked each item. That is the whole magic of control structures — one short program can handle lots of different situations.

## The Mix-Up Almost Everyone Makes

::: misconception
Wrong idea: "Every step written in the program always happens."
The truth: steps inside an **if** only happen when the condition is true. On turn 2, the robot never touched the recycling bin — not because that step is broken, but because "the item is trash" was false for the glove. A skipped step is not a mistake. Skipping is the if doing its job.
:::

A good trace shows exactly which steps ran and which were skipped. If a program ever does something surprising, trace it turn by turn — the surprise is almost always hiding inside an if, or at the moment a loop stops.

## Where This Takes You

Creating programs with loops and ifs, and tracing what they do, is the exact skill named in the CSTA 1B-AP-10 standard — and it is the doorway to real coding. Every game, app, and website you have ever used is built from these same two moves: repeat and decide. When you start building in a block-coding tool, or later typing real code, the blocks will have new names, but the thinking will be the thinking you practiced here. Loops and ifs also stack: soon you will put ifs inside loops and loops inside ifs to build bigger, smarter programs.

::: check
Q: A program says: repeat 3 times — take a card; if the number on it is even, clap once. The cards are 2, 5, and 8. How many turns does the loop take, and how many claps happen?
A: The loop takes 3 turns (one per card), but there are only 2 claps — for 2 and 8. On the turn with 5, the if is false, so the clap is skipped.
Q: A friend traces the clean-up robot and says, "Step c is broken — it didn''t run on turn 1!" What do you tell them?
A: Nothing is broken. Step c only runs when the item is NOT trash. On turn 1 the item was trash, so the robot skipped step c on purpose.
:::', NULL, NULL, 8, 0.6, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_reading_intro_id_v2', 'k5_control', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Ulangi dan Pilih: Dua Kata Ajaib dalam Program', 'Pernahkah kamu bermain lompat tali sambil menghitung "satu, dua, tiga..." berulang-ulang? Atau memilih memakai jas hujan karena langit mendung? Tanpa sadar, kamu sudah memakai dua jurus andalan para pembuat program komputer: **mengulang** dan **memilih**.

## Ide Besar: Program Bisa Mengulang dan Memilih

Kamu sudah tahu bahwa algoritma adalah daftar instruksi yang urut dan jelas. Sekarang kita tambahkan dua kata ajaib supaya daftar instruksi kita jadi lebih pintar:

- **ULANGI** (para programmer menyebutnya *loop* atau perulangan): menyuruh beberapa langkah dikerjakan berkali-kali tanpa harus menulisnya berkali-kali.
- **JIKA ... MAKA ...** (disebut percabangan): membuat program bisa memilih langkah yang berbeda tergantung keadaan.

Jalan yang dilewati instruksi dari awal sampai akhir disebut **alur program**. Kadang alurnya berputar-putar karena ada ULANGI, kadang bercabang karena ada JIKA. Tugas kita adalah bisa **menelusuri** alur itu langkah demi langkah, seperti detektif yang mengikuti jejak.

### Contoh: Petugas Siram Tanaman

Bayangkan kamu menjadi petugas penyiram tanaman kelas. Ada 3 pot di dekat jendela. Ini daftar instruksinya:

```
1. Berdiri di depan pot pertama.
2. ULANGI sampai semua pot sudah dicek:
   a. JIKA tanahnya kering,
      MAKA siram dengan segelas air.
   b. JIKA TIDAK, jangan disiram.
   c. Pindah ke pot berikutnya.
3. Kembalikan gelas ke tempatnya.
```

Ayo kita telusuri bersama:

1. **Pot pertama:** tanahnya kering. Jawaban JIKA adalah *ya*, jadi kamu menyiramnya, lalu pindah.
2. **Pot kedua:** tanahnya masih basah. Jawaban JIKA adalah *tidak*, jadi langkah menyiram dilewati, dan kamu langsung pindah.
3. **Pot ketiga:** kering lagi. Kamu menyiramnya.
4. Semua pot sudah dicek, jadi perulangan berhenti. Kamu mengembalikan gelas. Selesai!

Lihat serunya: instruksi menyiram hanya ditulis **satu kali**, tetapi bisa dipakai untuk banyak pot. Dan berkat JIKA, pot yang masih basah tidak kebanjiran!

::: check
Q: Dalam contoh menyiram tanaman, apa gunanya kata ULANGI?
A: ULANGI membuat langkah cek-dan-siram dikerjakan lagi untuk setiap pot, tanpa perlu menulis instruksi yang sama berkali-kali.
Q: Pot kedua tanahnya masih basah. Apa yang terjadi ketika alur program sampai di langkah JIKA?
A: Jawaban pertanyaan "tanahnya kering?" adalah tidak, jadi langkah menyiram dilewati dan petugas langsung pindah ke pot berikutnya.
:::

Di bacaan berikutnya, kita akan menelusuri sebuah program lengkap langkah demi langkah — bersiaplah menjadi detektif alur program!', NULL, NULL, 5, 0.3, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_diagram_id_v2', 'k5_control', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Alur Program: Ke Mana Instruksi Berjalan?', 'Alur program lebih mudah dipahami kalau digambar sebagai peta. Peta di bawah ini menunjukkan program beres-beres kamar yang memakai perulangan dan percabangan sekaligus.

```
        +---------------------------+
        | MULAI: beres-beres kamar  |
        +---------------------------+
                      |
                      v
        +---------------------------+
  +---->| Masih ada mainan          |
  |     | di lantai?                |
  |     +---------------------------+
  |          | ya             | tidak
  |          v                v
  |  +--------------+    +---------+
  |  | Ambil satu   |    | SELESAI |
  |  | mainan       |    +---------+
  |  +--------------+
  |          |
  |          v
  |  +--------------+
  |  | Mainan itu   |
  |  | boneka?      |
  |  +--------------+
  |      | ya     | tidak
  |      v        v
  | +----------+ +----------+
  | | Taruh di | | Taruh di |
  | | rak      | | kotak    |
  | +----------+ +----------+
  |      |            |
  +------+------------+
```

Legend

- Kotak = satu langkah atau satu pertanyaan dalam program.
- Garis dan tanda v = arah jalan alur program.
- Tulisan "ya" dan "tidak" = dua cabang jawaban pertanyaan JIKA.
- Garis panjang di tepi kiri = jalan pulang perulangan, kembali ke pertanyaan pertama.
- MULAI dan SELESAI = titik awal dan titik akhir program.

Cara membaca peta ini:

1. Mulailah dari kotak MULAI, lalu ikuti garis ke bawah.
2. Kamu tiba di pertanyaan "Masih ada mainan di lantai?" — inilah gerbang perulangan.
3. Jika jawabannya ya, ambil satu mainan, lalu masuk ke pertanyaan kedua: "Mainan itu boneka?"
4. Jawaban ya membawamu ke rak, jawaban tidak membawamu ke kotak. Inilah percabangan JIKA-MAKA.
5. Ikuti garis di tepi kiri naik ke atas, kembali ke pertanyaan pertama. Satu putaran selesai!
6. Ketika lantai sudah bersih, jawabannya tidak, dan alur berjalan ke SELESAI.

::: tip
Telusuri peta dengan ujung jari atau pensil, dan buat satu coretan penghitung setiap kali kamu melewati garis pulang di tepi kiri. Jumlah coretan = jumlah putaran perulangan. Cara ini juga ampuh untuk memeriksa program buatanmu sendiri sebelum dijalankan.
:::', NULL, NULL, 3, 0.4, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_audio_id_v2', 'k5_control', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cerita Robot yang Pandai Mengulang dan Memilih', NULL, NULL, 'Halo, teman belajar! Hari ini kita mengobrol tentang dua kata ajaib yang membuat program komputer menjadi pintar. Kata pertama adalah ulangi, dan kata kedua adalah jika maka.

Kamu sudah tahu bahwa program itu daftar instruksi yang urut. Tetapi kalau hanya urut saja, programnya kaku. Kata ulangi membuat beberapa langkah dikerjakan berkali-kali tanpa perlu ditulis berkali-kali. Para programmer menyebutnya loop atau perulangan. Sedangkan kata jika maka membuat program bisa memilih. Jika keadaannya begini, maka lakukan ini. Jika tidak, lakukan yang lain.

Ayo kita coba lewat permainan robot. Ajak seorang teman. Temanmu menjadi robot, dan kamu menjadi pembuat programnya. Kamu memberi instruksi begini: ulangi lima kali, majulah satu langkah, tetapi jika ada kursi tepat di depanmu, maka geser dulu ke kanan sebelum melangkah.

Sekarang kita telusuri jalannya. Putaran pertama, robot bertanya dalam hati, ada kursi di depanku? Tidak ada. Jadi dia maju satu langkah. Putaran kedua, dia bertanya lagi. Masih tidak ada. Maju lagi. Putaran ketiga, ternyata ada kursi! Karena jawabannya ya, robot geser ke kanan dulu, baru melangkah. Putaran keempat dan kelima, jalanan kosong, jadi robot maju dua kali lagi. Setelah lima putaran, hitungan ulanginya habis, dan robot berhenti.

Perhatikan hal penting ini. Pertanyaan tentang kursi itu tidak hanya ditanyakan sekali. Setiap putaran, robot bertanya lagi dari awal. Itulah sebabnya robot selamat dan tidak menabrak. Dia selalu memeriksa keadaan terbaru sebelum melangkah.

Kalau kamu bisa mengikuti jalannya instruksi seperti tadi, langkah demi langkah, itu namanya menelusuri alur program. Kemampuan ini seperti kekuatan super seorang detektif. Kamu bisa menebak apa yang akan dilakukan sebuah program, bahkan sebelum program itu dijalankan.

Sebelum kita selesai, coba jawab pertanyaan ini. Dalam permainan robot tadi, berapa kali pertanyaan tentang kursi itu ditanyakan? Pikirkan sebentar. Jawabannya lima kali, karena perulangan berputar lima kali, dan di setiap putaran pertanyaan jika selalu ditanyakan ulang. Hebat sekali! Sampai jumpa di petualangan belajar berikutnya.', 4, 0.45, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_control_reading_deep_id_v2', 'k5_control', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Jadi Detektif Program: Menelusuri Perulangan dan Percabangan', 'Program menjadi pintar berkat dua alat: perulangan (ULANGI) yang memutar langkah berkali-kali, dan percabangan (JIKA-MAKA) yang memilih jalan. Sekarang saatnya berlatih menelusuri alur program sampai tuntas.

## Menelusuri Program Robot Pemilah Kelereng

Bayangkan sebuah robot mainan yang tugasnya memilah kelereng dari toples ke dua kantong. Ini programnya:

```
Program: Robot Pemilah Kelereng
1. ULANGI 4 KALI:
   a. Ambil satu kelereng dari toples.
   b. JIKA kelerengnya biru,
      MAKA masukkan ke kantong biru.
   c. JIKA TIDAK,
      masukkan ke kantong merah.
2. Katakan "Selesai!"
```

Isi toples, dari atas ke bawah: biru, hijau, biru, kuning.

Cara menelusuri: **jadilah komputernya**. Kerjakan instruksi satu per satu, dan catat apa yang terjadi di setiap putaran. Tabel seperti ini sangat membantu:

| Putaran | Kelereng | Biru? | Masuk ke |
| --- | --- | --- | --- |
| 1 | biru | ya | kantong biru |
| 2 | hijau | tidak | kantong merah |
| 3 | biru | ya | kantong biru |
| 4 | kuning | tidak | kantong merah |

Setelah putaran ke-4, hitungan ULANGI habis. Alur program keluar dari perulangan, dan robot berkata "Selesai!". Hasil akhirnya: 2 kelereng di kantong biru, 2 kelereng di kantong merah.

Perhatikan hal penting ini: instruksinya **sama persis** di setiap putaran, tetapi hasilnya bisa **berbeda-beda**, karena jawaban pertanyaan JIKA berubah mengikuti kelereng yang diambil.

## Hati-Hati, Ini Sering Keliru

::: misconception
Keliru: "Pertanyaan JIKA di dalam perulangan hanya diperiksa satu kali, yaitu di putaran pertama. Kalau putaran pertama jawabannya ya, putaran berikutnya pasti ya juga."
Yang benar: setiap kali perulangan berputar, pertanyaan JIKA ditanyakan ulang dari awal. Pada program kelereng, robot bertanya "biru?" sebanyak empat kali — satu kali untuk setiap kelereng — dan jawabannya boleh berbeda di tiap putaran. Itulah yang membuat program bisa menyesuaikan diri dengan keadaan.
:::

Kalau kamu ragu, kembalilah ke tabel penelusuran: satu baris untuk satu putaran, dan kolom "Biru?" diisi ulang di setiap baris.

## Setelah Ini ke Mana?

Kemampuan membuat dan menelusuri program dengan perulangan dan percabangan — dalam kurikulum, inilah capaian AP-K5-2 — adalah bekal yang akan terus kamu pakai. Cara berpikir ini langsung terpakai saat kamu menyusun program balok di aplikasi seperti Scratch, mengatur gerak robot mainan, atau nanti menulis kode sungguhan di jenjang yang lebih tinggi. Bahkan di luar komputer, kamu jadi lebih jago merancang aturan permainan dan jadwal harian yang rapi.

::: check
Q: Sebuah program berbunyi: ULANGI 3 KALI: JIKA nomor putarannya ganjil, MAKA tepuk 1 kali; JIKA TIDAK, tepuk 2 kali. Berapa jumlah tepukan seluruhnya?
A: Putaran 1 ganjil (1 tepukan), putaran 2 genap (2 tepukan), putaran 3 ganjil (1 tepukan). Jumlah seluruhnya 4 tepukan.
Q: Apa bedanya "ULANGI 4 KALI" dengan "ULANGI SAMPAI toples kosong"?
A: ULANGI 4 KALI berputar tepat 4 kali lalu berhenti, berapa pun isi toplesnya. ULANGI SAMPAI toples kosong bisa berputar sedikit atau banyak — perulangan baru berhenti ketika keadaannya tercapai, yaitu saat tidak ada kelereng tersisa.
:::', NULL, NULL, 8, 0.6, '["k2_control", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_intro_en_v2', 'k5_modularity', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Name It Once, Use It Again and Again', 'Imagine you invented the perfect paper airplane. Every time a friend asks how to make one, you could explain all twelve folds again... or you could write the steps down once, give them a name like "Super Glider," and just say "follow Super Glider!" That trick — saving steps under a name so you can reuse them — is one of the most powerful ideas in all of computer science.

## The Big Idea: Name It, Reuse It, Fill in the Blank

You already know how to break a big job into smaller steps. The next move is to take a chunk of steps you use a lot, give it a **name**, and treat it like one single command. Computer scientists call this a **procedure**.

A procedure gets even more useful when you leave a **blank** in it — a spot you fill in with something different each time you use it. That blank is called a **parameter**.

And some procedures don''t just do something — they hand an answer back to you when they finish. That answer is called a **return value**.

- **Procedure**: a named list of steps you can reuse
- **Parameter**: the blank you fill in each time
- **Return value**: the answer the procedure hands back

### A Tiny Example: Count the Crayons

Say your teacher keeps asking you to count crayon boxes. Instead of figuring it out fresh every time, you could make a procedure:

**Count Crayons (which box?)**

1. Open the box named in the blank
2. Take the crayons out one at a time, counting as you go
3. Put them all back
4. Hand back the number you counted

Now "Count Crayons" works on ANY box. Monday: *Count Crayons (blue box)* — it hands back 24. Tuesday: *Count Crayons (art cart box)* — it hands back 61. Same steps every single time. Only the blank changes, and the answer comes back to whoever asked for it.

::: check
Q: What is the parameter in the Count Crayons procedure?
A: The blank "which box?" — you fill it in with a different box each time you use the procedure, but the steps stay the same.
Q: What is the return value, and who gets it?
A: The number of crayons counted. It goes back to whoever used the procedure, so they can use the answer for whatever they need next.
:::

Ready to watch a full procedure run from start to finish? The deeper read walks through one step by step.', NULL, NULL, 5, 0.3, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_diagram_en_v2', 'k5_modularity', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'How a Procedure Works Like a Machine', 'A procedure works a lot like a machine: something goes in the top, the same steps always run inside, and something useful comes out the bottom. Here is a smoothie machine drawn the computer science way.

```
      fruit  <-- parameter (what goes in)
        |
        v
+---------------------------+
| PROCEDURE: Make Smoothie  |
|---------------------------|
| 1. wash the fruit         |
| 2. chop the fruit         |
| 3. blend for 30 seconds   |
| 4. pour into a cup        |
+---------------------------+
        |
        v
    smoothie <-- return value (what comes out)
```

Legend

- **Box**: the procedure — a named, reusable list of steps
- **| and v (top)**: the arrow carrying the parameter INTO the procedure
- **| and v (bottom)**: the arrow carrying the return value back OUT
- **1. 2. 3. 4.**: the steps inside, which run in order and never change
- **<--**: points to the label explaining that part

How to read it

1. Start at the top. Pick any fruit — strawberry, banana, mango. That choice is the parameter.
2. Follow the arrow down: the fruit enters the procedure box.
3. Inside, steps 1 through 4 run in order, using whatever fruit came in.
4. Follow the bottom arrow: out comes the finished smoothie — the return value.
5. Change the fruit at the top and the SAME box hands back a different smoothie. Same steps, new result.

::: tip
When you plan your own procedure, sketch it as a machine first. Write what goes in at the top, the steps in the middle, and what comes back at the bottom. If you can''t say what goes in and what comes out, the procedure isn''t finished being designed yet.
:::', NULL, NULL, 3, 0.4, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_audio_en_v2', 'k5_modularity', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Pencil Sharpener Secret', NULL, NULL, 'Have you ever noticed that some machines at school do the same job over and over, and nobody ever has to teach them how? Today let''s talk about one of the biggest ideas in computer science, and it''s hiding inside the pencil sharpener on your teacher''s desk.

In computer science, a procedure is a list of steps that you write once, give a name, and then use again and again. But the really clever part is that a good procedure has two special features. It takes something in, and it gives something back.

Think about that pencil sharpener. You put in a dull pencil. The sharpener always does the same steps inside. It grips the pencil, spins the blade, shaves the wood, and stops. Then out comes a sharp pencil. Here''s the computer science way to say all that. The dull pencil you put in is called the parameter. It''s the part that can be different every time. You might put in a red pencil, a yellow pencil, or a short stubby pencil. The sharpener doesn''t care. Its steps never change. And the sharp pencil that comes back out? That''s called the return value. It''s the answer the procedure hands back to you when it''s done.

Now here''s why this matters. Imagine if you needed a different sharpener for every single pencil in your classroom. One machine for red pencils, one for blue, one for long ones, one for short ones. That would be silly. One machine handles them all, because the pencil is just the blank you fill in. Procedures work exactly the same way. Instead of writing brand new steps for every tiny change, you write the steps one time, leave a blank for the part that changes, and reuse those steps forever.

So the next time you sharpen a pencil, remember, you''re using a procedure. You give it a parameter, and it gives you back a return value.

Let''s finish with one quick question. In the pencil sharpener story, what is the parameter, and what is the return value? Take a second to think.

Here''s the answer. The parameter is the dull pencil you put in, because it can be different each time. The return value is the sharp pencil that comes back out, because that''s what the procedure hands back when it finishes its steps.', 4, 0.45, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_deep_en_v2', 'k5_modularity', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Parameters and Return Values in Action', 'Quick recap: a **procedure** is a named list of steps you can reuse, a **parameter** is the blank you fill in each time, and a **return value** is the answer the procedure hands back when it finishes.

## Worked Example: The Sandwich Procedure

It''s field trip day and you''re helping pack lunches for three friends. Amara wants peanut butter, Ben wants cheese, and Kai wants jam. Do you need three totally different instruction lists? Nope — the steps are almost identical. Only the filling changes. That''s the perfect job for one procedure with one parameter:

**Make Sandwich (filling)**

1. Put two slices of bread on the plate
2. Spread the *filling* on one slice
3. Press the second slice on top
4. Cut it in half
5. Wrap it up and hand back the wrapped sandwich

Now watch it run three times:

| Call | Blank filled with | Return value |
| --- | --- | --- |
| Make Sandwich (peanut butter) | peanut butter | wrapped PB sandwich |
| Make Sandwich (cheese) | cheese | wrapped cheese sandwich |
| Make Sandwich (jam) | jam | wrapped jam sandwich |

Trace the second call slowly. Step 1: bread on the plate. Step 2: the blank says *cheese*, so cheese gets spread. Steps 3, 4, 5: press, cut, wrap. The wrapped sandwich is the return value — it travels back to the lunch-packing line, where it goes straight into Ben''s lunchbox. You wrote the steps **once** and used them **three times**. That is modularity doing its job.

## The Mix-Up Most People Have

::: misconception
Wrong idea: "If the job is a little different each time — peanut butter one day, cheese the next — I have to write a whole new list of steps for each version."
Actually: you write ONE list and put a blank (a parameter) where the difference goes. The steps stay exactly the same every time; only what fills the blank changes. If you notice the steps themselves need to change, that changing part probably deserves its own separate procedure.
:::

## Where This Leads

Everything you practiced here transfers straight into real programming. In Scratch, procedures are called "My Blocks," and the little oval inputs you drag into them are parameters. In typed languages like Python, procedures are called functions, and "return" is an actual word that sends answers back. When you design a procedure by choosing its name, its blanks, and what it hands back, you are doing exactly what professional programmers do every day — and exactly what the CSTA 1B-AP-14 standard describes: creating procedures with parameters to organize your instructions and make them easier to reuse.

::: check
Q: Your friend writes a procedure called "Wrap Gift (paper color)". She uses it with red paper, then with blue paper. What stayed the same, and what changed?
A: The steps stayed exactly the same both times. Only the parameter changed — red first, then blue — so the return value, the wrapped gift, came out looking different each time.
Q: The procedure "Measure Plant (which plant)" hands back a height number. Why is handing the number back better than the measurer just remembering it in their head?
A: Because the return value travels back to whoever asked for it, so they can use it in their next step — like writing it on the class growth chart or comparing two plants to see which grew more.
:::', NULL, NULL, 8, 0.6, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_intro_id_v2', 'k5_modularity', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Prosedur: Mesin Instruksi yang Bisa Dipakai Berulang Kali', 'Pernah membantu membuat jus di dapur? Blender itu mesin yang pintar: masukkan mangga, keluarlah jus mangga; masukkan alpukat, keluarlah jus alpukat. Kamu tidak perlu membeli blender baru untuk setiap buah — satu mesin saja cukup. Nah, di dunia komputer ada "mesin" seperti itu juga. Namanya **prosedur**, dan hari ini kamu akan belajar membuatnya sendiri.

## Ide Besar: Satu Daftar Instruksi, Dipakai Berkali-kali

Waktu di kelas kecil dulu, kamu sudah belajar memecah tugas besar menjadi bagian-bagian kecil. Sekarang kita naik satu tingkat: bagian kecil itu kita beri **nama**, supaya bisa dipanggil kapan saja tanpa menulis ulang langkah-langkahnya. Daftar instruksi yang diberi nama itulah yang disebut *prosedur*.

Prosedur punya dua teman penting:

- **Parameter** — informasi yang *masuk* ke prosedur, seperti buah yang kamu masukkan ke blender. Parameter boleh berbeda-beda setiap kali prosedur dipanggil.
- **Nilai kembali (hasil)** — sesuatu yang *keluar* setelah prosedur selesai bekerja, seperti segelas jus yang siap diminum.

### Contoh: Prosedur "Buat Jus"

Coba ikuti daftar instruksi ini:

1. Terima satu jenis buah (ini parameternya!).
2. Kupas dan potong buah itu.
3. Masukkan potongan buah, air, dan sedikit gula ke blender.
4. Nyalakan blender selama 30 detik.
5. Tuang ke gelas, lalu serahkan gelasnya (ini nilai kembalinya!).

Sekarang kita panggil prosedurnya beberapa kali:

| Panggilan | Parameter | Hasil |
| --- | --- | --- |
| Buat Jus (mangga) | mangga | segelas jus mangga |
| Buat Jus (jambu) | jambu | segelas jus jambu |
| Buat Jus (alpukat) | alpukat | segelas jus alpukat |

Lihat betapa hematnya! Langkah 1 sampai 5 hanya ditulis **satu kali**, tetapi bisa dipakai untuk buah apa pun. Kalau suatu hari kamu menemukan cara memotong buah yang lebih cepat, kamu cukup memperbaiki langkah 2 di satu tempat — semua jus berikutnya langsung ikut lebih cepat.

::: check
Q: Apa yang berubah saat kamu menjalankan prosedur "Buat Jus" dengan buah yang berbeda?
A: Hanya bahannya, yaitu parameternya. Langkah-langkahnya tetap sama, tetapi hasil jusnya mengikuti buah yang dimasukkan.
Q: Mengapa lebih hemat membuat satu prosedur "Buat Jus" daripada menulis daftar instruksi baru untuk setiap buah?
A: Karena satu prosedur bisa dipakai berulang kali. Kita cukup mengganti parameternya tanpa menulis ulang semua langkah, dan kalau ada perbaikan, cukup diubah di satu tempat.
:::

Di bacaan berikutnya, kita akan membedah sebuah prosedur langkah demi langkah dan melihat jebakan yang paling sering membuat orang keliru.', NULL, NULL, 5, 0.3, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_diagram_id_v2', 'k5_modularity', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Mesin Prosedur: dari Parameter ke Hasil', 'Prosedur bisa digambarkan seperti mesin: sesuatu masuk dari atas, diolah di dalam kotak, lalu hasilnya keluar di bawah. Peta berikut menunjukkan prosedur "Mesin Salam" yang bisa menyapa siapa pun.

```
     PARAMETER masuk (contoh: nama teman)
                     |
                     v
       +------------------------------+
       |   PROSEDUR "MESIN SALAM"     |
       |   1. Terima sebuah nama      |
       |   2. Gabungkan kata "Halo,"  |
       |      dengan nama itu         |
       |   3. Serahkan sapaannya      |
       +------------------------------+
                     |
                     v
       NILAI KEMBALI keluar (sapaan jadi)

  Contoh pemakaian:
  "Sari" --> [MESIN SALAM] --> "Halo, Sari!"
  "Bima" --> [MESIN SALAM] --> "Halo, Bima!"
```

Legend:

- Kotak besar = prosedur, yaitu daftar instruksi yang diberi nama
- Panah (| dan v, atau -->) = arah jalannya informasi
- Tulisan dalam tanda kutip = nilai parameter yang masuk atau hasil yang keluar
- [MESIN SALAM] = cara singkat menuliskan panggilan prosedur

Cara membaca peta ini:

1. Mulai dari atas: parameter adalah informasi yang masuk, contohnya nama seorang teman.
2. Ikuti panah ke bawah menuju kotak besar — itulah prosedurnya, berisi tiga langkah yang selalu sama.
3. Di dalam kotak, nama yang masuk digabungkan dengan kata "Halo," sesuai instruksi.
4. Ikuti panah keluar di bawah kotak: itulah nilai kembali, yaitu sapaan yang sudah jadi.
5. Lihat dua baris contoh di bagian bawah: nama yang berbeda masuk ke mesin yang sama, dan sapaan yang berbeda pun keluar — tanpa mengubah isi kotak sedikit pun.

::: tip
Saat merancang prosedurmu sendiri, gambarlah kotaknya lalu tanyakan dua hal: "Apa yang masuk?" (parameter) dan "Apa yang keluar?" (nilai kembali). Kalau kedua jawaban itu jelas, prosedurmu hampir pasti mudah dipakai teman-temanmu.
:::', NULL, NULL, 3, 0.4, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_audio_id_v2', 'k5_modularity', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Ngobrol Santai tentang Prosedur, Parameter, dan Hasil', NULL, NULL, 'Hai! Hari ini kita akan ngobrol tentang salah satu trik paling hebat di dunia komputer. Namanya prosedur. Tenang saja, kamu sebenarnya sudah sering memakai trik ini di rumah tanpa sadar.

Bayangkan sore hari di rumahmu. Ayah minta dibuatkan teh manis, lalu tidak lama kemudian kakak juga minta. Kamu tahu cara membuatnya: siapkan gelas, masukkan kantong teh, tuang air hangat, tambahkan gula, aduk sampai rata, lalu serahkan gelasnya. Nah, daftar langkah itu, kalau kita beri nama, misalnya Buat Teh, akan menjadi sebuah prosedur. Prosedur adalah daftar instruksi yang diberi nama, supaya bisa dipakai berulang kali tanpa perlu diingat atau disusun ulang dari awal.

Sekarang bagian serunya. Ayah suka teh dengan satu sendok gula, tetapi kakak suka dua sendok. Apakah kamu perlu daftar langkah yang baru? Tidak perlu! Kamu cukup mengganti satu informasi kecil, yaitu jumlah sendok gulanya. Informasi yang masuk ke prosedur seperti itu disebut parameter. Langkah-langkahnya tetap sama persis. Yang berubah hanya isiannya.

Lalu apa yang muncul di akhir prosedur? Ada segelas teh manis yang siap kamu serahkan. Itulah yang disebut nilai kembali, atau hasil. Jadi ingat polanya: parameter masuk di awal, prosedur bekerja mengikuti langkah-langkahnya, lalu hasil keluar di akhir.

Kenapa ini penting? Karena programmer sungguhan bekerja seperti ini setiap hari. Mereka tidak menulis ulang instruksi yang sama ratusan kali. Mereka membuat satu prosedur yang rapi, memberinya nama yang jelas, lalu memanggilnya kapan pun dibutuhkan dengan parameter yang berbeda-beda. Programnya jadi rapi, pekerjaannya jadi cepat, dan kalau ada kesalahan, cukup diperbaiki di satu tempat saja.

Sebelum kita selesai, coba jawab pertanyaan ini. Kalau kamu menjalankan prosedur yang sama dua kali dengan parameter yang berbeda, apakah langkah-langkah prosedurnya ikut berubah? Pikirkan dulu sebentar. Jawabannya: tidak. Langkah-langkahnya tetap sama, seperti resep yang tidak pernah berubah. Yang berbeda hanyalah informasi yang masuk, yaitu parameternya, sehingga hasil yang keluar pun ikut menyesuaikan. Satu prosedur, banyak hasil. Itulah kekuatan modularitas.', 4, 0.45, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_deep_id_v2', 'k5_modularity', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Membedah Prosedur: Parameter Masuk, Hasil Keluar', 'Kamu sudah tahu ide besarnya: prosedur adalah daftar instruksi bernama yang bisa dipanggil berulang kali, dengan **parameter** sebagai informasi yang masuk dan **nilai kembali** sebagai hasil yang keluar. Sekarang kita bedah satu contoh sampai tuntas.

## Contoh Lengkap: Prosedur "Beri Makan"

Bayangkan kamu punya dua hewan peliharaan: kucing bernama Oyen dan ikan bernama Boni. Keduanya perlu makan, tetapi porsinya berbeda. Daripada mengingat dua daftar instruksi, kita buat SATU prosedur dengan DUA parameter.

**Prosedur: Beri Makan (nama hewan, jumlah sendok)**

1. Ambil mangkuk milik *nama hewan*.
2. Buka wadah makanan khusus *nama hewan*.
3. Masukkan makanan sebanyak *jumlah sendok* sendok ke mangkuk.
4. Letakkan mangkuk di tempat makan *nama hewan*.
5. Serahkan laporan: "mangkuk *nama hewan* terisi *jumlah sendok* sendok" — ini nilai kembalinya.

**Panggilan pertama: Beri Makan (Oyen, 2)**

- Langkah 1: ambil mangkuk milik Oyen.
- Langkah 2: buka wadah makanan kucing.
- Langkah 3: masukkan 2 sendok makanan.
- Langkah 4: letakkan mangkuk di pojok dapur, tempat makan Oyen.
- Langkah 5: laporannya — "mangkuk Oyen terisi 2 sendok".

**Panggilan kedua: Beri Makan (Boni, 1)**

Langkahnya sama persis; hanya isiannya yang berganti. Mangkuknya milik Boni, wadahnya makanan ikan, sendoknya cuma satu, dan laporannya — "mangkuk Boni terisi 1 sendok".

Perhatikan dua hal. Pertama, kita menulis langkah 1 sampai 5 hanya sekali, tetapi bisa memberi makan hewan mana pun. Kedua, nilai kembali itu berguna: ketika ibu bertanya, "Hewannya sudah makan belum?", kamu tinggal menyampaikan laporan dari langkah 5 — hasil sebuah prosedur bisa dipakai untuk langkah berikutnya.

## Awas, Ini Sering Keliru

::: misconception
Anggapan keliru: "Kalau parameternya berbeda, aku harus menulis ulang atau mengubah langkah-langkah prosedurnya."
Yang benar: langkah-langkah prosedur tidak pernah ditulis ulang. Parameter itu seperti kotak kosong di dalam instruksi yang diisi nilai baru setiap kali prosedur dipanggil. Beri Makan (Oyen, 2) dan Beri Makan (Boni, 1) menjalankan lima langkah yang sama persis — hanya isi kotaknya yang berbeda, sehingga hasilnya pun berbeda.
:::

Satu lagi yang sering tertukar: parameter dan nilai kembali. Cara mudah mengingatnya — parameter masuk *sebelum* prosedur bekerja, nilai kembali keluar *setelah* prosedur selesai.

## Ke Mana Ilmu Ini Membawamu

Kebiasaan membuat prosedur dengan parameter — salah satu tujuan belajar informatika di jenjangmu (standar AP-K5-4) — akan terus kamu pakai ke depannya. Saat bermain dengan aplikasi pemrograman visual, kamu bisa membuat balok instruksimu sendiri yang bekerja persis seperti prosedur ini. Nanti di jenjang berikutnya, prosedur akan kamu kenal dengan nama *fungsi*, dan cara berpikirnya tetap sama: apa yang masuk, apa langkahnya, apa yang keluar. Bahkan di luar komputer, kamu bisa merapikan jadwal piket kelas atau resep keluarga dengan pola yang sama.

::: check
Q: Prosedur "Buat Label Buku" punya dua parameter: nama pemilik dan nama pelajaran. Jika dipanggil dengan (Raka, Matematika) lalu (Sinta, IPA), apa yang sama dan apa yang berbeda dari kedua panggilan itu?
A: Langkah-langkah prosedurnya sama persis. Yang berbeda hanya isi parameternya, sehingga hasilnya dua label yang berbeda: label "Raka - Matematika" dan label "Sinta - IPA".
Q: Prosedur "Hitung Uang Tabungan" menerima parameter berupa isi celengan, lalu di akhir menyerahkan jumlah totalnya. Manakah nilai kembalinya, dan mengapa itu berguna?
A: Nilai kembalinya adalah jumlah total uang. Itu berguna karena hasilnya bisa dipakai untuk keputusan berikutnya, misalnya menentukan apakah tabungan sudah cukup untuk membeli barang yang diinginkan.
:::', NULL, NULL, 8, 0.6, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_intro_en_v2', 'k5_variables', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Variable Boxes: Numbers, Words, and Yes/No', 'Think about your favorite game. Somewhere, the computer is remembering your name, your score, and whether you won — all at the same time. It does that with variables, and today you''ll discover that these memory boxes come in different *types*, just like real boxes hold different kinds of stuff.

## One Box, One Label, One Thing Inside

You already know that a **variable** is like a box with a label on it, and the computer uses it to remember one thing. Here is the new part: different boxes hold different **types** of things.

- **Number boxes** hold numbers you can count with or do math on, like 7 or 250.
- **Word boxes** hold text, like a name: "Luna" or "Blue Team".
- **Yes/no boxes** hold only yes or no — perfect for questions like "Is the game over?"

Putting something into a box has a fancy name: **assignment**. And here is the golden rule of assignment: *a box holds exactly one thing.* When you assign a new value, the old value vanishes. It''s like erasing a mini whiteboard and writing something new.

One more secret: every box lives somewhere. A box made inside one part of a program belongs to that part, like a toy that stays in one room of your house. Programmers call this the variable''s **scope** — you''ll meet it properly in the deeper reading.

## Try It: The Virtual Pet

Follow this instruction list for a virtual pet program, one step at a time:

```
1. Make a box called petName. Put the word "Ziggy" in.
2. Make a box called treats. Put the number 5 in.
3. Make a box called isHungry. Put yes in.
4. Feed the pet: take the number out of treats,
   subtract 1, and put the answer back in.
5. Put no into isHungry. The old yes is gone.
```

After step 5, check the shelf: petName still says "Ziggy", treats now holds 4, and isHungry holds no. Three boxes, three different types, all remembered perfectly.

::: check
Q: What type of thing does the petName box hold — a number, a word, or a yes/no?
A: A word (text). It holds the pet''s name, "Ziggy".
Q: After feeding the pet once, what is inside the treats box, and where did the 5 go?
A: The box holds 4. The 5 is gone — assignment replaces the old value, because a box holds only one thing at a time.
:::

Ready for more? In the deeper reading you''ll run a whole relay-race scoreboard and find out exactly where variables live — and where they can''t be seen at all.', NULL, NULL, 5, 0.3, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_diagram_en_v2', 'k5_variables', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'A Map of Where Variable Boxes Live', 'Every variable box lives somewhere — some belong to the whole game, and some belong to just one small room inside it. This map shows both kinds at once.

```
GAME WORLD  (boxes the whole game can use)
+---------------------------------------------+
| [playerName | "Mia"]  <-- word box          |
| [totalStars | 12   ]  <-- number box        |
|                                             |
|   LEVEL 2 ROOM (boxes only this level uses) |
|   +--------------------------------+        |
|   | [keysFound | 3  ]   <-- number |        |
|   | [doorOpen  | yes]   <-- yes/no |        |
|   +--------------------------------+        |
+---------------------------------------------+
```

Legend:

- **[label | value]** — a variable box: its name on the left, the one thing it holds on the right
- **<--** — a note telling you the box''s type (word, number, or yes/no)
- **Outer border** — the whole game world, the biggest "room" a variable can live in (its scope)
- **Inner border** — Level 2''s own small room; its boxes exist only while that level is running

How to read the map:

1. Start at the outer border. Everything inside it belongs to the game world.
2. Find playerName and totalStars on the top shelf — any part of the game can use these two boxes.
3. Step into the Level 2 room. It has its own little shelf.
4. keysFound and doorOpen sit on that shelf, so only Level 2 can see them or change them.
5. When Level 2 ends, its room is cleaned out: those two boxes disappear, while playerName and totalStars stay safe outside.

::: tip
When you invent a variable, ask two quick questions: "What type of thing will it hold?" and "Which room really needs it?" Keep each box in the smallest room that works — your program stays tidy, and nothing gets changed by accident.
:::', NULL, NULL, 3, 0.4, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_audio_en_v2', 'k5_variables', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Lemonade Stand That Remembers', NULL, NULL, 'Hey there. Let''s spend a few minutes on variables, the little memory helpers inside every program. You already know the main trick: a variable is like a box with a label, and the computer uses it to remember one thing. Today we''re adding three big ideas. Boxes come in different types. Filling a box replaces what was there before. And every box lives in its own place.

First, types. Some boxes hold numbers, like nine or two hundred. Some boxes hold words, like a name. And some hold just a yes or a no, which is perfect for questions like, is the game finished?

Let me show you with a lemonade stand. Pretend you''re writing instructions for a lemonade stand program. You make a box called flavor and put the word strawberry inside. You make a box called cupsSold and put the number zero inside. And you make a box called standOpen and put yes inside. Every time you sell a cup, your instructions say: take the number out of cupsSold, add one, and put the answer back. So zero becomes one, one becomes two, and so on. Here''s the important part. When the two goes in, the one is gone. A box never holds two things at once. Putting a value into a box is called assignment, and assignment always replaces the old value. At the end of the day, you put no into standOpen. The yes disappears, and the program knows you''re closed.

One last idea, called scope. A box lives in the part of the program where it was made. If a little helper job, like counting coins, makes its own box, that box exists only while the job is running. When the job finishes, the box is packed away, and the rest of the program can''t use it. But boxes made for the whole program, like cupsSold, stick around from start to finish.

Time for one quick question. If cupsSold holds seven and you sell one more cup, what happens inside the box? Here''s the answer. Your instructions take out the seven, add one, and assign eight to the box. The seven is gone for good, because a variable holds exactly one value at a time.', 4, 0.45, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_deep_en_v2', 'k5_variables', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Swapping Values and Finding Where Boxes Live', 'Quick recap: a variable is a labeled box that holds exactly one thing — a number, a word, or a yes/no — and **assignment** means replacing what''s inside.

## Worked Example: The Recess Relay Scoreboard

Imagine your class builds a program to keep score at a relay race. Here is its instruction list:

```
1. Make a box called teamName. Put "Red Rockets" in.
2. Make a box called lapsDone. Put 0 in.
3. Make a box called raceOver. Put no in.
4. Each time a runner finishes a lap:
   take the number out of lapsDone, add 1,
   and put the answer back in.
5. When lapsDone reaches 4, put yes into raceOver.
```

Now run it in slow motion and watch the boxes:

| Moment | teamName | lapsDone | raceOver |
| --- | --- | --- | --- |
| Start | "Red Rockets" | 0 | no |
| Lap 1 done | "Red Rockets" | 1 | no |
| Lap 2 done | "Red Rockets" | 2 | no |
| Lap 4 done | "Red Rockets" | 4 | yes |

Notice three things. First, each box keeps its own type the whole race: teamName always holds a word, lapsDone always holds a number, and raceOver always holds yes or no. Second, every "add 1" is really an assignment — 2 replaces 1, then 3 replaces 2. The old numbers aren''t hiding anywhere. They''re gone.

Third — here comes **scope**. Suppose the program has a small helper job called *time one lap*. While that job runs, it makes its own box, secondsThisLap, to count seconds. The moment the job finishes, that box is packed away. The main scoreboard can never peek into secondsThisLap, because it only existed inside the job. That''s scope: a variable can be used only in the part of the program where it lives.

## A Mix-Up to Avoid

::: misconception
**The wrong idea:** "When I put a new value into a variable, the old value is still saved underneath, like a stack of papers I can dig through later."
**The truth:** A variable holds exactly one value. Assignment throws the old value away completely. If you will need the old value later, copy it into a second box *first* — for example, put lapsDone''s number into a box called lastLap before you change it.
:::

## Where This Takes You

Everything here transfers straight into real programming. When you build projects in Scratch — and later, when you write real code — score counters, player names, and game-over flags are exactly these boxes with exactly these rules; only the spelling changes. Understanding types, assignment, and scope now means those tools will feel familiar instead of mysterious. (A note for grown-ups: this practice matches the computer-science standard CSTA 1B-AP-09, about creating programs that use variables to store and change data.)

::: check
Q: A game''s "lock the door" job makes a box called secretCode. Why can''t the "open the window" job read it?
A: Because of scope. secretCode lives only inside the job that made it; when that job ends, the box is packed away, so other parts of the program never see it.
Q: You want to remember a player''s old score AND their new score. What should your instruction list do?
A: Use two boxes. First copy the current number into a box like oldScore, then assign the new number to score. One box can only ever hold one value.
:::', NULL, NULL, 8, 0.6, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_intro_id_v2', 'k5_variables', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Variabel: Kotak Berlabel dengan Berbagai Jenis Isi', 'Pernah bermain game lalu melihat skormu naik dari 0 menjadi 100? Atau menulis namamu di daftar piket kelas? Skor, nama, dan tanda "sudah selesai" seperti itu disimpan komputer di tempat khusus bernama **variabel**. Hari ini kamu akan tahu bahwa variabel punya jenis isi yang berbeda-beda, dan isinya bisa diganti kapan saja.

## Kotak Berlabel yang Punya Jenis

Di kelas sebelumnya kamu sudah belajar bahwa variabel itu seperti kotak berlabel: labelnya adalah nama, dan di dalamnya ada satu isi. Sekarang kita naik satu tingkat. Ternyata kotak-kotak itu punya **jenis**, tergantung apa yang mau disimpan:

- **Angka** — untuk hal yang bisa dihitung: skor, umur, jumlah nyawa.
- **Kata** — untuk tulisan: nama pemain, nama kucing, judul lagu.
- **Ya/tidak** — untuk jawaban pertanyaan: sudah selesai? punya kunci?

Jenis itu penting karena komputer memperlakukan tiap isi dengan cara berbeda. Angka bisa ditambah dan dikurangi. Kata bisa ditampilkan di layar. Ya/tidak dipakai untuk mengambil keputusan.

Ada satu aturan emas: **satu kotak hanya berisi satu hal pada satu waktu**. Menaruh isi baru ke dalam kotak disebut *pengisian* (assignment). Saat isi baru masuk, isi lama otomatis keluar dan hilang.

## Contoh: Petualangan Kucing Oyen

Bayangkan kamu merancang game tentang kucing bernama Oyen. Ikuti daftar instruksi ini sambil membayangkan kotak-kotaknya:

1. Siapkan kotak **namaPemain** (jenis: kata). Isi dengan "Sinta".
2. Siapkan kotak **skor** (jenis: angka). Isi dengan 0.
3. Siapkan kotak **punyaKunci** (jenis: ya/tidak). Isi dengan tidak.
4. Oyen menangkap seekor ikan! Isi **skor** dengan 10. Angka 0 keluar, angka 10 masuk.
5. Oyen menemukan kunci emas! Isi **punyaKunci** dengan ya.

Di akhir permainan, ketiga kotak berisi: "Sinta", 10, dan ya. Coba tunjuk kotak-kotak itu satu per satu dan sebutkan jenis masing-masing.

::: check
Q: Kotak skor berjenis angka. Bolehkah kita mengisinya dengan kata "sepuluh"?
A: Tidak cocok. Jenis kotaknya angka, jadi isinya harus angka seperti 10 supaya komputer bisa menghitungnya, misalnya saat menambah skor.
Q: Saat skor berubah dari 0 menjadi 10, ke mana angka 0 yang lama?
A: Angka 0 keluar dan hilang, karena satu variabel hanya menyimpan satu isi pada satu waktu.
:::

Di bacaan berikutnya, kita mengulik lebih dalam: bagaimana isi variabel berubah langkah demi langkah, dan mengapa dua variabel bernama sama bisa jadi kotak yang berbeda.', NULL, NULL, 5, 0.3, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_diagram_id_v2', 'k5_variables', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Variabel: Jenis, Isi, dan Wilayah Berlakunya', 'Setiap variabel tinggal di sebuah wilayah, seperti kamar di dalam rumah. Diagram ini memperlihatkan sebuah program pesta ulang tahun beserta variabel-variabelnya: jenisnya, isinya, dan di wilayah mana ia dikenal.

```
          PROGRAM: PESTA ULANG TAHUN
+----------------------------------------------+
| [namaAcara | kata]   isi: "Pesta Rara"       |
|                                              |
|   +-- PERMAINAN: TEBAK ANGKA ------------+   |
|   | [tebakan | angka]   isi: 7           |   |
|   | [benar | ya/tidak]  isi: tidak -> ya |   |
|   +--------------------------------------+   |
|                                              |
|   +-- PERMAINAN: JOGET BALON ------------+   |
|   | [ronde | angka]     isi: 1 -> 2      |   |
|   +--------------------------------------+   |
+----------------------------------------------+
```

Legend:

- **[nama | jenis]** — sebuah kotak variabel: label namanya di kiri, jenis datanya di kanan.
- **isi:** — apa yang sedang tersimpan di kotak itu.
- **->** — pengisian: isi lama diganti isi baru.
- **Kotak besar** — wilayah seluruh program; variabel di sini dikenal oleh semua bagian.
- **Kotak kecil** — wilayah satu permainan; variabelnya hanya dikenal di dalamnya.

Cara membaca diagram:

1. Mulai dari kotak paling luar: seluruh program pesta ulang tahun.
2. **namaAcara** dibuat di kotak besar, jadi kedua permainan boleh memakainya, misalnya untuk menampilkan judul pesta.
3. Masuk ke wilayah Tebak Angka: **tebakan** berjenis angka dan berisi 7; ketika tebakan itu tepat, **benar** diisi ulang dari tidak menjadi ya.
4. Di wilayah Joget Balon, **ronde** berubah dari 1 menjadi 2 saat lagu kedua dimulai.
5. Perhatikan: **tebakan** tidak dikenal di wilayah Joget Balon, karena kotaknya berada di ruangan lain.

::: tip
Sebelum membuat permainanmu sendiri, gambarlah peta kotak seperti ini di kertas: tulis nama, jenis, dan isi awal setiap variabel, lalu lingkari wilayah tempat ia dibutuhkan. Peta kecil ini akan menyelamatkanmu dari banyak kebingungan.
:::', NULL, NULL, 3, 0.4, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_audio_id_v2', 'k5_variables', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Celengan dan Papan Kecil: Cerita tentang Variabel', NULL, NULL, 'Hai, teman belajar! Hari ini kita mengobrol tentang variabel, yaitu tempat penyimpanan berlabel yang dipakai komputer untuk mengingat sesuatu.

Bayangkan kamu punya celengan di kamarmu, dan di depannya kamu menempelkan sebuah papan tulis kecil. Setiap kali jumlah uangmu berubah, kamu menghapus angka lama di papan itu dan menulis angka yang baru. Papan kecil itu bekerja persis seperti variabel. Ia punya nama, misalnya uang tabungan. Ia punya isi, misalnya lima ribu. Dan isinya bisa diganti kapan saja dengan cara hapus lalu tulis ulang. Mengganti isi seperti itu disebut pengisian nilai.

Variabel juga punya jenis. Papan uang tabungan berisi angka, karena uang bisa dihitung. Kamu bisa membuat papan lain bernama nama pemilik, yang isinya kata, misalnya Raka. Kamu juga bisa membuat papan bernama sudah penuh, yang isinya hanya boleh ya atau tidak. Jenis ini penting, sebab angka bisa ditambah dan dikurangi, kata bisa dibaca, dan ya atau tidak membantu mengambil keputusan, misalnya menentukan kapan celengan harus dibuka.

Sekarang kita coba bersama. Papanmu bertuliskan lima ribu. Lalu nenek memberimu tiga ribu, dan kamu memasukkannya ke celengan. Kamu berhitung: lima ribu ditambah tiga ribu sama dengan delapan ribu. Kamu menghapus tulisan lima ribu dan menulis delapan ribu. Ingat, di papan hanya ada satu angka pada satu waktu. Angka yang lama benar-benar hilang begitu angka baru ditulis.

Satu hal lagi: variabel punya wilayah berlakunya. Adikmu juga punya celengan dengan papan bernama uang tabungan, tetapi papan itu ada di kamarnya. Namanya sama, kotaknya berbeda. Kalau tabunganmu bertambah, tabungan adikmu tidak ikut berubah. Dalam program pun begitu: dua bagian program boleh punya variabel bernama sama, dan keduanya tetap terpisah.

Sebelum kita selesai, coba jawab pertanyaan ini. Papan uang tabunganmu bertuliskan delapan ribu, lalu kamu mengisinya dengan sepuluh ribu. Berapa isinya sekarang, dan ke mana angka delapan ribu tadi? Jawabannya: isinya sekarang sepuluh ribu, dan angka delapan ribu sudah terhapus, karena satu variabel hanya menyimpan satu isi pada satu waktu. Selamat, kamu baru saja berpikir seperti seorang programmer!', 4, 0.45, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_deep_id_v2', 'k5_variables', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Mengganti Isi Variabel dan Mengenal Wilayah Berlakunya', 'Kamu sudah tahu: variabel adalah kotak berlabel yang punya jenis (angka, kata, atau ya/tidak), dan mengisinya berarti mengganti isi lama dengan isi baru. Sekarang kita ikuti satu contoh dari awal sampai akhir, lalu membongkar satu kekeliruan yang sering terjadi.

## Merawat Bubu, Ikan Mas Kelas

Kelasmu memelihara ikan mas bernama Bubu. Supaya tidak ada yang lupa atau memberi makan dua kali, kalian membuat "program perawatan" dengan tiga variabel:

- **namaIkan** (kata), isi awal: "Bubu"
- **stokPakan** (angka), isi awal: 5
- **sudahMakan** (ya/tidak), isi awal: tidak

Daftar instruksinya:

1. Setiap pagi, isi **sudahMakan** dengan tidak.
2. Saat memberi makan, isi **stokPakan** dengan isi lamanya dikurangi 1.
3. Setelah itu, isi **sudahMakan** dengan ya.
4. Jika **stokPakan** berisi 0, tulis "beli pakan" di papan kelas.

Perhatikan langkah 2 — ini bagian paling seru. Komputer *membaca dulu* isi lama kotak, menghitung, lalu memasukkan hasilnya sebagai isi baru. Kalau isi lamanya 5, maka 5 dikurangi 1 sama dengan 4, dan angka 4 masuk menggantikan angka 5.

Ikuti dua hari pertama lewat tabel ini:

| Waktu | stokPakan | sudahMakan |
| --- | --- | --- |
| Senin pagi | 5 | tidak |
| Senin, setelah memberi makan | 4 | ya |
| Selasa pagi | 4 | tidak |
| Selasa, setelah memberi makan | 3 | ya |

Lihat polanya: **stokPakan** turun satu-satu, sedangkan **sudahMakan** bolak-balik antara tidak dan ya. Sementara itu **namaIkan** tidak pernah berubah — variabel boleh saja diam kalau tidak ada instruksi yang mengisinya ulang.

## Nama Sama, Kotak Berbeda

Setiap variabel punya **wilayah berlakunya** (dalam pemrograman disebut *scope*): tempat di mana ia dibuat dan dikenal.

::: misconception
Keliru: "Kalau dua bagian program punya variabel dengan nama yang sama, isinya pasti selalu sama."
Yang benar: variabel hanya hidup di wilayahnya sendiri. Kelas 4A dan kelas 4B sama-sama punya papan bernama "skor kebersihan", tetapi itu dua papan berbeda di dua ruangan berbeda — nilainya boleh berbeda. Program juga begitu: Permainan A dan Permainan B boleh sama-sama punya variabel nyawa, tetapi keduanya kotak yang terpisah. Mengubah yang satu tidak mengubah yang lain.
:::

Sebaliknya, ada juga variabel yang dibuat di "ruang bersama" — seperti papan pengumuman di lorong sekolah yang bisa dibaca semua kelas. Variabel seperti itu dikenal oleh seluruh bagian program. Saat merancang program, tanyakan: siapa saja yang perlu memakai kotak ini?

## Ke Mana Ilmu Ini Membawamu

Kemampuan memakai variabel dengan berbagai jenis data, mengisinya ulang, dan memahami wilayahnya adalah bekal inti pemrograman — inilah isi capaian belajar AP-K5-3. Nanti, saat kamu menulis program sungguhan di Scratch atau bahasa lain, kamu akan membuat variabel betulan dengan cara berpikir yang persis sama: apa namanya, apa jenisnya, apa isinya sekarang, dan di mana ia berlaku. Empat pertanyaan itu akan menemanimu di hampir semua program yang kamu buat nanti.

::: check
Q: stokPakan berisi 4. Instruksi "isi stokPakan dengan isi lamanya dikurangi 1" dijalankan dua kali berturut-turut. Berapa isinya sekarang?
A: 2. Pertama 4 menjadi 3, lalu 3 menjadi 2 — setiap pengisian membaca isi terbaru, bukan isi paling awal.
Q: Permainan A punya variabel nyawa berisi 3. Permainan B juga punya variabel bernama nyawa berisi 5. Jika nyawa di Permainan A berkurang menjadi 2, berapa isi nyawa di Permainan B?
A: Tetap 5. Keduanya kotak berbeda di wilayah berbeda, meskipun namanya sama.
:::', NULL, NULL, 8, 0.6, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_reading_intro_en_v2', 'k8_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Why Some Apps Feel Instant: Comparing Algorithm Speed', 'You type two letters into your music app and the right song appears instantly, even though the app knows millions of tracks. Meanwhile, scrolling your camera roll to find one photo from last summer can take ages. The difference isn''t magic — it''s which *algorithm* is doing the searching, and some algorithms are simply built to be faster than others.

## Correct Isn''t Enough — Count the Steps

You already know that an algorithm is a precise, ordered set of steps. Here''s the next level: two algorithms can both be **correct** and still not be equal, because one needs far more steps than the other. Computer scientists call this **efficiency**, and they measure it in two ways:

- **Time** — how many steps the algorithm takes, and how that number grows when the input gets bigger
- **Space** — how much extra memory the algorithm needs while it works

Let''s compare two ways to find your friend Zoe in a contact list of 16 names sorted alphabetically.

**Plan A: check every name, top to bottom.**

```
for each name in the list:
    if name is "Zoe":
        stop — found her!
```

If Zoe is at the very end, that''s 16 checks. If your list grows to 1,600 contacts, the worst case grows to 1,600 checks. The work grows exactly as fast as the list does.

**Plan B: use the alphabetical order and halve the list.**

```
look at the middle name
if "Zoe" comes later, throw away the first half
if "Zoe" comes earlier, throw away the second half
repeat on the half that''s left
```

Each check cuts the problem in half: 16 names, then 8, then 4, then 2, then 1. That''s about 4 checks instead of 16 — and even 1,600 contacts would take only about 11 checks. Writing plans out as pseudocode so you can compare them, like we just did, is the core skill of the CSTA 2-AP-10 standard.

::: check
Q: Plans A and B both find Zoe, so what actually makes Plan B "better"?
A: It needs far fewer steps, and its advantage grows as the list grows — Plan A''s checks grow as fast as the list does, while Plan B''s barely grow at all.
Q: Plan B only works if one thing is true about the contact list. What is it?
A: The list must be sorted (alphabetical), so throwing away half the names at each step is safe.
:::

Next up, you''ll race two algorithms step by step and discover a classic bargain in computing: spending extra memory to buy extra speed.', NULL, NULL, 5, 0.3, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_diagram_en_v2', 'k8_algorithms', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'What Happens to the Step Count When the List Doubles', 'Two search algorithms can both find a username on a sorted leaderboard, but they pay very different prices as the leaderboard grows. This diagram tracks the worst-case number of checks each one needs while the list keeps doubling.

```
   STEPS NEEDED AS THE LEADERBOARD KEEPS DOUBLING

+-----------+    +---------------+    +---------------+
| list size | -> |  CHECK-EVERY  |    | SPLIT-IN-HALF |
+-----------+    +---------------+    +---------------+
|  n =   8  |    |    8 checks   |    |   3 checks    |
|  n =  16  |    |   16 checks   |    |   4 checks    |
|  n =  32  |    |   32 checks   |    |   5 checks    |
|  n =  64  |    |   64 checks   |    |   6 checks    |
+-----------+    +---------------+    +---------------+
                  steps DOUBLE         steps go up
                  every time           by just +1
```

Legend:

- Boxes (drawn with + - and |) hold values: the left column is the leaderboard size, the two right columns are each algorithm''s worst-case checks
- -> means "read across the row: a list of this size costs this many checks"
- n = the number of usernames on the leaderboard
- CHECK-EVERY = look at every username one by one, top to bottom
- SPLIT-IN-HALF = repeatedly cut the sorted list in half until the name is found

How to read it:

1. Pick a row — say n = 16, a leaderboard with 16 usernames.
2. Read across: CHECK-EVERY may need 16 checks, but SPLIT-IN-HALF needs only 4.
3. Drop down one row: the list doubles to 32, and now it''s 32 checks versus 5.
4. Spot the pattern: every doubling doubles CHECK-EVERY''s work but adds just one check for SPLIT-IN-HALF.
5. Imagine the rows continuing until n = 1,000,000: about a million checks versus about 20.

::: tip
You can test any algorithm this way without a computer: run it on paper with a small input and count the steps, then double the input and count again. The pattern you see after two or three doublings predicts how the algorithm will behave on huge inputs.
:::', NULL, NULL, 3, 0.4, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_audio_en_v2', 'k8_algorithms', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Guess Smarter: Efficiency in a Number Game', NULL, NULL, 'Here''s a question at the heart of computer science: if two sets of instructions both get the right answer, how do you decide which one is better? You already know what an algorithm is — a precise, ordered list of steps. Today''s idea is that being correct is not enough. We also care about how much work an algorithm does, and how that work grows when the problem gets bigger.

Let''s play a guessing game. I''m thinking of a number between one and one hundred, and after every guess I''ll tell you whether my number is higher or lower. One algorithm is to guess one, then two, then three, and keep counting up. It works, but if my number is ninety-nine, you''ll need ninety-nine guesses. Now try a smarter algorithm. Guess fifty, right in the middle. If I say higher, you''ve just eliminated half of all the numbers with a single guess. So you guess seventy-five, and half of what''s left disappears again. Each guess cuts the possibilities in half: one hundred becomes fifty, then twenty-five, then about twelve, then six, then three, then two, then one. Seven guesses at most. And here''s the amazing part. If I picked a number between one and one million, counting up could take a million guesses, but the halving strategy needs only about twenty.

That''s what efficiency means: not just getting the answer, but counting the steps and asking how that count grows as the problem grows. There''s one more twist worth remembering. Sometimes an algorithm can run faster by storing extra information as it goes, and that storage costs memory. Time and memory trade against each other, and good programmers choose that trade on purpose, the way you''d choose the right gear on a bike before a hill.

So here''s your recap question. Why is the halving strategy so much faster than counting up one at a time? Say your answer out loud before I give mine. Ready? It''s because every guess throws away half of all the remaining possibilities instead of just one, so even a gigantic problem collapses after a small number of steps. That is the power of choosing a better algorithm.', 4, 0.45, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_reading_deep_en_v2', 'k8_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Counting Steps and the Time-Space Trade-Off', 'Quick recap: two correct algorithms can do wildly different amounts of work, so we compare them by counting steps (time) and extra memory (space) as the input grows.

## Worked Example: Catching a Duplicate Song

Your playlist app needs to warn you when you add a song you already have. Here are two algorithms that both work.

**Plan 1 — compare every pair.**

```
for each song A in the playlist:
    for each song B after A:
        if A and B are the same:
            report "duplicate!" and stop
```

Trace it on a 5-song playlist: Nova, Echo, Drift, Echo, Zoom.

1. A = Nova → compare with Echo, Drift, Echo, Zoom (4 checks, no match)
2. A = Echo → compare with Drift (check 5), then Echo (check 6) → **duplicate found!**

That took 6 comparisons. The worst case (no duplicates anywhere) for 5 songs is 4 + 3 + 2 + 1 = 10 comparisons. Fine. But for 100 songs the worst case is 4,950 comparisons, and for 1,000 songs it''s about 500,000. **Doubling the playlist roughly quadruples the work.**

**Plan 2 — trade memory for speed.**

```
create an empty "seen" collection (instant lookups)
for each song in the playlist:
    if song is already in "seen":
        report "duplicate!" and stop
    add song to "seen"
```

Trace it: Nova → not seen, add it. Echo → not seen, add it. Drift → not seen, add it. Echo → **already in "seen" — done.** About 4 steps. For 1,000 songs the worst case is about 1,000 steps instead of 500,000.

So Plan 2 always wins? Not for free:

| Plan | Steps for 100 songs | Extra memory |
| --- | --- | --- |
| 1 — compare pairs | about 4,950 | almost none |
| 2 — seen collection | about 100 | room for up to 100 songs |

That is the **time/space trade-off**: Plan 2 buys speed by paying memory. Neither plan is "the best" in all situations — it depends on how big the input gets and how much memory you can spare.

## A Misconception Worth Deleting

::: misconception
"Shorter code runs faster — a three-line algorithm must be quicker than a ten-line one."
Not true. The computer doesn''t run *lines*, it runs *steps*. Plan 1 above looks tiny, yet on 1,000 songs it does about 500 times more work than Plan 2, because its little nested loop repeats an enormous number of times. Judge an algorithm by counting the steps it performs as the input grows, not by how short it looks on the page.
:::

## Where This Leads

Comparing step counts is a skill that transfers far beyond this course. In high school computer science it grows into **Big-O notation**, the official language for describing how algorithms scale. It also transfers straight into anything you build: a game that lags when 100 enemies spawn, or an app that freezes on a long friend list, is having an efficiency problem — and you now own the tool for spotting it. Double the input, count the steps again, and the pattern tells you the story.

::: check
Q: A playlist grows from 200 songs to 400. Roughly what happens to the worst-case work for each plan?
A: Plan 1 roughly quadruples, because the number of pairs grows with the square of the playlist size; Plan 2 roughly doubles, from about 200 steps to about 400.
Q: You''re coding for a tiny gadget with almost no spare memory, and playlists on it never pass 20 songs. Which plan might you pick, and why?
A: Plan 1 — at 20 songs its worst case is only 190 comparisons, which is plenty fast, and it avoids the extra memory that Plan 2 demands.
:::', NULL, NULL, 8, 0.6, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_reading_intro_id_v2', 'k8_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Algoritma Cepat vs Algoritma Lambat: Ayo Hitung Langkahnya', 'Pernah menunggu aplikasi yang lemot, padahal temanmu membuka aplikasi serupa dan langsung jalan? Sering kali bedanya bukan pada HP-nya, melainkan pada algoritma di dalamnya. Dua program bisa mengerjakan tugas yang sama persis, tetapi yang satu butuh ribuan langkah dan yang lain hanya belasan.

## Ide Besar: Efisiensi Algoritma

Algoritma yang benar saja belum cukup; kita juga ingin algoritma yang **efisien**. Efisiensi diukur dari dua hal:

- **Waktu**: berapa banyak langkah yang dijalankan sampai tugas selesai.
- **Ruang (memori)**: berapa banyak data tambahan yang harus disimpan selama bekerja.

Cara paling adil untuk membandingkan dua algoritma adalah menghitung langkahnya pada **kasus terburuk** — situasi paling apes yang mungkin terjadi. Kemampuan menganalisis dan membandingkan algoritma seperti ini adalah bagian dari standar belajar AP-K8-2.

Yuk kita buktikan lewat permainan.

### Permainan Tebak Angka 1 sampai 100

Temanmu memikirkan satu angka rahasia antara 1 dan 100. Setiap kali kamu menebak, ia hanya menjawab "benar", "terlalu kecil", atau "terlalu besar".

**Cara 1: tebak satu per satu.**

```
untuk angka dari 1 sampai 100:
    tebak angka itu
    jika benar, berhenti
```

Kalau angka rahasianya 100, kamu butuh 100 tebakan. Itulah kasus terburuknya: 100 langkah.

**Cara 2: bagi dua wilayah pencarian.**

```
bawah = 1, atas = 100
selama belum benar:
    tengah = (bawah + atas) dibagi 2
    tebak tengah
    jika "terlalu kecil": bawah = tengah + 1
    jika "terlalu besar": atas  = tengah - 1
```

Tebakan pertama: 50. Jawabannya "terlalu besar"? Buang semua angka dari 50 ke atas. Setiap tebakan memangkas kemungkinan menjadi setengahnya: 100, 50, 25, 12, 6, 3, 1. Paling banyak hanya sekitar 7 tebakan!

Dua algoritma, hasil sama, tetapi 100 langkah lawan 7 langkah. Bayangkan bedanya kalau angkanya sampai satu juta: sekitar sejuta langkah lawan hanya 20 langkah.

::: check
Q: Apa arti "kasus terburuk" saat membandingkan algoritma?
A: Situasi yang membuat algoritma bekerja paling banyak langkah, misalnya angka rahasia baru tertebak pada percobaan paling akhir.
Q: Dengan cara bagi dua, dari 100 kemungkinan tersisa kira-kira berapa setelah dua tebakan?
A: Sekitar 25, karena setiap tebakan memangkas kemungkinan menjadi setengahnya: 100 menjadi 50, lalu menjadi 25.
:::

Di materi pendalaman, kamu akan menghitung langkah algoritma dengan lebih teliti dan menemukan bahwa "cepat" kadang harus dibayar dengan memori ekstra.', NULL, NULL, 5, 0.3, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_diagram_id_v2', 'k8_algorithms', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Langkah: Periksa Satu per Satu vs Bagi Dua', 'Diagram ini membandingkan dua cara mencari satu lagu di playlist berisi 16 lagu yang sudah urut abjad. Perhatikan berapa langkah terburuk yang dibutuhkan masing-masing cara.

```
 CARA A: PERIKSA SATU PER SATU
 [1]->[2]->[3]-> ... ->[16]
 terburuk: 16 langkah

 CARA B: BAGI DUA
 +------------------+
 |  sisa: 16 lagu   |
 +---------+--------+
           | periksa lagu tengah,
           v buang separuh sisanya
 +------------------+
 |  sisa: 8 lagu    |
 +---------+--------+
           |
           v
   sisa: 4 -> 2 -> 1
 terburuk: 5 langkah
```

Legend:

- `[angka]` = lagu yang sedang diperiksa pada Cara A
- `->` = lanjut ke pemeriksaan berikutnya
- kotak `+--+` = kelompok lagu yang masih mungkin memuat lagu yang dicari
- `|` dan `v` = alur proses menuju langkah berikutnya
- `...` = langkah-langkah yang tidak digambar satu per satu

Cara membaca diagram ini:

1. Mulai dari Cara A: lagu diperiksa satu per satu dari nomor 1; jika lagu yang dicari ada di urutan paling akhir, kamu butuh 16 pemeriksaan.
2. Pindah ke Cara B: semuanya berawal dari kotak "sisa: 16 lagu", artinya semua lagu masih mungkin.
3. Setiap panah ke bawah berarti satu pemeriksaan di tengah daftar; separuh lagu langsung dibuang dari pencarian.
4. Ikuti angka sisa yang menyusut — 16, 8, 4, 2, 1 — sehingga paling banyak hanya 5 pemeriksaan sampai pasti ketemu.
5. Bandingkan angka terburuk kedua cara: makin panjang playlist-nya, makin besar selisih kecepatannya.

::: tip
Cara B hanya bisa dipakai kalau daftarnya sudah urut. Sebelum memilih algoritma, periksa dulu kondisi datamu — data yang urut membuka pilihan algoritma yang jauh lebih cepat.
:::', NULL, NULL, 3, 0.4, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_audio_id_v2', 'k8_algorithms', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Rahasia Algoritma Cepat: Buang Separuh, Menang Banyak', NULL, NULL, 'Bayangkan kamu memegang kamus tebal berisi puluhan ribu kata, dan kamu harus menemukan arti kata "serindit". Ada dua cara. Cara pertama, kamu membuka halaman satu, lalu halaman dua, lalu halaman tiga, terus begitu sampai ketemu. Kalau kata itu ada di bagian belakang, kamu bisa membalik ribuan halaman. Cara kedua, kamu membuka kamus tepat di tengah. Ternyata kata-kata di halaman itu dimulai dengan huruf M. Karena "serindit" dimulai dengan huruf S, kamu tahu kata itu pasti ada di paruh belakang, jadi paruh depan kamus langsung kamu abaikan. Kamu buka lagi bagian tengah dari sisa halaman, membandingkan hurufnya, membuang separuhnya lagi, dan begitu seterusnya. Dengan cara ini, kamus berisi puluhan ribu kata bisa ditaklukkan hanya dengan belasan kali membuka halaman.

Dua cara tadi adalah dua algoritma. Keduanya benar, dan keduanya pasti menemukan kata yang dicari. Bedanya ada pada efisiensi, yaitu berapa banyak langkah yang dibutuhkan sampai selesai. Ilmuwan komputer membandingkan algoritma dengan menghitung langkah pada kasus terburuk, yaitu situasi yang paling apes. Untuk cara satu per satu, kasus terburuknya adalah membalik hampir semua halaman. Untuk cara bagi dua, kasus terburuknya tetap hanya belasan langkah, karena setiap langkah membuang separuh kemungkinan.

Selain waktu, ada satu hal lagi yang perlu ditimbang, yaitu ruang atau memori. Kadang algoritma bisa dibuat lebih cepat dengan menyimpan catatan tambahan. Misalnya, kalau kamu sering mencari kata yang sama, kamu bisa menulis kata-kata favoritmu beserta nomor halamannya di selembar kertas. Pencarian jadi hampir instan, tetapi kamu harus menyediakan kertas ekstra, alias memori tambahan. Cepat tapi boros ruang, atau hemat ruang tapi lebih lambat. Inilah pertukaran antara waktu dan ruang, dan programmer sungguhan menimbang hal ini setiap hari saat membangun aplikasi dan game yang kamu pakai.

Sekarang pertanyaan penutup untukmu. Kalau tebal kamus itu dilipatgandakan menjadi dua kali lipat, berapa langkah tambahan yang dibutuhkan cara bagi dua? Jawabannya, hanya satu langkah tambahan. Karena sekali buka halaman langsung membuang separuh kamus, kamus yang dua kali lebih tebal cukup dipangkas satu kali untuk kembali ke ukuran semula. Itulah kekuatan algoritma yang efisien: datanya boleh tumbuh sangat besar, tetapi jumlah langkahnya nyaris tidak bertambah.', 4, 0.45, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_reading_deep_id_v2', 'k8_algorithms', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menghitung Langkah dan Menimbang Memori: Trade-off Algoritma', 'Efisiensi algoritma diukur dari dua sisi: waktu (jumlah langkah) dan ruang (memori tambahan). Sering kali keduanya bisa saling ditukar — itulah yang disebut *trade-off* waktu dan ruang.

## Contoh Lengkap: Mendeteksi Nama Ganda

Kelasmu sedang membentuk grup proyek. Kamu punya daftar 30 nama dan ingin memastikan tidak ada nama yang tertulis dua kali.

**Algoritma A: bandingkan semua pasangan.**

```
untuk setiap nama ke-i dalam daftar:
    untuk setiap nama ke-j setelah i:
        jika nama[i] sama dengan nama[j]:
            laporkan "ada nama ganda"
```

Mari hitung langkahnya dengan daftar kecil dulu, misalnya 5 nama: Ayu, Bima, Cika, Dani, Emil.

1. Ayu dibandingkan dengan Bima, Cika, Dani, Emil — 4 perbandingan.
2. Bima dibandingkan dengan Cika, Dani, Emil — 3 perbandingan.
3. Cika — 2 perbandingan, lalu Dani — 1 perbandingan.
4. Total: 4 + 3 + 2 + 1 = 10 perbandingan untuk 5 nama.

Untuk 30 nama, kasus terburuknya: 29 + 28 + ... + 1 = 435 perbandingan. Memori tambahannya hampir nol, karena kita hanya memakai daftar yang sudah ada.

**Algoritma B: pakai catatan "sudah terlihat".**

```
buat catatan kosong
untuk setiap nama dalam daftar:
    jika nama sudah ada di catatan:
        laporkan "ada nama ganda"
    jika belum, tulis nama itu ke catatan
```

Setiap nama hanya diproses sekali: untuk 5 nama cukup 5 pemeriksaan, untuk 30 nama cukup 30 pemeriksaan. Jauh lebih hemat daripada 435! Tetapi ada harganya: catatan itu butuh memori tambahan untuk menampung sampai 30 nama.

| Algoritma | Langkah (30 nama) | Memori tambahan |
|---|---|---|
| A: semua pasangan | 435 | hampir nol |
| B: catatan | 30 | sampai 30 nama |

Inilah trade-off waktu dan ruang: Algoritma B "membayar" memori ekstra untuk memangkas waktu. Tidak ada pilihan yang selalu benar — semuanya bergantung pada seberapa besar datamu dan seberapa lega memori perangkatmu.

## Miskonsepsi yang Sering Muncul

::: misconception
Keliru: "Kode yang lebih pendek pasti lebih cepat."
Faktanya: jumlah baris kode tidak menentukan kecepatan. Yang dihitung adalah berapa kali langkah-langkahnya dijalankan. Algoritma A di atas hanya empat baris, tetapi loop di dalam loop membuatnya berjalan ratusan kali. Algoritma B sedikit lebih panjang, tetapi setiap nama hanya diproses satu kali.
:::

Miskonsepsi lain yang mirip: "komputer zaman sekarang cepat, jadi efisiensi tidak penting." Untuk 30 nama memang tidak terasa. Tetapi aplikasi nyata mengolah jutaan data, dan di skala itu algoritma yang boros bisa membuat aplikasi macet atau baterai cepat habis.

## Ke Mana Kemampuan Ini Membawamu

Kebiasaan menghitung langkah dan menimbang memori adalah bekal langsung untuk pelajaran informatika di jenjang berikutnya, tempat kamu akan mengenal notasi resmi untuk mengukur pertumbuhan langkah. Kemampuan yang sama terpakai setiap kali kamu merancang program sendiri: sebelum menulis kode, kamu bisa memperkirakan cara mana yang sanggup menangani data besar. Bahkan di luar koding, membandingkan "cara mana yang paling hemat usaha" adalah pola pikir yang berguna untuk proyek kelompok apa pun.

::: check
Q: Daftar diperbesar dari 30 nama menjadi 60 nama. Kira-kira bagaimana perubahan jumlah perbandingan pada Algoritma A?
A: Naik sekitar empat kali lipat, dari 435 menjadi 59 + 58 + ... + 1 = 1770, karena setiap nama harus dibandingkan dengan hampir semua nama lainnya.
Q: Kapan Algoritma A yang lebih lambat justru menjadi pilihan yang masuk akal?
A: Saat datanya kecil sehingga selisih waktunya tidak terasa, atau saat perangkat punya memori sangat terbatas sehingga catatan tambahan terlalu mahal.
:::', NULL, NULL, 8, 0.6, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_reading_intro_en_v2', 'k8_control', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Nested Loops, Booleans, and Events: Three Power Moves', 'Think about your favorite game. Enemies patrol in repeating patterns, the screen fills with tiles level after level, and the instant you tap the jump button, your character jumps. None of that is magic. It is all built from three control moves you are about to learn.

## The Big Idea: Three Ways to Steer a Program

You already know loops (repeat things) and if-statements (make choices). Now we level them up.

**1. Nested loops** are a loop inside a loop. The outer loop runs, and for *each* of its passes, the inner loop runs all the way through. That is how programs handle anything shaped like a grid: game boards, pixel art, seating charts.

**2. Boolean logic** means combining conditions with **AND**, **OR**, and **NOT**. AND means both parts must be true. OR means at least one part must be true. NOT flips true to false. This lets one if-statement ask smarter questions, like "is the player on the ground AND holding the jump key?"

**3. Events** are code that does not run top to bottom, but *waits*. An event handler sits quietly until something happens (a tap, a key press, a message), then springs into action. Apps and games are mostly a bunch of event handlers waiting for you to do something.

## A Worked Example: Drawing a Level Map

Say you are building a tiny game level: 3 rows of tiles, 4 tiles in each row.

```
for row from 1 to 3
    for col from 1 to 4
        draw a tile at (row, col)
```

Follow it exactly like the computer does:

1. The outer loop sets row to 1.
2. The inner loop runs completely: col 1, 2, 3, 4. Four tiles drawn.
3. Only now does the outer loop move to row 2, and the inner loop starts over at col 1.
4. Same again for row 3. Total tiles: 3 x 4 = **12**.

Now add a boolean to make the map interesting:

```
if row = 1 OR row = 3
    draw a grass tile
else
    draw a water tile
```

Two grassy rows with a river through the middle, all from five short lines of code.

::: check
Q: In the map example, how many times does "draw a tile" run, and why?
A: 12 times. The inner loop draws 4 tiles for each of the 3 outer-loop rows, and 3 x 4 = 12.
Q: Why is the condition "row = 1 OR row = 3" true when row is 1, even though row is not 3?
A: OR only needs one side to be true. Since row = 1 is true, the whole condition is true.
:::

In the deeper reading, you will combine all three moves to build the skeleton of a real tap-the-target game.', NULL, NULL, 5, 0.3, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_diagram_en_v2', 'k8_control', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'How a Nested Loop Flows Through a Grid', 'Imagine a photo app laying out a wall of pictures: 3 rows, 5 photos per row. This diagram shows the exact path the program follows, including the two boolean checks that decide when each loop stops.

```
 +---------------------------+
 | START: 3 rows, 5 columns  |
 +-------------+-------------+
               |
               v
       +---------------+  no   +--------+
  +--->| more rows?    |------>|  DONE  |
  |    +-------+-------+       +--------+
  |            | yes
  |            v
  |    +---------------+  no   +--------------+
  | +->| more photos   |------>| next row,    |
  | |  | in this row?  |       | reset column |
  | |  +-------+-------+       +------+-------+
  | |          | yes                  |
  | |          v                      |
  | |  +---------------+              |
  | +--| place photo,  |              |
  |    | next column   |              |
  |    +---------------+              |
  +-----------------------------------+
```

Legend

- Boxes are steps the program performs or questions it asks.
- Boxes ending in "?" are boolean checks with two exits.
- Arrows show the direction the program moves.
- The words "yes" and "no" label which exit gets taken.
- The long lines on the left edge are loop-back paths.

Walkthrough

1. Start at the top: the plan is 3 rows with 5 photos each.
2. "More rows?" is yes for row 1, so the program drops into the inner loop.
3. "More photos in this row?" is yes, so it places a photo, moves one column right, and loops back. This repeats 5 times.
4. When the row is full, the "no" exit fires: move to the next row, reset the column to 1, and loop all the way back up to "more rows?".
5. After row 3 is filled, "more rows?" finally answers no, and the program reaches DONE with 3 x 5 = 15 photos placed.

::: tip
When a nested loop confuses you, build a trace table with two columns, row and col, and write down every pair the program visits in order. To predict the total number of repeats without tracing, just multiply: outer passes times inner passes.
:::', NULL, NULL, 3, 0.4, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_audio_en_v2', 'k8_control', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Lost Phone: Loops, Rules, and Code That Waits', NULL, NULL, 'Here is a situation you can probably picture. You are at the movies, the lights come up, and your phone is gone. How do you search an entire theater? You go row by row. You start at row one and check seat one, seat two, seat three, all the way to the end of that row. Only when the entire row is finished do you move to row two and start again at seat one. Congratulations, you just ran a nested loop. The outer loop picks the row. The inner loop checks every seat in that row. The important part is the rhythm: the inner loop does a complete lap for every single step of the outer loop. If the theater has ten rows and twenty seats per row, that is two hundred seat checks, because ten times twenty is two hundred.

Now add boolean logic. While you search, you are not grabbing everything you find under the seats. Your rule is: pick it up if it is a phone AND it is mine. Both parts have to be true. A wallet fails the test. Somebody else''s phone fails the test. With OR, the rule loosens up. You might tell your friends, call me if you find my phone OR anything with a blue case. Either one alone is enough. So AND makes a rule stricter, and OR makes it easier to pass.

Finally, events. Searching two hundred seats is exhausting, so you try something smarter. You ask a friend to call your phone, and then you simply listen. Notice that you are not doing anything at all. You are waiting. The moment the phone buzzes, you spring toward the sound. That is event-driven control flow. Real apps work exactly this way. Nothing happens until you tap, swipe, or a message arrives, and then the matching piece of code, called an event handler, wakes up and runs.

So remember the three moves: nested loops for grid-shaped work, booleans for smart rules, and events for code that waits.

Here is your recap question. In a nested loop, which loop finishes a complete lap first, the outer one or the inner one? The answer is the inner one. The inner loop runs through all of its passes for each single pass of the outer loop, and only then does the outer loop take its next step.', 4, 0.45, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_reading_deep_en_v2', 'k8_control', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Building a Mini Game with Loops, Booleans, and Events', 'Quick recap of the big idea: nested loops build grid-shaped things, boolean logic asks smarter yes/no questions, and events let code wait for exactly the right moment. Now we put all three into one small game.

## Worked Example: Catch the Star

The game: a 2 x 3 grid of buttons. Every second, a star pops up on a random button. Tap a starred button in time and you score. Here is the whole skeleton in pseudocode:

```
when the game starts
    for row from 1 to 2
        for col from 1 to 3
            create a button at (row, col)
    set score to 0
    set timeLeft to 30

when any button is tapped
    if button shows a star AND timeLeft > 0
        change score by 1
        play "ding"
    else
        play "buzz"

when timeLeft reaches 0
    if score >= 10 OR streak >= 5
        show "You win!"
    else
        show "Try again!"
```

Walk through it piece by piece:

1. **Setup uses a nested loop.** The outer loop picks row 1, and the inner loop creates buttons at columns 1, 2, 3. Then the outer loop moves to row 2 and the inner loop runs again. Six buttons appear, and you never had to write six copy-pasted lines.
2. **The tap handler is an event plus an AND.** After setup, this code just waits. It might run forty times in one game, or zero. When it does run, the AND protects the score: a tap only counts if the button shows a star *and* the clock has not run out. Both parts must be true, or the player hears the buzz.
3. **The ending is an event plus an OR.** There are two paths to victory: reach 10 points, or pull off a 5-tap streak. With OR, either one alone is enough.

Notice how the three tools split the work. The nested loop builds the board once. The booleans guard the rules. The events make the game feel alive.

## A Misconception Worth Squashing

::: misconception
Wrong belief: "In a nested loop, the two loops take turns. The outer loop goes one step, then the inner loop goes one step."
The truth: the inner loop runs ALL of its passes for every single pass of the outer loop. With 2 rows and 3 columns, the order is (1,1), (1,2), (1,3), then (2,1), (2,2), (2,3). The inner loop finishes a complete lap before the outer loop takes even one more step.
:::

A related trap happens with booleans. AND sounds like adding, so students expect it to let *more* things through. It is the opposite: AND adds a requirement, so fewer situations pass the test. OR relaxes the rules, so more situations pass.

## Where This Leads

This is the top of the control-structures ladder in this course, and it lines up with CSTA standard 2-AP-11. Everything here transfers directly to whatever you build next: Python, JavaScript, and every other language you will meet in high school use these same three moves with slightly different spelling. When you later program robots, websites, or bigger games, you will recognize the pattern instantly: loops for structure, booleans for rules, events for interaction.

::: check
Q: In Catch the Star, the timer hits 0 at the exact moment a player with score 8 and streak 6 taps a starred button. Do they win?
A: Yes. The tap itself does not score, because timeLeft > 0 is false and the AND fails. But the win check is score >= 10 OR streak >= 5, and a streak of 6 makes the OR true.
Q: You change setup to 4 rows and 5 columns, and inside the inner loop you add "if row = col then make the button gold." How many gold buttons appear?
A: 4. The condition is true at (1,1), (2,2), (3,3), and (4,4). There is no row 5, so (5,5) never happens.
:::', NULL, NULL, 8, 0.6, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_reading_intro_id_v2', 'k8_control', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Naik Level: Loop Bersarang, Logika Boolean, dan Event', 'Pernah penasaran bagaimana game di HP tahu persis kapan karakter harus melompat, atau bagaimana aplikasi chat langsung berbunyi begitu pesan masuk? Semua itu diatur oleh struktur kendali — cara program menentukan apa yang dilakukan, kapan, dan berapa kali. Di jenjang sebelumnya kamu sudah memakai perulangan dan percabangan sederhana; sekarang saatnya naik level.

## Tiga Alat Kendali yang Lebih Kuat

Sesuai capaian AP-K8-3, ada tiga alat yang akan sering kamu pakai saat membuat program yang lebih serius:

- **Loop bersarang (nested loop)**: perulangan di dalam perulangan. Cocok untuk pekerjaan berbentuk baris dan kolom, seperti papan catur atau peta game.
- **Logika boolean**: menggabungkan beberapa syarat dengan DAN, ATAU, dan TIDAK sehingga keputusan program jadi lebih pintar.
- **Alur berbasis event**: program tidak berjalan lurus dari atas ke bawah, melainkan menunggu kejadian — sentuhan layar, klik tombol, pesan masuk — lalu bereaksi.

## Contoh Kecil: Menggambar Peta Game

Misalnya kamu membuat game petualangan dan butuh peta rumput berukuran 3 baris kali 5 kolom.

```
untuk baris dari 1 sampai 3
    untuk kolom dari 1 sampai 5
        gambar satu petak rumput
    turun ke baris berikutnya
```

Ikuti jalannya: saat baris = 1, loop dalam menggambar 5 petak (kolom 1 sampai 5). Setelah itu barulah baris naik ke 2, dan loop dalam berjalan 5 kali lagi. Begitu seterusnya sampai baris 3 selesai. Totalnya 3 kali 5 = 15 petak, padahal kamu hanya menulis satu perintah gambar.

Boolean dan event juga bisa langsung dipakai:

```
jika punya_kunci DAN di_depan_pintu
    buka pintu

saat pesan_masuk diterima
    mainkan suara notifikasi
```

Blok pertama hanya membuka pintu kalau dua syarat benar sekaligus. Blok kedua tidak berjalan sama sekali — sampai benar-benar ada pesan yang masuk.

::: check
Q: Pada contoh peta di atas, berapa kali perintah "gambar satu petak rumput" dijalankan?
A: 15 kali. Setiap satu putaran loop luar (baris), loop dalam (kolom) berjalan 5 kali penuh, dan 3 kali 5 = 15.
Q: Kapan kondisi "punya_kunci DAN di_depan_pintu" bernilai benar?
A: Hanya saat kedua syarat benar sekaligus. Jika salah satu saja salah, seluruh kondisi bernilai salah dan pintu tidak terbuka.
:::

Di materi pendalaman, kita akan merakit ketiga alat ini menjadi satu mini-game utuh, lengkap dengan skor, nyawa, dan kondisi menang.', NULL, NULL, 5, 0.3, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_diagram_id_v2', 'k8_control', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Alur Program Berbasis Event', 'Program berbasis event menghabiskan sebagian besar waktunya untuk menunggu, lalu bereaksi saat sesuatu terjadi. Diagram ini menunjukkan alur sebuah game sederhana: karakter melompat saat layar disentuh, dan level selesai jika syarat boolean terpenuhi.

```
      +-----------------+
      |   Mulai game    |
      +--------+--------+
               |
               v
      +-----------------+
      | Tunggu kejadian |<-------------+
      +--------+--------+              |
               |                       |
               v                       |
      [ layar disentuh? ]              |
        |            |                 |
        | ya         | tidak           |
        v            +---------------->+
      +-----------------+              |
      |    Karakter     |              |
      |    melompat     |              |
      +--------+--------+              |
               |                       |
               v                       |
 [ koin >= 5 DAN waktu > 0 ? ]         |
        |            |                 |
        | ya         | tidak           |
        v            +---------------->+
      +-----------------+
      | Level selesai!  |
      +-----------------+
```

Legenda:

- Kotak bergaris (+---+): aksi yang dijalankan program.
- Tanda [ ... ]: pertanyaan boolean, jawabannya hanya ya atau tidak.
- Garis | dan panah v: arah jalannya program dari atas ke bawah.
- Cabang "ya" dan "tidak": dua kemungkinan hasil pemeriksaan.
- Garis tegak di sisi kanan: jalur kembali ke kotak "Tunggu kejadian".

Cara membaca diagram:

1. Game dinyalakan, lalu program langsung masuk ke kotak "Tunggu kejadian" — di sanalah ia berada hampir sepanjang waktu.
2. Saat layar disentuh, jawaban pemeriksaan pertama adalah "ya": alur turun dan karakter melompat.
3. Program lalu memeriksa kondisi gabungan: koin >= 5 DAN waktu > 0. Keduanya harus benar sekaligus.
4. Jika keduanya benar, alur turun ke kotak "Level selesai!" dan permainan berakhir.
5. Jika salah satu saja salah, cabang "tidak" mengikuti garis kanan dan kembali ke "Tunggu kejadian", siap bereaksi pada sentuhan berikutnya.

::: tip
Sebelum menulis kode game buatanmu sendiri, gambar dulu diagram seperti ini di kertas: daftar semua kejadian (sentuhan, tombol, tabrakan, waktu habis), lalu tentukan reaksi untuk masing-masing. Kodenya jadi jauh lebih mudah ditulis dan dicek.
:::', NULL, NULL, 3, 0.4, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_audio_id_v2', 'k8_control', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cara Program Menunggu, Mengulang, dan Memutuskan', NULL, NULL, 'Halo! Kali ini kita membahas tiga cara program mengatur jalannya sendiri: perulangan bersarang, logika boolean, dan alur berbasis kejadian, yang biasa disebut event.

Mulai dari perulangan bersarang. Bayangkan gurumu memintamu membagikan buku ke seluruh kelas. Kamu berdiri di baris pertama, lalu meletakkan satu buku di meja pertama, meja kedua, meja ketiga, sampai meja terakhir di baris itu. Setelah baris pertama selesai, barulah kamu pindah ke baris kedua dan mengulang hal yang sama. Itulah perulangan bersarang: ada perulangan besar, yaitu berpindah dari baris ke baris, dan di dalamnya ada perulangan kecil, yaitu meletakkan buku di setiap meja. Kuncinya, perulangan kecil harus selesai penuh dulu sebelum perulangan besar melangkah satu kali.

Berikutnya, logika boolean. Boolean hanya punya dua nilai: benar atau salah. Serunya, kita bisa menggabungkan beberapa syarat sekaligus. Misalnya, kamu boleh bermain ke rumah teman jika PR sudah selesai dan hujan sudah berhenti. Kata dan di sini ketat sekali: dua-duanya harus benar. PR selesai tapi masih hujan? Berarti tidak boleh. Kalau syaratnya memakai kata atau, cukup satu saja yang benar, dan itu aturan yang sangat berbeda. Program memakai gabungan seperti ini untuk mengambil keputusan yang lebih pintar.

Terakhir, alur berbasis event. Saat menunggu jam istirahat, kamu tidak berdiri di depan kelas sambil menatap jam terus-menerus, kan? Kamu mengerjakan hal lain, dan begitu bel berbunyi, kamu langsung bereaksi. Program modern bekerja persis seperti itu. Sebagian besar waktunya dipakai untuk menunggu, dan begitu ada kejadian, misalnya layar disentuh atau pesan masuk, barulah potongan kode tertentu dijalankan. Karena itu, urutan kejadian di sebuah aplikasi ditentukan oleh penggunanya, bukan oleh urutan baris kode.

Gabungan ketiga alat inilah yang membuat aplikasi dan game favoritmu terasa hidup dan cepat menanggapi.

Sebelum selesai, satu pertanyaan untukmu. Jika perulangan luar berjalan tiga kali dan perulangan dalam berjalan lima kali, berapa kali tugas yang paling dalam dikerjakan? Coba pikirkan sebentar. Jawabannya lima belas kali, karena setiap satu putaran perulangan luar, perulangan dalam berjalan lima kali penuh, dan tiga kali lima sama dengan lima belas.', 4, 0.45, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_control_reading_deep_id_v2', 'k8_control', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Merakit Mini-Game dengan Loop Bersarang, Boolean, dan Event', 'Ingat idenya: loop bersarang mengulang pekerjaan berlapis-lapis, logika boolean menggabungkan syarat, dan event membuat program bereaksi terhadap kejadian. Sekarang kita rakit ketiganya menjadi satu game utuh.

## Bedah Kode: Mini-Game "Tangkap Apel"

Aturannya sederhana: apel berjatuhan, pemain menggeser keranjang, dan level selesai jika skor cukup selagi nyawa masih ada.

```
saat game dimulai
    skor = 0
    nyawa = 3
    untuk baris dari 1 sampai 2
        untuk kolom dari 1 sampai 4
            letakkan apel di posisi (baris, kolom)

saat tombol_kiri ditekan
    geser keranjang ke kiri

saat tombol_kanan ditekan
    geser keranjang ke kanan

saat apel jatuh ke tanah
    nyawa = nyawa - 1

saat apel masuk keranjang
    skor = skor + 1
    jika skor >= 8 DAN nyawa > 0
        tampilkan "Level Selesai!"
```

Mari kita telusuri langkah demi langkah:

1. **Persiapan level.** Begitu game dimulai, loop bersarang berjalan: baris 1 diisi apel di kolom 1 sampai 4, lalu baris 2 diisi 4 apel lagi. Total 2 kali 4 = 8 apel muncul di layar.
2. **Program "diam".** Setelah persiapan, tidak ada kode yang berjalan. Program menunggu — inilah ciri khas alur berbasis event.
3. **Pemain menekan tombol kanan.** Blok "saat tombol_kanan ditekan" langsung dijalankan, dan hanya blok itu. Keranjang bergeser ke kanan.
4. **Apel masuk keranjang.** Blok event lain aktif: skor bertambah 1, lalu kondisi boolean diperiksa. Misalnya skor sekarang 5 dan nyawa 3: syarat skor >= 8 salah, jadi walaupun nyawa > 0 benar, gabungan DAN tetap bernilai salah — belum menang.
5. **Kondisi menang.** Saat skor mencapai 8 dan nyawa masih di atas 0, kedua syarat benar sekaligus, DAN bernilai benar, dan tulisan "Level Selesai!" muncul.

Perhatikan: urutan kejadian di game ditentukan oleh pemain, bukan oleh urutan penulisan kode.

## Miskonsepsi yang Sering Terjadi

::: misconception
Anggapan keliru: pada loop bersarang, loop luar dan loop dalam berjalan bergantian satu langkah — baris 1, kolom 1, lalu baris 2, kolom 2, dan seterusnya.
Yang benar: loop dalam menyelesaikan seluruh putarannya lebih dulu untuk setiap satu putaran loop luar. Pada game di atas, baris 1 diisi apel di kolom 1, 2, 3, 4 sampai tuntas, baru program pindah ke baris 2.
:::

Cara cepat mengeceknya: tulis pasangan (baris, kolom) yang dihasilkan. Urutannya (1,1), (1,2), (1,3), (1,4), (2,1), dan seterusnya — angka kolom berganti cepat, angka baris berganti lambat.

## Ke Mana Ilmu Ini Membawamu

Pola yang kamu latih di sini dipakai di hampir semua pemrograman sungguhan. Loop bersarang dan logika boolean akan kamu tulis lagi di bahasa berbasis teks seperti Python saat jenjang berikutnya, dan seluruh aplikasi modern — game, media sosial, sampai perangkat rumah pintar — dibangun di atas alur berbasis event. Menguasainya sekarang berarti nanti kamu tinggal mengganti bahasanya, bukan cara berpikirnya.

::: check
Q: Skor pemain 7 dan nyawa 2, lalu satu apel masuk keranjang. Apakah "Level Selesai!" tampil? Jelaskan.
A: Ya. Skor menjadi 8, sehingga syarat skor >= 8 benar dan nyawa > 0 juga benar. Karena kedua syarat benar, kondisi DAN bernilai benar dan tulisan tampil.
Q: Mengapa mengganti kondisinya menjadi "skor >= 8 ATAU nyawa > 0" membuat game rusak?
A: ATAU hanya butuh satu syarat benar. Pemain baru dengan skor 0 tapi nyawa 3 akan langsung dinyatakan menang begitu menangkap satu apel, karena nyawa > 0 sudah benar.
:::', NULL, NULL, 8, 0.6, '["k5_control", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_intro_en_v2', 'k8_modularity', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Big Programs, Small Parts: Thinking in Modules', 'Ever wondered how a game like Minecraft or an app like Spotify can have millions of lines of code and still (mostly) work? Nobody''s brain can hold all of that at once — and nobody has to. Big programs are built the same way your best group projects are: split into parts, where each part has one clear job.

## The Big Idea: Modules and Abstraction Layers

A **module** is a self-contained chunk of a program with one clear job. Every good module has:

- a **name** that says what it does
- **inputs** it needs (its parameters)
- an **output** or effect it promises to deliver

Everything else — the messy details of *how* it does its job — stays hidden inside. That hiding is called **abstraction**. When you stack modules so each level only talks to the level below it, you get **abstraction layers**.

You already use abstraction layers every day. When you tap "send" on a message, you don''t think about Wi-Fi signals or servers. Your tap is the top layer; all the details live in layers below.

### A tiny worked example

Say you''re building a virtual pet game. Instead of one giant script, you split it into modules:

```
module PetCare
  feed(pet, food)     -> updates hunger
  play(pet, minutes)  -> updates happiness

module Screen
  drawPet(pet)        -> shows the pet
  showStats(pet)      -> shows hunger + happiness

main program:
  pet = loadPet()
  feed(pet, "apple")
  play(pet, 10)
  drawPet(pet)
  showStats(pet)
```

Read the main program out loud. It''s basically a story: load the pet, feed it, play with it, show it. You can understand the whole game without ever seeing how drawPet colors in pixels. And if the hunger math ever goes wrong, you know exactly which module to open: PetCare, not Screen.

::: check
Q: In the pet game, which module would you open to change how fast hunger goes down, and why?
A: PetCare, because hunger rules are its job. Screen only displays values; it never changes them.
Q: What does abstraction hide from you when you call drawPet(pet)?
A: All the details of how the pet gets drawn. You only need to know what the function does, not how it does it.
:::

Ready for more? The deeper material walks through designing modules for a full project — and shows how layers make bugs dramatically easier to hunt down.', NULL, NULL, 5, 0.3, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_diagram_en_v2', 'k8_modularity', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Abstraction Layers, Stacked Like Floors', 'A modular program is built like a building with floors: each layer stands on the one below it, and you never need to see inside a lower floor to use it. Here is how the layers stack in a simple game.

```
            YOU / THE PLAYER
                   |
                   v
+------------------------------------+
| LAYER 3: MAIN PROGRAM              |
| "show menu, start level, play"     |
+------------------+-----------------+
                   | calls
                   v
+------------------------------------+
| LAYER 2: MODULES                   |
| [Menu]   [Levels]   [Sound]        |
+------------------+-----------------+
                   | hides
                   v
+------------------------------------+
| LAYER 1: LOW-LEVEL DETAILS         |
| pixels, files, speaker signals     |
+------------------------------------+
```

Legend

- Box = one abstraction layer of the program
- [Name] = a single module living inside a layer
- | and v = an arrow showing calls flowing downward
- "calls" = the upper layer uses the lower layer''s functions
- "hides" = the lower layer''s details are invisible from above

How to read it

1. Start at the top: the player only ever touches the main program, nothing deeper.
2. Layer 3 reads like a story — it just calls modules by name in order.
3. Layer 2 modules each own exactly one job: Menu handles choices, Levels handles gameplay, Sound handles audio.
4. Layer 1 holds the messy details, and no layer above it ever deals with them directly.
5. When a bug appears, follow the arrows downward and check the data at each crossing point between layers.

::: tip
When you debug, print or display the data right where an arrow crosses from one layer to the next. The first crossing where the data looks wrong points straight at the guilty module — no need to reread everything.
:::', NULL, NULL, 3, 0.4, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_audio_en_v2', 'k8_modularity', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'One Tap, Many Modules', NULL, NULL, 'Have you ever ordered food with an app? You tap a picture of a pizza, tap the cart, tap pay, and a little while later dinner shows up. In those three taps you used one of the biggest ideas in computer science. It''s called modularity, and today I want you to hear how it works.

A module is a piece of a program that has one clear job. A food app isn''t one giant tangle of code. It has a menu module whose only job is showing what you can order. It has a cart module whose only job is keeping track of your items and adding up the total. And it has a payment module whose only job is handling the money safely. Each module has a name, the information it needs to receive, and the result it promises to give back. Everything else stays hidden inside it.

That hiding has a name too. It''s called abstraction. When you tap pay, you don''t think about bank connections or encryption. And here''s the interesting part: the person who wrote the menu module doesn''t think about them either. Each layer of the program only needs to understand the layer right below it. That''s what programmers mean when they talk about abstraction layers.

Here''s why this matters when things go wrong. Imagine the app charges you for three pizzas when you only ordered two. Where''s the bug? Because the app is modular, a programmer doesn''t reread everything. They follow the number. Did the menu send the right order? Did the cart add it up correctly? Did payment charge exactly what the cart passed in? They test the value at each handoff between modules, and the first handoff where the number is wrong points straight at the guilty module. A bug in a modular program has very few places to hide.

So when you build your own projects, do the same thing. Split the work into modules with one job each, give every module clear inputs and outputs, and connect them layer by layer.

Time for your recap question. What two things do you need to know to use a module, and what do you not need to know? You need to know what inputs it takes and what result it promises to give back. You do not need to know how it works on the inside. That''s abstraction doing its job.', 4, 0.45, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_deep_en_v2', 'k8_modularity', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Bug Hunting Across Modules', 'Quick recap: a module is a chunk of a program with one clear job, and abstraction layers let each part of a program use the parts below it without knowing their inner details.

## Worked Example: The Class Quiz App

Your class is building a quiz app for review day. You design it as three modules, each with functions that take **parameters**. Organizing code with procedures and parameters so it''s easy to reuse is exactly what standard CSTA 2-AP-14 asks middle schoolers to master.

```
module Questions
  getQuestion(n)        -> returns question n
  checkAnswer(n, guess) -> returns true or false

module Scoring
  addPoints(score, correct) -> returns new score

module Screen
  askPlayer(question)   -> returns the player''s guess
  showScore(score)
```

The main program becomes one clean loop:

```
score = 0
for n from 1 to 10
  q = getQuestion(n)
  guess = askPlayer(q)
  correct = checkAnswer(n, guess)
  score = addPoints(score, correct)
showScore(score)
```

Then a bug shows up: a player gets 7 answers right, but the app shows 14 points. Time to debug **across modules** by checking each boundary — the places where data passes from one module to another.

1. Test checkAnswer alone with answers you already know. It returns true and false correctly. Not the bug.
2. Test addPoints(0, true) alone. It returns 2 instead of 1. Found it!
3. Open Scoring and look inside: someone wrote score = score + 2. One-line fix.

Notice what you did *not* do: you never reread the whole program. Because each module has one job with clear inputs and outputs, you could test them one at a time, like checking links in a chain — and the bug had nowhere to hide.

## A Trap to Avoid

::: misconception
Wrong belief: "The score displays wrong, so the bug must be in the Screen module — that''s where I saw the problem."
Correction: The place a bug *appears* is often not where it *lives*. Data flows through layers, so a wrong value on screen may have been broken upstream in Scoring or Questions. Trace the value backward, testing at each module boundary, until you find the first place it goes wrong. That module owns the bug.
:::

## Where This Leads

Modular thinking is one of the most transferable skills in all of computing. It''s how professional teams split big apps into services, how game studios let dozens of people build one game without stepping on each other''s code, and how you''ll soon use libraries and APIs — code written by total strangers that you can trust because its inputs and outputs are clearly promised. Every large system you build or debug from here on, in high school CS and beyond, runs on the layer-by-layer thinking you''re practicing now.

::: check
Q: Your Weather module returns temperature in Fahrenheit, but the Screen module that uses it expects Celsius, so the display is wrong. Where does this bug live?
A: At the boundary between the two modules. Each module works fine alone, but they disagree on the "contract" for the data they pass. Fix it by agreeing on one unit and converting in one clearly chosen place.
Q: A wrong value shows on screen and your program has four layers. What is the fastest way to find the broken layer?
A: Check the value at each boundary between layers, working backward from the screen. The first boundary where the value is already wrong tells you exactly which module to open.
:::', NULL, NULL, 8, 0.6, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_intro_id_v2', 'k8_modularity', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Membangun Program dari Modul-Modul Kecil', 'Pernah penasaran bagaimana game favoritmu atau aplikasi chat yang kamu pakai setiap hari bisa dibuat? Tidak ada satu orang pun yang menulis seluruh kodenya sekaligus dalam satu file raksasa. Program besar selalu dibangun dari bagian-bagian kecil yang disebut **modul** — dan di materi ini kamu akan belajar merancang program dengan cara yang sama.

## Ide Besar: Modul dan Lapisan Abstraksi

Sebuah **modul** adalah bagian program yang punya satu tugas jelas, mirip pembagian tugas dalam kerja kelompok. **Abstraksi** artinya menyembunyikan detail: pemakai modul cukup tahu *apa* yang dilakukan modul itu, tanpa perlu tahu *bagaimana* caranya.

Program modular tersusun dalam **lapisan abstraksi**:

- **Lapisan atas**: program utama, berisi perintah-perintah besar yang mudah dibaca.
- **Lapisan tengah**: modul-modul yang menjalankan tiap perintah besar.
- **Lapisan bawah**: detail kecil di dalam tiap modul.

Cara berpikir seperti ini adalah inti standar berpikir komputasional AP-K8-5: memecah masalah menjadi bagian-bagian, lalu menyusunnya kembali menjadi program yang bisa diuji satu per satu.

### Contoh: Game Lompat Rintangan

Coba baca program utama game sederhana ini:

```
selama permainan berjalan:
    gerakkanPemain()
    munculkanRintangan()
    jika cekTabrakan() bernilai benar:
        akhiriPermainan()
    perbaruiSkor()
```

Program utama terasa seperti daftar isi buku — pendek dan jelas. Detailnya disimpan di dalam modul, misalnya:

```
fungsi cekTabrakan():
    jika kotak pemain bersentuhan dengan kotak rintangan:
        kembalikan benar
    jika tidak:
        kembalikan salah
```

Bagian terpentingnya: program utama sama sekali tidak peduli *bagaimana* cekTabrakan() bekerja. Suatu hari kamu bisa mengganti isinya — misalnya memakai deteksi lingkaran, bukan kotak — tanpa mengubah program utama sedikit pun. Itulah kekuatan abstraksi: setiap lapisan hanya perlu tahu secukupnya.

::: check
Q: Apa keuntungan program utama hanya berisi panggilan seperti gerakkanPemain() tanpa memuat detailnya?
A: Program utama jadi mudah dibaca seperti ringkasan, dan detail tiap modul bisa diubah atau diperbaiki tanpa perlu mengubah program utama.
Q: Jika kamu ingin mengubah cara skor dihitung, bagian mana yang perlu kamu buka?
A: Cukup modul perbaruiSkor(); program utama dan modul-modul lain tidak perlu disentuh sama sekali.
:::

Di materi pendalaman, kamu akan merancang satu aplikasi utuh dari nol — dan belajar melacak bug licik yang bersembunyi di antara dua modul.', NULL, NULL, 5, 0.3, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_diagram_id_v2', 'k8_modularity', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Lapisan Abstraksi Program Modular', 'Program modular tersusun seperti piramida: perintah besar di atas, detail kecil di bawah. Diagram ini memetakan lapisan abstraksi sebuah aplikasi pemutar musik sederhana.

```
+---------------------------------------------+
|  LAPISAN ATAS: PROGRAM UTAMA                |
|  "mainkan lagu favorit pengguna"            |
+---------------------+-----------------------+
                      |
      +---------------+--------------+
      |               |              |
      v               v              v
+-----------+  +-----------+  +------------+
| Modul     |  | Modul     |  | Modul      |
| Playlist  |  | Audio     |  | Layar      |
+-----+-----+  +-----+-----+  +-----+------+
      |              |              |
      v              v              v
 cariLagu()    mainkanFile()   tulisJudul()
```

Legend:

- Kotak (garis +, -, dan |): satu bagian program — program utama atau sebuah modul.
- Garis | dan panah v: arah "memanggil" — bagian di atas menyuruh bagian di bawahnya bekerja.
- Tulisan dalam tanda kutip: tugas besar yang dipahami lapisan atas.
- namaFungsi(): fungsi berisi detail pekerjaan di lapisan paling bawah.

Cara membaca diagram:

1. Mulai dari kotak paling atas: program utama hanya tahu satu tugas besar, "mainkan lagu favorit pengguna".
2. Ikuti panah ke bawah: tugas besar itu dibagi ke tiga modul — Playlist memilih lagu, Audio membunyikannya, Layar menampilkan informasinya.
3. Turun sekali lagi: setiap modul menyimpan fungsi detailnya sendiri, seperti cariLagu() di dalam modul Playlist.
4. Perhatikan bahwa panah hanya mengalir ke bawah: lapisan atas tidak perlu tahu detail lapisan bawah — itulah abstraksi.
5. Saat ada bug, telusuri jalur panahnya: temukan gejala, lalu periksa modul-modul di sepanjang jalur itu satu per satu.

::: tip
Sebelum menulis kode, gambarlah diagram lapisan seperti ini di kertas. Kalau ada kotak yang tugasnya sulit dijelaskan dalam satu kalimat, itu tanda kotak tersebut perlu dipecah menjadi dua modul.
:::', NULL, NULL, 3, 0.4, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_audio_id_v2', 'k8_modularity', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Rahasia Program Besar: Bagian-Bagian Kecil yang Kompak', NULL, NULL, 'Hai. Hari ini kita membahas salah satu rahasia terbesar para pembuat aplikasi dan game, yaitu modularitas. Modularitas adalah seni membangun program besar dari bagian-bagian kecil yang masing-masing punya tugas jelas.

Bayangkan sekolahmu mengadakan pentas seni. Kalau satu orang harus mengurus semuanya, mulai dari panggung, musik, konsumsi, tiket, sampai dokumentasi, acaranya hampir pasti berantakan. Karena itu dibentuk panitia dengan divisi-divisi. Ketua panitia cukup berkata, divisi konsumsi, siapkan tiga ratus kotak makanan. Ketua tidak perlu tahu resepnya atau nama kateringnya. Yang penting, divisi konsumsi paham tugasnya dan menghasilkan sesuatu yang jelas.

Program modular bekerja persis seperti itu. Program utama berperan seperti ketua panitia, isinya hanya perintah-perintah besar. Setiap perintah besar dikerjakan oleh sebuah modul, dan setiap modul menyimpan detail pekerjaannya sendiri. Menyembunyikan detail seperti ini disebut abstraksi. Berkat abstraksi, kamu bisa membaca program utama seperti membaca ringkasan cerita, dan kamu bisa memperbaiki isi satu modul tanpa merusak modul yang lain.

Modularitas juga membuatmu lebih jago mencari bug. Kembali ke pentas seni tadi. Kalau semua fotonya buram, kamu tidak perlu menginterogasi seluruh panitia. Kamu langsung menemui divisi dokumentasi. Tapi hati-hati, kadang sumber masalahnya ada di divisi lain. Mungkin divisi acara memberikan jadwal yang salah, sehingga fotografernya datang terlambat dan memotret terburu-buru. Dalam program juga begitu. Kesalahan bisa terlihat di satu modul, padahal sumbernya adalah data keliru yang dikirim oleh modul lain. Karena itu, pemrogram yang andal selalu memeriksa perbatasan antarmodul, yaitu data apa yang keluar dari modul pertama, dan data apa yang sebenarnya diharapkan oleh modul berikutnya.

Jadi, kalau kamu ingin membuat game atau aplikasi, mulailah dengan membagi programmu menjadi modul-modul dengan tugas yang jelas, sepakati apa yang masuk dan keluar dari tiap modul, lalu uji setiap modul satu per satu.

Sekarang satu pertanyaan pengingat. Kalau hasil akhir programmu salah, apakah bug pasti berada di modul yang menampilkan hasil itu? Jawabannya, belum tentu. Gejala bisa muncul di satu modul, tetapi sumbernya bisa berada di modul lain yang mengirim data keliru. Lacaklah datanya mundur, dari tempat gejala muncul menuju sumbernya, sambil memeriksa setiap perbatasan antarmodul.', 4, 0.45, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_deep_id_v2', 'k8_modularity', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Berburu Bug Lintas Modul: Studi Kasus Aplikasi Kantin', 'Kamu sudah tahu ide besarnya: program besar dibangun dari modul-modul bertugas jelas yang tersusun dalam lapisan abstraksi. Sekarang kita rancang satu aplikasi utuh, lalu berburu bug yang bersembunyi di antara dua modul.

## Merancang Aplikasi Pemesanan Kantin

Sekolahmu ingin aplikasi agar siswa bisa memesan makanan kantin dari kelas. Rancangan lapisan atasnya:

```
mulai:
    tampilkanMenu()
    pesanan = ambilPesanan()
    total = hitungTotal(pesanan)
    prosesPembayaran(total)
```

Empat modul, empat tugas. Sebelum menulis detailnya, tim menyepakati **kontrak antarmuka**: apa yang masuk dan keluar dari tiap modul.

| Modul | Menerima | Mengembalikan |
| --- | --- | --- |
| tampilkanMenu | tidak ada | tidak ada |
| ambilPesanan | tidak ada | daftar item pesanan |
| hitungTotal | daftar item | total harga |
| prosesPembayaran | total harga | tidak ada |

Suatu hari muncul bug: apa pun yang dipesan, totalnya selalu Rp0. Begini cara melacaknya lintas modul:

1. **Reproduksi bug**: jalankan aplikasi, pesan bakso dan es teh. Total tetap Rp0. Bug terkonfirmasi.
2. **Uji modul secara terpisah**: panggil hitungTotal dengan data buatan berisi harga, misalnya hitungTotal([12000, 5000]). Hasilnya 17000 — benar! Berarti mesin di dalam modul ini sehat.
3. **Periksa perbatasan modul**: cetak isi variabel pesanan tepat setelah ambilPesanan selesai. Ternyata isinya ["bakso", "es teh"] — daftar *nama*, bukan daftar *harga*.
4. **Temukan akar masalah**: ambilPesanan mengirim nama makanan, padahal hitungTotal mengharapkan harga. Kedua modul terasa "benar" sendiri-sendiri, tetapi kontrak antarmukanya tidak cocok.
5. **Perbaiki kontraknya**: sepakati bahwa ambilPesanan mengembalikan pasangan (nama, harga), lalu sesuaikan hitungTotal:

```
fungsi hitungTotal(pesanan):
    total = 0
    untuk setiap item dalam pesanan:
        total = total + harga milik item
    kembalikan total
```

Pelajaran pentingnya: bug lintas modul paling sering tinggal di *perbatasan* — tempat data berpindah dari satu modul ke modul lain.

## Miskonsepsi Umum

::: misconception
Keliru: "Kalau angka yang salah muncul di layar pembayaran, berarti bugnya pasti ada di modul prosesPembayaran."
Yang benar: gejala dan sumber bug sering berada di modul yang berbeda. prosesPembayaran hanya menampilkan angka yang ia terima; jika angka itu sudah salah sejak ambilPesanan atau hitungTotal, modul pembayaran tidak bersalah. Lacaklah data mundur dari tempat gejala muncul sampai kamu menemukan modul pertama yang mengeluarkan data keliru.
:::

## Ke Mana Keterampilan Ini Membawamu

Apa yang kamu pelajari di sini adalah cara kerja pemrogram profesional di mana pun. Saat kamu memakai pustaka (library) buatan orang lain, kamu sebenarnya memanggil modul yang detailnya tidak pernah kamu baca — kamu hanya memegang kontrak antarmukanya. Kebiasaan menyepakati kontrak, menguji modul satu per satu, dan memeriksa perbatasan antarmodul akan langsung terpakai saat kamu membangun proyek yang lebih besar: game bertingkat, situs web, robot, atau proyek kelompok pemrograman di jenjang berikutnya.

::: check
Q: hitungTotal terbukti benar saat diuji sendiri, tetapi total di aplikasi tetap salah. Apa langkah paling cerdas berikutnya?
A: Periksa perbatasan antarmodul: amati data yang benar-benar dikirim ke hitungTotal saat aplikasi berjalan, karena kemungkinan besar formatnya tidak sesuai kontrak antarmuka.
Q: Kantin ingin memberi diskon 10% khusus hari Jumat. Bagaimana menambahkannya tanpa mengganggu modul lain?
A: Buat modul baru, misalnya terapkanDiskon(total), lalu panggil di program utama di antara hitungTotal dan prosesPembayaran; kontrak modul-modul lain tidak perlu berubah.
:::', NULL, NULL, 8, 0.6, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_reading_intro_en_v2', 'k8_variables', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'When One Variable Isn''t Enough: Lists and Scope', 'Your favorite game doesn''t track your inventory with fifty separate variables, and your music app doesn''t store a playlist one song at a time. Real programs manage whole collections of data at once, and they''re built from many functions that each need the right access to that data. Learning to handle that is what separates a toy script from a real app.

## From One Box to a Whole Shelf

In earlier grades, a variable was one labeled box holding one value: `score = 10` or `name = "Ada"`. That still works, but bigger programs need two upgrades:

1. **Lists** — a single variable that holds many values in order. Each value sits at a numbered position called an **index**, and indexes start counting at **0**, not 1.
2. **Scope** — once a program has more than one function, every variable has a "home territory" that decides which parts of the code can see and use it.

Variables can also hold different **data types**: numbers, text (called strings), true/false values (called booleans), and lists that hold any of these. Choosing the right type and doing operations on it is the heart of the standard CSTA 2-AP-09.

### Follow along: fixing a playlist

Read this pseudocode line by line and predict what happens:

```
playlist = ["Skyline", "Firefly", "Echo"]

print playlist[0]         // prints "Skyline"
add "Nova" to playlist    // now 4 songs
remove playlist[1]        // "Firefly" is gone
print length of playlist  // prints 3
```

Trace it: `playlist[0]` is the *first* song because indexes start at 0. After adding "Nova" the list has 4 items. Removing index 1 deletes "Firefly", the second item. The final list is `["Skyline", "Echo", "Nova"]`.

Notice what you never had to do: create a new variable. One name, `playlist`, held a collection that grew and shrank while the program ran. That''s the power move — one variable, many values, all under your control.

::: check
Q: If scores = [10, 25, 40], what value is scores[1]?
A: 25 — list positions start counting at 0, so index 1 is the second item, not the first.
Q: Why would a game use one list called inventory instead of separate variables like item1, item2, and item3?
A: A list can grow and shrink as the player picks up or drops items, and the program can loop through it or count it — a fixed set of separate variables can''t do any of that.
:::

In the deeper read, you''ll build a multi-function program and see exactly why a variable created inside one function is completely invisible everywhere else.', NULL, NULL, 5, 0.3, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_diagram_en_v2', 'k8_variables', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Where Variables Live: Boxes Inside Boxes', 'Scope is easiest to picture as boxes inside boxes. Here is a mini game program with one global list and two functions, drawn as a map of who can see what.

```
+------------- GLOBAL SCOPE --------------+
| scores = [12, 30, 45]                   |
|                                         |
|   +------ function add_score ------+    |
|   | points = 50         (local)    |    |
|   | scores <--- can see & change   |    |
|   +--------------------------------+    |
|                                         |
|   +------ function show_best ------+    |
|   | best = 50           (local)    |    |
|   | points <-X- cannot see         |    |
|   +--------------------------------+    |
+-----------------------------------------+
```

**Legend**

- Outer box = global scope, the whole program
- Inner boxes = local scope, one for each function
- `(local)` = a variable that exists only while its function is running
- `<---` = allowed: this function can read and change that variable
- `<-X-` = blocked: that variable is invisible from here

**How to read it**

1. Start at the outer box. `scores` was created at the top level, so it sits in global scope and is visible from everywhere, including inside both inner boxes.
2. When `add_score` runs, it creates its own local variable `points` inside its box, and it can also reach *outward* to read and change the global `scores` list.
3. The moment `add_score` finishes, `points` is erased — but any change it made to `scores` stays, because `scores` lives in the outer box.
4. `show_best` has its own local variable `best`. It cannot see `points`, because `points` belongs to a *different* inner box that isn''t even running anymore.
5. Remember the rule the arrows show: inner boxes can look out, but nothing can look into an inner box from outside.

::: tip
When you hit a "variable is not defined" error, ask one question: which box was this variable born in? If it was born inside a function, it can''t be used outside that function — return the value instead, or create the variable at the top level on purpose.
:::', NULL, NULL, 3, 0.4, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_audio_en_v2', 'k8_variables', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Whiteboards and Sticky Notes: How Scope Works', NULL, NULL, 'Think about a group project at school. There''s the class whiteboard at the front of the room, where anyone in any group can write, and everyone can read what''s there. Then there are the sticky notes on your own desk. You can scribble on those all you want, but when class ends, they go in the recycling bin, and nobody in another group ever sees them. Programs that are built from multiple functions work exactly like this.

By now you know that a variable is a named container for a value. Here''s the upgrade. First, a variable can hold a whole collection of values at once. That''s called a list. Instead of making thirty separate variables for thirty quiz questions, you make one list called questions, and it holds all of them in order. You can add items to it, remove items from it, and count how many it has, all through that one name.

Second, and this is the part that trips people up, every variable has a home, called its scope. A variable created at the top of your program, outside any function, is like the class whiteboard. We call it global. Every function can read it and change it. But a variable created inside a function is like a sticky note on your desk. It''s local. It appears when the function starts running, and the moment the function finishes, it gets thrown away.

Say you''re building a quiz game. Your list of questions is global, created at the top, so both your ask question function and your grade answer function can use it. But inside the ask question function, you create a variable called reply to hold whatever the player typed. When that function finishes, reply is gone. If the grade answer function needs that value, the ask question function has to hand it over by returning it, the same way you''d have to copy your sticky note onto the whiteboard for another group to see it.

So here''s your recap question. If a variable is created inside a function, can the rest of the program use it after that function finishes? The answer is no. It''s local, so it''s erased when the function ends. If you want to keep the value, return it from the function, or store it in a global variable on purpose.', 4, 0.45, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_reading_deep_en_v2', 'k8_variables', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Lists, Functions, and Who Can See What', 'Quick recap of the big idea: one variable can hold an entire list of values, and in a program with multiple functions, every variable has a **scope** — the region of code where it exists and can be used.

## Worked Example: The Pizza Order App

Imagine your group is building an app to collect pizza orders for a class party. Here''s the whole program:

```
orders = []                        // created at top level

function add_order(name, topping):
    order = name + ": " + topping  // created inside
    add order to orders
    print order + " saved"

function summary():
    total = length of orders       // created inside
    print "We have " + total + " orders"

add_order("Maya", "mushroom")
add_order("Jun", "cheese")
summary()
```

Walk through it step by step:

1. The first line runs at the top level, outside every function. That makes `orders` a **global** variable: every function in the file can see it. Right now it''s an empty list.
2. `add_order("Maya", "mushroom")` runs. The parameters `name` and `topping` are **local** — they exist only inside this one call. The function builds the local string `order`, which is `"Maya: mushroom"`, and adds it to the global list. When the function ends, `name`, `topping`, and `order` are all erased.
3. But `orders` still holds one item! The list lives in global scope, so changes to it survive after the function finishes.
4. The second call repeats the process with brand-new locals, and `orders` grows to 2 items.
5. `summary()` creates its own local `total`, counts the list, and prints "We have 2 orders".
6. Now the trap: if the last line of the program were `print order`, it would crash. `order` was born inside `add_order` and no longer exists.

Look at the types in play: `orders` is a list, `name` and `topping` and `order` are strings, and `total` is a number. One small program, several data types, each doing its job.

## The Misconception That Breaks Programs

::: misconception
Wrong belief: "If I create a variable inside a function, the rest of my program can use it too."
Correction: a variable created inside a function is **local** — it exists only while that function is running, then it''s erased. If two functions each create a variable called `total`, those are two completely separate variables that never affect each other, even though they share a name. To share a value, either return it from the function or store it in a variable created at the top level.
:::

## Where This Takes You

Everything in this concept transfers directly to real programming languages. In Python or JavaScript, lists become the arrays you''ll use in nearly every project, and these exact scope rules explain the most common bugs beginners hit. The same thinking scales up to richer structures like dictionaries and objects, which are really just variables holding labeled collections. And when you debug a teammate''s code in a group project, scope is the map that tells you where every variable lives and dies.

::: check
Q: In the pizza app, why does orders keep its items after add_order finishes, while order disappears?
A: orders was created at the top level, so it''s global and outlives every function call. order was created inside add_order, so it''s local and gets erased the moment the function ends.
Q: Two different functions each create their own variable named count. One function sets its count to 99. What happens to the other function''s count?
A: Nothing — same name, but they are two separate local variables living in two separate scopes, so changing one never touches the other.
:::', NULL, NULL, 8, 0.6, '["k5_variables"]'::jsonb);
COMMIT;