BEGIN;
DELETE FROM learning_materials WHERE concept_id = 'k12_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k12_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k12_control' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k12_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k12_data_collection' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k12_data_collection' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_computing_systems_devices' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_computing_systems_devices' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_control' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_culture' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_culture' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_data_collection' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_data_collection' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_modularity' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_modularity' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_networks_communication' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_networks_communication' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_program_development' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_program_development' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k2_variables' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k2_variables' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_computing_systems_devices' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_computing_systems_devices' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_control' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_culture' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_culture' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_data_collection' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_data_collection' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_modularity' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_modularity' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_networks_communication' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_networks_communication' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_program_development' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_program_development' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k5_variables' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k5_variables' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_algorithms' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_algorithms' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_computing_systems_devices' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_computing_systems_devices' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_control' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_control' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_culture' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_culture' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_data_collection' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_data_collection' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_modularity' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_modularity' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_networks_communication' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_networks_communication' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_program_development' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_program_development' AND language = 'id';
DELETE FROM learning_materials WHERE concept_id = 'k8_variables' AND language = 'en';
DELETE FROM learning_materials WHERE concept_id = 'k8_variables' AND language = 'id';
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_reading_intro_en_v2', 'k12_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Why Fast Beats Clever: Designing Algorithms That Scale', 'When you type three letters and your phone instantly surfaces the right contact out of thousands, that speed is not luck — it is design. Every app you rely on, from maps to matchmaking in games, works because an engineer asked one question before shipping: *what happens on the worst possible input?* Learning to ask — and answer — that question is the skill this concept builds.

## The big idea: design for the worst case, not the demo

An algorithm that merely works is table stakes. At this level, the engineering questions get sharper:

- **Correctness on edge cases.** Empty input? Duplicates? The target missing entirely?
- **Worst-case cost.** As input size *n* grows, how does the number of steps grow — like *n*? Like *n²*? Like log *n*?
- **Tradeoffs.** Can you spend memory to save time? Sacrifice simplicity to gain speed?

We summarize growth with **Big-O notation**: O(n) means work grows in proportion to input size; O(n²) means doubling the input roughly quadruples the work; O(log n) means doubling the input adds only one extra step. Evaluating and comparing algorithms this way is the heart of CSTA standard 3A-AP-10 — and of real software engineering.

### Worked example: one contact among a million

Suppose a sorted contact list holds 1,048,576 entries (that is 2 to the 20th power). A **linear search** checks entries one by one:

```
function linearSearch(list, target):
    for i = 0 to length(list) - 1:
        if list[i] == target:
            return i
    return NOT_FOUND
```

Worst case — the name is last, or absent — that is 1,048,576 checks. Now exploit the sorted order. **Binary search** compares against the middle entry and discards half the list each round:

```
function binarySearch(sorted, target):
    lo = 0
    hi = length(sorted) - 1
    while lo <= hi:
        mid = (lo + hi) / 2    // integer division
        if sorted[mid] == target:
            return mid
        else if sorted[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return NOT_FOUND
```

Halving 1,048,576 repeatedly — 524,288, 262,144, and so on down to 1 — takes exactly 20 halvings. Worst case: about **20 comparisons instead of a million**. Same problem, same computer; a massive gap created purely by algorithm design. The tradeoff: binary search demands sorted data, so if your data changes constantly, keeping it sorted carries its own cost.

::: check
Q: In the worst case, how many entries does linear search examine in a list of n items, and what input causes that?
A: All n entries — the worst case occurs when the target is the last element or not in the list at all.
Q: Why does binary search require sorted data?
A: Each comparison discards half the list only because sorted order guarantees which half must contain the target; on unsorted data that guarantee disappears.
:::

In the deeper reading, you will take a slow brute-force solution and re-engineer it into a fast one, step by step.', NULL, NULL, 5, 0.3, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_diagram_en_v2', 'k12_algorithms', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Optimization Loop Every Engineer Runs', 'Optimization is not a single trick — it is a cycle engineers repeat until the worst case is acceptable. This diagram shows that cycle from first idea to shipped code.

```
+--------------------+
| Problem, size n    |
+--------------------+
          |
          v
+--------------------+
| Design algorithm   |<----------------+
+--------------------+                 |
          |                            |
          v                            |
+--------------------+                 |
| Find worst-case    |                 |
| input              |                 |
+--------------------+                 |
          |                            |
          v                            |
+--------------------+   too slow ->   |
| Count steps f(n)   |-----------------+
| -> O(...) class    |
+--------------------+
          |
          v  fast enough
+--------------------+
| Ship it + test     |
| edge cases         |
+--------------------+
```

Legend:

- Boxes = stages of the engineer''s workflow
- Downward `|` and `v` arrows = the normal analysis flow
- The line on the right looping back up = the redesign (optimization) cycle
- `f(n)` = step count as a formula in input size n
- `O(...)` = the growth class that formula belongs to, such as O(n) or O(n²)

How to read it:

1. Start at the top: state the problem and how large the input n can realistically get.
2. Design a candidate algorithm — brute force is a legitimate first draft.
3. Hunt for the worst-case input: the one that forces the most steps, such as a missing target or data arranged in the most hostile order.
4. Count the steps as a formula in n and reduce it to a growth class.
5. If that class is too slow for your n, follow the loop-back arrow: redesign with a better data structure, pre-sorting, or pruned work, then re-analyze. Only when the worst case is acceptable do you exit downward and ship.

::: tip
Before optimizing, plug your real maximum n into the growth class. If n never exceeds 100, an O(n²) algorithm does at most about 10,000 steps — already instant. Optimize only when the math says the worst case actually hurts.
:::', NULL, NULL, 3, 0.4, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_audio_en_v2', 'k12_algorithms', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Thinking in Worst Cases', NULL, NULL, 'Imagine your school gives every student an ID number, and you are asked to write a program that checks whether any two of the two thousand students accidentally received the same ID. How would you do it?

The obvious plan is to compare every ID with every other ID. That is a fine first draft, and it is always worth writing. But before you trust it, ask the question professional engineers always ask: what happens in the worst case? Here, the worst case is when there are no duplicates at all, because then the program can never stop early. It must compare every possible pair. With two thousand students, that is nearly two million comparisons. And here is the dangerous part. If the school grows to twenty thousand students, ten times bigger, the work does not grow ten times. It grows about one hundred times, to almost two hundred million comparisons. When doubling the input quadruples the work, we call that quadratic growth.

Now consider a redesign. First, sort the IDs. Sorting two thousand numbers with a good algorithm takes roughly two thousand times eleven steps, around twenty two thousand operations. After sorting, any duplicates must sit right next to each other. So you make one single pass down the list, comparing each ID only to its neighbor. That is just two thousand quick checks. In total, you have done under thirty thousand steps instead of two million, and the gap grows even more dramatic as the school gets bigger.

Notice what changed. Not the computer, and not the programming language. Only the algorithm. That is what this whole topic is about: designing a procedure, finding the input that hurts it most, counting the steps that input forces, and redesigning until the worst case is something you can live with. There are tradeoffs too. Sorting rearranges the data, so if you needed the original order, you would keep a copy, and that costs memory.

Here is your recap question. Why do we judge algorithms by their worst case instead of their best case? Think about it for a moment. The answer: because the best case is luck, but the worst case is a guarantee. If the worst case is fast enough, the program is fast enough for every user, every time, even on the most hostile input.', 4, 0.45, '["k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_algorithms_reading_deep_en_v2', 'k12_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'From Brute Force to Optimal: Worst-Case Thinking in Action', 'The big idea in one line: judge an algorithm by how its worst-case step count grows with input size n, then redesign until that growth curve is acceptable.

## Worked example: does any pair sum to the target?

Problem: given an array a of n integers and a target T, report whether any two different elements sum to T.

**Version 1 — brute force.** Try every pair (n is the length of a):

```
function pairSum_v1(a, T):
    for i = 0 to n - 2:
        for j = i + 1 to n - 1:
            if a[i] + a[j] == T:
                return (i, j)
    return NONE
```

The worst case is when no pair works: both loops run to completion, checking n(n−1)/2 pairs — that is O(n²). For n = 10,000, about 50 million comparisons. For n = 1,000,000, about 500 billion — minutes or hours, not milliseconds.

**Version 2 — trade memory for time.** As we scan, remember what we have seen. A new value x completes a pair exactly when T − x has already appeared:

```
function pairSum_v2(a, T):
    seen = empty hash set
    for each x in a:
        if (T - x) in seen:
            return FOUND
        add x to seen
    return NONE
```

Trace it on a = [8, 3, 11, 5] with T = 14:

1. x = 8: is 6 in seen? No. seen = {8}
2. x = 3: is 11 in seen? No. seen = {8, 3}
3. x = 11: is 3 in seen? Yes — FOUND.

One pass, one cheap hash lookup per element: O(n) expected time, at the price of O(n) extra memory. Note the edge case handled by checking *before* inserting: if T = 16 and the value 8 appears only once, we never falsely pair 8 with itself.

The engineering lesson: the speedup came from neither a faster computer nor tighter code. It came from choosing a data structure with cheap lookups and restructuring the algorithm around it.

## Common misconception

::: misconception
Wrong belief: "O(n) code is always faster than O(n²) code, so Big-O tells me which program wins on any input."
Correction: Big-O describes how cost grows as n gets large, in the worst case — it deliberately hides constant factors and small-input behavior. At n = 20, the brute-force version may actually run faster, because hash sets carry per-operation overhead. Analyze the growth class first, then measure real timings at realistic input sizes before declaring a winner.
:::

## Where this leads

This concept is the capstone of the algorithms strand in this curriculum, so nothing here sits above it — but the skill transfers far beyond it. Worst-case reasoning is the backbone of college data structures and algorithms courses, it is the shared language of technical interviews, and it is how working engineers decide whether a database query, a game physics loop, or a machine-learning pipeline will survive real-world scale. Wherever you write code next, this habit of mind goes with you.

::: check
Q: An algorithm runs a loop n times, and each iteration performs a binary search over n sorted items. What is its worst-case complexity?
A: O(n log n) — n iterations, each costing about log n comparisons, multiply to n log n total.
Q: pairSum_v2 is O(n) time but O(n) extra memory, while pairSum_v1 is O(n²) time and O(1) memory. Give one situation where version 1 is the better engineering choice.
A: When n is guaranteed to stay small or memory is severely constrained, such as on an embedded device — quadratic cost is negligible at tiny n, and constant memory can matter more than raw speed.
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
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_reading_intro_en_v2', 'k12_control', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Loops Inside Loops: Why Nested Code Gets Slow Fast', 'Every time a game checks whether any two objects on screen are colliding, or an app scans your contacts against its user database, nested control structures are doing the work. Whether that check finishes in a blink or freezes the frame depends on the *shape* of the code. By the end of this lesson you will be able to predict the cost of a program just by reading its structure — before you ever run it.

## The Big Idea: Nesting Multiplies, Sequencing Adds

You already know the core control structures: sequence, selection (IF), and iteration (loops). The next level is analyzing what happens when you put them *inside each other*. Three rules cover almost everything:

- Statements in **sequence** add their costs.
- A **loop** multiplies the cost of its body by the number of iterations.
- A **loop inside a loop** multiplies again.

Here is a real problem: a site with a list of `n` usernames wants to warn about duplicates.

```
FOR i FROM 0 TO n - 1
    FOR j FROM 0 TO n - 1
        IF i != j AND names[i] == names[j] THEN
            OUTPUT names[i] + " appears twice"
        END IF
    END FOR
END FOR
```

Follow along with n = 4. When i = 0, the inner loop runs j = 0, 1, 2, 3 — so the IF test executes 4 times. The same happens for i = 1, i = 2, and i = 3. Total: 4 × 4 = **16 comparisons**. No problem.

Now scale it. With n = 10,000 users, this exact same code performs 10,000 × 10,000 = **100,000,000 comparisons**. Doubling the input *quadruples* the work — the signature of a quadratic, or n², algorithm. And here is the engineering payoff: you can see all of this from the structure alone. Two nested loops, each of whose bounds scales with input size, means n² work.

One more habit worth building: think about the **worst case**. Even when there are zero duplicates, this code still does every one of its n² checks, because nothing in the control flow lets it stop early. Best case and worst case are identical here.

::: check
Q: A loop runs n times, and on every pass an inner loop runs n times. How many times does the innermost statement execute?
A: n × n = n² times. For 10 items that is 100 executions; for 1,000 items it is 1,000,000.
Q: Two loops written one after the other (not nested), each running n times, do how much total work?
A: n + n = 2n. Sequential loops add their costs; only nested loops multiply them.
:::

In the deeper read, you will trace a nested search that *can* exit early — and see why two nested loops do not always mean n².', NULL, NULL, 5, 0.3, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_diagram_en_v2', 'k12_control', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Anatomy of a Nested Loop', 'Every nested loop, whatever it computes, shares one skeleton: an outer cycle that starts and finishes a *complete* inner cycle on every pass. This flowchart is that skeleton.

```
        +------------------+
        | outer: i = 0     |
        +--------+---------+
                 |
                 v
  +---->+------------------+
  |     |     i < n ?      +--no--> DONE
  |     +--------+---------+
  |              | yes
  |              v
  |     +------------------+
  |     | inner: j = 0     |
  |     +--------+---------+
  |              |
  |              v
  | +-->+------------------+
  | |   |     j < n ?      +--no--+
  | |   +--------+---------+      |
  | |            | yes            |
  | |            v                |
  | |   +------------------+      |
  | |   | BODY (the work)  |      |
  | |   | j = j + 1        |      |
  | |   +--------+---------+      |
  | +------------+                |
  |                               |
  |     +------------------+      |
  +-----+    i = i + 1     +<-----+
        +------------------+
```

Legend:
- Plain boxes: a step the computer performs
- Boxes containing `?`: decision tests with yes/no exits
- `v` and `-->`: the direction control flows
- Vertical lines running back upward: loop-back paths (repetition)
- DONE: the single exit, reached only when the outer test fails

How to read it:

1. Control enters at the top: the outer counter i is set to 0.
2. The outer test `i < n ?` either ends everything (no → DONE) or drops into the inner loop — and notice j is **reset to 0 on every outer pass**. That reset is why the work multiplies.
3. The inner cycle spins: test j, run BODY, increment j, loop back — n times.
4. When the inner test finally fails, control slides down the right edge to `i = i + 1`, then climbs the left edge back to the outer test.
5. Count visits: BODY runs n times per outer pass × n outer passes = n² total.

::: tip
Do not read nested code top-to-bottom like prose. First find each loop''s test and its loop-back arrow, then ask how many times each back-arrow is taken. Tracing on paper with a tiny value like n = 3 catches most off-by-one errors before the code ever runs.
:::', NULL, NULL, 3, 0.4, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_audio_en_v2', 'k12_control', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'How Nested Loops Multiply Work', NULL, NULL, 'Let''s talk about what happens when you put one loop inside another, because it is the single biggest reason programs suddenly get slow.

Suppose you are writing scheduling software for a round-robin chess tournament, where every player must play every other player. Your code has an outer loop that walks through the list of players one at a time. Inside it, a second loop walks through the whole list again, pairing the current player with each possible opponent.

Now think about the cost. With ten players, the outer loop runs ten times, and on each of those passes the inner loop runs ten times. Ten times ten is one hundred pairings. Then the club grows to one hundred players. The outer loop runs a hundred times, the inner loop runs a hundred times for each, and suddenly you are generating ten thousand pairings. Notice what just happened: the input got ten times bigger, but the work got one hundred times bigger. That multiplication is the signature of nested loops. Programmers call it quadratic growth, because the work grows like the square of the input size.

Compare that with two loops written one after the other instead of one inside the other. The first loop prints every player''s name, and the second prints every player''s rating. That is ten steps plus ten steps, twenty in total. Sequential loops add. Nested loops multiply. The same keywords appear in both programs, but the shape of the control flow gives them completely different costs.

One more engineering habit: always ask about the worst case. If your nested loop can stop early, say by returning the moment it finds a matching pair, that helps when you are lucky. But when the thing you are searching for is not there at all, you still pay full price, checking everything. Good engineers plan around that full price, because that is the moment users feel the lag.

Here is your recap question. A program uses one loop nested inside another, and both run once per item in a list. If the list doubles in size, what happens to the total work?

The answer: it roughly quadruples. Double times double is four, because nested loops multiply — processing n items costs about n times n steps.', 4, 0.45, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_reading_deep_en_v2', 'k12_control', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Analyzing Nested Control Flow: Traces, Early Exits, and Worst Cases', 'Quick recap: a loop''s cost is (number of iterations) × (cost of its body), and when the body is itself a loop, the costs compound. Analyzing that shape lets you predict best and worst cases before running a single line.

## Worked Example: Grid Search With an Early Exit

A theater''s seating chart is a 2D grid. This function finds the first empty seat:

```
FUNCTION findSeat(grid, rows, cols)
    FOR r FROM 0 TO rows - 1
        FOR c FROM 0 TO cols - 1
            IF grid[r][c] == EMPTY THEN
                RETURN (r, c)
            END IF
        END FOR
    END FOR
    RETURN NOT_FOUND
END FUNCTION
```

Trace it on a 3 × 4 grid where the first empty seat is at row 1, column 2:

1. **r = 0:** the inner loop checks c = 0, 1, 2, 3 — four checks, all occupied.
2. **r = 1:** c = 0 is check 5, c = 1 is check 6, c = 2 is check 7 — EMPTY. `RETURN (1, 2)` fires and control leaves the *entire function*, killing both loops at once.

Now analyze the cases instead of just one trace:

- **Best case:** the very first cell is empty — 1 check.
- **Worst case:** the grid is full, or the only empty seat is the last cell — every one of rows × cols cells is checked. For an R × C grid, that is R·C checks, no matter how clever the early exit is.
- **Tradeoff:** the early RETURN improves the best and typical cases but does nothing for the worst case — and engineers size systems for the worst case, because that is when users feel the lag.

One control-flow subtlety deserves attention: RETURN exits both loops because it exits the function. A plain BREAK would exit only the *inner* loop, and the outer loop would keep going with r + 1 — a classic source of bugs. Escaping two loops without RETURN requires a flag variable or restructuring the code into a function, which is one reason small functions are good engineering.

## Common Misconception

::: misconception
Wrong belief: "Just count the loop keywords — two nested FOR loops always means n² work, three always means n³."
Correction: The *bounds* decide the cost, not the keyword count. If the inner loop always runs exactly 8 times no matter how large n grows, the total is 8n — linear. If the inner loop runs i times, growing with the outer counter, the total is 1 + 2 + ... + n = n(n + 1)/2, which still grows quadratically. Always ask what each loop''s bound depends on: the input size, a fixed constant, or another loop''s counter.
:::

## Where This Leads

This concept is a capstone of the control-structures strand, and it transfers far beyond this course. The habit of predicting cost from structure is exactly what Big-O notation formalizes in AP-level and university algorithm analysis. It is also the everyday lens of working engineers: the accidental nested scan is the classic performance bug in database queries, game engines, and web backends. Evaluating and comparing algorithms this way is the practice described by CSTA standard 3A-AP-11 — and it will follow you into every technical interview you ever take.

::: check
Q: An outer loop runs i from 0 to n − 1, and its inner loop runs j from 0 to i − 1. Exactly how many times does the innermost statement execute, and how does that scale?
A: 0 + 1 + 2 + ... + (n − 1) = n(n − 1)/2 times. That is roughly n²/2, so it still scales quadratically — halving the constant does not change the growth rate.
Q: A search over an n-element list RETURNs the moment it finds its target. A teammate claims this early exit improved the worst case. Are they right?
A: No. When the target is absent or sits in the last position, all n elements are still examined, so the worst case remains n. The early exit improves the best case (1 check) and often the average case — never the worst.
:::', NULL, NULL, 8, 0.6, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_reading_intro_id_v2', 'k12_control', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Loop di Dalam Loop: Saat Kerja Program Berlipat Ganda', 'Pernah main game yang mendadak patah-patah saat musuh di layar makin banyak? Atau menunggu aplikasi "berpikir" lama sekali begitu datanya ribuan? Sering kali biang keladinya bukan perangkatmu, melainkan *struktur* perulangan di dalam programnya — dan di materi ini kamu akan belajar membacanya seperti seorang engineer.

## Ide Besar: Struktur Loop Menentukan Biaya Kerja

Kamu sudah terbiasa menulis loop dan percabangan. Sekarang naik satu level: **menganalisis** apa yang terjadi ketika struktur kontrol disusun bersarang — loop di dalam loop, dengan percabangan di dalamnya.

Tiga aturan utamanya:

- **Loop bersarang mengalikan kerja.** Loop luar n kali × loop dalam m kali berarti badan loop dieksekusi n × m kali.
- **Loop berurutan menjumlahkan kerja.** Loop n kali lalu (setelah selesai) loop m kali berarti n + m eksekusi.
- **Percabangan tidak menambah iterasi**, tetapi menentukan jalur mana yang diambil — dan jalur termahal itulah *worst case* (kasus terburuk) yang wajib diperhitungkan.

Perhatikan pseudocode berikut:

```
untuk i dari 1 sampai 3
    untuk j dari 1 sampai 4
        cetak(i, j)
```

Loop luar berjalan 3 kali. Untuk *setiap* nilai i, loop dalam berjalan penuh 4 kali. Jadi perintah cetak dieksekusi 3 × 4 = 12 kali: (1,1), (1,2), dan seterusnya sampai (3,4). Ganti batasnya menjadi n dan m, dan totalnya n × m — inilah alasan memproses gambar 1000 × 1000 piksel berarti sejuta operasi, padahal kodenya cuma beberapa baris.

Sekarang tambahkan percabangan:

```
untuk i dari 1 sampai n
    untuk j dari 1 sampai n
        jika i != j
            bandingkan(i, j)
```

Jumlah *iterasi* tetap n × n, tetapi fungsi bandingkan hanya dipanggil saat i tidak sama dengan j, yaitu n² − n kali. Kemampuan membaca struktur seperti inilah yang membedakan "kodenya jalan" dengan "kodenya efisien".

::: check
Q: Loop luar berjalan 5 kali, dan loop dalam berjalan 10 kali untuk setiap putaran loop luar. Berapa kali badan loop dalam dieksekusi?
A: 5 × 10 = 50 kali, karena loop bersarang mengalikan jumlah iterasinya.
Q: Bagaimana jika batas loop dalam bergantung pada loop luar, misalnya "untuk j dari 1 sampai i" dengan n = 4?
A: Totalnya 1 + 2 + 3 + 4 = 10 iterasi — batas yang berubah membuat kita menjumlahkan deret, bukan sekadar mengalikan dua angka.
:::

Di materi pendalaman, kamu akan membedah satu algoritma nyata langkah demi langkah dan melihat kenapa kasus terburuknya tumbuh secara kuadratik.', NULL, NULL, 5, 0.3, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_diagram_id_v2', 'k12_control', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Alur Loop Bersarang', 'Loop bersarang paling mudah dipahami sebagai kotak di dalam kotak: seluruh isi kotak dalam ikut diulang oleh kotak luarnya. Diagram berikut menunjukkan kenapa total kerjanya adalah hasil *kali*, bukan hasil jumlah.

```
                 MULAI
                   |
                   v
+--------------------------------------+
| LOOP LUAR: ulangi n kali             |
|                                      |
|   +------------------------------+   |
|   | LOOP DALAM: ulangi m kali    |   |
|   |                              |   |
|   |   +----------------------+   |   |
|   |   | BADAN LOOP:          |   |   |
|   |   | 1 unit kerja         |   |   |
|   |   +----------------------+   |   |
|   |  badan jalan m kali per i    |   |
|   +------------------------------+   |
|   blok dalam diulang n kali          |
+--------------------------------------+
                   |
                   v
                SELESAI

     Total kerja BADAN = n x m kali
```

Legend:

- Kotak terluar = loop luar; setiap lapis kotak = satu tingkat sarang.
- Kotak paling dalam = badan loop, tempat 1 unit kerja nyata terjadi.
- MULAI dan SELESAI = titik masuk dan keluar eksekusi program.
- Panah = arah alur eksekusi dari atas ke bawah.
- n dan m = banyaknya iterasi loop luar dan loop dalam.

Cara membaca diagram:

1. Eksekusi masuk dari MULAI ke kotak loop luar untuk putaran pertama.
2. Loop luar tidak menjalankan satu perintah saja — ia menjalankan *seluruh isi kotaknya*, termasuk loop dalam.
3. Loop dalam memutar badan loop sebanyak m kali sampai hitungannya habis.
4. Kendali kembali ke loop luar, hitungan i bertambah satu, dan loop dalam dimulai lagi dari awal — inilah sumber perkalian.
5. Setelah n putaran loop luar, eksekusi keluar ke SELESAI; badan loop total berjalan n × m kali.

::: tip
Saat membaca kode, bayangkan sarangnya sebagai kotak-di-dalam-kotak lalu kalikan iterasi tiap lapis: tiga lapis loop n berarti n³. Kalau batas loop dalam bergantung pada loop luar, jumlahkan deretnya dulu sebelum menyimpulkan besarnya kerja.
:::', NULL, NULL, 3, 0.4, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_audio_id_v2', 'k12_control', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Kenapa Loop Bersarang Membuat Program Melambat', NULL, NULL, 'Pernah tidak, sebuah aplikasi terasa cepat saat datanya sedikit, lalu tiba-tiba lambat sekali begitu datanya banyak? Sering kali penyebabnya bukan komputer yang lemah, melainkan struktur perulangan di dalam programnya. Kali ini kita membahas cara menganalisis loop bersarang, yaitu loop di dalam loop, dan bagaimana struktur itu menentukan seberapa cepat kerja program bertambah.

Ide besarnya begini. Kalau sebuah loop berjalan n kali, dan di dalam badannya ada loop lain yang berjalan m kali, maka perintah yang paling dalam dieksekusi n dikali m kali. Kerjanya berlipat ganda karena dikalikan, bukan sekadar ditambahkan.

Ambil contoh fitur pencari foto kembar di galeri ponselmu. Untuk memastikan tidak ada foto ganda, program harus membandingkan setiap foto dengan setiap foto lainnya. Dengan seratus foto, itu sekitar lima ribu perbandingan, masih terasa instan. Tetapi dengan sepuluh ribu foto, jumlah perbandingannya melonjak menjadi sekitar lima puluh juta. Datanya hanya bertambah seratus kali lipat, sedangkan kerjanya membengkak hampir sepuluh ribu kali lipat. Itulah ciri khas pertumbuhan kuadratik yang lahir dari loop bersarang.

Bandingkan dengan mencari satu nama di daftar kontak. Di sana hanya ada satu loop yang menelusuri daftar dari awal sampai ketemu. Kerjanya tumbuh sebanding dengan banyaknya data. Kontak dua kali lebih banyak berarti kerja paling banter dua kali lebih lama. Itu pertumbuhan linear, jauh lebih ramah daripada kuadratik.

Ada dua kebiasaan analisis yang perlu kamu bawa. Pertama, selalu tanyakan kasus terburuknya. Percabangan atau perintah berhenti lebih awal memang bisa mempercepat kasus yang mujur, tetapi kasus terburuk tetap menunggu, misalnya saat data yang dicari tidak ada sama sekali. Kedua, bedakan loop bersarang dengan loop berurutan. Dua loop yang ditulis berurutan, satu selesai baru yang lain mulai, kerjanya hanya dijumlahkan dan tetap linear. Yang membuat kerja meledak adalah sarangnya, bukan banyaknya loop.

Sebagai rekap, coba jawab pertanyaan ini. Jika loop luar berjalan seribu kali, dan untuk setiap putarannya loop dalam berjalan seribu kali, berapa kali badan loop paling dalam dieksekusi? Jawabannya satu juta kali, karena struktur bersarang berarti mengalikan: seribu dikali seribu. Kalau kamu bisa menjelaskan alasan perkalian itu, kamu sudah berpikir seperti seorang analis algoritma.', 4, 0.45, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_control_reading_deep_id_v2', 'k12_control', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menganalisis Loop Bersarang dan Kasus Terburuk', 'Intinya: bentuk sarang struktur kontrol menentukan berapa banyak kerja yang dilakukan program, dan analisis yang jujur selalu diukur pada kasus terburuk, bukan pada kasus yang kebetulan mujur.

## Bedah Algoritma: Mendeteksi Nilai Kembar

Misalkan kamu diminta memeriksa apakah sebuah daftar berisi nilai duplikat.

```
fungsi adaKembar(data, n)
    untuk i dari 0 sampai n - 2
        untuk j dari i + 1 sampai n - 1
            jika data[i] = data[j]
                kembalikan benar
    kembalikan salah
```

Jalankan dengan data = [7, 3, 9, 3] dan n = 4:

1. i = 0 → j = 1, 2, 3: bandingkan 7 dengan 3, 9, lalu 3 — tidak ada yang sama (3 perbandingan).
2. i = 1 → j = 2: 3 lawan 9, beda. Lalu j = 3: 3 lawan 3 — **sama!** Fungsi langsung mengembalikan benar (2 perbandingan).

Total hanya 5 perbandingan karena program berhenti lebih awal. Tetapi seorang engineer tidak boleh puas dengan kasus mujur. Tanyakan: *bagaimana kalau tidak ada duplikat sama sekali?* Kedua loop berjalan tuntas: (n − 1) + (n − 2) + … + 1 = n(n − 1)/2 perbandingan. Untuk n = 4 itu cuma 6; untuk n = 1.000 menjadi 499.500. Data bertambah 250 kali lipat, kerjanya membengkak lebih dari 80.000 kali lipat — ciri khas pertumbuhan kuadratik.

Dua detail rancangan yang layak dianalisis:

- Perintah "kembalikan benar" di dalam loop adalah *early exit*: mempercepat kasus terbaik, tetapi **tidak mengubah kasus terburuk** sedikit pun.
- Batas j mulai dari i + 1, bukan dari 0: pasangan yang sama tidak diperiksa dua kali, dan sebuah elemen tidak dibandingkan dengan dirinya sendiri. Cek juga *edge case*: saat n = 0 atau n = 1, loop luar tidak pernah berjalan dan fungsi dengan benar mengembalikan salah.

## Miskonsepsi yang Sering Muncul

::: misconception
Keliru: "Program yang memuat dua buah loop pasti kerjanya n²."
Yang benar: hanya loop **bersarang** yang mengalikan kerja. Dua loop yang ditulis berurutan — satu selesai, baru yang lain mulai — hanya menjumlahkan: n + n = 2n, tetap tumbuh linear. Yang harus kamu baca adalah struktur sarangnya, yaitu apakah satu loop berada *di dalam* badan loop lain, bukan sekadar menghitung berapa kali kata "untuk" muncul di kode.
:::

## Ke Mana Kemampuan Ini Membawamu

Kemampuan menganalisis struktur kontrol bersarang — sejalan dengan standar AP-K12-4 — adalah gerbang menuju analisis algoritma formal di jenjang berikutnya: notasi Big-O, perbandingan algoritma pengurutan, dan pemilihan struktur data yang tepat. Kebiasaan bertanya "berapa kali baris ini dieksekusi pada kasus terburuk?" akan terus terpakai saat kamu menulis kueri basis data, mengoptimalkan game, atau berlaga di kompetisi pemrograman.

::: check
Q: Untuk n = 6, berapa perbandingan yang dilakukan adaKembar pada kasus terburuk, dan kapan kasus itu terjadi?
A: n(n − 1)/2 = 15 perbandingan; terjadi saat tidak ada duplikat sama sekali (atau duplikat baru ditemukan di pasangan terakhir), sehingga early exit tidak pernah menolong.
Q: Program A memakai dua loop berurutan yang masing-masing n iterasi; Program B memakai loop bersarang n × n. Bandingkan kerjanya untuk n = 1.000.
A: A butuh sekitar 2n = 2.000 langkah (linear), sedangkan B butuh n² = 1.000.000 langkah (kuadratik) — kira-kira 500 kali lebih banyak, dan selisihnya makin ekstrem saat n membesar.
:::', NULL, NULL, 8, 0.6, '["k8_control"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_reading_intro_en_v2', 'k12_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Data Pipelines: From Messy Logs to Smart Predictions', 'Every playlist recommendation, every "for you" feed, every college-admissions dashboard starts the same way: someone built a pipeline that moves data from the messy real world into a model that makes predictions. When the pipeline is engineered well, it feels like magic. When the data feeding it is skewed, it quietly fails — often for specific groups of people — and nobody notices until it ships.

## The Big Idea: Data Is a Supply Chain

A **data pipeline** is an assembly line for information. Raw data enters at one end; decisions come out the other. The standard stages:

1. **Collect** — gather raw records (sensors, forms, logs).
2. **Clean** — remove duplicates, handle missing values, flag outliers.
3. **Transform** — reshape the data into features a model can use.
4. **Train / analyze** — let an algorithm find patterns.
5. **Evaluate** — test those patterns on data the model has never seen.
6. **Deploy and monitor** — use it, and watch for drift over time.

Two engineering rules govern everything. First: *garbage in, garbage out* — no downstream stage can rescue data that was collected badly. Second: every stage involves tradeoffs. How you organize and store data determines which questions you can even ask later, and how fast you can answer them — exactly the tradeoff the CSTA 3A-DA-10 standard asks you to evaluate.

**Machine learning** is what happens at stage 4 when, instead of hand-writing rules, you let the algorithm derive rules from examples. That is powerful, but it means the model inherits whatever patterns — including unfair ones — live in your data. That inherited unfairness is called **bias**.

## A Small Pipeline You Can Build Today

Goal: predict the cafeteria lunch-line wait so you know when to show up. You log 20 school days of `(day_of_week, wait_minutes)`.

Cleaning matters immediately: two days have missing values (you forgot to time them), and one entry says 300 minutes — clearly a typo. Worst case, that single bad row would wreck every average, so the pipeline defends against it:

```
clean_log = []
FOR each row IN raw_log:
    IF row.wait IS MISSING: skip row
    IF row.wait > 60:       skip row   # outlier guard
    APPEND row TO clean_log

FOR each day IN [Mon..Fri]:
    avg[day] = MEAN(row.wait WHERE row.day == day)

PREDICT(day) = avg[day]
```

Your model says Fridays are the worst day of the week. Useful! But notice the edge case: all 20 days came from one month. If the kitchen changes its schedule next month, your model is confidently wrong. Pipelines are not built once — they are monitored and refreshed.

::: check
Q: Why can''t a brilliant model at stage 4 fix data that was collected badly at stage 1?
A: A model can only learn patterns present in the data it receives; if the input is wrong or skewed, it learns wrong or skewed patterns — garbage in, garbage out.
Q: In the lunch-line pipeline, why skip the 300-minute entry instead of averaging it in?
A: It is an outlier almost certainly caused by an error, and one extreme value would distort the mean, making every prediction for that day wildly wrong.
:::

Next, the deeper material walks a full machine-learning pipeline — training, testing, and a bias bug hiding behind a strong accuracy score.', NULL, NULL, 5, 0.3, '["k8_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_diagram_en_v2', 'k12_data_collection', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Machine Learning Pipeline at a Glance', 'Every machine-learning system, from a homework project to a production recommender, follows the same loop. Notice that the diagram is a cycle, not a straight line — failure sends you back to the data, not just the code.

```
+---------+   +-------+   +-------+
| COLLECT |-->| CLEAN |-->| SPLIT |
+---------+   +-------+   +---+---+
     ^                        |
     |         +--------------+------------+
     |         v                           v
     |  [train set 80%]             [test set 20%]
     |         |                           |
     |         v                           v
     |    +--------+                 +----------+
     |    | TRAIN  |----- model ----->| EVALUATE |
     |    +--------+                 +----------+
     |                                     |
     |     fails audit (bias, bad score)   |
     +-------------------------------------+
                                           |
                                     passes audit
                                           v
                                      +--------+
                                      | DEPLOY |
                                      +--------+
```

Legend:

- Boxes = pipeline stages the data passes through
- `-->` and `v` = the direction data flows
- `[ ]` = the two datasets produced by the split
- Left vertical rail = the feedback loop taken when evaluation fails
- "model" = the trained model handed over for testing

How to read it:

1. Follow the top row left to right: raw data is collected, cleaned, then split.
2. The split creates two piles — roughly 80 percent for training and 20 percent for testing, which stays locked away.
3. TRAIN produces a model; EVALUATE scores that model on the unseen test set.
4. If the audit fails — low score, or errors concentrated on one group (bias) — follow the rail back up to COLLECT and fix the data.
5. Only a model that passes the audit flows down to DEPLOY, and even then it must be monitored.

::: tip
When a pipeline misbehaves, debug upstream first. Most "model bugs" are really data bugs, so inspect the collect and clean stages before you touch the training algorithm.
:::', NULL, NULL, 3, 0.4, '["k8_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_audio_en_v2', 'k12_data_collection', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'How Models Learn, and How They Inherit Bias', NULL, NULL, 'Imagine you are building an app for your school that recommends which elective each student should try next. You do not write the rules by hand. Instead, you feed the computer data — past students, the electives they took, and whether they liked them — and you let it find the patterns. That is machine learning, and the road the data travels is called a pipeline.

Every pipeline has the same stages. First you collect the data. Then you clean it, because real data is messy, full of missing answers, typos, and duplicates. Then you split it into two piles: a big pile for training and a smaller pile for testing, which you lock away. You train the model on the first pile, then evaluate it on the second, on data it has never seen, to check whether it actually learned something general or just memorized its examples.

Here is the part that separates careful engineers from careless ones. Suppose your elective recommender was trained only on surveys from students who stayed after school to fill them out. Athletes at practice, students with jobs, students who ride the early bus — they never made it into your data. The model will still run. It will still produce confident recommendations. But for those missing students, its patterns are borrowed from people whose lives are different. That is bias. It is not a math error; it is a data error. The model faithfully learned a skewed picture of the world.

The fix is not a smarter algorithm. It is better collection, like surveying every homeroom instead of only volunteers, and honest evaluation, where you check how the model performs for each group separately instead of trusting one overall number. A single accuracy score can hide a model that works well for most students and fails badly for a few.

So remember the pipeline: collect, clean, split, train, evaluate, and only then deploy. And remember that every stage can introduce bias, or catch it.

Here is your recap question. If a model scores ninety-five percent accuracy on its test set, does that prove it will work fairly for everyone?

The answer is no. The test set is usually carved from the same collected data as the training set. If the collection skipped certain groups of people, the test set skipped them too, which means the score never measured the model on those people at all.', 4, 0.45, '["k8_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_reading_deep_en_v2', 'k12_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Inside an ML Pipeline: Training, Testing, and Hidden Bias', 'Recap: a data pipeline moves information through collect, clean, split, train, evaluate, and deploy — and a machine-learning model is only as trustworthy as the data that flowed into it.

## Worked Example: A Spam Filter for the Robotics Club Inbox

The club inbox drowns in junk, so you build a classifier. Walk each stage deliberately.

**Step 1 — Collect.** Officers label 200 past emails: 120 legit, 80 spam.

**Step 2 — Clean.** Lowercase everything, strip punctuation, delete exact duplicates. The same scam arrived nine times; leaving duplicates in would let one email vote nine times during training.

**Step 3 — Split.** Shuffle, then hold out 160 emails for training and 40 for testing. Shuffling matters: split by date instead, and the training set might be all September while the test set is all October — different spam waves, misleading scores.

**Step 4 — Train.** A word-frequency classifier:

```
# learn
FOR each email IN train_set:
    FOR each word IN email:
        count[email.label][word] += 1

# predict: which label fits these words better?
SCORE(email, label) =
    SUM over words IN email of
        log((count[label][word] + 1) / total[label])

PREDICT(email) =
    IF SCORE(email,"spam") > SCORE(email,"legit"):
        RETURN "spam"
    ELSE:
        RETURN "legit"
```

The `+ 1` guards an edge case: a word never seen in training would otherwise produce log(0) and blow up the score.

**Step 5 — Evaluate.** The model gets 36 of 40 test emails right: 90 percent accuracy. Ship it? Not yet — audit the four errors. Three are *legit* emails flagged as spam, and all three contain the word "free."

**Step 6 — Diagnose.** Your 80 spam examples happened to be collected during a wave of "FREE giveaway" scams, so the model learned that "free" is near-certain spam. Now the club''s "free pizza at Friday''s meeting" announcements get buried. This is bias: a skew introduced at the *collect* stage, invisible inside the headline accuracy number, and discovered only by auditing errors case by case.

**Step 7 — Iterate.** Gather spam from several months, add legit emails that use "free," re-split, retrain, re-audit. Then weigh the tradeoff: a false positive (a real email buried) probably costs the club more than a false negative (one junk email read), so you might require a wider score gap before calling anything spam.

## Common Misconception

::: misconception
Wrong belief: "A model can''t be biased — it''s just math, and math is objective."
Correction: The algorithm is neutral; the data is not. A model is a compressed summary of its training examples, so any skew in who or what got sampled becomes a skew in predictions. High accuracy on a skewed test set proves nothing, because the test set carries the same blind spots as the training set. You check fairness by auditing error rates across groups and situations — never by trusting the math.
:::

## Where This Leads

No later unit in this course depends on this one, but almost everything downstream of school does. The habits you built here — split before you train, guard the worst-case input, audit errors instead of trusting one score — transfer directly to AP Statistics, college data science, and any engineering job that touches data. They also transfer to daily life: the next time a product advertises a highly accurate AI, you know exactly which questions to ask about where the data came from and who it might fail.

::: check
Q: A classifier answers "legit" for every single email and still scores 97 percent accuracy on an inbox that is 97 percent legit mail. What went wrong with the evaluation?
A: Accuracy alone hides performance on the rare class — a do-nothing model matches the majority rate. You must measure per-class errors: how much spam it actually catches and how many real emails it wrongly flags.
Q: While tuning, you repeatedly checked results on the test set and adjusted the model until test accuracy peaked. Why is your final score untrustworthy?
A: Information from the test set leaked into your design choices, so the model is partly fitted to that specific set. The score now measures memorization, not generalization; you would need a fresh, untouched test set to evaluate honestly.
:::', NULL, NULL, 8, 0.6, '["k8_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_reading_intro_id_v2', 'k12_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Dari Data Mentah ke Keputusan: Mengenal Pipeline Data', 'Setiap kali kamu membuka aplikasi video pendek, ada model machine learning yang memutuskan tontonan berikutnya — dan model itu belajar dari jejak data jutaan pengguna, termasuk datamu. Filter spam di email, rekomendasi lagu, sampai fitur buka kunci wajah di ponsel semuanya bekerja dengan pola yang sama: data masuk, keputusan keluar. Kalau kamu paham cara data mengalir dan diolah di baliknya, kamu bukan sekadar pengguna — kamu bisa menjadi perancangnya.

## Ide besar: pipeline data

Data mentah hampir selalu berantakan: ada nilai kosong, duplikat, salah ketik, dan format yang tidak seragam. Karena itu, engineer tidak langsung "menganalisis data", melainkan merancang **pipeline data** — rangkaian tahap yang tersusun rapi:

1. **Kumpulkan** — ambil data dari sumber (formulir, log aplikasi, sensor).
2. **Bersihkan** — buang duplikat, tangani nilai kosong, perbaiki format.
3. **Transformasi** — ubah data ke bentuk yang siap dihitung.
4. **Analisis atau latih model** — cari pola, atau biarkan algoritma machine learning menemukannya.
5. **Evaluasi** — uji apakah hasilnya layak dipercaya sebelum dipakai.

*Machine learning* sendiri berbeda dari pemrograman biasa: alih-alih menulis aturan satu per satu, kamu memberi program banyak contoh berlabel, lalu algoritma menemukan polanya sendiri. Konsekuensinya penting: **model hanya sebaik data yang melatihnya**. Kalau datanya timpang, keputusannya ikut timpang — inilah yang disebut *bias*. Kemampuan merancang pipeline yang setiap tahapnya bisa dipertanggungjawabkan adalah inti capaian standar AD-K12-3.

## Contoh kecil: filter spam sederhana

Misalkan kamu punya enam email latih: tiga berlabel "spam", tiga berlabel "normal". Dari email spam, kamu menemukan kata yang sering muncul: "gratis", "menang", "klik". Aturannya bisa ditulis sebagai pseudocode:

```
kata_spam = ["gratis", "menang", "klik"]

fungsi skor(email):
    hitung = 0
    untuk setiap kata dalam email:
        jika kata ada di kata_spam:
            hitung = hitung + 1
    kembalikan hitung

jika skor(email_baru) >= 2:
    tandai "spam"
lain:
    tandai "normal"
```

Email baru "Selamat! Kamu MENANG hadiah GRATIS, klik di sini" mendapat skor 3 — ditandai spam. Benar. Tapi perhatikan kasus tepinya: pengumuman guru "Seminar gratis untuk kelas XI, klik tautan pendaftaran" mendapat skor 2 dan ikut terblokir. Menurunkan ambang membuat lebih banyak spam tertangkap tetapi lebih banyak email penting ikut terblokir; menaikkannya berlaku sebaliknya. Tidak ada ambang yang sempurna — yang ada hanyalah *tradeoff* yang kamu pilih secara sadar.

::: check
Q: Mengapa tahap pembersihan data harus dilakukan sebelum melatih model?
A: Karena model belajar dari data apa adanya; duplikat dan nilai yang salah akan menjadi "pola" yang ikut dipelajari, sehingga hasilnya menyesatkan.
Q: Pada filter spam di atas, apa akibatnya jika ambang skor diturunkan menjadi 1?
A: Lebih banyak spam tertangkap, tetapi email normal yang kebetulan memuat satu kata seperti "gratis" ikut terblokir — jumlah salah tandai (false positive) naik.
:::

Di materi pendalaman, kamu akan merancang satu pipeline utuh dari nol dan melihat bagaimana bias bisa menyusup diam-diam di setiap tahapnya.', NULL, NULL, 5, 0.3, '["k8_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_diagram_id_v2', 'k12_data_collection', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Alur Pipeline Data dari Sumber sampai Pemantauan', 'Pipeline data bukan garis lurus sekali jalan — hasil evaluasi sering memaksa kita kembali memperbaiki data. Diagram berikut menunjukkan enam tahap pipeline beserta jalur umpan baliknya.

```
[SUMBER: formulir, log aplikasi, sensor]
              |
              v
      +----------------+
      | 1. KUMPULKAN   |
      +----------------+
              |
              v
      +----------------+  gagal? perbaiki data
      | 2. BERSIHKAN   |<-----------------+
      +----------------+                  |
              |                           |
              v                           |
      +----------------+                  |
      | 3. TRANSFORMASI|                  |
      +----------------+                  |
              |                           |
              v                           |
      +----------------+         +-------------+
      | 4. LATIH MODEL |-------->| 5. EVALUASI |
      +----------------+         +-------------+
                                        |
                                  lolos v
                                 +-------------+
                                 | 6. TERAPKAN |
                                 |  & PANTAU   |
                                 +-------------+
```

Legend:
- Kotak bernomor = tahap pipeline yang harus kamu rancang.
- Panah (v dan -->) = arah aliran data dari tahap ke tahap.
- Tanda [ ] = sumber data di luar pipeline.
- Garis di sisi kanan yang kembali ke tahap 2 = jalur umpan balik.
- Kata "gagal?" dan "lolos" = kondisi yang menentukan cabang mana yang diambil.

Cara membaca diagram:
1. Mulai dari atas: data mentah masuk dari sumber ke tahap KUMPULKAN.
2. Ikuti panah ke bawah: data dibersihkan, lalu ditransformasi menjadi fitur yang siap dihitung.
3. Tahap LATIH MODEL memakai fitur itu, lalu hasilnya dikirim ke tahap EVALUASI.
4. Jika evaluasi gagal, ikuti garis di sisi kanan kembali ke tahap 2 — biasanya masalahnya ada di data, bukan di algoritma.
5. Jika lolos, model diterapkan; tahap PANTAU memastikan kinerjanya tidak menurun ketika pola data di dunia nyata berubah.

::: tip
Sebelum menggambar pipelinemu sendiri, tulis dulu satu kalimat pertanyaan yang ingin dijawab. Lalu uji setiap kotak dengan pertanyaan: "kalau tahap ini dihapus, apa yang rusak?" Kalau tidak ada jawabannya, tahap itu belum kamu pahami — atau memang tidak perlu.
:::', NULL, NULL, 3, 0.4, '["k8_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_audio_id_v2', 'k12_data_collection', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Mengapa Model Belajar dari Data dan Ikut Mewarisi Biasnya', NULL, NULL, 'Bayangkan kamu sedang memasak untuk acara besar. Kamu tidak langsung melempar bahan mentah ke panci, kan? Kamu memilih bahan, mencucinya, memotongnya, memasaknya, lalu mencicipinya sebelum dihidangkan. Pengolahan data bekerja dengan urutan yang sama, dan para engineer menyebut urutan itu pipeline data.

Pipeline data punya tahap-tahap yang jelas. Pertama, kumpulkan data dari sumbernya, misalnya formulir, catatan aplikasi, atau sensor. Kedua, bersihkan datanya: buang data ganda, tangani nilai yang kosong, perbaiki salah ketik. Ketiga, ubah data ke bentuk yang bisa dihitung. Keempat, analisis datanya, atau latih model machine learning untuk menemukan pola. Kelima, evaluasi hasilnya sebelum benar-benar dipakai. Kalau hasil evaluasinya mengecewakan, kamu kembali ke tahap pembersihan data, bukan langsung menyalahkan algoritmanya.

Machine learning sendiri adalah cara membuat program tanpa menulis semua aturannya satu per satu. Kamu memberi komputer banyak contoh, lalu komputer menemukan polanya sendiri. Tapi di sinilah letak bahayanya: model hanya sebaik data yang melatihnya.

Begini contohnya. Misalkan sebuah tim membuat asisten suara, dan mereka melatihnya dengan ribuan rekaman. Tapi hampir semua rekaman itu berasal dari orang dewasa yang berbicara dengan satu logat saja. Asisten itu akan lancar memahami mereka, tapi kesulitan memahami suara remaja, atau penutur dengan logat daerah yang berbeda. Tidak ada programmer yang berniat jahat di sini. Kodenya bisa jadi sempurna. Yang timpang adalah datanya: sebagian orang terwakili, sebagian lainnya tidak. Itulah yang disebut bias, dan bias menyusup lewat pipeline, bukan lewat niat.

Karena itu, perancang pipeline yang baik selalu bertanya tiga hal. Dari mana data ini berasal? Siapa yang tidak terwakili di dalamnya? Dan bagaimana hasilnya diuji sebelum dipakai orang banyak? Tiga pertanyaan itu sederhana, tapi bisa mencegah kesalahan yang menyebar ke jutaan pengguna.

Sekarang, satu pertanyaan pengingat untukmu. Kalau sebuah model machine learning menghasilkan keputusan yang tidak adil, di mana biasanya sumber masalahnya berada?

Jawabannya: hampir selalu di datanya. Perhatikan cara data itu dikumpulkan, siapa saja yang terwakili di dalamnya, dan bagaimana labelnya dibuat. Komputer tidak berniat curang; ia hanya setia mengulang pola dari data yang kita berikan. Maka tugas kita adalah merancang pipeline yang datanya bisa dipertanggungjawabkan, dari tahap pertama sampai tahap terakhir.', 4, 0.45, '["k8_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k12_data_collection_reading_deep_id_v2', 'k12_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Merancang Pipeline Data dari Nol dan Mewaspadai Bias', 'Inti analisis data modern: rancang pipeline yang tahapannya jelas — kumpulkan, bersihkan, transformasi, latih, evaluasi — karena model machine learning hanya sebaik data yang mengalir melewatinya.

## Studi kasus: memprediksi porsi makan siang kantin

Kantin sekolahmu sering kelebihan atau kekurangan masakan. Tugasmu: bangun model yang memprediksi berapa porsi yang harus disiapkan besok. Ikuti pipelinenya tahap demi tahap.

1. **Rumuskan pertanyaan.** Target prediksinya berupa angka (jumlah porsi), jadi ini masalah *regresi*, bukan klasifikasi.
2. **Kumpulkan data.** Log 90 hari: hari dalam seminggu, cuaca, ada tidaknya acara sekolah, dan porsi yang terjual.
3. **Bersihkan.** Empat baris kosong karena kasir lupa mencatat — buang, atau isi dengan rata-rata hari serupa (dua pilihan dengan konsekuensi berbeda). Satu baris tercatat 950 porsi padahal biasanya sekitar 300 — telusuri dulu: salah ketik, atau memang hari lomba antarsekolah? Outlier tidak boleh dihapus membabi buta.
4. **Transformasi.** Ubah "Senin"–"Jumat" menjadi kolom angka, dan cuaca menjadi kategori seperti cerah/hujan.
5. **Pisahkan data.** 80 hari untuk latihan, 10 hari terakhir untuk pengujian. Data uji tidak boleh disentuh saat melatih — kalau bocor, hasil evaluasimu berbohong.
6. **Latih dan evaluasi.**

```
model = latih_regresi(fitur_latih, target_latih)
untuk setiap hari dalam data_uji:
    p = model.prediksi(fitur[hari])
    selisih[hari] = |p - porsi_asli[hari]|
MAE = rata_rata(selisih)
```

Jika MAE-nya 15, prediksimu rata-rata meleset 15 porsi — mungkin sudah cukup baik untuk dipakai. Tapi pikirkan kasus terburuknya: hari pertama masuk setelah libur panjang tidak punya pola serupa di data latih, dan di situlah model paling mungkin meleset jauh.

7. **Pantau setelah dipakai.** Semester berganti, menu berubah, pola bergeser. Pipeline yang baik menyertakan pemantauan dan pelatihan ulang berkala.

Sekarang soal bias: bayangkan 90 hari data itu semuanya diambil pada musim hujan. Model akan "yakin" bahwa hari hujan itu kondisi normal, lalu salah besar begitu kemarau tiba. Tidak ada satu baris kode pun yang keliru — yang timpang adalah *cara datanya dikumpulkan*. Bias bisa masuk lewat sampel yang tidak mewakili (bias pengumpulan), lewat label yang diberikan manusia (bias pelabelan), atau lewat data historis yang merekam ketidakadilan masa lalu (bias historis).

## Miskonsepsi umum

::: misconception
Keliru: "Komputer tidak punya perasaan atau kepentingan, jadi keputusan machine learning pasti objektif dan adil."
Faktanya: model hanya menemukan dan mengulang pola dari data latihnya. Jika data itu timpang — hanya mewakili satu kelompok, satu musim, atau satu kebiasaan lama — model mewarisi ketimpangan itu dan bisa memperkuatnya dalam skala besar, tanpa ada satu pun baris kode yang "berniat" curang. Keadilan harus dirancang di dalam pipeline, bukan diasumsikan dari mesinnya.
:::

## Ke mana keterampilan ini membawamu

Pola pikir pipeline — memecah pengolahan data menjadi tahap-tahap yang bisa diperiksa satu per satu — adalah keterampilan yang sama yang dipakai data engineer, ilmuwan data, dan peneliti AI di industri. Kebiasaan bertanya "dari mana data ini berasal, siapa yang tidak terwakili, dan bagaimana modelnya diuji?" akan terpakai setiap kali kamu membaca klaim tentang AI di berita, memakai produk berbasis model, atau kelak membangun sistemmu sendiri di jenjang kuliah dan dunia kerja.

::: check
Q: Model kantinmu punya MAE bagus di data uji, tetapi meleset parah saat dipakai dua bulan kemudian. Sebutkan satu penyebab yang berkaitan dengan pipeline, bukan dengan algoritmanya.
A: Distribusi data berubah — menu, musim, atau jadwal sekolah bergeser sehingga data latih tidak lagi mewakili kondisi nyata; pipeline seharusnya memantau kinerja dan melatih ulang model secara berkala.
Q: Mengapa data uji harus dipisahkan sebelum pelatihan dimulai, bukan setelahnya?
A: Jika model sempat "melihat" data uji saat dilatih (kebocoran data), skor evaluasinya terlalu optimis karena model dinilai pada contoh yang sudah dihafalnya — bukan pada kemampuannya menggeneralisasi ke data baru.
:::', NULL, NULL, 8, 0.6, '["k8_data_collection"]'::jsonb);
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
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_reading_intro_en_v2', 'k2_computing_systems_devices', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Computers Everywhere: Parts You Touch, Helpers You Can''t', 'Do you play games on a tablet? Does someone in your family talk to a phone? Guess what — those are computers, and you use them almost every day!

## The Big Idea: Parts You Can Touch, Helpers You Can''t

Computers are all around us. A tablet is a computer. A phone is a computer. A laptop is a computer. A game console is a computer too!

Every computer has two kinds of things.

**Hardware** is every part you can touch. The screen. The buttons. The speaker that makes sound. If your finger can tap it, it is hardware.

**Software** is the helpers you cannot touch. Games are software. Drawing apps are software. Music apps are software. Software lives inside the device, like a story lives inside a book.

Here is a fun way to remember it. Software is like a recipe. A recipe tells a cook what to do. Software tells the hardware what to do!

## Let''s Follow One Tap

Pretend you are playing a matching game on a tablet.

1. You tap a card on the screen. Your finger touched **hardware**.
2. The game flips the card over. The game decided that. The game is **software**.
3. Ding! The speaker plays a happy sound. The speaker is **hardware**. The software told it to ding.

See? You touch the hardware. The software does the thinking and telling. They work as a team, like a cook and a recipe.

::: check
Q: Is the screen on a tablet hardware or software?
A: Hardware, because you can touch it with your finger.
Q: Can you pick up a game and hold it in your hand?
A: No. A game is software. It lives inside the device, like a story lives inside a book.
:::

Ready for more? Next we will follow one photo from button to screen and watch the team in action!', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_diagram_en_v2', 'k2_computing_systems_devices', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Two Teams Inside Every Computer', 'Every computer — a tablet, a phone, a laptop — has the same two teams inside. This picture shows how the teams work together.

```
         ONE COMPUTER, TWO TEAMS
  +-----------------------------------+
  |  SOFTWARE  (you cannot touch it)  |
  |  (game)  (music app)  (paint app) |
  +-----------------------------------+
                   |
                   v  "do this!"
  +-----------------------------------+
  |  HARDWARE  (you can touch it)     |
  |  [screen]  [button]  [speaker]    |
  +-----------------------------------+
                   |
                   v
       You see, hear, and play!
```

Legend

- ( ) round brackets = software, the helpers you cannot touch
- [ ] square brackets = hardware, the parts you can touch
- | and v = the path the instructions travel, going down
- "do this!" = software telling hardware what to do

How to read the picture

1. Start at the top box. That is the software team: games and apps that live inside the computer.
2. Follow the arrow down. Software sends instructions, like a recipe tells a cook.
3. Look at the bottom box. That is the hardware team: the screen, the buttons, the speaker. You can touch every one.
4. Follow the last arrow. When both teams do their jobs, you get to see pictures, hear sounds, and play!

::: tip
Try the touch test at home with a grown-up. Point at a device. If your finger can tap the part, say "hardware!" If it is a game or an app, say "software!"
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_audio_en_v2', 'k2_computing_systems_devices', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'What Makes a Computer Go', NULL, NULL, 'Hello, friend! Today we are talking about computers. Computers are not just the big ones on desks. A phone is a computer. A tablet is a computer. A laptop and a game console are computers too. Some watches are even tiny computers you can wear!

Every computer is made of two kinds of things. The first kind is called hardware. Hardware is every part you can touch. The screen is hardware. The buttons are hardware. The speaker that makes the sound is hardware. If your finger can tap it or poke it, it is hardware.

The second kind is called software. Software is the part you cannot touch. Games are software. Apps are software. Software is a set of instructions that tells the hardware what to do.

Think about brushing your teeth. Your toothbrush is a tool you can hold, just like hardware. But the steps you follow, like wet the brush, add the toothpaste, and brush up and down, those steps are like software. The steps are not a thing you can hold. They are the plan!

Here is one more example. Maybe you have heard a smart speaker at home. Someone says, play my favorite song, and music comes out. The speaker box on the table is hardware. You can touch it. But inside, software is doing the busy work. The software hears the words, finds the song, and tells the speaker to play it right now. You can touch the box, but you can never touch the software. They are a team. The software is the friend with the plan, and the hardware does the moving, the showing, and the singing.

So here is your question. If you can touch a part with your finger, like a screen or a button, is it hardware or software? Think about it. Ready? It is hardware! And the games and apps you cannot touch? That is software. Great job! Now you know the two teams inside every computer.', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_reading_deep_en_v2', 'k2_computing_systems_devices', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Hardware and Software: The Great Team Inside', 'Remember the big idea. Hardware is the parts you can touch. Software is the invisible helper that tells the hardware what to do.

## Taking a Photo, Step by Step

Let''s say you want to take a picture of your dog with a phone.

1. **You press the round camera button on the screen.** Your finger touches the screen. The screen is hardware.
2. **The camera app wakes up.** The app is software. You cannot touch it. It says, "Take a picture right now!"
3. **The tiny camera eye looks.** The camera is hardware. It is a little part on the back of the phone.
4. **The software saves the picture.** It tucks the photo away inside the phone, like putting a drawing in a folder.
5. **The screen shows your dog!** Hardware shows the picture. Software chose what to show.

Count the teamwork. Hardware did the touching, the seeing, and the showing. Software did the deciding and the telling. Neither one could take the photo alone!

## A Mix-Up to Watch Out For

::: misconception
Wrong idea: "If a part is hiding inside the computer where I can''t see it, it must be software."
The truth: hidden parts are still hardware! Inside every device there are tiny chips and wires. You could touch them if you opened the case (please don''t!). Software is not a part at all. It is a set of instructions — like a song is not the radio, and a story is not the book.
:::

So the real test is not "can I see it?" The real test is: is it a **thing**, or is it **instructions**? Things are hardware. Instructions are software.

## Where This Leads

What you learn here transfers to bigger adventures. In grades 3 to 5, you will see how hardware and software work together as one big system, and you will play detective when a device stops working: is it a hardware problem or a software problem? Later, in middle school, you will look even deeper at the parts inside and how they store and share information. Teachers call this first step CSTA 1A-CS-01, but you can just call it knowing your computer!

::: check
Q: A game on a tablet freezes, but the screen is not cracked and the buttons still click. Is the problem more likely hardware or software?
A: Software. The parts you can touch are working fine, but the instructions inside got stuck.
Q: Name one hardware part and one software helper on a school computer.
A: Hardware could be the keyboard, the mouse, or the screen. Software could be a drawing app or a math game.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_reading_intro_id_v2', 'k2_computing_systems_devices', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Benda Pintar di Sekitar Kita', 'Coba lihat sekelilingmu. Ada HP? Ada tablet? Benda-benda itu menemani kita setiap hari. Mereka memutar lagu, menampilkan kartun, dan mengajak kita bermain.

## Benda Pintar dan Dua Bagiannya

Beberapa benda di rumah kita adalah **benda pintar**. Komputer, laptop, tablet, dan HP adalah benda pintar. Mereka bisa mengikuti perintah kita. Kita tekan tombolnya, mereka menurut!

Bola dan sendok bukan benda pintar. Mereka tidak bisa mengikuti perintah. Coba bilang "halo" pada sendok. Sendok diam saja, kan?

Nah, setiap benda pintar punya dua bagian:

- **Perangkat keras**: bagian yang bisa dipegang. Contohnya layar dan tombol.
- **Perangkat lunak**: bagian yang tidak bisa dipegang. Contohnya game dan aplikasi.

Masih bingung? Coba trik ini. Pegang tanganmu. Bisa, kan? Sekarang coba pegang mimpimu tadi malam. Tidak bisa! Tanganmu seperti perangkat keras. Mimpimu seperti perangkat lunak.

## Ayo Coba Bersama

Kita coba dengan tablet, yuk. Minta izin dulu pada ayah atau ibu, ya.

1. Pegang badan tablet. Terasa keras dan dingin. Itu **perangkat keras**.
2. Sentuh layarnya dengan jarimu. Layar juga bisa disentuh. Layar adalah perangkat keras.
3. Buka aplikasi menggambar. Gambar bunga muncul di layar. Cantik!
4. Sekarang coba cubit gambar bunga itu. Angkat keluar dari layar. Tidak bisa! Aplikasi menggambar adalah **perangkat lunak**.

Mudah, kan? Kalau bisa dipegang, itu perangkat keras. Kalau tidak bisa dipegang, itu perangkat lunak.

::: check
Q: Sebutkan satu benda pintar yang ada di rumahmu!
A: Contohnya HP, tablet, laptop, atau komputer. Semuanya bisa mengikuti perintah kita.
Q: Tombol di tablet bisa ditekan dan dipegang. Tombol itu perangkat keras atau perangkat lunak?
A: Perangkat keras, karena tombol bisa dipegang.
:::

Kalau sudah siap, ayo lanjut ke bacaan berikutnya dan jadi detektif pegang-pegang!', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_diagram_id_v2', 'k2_computing_systems_devices', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Dua Bagian Benda Pintar', 'Benda pintar punya dua bagian. Peta di bawah ini menunjukkan keduanya. Ayo kita baca bersama!

```
        +---------------------+
        |    BENDA PINTAR     |
        |    (contoh: HP)     |
        +----------+----------+
                   |
         +---------+-------------+
         |                       |
         v                       v
+------------------+  +---------------------+
| PERANGKAT KERAS  |  | PERANGKAT LUNAK     |
| (bisa dipegang)  |  | (tak bisa dipegang) |
+------------------+  +---------------------+
| - layar          |  | - game              |
| - tombol         |  | - video             |
| - kamera         |  | - aplikasi belajar  |
+------------------+  +---------------------+
```

Legend:

- **Kotak**: satu kelompok. Kotak paling atas adalah benda pintarnya.
- **Garis dengan ujung v**: artinya "terbagi menjadi". Ikuti garisnya ke bawah.
- **Tanda -** di dalam kotak: daftar contoh untuk kelompok itu.

Cara membaca petanya:

1. Mulai dari kotak paling atas. Ada benda pintar, contohnya HP.
2. Ikuti garis ke bawah. Garisnya bercabang dua, seperti jalan bercabang.
3. Cabang kiri menuju perangkat keras: layar, tombol, dan kamera. Semuanya bisa dipegang.
4. Cabang kanan menuju perangkat lunak: game, video, dan aplikasi belajar. Semuanya tidak bisa dipegang.
5. Jadi, satu benda pintar selalu punya dua bagian ini.

::: tip
Main "tebak pegang" bersama temanmu! Tunjuk sesuatu pada benda pintar di rumah, lalu tanya: "Bisa dipegang atau tidak?" Kalau bisa dipegang, itu perangkat keras. Kalau tidak bisa, itu perangkat lunak.
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_audio_id_v2', 'k2_computing_systems_devices', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cerita Benda Pintar dan Isinya', NULL, NULL, 'Halo! Senang sekali bisa bercerita denganmu hari ini. Kita akan berkenalan dengan benda pintar.

Benda pintar itu apa, ya? Benda pintar adalah benda yang bisa mengikuti perintah kita. Komputer itu benda pintar. Laptop juga. Tablet dan HP juga benda pintar. Kalau kamu menekan tombolnya, mereka menurut. Sekarang bandingkan dengan bola. Kalau kamu berkata halo pada bola, bola diam saja. Bola bukan benda pintar.

Nah, setiap benda pintar punya dua bagian. Bagian pertama namanya perangkat keras. Perangkat keras adalah semua bagian yang bisa kamu pegang. Bagian kedua namanya perangkat lunak. Perangkat lunak tidak bisa dipegang. Tapi bisa dilihat, didengar, dan dimainkan.

Aku punya cerita untukmu. Suatu sore, kamu ingin menonton video kartun di HP ibu. Ibu mengizinkan. Kamu memegang HP itu dengan dua tangan. Terasa keras dan halus. Badan HP, layarnya, dan tombolnya bisa kamu pegang semua. Itu semua perangkat keras.

Lalu kamu menekan layar, dan video kartun pun mulai. Ada kelinci yang menari dan bernyanyi. Lucu sekali! Sekarang coba pikirkan. Bisakah kamu memegang kelinci itu? Jarimu hanya menyentuh layar. Kelincinya tidak bisa kamu genggam. Video kartun itu perangkat lunak. Bisa dilihat, bisa didengar, tapi tidak bisa dipegang.

Perangkat lunak itu mirip suara nyanyianmu. Kamu bisa mendengar nyanyianmu sendiri. Tapi kamu tidak bisa memegang suaramu, kan? Begitulah perangkat lunak.

Jadi ingat-ingat, ya. Benda pintar bisa mengikuti perintah kita. Benda pintar punya dua bagian. Perangkat keras bisa dipegang. Perangkat lunak tidak bisa dipegang.

Sekarang, ada pertanyaan untukmu. Kalau kamu menyentuh tombol kecil di samping HP, tombol itu perangkat keras atau perangkat lunak? Coba jawab dulu. Pelan-pelan saja.

Jawabannya adalah perangkat keras. Tombol bisa kamu pegang dan kamu tekan dengan jarimu. Semua yang bisa dipegang adalah perangkat keras. Hebat sekali! Sampai jumpa di cerita berikutnya!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_computing_systems_devices_reading_deep_id_v2', 'k2_computing_systems_devices', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Ayo Bedakan Perangkat Keras dan Perangkat Lunak', 'Kita sudah tahu: benda pintar seperti laptop dan HP punya dua bagian. Perangkat keras bisa dipegang. Perangkat lunak tidak bisa dipegang.

## Jadi Detektif Pegang-Pegang

Kakak sedang bermain game petualangan kucing di laptop. Ayo kita jadi detektif! Tugas kita: memeriksa satu-satu, mana perangkat keras dan mana perangkat lunak.

1. Periksa papan tombol, tempat huruf-huruf berbaris. Sentuh! Bisa dipegang. Berarti **perangkat keras**.
2. Periksa layar. Ketuk pelan-pelan. Bisa disentuh. Perangkat keras juga.
3. Periksa pengeras suara, lubang kecil tempat suara keluar. Bisa diraba. Perangkat keras lagi!
4. Sekarang periksa si kucing dalam game. Coba pegang kucingnya. Hihi, jarimu hanya menyentuh layar! Kucingnya tidak bisa digenggam. Game itu **perangkat lunak**.
5. Terakhir, dengarkan musik dalam game. Bisa didengar, tapi tidak bisa dipegang. Perangkat lunak juga.

Ini catatan detektif kita:

| Yang diperiksa | Bisa dipegang? | Jenisnya |
| --- | --- | --- |
| Papan tombol | Bisa | Perangkat keras |
| Layar | Bisa | Perangkat keras |
| Pengeras suara | Bisa | Perangkat keras |
| Game kucing | Tidak | Perangkat lunak |
| Musik game | Tidak | Perangkat lunak |

## Awas, Jangan Tertukar!

::: misconception
**Keliru:** "Game ada di dalam HP. HP bisa dipegang. Jadi game juga perangkat keras."
**Yang benar:** Yang kamu pegang adalah HP-nya, bukan game-nya. Game hanya bisa dilihat dan dimainkan. Seperti kartun di TV: TV-nya bisa dipegang, tapi kartunnya tidak bisa.
:::

Perangkat keras dan perangkat lunak selalu bekerja bersama. Seperti peluit dan bunyinya. Peluit bisa dipegang. Bunyinya tidak bisa. Tapi keduanya saling membutuhkan.

## Setelah Ini, Belajar Apa Lagi?

Hebat, kamu sudah bisa membedakan dua bagian benda pintar! Di sekolah, kemampuan ini termasuk capaian belajar SK-K2-1. Nanti kamu akan belajar lebih jauh: mengenal bagian-bagian benda pintar dan tugasnya masing-masing, melihat cara perangkat keras dan perangkat lunak bekerja sama, dan mencari tahu penyebabnya kalau benda pintar tiba-tiba rewel. Semua itu akan terasa mudah, karena kamu sudah paham pelajaran hari ini.

::: check
Q: Ayah memotret bunga dengan HP. Lensa kamera di belakang HP itu perangkat apa? Lalu aplikasi kameranya?
A: Lensa kamera bisa dipegang, jadi perangkat keras. Aplikasi kamera tidak bisa dipegang, jadi perangkat lunak.
Q: Adik berkata, "Lagu itu perangkat keras, karena keluar dari pengeras suara yang keras." Benar atau keliru?
A: Keliru. Pengeras suara memang perangkat keras. Tapi lagu tidak bisa dipegang. Jadi lagu adalah perangkat lunak.
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
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_reading_intro_en_v2', 'k2_culture', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Technology Has Two Sides: Sunny Helps and Rainy Troubles', 'Beep! That is the microwave making popcorn. Ring! That is a phone call from Grandpa. Technology is all around you, every single day. Some of it helps you a lot. Some of it can cause a little trouble, too.

## The Big Idea: Every Tool Has Two Sides

Think about rain. Rain helps flowers grow. Yay! But rain can also cancel your picnic. Aww. Rain is not all good or all bad. It is both.

Technology is like that too. **Technology** means machines and tools that people make. Phones, tablets, TVs, and talking speakers are all technology. Each one can help us. Each one can also cause trouble sometimes.

- A **help** makes life better. That is the sunny side.
- A **trouble** makes a problem. That is the rainy side.

Smart kids like you can spot both sides!

### Let''s Try One Together

Let''s think about watching cartoons on TV.

1. First, name the technology: **the TV**.
2. Next, find a sunny side: Cartoons make you laugh! You can learn new songs and new words.
3. Then, find a rainy side: If you watch too long, your eyes get tired. You might miss playing outside with your friends.
4. Last, say the whole thing out loud: "TV can help me learn songs, but too much TV makes my eyes tired."

You did it! You found a help and a trouble for the very same machine.

::: check
Q: You video call your grandma who lives far away, and it makes you both smile. Is that a sunny side or a rainy side of the phone?
A: A sunny side! The phone helps you see and talk to someone you love, even from far away.
Q: You play a tablet game so long that you forget to brush your teeth. Sunny side or rainy side?
A: A rainy side. The game caused a little trouble because it made you forget something important.
:::

Ready for more? In the next reading, you will become a real technology detective and practice on a silly robot.', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_diagram_en_v2', 'k2_culture', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'One Machine, Two Sides: A Sorting Picture', 'Here is a picture that sorts one technology into its two sides. Read it from the top down, like water flowing downhill.

```
            +----------------------+
            |    ONE TECHNOLOGY    |
            | (a washing machine)  |
            +----------------------+
                /            \
               v              v
  +--------------------+  +--------------------+
  |   SUNNY SIDE :)    |  |   RAINY SIDE :(    |
  |   (the helps)      |  |   (the troubles)   |
  +--------------------+  +--------------------+
  | clean clothes fast |  | loud rumble sound  |
  | more time to play  |  | uses lots of water |
  +--------------------+  +--------------------+
```

**Legend**

- Boxes hold ideas you can read.
- The top box is the technology we are checking.
- The lines with **v** are arrows. They mean "this leads to."
- **:)** marks the sunny side, the happy helps.
- **:(** marks the rainy side, the little troubles.

**How to read it**

1. Start at the top box. Name the technology. Here it is a washing machine.
2. Follow the left arrow down to the sunny side. Read the helps: clean clothes fast, and more time to play.
3. Follow the right arrow down to the rainy side. Read the troubles: a loud rumble, and it uses lots of water.
4. Notice something cool: one machine fills BOTH boxes.
5. Say both sides in one sentence: "It cleans our clothes fast, but it is loud and uses lots of water."

::: tip
Try this at home! Pick any machine in your house. Draw two boxes on paper. Put a sun over one and a rain cloud over the other. Then fill in one help and one trouble. You just made your own sorting picture!
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_audio_en_v2', 'k2_culture', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Two Sides of Technology', NULL, NULL, 'Hi there, friend! Today we are going to talk about technology. Technology means the machines and tools that people make. Phones are technology. Tablets are technology. Even the toaster that pops your toast is technology.

Here is the big idea. Every technology has two sides, kind of like rain. Rain helps the flowers grow. That is the good side. But rain can also cancel your trip to the park. That is the tricky side. Rain is not all good and not all bad. It is both. Technology is just the same.

Let''s think about a camera together. Maybe it is the camera on a grown-up''s phone. What is the good side? A camera helps you remember happy days. Snap! Now you can see your birthday cake again next winter. Snap! Now your aunt, who lives far away, can see how big you are getting. That is a real help.

But what is the tricky side? Imagine you are at a party. Someone takes pictures the whole time. They stare at the little screen instead of playing the games. They might even take a picture of a friend who did not want one, and that friend feels sad. So the very same camera can help us remember, and it can also cause a little trouble.

This is your new superpower. When you see a machine, ask two questions. Question one: how does this help people? Question two: what trouble could it make? When you ask both questions, you are thinking like a smart, careful technology detective.

Here is one more example, just for your ears. Think of a doorbell. Ding dong! It helps, because your family knows a friend is at the door. But if someone rings it over and over during nap time, that is trouble for the sleepy baby.

Now for your recap question. Ready? Is technology all good, all bad, or both at once? Think about it for a second. Here comes the answer. It is both! Almost every technology has a helping side and a trouble side. And now you know how to spot the two sides all by yourself. Great job, detective!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_reading_deep_en_v2', 'k2_culture', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Be a Technology Detective: Find the Helps and the Troubles', 'You know the big idea now: technology has a sunny side (the helps) and a rainy side (the troubles). Today you get to practice like a real detective.

## Detective Time: The Robot Vacuum

Meet Zoomy, a robot vacuum. It rolls around the floor and eats up crumbs. Let''s investigate it, step by step.

1. **Name it.** The technology is a robot vacuum.
2. **Ask: who does it help?** It helps Dad. He does not have to sweep. Now he has more time to build blocks with you. It helps you too. No crunchy crumbs under your feet!
3. **Ask: what trouble can it make?** It is loud. The rumbling might scare the cat. And if a tiny toy is on the floor, Zoomy might bump it or gobble it up.
4. **Ask: who feels the trouble?** The cat feels scared. You feel sad if your toy gets gobbled.
5. **Say both sides out loud.** "Zoomy gives my family more play time, but it can scare our cat and eat my little toys."

Did you spot the trick? One machine. Two sides. And different people (and cats!) feel different things. That is exactly what good detectives notice.

## Watch Out for This Mix-Up

::: misconception
Wrong idea: "Technology is all good!" or "Technology is all bad!"
The truth: Almost every technology is BOTH. Think of a bicycle. A bike is super fun and zooms you to the park fast. But you can also fall and scrape your knee. That does not make bikes bad. It means we ride them carefully, with a helmet on. Technology works the same way. We enjoy the helps, and we stay careful about the troubles.
:::

## Where This Leads

This detective skill grows right along with you. Soon, in Social Impacts for older kids, you will think about how technology changes whole neighborhoods and schools, not just one home. Later still, you will ask even bigger questions, like how to make technology fair and kind for everyone. It all starts with the two-sides trick you practiced today. Teachers have a fancy name for this skill, CSTA 1A-IC-16, but you can just call it being a technology detective.

::: check
Q: Your friend says, "Video games are only bad!" What could a technology detective say back?
A: A detective would say games have two sides. They can be fun and teach you to solve puzzles, but playing too long can make you miss sleep or playtime outside.
Q: A talking speaker plays your favorite songs, but it plays them so loud that the baby wakes up. Who feels the help, and who feels the trouble?
A: You feel the help, because you get the music you love. The baby and the grown-ups feel the trouble, because the loud sound wakes the baby up.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_reading_intro_id_v2', 'k2_culture', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Teknologi di Sekitarku: Baik atau Kurang Baik?', 'Coba lihat sekelilingmu. Ada televisi. Ada ponsel. Mungkin ada kipas angin juga. Semua itu namanya teknologi, dan teknologi ada di mana-mana: di rumah, di sekolah, bahkan di jalan.

## Ide Besar: Teknologi Itu Seperti Garam di Masakan

Pernah melihat Ibu memasak sup? Sedikit garam membuat sup jadi lezat. Tapi kalau garamnya terlalu banyak? Wah, supnya jadi asin sekali!

Teknologi juga begitu. Teknologi adalah alat buatan manusia. Kalau dipakai dengan tepat, alat ini **membantu** kita. Tapi kalau dipakai berlebihan atau sembarangan, alat ini bisa jadi **kurang baik** untuk kita.

- **Hal baik:** teknologi membantu kita belajar lagu baru, menerangi kamar saat gelap, dan bicara dengan keluarga yang jauh.
- **Hal kurang baik:** kalau terlalu lama menatap layar, mata bisa lelah dan kita lupa bermain bersama teman.

*Materi ini sesuai capaian DSI-K2-1.*

## Yuk Coba Bersama: Video Call dengan Nenek

Bayangkan Nenek tinggal jauh sekali. Naik bus saja butuh waktu seharian! Ikuti ceritanya, ya.

1. Ibu membuka ponsel dan menelepon Nenek lewat panggilan video.
2. Wajah Nenek muncul di layar. Nenek tersenyum dan melambai!
3. Kamu bercerita tentang sekolah. Nenek tertawa senang.
4. Telepon selesai. Kamu senang, Nenek juga senang. Ini **hal baik** dari teknologi.
5. Tapi setelah itu kamu terus main ponsel sampai sore. Mata jadi perih. Kamu lupa merapikan mainan. Ini **hal kurang baik**.

Lihat, ponselnya sama, lho! Yang berbeda adalah cara kita memakainya.

::: check
Q: Apa hal baik dari video call dengan Nenek?
A: Kita bisa melihat wajah Nenek dan mengobrol walaupun tinggal berjauhan.
Q: Apa hal kurang baik kalau main ponsel terlalu lama?
A: Mata jadi lelah dan kita bisa lupa bermain atau membantu di rumah.
:::

Di bacaan berikutnya, kita akan berlatih memilah lebih banyak hal baik dan kurang baik dari teknologi, langkah demi langkah.', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_diagram_id_v2', 'k2_culture', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Memilah Dampak Teknologi', 'Teknologi yang sama bisa membawa hal baik atau hal kurang baik. Peta di bawah ini membantumu memilahnya, seperti memilah mainan ke dua keranjang.

```
            +---------------------+
            |      TEKNOLOGI      |
            | (alat buatan orang) |
            +----------+----------+
                       |
           Bagaimana cara memakainya?
                       |
         +-------------+-------------+
         |                           |
         v                           v
+--------------------+    +--------------------+
| (+) MEMBANTU       |    | (-) KURANG BAIK    |
+--------------------+    +--------------------+
| Mesin cuci bantu   |    | Suara game keras,  |
| Ibu mencuci baju   |    | adik tak bisa tidur|
| Peta di ponsel     |    | Menonton terus,    |
| tunjukkan arah     |    | lupa sikat gigi    |
+--------------------+    +--------------------+
```

Legend:

- Kotak: satu benda atau satu kelompok dampak.
- Garis dan tanda panah (v): arah membaca, dari atas ke bawah.
- (+): dampak baik, teknologi membantu kita.
- (-): dampak kurang baik, teknologi membuat masalah.

Cara membaca peta ini:

1. Mulai dari kotak paling atas. Isinya teknologi, yaitu alat buatan orang.
2. Turun mengikuti garis dan baca pertanyaannya: "Bagaimana cara memakainya?"
3. Kalau cara pakainya tepat, ikuti panah kiri ke kotak (+) MEMBANTU. Contohnya mesin cuci membantu Ibu, dan peta di ponsel menunjukkan arah jalan.
4. Kalau berlebihan atau mengganggu, ikuti panah kanan ke kotak (-) KURANG BAIK. Contohnya suara game yang keras membuat adik tidak bisa tidur.
5. Ingat: satu alat bisa masuk ke dua kotak sekaligus, tergantung cara memakainya.

::: tip
Coba mainkan di rumah! Sebutkan satu alat, misalnya kipas angin. Lalu tunjuk: masuk kotak membantu atau kurang baik? Jawabannya boleh dua-duanya, asal kamu bisa menjelaskan alasannya.
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_audio_id_v2', 'k2_culture', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Teknologi, Kawan Kecil yang Perlu Aturan', NULL, NULL, 'Halo! Hari ini kita akan mengobrol tentang teknologi. Teknologi adalah alat-alat pintar buatan manusia. Televisi itu teknologi. Ponsel itu teknologi. Lampu lalu lintas di jalan juga teknologi.

Nah, ini ide besarnya. Teknologi bisa membawa hal baik, tapi juga bisa membawa hal kurang baik. Semuanya tergantung cara kita memakainya.

Teknologi itu mirip sepeda. Sepeda bisa membawamu ke taman dengan cepat. Menyenangkan sekali! Tapi kalau kamu ngebut dan tidak hati-hati, kamu bisa jatuh. Sepedanya sama. Yang berbeda adalah cara kita memakainya.

Ayo dengarkan satu contoh. Bayangkan kamu mau menyeberang jalan bersama Ayah. Di ujung jalan ada lampu lalu lintas. Lampunya berubah menjadi merah. Semua mobil berhenti. Kamu dan Ayah bisa menyeberang dengan aman. Nah, itu hal baik dari teknologi. Lampu lalu lintas menjaga kita tetap aman.

Sekarang contoh yang lain. Bayangkan saat makan malam, semua orang sibuk menonton video di ponsel masing-masing. Tidak ada yang mengobrol. Tidak ada yang bercerita. Makanannya sampai dingin. Wah, itu hal yang kurang baik. Ponselnya tidak jahat, tapi waktunya tidak tepat. Waktu makan malam adalah waktu untuk keluarga.

Jadi, apa yang bisa kamu lakukan? Pertama, pakai teknologi secukupnya, jangan terlalu lama. Kedua, pilih waktu yang tepat. Selesaikan dulu makan, tidur, dan bermain di luar. Ketiga, kalau bingung, tanya orang dewasa yang kamu percaya, seperti Ayah, Ibu, atau guru.

Sebelum kita selesai, coba jawab pertanyaan ini. Apakah teknologi selalu baik, atau selalu buruk?

Sudah punya jawaban? Ini jawabannya. Teknologi tidak selalu baik dan tidak selalu buruk. Teknologi itu alat. Kalau dipakai dengan tepat, teknologi membantu kita, seperti lampu lalu lintas yang menjaga kita saat menyeberang. Kalau dipakai berlebihan atau di waktu yang salah, teknologi bisa mengganggu, seperti ponsel di meja makan. Kamu yang memilih cara memakainya. Sampai jumpa di petualangan belajar berikutnya!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_culture_reading_deep_id_v2', 'k2_culture', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Memilah Hal Baik dan Kurang Baik dari Teknologi', 'Masih ingat ide besarnya? Teknologi itu seperti garam: pas takarannya, membantu; berlebihan, jadi kurang baik. Sekarang kita berlatih memilah dengan cerita yang lebih panjang.

## Contoh Lengkap: Sehari Bersama Ponsel Ibu

Ikuti cerita Rara dari pagi sampai malam. Di setiap langkah, tanyakan dalam hati: "Ini membantu atau kurang baik?"

1. **Pagi.** Alarm ponsel berbunyi. Kring! Rara bangun tepat waktu dan tidak terlambat ke sekolah. Ini membantu.
2. **Siang.** Ibu membuka resep kue di ponsel. Rara dan Ibu membuat kue bolu bersama. Harum sekali! Ini membantu.
3. **Sore.** Rara menonton video lucu. Satu video, dua video, sepuluh video. Rara lupa waktu. Matanya perih dan mainannya berantakan. Ini kurang baik.
4. **Malam.** Rara mengantuk saat makan malam karena terlalu lama menonton. Ini kurang baik.
5. **Sebelum tidur.** Rara dan Ibu membuat aturan baru: pakai ponsel sebentar saja, lalu bermain di luar atau membaca buku. Ini membantu!

Kita rangkum dalam tabel:

| Kejadian | Membantu atau kurang baik? |
|---|---|
| Alarm membangunkan Rara | Membantu |
| Resep kue di ponsel | Membantu |
| Menonton terlalu lama | Kurang baik |
| Mengantuk saat makan malam | Kurang baik |
| Aturan waktu layar | Membantu |

Ponselnya satu, tapi dampaknya bisa berbeda-beda. Semua tergantung cara dan waktu memakainya.

## Awas, Jangan Keliru!

::: misconception
Keliru: "Ponsel dan televisi itu jahat. Sebaiknya tidak dipakai sama sekali."
Yang benar: Teknologi itu alat, seperti gunting di kelas. Gunting membantu kita membuat prakarya, tapi harus dipakai dengan hati-hati. Teknologi juga begitu. Dipakai secukupnya dan dengan bantuan orang dewasa, teknologi jadi kawan yang membantu.
:::

Kebalikannya juga keliru, lho. Teknologi bukan selalu baik. Kalau dipakai terlalu lama atau di waktu yang salah, teknologi bisa mengganggu tidur, mata, dan waktu bermain kita.

## Setelah Ini, Belajar Apa Lagi?

Kebiasaan memilah "membantu atau kurang baik" yang kamu latih di sini akan terus kamu pakai. Di jenjang berikutnya, kamu akan belajar bagaimana teknologi memengaruhi lebih banyak orang, bukan hanya dirimu, misalnya teman sekelas dan tetanggamu. Lalu di jenjang yang lebih tinggi lagi, kamu akan belajar menjadi warga digital yang baik dan menimbang dampak teknologi untuk banyak orang sekaligus. Semuanya dimulai dari latihan sederhana hari ini.

::: check
Q: Sebutkan satu alat yang bisa membantu sekaligus bisa kurang baik. Jelaskan!
A: Contohnya televisi. Televisi membantu kita belajar lagu dan cerita, tapi kurang baik kalau ditonton terlalu lama sampai lupa tidur.
Q: Apa yang bisa kamu lakukan supaya teknologi tetap jadi kawan yang membantu?
A: Memakainya sebentar saja, berhenti saat sudah waktunya makan atau tidur, dan minta bantuan orang dewasa.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_reading_intro_en_v2', 'k2_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Count It, Chart It! Your First Data Adventure', 'Have you ever argued with a friend about which color is the best? Or wondered how many kids in your class have a loose tooth? You can find out — by counting! Counting things and showing what you counted is a real computer skill, and you can start today with just paper and crayons.

## The Big Idea: Find Out, Then Show

Here is a secret word: **data**. Data is just the stuff you find out when you ask questions and count things. Your age is data. The number of teeth you brushed this morning is data!

Working with data has two parts, like a two-step dance:

1. **Collect it.** Ask a question. Count the answers, one by one.
2. **Show it.** Turn your counts into a chart, so anyone can see the answer fast.

A chart is like showing your counting instead of just telling it. When counts become pictures, your eyes can spot the winner right away — no re-counting needed!

### Let''s Try It Together

Amira wants to know: *apples or bananas — which snack do my friends like more?*

1. She asks six friends, one at a time, like taking turns in line.
2. Every time someone says "apple," she draws one mark under a picture of an apple. Every "banana" gets a mark under a banana.
3. When everyone has answered, she counts the marks.

| Snack | Marks | How many |
| --- | --- | --- |
| Apple | * * * * | 4 |
| Banana | * * | 2 |

The apple row is longer. Amira can see the answer without counting again: her friends like apples more! She collected data, then she showed it. That is data analysis — and you just did it too.

::: check
Q: What is data?
A: Data is what you find out when you ask questions and count things, like how many friends picked apples.
Q: Amira''s chart shows 4 marks for apples and 2 marks for bananas. Which snack did more friends pick?
A: Apples! The apple row has more marks, and 4 is more than 2.
:::

Ready for more? In the next part, you will build a whole chart step by step, all by yourself.', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_diagram_en_v2', 'k2_data_collection', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Reading a Weather Chart from Top to Bottom', 'Charts turn counting into a picture your eyes can read in one second. Here is a chart about the sky during one school week — let''s learn to read it from top to bottom.

```
Question: What was the sky like this week?

+---------+   +---------+   +---------+
|  SUNNY  |   |  RAINY  |   | CLOUDY  |
+---------+   +---------+   +---------+
     |             |             |
     v             v             v
  * * * *        * *             *
   4 days       2 days         1 day
```

Legend:

- Box with a word = one kind of weather we watched for
- | and v = an arrow saying "the count is down here"
- * = one whole day of that kind of weather
- Number at the bottom = the total for that kind

How to read it:

1. Start at the top. The question tells you what the chart is all about.
2. Read the three boxes. Those are the choices: sunny, rainy, or cloudy.
3. Follow one arrow down. Under SUNNY, you land on a row of stars.
4. Count the stars: one, two, three, four. That means four sunny days.
5. Compare the groups. SUNNY has the most stars, so it was a mostly sunny week!

::: tip
When you make your own chart, keep every mark the same size and line them up neatly, like kids lining up for recess. Straight, even rows make the winner easy to spot in a blink.
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_audio_en_v2', 'k2_data_collection', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Birthday Party Ice Cream Count', NULL, NULL, 'Hi, friend! Today I want to tell you about a superpower you already have. It is counting — and then sharing what you counted.

Imagine you are at a birthday party. There are three ice cream flavors: chocolate, vanilla, and strawberry. You wonder, which flavor do most kids at this party love best? You could guess. But guessing can be wrong. So instead, you find out for real.

First, you ask a question. You say, "Which flavor is your favorite: chocolate, vanilla, or strawberry?" Then you ask each kid, one at a time, just like taking turns on the slide.

Every time someone answers, you make one little mark on your paper. One answer, one mark. Chocolate gets a mark. Chocolate again, another mark. Vanilla, mark. You keep going until every kid has answered.

Now you count your marks. Chocolate has five marks. Vanilla has three marks. Strawberry has two marks. All those marks together have a special name. They are called data. Data is just the stuff you find out when you ask and count.

Here comes the fun part. When you put your marks in neat rows, one row for each flavor, something wonderful happens. You do not even have to count again to know the winner. The chocolate row is the longest, so chocolate is the favorite. That is what a chart does. It turns your counting into a shape that answers the question super fast.

You can do this with anything. Count shoes with laces and shoes without laces. Count sunny days and rainy days. Ask one clear question, make one mark for each answer, put the marks in neat rows, and read your answer.

Time for one recap question. Ready? If vanilla has three marks and strawberry has two marks, which flavor did more kids pick? Think about it for a moment. Three is more than two. So the answer is vanilla. More kids picked vanilla than strawberry.

Great counting today! Next time you wonder about something, do not just guess. Ask, count, and chart it.', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_reading_deep_en_v2', 'k2_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'The Great Pet Count: Build a Chart Step by Step', 'You already know the two-step dance: first you **collect** data by asking and counting, then you **show** it with a chart so anyone can see the answer fast. Now let''s build a whole chart together, from start to finish.

## Worked Example: The Great Pet Count

Mr. Lee''s class wants to know: *which pet do kids have the most — a dog, a cat, or a fish?*

**Step 1: Pick one clear question.** The class agrees on exactly one question: "Do you have a dog, a cat, or a fish?" One question at a time keeps the counting easy.

**Step 2: Ask everyone, one at a time.** Ten kids answer, taking turns like lining up for lunch. Nobody shouts over anybody. One kid, one answer.

**Step 3: Make one mark for each answer.** Every answer gets one mark right away, before the next kid speaks. Here is the finished tally table:

| Pet | Marks | How many |
| --- | --- | --- |
| Dog | * * * * * | 5 |
| Cat | * * * | 3 |
| Fish | * * | 2 |

**Step 4: Turn it into a picture chart.** For every dog answer, the class draws one small dog. For every cat, one small cat. For every fish, one small fish. All the drawings are the same size, lined up in neat rows.

**Step 5: Read the chart.** The dog row is the longest. Dogs win! And here is a smart check: 5 + 3 + 2 = 10. That matches the ten kids who answered, so no answer got lost on the way.

## Watch Out for This Mix-Up

::: misconception
Wrong idea: "The row with the biggest drawings has the most."
The truth: how **big** a picture is does not matter — how **many** pictures there are is what counts. One giant fish drawing still means just one fish. Keep every picture the same size, then count them. The counting tells the truth, not the size.
:::

## Where This Leads

Everything you practiced here grows right along with you. In data analysis for grades 3 to 5, you will take the very same counts and show them in different kinds of charts, and you will let a computer help you sort and store them. Later, in middle school data analysis, you will use charts to spot patterns and make smart guesses about what might happen next. Grown-ups call this skill CSTA 1A-DA-06 — but you can just call it asking, counting, and charting.

::: check
Q: Rosa''s chart shows 5 marks for dogs, 3 marks for cats, and 1 mark for a bird. How many kids did she ask in all?
A: Add the rows together: 5 + 3 + 1 = 9 kids in all.
Q: Why should you make a mark the moment someone answers, instead of trying to remember all the answers for later?
A: Brains can forget, but marks do not! One mark per answer, right away, keeps the count true and fair.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_reading_intro_id_v2', 'k2_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Kenalan dengan Data: Menghitung Kesukaan Teman', 'Pernahkah kamu penasaran, buah apa yang paling disukai teman-teman sekelasmu? Kalau kamu tahu jawabannya, kamu bisa memilih bekal yang paling tepat untuk pesta kelas. Nah, ada cara seru untuk mencari tahu: bertanya, lalu mencatat!

## Ide Besar: Jawaban yang Dikumpulkan Namanya Data

Bayangkan mainanmu berserakan di lantai. Susah, kan, menghitung ada berapa mobil-mobilan? Tapi kalau mainan disusun rapi di rak, sekali lihat kamu langsung tahu jumlahnya.

Jawaban teman-teman juga begitu. Kalau hanya diingat-ingat di kepala, gampang lupa dan tercampur. Tapi kalau dicatat dengan rapi, kita bisa langsung melihat mana yang paling banyak. Kumpulan jawaban yang kita catat itu punya nama keren: **data**.

Ada dua alat sederhana untuk merapikan data:

- **Turus**: garis kecil untuk menghitung. Satu jawaban, satu garis. Kita menulisnya seperti huruf I.
- **Tabel**: kotak-kotak rapi seperti rak mainan. Setiap jawaban punya tempatnya sendiri.

## Ayo Coba: Buah Kesukaan

Kamu bertanya kepada 7 teman: "Buah apa kesukaanmu?"

Jawaban mereka satu per satu: apel, pisang, apel, jeruk, apel, pisang, apel.

Setiap mendengar satu jawaban, tulis satu turus di baris yang cocok:

| Buah | Turus | Jumlah |
| --- | --- | --- |
| Apel | IIII | 4 |
| Pisang | II | 2 |
| Jeruk | I | 1 |

Sekarang lihat tabelnya. Apel punya turus paling banyak. Jadi, buah yang paling disukai adalah apel! Coba cek juga: 4 + 2 + 1 = 7. Pas dengan jumlah teman yang kamu tanya. Hebat!

::: check
Q: Apa yang kita lakukan supaya jawaban teman-teman tidak lupa dan mudah dihitung?
A: Kita mencatatnya dengan rapi memakai turus dan tabel.
Q: Kalau 5 teman suka pisang, berapa turus yang kamu tulis untuk pisang?
A: Lima turus, karena satu jawaban selalu ditulis dengan satu turus.
:::

Di bacaan berikutnya, kita akan berlatih membuat tabel data sendiri langkah demi langkah, dari pertanyaan sampai selesai.', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_diagram_id_v2', 'k2_data_collection', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Empat Langkah Bermain Data', 'Bermain data itu seperti berjalan di peta: ada empat perhentian. Diagram ini menunjukkan jalannya, lengkap dengan contoh grafik gambar tentang warna kesukaan.

```
+-------+   +-------+   +--------+   +-------+
| TANYA |-->| CATAT |-->| HITUNG |-->| BACA  |
+-------+   +-------+   +--------+   +-------+

Contoh: "Warna apa kesukaanmu?"

  Merah  | * * * *      <- 4 anak
  Biru   | * *          <- 2 anak
  Kuning | * * *        <- 3 anak
```

Legend:

- Kotak (TANYA, CATAT, HITUNG, BACA) = langkah yang kamu lakukan
- --> = panah urutan, artinya "lanjut ke langkah berikutnya"
- * = satu bintang untuk satu anak yang memilih warna itu
- | = garis pemisah antara nama warna dan deretan bintang
- <- = keterangan jumlah bintang di baris itu

Cara membaca diagramnya:

1. Mulai dari kotak TANYA. Pilih satu pertanyaan, misalnya "Warna apa kesukaanmu?"
2. Ikuti panah ke CATAT. Setiap ada anak yang menjawab, gambar satu bintang di baris warnanya.
3. Lanjut ke HITUNG. Merah punya 4 bintang, Biru 2 bintang, Kuning 3 bintang.
4. Terakhir, BACA. Baris yang paling panjang adalah Merah, jadi warna yang paling disukai adalah merah.
5. Jangan lupa cek: 4 + 3 + 2 = 9 bintang, sama dengan 9 anak yang ditanya.

::: tip
Kamu bisa membuat grafik sungguhan di rumah. Pakai tutup botol atau stiker: satu benda untuk satu jawaban, lalu jajarkan dari kiri ke kanan. Baris yang paling panjang langsung terlihat!
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_audio_id_v2', 'k2_data_collection', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Detektif Kecil Pengumpul Data', NULL, NULL, 'Halo, teman kecil! Hari ini kita akan bermain menjadi detektif. Detektif suka mengumpulkan petunjuk. Nah, petunjuk kita hari ini punya nama istimewa. Namanya data. Data adalah kumpulan jawaban yang kita catat supaya tidak lupa.

Ayo kita mulai dengan sebuah cerita. Bayangkan malam ini keluargamu ingin membeli es krim. Tapi rasa apa yang harus dibeli? Cokelat? Stroberi? Atau vanila? Daripada bingung, kamu bisa mencari tahu dengan tiga langkah sederhana.

Langkah pertama, bertanya. Kamu bertanya kepada semua orang di rumah, satu per satu. Rasa es krim apa yang paling kamu suka?

Langkah kedua, mencatat. Setiap kali ada yang menjawab, kamu membuat satu garis kecil di kertas. Satu jawaban, satu garis. Ayah menjawab cokelat. Kamu menulis satu garis untuk cokelat. Ibu menjawab vanila. Satu garis untuk vanila. Kakak menjawab cokelat. Satu garis lagi untuk cokelat. Dan kamu sendiri memilih stroberi. Satu garis untuk stroberi.

Langkah ketiga, menghitung dan membaca. Sekarang hitung garisnya. Cokelat punya dua garis. Vanila punya satu. Stroberi juga satu. Rasa yang punya garis paling banyak adalah cokelat. Jadi, es krim cokelat adalah juaranya di rumahmu!

Kenapa kita harus mencatat? Kenapa tidak diingat saja di kepala? Coba bayangkan kamu harus mengingat sepuluh jawaban sekaligus. Wah, pasti tercampur, seperti kaus kaki yang hilang sebelah. Catatan itu seperti barisan anak yang mengantre dengan rapi. Sekali lihat, langsung bisa dihitung. Ingatan bisa lupa, tapi catatan tidak.

Satu hal lagi yang penting. Setelah selesai, hitung semua garismu. Jumlahnya harus sama dengan jumlah orang yang kamu tanya. Tadi kamu bertanya kepada empat orang, jadi harus ada empat garis. Kalau jumlahnya berbeda, berarti ada jawaban yang terlewat atau tercatat dua kali. Detektif yang baik selalu memeriksa ulang pekerjaannya.

Sekarang, pertanyaan untukmu. Kalau lima temanmu menjawab pertanyaanmu, berapa garis kecil yang harus kamu tulis?

Sudah menebak? Jawabannya lima. Karena satu jawaban selalu dicatat dengan satu garis. Tidak lebih, tidak kurang.

Hebat sekali! Sekarang kamu sudah tahu rahasianya. Bertanya, mencatat, menghitung, lalu membaca. Selamat berburu data, detektif kecil!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_data_collection_reading_deep_id_v2', 'k2_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Langkah demi Langkah Membuat Tabel Data Sendiri', 'Ingat ide besarnya: data adalah kumpulan jawaban yang kita catat. Kalau data disusun rapi dalam tabel, sekali lihat kita langsung tahu ceritanya.

## Latihan Lengkap: Naik Apa ke Sekolah?

Ayo kita buat tabel data dari awal sampai selesai, langkah demi langkah.

1. **Pilih satu pertanyaan.** Kita pilih: "Kamu berangkat ke sekolah naik apa?"
2. **Siapkan pilihan jawaban.** Ada tiga: jalan kaki, sepeda, atau diantar.
3. **Kumpulkan jawaban satu per satu.** Kamu bertanya kepada 10 teman. Setiap satu jawaban, langsung tulis satu turus di tempat yang cocok. Jangan ditunda-tunda!
4. **Hitung turusnya.** Jalan kaki ada 5 turus. Sepeda ada 2. Diantar ada 3.
5. **Susun menjadi tabel seperti ini.**

| Cara ke Sekolah | Turus | Jumlah |
| --- | --- | --- |
| Jalan kaki | IIIII | 5 |
| Sepeda | II | 2 |
| Diantar | III | 3 |

Terakhir, **baca datanya**. Paling banyak jalan kaki. Paling sedikit sepeda. Lalu periksa: 5 + 2 + 3 = 10. Sama persis dengan jumlah teman yang kamu tanya. Kalau jumlahnya beda, berarti ada jawaban yang terlewat atau terhitung dua kali.

Tabel kecil ini bisa menjawab banyak pertanyaan. Berapa anak yang naik sepeda? Dua. Mana yang paling banyak? Jalan kaki. Berlatih seperti ini adalah bagian dari capaian belajar AD-K2-1: mengumpulkan dan menyajikan data sederhana.

## Hati-Hati, Ini Sering Keliru

::: misconception
Keliru: "Aku tidak perlu mencatat. Aku bisa mengingat semua jawaban di kepala."
Yang benar: Ingatan mudah tercampur, seperti kaus kaki yang hilang sebelah. Tulislah satu turus untuk satu jawaban, tepat saat jawabannya kamu dengar. Lalu cek: jumlah semua turus harus sama dengan jumlah orang yang kamu tanya.
:::

## Ke Mana Ilmu Ini Membawamu?

Kebiasaan bertanya, mencatat, menghitung, lalu membaca data akan terus kamu pakai. Di kelas yang lebih tinggi, kamu akan mengubah tabel seperti ini menjadi diagram batang yang lebih besar dan membandingkan data yang lebih banyak. Lebih jauh lagi, kamu akan belajar memakai komputer untuk menyimpan dan menyusun data yang sangat banyak. Semuanya dimulai dari satu turus kecil yang kamu tulis hari ini.

::: check
Q: Kamu bertanya kepada 10 teman, tetapi jumlah semua turusmu 11. Apa artinya, dan apa yang harus kamu lakukan?
A: Ada jawaban yang tercatat dua kali atau salah tulis. Hitung ulang turusnya, atau kumpulkan jawabannya sekali lagi dengan lebih teliti.
Q: Dari tabel di atas, berapa teman yang berangkat tanpa diantar?
A: 7 teman, karena 5 anak jalan kaki ditambah 2 anak naik sepeda.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_intro_en_v2', 'k2_modularity', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Big Jobs, Little Pieces', 'Have you ever looked at your messy room and thought, "This is TOO big for me"? Big jobs can feel scary. But here is a happy secret: every big job is really a bunch of little jobs hiding inside.

## The Big Idea: Break It Into Pieces

You do not eat a pizza in one giant bite. You eat it slice by slice. Big jobs work the same way!

When a job feels too big, you can **break it into small parts**. Then you do one small part at a time. Each part is easy. And when all the parts are done — surprise! — the big job is done too.

Grown-ups use this trick all the time. People who make computer games do not build the whole game at once. They break it into tiny parts and make one part at a time.

You already know how to follow steps in order, like a recipe. This trick comes first: find the pieces. Then follow the steps for each piece.

### Let''s Try It: The Messy Room

The big job: **clean your room**. Whoa. That sounds hard. Let''s break it up!

1. Put the toys in the toy box.
2. Put the books on the shelf.
3. Put the clothes in the basket.

Now pick just one part. Toys first! That is easy — you can do that. Done? High five. Now books. Done! Now clothes. Done!

Three little jobs. One clean room. You did not do one giant job. You did three small ones — and that made all the difference.

::: check
Q: What can you do when a job feels too big?
A: Break it into small parts and do one small part at a time.
Q: You broke "clean your room" into toys, books, and clothes. When is the whole big job finished?
A: When every small part is done — the toys, the books, and the clothes are all put away.
:::

*(Teacher note: this lesson matches CSTA standard 1A-AP-14.)*

Want to see this trick build something big? In the next part, we will break down a whole castle, piece by piece.', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_diagram_en_v2', 'k2_modularity', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'How One Big Job Splits Into Small Jobs', 'A big job is like a puzzle made of small jobs. This picture shows one big job splitting into three small jobs — and how the small jobs add up to the finished big job.

```
         +--------------------------+
         |  BIG JOB: Class Party!   |
         +--------------------------+
           |           |           |
           v           v           v
     +----------+ +---------+ +---------+
     | Hang the | | Set out | | Pick a  |
     | balloons | | snacks  | | game    |
     +----------+ +---------+ +---------+
           |           |           |
           v           v           v
         +--------------------------+
         |  ALL DONE: Party ready!  |
         +--------------------------+
```

Legend:
- A box (drawn with +, -, and |) holds one job.
- The top box is the big job.
- The three middle boxes are the small jobs hiding inside the big job.
- A line with a v is an arrow. It means "go down to the next step."

How to read it:
1. Start at the top box. The big job is "Class Party!" That is a lot for one kid to do.
2. Follow the three arrows down. The big job splits into three small jobs.
3. Read the small boxes: hang the balloons, set out the snacks, pick a game. Each one is easy!
4. Do the small jobs one at a time. Finish one, then start the next.
5. Follow the arrows to the bottom box. When all three small jobs are done, the party is ready!

::: tip
Next time a job feels too big, draw your own boxes! Put the big job in a box at the top. Draw one box below it for each small part. Cross off each small box when you finish it — the crossing-off is the fun part.
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_audio_en_v2', 'k2_modularity', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Little-Jobs Secret', NULL, NULL, 'Hi, friend! Have you ever had a job that felt way too big? Maybe a grown-up said, please help with dinner, and you thought, that is a lot! Well, here is a secret that helpers and computer builders both use. Every big job is really a bunch of little jobs stuck together. When you find the little jobs, the big job stops being scary.

Let''s try it with a real job. Setting the table for dinner. Saying set the table all at once sounds like a lot. So let''s break it into small parts. Part one, put a plate at every seat. Part two, put a cup next to every plate. Part three, put a fork and a spoon by every plate. Part four, put a napkin at each spot.

Now do just one part. Plates first. Walk around the table. One plate for you, and one plate for each person in your family. Done! That was easy. Now cups. Done! Now forks and spoons. Done! Now napkins. Done! And guess what. When every little part is done, the whole table is set. The big job finished itself, one small piece at a time.

Little parts help in another way, too. If you forget the cups, you do not start the whole table over. You just do the cup part again. And if your sister wants to help, she can do the napkins while you do the plates. Small parts are easy to fix and easy to share.

You can play this game anywhere. When a job feels too big, stop and ask yourself, what small parts is it made of? Then do the parts one at a time, just like following the steps in a recipe. Cleaning up, packing a bag, building with blocks. Every big job is hiding little jobs inside, waiting for you to find them.

Here is your question before you go. What is the trick for a job that feels too big? The answer is, break it into small parts, do the parts one at a time, and when all the parts are done, the big job is done too. Great thinking. See you next time!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_deep_en_v2', 'k2_modularity', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Break It Down: Building Big Things from Small Parts', 'Here is the big idea again: every big job is made of little jobs. Break the big job into small parts, and each part becomes easy.

## Let''s Build a Block Castle

Today''s big job: build a giant block castle. All at once? Too big! Let''s use our trick, step by step.

**Step 1: Say the big job.**
"I want to build a castle." Saying it out loud helps you see how big it is.

**Step 2: Find the parts.**
What does a castle have? Hmm. Walls all around. A tall tower. A gate to walk through. That is three parts!

**Step 3: Do the first part.**
Build the walls. Just the walls. Line up blocks in a big square. Done! One part finished.

**Step 4: Do the next part.**
Build the tower. Stack blocks up, up, up in one corner. Done!

**Step 5: Do the last part.**
Build the gate. Leave a space in the wall for a door. Done!

**Step 6: Look at what happened.**
Walls, check. Tower, check. Gate, check. All the parts are done — so the castle is done!

Now here is the best part. Uh oh — the tower falls over! Do you knock down the whole castle and start again? No way. The walls are fine. The gate is fine. You only rebuild the tower. When a big thing is made of parts, you can fix one part and keep the rest.

And one more trick: parts are easy to share. A friend can build the gate while you build the tower. Two builders, two parts, one castle — twice as fast!

## But Wait — Is Breaking It Up Extra Work?

::: misconception
Some kids think: "Breaking a job into pieces takes extra time. It is faster to just do the whole big thing at once."
Not quite! When you try a whole big job in one go, it is easy to get stuck, tired, or mixed up. Small parts give you little wins along the way. You can rest between parts. You can share parts with a friend. And if one part goes wrong, you fix just that part. The pieces are not extra — the pieces ARE the job. When every piece is done, the big job is done.
:::

## Where This Trick Takes You

This trick grows with you. Soon you will give your small parts names, so you can use the same part again and again — like using your favorite tower plan in every castle you build. Later, you will make computer programs out of small parts that snap together just like blocks. Every big program in the world is built this way: little piece by little piece. What you practice today is exactly what the big kids do — just with bigger blocks.

::: check
Q: Your castle''s tower falls down, but the walls and gate are fine. What do you rebuild?
A: Only the tower. The castle is made of parts, so you can fix one part without touching the rest.
Q: You and a friend want to finish the castle faster. How do the parts help?
A: You each take a different part — one builds the tower while the other builds the gate — and the finished parts join into one castle.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_intro_id_v2', 'k2_modularity', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Memecah Tugas Besar Menjadi Bagian Kecil', 'Pernah melihat kamarmu berantakan sekali? Mainan di lantai, buku di kasur, baju di kursi. Rasanya berat, ya? Tenang. Ada trik hebat yang dipakai anak-anak pintar dan juga para pembuat komputer: pecah tugas besar menjadi bagian-bagian kecil!

## Ide Besar: Potong Tugasmu Seperti Memotong Kue

Bayangkan kue ulang tahun yang besar. Kamu tidak memakannya sekali telan, kan? Kamu memotongnya menjadi irisan kecil. Satu potong, lalu satu potong lagi. Lama-lama habis!

Tugas besar juga begitu. Kalau dilihat sekaligus, tugas besar terasa menakutkan. Tapi kalau dipecah menjadi bagian kecil, setiap bagian jadi mudah. Kamu kerjakan satu bagian dulu. Selesai! Lalu bagian berikutnya. Selesai lagi! Tanpa terasa, tugas besarnya tuntas.

Kamu sudah pernah belajar tentang langkah-langkah yang berurutan. Namanya algoritma. Nah, memecah tugas adalah teman baiknya algoritma. Pertama kita bagi tugas besar menjadi bagian-bagian kecil. Lalu tiap bagian kita kerjakan langkah demi langkah.

## Ayo Coba: Merapikan Kamar

Yuk kita coba bersama. Tugas besarnya: merapikan kamar. Wah, terdengar berat! Sekarang kita pecah:

1. **Bagian mainan** — masukkan semua mainan ke keranjang.
2. **Bagian buku** — susun buku di rak.
3. **Bagian baju** — lipat baju, taruh di lemari.

Lihat! Tugas besar yang tadi menakutkan sekarang menjadi tiga tugas kecil yang ramah. Kerjakan bagian mainan dulu. Selesai? Tos dulu! Lanjut ke buku. Lalu baju. Kamar rapi, kamu hebat!

Trik ini bisa kamu pakai di mana saja. Di rumah, di sekolah, saat bermain. Setiap kali ada tugas yang terasa besar, tanyakan pada dirimu: "Bagian-bagian kecilnya apa saja, ya?"

::: check
Q: Apa yang kita lakukan pada tugas besar supaya terasa lebih mudah?
A: Kita memecahnya menjadi bagian-bagian kecil, lalu mengerjakannya satu per satu.
Q: Saat merapikan kamar, sebutkan satu bagian kecil yang bisa dikerjakan lebih dulu!
A: Contohnya bagian mainan: memasukkan semua mainan ke keranjang. Bagian buku atau baju juga boleh!
:::

Di bacaan berikutnya, kita akan berlatih memecah tugas lain dan melihat kekeliruan yang sering terjadi. Siap? Ayo lanjut!', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_diagram_id_v2', 'k2_modularity', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Pohon Tugas: Dari Satu Tugas Besar ke Bagian Kecil', 'Tugas besar itu seperti pohon. Di atas ada satu tugas besar, di bawahnya bergantung bagian-bagian kecil. Yuk kita baca gambarnya pelan-pelan!

```
         +------------------------+
         |     TUGAS BESAR:       |
         |   Menggambar Rumah     |
         +-----------+------------+
                     |
      +--------------+--------------+
      |              |              |
      v              v              v
+-----------+  +-----------+  +-----------+
| Bagian 1  |  | Bagian 2  |  | Bagian 3  |
| Gambar    |  | Gambar    |  | Gambar    |
| atap      |  | dinding   |  | pintu dan |
|           |  |           |  | jendela   |
+-----------+  +-----------+  +-----------+
      |              |              |
      +--------------+--------------+
                     |
                     v
         +------------------------+
         |     Rumah selesai!     |
         +------------------------+
```

Legend:
- Kotak = sebuah tugas (yang besar atau yang kecil)
- Panah (v) = "dipecah menjadi" atau "menuju ke"
- Garis (| dan +) = penghubung antar kotak

Cara membacanya:

1. Mulai dari kotak paling atas. Tugas besarnya: menggambar rumah.
2. Ikuti panah ke bawah. Tugas besar dipecah menjadi tiga bagian kecil.
3. Kerjakan Bagian 1 dulu: gambar atapnya.
4. Lanjut ke Bagian 2 dan Bagian 3: dinding, lalu pintu dan jendela.
5. Semua garis bertemu lagi di bawah. Bagian-bagian bergabung, dan rumahmu selesai!

::: tip
Sebelum memulai tugas besar, gambarlah "pohon tugas" seperti ini di kertas. Tulis tugas besar di atas, lalu bagian-bagian kecil di bawahnya. Coret setiap bagian yang sudah selesai. Rasanya menyenangkan sekali!
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_audio_id_v2', 'k2_modularity', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Trik Hebat: Pecah Tugas Besar Jadi Kecil', NULL, NULL, 'Halo! Hari ini kita belajar satu trik hebat. Trik ini dipakai oleh koki, tukang bangunan, dan juga para pembuat komputer. Triknya begini: kalau ada tugas besar, pecahlah menjadi bagian-bagian kecil.

Kenapa begitu? Coba bayangkan. Tugas besar itu seperti gunung. Kalau kamu memandang seluruh gunung, wah, rasanya tinggi sekali. Tapi kamu tidak perlu melompat ke puncak. Kamu cukup melangkah satu kali. Lalu satu kali lagi. Setiap langkah itu kecil dan mudah. Lama-lama, sampai juga di atas.

Ayo kita coba dengan contoh. Setiap pagi, kamu bersiap ke sekolah. Itu tugas besar, lho. Kalau dipikirkan sekaligus, bisa bingung. Jadi kita pecah menjadi bagian-bagian kecil. Bagian pertama, memakai baju seragam. Bagian kedua, sarapan. Bagian ketiga, menyikat gigi. Bagian keempat, memakai sepatu dan mengambil tas.

Sekarang, kerjakan satu bagian saja dulu. Pakai bajumu. Selesai! Satu bagian beres. Lanjut sarapan. Selesai lagi! Sikat gigi. Beres! Pakai sepatu, ambil tas. Dan taraa, kamu siap berangkat. Tugas besar tadi selesai, padahal kamu hanya mengerjakan bagian-bagian kecil satu per satu.

Kamu sudah tahu bahwa langkah-langkah yang urut namanya algoritma. Nah, memecah tugas adalah teman baiknya algoritma. Pertama, pecah tugas besar menjadi bagian-bagian kecil. Lalu, kerjakan setiap bagian langkah demi langkah.

Ada satu rahasia lagi. Memecah tugas membuat kita bisa saling membantu. Kalau kamu dan adikmu ingin membereskan ruang tamu, kamu bisa mengambil bagian bantal, dan adikmu mengambil bagian mainan. Dua bagian dikerjakan bersama-sama. Pekerjaannya selesai lebih cepat, dan semua kebagian tugas yang mudah.

Jadi, mulai sekarang, kalau ada tugas yang terasa besar dan berat, jangan takut. Tarik napas dulu. Lalu tanyakan pada dirimu: bagian-bagian kecilnya apa saja, ya?

Sebelum kita selesai, coba jawab pertanyaan ini. Kalau kamu mendapat tugas besar, apa yang sebaiknya kamu lakukan lebih dulu supaya tugas itu terasa mudah?

Jawabannya: pecah tugas besar itu menjadi bagian-bagian kecil, lalu kerjakan satu per satu sampai semuanya selesai. Kamu pasti bisa. Sampai jumpa di petualangan belajar berikutnya!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_modularity_reading_deep_id_v2', 'k2_modularity', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Ayo Berlatih Memecah Tugas Besar', 'Ingat ide besarnya: tugas besar terasa mudah kalau dipecah menjadi bagian-bagian kecil. Sekarang kita berlatih lagi dengan contoh baru.

## Contoh Lengkap: Membuat Kartu Ucapan untuk Ibu

Tugas besarnya: membuat kartu ucapan yang cantik. Hmm, mulai dari mana, ya? Jangan bingung. Kita pecah dulu!

Bagian-bagiannya:

1. **Bagian kertas** — ambil kertas, lipat menjadi dua.
2. **Bagian gambar** — hias bagian depan dengan gambar bunga.
3. **Bagian tulisan** — tulis pesan sayang di bagian dalam.
4. **Bagian hiasan** — tempel stiker di sekelilingnya.

Sekarang kerjakan satu per satu:

- Ambil kertas. Lipat. Bagian kertas selesai!
- Gambar bunga di depan. Warnai. Bagian gambar selesai!
- Buka kartunya. Tulis "Aku sayang Ibu". Bagian tulisan selesai!
- Tempel stiker satu-satu. Bagian hiasan selesai!

Taraa! Empat bagian kecil selesai, dan jadilah satu kartu yang utuh dan cantik. Perhatikan: setiap bagian tadi punya langkah-langkahnya sendiri, seperti algoritma kecil. Lalu semua bagian bergabung menjadi satu hasil besar.

## Awas, Jangan Keliru!

::: misconception
Ada yang berpikir: "Memecah tugas membuat pekerjaan jadi lebih banyak dan lebih lama."
Itu keliru! Pekerjaannya tetap sama banyak. Tapi dengan memecahnya, kepalamu tidak pusing, kamu tahu harus mulai dari mana, dan kamu bisa senang setiap satu bagian selesai. Bagian kecil juga bisa dibagi dengan teman: kamu mengerjakan satu bagian, temanmu bagian yang lain. Malah jadi lebih cepat!
:::

## Ke Mana Ilmu Ini Membawamu

Kebiasaan memecah tugas besar — di sekolah, ini bagian dari capaian belajar BK-K2-3 — akan terus kamu pakai sampai besar nanti. Di kelas yang lebih tinggi, kamu akan memecah masalah komputer menjadi bagian-bagian, lalu menyusunnya kembali seperti balok mainan. Nanti kamu juga akan belajar bahwa satu bagian yang bagus bisa dipakai berulang-ulang untuk banyak tugas berbeda. Semua itu dimulai dari sini: melihat tugas besar dan berani berkata, "Ayo kita pecah dulu!"

::: check
Q: Nenek ingin membuat sup sayur. Coba pecah tugas besar itu menjadi tiga bagian kecil!
A: Contohnya: mencuci sayur, memotong sayur, dan memasak sayur di panci. Pembagian lain juga boleh, asal setiap bagian kecil dan jelas.
Q: Dua anak ingin membangun kota dari balok. Bagaimana memecah tugas bisa membantu mereka bekerja bersama?
A: Kota bisa dipecah menjadi bagian-bagian, misalnya rumah dan jalan. Satu anak membuat rumah, satu anak membuat jalan. Lalu bagian-bagian itu digabung menjadi satu kota yang utuh.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_reading_intro_en_v2', 'k2_networks_communication', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'How Devices Talk to Each Other', 'Have you ever seen Grandma''s face on a phone, even when she lives far away? Have you ever watched a silly cat video on a tablet? A hidden team of helpers carried those pictures to you. That team is called a **network**.

## The Big Idea: Devices Work as a Team

A **network** is a group of devices that pass messages to each other. It works like friends passing a note across the room. One friend hands the note to the next. The note keeps moving until it reaches the right person.

Devices pass their messages in two ways:

- **With cords.** Some devices are plugged in with a cable. The message zooms through the cord, like water through a straw.
- **Without cords.** Some devices use invisible waves in the air. People call this **Wi-Fi**. You cannot see the waves, but they are working all around you.

Some networks are small, like the one in your home. It might be just a tablet, a phone, and a Wi-Fi box. Some networks are HUGE. The biggest network of all is the **internet**. It connects computers all over the whole world.

## Follow Along: Sending a Drawing to Grandma

Let''s say you draw a dinosaur. You want Grandma to see it. Here is the trip your drawing takes:

1. A grown-up takes a photo of your drawing on a tablet.
2. They tap **send**. The tablet turns the photo into a message.
3. The message rides invisible waves to the Wi-Fi box in your house.
4. The Wi-Fi box sends it out through big cables to the internet.
5. The internet passes it along, helper to helper, all the way to Grandma''s phone.
6. Ding! Grandma sees your dinosaur and smiles.

The photo did not fly through the sky in one big jump. It hopped from helper to helper, like a note passed across a very, very big room.

::: check
Q: What is a network?
A: A team of devices that pass messages to each other, like friends passing a note.
Q: What are the two ways devices can send messages?
A: Through cords (cables) or without cords, using invisible waves called Wi-Fi.
:::

Next, we will follow one message on its whole trip, hop by hop. Let''s go!', NULL, NULL, 5, 0.3, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_diagram_en_v2', 'k2_networks_communication', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Path a Message Takes', 'Every message takes a trip. This picture shows the path a little "Hi!" takes from your tablet to a friend''s computer.

```
        YOU
    +--------+
    | Tablet |  "Hi!"
    +--------+
        |
       ))) invisible waves (no cord)
        |
        v
  +------------+
  | Wi-Fi Box  |
  +------------+
        |
       === cord (a real wire)
        |
        v
  ( The Internet )
   big cables everywhere
        |
        v
  +------------+
  | Friend''s   |
  | Computer   |  "Hi!" arrives!
  +------------+
```

**Legend**

- Boxes = devices and helpers you can touch
- ))) = wireless: invisible waves in the air
- === = wired: a real cord you can see
- ( ) = the internet, the biggest network in the world
- | and v = the direction the message travels

**How to read it**

1. Start at the top. Your tablet makes the message "Hi!"
2. Follow the ))) waves. The first hop is wireless, through the air, to the Wi-Fi box.
3. Follow the === cord. Now the message rides on a real wire.
4. It enters the internet and hops through big cables, maybe even under the ocean.
5. It pops out at your friend''s computer. The trip is done!

::: tip
Go on a network hunt at home! Find a cord plugged into a Wi-Fi box (that part is wired). Then count the devices with no cords at all (those are wireless). Ask a grown-up before touching any cables.
:::', NULL, NULL, 3, 0.4, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_audio_en_v2', 'k2_networks_communication', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Networks: Teams That Pass Messages', NULL, NULL, 'Have you ever asked a smart speaker to play your favorite song? You say the words, and a moment later, the music starts. That feels like magic. But it is not magic. It is a network.

A network is a team of devices that pass messages to each other. It works like friends passing a note across a classroom. One friend hands the note to the next friend, and the next, until it reaches the right person. Devices do the very same thing with their messages.

Here is what happens with the smart speaker. First, the speaker hears you ask for the song. It turns your words into a message. Then the message rides invisible waves through the air to the Wi-Fi box in your home. You cannot see those waves, but they are real, and they are all around you. Next, the Wi-Fi box sends the message into a cord, and the cord carries it out of your house. The message zooms through big cables under the streets. It hops from helper computer to helper computer until it reaches a faraway computer that keeps the song. That computer sends the song back the same way, hop by hop, all the way to your speaker. Then the music plays. All of those hops happen faster than you can blink.

Some parts of the trip use no cords at all. That is called wireless. Some parts use real cords and giant cables. That is called wired. Small networks, like the one in your home, connect just a few devices. The biggest network in the whole world is called the internet. It connects computers everywhere.

Here is your question. When your message travels to a faraway place, does it make one giant jump, or lots of little hops? Think about it for a moment. Ready? The answer is lots of little hops. Your message goes to the Wi-Fi box, then through cords and cables, helper to helper, until it arrives. Just like a note passed across a very, very big room.', 4, 0.45, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_reading_deep_en_v2', 'k2_networks_communication', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Hop by Hop: A Message''s Big Trip', 'You learned that a network is a team of devices passing messages. Some use cords, and some use invisible Wi-Fi waves. Now let''s follow one message on its whole trip.

## A Video Call, Step by Step

Imagine you call your cousin to show her your new puppy. Her face pops up on the screen. How does that work? Watch each hop:

1. **Your tablet listens and looks.** Its camera and microphone turn your voice and your puppy''s wiggly face into messages.
2. **First hop: invisible waves.** The messages ride Wi-Fi waves through the air to the Wi-Fi box in your home.
3. **Second hop: cords.** The Wi-Fi box pushes the messages into a cable. The cable runs out of your house.
4. **Many middle hops: the internet.** The messages zoom through big cables under the streets. Some cables even lie on the bottom of the ocean! Helper computers along the way read the address and say, "This way!"
5. **Last hop: your cousin''s house.** Her Wi-Fi box catches the messages and beams them to her tablet.
6. **Her tablet rebuilds the picture.** She sees your puppy and hears you laugh.

All of these hops happen faster than you can blink. And her messages make the same trip back to you at the very same time!

One more helper keeps your home network safe: a **password**. It works like a secret club word. Only devices that know the word may join your Wi-Fi. That keeps strangers out. (Teachers call this lesson CSTA 1A-NI-04.)

## A Mix-Up to Fix

::: misconception
Wrong idea: "Wireless" means the message floats through the air the whole way, with no wires at all.
The fix: The wireless part is usually just the first little hop, from your device to the Wi-Fi box. After that, the message travels through real cords and giant cables under streets and even under the ocean. Most of the trip happens on wires!
:::

## Where This Leads

Keep this picture in your head: messages hopping from helper to helper. In **Networks (K-5)**, you will learn that big messages get chopped into tiny pieces for the trip, and how the internet picks a path for each piece. Later, in **Networks (K-8)**, you will see the clever rules devices follow so every piece arrives and fits back together. The hop-by-hop idea you learned today is the seed for all of it.

::: check
Q: A message goes from your tablet to a friend far away. Does it make one giant jump or many little hops?
A: Many little hops. It goes to the Wi-Fi box, then through cables and helper computers on the internet, then to your friend''s Wi-Fi box and device.
Q: Why does a home Wi-Fi network have a password?
A: The password is like a secret club word. It lets your family''s devices join and keeps strangers'' devices out.
:::', NULL, NULL, 8, 0.6, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_reading_intro_id_v2', 'k2_networks_communication', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Bagaimana Alat-Alat Pintar Saling Bicara?', 'Coba ingat-ingat. Pernahkah kamu menelepon video nenek yang rumahnya jauh? Wajah nenek muncul di layar, suaranya juga terdengar jelas. Itu bisa terjadi karena ada sesuatu yang hebat bernama **jaringan**.

## Alat-Alat yang Bergandengan Tangan

Bayangkan kamu dan teman-teman berbaris sambil bergandengan tangan. Kalau kamu meremas tangan temanmu pelan-pelan, remasan itu bisa diteruskan sampai ke ujung barisan. Nah, jaringan itu mirip seperti itu!

**Jaringan** adalah alat-alat yang saling tersambung. HP, tablet, komputer, dan printer bisa ikut dalam jaringan. Karena tersambung, mereka bisa saling mengirim pesan. Pesannya bisa berupa foto, suara, atau video.

Ada dua cara alat bergandengan:

- **Pakai kabel.** Pesan berjalan di dalam kabel, seperti kereta yang berjalan di atas rel.
- **Tanpa kabel.** Pesan terbang lewat udara, seperti suaramu saat memanggil teman dari seberang lapangan. Cara ini sering disebut Wi-Fi.

Dua-duanya sama-sama bisa mengantar pesan sampai tujuan. (Materi ini selaras dengan capaian pembelajaran JKI-K2-1.)

## Ayo Ikuti Ceritanya

Kamu baru selesai menggambar kucing. Bagus sekali! Kamu ingin nenek melihatnya. Ayo kita antar fotonya:

1. Kamu memotret gambar kucing dengan tablet ibu.
2. Kamu menekan tombol kirim ke HP nenek.
3. Tablet mengubah foto menjadi pesan kecil.
4. Pesan terbang lewat udara ke kotak Wi-Fi di rumahmu.
5. Kotak Wi-Fi meneruskan pesan itu jauh sekali, sampai ke HP nenek.
6. HP nenek berbunyi. Ting! Foto kucingmu sampai!

Cepat sekali, ya? Padahal rumah nenek jauh dari rumahmu.

::: check
Q: Apa itu jaringan?
A: Alat-alat yang saling tersambung dan bisa saling mengirim pesan, seperti teman-teman yang bergandengan tangan.
Q: Sebutkan dua cara alat bisa tersambung ke jaringan.
A: Pakai kabel, dan tanpa kabel lewat udara (misalnya Wi-Fi).
:::

Di bacaan berikutnya, kita akan mengikuti perjalanan sebuah pesan langkah demi langkah, dan melihat siapa saja yang membantunya di tengah jalan.', NULL, NULL, 5, 0.3, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_diagram_id_v2', 'k2_networks_communication', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Jalan Sebuah Pesan', 'Kamu mengirim pesan suara "Selamat ulang tahun!" untuk sepupumu. Gambar ini menunjukkan jalan yang dilewati pesanmu dari atas sampai ke bawah.

```
 [Tabletmu]
     |
     v  ~ ~ ~  terbang lewat udara
[Kotak Wi-Fi rumahmu]
     |
     v  =====  berjalan lewat kabel panjang
[Kotak Wi-Fi rumah sepupu]
     |
     v  ~ ~ ~  terbang lewat udara
 [HP Sepupu]   Ting! Pesan sampai!
```

Legend:

- [ ] = alat, misalnya tablet, HP, atau kotak Wi-Fi
- | dan v = arah pesan berjalan, dari atas ke bawah
- ~ ~ ~ = jalan tanpa kabel, pesan terbang lewat udara
- ===== = jalan pakai kabel

Cara membaca gambarnya:

1. Mulai dari kotak paling atas. Tabletmu membuat pesan suara ulang tahun.
2. Pesan terbang lewat udara menuju kotak Wi-Fi di rumahmu.
3. Kotak Wi-Fi meneruskan pesan lewat kabel yang panjang sampai ke rumah sepupumu.
4. Kotak Wi-Fi di rumah sepupu menerbangkan pesan lewat udara lagi.
5. Pesan tiba di HP sepupu. Ting! Dia mendengar ucapanmu.

::: tip
Coba cari kotak Wi-Fi di rumahmu bersama orang dewasa. Perhatikan lampunya yang berkedip-kedip. Setiap kedipan artinya dia sedang sibuk meneruskan pesan!
:::', NULL, NULL, 3, 0.4, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_audio_id_v2', 'k2_networks_communication', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cerita Seru tentang Jaringan di Sekitar Kita', NULL, NULL, 'Halo, teman kecil! Hari ini kita akan mengobrol tentang sesuatu yang hebat. Namanya jaringan.

Coba dengarkan cerita ini. Di kelas, ibu guru duduk di depan komputernya. Dia ingin mencetak gambar bintang untuk kalian semua. Dia menekan satu tombol. Lalu, dari pojok kelas, terdengar suara printer. Printer itu mulai bekerja dan mengeluarkan kertas bergambar bintang. Padahal ibu guru tidak menyentuh printer itu sama sekali. Kok bisa, ya?

Bisa, karena komputer dan printer itu tersambung dalam satu jaringan. Jaringan adalah alat-alat yang saling tersambung, sehingga bisa saling mengirim pesan. Komputer ibu guru mengirim pesan kepada printer. Pesannya kira-kira begini. Tolong cetak gambar bintang ini, ya. Printer menerima pesan itu, lalu langsung bekerja.

Alat-alat bisa tersambung dengan dua cara. Cara pertama, pakai kabel. Pesan berjalan di dalam kabel, seperti kereta yang berjalan di atas rel. Cara kedua, tanpa kabel. Pesan terbang lewat udara. Seperti saat kamu memanggil temanmu dari seberang lapangan. Suaramu sampai ke telinganya, padahal tidak ada tali yang menghubungkan kalian. Sambungan tanpa kabel seperti ini sering dipakai HP dan tablet. Namanya Wi-Fi.

Jaringan ada di sekitar kita setiap hari. Saat ayah mengirim pesan singkat kepada ibu. Saat ibu memutar lagu dari HP. Saat kamu menonton video belajar di tablet. Semuanya memakai jaringan. Alat-alat itu seperti teman-teman yang bergandengan tangan. Mereka saling meneruskan pesan sampai ke tujuan.

Satu hal lagi yang seru. Pesan di dalam jaringan berjalan cepat sekali. Lebih cepat dari mobil balap. Lebih cepat dari kedipan matamu. Karena itu, pesanmu bisa sampai ke tempat yang sangat jauh dalam sekejap.

Sekarang, pertanyaan pengingat untukmu. Apa itu jaringan? Ayo pikirkan dulu sebentar. Jawabannya begini. Jaringan adalah alat-alat yang saling tersambung dan bisa saling mengirim pesan. Sambungannya bisa lewat kabel, bisa juga tanpa kabel lewat udara. Hebat sekali! Sampai jumpa di petualangan belajar berikutnya!', 4, 0.45, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_networks_communication_reading_deep_id_v2', 'k2_networks_communication', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Mengikuti Perjalanan Pesan Sampai ke Rumah Kakek', 'Masih ingat? Jaringan adalah alat-alat yang saling tersambung sehingga bisa saling mengirim pesan. Sekarang, ayo kita ikuti satu pesan dari awal sampai akhir.

## Perjalanan Telepon Video ke Kakek

Sore ini kamu menelepon video kakek. Ayo kita intip apa yang terjadi:

1. Kamu menekan gambar kakek di HP ibu.
2. HP mengubah suara dan wajahmu menjadi pesan-pesan kecil.
3. Pesan-pesan itu terbang lewat udara ke kotak Wi-Fi di rumahmu.
4. Kotak Wi-Fi meneruskannya lewat jalan yang panjang, melewati banyak kabel dan alat lain.
5. Pesan sampai di kotak Wi-Fi rumah kakek, lalu terbang ke HP kakek.
6. HP kakek menyusun pesan-pesan itu kembali menjadi wajah dan suaramu.
7. Kakek menjawab, "Halo, cucuku!" Jawabannya menempuh jalan pulang yang sama.

Semua itu terjadi bolak-balik dengan sangat cepat. Setiap alat punya tugasnya sendiri:

| Alat | Tugasnya |
| --- | --- |
| HP-mu | Membuat dan mengirim pesan |
| Kotak Wi-Fi | Meneruskan pesan, seperti pak pos |
| HP kakek | Menerima dan menyusun pesan |

## Hati-Hati, Jangan Keliru

::: misconception
Keliru: Pesan terbang sendirian, langsung dari HP-mu ke HP kakek, seperti burung yang terbang lurus tanpa berhenti.
Yang benar: Pesan berpindah dari satu alat ke alat lain, seperti tongkat dalam lari estafet. Kotak Wi-Fi dan kabel-kabel di jalan ikut membantu meneruskannya. Kalau salah satu penolongnya mati, pesan bisa berhenti di tengah jalan.
:::

## Ilmu Ini Akan Terus Berguna

Apa yang kamu pelajari hari ini adalah bekal yang penting. Di kelas yang lebih tinggi nanti, kamu akan belajar bahwa pesan besar dipotong menjadi potongan-potongan kecil dulu sebelum dikirim, lalu disusun lagi di tempat tujuan. Kamu juga akan belajar tentang jaringan raksasa bernama internet, yang menghubungkan hampir seluruh dunia. Semua itu akan terasa mudah kalau kamu sudah paham cerita perjalanan pesan hari ini.

::: check
Q: Saat telepon video, kamu bicara dan kakek langsung menjawab. Apa artinya itu tentang jaringan?
A: Jaringan mengirim pesan dua arah. Pesanmu pergi ke kakek, jawaban kakek pulang kepadamu, bolak-balik dengan sangat cepat.
Q: Kotak Wi-Fi di rumahmu mati karena listrik padam. Tabletmu masih menyala. Bisakah tablet mengirim foto lewat Wi-Fi rumah? Mengapa?
A: Tidak bisa. Kotak Wi-Fi adalah penerus pesan. Kalau penerusnya mati, tidak ada yang membawa pesan itu keluar dari rumah.
:::', NULL, NULL, 8, 0.6, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_reading_intro_en_v2', 'k2_program_development', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Try It, Fix It: How Programs Get Better', 'Did you ever zip your coat and it got stuck? You did not throw the coat away. You wiggled the zipper and tried again. Guess what — people who make computer programs do the very same thing!

## The Big Idea: Try, Check, Fix

You already know about step lists. A step list tells you what to do, one step at a time. A **program** is a step list for a computer. It is like a recipe for a cake, but for a machine.

Here is the fun part. First tries almost never come out perfect. Maybe a step is missing. Maybe two steps are in the wrong order. A mix-up like that has a silly name. It is called a **bug**!

So program makers do three things, over and over:

1. **Try it.** Do your steps and watch what happens. This is called *testing*.
2. **Check it.** Did it do what you wanted? Or did something go wrong?
3. **Fix it.** Find the mix-up, change that one step, and try again. This is called *debugging*.

That is it. Try, check, fix. Just like practicing hopscotch.

### Let''s Play Robot

Ask a grown-up or a friend to be your robot. Your job: get the robot to the door. Here are your steps:

1. Take three big steps.
2. Open the door.

Now test it! Say the steps out loud. Your robot takes three big steps and... bonk! The door is still far away. The robot''s hand grabs only air.

Your test found a bug! Step one is too small. Fix just that step:

1. Take **five** big steps.
2. Open the door.

Test it again. Step, step, step, step, step... the robot opens the door. Hooray!

You did not start over. You did not get mad. You fixed one step and tried again. That is exactly how real program makers work every single day.

::: check
Q: What is a bug in a step list?
A: A mix-up, like a missing step or steps in the wrong order, that makes the steps not work right.
Q: Your robot bonks into a wall. Should you throw away all your steps?
A: No! Find the one step with the mix-up, fix just that step, and try again.
:::

Ready for more? Next we will go on a real bug hunt and fix a whole step list together.', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_diagram_en_v2', 'k2_program_development', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Fix-It Circle', 'Program makers go around a little circle when they build something: make steps, try them, and fix any mix-ups. This picture shows the whole circle.

```
+------------+   +---------+   +--------------+
| MAKE STEPS |-->| TRY IT! |-->| DID IT WORK? |
+------------+   +---------+   +--------------+
                      ^            |        |
                      |           YES       NO
                      |            |        |
                      |            v        v
                      |        +------+  +----------+
                      |        | YAY! |  | FIND THE |
                      |        | DONE |  | MIX-UP   |
                      |        +------+  +----+-----+
                      |                       |
                      |      +---------+      |
                      +------| FIX IT! |<-----+
                             +---------+
```

Legend:
- Boxes are jobs to do.
- Arrows show where to go next.
- YES means your steps worked.
- NO means something went wrong.
- The long arrow back up to TRY IT! makes the fix-it circle.

How to read it:
1. Start at MAKE STEPS. Say your steps are for feeding a pet fish.
2. Follow the arrow to TRY IT! and do the steps for real.
3. At DID IT WORK?, pick a path. Fish fed and happy? Take YES down to YAY! DONE.
4. Food still stuck in your hand? Take NO down to FIND THE MIX-UP.
5. Move to FIX IT!, change the broken step, then ride the long arrow back up to TRY IT!
6. Go around the circle as many times as you need, until you land on YAY! DONE.

::: tip
Fix only **one** step each time around the circle. If you change lots of steps at once, you will not know which change made things better!
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_audio_en_v2', 'k2_program_development', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Every Mix-Up Can Be Fixed', NULL, NULL, 'Hi there, friend! Today we are talking about something super cool: how to make your steps better and better, just like real computer programmers do.

You already know that a step list tells someone what to do, one step at a time. A program is a step list for a computer. Now here is a secret that grown-up programmers know. The first try almost never works perfectly. And that is okay! When a step is missing, or two steps get flipped around, we call that mix-up a bug. What a funny name, right? A bug! And when we find a bug and fix it, that is called debugging. It is like being a bug detective.

Let me tell you about the morning I pretended to be a computer. My steps for making toast with jam went like this. Step one, take out a slice of bread. Step two, spread jam on the bread. Step three, put the bread in the toaster. Uh oh. Can you hear the problem? I put the jam on before the toasting. Sticky, drippy jam went right into the hot toaster. What a gooey mess!

But I did not give up, and I did not throw my steps away. I did what programmers do. I tested my steps, I found the bug, and I fixed just one thing. I moved the toasting step so it came before the jam step. Then I tried again. Toast first, jam second. Crunchy, sweet, and perfect.

That little circle is the whole big idea. Try your steps. Check if they worked. If something went wrong, hunt for the bug, fix one step, and try again. Go around the circle until it works. Remember, bugs are not bad news. Finding a bug means you are only one fix away from getting it right.

So the next time your paper airplane flops, or your dance moves get jumbled, you know the plan. Test, fix, and try again.

Here is your question before we go. What do we call a mix-up in a step list, and what should we do when we find one? The answer: it is called a bug, and we fix just that one step, then test our steps again. Happy bug hunting, detective!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_reading_deep_en_v2', 'k2_program_development', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Bug Hunters: Finding and Fixing Mix-Ups', 'Quick reminder of the big idea: a program is a step list for a computer, and first tries almost always have a mix-up called a bug. Good program makers test their steps, find the bug, fix it, and try again.

## A Bug Hunt, Step by Step

Pretend you wrote steps for a friend who is getting ready to play in the snow:

1. Put on shoes.
2. Put on socks.
3. Put on a coat.
4. Go outside.

Time to test! Your friend follows the steps *exactly*, like a robot.

- **Step 1:** Shoes go on. Okay so far.
- **Step 2:** Socks go on... over the shoes?! Lumpy and silly!

Stop right there. The test found bug number one: steps 1 and 2 are in the **wrong order**. Fix it by swapping them:

1. Put on socks.
2. Put on shoes.
3. Put on a coat.
4. Go outside.

Test again from the top. Socks, then shoes, then coat. Your friend goes outside... brrr! The coat is flapping wide open. Cold wind sneaks in!

That is bug number two: a **missing step**. Nothing says to zip the coat. Add one step:

1. Put on socks.
2. Put on shoes.
3. Put on a coat.
4. Zip the coat.
5. Go outside.

Test one more time. Warm and snug! Now you know the two most common bugs:

- Steps in the wrong order.
- A step that is missing.

And you know the fix-it plan: test, find the bug, change one little thing, test again.

## Wait — Bugs Are Bad, Right?

::: misconception
**Wrong idea:** "My steps had a bug. That means I did a bad job, and I should feel sad."
**The truth:** Bugs are normal! Every program maker, even grown-ups who do it all day long, finds bugs in their first try. Finding a bug is *good* news. It means your test worked, and now you know exactly what to fix. Bug hunters are proud hunters!
:::

Here is another wrong idea to squish: some kids think a broken step list must go in the trash. Never! You only fix the one step with the mix-up. The other steps are still great.

## Where This Takes You

You are learning to use steps, test them, and fix them — teachers call this skill CSTA 1A-AP-15. Soon, at the next level, you will build bigger programs piece by piece, like snapping blocks together, and your bug-hunting eyes will help you check each piece as you go. Later still, you will plan whole projects and test them carefully, like a scientist. It all grows from the little circle you learned today: try, check, fix.

::: check
Q: You test your steps and everything goes wrong at step 3. What should you change?
A: Only step 3, the step with the mix-up. Then test again from the start. Keep the good steps!
Q: Why do we test again after fixing a bug?
A: To make sure our fix really worked, and to catch any other bugs still hiding, like the missing zip step.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_reading_intro_id_v2', 'k2_program_development', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Coba, Cek, Perbaiki: Rahasia Membuat Program', 'Pernahkah menara balokmu roboh? Kamu tidak menangis lama. Kamu menyusunnya lagi dengan cara baru. Membuat program juga seperti itu: coba dulu, lihat hasilnya, lalu perbaiki.

## Ide Besarnya: Coba, Cek, Perbaiki

Kamu sudah kenal algoritma. Algoritma itu urutan langkah yang jelas. Nah, **program** itu urutan langkah yang kita berikan kepada komputer, robot, atau mainan pintar. Mereka akan mengikuti langkah itu persis, satu demi satu.

Tapi ada rahasianya. Program jarang langsung sempurna. Dan itu wajar sekali!

Karena itu, ada dua kebiasaan hebat:

- **Menguji**: mencoba program untuk melihat apakah hasilnya benar.
- **Memperbaiki**: mencari langkah yang keliru, lalu menggantinya.

Seperti koki mencicipi sup. Cicipi dulu. Kurang garam? Tambah sedikit. Cicipi lagi. Enak? Selesai!

### Contoh Kecil: Roti Selai

Ayo kita coba bersama. Bayangkan kamu menulis langkah membuat roti selai untuk ayah:

1. Ambil dua lembar roti.
2. Tempelkan kedua roti.
3. Oleskan selai.

Sekarang kita **uji**. Ayah mengikuti langkahnya persis, dan... wah! Selainya dioles di luar roti. Tangan ayah jadi lengket. Ada yang salah!

Kita jadi detektif. Langkah mana yang keliru? Ternyata langkah 2 dan langkah 3 tertukar. Selai harus dioles dulu, baru rotinya ditempel.

Kita **perbaiki** urutannya:

1. Ambil dua lembar roti.
2. Oleskan selai.
3. Tempelkan kedua roti.

Uji sekali lagi. Berhasil! Roti selainya rapi dan enak.

Itulah yang dilakukan pembuat program setiap hari: buat, coba, cek, perbaiki, lalu coba lagi. Tidak ada yang menyerah hanya karena salah satu langkah.

::: check
Q: Apa yang kita lakukan saat menguji sebuah program?
A: Kita mencoba menjalankan langkah-langkahnya, lalu melihat apakah hasilnya sesuai dengan keinginan kita.
Q: Program roti selai tadi salah. Apakah kita harus membuang semua langkahnya?
A: Tidak. Kita hanya mencari langkah yang keliru, lalu memperbaiki bagian itu saja.
:::

Di bacaan berikutnya, kita akan berlatih menjadi detektif kesalahan yang lebih hebat lagi.', NULL, NULL, 5, 0.3, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_diagram_id_v2', 'k2_program_development', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Lingkaran Coba dan Perbaiki', 'Setiap program berjalan lewat lingkaran yang sama: buat, coba, cek, lalu perbaiki. Diagram ini menunjukkan jalannya, seperti peta permainan.

```
   +----------------------+
   |  1. BUAT langkahnya  |
   +----------------------+
              |
              v
   +----------------------+
   |  2. COBA jalankan    |<------+
   +----------------------+       |
              |                   |
              v                   |
   +----------------------+       |
   |  3. CEK hasilnya     |       |
   +----------------------+       |
       |            |             |
   sudah pas    ada salah         |
       |            |             |
       v            v             |
 +----------+  +--------------+   |
 |  HORE!   |  | 4. PERBAIKI  |---+
 | Selesai  |  |  langkahnya  |
 +----------+  +--------------+
```

Legend

- Kotak = satu kegiatan yang kamu lakukan.
- Panah (v dan garis) = jalan menuju kegiatan berikutnya.
- "sudah pas" dan "ada salah" = dua pilihan setelah mengecek.
- Kotak HORE! = programmu sudah berhasil.

Cara membaca diagram ini:

1. Mulai dari kotak paling atas: buat langkah-langkah programmu.
2. Ikuti panah ke bawah: coba jalankan langkahnya satu per satu.
3. Cek hasilnya: sesuai keinginanmu atau belum?
4. Kalau sudah pas, ikuti panah kiri: hore, selesai!
5. Kalau ada salah, ikuti panah kanan: perbaiki langkah yang keliru.
6. Ikuti panah panjang kembali ke kotak COBA. Lingkaran ini boleh berputar berkali-kali sampai berhasil.

::: tip
Ujilah programmu sedikit demi sedikit, jangan tunggu sampai panjang sekali. Kesalahan di program pendek lebih mudah ditemukan, seperti mencari mainan di kotak kecil, bukan di gudang besar.
:::', NULL, NULL, 3, 0.4, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_audio_id_v2', 'k2_program_development', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Kalau Salah, Coba Lagi!', NULL, NULL, 'Halo! Hari ini kita bicara tentang program. Program itu urutan langkah yang kita berikan kepada komputer atau robot. Komputer akan mengikuti langkah itu persis, satu demi satu. Kamu sudah tahu tentang algoritma, kan? Program itu mirip sekali. Bedanya, program dibuat supaya mesin bisa mengikutinya.

Sekarang, ada rahasia penting. Program hampir tidak pernah langsung sempurna. Dan itu tidak apa-apa! Semua pembuat program, bahkan yang sudah dewasa, sering menemukan kesalahan. Yang hebat bukan orang yang tidak pernah salah. Yang hebat adalah orang yang mau mencoba, mengecek, lalu memperbaiki.

Ayo dengarkan cerita ini. Bayangkan kamu membuat urutan langkah untuk bersiap ke sekolah. Langkah satu: pakai sepatu. Langkah dua: pakai kaus kaki. Sekarang bayangkan kamu menjalankannya. Kamu pakai sepatu dulu. Lalu kamu coba pakai kaus kaki. Wah, tidak bisa! Kaus kaki tidak muat dipakai di luar sepatu. Rasanya aneh sekali.

Nah, sekarang kamu jadi detektif. Langkah mana yang keliru? Ternyata urutannya terbalik. Kaus kaki harus dipakai dulu, baru sepatu. Kamu tukar urutannya, lalu coba lagi. Pakai kaus kaki. Pakai sepatu. Pas! Nyaman! Berhasil!

Yang baru saja kamu lakukan itu punya nama keren. Mencoba program untuk melihat hasilnya, itu namanya menguji. Mencari langkah yang keliru lalu menggantinya, itu namanya memperbaiki kesalahan. Coba, cek, perbaiki, lalu coba lagi. Seperti lingkaran yang berputar terus sampai programmu berhasil.

Ingat juga, kamu tidak perlu membuang semua langkah kalau ada yang salah. Cukup ganti satu langkah yang keliru saja. Lalu uji lagi dari awal, supaya kamu yakin semuanya sudah benar.

Sekarang pertanyaan untukmu. Kalau programmu tidak berjalan seperti keinginanmu, apa tiga hal yang kamu lakukan? Coba pikirkan dulu. Sudah? Ini jawabannya. Pertama, jalankan lagi pelan-pelan dan cek setiap langkah. Kedua, temukan langkah yang keliru dan ganti langkah itu. Ketiga, uji lagi dari awal sampai berhasil. Kalau kamu berani mencoba dan tidak takut salah, kamu sudah berpikir seperti pembuat program sejati. Sampai jumpa!', 4, 0.45, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_program_development_reading_deep_id_v2', 'k2_program_development', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Jadi Detektif Kesalahan: Memperbaiki Program', 'Ingat ya: program itu urutan langkah untuk komputer atau robot, dan program jarang langsung sempurna. Tugas kita adalah mencoba, mencari langkah yang keliru, lalu memperbaikinya.

## Contoh Lengkap: Permainan Robot Kecil

Ayo main bersama teman. Temanmu jadi "robot". Robot hanya boleh mengikuti perintahmu, persis seperti yang kamu ucapkan. Tugasnya: berjalan dari kursi ke pintu.

Kamu membuat program ini:

1. Maju tiga langkah.
2. Belok kiri.
3. Maju dua langkah.

Sekarang kita uji! Temanmu maju tiga langkah. Bagus. Lalu belok kiri. Lalu maju dua langkah dan... duk! Robotmu menabrak lemari. Padahal pintunya ada di sebelah kanan!

Jangan panik. Ayo jadi detektif:

1. Lihat langkah 1: maju tiga langkah. Ini benar, robot makin dekat ke pintu.
2. Lihat langkah 2: belok kiri. Hmm, pintunya di kanan. Ketemu! Ini kesalahannya.
3. Ganti langkah 2 menjadi: belok kanan.
4. Uji lagi dari awal.

Program barumu: maju tiga langkah, belok kanan, maju dua langkah. Temanmu berjalan dan... sampai di pintu! Beri tepuk tangan. Kamu baru saja memperbaiki sebuah program.

Perhatikan satu hal penting. Kamu tidak mengganti semua langkah. Kamu hanya mengganti satu langkah yang keliru. Lalu kamu menguji lagi dari awal untuk memastikan semuanya benar.

## Awas, Jangan Salah Paham

::: misconception
Banyak anak berpikir: "Programku salah, berarti aku gagal dan harus mulai dari nol."
Itu keliru. Kesalahan adalah bagian biasa dari membuat program. Pembuat program dewasa pun menemukan kesalahan setiap hari. Kamu tidak perlu membuang semuanya. Cukup temukan langkah yang keliru, ganti langkah itu saja, lalu uji lagi. Menemukan kesalahan artinya kamu sedang menjadi detektif yang teliti, bukan gagal.
:::

## Ke Mana Ilmu Ini Membawamu?

Kebiasaan coba, cek, dan perbaiki ini akan terus kamu pakai. Di kelas berikutnya, kamu akan membuat program yang lebih panjang, merencanakannya dulu, dan memperbaikinya dengan lebih teliti. Nanti kamu juga akan mengerjakan proyek yang lebih besar bersama teman, dan kalian akan saling membantu mencari kesalahan. Di pelajaran informatika, kebiasaan hebat ini termasuk dalam standar AP-K2-3. Semuanya dimulai dari sini: berani mencoba, dan tidak takut salah.

::: check
Q: Robot mainanmu berhenti sebelum sampai tujuan. Apa urutan cara paling baik untuk menolongnya?
A: Jalankan lagi pelan-pelan sambil memeriksa setiap langkah, temukan langkah yang keliru, ganti langkah itu saja, lalu uji lagi dari awal.
Q: Temanmu mengubah satu langkah di programmu supaya lebih bagus. Bagaimana cara tahu perubahan itu berhasil?
A: Uji programnya: jalankan dari awal sampai akhir dan lihat apakah hasilnya sesuai tujuan. Kalau belum, cari lagi langkah yang keliru dan perbaiki.
:::', NULL, NULL, 8, 0.6, '["k2_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_intro_en_v2', 'k2_variables', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'A Special Box with a Name', 'Do you keep score when you play a game? Does the score go up when you win a point? That changing number has a secret behind it — and it is the same secret computers use to remember things.

## The Big Idea: A Box with a Name

Pretend you have a little box. You write a name on it. The box holds one thing.

A computer is full of tiny boxes like this. Each box has a name. Each box holds one thing. And here is the fun part: the thing inside can change!

Think of your cubby at school. Your cubby always has your name on it. But what is inside changes. A coat in winter. A sun hat in summer. Same cubby. Same name. Different things inside.

Big kids and grown-up coders call a box like this a **variable**. That is a big word for a simple idea. A variable is a box with a name. It holds something. And that something can change.

## Try It: The Sticker Jar

You can do this one for real, or just in your head.

1. Find a jar. Put a label on it that says **my stickers**.
2. Drop in 1 sticker. The jar named "my stickers" holds 1.
3. You earn 2 more stickers. Drop them in. Now the jar holds 3.
4. You give 1 sticker to a friend. Take it out. Now the jar holds 2.

Look at what happened. The name never changed. It was "my stickers" the whole time. But the number inside changed again and again. That is exactly what a variable does.

::: check
Q: You put something new into a name box. Does the name on the box change?
A: No. The name stays the same. Only the thing inside changes.
Q: A jar named "shells" holds 4 shells. You add 1 more. What does the jar hold now?
A: 5 shells. It is still the jar named "shells," but the number inside changed from 4 to 5.
:::

Ready for more? Next we will play a whole game, step by step, and watch one box change over and over.', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_diagram_en_v2', 'k2_variables', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Apple Box: Before and After', 'This picture shows one name box at two moments: before a change and after a change. The box is named "apples."

```
       BEFORE                      AFTER

  +---------------+          +---------------+
  | name: apples  |          | name: apples  |
  +---------------+    +1    +---------------+
  |  inside:  2   | -------> |  inside:  3   |
  +---------------+          +---------------+

  The name stays the same.
  Only the number inside changes.
```

**Legend**

- Each rectangle made of +, -, and | marks is one name box.
- "name:" is the label on the box. It never changes.
- "inside:" is what the box holds right now.
- The arrow ( -------> ) means time passes and a change happens.
- "+1" means one apple was added.

**How to read it**

1. Start with the left box, under BEFORE. Its name is "apples," and it holds 2.
2. Follow the arrow to the right. The "+1" above it tells you one apple was added.
3. Read the right box, under AFTER. Its name is still "apples." Now it holds 3.
4. Compare the two boxes. The name did not change at all. The number inside did.

::: tip
Make this picture real! Tape a paper label on a cup and write any name you like on it. Drop in some buttons or beans. Count them. Add one, then count again. The label stays the same, but the count changes — just like in the picture.
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_audio_en_v2', 'k2_variables', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Name Stays, the Number Changes', NULL, NULL, 'Hi, friend. Today I want to tell you about a clever trick that computers use to remember things.

Think about your age. Your age is a number, and it belongs to you. Maybe you are six right now. On your next birthday, you will be seven. The word age stays the same, but the number changes. One name, and a number inside that can change. That is the whole trick.

Computers remember things the very same way. Imagine that a computer is full of tiny boxes. Every box gets a name, like the label on a lunch bag. One box might be named age. Another box might be named points. Inside each box, the computer keeps one thing, such as a number.

Here is the magic part. The thing inside the box can change. When something new goes in, the old thing goes away. The box keeps only the newest thing. But the name on the box never, ever changes. Big kids call this kind of box a variable. You can just call it a name box for now.

Let''s play a quick pretend game together. Pretend you are playing a jumping game, and a computer is counting your jumps. First, the computer makes a box and names it jumps. It puts a zero inside, because you have not jumped yet. Now you jump one time. The computer takes out the zero and puts in a one. You jump again. Out goes the one, and in goes the two. One more big jump! Out goes the two, and in goes the three. The box is still named jumps. Only the number inside changed.

This is how a game remembers your score, and how a tablet remembers how loud your song should be. Something with a name holds a number, and that number can change.

Here is one question before you go. When a new number goes into a name box, what happens to the name, and what happens to the old number? Think about it. Ready? The name stays exactly the same, and the old number goes away, because a name box keeps only the newest thing. Great thinking. See you next time.', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_deep_en_v2', 'k2_variables', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Watch What''s Inside the Box Change', 'Remember the big idea: a variable is a box with a name. The name stays the same, but the thing inside can change.

## Step by Step: The Bean Bag Game

Let''s watch one box change during a real game. You are tossing bean bags into a basket. A whiteboard keeps your score.

1. Draw a box on the whiteboard. Write the name **points** above it. Write **0** inside, because the game has not started yet.
2. Toss your first bean bag. It lands in the basket! Erase the 0. Write **1**.
3. Toss again. Oh no, it misses. Do not touch the box. It still holds 1.
4. Toss again. It lands! Erase the 1. Write **2**.
5. Last toss. It lands too! Erase the 2. Write **3**.
6. The game is over. Look at the box named "points." It holds 3. That is your score!

Notice two things. First, you never erased the name. Only the number got erased and rewritten. Second, the box held just one number at a time. Never two.

That is how a computer keeps score in your favorite games. It has a box named something like "points," and it changes the number inside every time you do something great.

## Where Did the Old Number Go?

Here is a tricky question. When you wrote 2 in the points box, where did the 1 go?

::: misconception
Wrong idea: The box remembers all the old numbers too. The 0, the 1, and the 2 are all still in there somewhere.
Actually: A name box holds only ONE thing — the newest one. When a new number goes in, the old number is gone, like an erased mark on a whiteboard. If you want to keep the old number too, you need another box with its own name.
:::

## Where This Leads

You just learned the very first idea about variables, and it matches a school learning goal called CSTA 1A-AP-09. Here is where it takes you next. Soon, you will make name boxes inside real programs and pick the names all by yourself. Later, your boxes will hold more than numbers — they can hold words, like a name or a color. Every game, app, and robot you will ever build uses boxes just like the ones you played with today.

::: check
Q: A box named "snack" holds the word "apple." You put the word "banana" in. What is inside now, and why isn''t "apple" there?
A: The box holds "banana." A name box keeps only the newest thing, so putting in "banana" made "apple" go away.
Q: A box named "hats" holds 2. You put in 5. Then you put in 1. What is inside at the end?
A: 1. The box keeps only the last thing you put in. The 2 and the 5 are gone.
:::', NULL, NULL, 8, 0.6, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_intro_id_v2', 'k2_variables', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Kotak Ajaib yang Isinya Bisa Berganti', 'Pernah lihat toples camilan di rumah? Kemarin isinya biskuit. Hari ini isinya pisang. Toplesnya sama, tapi isinya berganti-ganti. Nah, komputer juga punya banyak "toples" seperti itu!

## Kotak Bernama yang Isinya Bisa Berganti

Komputer suka menyimpan banyak hal. Angka. Kata. Nama teman. Semua itu disimpan di dalam kotak-kotak kecil. Setiap kotak punya nama sendiri. Kotak bernama itu punya sebutan keren: **variabel**.

Variabel punya dua aturan main:

- Nama kotak selalu tetap. Tidak berganti-ganti.
- Isi kotak boleh diganti. Kapan saja!

Jadi kalau ada isi baru, kita tidak perlu kotak baru. Cukup keluarkan isi lama. Masukkan isi baru. Selesai! Gampang sekali, kan?

### Ayo ikuti: toples "Camilan"

1. Ibu punya satu toples. Namanya "Camilan".
2. Pagi-pagi, Ibu mengisinya dengan biskuit. Isi toples: biskuit.
3. Siang hari, kamu memakan biskuitnya. Toples jadi kosong.
4. Sore hari, Ibu memasukkan pisang. Isi toples: pisang.

Coba perhatikan. Nama toples selalu "Camilan", dari pagi sampai sore. Yang berganti hanya isinya. Komputer bekerja persis seperti itu. Ia menyimpan sesuatu di dalam kotak bernama. Lalu mengganti isinya bila perlu. Begitulah cara komputer mengingat skor game, nama pemain, dan banyak hal lain.

::: check
Q: Toples "Camilan" tadi pagi berisi biskuit. Sekarang berisi pisang. Apa yang berganti?
A: Isinya yang berganti, dari biskuit menjadi pisang. Nama toplesnya tetap "Camilan".
Q: Variabel itu paling mirip dengan benda apa?
A: Mirip kotak yang punya nama. Kotak itu menyimpan satu isi, dan isinya bisa diganti.
:::

Di bacaan berikutnya, kita akan menonton variabel bekerja di papan skor permainan lempar bola. Seru!', NULL, NULL, 5, 0.3, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_diagram_id_v2', 'k2_variables', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Papan Cuaca: Satu Kotak, Isi Berganti', 'Di banyak kelas ada papan kecil bernama "Cuaca". Setiap hari isinya diganti sesuai langit di luar. Gambar di bawah ini menunjukkan cara kerjanya — persis seperti variabel di dalam komputer.

```
         PAGI
   +------------------+
   | nama: Cuaca      |
   | isi : ( cerah )  |
   +------------------+
            |
            |  hujan turun!
            |  isi diganti
            v
         SIANG
   +------------------+
   | nama: Cuaca      |
   | isi : ( hujan )  |
   +------------------+
```

Legend:

- Kotak bergaris = satu variabel, yaitu kotak yang punya nama.
- "nama:" = label kotak. Tidak pernah berganti.
- "isi :" = benda yang sedang disimpan di dalam kotak.
- ( ... ) = isi kotak pada saat itu.
- Tanda panah ke bawah = waktu berjalan dan isi diganti.

Cara membaca gambarnya:

1. Mulai dari kotak paling atas. Namanya "Cuaca". Pagi hari, isinya "cerah".
2. Ikuti tanda panah ke bawah. Hujan turun, jadi isinya harus diganti.
3. Isi lama, "cerah", dikeluarkan. Isi baru, "hujan", dimasukkan.
4. Lihat kotak paling bawah. Namanya masih "Cuaca". Isinya sekarang "hujan".
5. Hitung kotaknya: dari pagi sampai siang, kotaknya tetap satu. Hanya isinya yang berganti.

::: tip
Buat papan "Cuaca" sungguhan di rumah! Tulis kata "Cuaca" di kertas besar. Lalu tempelkan kartu kecil bergambar matahari atau awan. Ganti kartunya setiap hari. Tanpa sadar, kamu sedang memainkan sebuah variabel!
:::', NULL, NULL, 3, 0.4, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_audio_id_v2', 'k2_variables', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cerita Kotak Bernama yang Isinya Berganti', NULL, NULL, 'Hai, teman kecil! Hari ini kita akan bicara tentang kotak ajaib. Bukan kotak sungguhan, tapi kotak di dalam pikiran komputer.

Bayangkan di kelasmu ada papan kecil di dekat pintu. Di atas papan itu tertulis satu nama: Hari Ini. Setiap pagi, guru menaruh satu kartu di papan itu. Hari Senin, kartunya bertuliskan Senin. Besok paginya, guru mengambil kartu Senin dan menaruh kartu Selasa. Papannya tetap papan yang sama. Namanya tetap Hari Ini. Tapi isinya berganti setiap hari.

Nah, komputer juga punya banyak papan kecil seperti itu. Setiap papan punya nama. Setiap papan bisa menyimpan satu isi. Dan isinya boleh diganti kapan saja. Papan bernama itu punya sebutan keren: variabel.

Kenapa ini penting? Coba ingat saat kamu bermain game di tablet. Di layar ada angka skor. Setiap kali kamu berhasil, angkanya naik. Itu karena komputer menyimpan skormu di dalam satu kotak bernama. Lalu komputer mengganti isinya dengan angka yang baru. Kotaknya tetap, isinya berganti.

Ayo kita coba bersama. Bayangkan kamu punya kotak bernama Hewan Kesukaan. Hari ini kamu suka kucing. Maka isi kotaknya adalah kucing. Minggu depan, kamu jadi suka kelinci. Apa yang kamu lakukan? Kamu tidak membuang kotaknya. Kamu hanya mengeluarkan kata kucing, lalu memasukkan kata kelinci. Kotaknya masih bernama Hewan Kesukaan. Isinya sekarang kelinci. Mudah, kan?

Jadi, ingat dua hal ini. Pertama, variabel itu seperti kotak yang punya nama. Kedua, isinya bisa berganti, tapi namanya selalu tetap.

Sekarang, satu pertanyaan penutup untukmu. Papan bernama Hari Ini sedang berisi kartu Rabu. Besok pagi, guru akan menggantinya. Kira-kira, apa yang berubah, dan apa yang tetap?

Jawabannya begini. Isinya yang berubah, dari Rabu menjadi Kamis. Nama papannya tetap Hari Ini. Itulah variabel. Kotaknya tetap, isinya boleh berganti. Sampai jumpa di petualangan berikutnya!', 4, 0.45, '[]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k2_variables_reading_deep_id_v2', 'k2_variables', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Papan Skor: Variabel Sedang Bekerja', 'Masih ingat idenya? Variabel itu seperti kotak yang punya nama. Namanya selalu tetap, tapi isinya boleh berganti.

## Melihat Variabel Bekerja: Papan Skor

Dinda dan teman-teman bermain lempar bola ke keranjang. Bu Guru membawa papan tulis kecil. Di atasnya tertulis satu nama: "Skor". Ayo kita ikuti pelan-pelan.

1. Sebelum permainan mulai, Bu Guru menulis angka 0. Isi papan "Skor" sekarang: 0.
2. Dinda melempar. Bolanya masuk! Bu Guru menghapus angka 0, lalu menulis angka 1.
3. Dinda melempar lagi. Dua bola masuk sekaligus! Bu Guru menghapus angka 1, lalu menulis angka 3.
4. Permainan selesai. Isi papan "Skor" sekarang: 3.

| Kejadian | Isi papan "Skor" |
| --- | --- |
| Permainan dimulai | 0 |
| Satu bola masuk | 1 |
| Dua bola masuk lagi | 3 |

Coba hitung papannya. Cuma ada satu! Dari awal sampai akhir, namanya selalu "Skor". Yang berganti hanyalah angkanya. Saat kamu bermain game di komputer atau tablet, hal yang sama terjadi di dalamnya. Ada kotak bernama untuk skormu. Setiap kali kamu berhasil, komputer mengganti isinya dengan angka baru.

## Awas, Jangan Keliru!

::: misconception
Ada yang mengira: "Kalau isinya baru, kita harus membuat kotak baru. Jadi perlu satu kotak untuk angka 0, satu kotak untuk angka 1, dan satu kotak lagi untuk angka 3."
Itu keliru. Kotaknya cukup satu saja! Isi lama dikeluarkan, isi baru dimasukkan. Nama kotaknya tidak pernah berganti. Satu papan "Skor" bisa dipakai dari awal permainan sampai selesai. Justru itulah gunanya variabel: satu kotak, dipakai berulang-ulang.
:::

## Ke Mana Ilmu Ini Membawamu?

Kamu baru saja menguasai satu ide besar. Di sekolah, ide ini termasuk standar belajar AP-K2-2. Nanti di "Variabel (K-5)", kamu akan memberi nama kotak-kotakmu sendiri dan menyimpan angka serta kata di dalam program sungguhan. Lalu di "Variabel (K-8)", kotak-kotak itu akan bekerja sama untuk membuat game dan program yang lebih pintar. Semuanya tumbuh dari ide sederhana hari ini: kotak bernama yang isinya bisa berganti.

::: check
Q: Isi papan "Skor" sekarang 3. Lalu satu bola masuk lagi. Apa yang dilakukan pada papan?
A: Angka 3 dihapus, lalu ditulis angka 4. Papannya tetap papan "Skor" yang sama, tidak diganti.
Q: Mengapa kita tidak membuat papan baru setiap kali skor berubah?
A: Karena satu kotak bernama bisa dipakai terus-menerus. Kita cukup mengganti isinya. Itulah kehebatan variabel.
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
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_reading_intro_en_v2', 'k5_computing_systems_devices', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Hardware and Software: The Team Inside Your Computer', 'You press one button, and a game character leaps over a pit of lava. In that split second, a whole team inside your computer sprang into action. Once you know who is on that team, every device you use — tablets, laptops, game consoles — stops being a mystery box.

## The Big Idea: Parts Plus Instructions

Every computer is made of two kinds of stuff.

**Hardware** is every part you could touch. Some hardware is easy to spot: the keyboard, the mouse, the touch screen, the speakers. Some hardware hides inside the case: the **processor**, a chip that works like the computer''s brain, and the **memory**, chips that work like a notepad for remembering things.

**Software** is the stuff you cannot touch: apps, games, and programs. A program is really one thing — a very long, very exact **instruction list**. It tells the hardware what to do, step by step, like "when this key is pressed, do that."

Here is the teamwork rule to remember:

- Hardware **without** software just sits there, like a puppet with nobody holding the strings.
- Software **without** hardware cannot do anything, like a recipe with no kitchen to cook in.
- **Together**, they run every app you have ever used.

## Follow One Jump Through the Machine

Trace what happens when you press the space bar to make a game character jump:

1. Your finger presses the space bar. The keyboard is hardware — it senses the press and sends a signal into the computer.
2. The signal reaches the processor. The processor checks the game''s instruction list, which is software.
3. One instruction says: "When the space bar is pressed, make the character jump and play a boing sound."
4. The processor follows that instruction and figures out the new picture and the new sound.
5. The screen (hardware) shows the character in the air, and the speakers (hardware) play the boing.

All of that happens faster than you can blink — and every single step needed both a part and an instruction.

::: check
Q: Your tablet''s screen and the drawing game running on it — which one is hardware and which one is software?
A: The screen is hardware because it is a part you could touch. The drawing game is software because it is an instruction list, not a part.
Q: In the jump example, what job did the processor do?
A: It read the game''s instruction for the space bar and followed it, then told the screen and speakers what to show and play.
:::

Ready to zoom in even closer? The next reading follows a single tap through a virtual pet app, one tiny step at a time.', NULL, NULL, 5, 0.3, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_diagram_en_v2', 'k5_computing_systems_devices', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Journey of a Button Press', 'Every press, tap, or click takes the same journey through a computer. This map shows the whole trip in one picture.

```
      YOU  (a press, a tap, or a click)
      |
      v
+-----------+    +----------------+    +------------+
|   INPUT   |    |   PROCESSOR    |    |   OUTPUT   |
| keyboard  |--->| the "brain"    |--->| screen     |
| mouse     |    | follows steps  |    | speakers   |
+-----------+    +-------+--------+    +------------+
                         ^
                         |
                         v
                 +-------+--------+
                 |     MEMORY     |
                 | holds program  |
                 | and app data   |
                 +----------------+
```

**Legend**

- Boxes = hardware, real parts you could touch
- `--->` = a signal traveling from one part to the next
- `|` and `v` under YOU = your action entering the computer
- The up-and-down arrow (`^` over `v`) = the processor and memory trade information both ways: instructions come up, new facts get saved down
- MEMORY = the chips holding the software (the instruction list) and the app''s facts, like scores

**How to read the map**

1. Start at YOU. Every journey begins with a press, a tap, or a click.
2. The INPUT part senses your action and fires a signal to the PROCESSOR.
3. The PROCESSOR pulls the program''s instruction list up from MEMORY and follows it, step by step.
4. If the program needs to remember something new — a score, a drawing — the processor saves it back down into MEMORY.
5. The PROCESSOR sends commands to the OUTPUT parts, and the screen or speakers show you the result.

::: tip
Next time a device acts up, walk this map like a detective. Nothing happens when you press? Suspect the INPUT. Sound plays but the picture is frozen? Suspect the path to the screen. And restarting helps so often because it loads the software fresh from memory and lets the instructions start over cleanly.
:::', NULL, NULL, 3, 0.4, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_audio_en_v2', 'k5_computing_systems_devices', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Team Inside Every Device', NULL, NULL, 'Have you ever wondered what is really happening inside a computer while you use it? Every computer, tablet, and game console is two things working as a team. The first is hardware. Hardware means the parts you could actually touch. That includes the screen, the keyboard, the speakers, and the tiny chips hidden inside, like the processor, which acts like the computer''s brain, and the memory, which acts like its notepad. The second is software. Software means the programs, apps, and games. You cannot touch software, because it is not a part. It is a long, exact list of instructions that tells the hardware what to do, one step at a time.

Here is the big idea. Neither one works alone. Hardware without software just sits there quietly, like a puppet with nobody holding the strings. Software without hardware cannot do anything at all, like a recipe with no kitchen to cook in. But together, they can run any app ever made.

Let''s follow one example from start to finish. Imagine you say to a smart speaker, play my favorite song. First, the microphone hears your voice. The microphone is hardware, and its job is to sense the world and turn your voice into a signal. Next, the processor takes that signal and follows the software''s instructions to figure out which words you said. Then the instructions say to find that song, which is stored in the memory chips. Finally, the processor sends the music to the speaker, and your song fills the room. The microphone, the processor, the memory, and the speaker were the hardware team. The instructions telling them what to do at every step were the software.

So here is your recap question. When you tap a drawing app and a red line appears on the screen, which parts are hardware, and which part is software? Think about it for a second. Here is the answer. The touch screen that felt your finger and the screen that shows the line are hardware, because they are parts you could touch. The drawing app is software, because it is the instruction list that said, when a finger moves, draw a red line. Hardware and software. A team inside every device you use.', 4, 0.45, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_reading_deep_en_v2', 'k5_computing_systems_devices', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Follow the Signal: How One Tap Becomes Action', 'Quick recap: hardware is the touchable parts of a computer, and software is the instruction list that tells those parts what to do. A running program is like a relay race — a signal passes from part to part, and instructions decide every move.

## Worked Example: Feeding a Virtual Pet

Imagine a tablet app with a fluffy virtual pet named Biscuit. On the screen there is a button shaped like a food bowl. Here is what happens, in slow motion, when you tap it:

1. **Your finger taps the glass.** The touch screen is an input — a hardware part whose whole job is sensing the world. It notices exactly where your finger landed.
2. **The touch screen sends a signal to the processor.** The signal basically says, "A tap happened at this exact spot."
3. **The processor opens the app''s instruction list.** The pet app is software. One instruction says: "If the tap is on the food bowl button, feed the pet."
4. **The instructions tell the processor to update memory.** Biscuit has a "fullness number" stored in memory. The instruction says to add one to it. Memory is hardware — chips that hold the program and its facts.
5. **The instructions tell the outputs what to do.** The processor sends a new picture to the screen — Biscuit munching happily — and a crunch sound to the speaker.

| Part | Hardware or software? | Job in the story |
| --- | --- | --- |
| Touch screen | Hardware | Senses the tap |
| Pet app | Software | Decides what the tap means |
| Processor | Hardware | Follows the instructions |
| Memory | Hardware | Remembers Biscuit''s fullness number |
| Screen and speaker | Hardware | Show and play the result |

One tap, five steps — and every step was hardware and software working together. Take away the app, and tapping the glass does nothing. Take away the touch screen, and the app never finds out you tapped at all.

## A Trap to Avoid

::: misconception
The wrong belief: "The screen makes the game happen. The pictures come from the screen, so the screen must be creating the game."
The truth: the screen is only an output. It shows whatever it is told to show, like a puppet''s face. The game is actually created by the processor following the app''s instruction list, using memory to keep track of everything. The screen never decides anything — it just displays the result of the software''s instructions.
:::

## Where This Leads

Describing how hardware and software work together as one system is exactly what the computer science standard CSTA 1B-CS-01 asks students to do — and you just did it. What you learn here transfers straight into real life: whenever a device misbehaves, you can now ask the smartest first question in tech — "Is this a hardware problem or a software problem?" And when you start writing programs of your own someday, you will already know who follows your instructions (the processor) and how your written steps turn into pictures and sounds.

::: check
Q: Your game controller works perfectly in every game except one, where the buttons do nothing. Is the problem more likely hardware or software, and why?
A: More likely software. The controller proves its hardware works in the other games, so the broken game''s instruction list is the more likely problem.
Q: Put these steps in the correct order for feeding Biscuit: the app''s instruction runs; the screen shows Biscuit eating; your finger taps the bowl button; the touch screen signals the processor.
A: Your finger taps the bowl button, then the touch screen signals the processor, then the app''s instruction runs, then the screen shows Biscuit eating.
:::', NULL, NULL, 8, 0.6, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_reading_intro_id_v2', 'k5_computing_systems_devices', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Hardware dan Software: Tim Hebat di Dalam Komputermu', 'Pernahkah kamu menggambar di tablet, lalu garis warna-warni muncul persis di tempat jarimu bergerak? Rasanya seperti sulap, padahal di dalam tablet tidak ada penyihir sama sekali. Yang ada hanyalah kerja sama rapi antara bagian-bagian mesin dan sebuah daftar instruksi — dan hari ini kamu akan tahu rahasianya.

## Ide Besar: Tubuh Mesin dan Daftar Instruksinya

Setiap komputer, tablet, atau konsol game punya dua pemain utama:

- **Perangkat keras (hardware)**: semua bagian yang bisa kamu sentuh atau lihat, seperti layar, keyboard, speaker, dan prosesor (cip kecil yang menjadi "otak" mesin).
- **Perangkat lunak (software)**: program, yaitu daftar instruksi yang memberi tahu perangkat keras apa yang harus dilakukan. Software tidak bisa disentuh — ia seperti resep kue, bukan panci dan ovennya.

Bayangkan robot mainan. Tubuh robot adalah hardware-nya. Tetapi robot tidak akan bergerak sebelum ada daftar instruksi seperti "maju tiga langkah, lalu belok kanan". Daftar instruksi itulah software-nya. Keduanya saling membutuhkan: hardware tanpa software hanya diam membisu, dan software tanpa hardware tidak punya tubuh untuk bekerja. Inilah inti yang kamu kuasai di capaian SK-K5-1.

Kerja sama itu selalu mengikuti tiga langkah besar:

1. **Masukan (input)** — kamu memberi perintah, misalnya menyentuh layar atau menekan tombol.
2. **Proses** — prosesor membaca instruksi dari software dan memutuskan apa yang harus terjadi.
3. **Keluaran (output)** — hasilnya ditunjukkan kepadamu lewat layar, speaker, atau lampu.

## Contoh: Menggambar Garis di Tablet

Ayo ikuti perjalanan satu sentuhan jari:

1. Jarimu menyentuh layar. Layar sentuh adalah alat masukan; ia mengirim pesan ke prosesor: "Ada sentuhan di titik ini!"
2. Prosesor membuka daftar instruksi milik aplikasi gambar. Salah satu instruksinya berbunyi: "Jika ada sentuhan, gambarlah garis di titik itu dengan warna yang sedang dipilih."
3. Prosesor mengikuti instruksi itu, lalu menyuruh layar (alat keluaran): "Tampilkan garis biru di sini!"
4. Garis biru muncul — semuanya terjadi lebih cepat daripada satu kedipan mata.

::: check
Q: Manakah yang termasuk perangkat keras: aplikasi gambar atau speaker?
A: Speaker, karena speaker adalah benda yang bisa disentuh. Aplikasi gambar adalah perangkat lunak, yaitu daftar instruksi.
Q: Apa tugas perangkat lunak saat kamu menggambar di tablet?
A: Memberi daftar instruksi kepada prosesor, misalnya "jika ada sentuhan, gambarlah garis di titik itu", supaya perangkat keras tahu apa yang harus dilakukan.
:::

Di bacaan berikutnya, kita akan membedah perjalanan sebuah perintah langkah demi langkah — dari tombol yang kamu tekan sampai hasilnya tersimpan rapi di dalam komputer.', NULL, NULL, 5, 0.3, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_diagram_id_v2', 'k5_computing_systems_devices', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Jalur Perintah di Dalam Komputer', 'Setiap perintah yang kamu berikan kepada komputer menempuh jalur yang sama: masuk, diproses, lalu keluar sebagai hasil yang bisa kamu lihat atau dengar. Diagram ini memperlihatkan jalur itu beserta para pemainnya.

```
              [ KAMU ]
                 |
                 v
      +--------------------+
      |    ALAT MASUKAN    |
      |  keyboard, mouse,  |
      |    layar sentuh    |
      +--------------------+
                 |
                 v
+--------+   +----------+   +-----------------+
| MEMORI |<->| PROSESOR |<==| PERANGKAT LUNAK |
+--------+   +----------+   +-----------------+
                 |
                 v
      +--------------------+
      |   ALAT KELUARAN    |
      |   layar, speaker   |
      +--------------------+
                 |
                 v
              [ KAMU ]
```

Legend:

- **[ KAMU ]** : kamu, sang pengguna komputer
- **Kotak** : satu komponen; alat masukan, prosesor, memori, dan alat keluaran adalah perangkat keras
- **| dan v** : arah perjalanan perintah dan data
- **<->** : prosesor dan memori bertukar data bolak-balik
- **<==** : perangkat lunak menyodorkan daftar instruksi kepada prosesor

Cara membaca diagram ini, dengan contoh memutar lagu:

1. Mulai dari [ KAMU ] di bagian atas: kamu menekan tombol "putar" lagu favoritmu di layar sentuh.
2. Layar sentuh, si alat masukan, mengirim sinyal ke bawah menuju prosesor.
3. Lewat panah <==, prosesor membaca instruksi aplikasi pemutar musik: "jika tombol putar ditekan, bunyikan lagu".
4. Lewat panah <->, prosesor mengambil data lagu dan mencatat bagian yang sedang diputar di memori.
5. Prosesor menyuruh alat keluaran bekerja: speaker mengeluarkan musik.
6. Panah terakhir kembali ke [ KAMU ]: kamu mendengar lagunya!

::: tip
Mainkan "tebak jalur" pada perangkat apa pun yang kamu pakai hari ini: tentukan mana alat masukannya, apa keluarannya, dan instruksi apa kira-kira yang sedang dijalankan prosesornya. Contoh: pada kamera, tombol jepret adalah masukan dan foto yang muncul adalah keluaran.
:::', NULL, NULL, 3, 0.4, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_audio_id_v2', 'k5_computing_systems_devices', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Rahasia Tombol Lompat: Cara Komputer Menjalankan Program', NULL, NULL, 'Hai, teman belajar! Hari ini kita akan mengobrol tentang rahasia di dalam komputer, tablet, dan konsol game: bagaimana mesin-mesin itu bisa menjalankan program.

Setiap komputer punya dua pemain utama. Pemain pertama adalah perangkat keras, atau hardware. Ini semua bagian yang bisa kamu pegang: tombol, layar, speaker, dan sebuah cip kecil bernama prosesor yang menjadi otak mesin. Pemain kedua adalah perangkat lunak, atau software. Software tidak bisa dipegang, karena ia berupa daftar instruksi. Bayangkan seperti resep kue: resep memberi tahu langkah-langkah membuat kue, tetapi resep itu sendiri bukan oven dan bukan adonannya.

Nah, kedua pemain ini saling membutuhkan. Hardware tanpa software hanya diam, seperti robot mainan yang tidak diberi perintah apa pun. Sebaliknya, software tanpa hardware juga tidak bisa berbuat apa-apa, karena tidak punya tubuh untuk bekerja.

Ayo kita buktikan dengan sebuah contoh. Bayangkan kamu sedang bermain game petualangan memakai gamepad, lalu menekan tombol lompat. Pertama, tombol itu mengirim sinyal listrik ke prosesor. Sinyal itu disebut masukan, atau input. Kedua, prosesor membuka daftar instruksi milik game dan menemukan perintah yang berbunyi: jika tombol lompat ditekan, gerakkan karakter ke atas. Ketiga, prosesor menyuruh layar menggambar karakter yang sedang melompat, dan menyuruh speaker membunyikan suara hup. Itulah keluaran, atau output. Semua langkah tadi terjadi lebih cepat dari satu kedipan mata, sehingga rasanya karaktermu melompat tepat saat jempolmu menekan tombol.

Jadi, ingat pola ini baik-baik: masukan, proses, keluaran. Kamu memberi perintah lewat alat masukan, prosesor mengikuti instruksi dari software, lalu hasilnya keluar lewat layar atau speaker.

Sebelum kita selesai, coba jawab pertanyaan ini. Saat kamu menekan tombol lompat dan karaktermu melompat, siapa yang memberi tahu prosesor apa yang harus dilakukan: perangkat keras atau perangkat lunak?

Jawabannya adalah perangkat lunak. Prosesor memang yang bekerja, tetapi perangkat lunaklah yang berisi daftar instruksinya. Prosesor hanya mengikuti instruksi itu satu per satu, dengan kecepatan luar biasa. Keren, kan? Sampai jumpa di latihan berikutnya!', 4, 0.45, '["k2_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_computing_systems_devices_reading_deep_id_v2', 'k5_computing_systems_devices', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Perjalanan Satu Perintah: Dari Tombol sampai Tersimpan', 'Ingat ide besarnya: perangkat keras adalah tubuh mesin yang bisa disentuh, dan perangkat lunak adalah daftar instruksi yang memberi tahu tubuh itu apa yang harus dilakukan. Sekarang kita ikuti satu perintah dari awal sampai akhir.

## Contoh Lengkap: Mengetik Namamu di Laptop

Bayangkan kamu membuka aplikasi tulis di laptop, lalu mengetik nama "BIMA". Inilah yang terjadi di balik layar:

1. **Kamu menekan tombol B.** Keyboard adalah alat masukan. Di bawah tombol ada saklar kecil yang mengirim sinyal listrik ke prosesor: "Tombol B baru saja ditekan!"
2. **Prosesor bertanya pada software.** Prosesor tidak tahu sendiri apa arti sinyal itu. Ia membuka daftar instruksi aplikasi tulis dan menemukan instruksi: "Jika sebuah tombol huruf ditekan, tampilkan huruf itu di posisi kursor."
3. **Memori mencatat.** Huruf B disimpan sementara di memori — semacam papan tulis kecil di dalam komputer — supaya komputer ingat apa saja yang sudah kamu ketik.
4. **Layar menampilkan hasilnya.** Prosesor menyuruh layar, si alat keluaran, menggambar huruf B. Kamu melihatnya muncul seketika.
5. **Langkah 1 sampai 4 terulang** untuk huruf I, M, dan A. Setiap huruf menempuh perjalanan yang sama: masukan, proses, keluaran.
6. **Kamu menekan Simpan.** Software memberi instruksi baru: "Pindahkan tulisan dari memori ke penyimpanan." Penyimpanan itu seperti lemari arsip — isinya tidak hilang walau laptop dimatikan.

Perhatikan: keyboard, prosesor, memori, dan layar (semuanya perangkat keras) tidak pernah bekerja sendiri-sendiri. Software-lah yang mengatur mereka, seperti pelatih yang mengatur tim sepak bola.

## Salah Paham yang Sering Terjadi

::: misconception
Banyak orang mengira komputer itu pintar dan bisa berpikir sendiri seperti manusia. Padahal komputer sama sekali tidak bisa berpikir sendiri. Prosesor hanya menjalankan daftar instruksi yang ditulis manusia di dalam software, satu per satu, dengan sangat cepat. Kalau instruksinya keliru, komputer akan patuh melakukan hal yang keliru juga. Jadi yang "pintar" bukan mesinnya, melainkan orang yang menyusun instruksinya.
:::

Ada juga yang mengira aplikasi "tinggal di dalam layar". Layar hanyalah alat keluaran — tugasnya cuma menampilkan. Yang benar-benar menjalankan aplikasi adalah prosesor, dibantu memori.

## Ke Mana Pengetahuan Ini Membawamu

Pola masukan-proses-keluaran yang kamu kuasai di sini akan terus kamu pakai ke depannya. Saat nanti kamu mulai menyusun program sendiri, sebenarnya kamu sedang menulis daftar instruksi untuk prosesor — persis seperti instruksi milik aplikasi tulis tadi. Pemahaman ini juga membantumu menjadi detektif perangkat: saat sesuatu tidak bekerja, kamu bisa menebak apakah tubuhnya (hardware) yang rusak atau daftar instruksinya (software) yang keliru.

::: check
Q: Kamu menekan tombol volume dan suara laptop menjadi lebih keras. Urutkan perjalanan perintah itu dari awal sampai akhir.
A: Tombol volume (masukan) mengirim sinyal ke prosesor; prosesor mengikuti instruksi software "jika tombol volume ditekan, keraskan suara"; lalu speaker (keluaran) mengeluarkan suara yang lebih keras.
Q: Layar tablet Rara retak dan tidak menyala, tetapi musik masih terdengar dari speaker. Bagian mana yang bermasalah: perangkat keras atau perangkat lunak? Jelaskan.
A: Perangkat keras, tepatnya layar sebagai alat keluaran. Perangkat lunaknya masih berjalan baik — buktinya prosesor tetap menjalankan instruksi pemutar musik dan speaker tetap bersuara.
:::', NULL, NULL, 8, 0.6, '["k2_computing_systems_devices"]'::jsonb);
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
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_reading_intro_en_v2', 'k5_culture', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'How Computers Change Our World', 'Think about this morning. Did anyone in your house check the weather on a phone, order groceries with an app, or play a song by asking a speaker? Computers quietly shape your day before you even get to school. Learning to spot *how* they change life around you is like getting x-ray vision for the modern world.

## The Big Idea: Computing Makes Ripples

Drop a pebble into a puddle and rings spread out in every direction. A new computing tool works the same way. When lots of people start using it, ripples spread through three big parts of life:

- **Society** — how people live, help each other, and get things done
- **Culture** — the habits, traditions, games, and ways of talking that groups share
- **Economy** — money, jobs, and the things people buy and sell

Your job as a ripple-spotter is to follow the rings and notice *all* of them — the happy ripples and the tricky ones. (Teachers call this skill CSTA 1B-IC-18, but you can just call it ripple-spotting.)

### Follow along: the lunch app

Imagine your school gets a lunch app. Instead of telling a worker your order in a noisy line, every student taps a meal choice on a tablet in the morning. Trace the ripples with me:

1. **Society ripple:** Lunch lines get shorter and calmer, and shy kids don''t have to shout their order over the crowd.
2. **Culture ripple:** A new habit is born. "Tap your taco!" becomes part of the morning routine, right next to announcements — a tiny new school tradition.
3. **Economy ripple:** The kitchen knows exactly how many tacos to cook, so less food gets thrown away and the school saves money.
4. **Tricky ripple:** The worker who used to write orders on paper needs a new job to do. The change helped many people but made one person''s day harder.

One small app, four ripples — and only a careful spotter catches the fourth one.

::: check
Q: What are the three big parts of life that a new computing tool can change?
A: Society (how people live and get things done), culture (shared habits and traditions), and the economy (money, jobs, buying, and selling).
Q: In the lunch app story, which ripple was tricky instead of happy?
A: The worker who used to take paper orders needed a different job, so the change was hard for that person even though it helped others.
:::

Ready to go deeper? Next, you''ll follow every ripple from one world-famous game and learn the questions expert ripple-spotters always ask.', NULL, NULL, 5, 0.3, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_diagram_en_v2', 'k5_culture', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Ripple Map of a New App', 'A ripple map shows how one computing tool sends changes through three parts of life. This one follows a website where animal shelters post photos of pets that need homes.

```
             +--------------------------+
             |    NEW COMPUTING TOOL    |
             |  (pet-adoption website)  |
             +------------+-------------+
                          |
                  ripples | spread out
                          v
   +-----------+   +-----------+   +-----------+
   |  SOCIETY  |   |  CULTURE  |   |  ECONOMY  |
   | how we    |   | habits we |   | money and |
   | live      |   | share     |   | jobs      |
   +-----+-----+   +-----+-----+   +-----+-----+
         |               |               |
         v               v               v
    more pets      "meet pets      shelter needs
    find homes     online first"   fewer flyers;
    faster         is the new      web helpers
                   family habit    get hired
         |               |               |
         +-------------->+<--------------+
                         v
             ASK: Who is helped?
             ASK: Who is left out?
```

**Legend**
- Boxes with CAPITAL labels = the new tool (top) and the three parts of life it changes
- Lines and "v" arrows = "this leads to..." (follow them downward)
- Words under each box = the real-life change, called a ripple
- ASK lines = the two questions a ripple-spotter always asks at the end

**How to read it**
1. Start at the top box: the new computing tool — here, a pet-adoption website.
2. Follow the arrow down and split three ways: every big tool ripples into society, culture, and the economy.
3. Read the society ripple: more pets find homes faster because families can search from their couch.
4. Read the culture ripple: "meet pets online first" becomes the new family habit before visiting a shelter.
5. Read the economy ripple: shelters print fewer flyers and hire web helpers instead — money and jobs shift.
6. Finish at the ASK lines: Who is helped? Pets, families, and web helpers. Who is left out? Families without internet, and maybe the flyer printer''s business.

::: tip
Try this today: pick any app someone in your family uses and draw your own ripple map for it — one top box, three arrows down, and the two ASK questions at the bottom. If you can fill in all three ripples, you''re officially a ripple-spotter.
:::', NULL, NULL, 3, 0.4, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_audio_en_v2', 'k5_culture', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Tiny Tech, Big Ripples', NULL, NULL, 'Have you ever waved goodbye to someone through a screen? Today we are going to talk about something amazing: how computers do not just change what is on a screen. They change the whole world around us.

Here is the big idea. When lots of people start using a new computing tool, it is like dropping a pebble into a puddle. Ripples spread out in three directions. The first ripple is society, which means how people live and help each other. The second is culture, which means the habits, traditions, and ways of talking that groups of people share. The third is the economy, which means money, jobs, and the things people buy and sell.

Let''s follow one example together. Think about video calls. Imagine your cousin moves far away, to another country. A long time ago, your family would have waited weeks for letters. Now you can see your cousin''s face tonight. That is a society ripple: families stay close even across oceans. Video calls changed culture, too. In many homes, calling Grandma every Sunday became a brand-new tradition, and people even invented new manners, like waving at the camera to say goodbye. And video calls changed the economy. Companies hired thousands of workers to build calling apps, and many grown-ups can now do their jobs from home instead of driving to an office.

But careful listeners catch the tricky ripples too. A family without internet cannot join the call. And if screens replace every real visit, someone might feel a little lonely. The same tool that helps millions of people can still leave some people out. That is why smart ripple-spotters always ask two questions: who does this tool help, and who might it leave out?

Here is your recap question. When a new computing tool becomes popular, what are the three parts of life it can change? Take a second and say them out loud.

The answer: society, which is how people live together; culture, which is the habits and traditions we share; and the economy, which is money and jobs. And do not forget the bonus move: always ask who is helped and who is left out. Spot those ripples, and you will understand the world better than most grown-ups do.', 4, 0.45, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_reading_deep_en_v2', 'k5_culture', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'One Game, a World of Ripples', 'Quick recap: a new computing tool is like a pebble in a puddle. It sends ripples through society, culture, and the economy — and a good ripple-spotter finds the helpful ripples *and* the tricky ones.

## Worked example: tracing every ripple from one game

Meet **Blockville**, a made-up (but very familiar-sounding) online building game where players create castles, zoos, and roller coasters together. Let''s analyze it step by step, like detectives.

**Step 1 — Drop the pebble.** Blockville launches. It''s free, it''s fun, and soon millions of kids around the world are building together.

**Step 2 — Trace the society ripples.** Kids team up with players from other countries. A girl in Brazil and a boy in Japan build a dragon zoo together without ever meeting. Cousins who live far apart now hang out every weekend inside the game.

**Step 3 — Trace the culture ripples.** Players invent victory dances that kids copy at recess. New words like "spawn" and "gg" sneak into playground talk. Birthday parties get Blockville cakes. The game starts shaping what kids draw, say, and play — that''s culture changing.

**Step 4 — Trace the economy ripples.** The Blockville company hires artists, coders, testers, and helpers — brand-new jobs. Players spend real money on costumes for their characters. Toy stores start selling Blockville plushies.

**Step 5 — Hunt for tricky ripples.** Some players stay up too late building. Kids without internet at home feel left out of recess conversations. Some families argue about money spent on costumes.

**Step 6 — Sort what you found.**

| Ripple | Part of life | Helpful or tricky? |
| Friends across the world | Society | Helpful |
| New playground words and dances | Culture | Helpful |
| New jobs at the game company | Economy | Helpful |
| Kids without internet feel left out | Society | Tricky |
| Arguments over costume money | Economy | Tricky |

That''s real analysis: one game, many ripples, sorted and understood.

## A common misconception

::: misconception
**Wrong idea:** "A popular new technology makes life better for everyone."
**The truth:** The same change can help one person and make things harder for another — at the very same time. Blockville gave artists new jobs *and* left out kids without internet. That''s why expert ripple-spotters always ask three questions: Who is helped? Who has it harder now? Who is left out completely?
:::

## Where this leads

Ripple-spotting doesn''t stay in computer class — it travels with you everywhere. When you''re older and someone shows you a shiny new app, robot, or gadget, you''ll automatically ask who it helps, who it leaves out, and how it might change jobs and habits. That''s the same thinking inventors, city planners, and lawmakers use when they decide how technology should fit into the world. You''re practicing their moves right now.

::: check
Q: A homework-helper app becomes popular at your school. Name one possible society ripple, one culture ripple, and one economy ripple.
A: Society: students who get stuck can find help at home. Culture: "ask the app first" might become a new homework habit. Economy: the app company earns money and hires workers — and maybe fewer families pay human tutors.
Q: Why do ripple-spotters ask "Who is left out?" even when a tool seems great?
A: Because ripples never reach everyone equally. A student without a device or internet can''t use the tool at all, and noticing that helps people make fairer choices about technology.
:::', NULL, NULL, 8, 0.6, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_reading_intro_id_v2', 'k5_culture', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Komputer Mengubah Dunia di Sekitar Kita', 'Pernahkah kamu melihat ayah atau ibu memesan makanan lewat HP, lalu tidak lama kemudian kakak pengantar datang membawa pesanan hangat? Itu bukan sulap — di baliknya ada komputer dan program yang bekerja sama. Diam-diam, teknologi komputer mengubah cara kita makan, bermain, belajar, bahkan cara keluarga kita mencari uang.

## Ide Besar: Teknologi Selalu Membawa Perubahan

Setiap teknologi komputer — aplikasi, game, atau situs web — membawa perubahan pada tiga bidang kehidupan:

- **Masyarakat**: cara orang hidup bersama dan saling membantu.
- **Budaya**: kebiasaan yang kita lakukan sehari-hari.
- **Ekonomi**: cara orang bekerja, berjualan, dan menggunakan uang.

Perubahan itu bisa baik dan kurang baik sekaligus, seperti dua sisi uang logam. Tugas kita adalah **menganalisis**: memeriksa dengan teliti apa yang berubah, siapa yang terpengaruh, dan apa untung-ruginya. Kemampuan menganalisis dampak seperti ini adalah bagian dari capaian belajar DSI-K5-1.

Kamu bisa memakai daftar instruksi sederhana ini:

1. Sebutkan teknologinya.
2. Tanyakan: apa yang berubah?
3. Tanyakan: siapa saja yang terpengaruh?
4. Tuliskan dampak baik dan dampak kurang baiknya.

## Contoh: Warung Bu Sari Masuk Aplikasi

Ayo kita coba daftar instruksi itu pada satu cerita.

Bu Sari punya warung nasi kecil dekat sekolah. Bulan lalu, warungnya mulai menerima pesanan lewat aplikasi pesan-antar makanan.

1. **Teknologinya**: aplikasi pesan-antar makanan di HP.
2. **Apa yang berubah?** Pembeli tidak harus datang ke warung. Mereka memesan lewat HP, lalu kakak pengantar membawakan makanannya.
3. **Siapa yang terpengaruh?** Bu Sari, para pengantar, pembeli, dan warung-warung lain di sekitarnya.
4. **Dampak baik dan kurang baik**:
   - Baik: dagangan Bu Sari laku lebih banyak (ekonomi), pengantar mendapat pekerjaan baru (ekonomi), dan pembeli yang sibuk tetap bisa makan masakan hangat (masyarakat).
   - Kurang baik: warung lain yang belum memakai aplikasi bisa menjadi lebih sepi, dan pembeli jadi jarang mengobrol langsung dengan Bu Sari (budaya).

Lihat, satu aplikasi saja bisa mengubah banyak hal sekaligus!

::: check
Q: Apa saja tiga bidang kehidupan yang berubah karena teknologi komputer?
A: Masyarakat (cara orang hidup bersama), budaya (kebiasaan sehari-hari), dan ekonomi (cara orang bekerja dan menggunakan uang).
Q: Dalam cerita warung Bu Sari, siapa yang terkena dampak kurang baik?
A: Warung lain yang belum memakai aplikasi bisa menjadi lebih sepi pembelinya.
:::

Di bacaan berikutnya, kita akan menganalisis sebuah game online langkah demi langkah dan membongkar satu salah paham yang sering membuat orang keliru.', NULL, NULL, 5, 0.3, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_diagram_id_v2', 'k5_culture', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Satu Teknologi, Tiga Dampak', 'Satu teknologi komputer bisa memberi dampak ke tiga bidang kehidupan sekaligus. Diagram ini menunjukkan contohnya: aplikasi peta digital yang membantu orang mencari jalan.

```
           +------------------------+
           |   TEKNOLOGI KOMPUTER   |
           |    (aplikasi peta)     |
           +-----------+------------+
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
+-------------+ +-------------+ +-------------+
| MASYARAKAT  | |   BUDAYA    | |   EKONOMI   |
+-------------+ +-------------+ +-------------+
| + jarang    | | + kebiasaan | | + sopir     |
|   tersesat  | |   baru: cek | |   ojek dapat|
| - jarang    | |   rute dulu | |   penumpang |
|   bertanya  | | - peta      | | - penjual   |
|   arah ke   | |   kertas    | |   peta      |
|   warga     | |   terlupakan| |   kertas    |
|             | |             | |   jadi sepi |
+-------------+ +-------------+ +-------------+
```

**Legenda**

- Kotak paling atas: teknologi yang sedang kita analisis.
- Garis dan panah (| dan v): artinya "memberi dampak ke".
- Tiga kotak bawah: bidang masyarakat, budaya, dan ekonomi.
- Tanda +: dampak baik.
- Tanda -: dampak kurang baik.

**Cara membaca diagram**

1. Mulai dari kotak paling atas: teknologinya adalah aplikasi peta digital.
2. Ikuti panah ke bawah — dampaknya menyebar ke tiga kotak sekaligus.
3. Baca kotak MASYARAKAT: orang jadi jarang tersesat (+), tetapi juga jarang bertanya arah ke warga (-), jadi obrolan di jalan berkurang.
4. Baca kotak BUDAYA: muncul kebiasaan baru mengecek rute sebelum pergi (+), tetapi peta kertas mulai terlupakan (-).
5. Baca kotak EKONOMI: sopir ojek lebih mudah menemukan penumpang (+), tetapi penjual peta kertas menjadi sepi pembeli (-).

::: tip
Saat menganalisis teknologi apa pun, gambarlah tiga kotak seperti ini di bukumu, lalu isi setiap kotak dengan minimal satu tanda + dan satu tanda -. Kalau ada kotak yang masih kosong, itu tanda kamu perlu berpikir lebih dalam lagi.
:::', NULL, NULL, 3, 0.4, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_audio_id_v2', 'k5_culture', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Bagaimana Komputer Mengubah Kehidupan Kita', NULL, NULL, 'Halo, teman belajar! Hari ini kita mengobrol tentang bagaimana komputer dan teknologi mengubah kehidupan orang-orang di sekitar kita.

Coba pikirkan panggilan video. Dulu, kalau nenek dan kakek tinggal jauh di kampung, kita hanya bisa mendengar suara mereka lewat telepon, atau menunggu liburan panjang untuk bertemu. Sekarang, lewat panggilan video, kita bisa melihat senyum nenek setiap minggu, memamerkan gambar buatan kita, bahkan ikut merayakan ulang tahun dari jauh.

Perubahan seperti ini disebut dampak teknologi. Dampak artinya perubahan yang terjadi karena sesuatu. Teknologi komputer biasanya memberi dampak pada tiga bidang. Pertama, masyarakat, yaitu cara orang hidup bersama dan saling membantu. Keluarga yang berjauhan sekarang tetap bisa merasa dekat. Kedua, budaya, yaitu kebiasaan sehari-hari. Banyak keluarga punya kebiasaan baru, misalnya panggilan video setiap Minggu sore. Ketiga, ekonomi, yaitu cara orang bekerja dan menggunakan uang. Ada orang yang bekerja membuat aplikasinya, dan keluarga membeli paket data supaya bisa terhubung.

Tapi ingat, dampak tidak selalu baik. Panggilan video juga punya sisi kurang baik. Kadang sinyal di kampung lemah, sehingga gambarnya patah-patah. Ada juga keluarga yang belum punya telepon pintar, jadi mereka belum bisa ikut merasakan. Dan kalau kita terlalu asyik menatap layar, kita bisa lupa mengobrol dengan orang yang duduk tepat di sebelah kita.

Karena itu, kamu perlu belajar menganalisis, artinya memeriksa dengan teliti. Caranya seperti daftar instruksi. Satu, sebutkan teknologinya. Dua, tanyakan apa yang berubah. Tiga, tanyakan siapa saja yang terpengaruh. Empat, tuliskan dampak baik dan dampak kurang baiknya. Kalau kamu terbiasa berpikir seperti ini, kamu akan menjadi pengguna teknologi yang bijak, bukan sekadar pengguna yang asyik sendiri.

Sekarang, satu pertanyaan pengingat. Sebutkan tiga bidang kehidupan yang biasanya berubah karena teknologi komputer. Coba jawab dulu di dalam hati.

Jawabannya adalah masyarakat, budaya, dan ekonomi. Masyarakat berarti cara orang hidup bersama, budaya berarti kebiasaan sehari-hari, dan ekonomi berarti cara orang bekerja dan menggunakan uang. Kerja bagus! Sampai jumpa di pelajaran berikutnya.', 4, 0.45, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_culture_reading_deep_id_v2', 'k5_culture', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menganalisis Dampak Teknologi Selangkah demi Selangkah', 'Kamu sudah tahu ide besarnya: teknologi komputer mengubah masyarakat, budaya, dan ekonomi, dan dampaknya bisa baik sekaligus kurang baik. Sekarang kita berlatih menganalisis dengan lebih dalam.

## Contoh Lengkap: Game Online "Kebun Ajaib"

Bayangkan sebuah game online bernama "Kebun Ajaib". Pemain menanam sayur di kebun digital dan bisa berkunjung ke kebun milik teman dari kota lain. Ayo analisis langkah demi langkah.

**Langkah 1 — Sebutkan teknologinya.** Game online yang dimainkan lewat HP atau tablet dan terhubung ke internet.

**Langkah 2 — Apa yang berubah?** Dulu, anak-anak hanya bisa bermain dengan teman yang tinggal dekat. Sekarang, pemain dari Aceh sampai Papua bisa merawat kebun bersama tanpa pernah bertemu.

**Langkah 3 — Siapa saja yang terpengaruh?** Para pemain, keluarga mereka, pembuat game, penjual paket data, dan juga anak-anak yang tidak punya perangkat untuk ikut bermain.

**Langkah 4 — Tuliskan dampaknya.** Supaya rapi, kita susun dalam tabel:

| Bidang | Dampak baik | Dampak kurang baik |
| --- | --- | --- |
| Masyarakat | Punya teman baru dari kota lain | Anak tanpa perangkat merasa tertinggal |
| Budaya | Muncul kebiasaan dan istilah bermain yang baru | Permainan tradisional jadi jarang dimainkan |
| Ekonomi | Pembuat game mendapat pekerjaan | Uang jajan bisa habis untuk membeli item game |

Kesimpulan analisis: "Kebun Ajaib" membawa banyak hal baik, tetapi pemain butuh aturan, misalnya batas waktu bermain dan tetap bermain di luar rumah bersama teman.

## Awas, Salah Paham!

::: misconception
Keliru: "Kalau teknologinya canggih, dampaknya pasti baik untuk semua orang."
Yang benar: dampak teknologi bisa berbeda-beda untuk tiap orang. Contohnya pembayaran dengan kode QR. Pembeli yang punya HP merasa sangat dimudahkan, tetapi penjual keliling yang belum punya HP bisa kehilangan pembeli. Teknologi yang sama bisa membantu satu kelompok dan menyulitkan kelompok lain. Karena itu, penganalisis yang baik selalu bertanya: baik untuk siapa, dan kurang baik untuk siapa?
:::

## Ke Mana Ilmu Ini Membawamu

Kebiasaan bertanya "apa yang berubah, siapa yang terpengaruh, apa untung-ruginya" akan terus kamu pakai seumur hidup. Di jenjang berikutnya, kamu akan memakai cara berpikir yang sama untuk menimbang teknologi yang lebih rumit, seperti media sosial dan kecerdasan buatan. Cara berpikir ini juga berguna hari ini, misalnya saat keluargamu menimbang perlu atau tidaknya memasang aplikasi baru di HP.

::: check
Q: Sekolahmu mengganti pengumuman kertas dengan pesan di grup chat orang tua. Sebutkan satu dampak baik dan satu dampak kurang baiknya.
A: Dampak baik: pengumuman sampai lebih cepat dan tidak mudah hilang. Dampak kurang baik: orang tua yang tidak punya HP atau pulsa bisa ketinggalan informasi penting.
Q: Mengapa teknologi yang sama bisa menguntungkan satu orang tetapi merugikan orang lain?
A: Karena keadaan tiap orang berbeda — ada yang punya perangkat dan sinyal, ada yang tidak; ada yang pekerjaannya terbantu, ada yang pekerjaannya tergeser. Analisis yang baik memeriksa semua kelompok, bukan hanya satu.
:::', NULL, NULL, 8, 0.6, '["k2_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_reading_intro_en_v2', 'k5_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Be a Data Detective: Ask, Collect, Discover', 'Have you ever argued with your friends about which recess game is the most fun, or which flavor of juice most kids actually like? Instead of arguing, you can find out for real. Data — little pieces of information you collect and count — can settle the question.

## The Big Idea: Data Turns Questions into Answers

Data is just information you gather on purpose: answers, counts, checkmarks, tallies. When you collect data, organize it neatly, and look for patterns, you become a **data detective**. Detectives don''t guess — they gather clues and let the clues point to the answer.

Every data investigation follows the same instruction list:

1. Ask a clear question you can count answers for.
2. Collect the data (ask people, watch things, count things).
3. Organize it (tallies, tables, or charts).
4. Look for patterns (what is biggest? smallest? surprising?).
5. Answer your question using what the data shows.

The secret superpower is step 3. A messy pile of answers hides its secrets. But when you line the answers up neatly, the pattern almost jumps out at you.

## Try It: The Great Recess Game Survey

Imagine you want to know: **which recess game do kids in my class like best?**

You ask 10 classmates to pick one game: tag, four square, or soccer. Here is the messy list you write down:

tag, soccer, four square, soccer, soccer, tag, soccer, four square, soccer, tag

Hard to tell who wins, right? Now organize it into a table:

| Game | Votes |
| --- | --- |
| tag | 3 |
| four square | 2 |
| soccer | 5 |

Suddenly the pattern is easy to spot: soccer got the most votes — half the class picked it! You also notice something extra: every game got at least two votes, so no game is unloved. Your data answered the question, and nobody had to argue.

::: check
Q: What should a data detective do first, before collecting anything?
A: Decide on one clear question to answer, so you know exactly what to count.
Q: Why organize data into a tally chart or table instead of leaving it as a messy list?
A: Organized data makes counting and comparing easy, so the pattern jumps out.
:::

There is another layer of detective skill waiting for you — like spotting data traps and proving your fixes worked — so head to the deeper read next.', NULL, NULL, 5, 0.3, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_diagram_en_v2', 'k5_data_collection', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Five Steps of a Data Investigation', 'Every data investigation follows the same path from question to answer. This diagram shows a class using all five steps to pick a class pet.

```
+------------------------+
| 1. ASK A QUESTION      |
| "Which class pet       |
|  should we get?"       |
+-----------+------------+
            |
            v
+------------------------+
| 2. COLLECT DATA        |
|  fish:    / / / / /    |
|  hamster: / / /        |
|  lizard:  / /          |
+-----------+------------+
            |
            v
+------------------------+
| 3. ORGANIZE            |
|  fish ....... 5        |
|  hamster .... 3        |
|  lizard ..... 2        |
+-----------+------------+
            |
            v
+------------------------+
| 4. FIND THE PATTERN    |
|  fish has the most,    |
|  lizard has the least  |
+-----------+------------+
            |
            v
+------------------------+
| 5. ANSWER THE QUESTION |
|  "Let''s get a fish!"   |
+------------------------+
```

Legend:
- A box = one step of the investigation
- The line and the "v" between boxes = "then do this next"
- "/" = one tally mark, meaning one vote
- "...." = dots that line a choice up with its count
- Words in quotes = what the class asks or decides

How to read the diagram:

1. Start at the top box: the class asks one clear, countable question.
2. Follow the arrow down: each student votes, and every vote becomes one "/" tally.
3. In step 3, the tallies become neat counts, lined up so they are easy to compare.
4. In step 4, compare the counts: 5 is the biggest and 2 is the smallest — that is the pattern.
5. The bottom box turns the pattern back into an answer to the original question.

::: tip
If a pattern is hard to see, reorganize! Put the biggest count first, or draw one symbol per vote in a row so the longest row shows the winner at a glance. The same data can hide or shine depending on how you arrange it.
:::', NULL, NULL, 3, 0.4, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_audio_en_v2', 'k5_data_collection', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'How Data Detectives Answer Questions', NULL, NULL, 'Have you ever wondered about something and wished you could know the real answer instead of just guessing? Today I want to teach you how to answer questions like a data detective.

Data is information you collect on purpose. It can be counts, answers to a survey, or checkmarks in a notebook. When you collect data, organize it, and hunt for patterns, questions almost answer themselves.

Every data investigation follows five steps. First, ask a clear question that you can count answers for. Second, collect the data. Third, organize it into tidy groups. Fourth, look for patterns, like which group is the biggest or the smallest. Fifth, use the pattern to answer your question.

Here is an example you could try this week. Suppose you wonder which color of car is the most common on your street. That is your question. To collect data, you watch the street for fifteen minutes, and every time a car passes, you make a mark for its color. Maybe you count nine white cars, six black cars, four red cars, and two green cars. Now organize the counts from biggest to smallest: white, black, red, then green. Time to find the pattern. White has more marks than any other color. So your answer is that white cars are the most common on your street, at least during the time you watched.

Here is one more detective secret: more data makes your answer stronger. If you watched for only one minute, you might see just two cars and get a strange answer. Watching longer, or on a few different days, gives you a fairer picture.

So remember the five steps: ask, collect, organize, find the pattern, and answer.

Now for your recap question. Why do data detectives organize their data into groups instead of leaving it as one long messy list? Take a second to think about it.

Here is the answer. Organized data makes counting and comparing easy, and that is what makes patterns pop out. And when the pattern pops out, your answer is sitting right there waiting for you.', 4, 0.45, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_reading_deep_en_v2', 'k5_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Data Detective Skills: Patterns, Traps, and Proof', 'Quick recap: a data investigation is a five-step instruction list — ask a question, collect data, organize it, find the pattern, and answer. Now let''s use the whole list on a real classroom mystery.

## Worked Example: The Mystery of the Forgotten Homework

Ms. Rivera''s class keeps forgetting homework, and everyone wants to know: **which day of the week is homework forgotten the most?**

**Step 1 — Ask.** The question is clear and countable: "On which weekday do the most students forget their homework?"

**Step 2 — Plan.** Every morning for two whole weeks, the class helper counts how many students forgot, and writes the number next to the day. Same time, same way, every day — that keeps the data fair.

**Step 3 — Collect.** After two weeks, the notebook is full of numbers.

**Step 4 — Organize.** The class adds both weeks together and builds this table:

| Day | Forgotten homework |
| --- | --- |
| Monday | 6 |
| Tuesday | 2 |
| Wednesday | 1 |
| Thursday | 2 |
| Friday | 3 |

**Step 5 — Find the pattern.** Monday''s number is way bigger than the rest. Pattern spotted: homework gets forgotten most right after the weekend.

**Step 6 — Answer and act.** The class decides everyone will pack their school bags on Sunday night. Then comes the best part: they collect data for two more weeks to check whether the plan worked. If Monday drops from 6 to 1, the data proves the fix worked. Data isn''t only for answering questions — it can test whether a fix actually fixed something.

## A Trap to Avoid

::: misconception
Wrong belief: "I asked three friends and they all said pizza, so pizza must be the whole school''s favorite lunch."
The truth: Three people is a very small amount of data, and your friends might all be a lot like you. Small or one-sided data can point to the wrong answer. Ask more people, from different groups, before you trust a pattern — the more fair data you collect, the more trustworthy your answer becomes.
:::

## Where This Leads

You have now reached the top of the data-detective ladder for elementary school — the skill computer scientists describe in the CSTA standard 1B-DA-06: organizing and presenting collected data to highlight relationships and support a claim. What you learn here transfers far beyond this lesson: science fair experiments, keeping fair score in games, graphing in math class, and someday using computers and spreadsheets that organize thousands of data points with the exact same five steps you just practiced.

::: check
Q: Your class counts lost-and-found items on one rainy day and finds mostly umbrellas. Why shouldn''t you announce "students mostly lose umbrellas"?
A: One unusual day is too little data — the rain made umbrellas extra common that day. Counting across many different days would reveal a fairer pattern.
Q: After acting on data, like the Sunday bag-packing plan, why should the class collect data again?
A: The second round of data shows whether the change actually worked. Comparing the before and after numbers turns your fix into something you can prove.
:::', NULL, NULL, 8, 0.6, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_reading_intro_id_v2', 'k5_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Detektif Data: Kumpulkan, Susun, dan Temukan Jawabannya', 'Pernahkah kamu penasaran, hewan peliharaan apa yang paling disukai teman-teman di kelasmu? Kamu bisa menebak-nebak, tapi tebakan sering meleset. Ada cara yang lebih jitu: kumpulkan **data**, lalu biarkan data itu "bercerita" kepadamu.

## Ide Besar: Data Menjawab Pertanyaan

**Data** adalah kumpulan informasi atau fakta, misalnya jawaban teman-temanmu, catatan cuaca, atau skor permainan. Di kelas sebelumnya kamu sudah belajar mengelompokkan dan menghitung benda. Sekarang kita naik satu tingkat: memakai data untuk **menjawab pertanyaan** dan **menemukan pola**. Dalam pelajaran informatika, keterampilan ini termasuk dalam standar AD-K5-1.

Prosesnya seperti pekerjaan detektif, dengan daftar instruksi seperti ini:

1. Mulai dari **pertanyaan** yang jelas.
2. **Kumpulkan** data dengan bertanya atau mengamati.
3. **Susun** data supaya rapi, misalnya dengan tabel turus.
4. **Amati pola**: mana yang paling banyak, paling sedikit, atau hampir sama.
5. **Jawab** pertanyaanmu dengan bukti dari data.

Tanpa langkah menyusun, data hanyalah tumpukan catatan yang membingungkan. Begitu disusun, polanya langsung terlihat!

### Contoh: Hewan Peliharaan Favorit

Bayu ingin tahu: "Hewan peliharaan apa yang paling disukai di kelasku?" Ia bertanya kepada 20 teman satu per satu, lalu mencatat jawaban dengan turus. Satu garis turus (ditulis dengan huruf I) berarti satu teman.

| Hewan | Turus | Jumlah |
| --- | --- | --- |
| Kucing | IIII III | 8 |
| Ikan | IIII I | 6 |
| Burung | IIII | 4 |
| Anjing | II | 2 |

Sebelum menyimpulkan, Bayu memeriksa dulu: 8 + 6 + 4 + 2 = 20. Cocok dengan jumlah teman yang ia tanya, berarti tidak ada jawaban yang hilang. Sekarang polanya terlihat jelas: kucing paling banyak dipilih, anjing paling sedikit. Jadi jawaban Bayu: hewan peliharaan favorit kelasnya adalah kucing — dan itu bukan tebakan, melainkan kesimpulan dari data!

::: check
Q: Mengapa data perlu disusun ke dalam tabel sebelum diamati?
A: Karena data yang rapi membuat pola mudah terlihat, misalnya pilihan mana yang paling banyak dan paling sedikit.
Q: Dari tabel Bayu, pola apa yang bisa kamu temukan?
A: Kucing paling banyak dipilih, anjing paling sedikit, dan jumlah semua turus sama dengan 20 teman yang ditanya.
:::

Di bacaan berikutnya, kita akan menyelidiki satu kasus lengkap selangkah demi selangkah dan membongkar salah paham yang sering terjadi soal data.', NULL, NULL, 5, 0.3, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_diagram_id_v2', 'k5_data_collection', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Perjalanan Data: dari Pertanyaan ke Jawaban', 'Setiap penyelidikan data menempuh jalan yang sama, dari pertanyaan sampai jawaban. Peta di bawah ini menunjukkan lima perhentiannya, dengan contoh survei buah favorit.

```
+--------------+
| 1. TANYA     |  "Apa buah favorit kelas?"
+--------------+
       |
       v
+--------------+
| 2. KUMPULKAN |  tanya teman satu per satu
+--------------+
       |
       v
+--------------+   Mangga : IIII I  (6)
| 3. SUSUN     |   Pisang : IIII    (4)
+--------------+   Jeruk  : II      (2)
       |
       v
+--------------+
| 4. AMATI     |  mana terbanyak? tersedikit?
+--------------+
       |
       v
+--------------+
| 5. JAWAB     |  "Mangga juaranya!"
+--------------+
```

Legend:

- Kotak = satu langkah dalam penyelidikan data
- Panah (v) = urutan langkah, dibaca dari atas ke bawah
- Huruf I = satu turus, artinya satu jawaban dari satu teman
- Tulisan di samping kotak = contoh dari survei buah favorit
- Angka dalam kurung = jumlah turus setelah dihitung

Cara membaca peta ini:

1. Mulai dari kotak paling atas: semuanya berawal dari pertanyaan yang jelas.
2. Ikuti panah ke bawah: data dikumpulkan dengan bertanya kepada setiap teman.
3. Di kotak SUSUN, jawaban yang berantakan diubah menjadi turus yang rapi — di sinilah data mulai "berbicara".
4. Di kotak AMATI, bandingkan jumlahnya: mangga 6, pisang 4, jeruk 2. Polanya terlihat!
5. Kotak terakhir memberikan jawaban berdasarkan bukti: mangga adalah buah favorit kelas.

::: tip
Sebelum pindah dari SUSUN ke AMATI, jumlahkan semua turus dan cocokkan dengan banyaknya orang yang kamu tanya. Kalau angkanya tidak sama, berarti ada catatan yang terlewat atau tercatat dua kali.
:::', NULL, NULL, 3, 0.4, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_audio_id_v2', 'k5_data_collection', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Bertanya, Mencatat, Menemukan Jawaban', NULL, NULL, 'Hai! Hari ini kita akan berbicara tentang cara yang keren untuk menjawab pertanyaan, yaitu dengan data. Data adalah kumpulan informasi, misalnya jawaban teman-temanmu, catatan cuaca, atau daftar skor permainan. Kalau kamu penasaran tentang sesuatu, kamu tidak perlu menebak-nebak. Kamu bisa mengumpulkan data, menyusunnya dengan rapi, lalu membaca polanya.

Bayangkan kelasmu akan mengadakan pesta, dan kamu bertugas memilih rasa es krim. Rasa apa yang harus dibeli? Daripada menebak, jadilah detektif data. Pertama, tentukan pertanyaannya dengan jelas. Misalnya, rasa es krim apa yang paling disukai kelas kita, cokelat, vanila, atau stroberi? Kedua, kumpulkan datanya. Tanyai teman-temanmu satu per satu, dan catat setiap jawaban dengan garis turus. Satu garis untuk satu teman. Ketiga, susun catatanmu supaya rapi. Kelompokkan turus untuk cokelat, turus untuk vanila, dan turus untuk stroberi. Keempat, hitung dan periksa. Misalnya cokelat mendapat dua belas suara, stroberi delapan, dan vanila lima. Coba jumlahkan. Dua belas tambah delapan tambah lima sama dengan dua puluh lima. Kalau kamu memang bertanya kepada dua puluh lima teman, berarti catatanmu lengkap dan tidak ada jawaban yang hilang. Kelima, amati polanya. Cokelat paling banyak, vanila paling sedikit. Terakhir, jawab pertanyaanmu. Kelas paling suka cokelat, jadi belilah cokelat paling banyak, tapi tetap sediakan stroberi dan vanila untuk teman-teman yang memilihnya.

Ada satu hal penting yang perlu kamu ingat. Angka terbesar bukan berarti rasa itu paling enak untuk semua orang di dunia. Angka itu hanya bercerita tentang kelompok yang kamu tanyai. Kalau kelas sebelah yang ditanya, hasilnya bisa saja berbeda, dan itu tidak apa-apa. Data selalu bercerita tentang orang-orang yang datanya kita kumpulkan.

Sebelum kita selesai, coba jawab pertanyaan ini. Setelah semua data terkumpul, mengapa kita harus menyusunnya dulu sebelum mengambil kesimpulan? Coba pikirkan sebentar. Jawabannya, karena data yang tersusun rapi membuat pola mudah terlihat, misalnya pilihan mana yang paling banyak dan mana yang paling sedikit. Dengan begitu, jawabanmu berdasarkan bukti, bukan tebakan. Selamat menyelidiki data di sekitarmu, detektif!', 4, 0.45, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_data_collection_reading_deep_id_v2', 'k5_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menyelidiki Data Selangkah demi Selangkah', 'Ingat ide besarnya: data yang dikumpulkan lalu disusun dengan rapi bisa menjawab pertanyaan dan memperlihatkan pola. Sekarang kita ikuti satu penyelidikan dari awal sampai akhir.

## Contoh Lengkap: Permainan Favorit Saat Istirahat

Sari adalah ketua kelas. Sekolahnya akan mengadakan pekan bermain, dan gurunya bertanya: permainan apa yang harus disiapkan? Sari tidak mau asal menjawab, jadi ia menjadi detektif data.

**Langkah 1 — Tentukan pertanyaan.** "Permainan apa yang paling ingin dimainkan kelas kita saat pekan bermain?" Pilihannya: sepak bola, lompat tali, petak umpet, dan congklak.

**Langkah 2 — Kumpulkan data.** Sari bertanya kepada 24 murid satu per satu dan mencatat setiap jawaban di bukunya. Setiap murid hanya boleh memilih satu.

**Langkah 3 — Susun data.** Catatan yang berantakan diubah menjadi tabel:

| Permainan | Jumlah pemilih |
| --- | --- |
| Sepak bola | 9 |
| Lompat tali | 7 |
| Petak umpet | 5 |
| Congklak | 3 |

**Langkah 4 — Periksa data.** Sari menjumlahkan: 9 + 7 + 5 + 3 = 24. Cocok dengan jumlah murid yang ditanya. Kalau tidak cocok, ia harus memeriksa catatannya dulu sebelum lanjut.

**Langkah 5 — Amati pola.** Sepak bola paling banyak dipilih, congklak paling sedikit. Sari juga menemukan pola menarik: dua pilihan teratas adalah permainan yang dimainkan ramai-ramai. Sepertinya kelasnya suka bermain bersama dalam kelompok besar.

**Langkah 6 — Jawab dan putuskan.** Jawabannya: sepak bola adalah favorit kelas. Guru pun menyiapkan bola dan tali lompat paling banyak, tapi tetap menyediakan congklak untuk tiga murid yang memilihnya.

Perhatikan: data bukan hanya untuk menjawab pertanyaan, tapi juga membantu mengambil keputusan yang adil — berdasarkan bukti, bukan berdasarkan suara yang paling keras.

## Salah Paham yang Sering Terjadi

::: misconception
Anggapan keliru: "Pilihan dengan angka terbesar berarti pilihan yang paling bagus, dan hasilnya pasti sama di mana-mana."
Yang benar: angka terbesar hanya berarti pilihan itu **paling banyak dipilih** oleh kelompok yang ditanya. Sepak bola menang di kelas Sari, tapi kalau kelas lain yang ditanya, hasilnya bisa saja berbeda. Data bercerita tentang kelompok yang datanya kita kumpulkan, bukan tentang seluruh dunia — dan "terbanyak" tidak sama dengan "terbaik".
:::

## Ke Mana Keterampilan Ini Membawamu

Kebiasaan bertanya, mengumpulkan, menyusun, lalu menyimpulkan akan terus kamu pakai di mana-mana: saat melakukan percobaan sains, saat membaca grafik di buku atau berita, bahkan saat memutuskan hal sederhana di rumah. Nanti, ketika kamu belajar pemrograman, kamu akan melihat komputer melakukan langkah-langkah yang sama persis — menyimpan data dalam variabel dan mengolahnya dengan algoritma — hanya saja jauh lebih cepat dan dengan data yang jauh lebih banyak.

::: check
Q: Kelas A dan kelas B menjawab survei yang sama, tetapi hasilnya berbeda. Apakah salah satu kelas pasti keliru?
A: Tidak. Data menggambarkan kelompok yang ditanya, jadi dua kelompok yang berbeda wajar menghasilkan data yang berbeda.
Q: Sari bertanya kepada 24 murid, tetapi jumlah catatannya 26. Apa langkah paling tepat sebelum menyimpulkan?
A: Memeriksa ulang catatan, karena mungkin ada jawaban yang tercatat dua kali. Data harus diperiksa dulu supaya kesimpulannya bisa dipercaya.
:::', NULL, NULL, 8, 0.6, '["k2_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_intro_en_v2', 'k5_modularity', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Build It Once, Use It Again: Procedures with Blanks', 'Do you know how to tie your shoes? You learned the steps once, and now you can tie *any* shoe — sneakers, boots, even your little cousin''s cleats — without learning it all over again. Programmers do the exact same thing: they save a list of steps, give it a name, and reuse it whenever they want.

## The Big Idea: Save It, Name It, Reuse It

You already know how to break a big job into smaller chunks. Now comes the power move: turning those chunks into **procedures** you can use over and over.

- A **procedure** is an instruction list with a name. Once it has a name, you don''t rewrite the steps — you just *call* the name.
- A **parameter** is a blank inside the instruction list. Each time you use the procedure, you fill the blank with different information.
- A **return value** is the answer the procedure hands back when it finishes.

Think of a procedure as a helpful robot: you call its name, hand it some information, it does its steps, and it hands something back.

## Try It: The Pet-Feeding Procedure

Pretend your family has a dog named Biscuit and a cat named Mochi. Feeding them uses almost the same steps — so write the steps **once**, with blanks:

**Feed the Pet** (pet, food):

1. Grab [pet]''s bowl from the shelf.
2. Scoop two scoops of [food] into the bowl.
3. Set the bowl down in front of [pet].
4. Count the scoops left in the bag and report that number back.

Now use it twice:

- **Feed the Pet (Biscuit, dog kibble)** — Biscuit''s bowl gets kibble.
- **Feed the Pet (Mochi, cat crunchies)** — Mochi''s bowl gets crunchies.

One instruction list, two happy pets! The blanks *pet* and *food* are the **parameters**. And that number from step 4 — like "6 scoops left" — is the **return value**. It''s the answer the procedure sends back, so your family knows when it''s time to buy more food.

::: check
Q: In the Feed the Pet procedure, what are the parameters?
A: The blanks pet and food — the information you fill in each time you use the procedure, like Biscuit and dog kibble.
Q: What is the return value of Feed the Pet?
A: The number of scoops left in the bag — the answer the procedure reports back when it finishes.
:::

In the next reading, you''ll build a procedure step by step and see why one good procedure can do the work of a whole pile of instruction lists.', NULL, NULL, 5, 0.3, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_diagram_en_v2', 'k5_modularity', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Procedure Machine: What Goes In, What Comes Out', 'You can picture any procedure as a machine in a box. Information drops in at the top, the steps run inside, and the result pops out at the bottom.

```
        YOU CALL IT
    Make Juice ("mango")
            |
            |  parameter goes IN
            v
  +----------------------+
  |  MAKE JUICE          |
  |  (a procedure)       |
  |----------------------|
  |  1. wash [fruit]     |
  |  2. peel [fruit]     |
  |  3. blend [fruit]    |
  |  4. pour into a cup  |
  +----------------------+
            |
            |  return value comes OUT
            v
    a cup of mango juice
```

**Legend**

- **Box** — the procedure: a named instruction list saved so you can reuse it.
- **[fruit]** — a blank inside the steps; the parameter fills every one of these.
- **Top arrow** — the parameter value ("mango") traveling *into* the machine.
- **Bottom arrow** — the return value (the juice) coming back *out*.
- **1–4** — the steps, which always run in order from top to bottom.

**How to read it**

1. Start at the top: you call the procedure by name and hand it "mango".
2. The word "mango" drops into every [fruit] blank inside the box.
3. The four steps run in order: wash, peel, blend, pour.
4. The machine hands back a cup of mango juice — that''s the return value.
5. Call it again with "apple" and the *same* machine gives you apple juice. No new steps needed!

::: tip
When you notice yourself repeating steps with one small change — like packing lunch on Monday, then packing lunch on Tuesday — the part that changes is your parameter. Spot it, and you''ve found a procedure waiting to be built.
:::', NULL, NULL, 3, 0.4, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_audio_en_v2', 'k5_modularity', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Fetch! How Procedures, Parameters, and Return Values Work', NULL, NULL, 'Have you ever played fetch with a dog? Think about what''s really happening in that game, because it is secretly a computer science lesson.

When a dog learns fetch, it doesn''t learn a hundred separate tricks. It doesn''t learn fetch-the-ball as one trick and fetch-the-stick as a completely different trick. It learns one trick with a name: fetch. Chase the thing, grab the thing, bring the thing back. In computer science, a saved list of steps with a name like that is called a procedure. You teach it once, and then you can use it again and again, whenever you want.

Now here''s the clever part. When you shout, fetch the ball, you''re filling in a blank. That blank is called a parameter. A parameter is the piece of information you hand to the procedure so it knows exactly what to work on. Say ball, and the dog chases the ball. Say stick, and the very same steps happen, just with a stick instead. You didn''t teach the dog anything new. You only filled the blank with something different.

And what happens at the end of fetch? The dog trots back and drops something right at your feet. That thing the dog brings back is like a return value. A return value is whatever a procedure hands back to you when it finishes its job. Some procedures hand back an object. Others hand back an answer, like a number, or a yes, or a no.

Programmers love procedures because they save enormous amounts of work. Instead of writing the same steps over and over, they write them one time, give them a name, add blanks for the parts that change, and decide what should come back at the end. Then they can use that procedure a thousand times without rewriting anything.

So here is your recap question. In the game of fetch, what is the parameter, and what is the return value? Ready? The parameter is the thing you ask for, like the ball or the stick. That''s the information going in. The return value is whatever the dog actually brings back and drops at your feet. That''s the answer coming out.', 4, 0.45, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_deep_en_v2', 'k5_modularity', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'One Procedure, Many Jobs: A Step-by-Step Build', 'Quick recap: a **procedure** is a named instruction list you can reuse, a **parameter** is a blank you fill in each time, and a **return value** is the answer the procedure hands back.

## Worked Example: The Name-Tag Maker

Your class is throwing a party, and all 28 classmates need a name tag. Writing out the instructions 28 times would take forever. Instead, build one procedure with two blanks:

**Make a Name Tag** (name, color):

1. Cut a rectangle out of card paper.
2. Write [name] in big bubble letters.
3. Color in the letters using [color].
4. Stick one star sticker in the corner.
5. Hand back the finished tag. ← this is the return value

Now let''s *call* it — that means run it with the blanks filled in.

**Call 1: Make a Name Tag (Maya, purple)**

- Step 1: cut the rectangle.
- Step 2: [name] becomes **Maya**, so you write Maya in bubble letters.
- Step 3: [color] becomes **purple**, so the letters turn purple.
- Step 4: star sticker on.
- Step 5: a purple Maya tag comes back. That tag is the return value.

**Call 2: Make a Name Tag (Leo, green)** — same five steps, but this time a green Leo tag comes back.

| Call | name | color | Return value |
| --- | --- | --- | --- |
| Make a Name Tag (Maya, purple) | Maya | purple | purple Maya tag |
| Make a Name Tag (Leo, green) | Leo | green | green Leo tag |

Twenty-eight tags, and you only wrote the steps **once**. That''s the whole superpower.

## A Mix-Up to Avoid

::: misconception
Wrong idea: "If I want different results, I need a different procedure for each one — one procedure for purple tags, one for green tags, one for every classmate."
The truth: you need just **one** procedure with parameters. The steps never change — only the blanks do. Passing in different information (Maya and purple, or Leo and green) changes the result without rewriting a single step.
:::

If you ever catch yourself copying the same steps twice, stop and ask: *which tiny part is different?* That part wants to be a parameter.

## Where This Leads

What you learn here transfers straight into real programming. In coding tools you''ll meet later, procedures are called *functions* or *blocks*, and they work exactly like your Name-Tag Maker: information goes in through parameters, steps run, and an answer comes back out. Building procedures with parameters is such a big deal that it has its own learning standard, CSTA 1B-AP-14. Master it now with paper and pets, and real code will feel familiar later.

::: check
Q: Your friend wrote three separate instruction lists: "hop 2 times," "hop 5 times," and "hop 9 times." How could one procedure replace all three?
A: Write one procedure, Hop (number), with a parameter for how many hops. Then call Hop (2), Hop (5), or Hop (9) — the same steps run, only the blank changes.
Q: In the call Make a Name Tag (Leo, green), which information goes in, and what comes out?
A: Leo and green go in as the parameter values; the finished green Leo tag comes out as the return value.
:::', NULL, NULL, 8, 0.6, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_intro_id_v2', 'k5_modularity', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Prosedur: Daftar Langkah Ajaib yang Bisa Dipakai Ulang', 'Pernahkah kamu menyanyikan lagu "Selamat Ulang Tahun"? Nadanya selalu sama, urutan menyanyikannya selalu sama, tetapi ada satu bagian yang berganti-ganti: nama orang yang berulang tahun. Tanpa sadar, kamu sudah memakai salah satu ide terpenting di dunia komputer — dan hari ini kita akan memberinya nama.

## Ide Besar: Prosedur, Parameter, dan Nilai Balik

Dulu kamu sudah belajar bahwa pekerjaan besar bisa dipecah menjadi langkah-langkah kecil. Sekarang kita naik satu tingkat dengan tiga kata baru:

- **Prosedur** adalah daftar langkah yang kita beri *nama*. Karena punya nama, daftar itu bisa dipakai berulang-ulang cukup dengan menyebut namanya, tanpa menulis ulang semua langkahnya.
- **Parameter** adalah *bahan yang bisa diganti* setiap kali prosedur dipakai. Seperti nama pada lagu ulang tahun: lagunya tetap, namanya berganti.
- **Nilai balik** adalah *hasil* yang diberikan prosedur kembali kepada kita setelah semua langkah selesai.

Bayangkan prosedur seperti mesin kecil: kamu memasukkan bahan (parameter) dari atas, mesin menjalankan langkah-langkahnya, lalu hasil (nilai balik) keluar dari bawah.

## Contoh: Prosedur BuatJus

Ayo kita buat satu prosedur sungguhan. Kita beri nama **BuatJus**, dan parameternya adalah *buah*:

1. Kupas buah, lalu potong kecil-kecil.
2. Masukkan potongan buah ke blender bersama air dan sedikit gula.
3. Nyalakan blender selama satu menit.
4. Tuang ke dalam gelas.

Nilai baliknya: **segelas jus buah** yang siap diminum.

Sekarang lihat kehebatannya. Kalau ibumu berkata "BuatJus dengan mangga", kamu menjalankan empat langkah itu dengan mangga, dan nilai baliknya segelas jus mangga. Kalau adikmu minta "BuatJus dengan jambu", langkahnya *sama persis* — hanya buahnya yang berbeda — dan nilai baliknya jus jambu. Satu daftar langkah, banyak hasil berbeda. Itulah kekuatan prosedur!

::: check
Q: Apa untungnya memberi nama pada sebuah daftar langkah sehingga menjadi prosedur?
A: Daftar langkah itu bisa dipakai ulang kapan saja cukup dengan menyebut namanya, tanpa perlu menulis ulang semua langkahnya.
Q: Pada prosedur BuatJus, apa yang berubah dan apa yang tetap saat parameter buah diganti dari mangga menjadi jambu?
A: Langkah-langkahnya tetap sama; yang berubah hanya bahannya (parameter), sehingga nilai baliknya berubah menjadi segelas jus jambu.
:::

Di bacaan berikutnya, kamu akan mengikuti kisah seru tentang membuat 28 kartu ucapan dengan satu prosedur saja — bersiaplah terkejut betapa hematnya!', NULL, NULL, 5, 0.3, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_diagram_id_v2', 'k5_modularity', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Mesin Prosedur: Bahan Masuk, Hasil Keluar', 'Prosedur bekerja seperti mesin: bahan (parameter) masuk dari atas, langkah-langkah berjalan di dalam kotak, dan hasil (nilai balik) keluar di bawah. Diagram ini menunjukkan satu prosedur yang dipanggil dua kali dengan parameter berbeda.

```
   PANGGIL 1               PANGGIL 2
   isian: keju             isian: coklat
       |                        |
       +-----------+------------+
                   v
    +----------------------------+
    |  PROSEDUR: BuatRotiIsi     |
    |----------------------------|
    | 1. Ambil dua lembar roti   |
    | 2. Oleskan mentega tipis   |
    | 3. Taruh <isian> di tengah |
    | 4. Tangkupkan kedua roti   |
    +----------------------------+
                   |
       +-----------+------------+
       v                        v
  NILAI BALIK:            NILAI BALIK:
  roti isi keju           roti isi coklat
```

Legend:

- **Kotak besar** = prosedur, yaitu daftar langkah yang punya nama.
- **<isian>** = parameter, bahan yang bisa diganti-ganti.
- **PANGGIL** = saat prosedur dipakai; setiap panggilan boleh mengirim parameter yang berbeda.
- **Panah (v)** = arah perjalanan: bahan masuk dari atas, hasil keluar ke bawah.
- **NILAI BALIK** = hasil yang diberikan prosedur setelah semua langkah selesai.

Cara membaca diagram:

1. Mulai dari atas: ada dua panggilan untuk prosedur yang sama — satu mengirim parameter "keju", satu lagi "coklat".
2. Ikuti panah ke bawah: parameter masuk ke dalam kotak prosedur.
3. Di dalam kotak, empat langkah berjalan berurutan; pada langkah 3, tanda <isian> diganti dengan bahan yang dikirim.
4. Ikuti panah keluar di bagian bawah: setiap panggilan menghasilkan nilai baliknya sendiri.
5. Perhatikan hal terpenting: kotak langkahnya hanya ditulis satu kali, tetapi hasilnya bisa bermacam-macam.

::: tip
Saat menulis daftar langkah buatanmu sendiri, lingkari kata yang mungkin berubah-ubah — rasa, warna, nama, atau jumlah. Kata yang kamu lingkari itulah calon parameter, dan daftar langkahmu siap berubah menjadi prosedur!
:::', NULL, NULL, 3, 0.4, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_audio_id_v2', 'k5_modularity', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Pesawat Kertas dan Rahasia Prosedur', NULL, NULL, 'Halo! Coba bayangkan kamu jago sekali membuat pesawat kertas. Teman-temanmu di kelas mulai minta dibuatkan juga. Ada yang mau pesawat dari kertas merah, ada yang biru, ada yang kuning. Apakah kamu harus memikirkan cara melipat dari awal setiap kali? Tentu tidak. Cara melipatnya selalu sama, yang berganti hanya kertasnya.

Nah, dalam dunia komputer, daftar langkah yang diberi nama dan bisa dipakai berulang-ulang itu disebut prosedur. Misalnya kamu punya prosedur bernama Buat Pesawat. Isinya begini: lipat kertas menjadi dua, buka lagi, lipat kedua pojok atas ke garis tengah, lipat sisi kiri dan kanan menjadi sayap, lalu rapikan semua lipatannya. Satu daftar langkah itu bisa kamu pakai lagi dan lagi, cukup dengan menyebut namanya.

Lalu ada yang namanya parameter. Parameter itu seperti bahan yang bisa diganti-ganti setiap kali prosedur dipakai. Pada prosedur Buat Pesawat, parameternya adalah warna kertas. Kalau temanmu minta merah, kamu menjalankan langkah yang sama dengan kertas merah. Kalau temanmu minta biru, langkahnya tetap sama, hanya kertasnya yang biru.

Terakhir ada nilai balik, yaitu hasil yang diberikan prosedur kembali kepadamu setelah semua langkah selesai. Hasil dari prosedur Buat Pesawat adalah satu pesawat kertas yang siap diterbangkan. Jadi ingat tiga kata ini. Prosedur adalah daftar langkah yang punya nama. Parameter adalah bahan masuk yang bisa diganti. Nilai balik adalah hasil yang keluar.

Kenapa ini penting? Karena dengan prosedur, kamu tidak perlu mengulang pekerjaan yang sama berkali-kali. Kamu cukup menyusun langkahnya sekali, memberinya nama, lalu memanggilnya kapan pun dibutuhkan. Para pembuat game dan aplikasi bekerja persis seperti ini setiap hari.

Sekarang, satu pertanyaan pengingat untukmu. Kalau sepuluh temanmu minta pesawat kertas dengan warna yang berbeda-beda, berapa daftar langkah yang perlu kamu tulis? Jawabannya cukup satu. Satu prosedur Buat Pesawat, dipanggil sepuluh kali dengan parameter warna yang berbeda, dan setiap panggilan memberikan nilai balik berupa satu pesawat baru. Hebat, kan? Sampai jumpa di latihan berikutnya!', 4, 0.45, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_modularity_reading_deep_id_v2', 'k5_modularity', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Satu Prosedur, Banyak Hasil: Kisah 28 Kartu Ucapan', 'Ingat ide besarnya: **prosedur** adalah daftar langkah bernama yang bisa dipakai ulang, **parameter** adalah bahan yang bisa diganti, dan **nilai balik** adalah hasil yang keluar setelah semua langkah selesai. Sekarang kita buktikan betapa hematnya ide ini lewat sebuah cerita.

## Contoh Lengkap: 28 Kartu, 1 Prosedur

Bu Guru meminta Sari membuat kartu ucapan "Selamat Naik Kelas" untuk 28 teman sekelasnya — dan satu kartu ulang tahun tambahan untuk Bima. Kalau Sari menulis daftar langkah baru untuk setiap kartu, dia harus menulis lebih dari seratus langkah! Sari punya ide yang lebih cerdas: dia menulis **satu prosedur** bernama **BuatKartu** dengan **dua parameter**, yaitu *nama* dan *acara*.

Prosedur BuatKartu (nama, acara):

1. Ambil selembar kertas karton dan lipat menjadi dua.
2. Gambar hiasan bintang di sampul depan.
3. Di bagian dalam, tulis: "Selamat (acara), (nama)!"
4. Bubuhkan tanda tangan di pojok kanan bawah.

Nilai balik: satu kartu ucapan yang siap diberikan.

Ayo ikuti satu panggilan pelan-pelan. Sari memanggil **BuatKartu dengan nama = Bima, acara = Ulang Tahun**:

- Langkah 1: kertas dilipat dua (tidak ada parameter di sini, langkah berjalan seperti biasa).
- Langkah 2: bintang digambar di sampul depan.
- Langkah 3: tanda (acara) diganti "Ulang Tahun" dan (nama) diganti "Bima", sehingga tulisannya menjadi "Selamat Ulang Tahun, Bima!"
- Langkah 4: tanda tangan dibubuhkan.
- Nilai balik keluar: satu kartu ulang tahun untuk Bima. Selesai!

Untuk teman-teman yang lain, Sari tinggal memanggil prosedur yang sama berulang kali:

| Panggilan | Parameter nama | Parameter acara | Nilai balik |
| --- | --- | --- | --- |
| BuatKartu | Tania | Naik Kelas | kartu naik kelas untuk Tania |
| BuatKartu | Raka | Naik Kelas | kartu naik kelas untuk Raka |
| BuatKartu | Bima | Ulang Tahun | kartu ulang tahun untuk Bima |

Satu prosedur, empat langkah, 29 kartu. Sari hanya menulis langkahnya **sekali**.

## Miskonsepsi yang Sering Terjadi

::: misconception
Keliru: "Kalau aku ingin hasil yang berbeda, aku harus menulis daftar langkah baru dari awal."
Yang benar: selama *langkah-langkahnya sama* dan hanya *bahannya* yang berbeda, cukup satu prosedur dengan parameter. Sari tidak membuat 29 prosedur; dia membuat 1 prosedur dan memanggilnya 29 kali. Prosedur baru hanya diperlukan jika langkahnya memang berbeda — misalnya membuat *amplop* butuh cara melipat yang lain, jadi pantas dibuatkan prosedur BuatAmplop tersendiri.
:::

## Ke Mana Ilmu Ini Membawamu

Kebiasaan menyusun prosedur bernama dengan parameter dan nilai balik adalah bekal yang akan terus kamu pakai. Saat nanti membuat game atau animasi di aplikasi pemrograman balok, kamu akan bertemu "blok buatanku sendiri" yang bekerja persis seperti BuatKartu. Di jenjang berikutnya, ide yang sama muncul lagi dengan nama *fungsi* dalam bahasa pemrograman sungguhan. Dalam kurikulum informatika, kemampuan ini dikenal sebagai standar AP-K5-4 — dan kamu baru saja melatihnya hanya dengan kertas karton dan spidol.

::: check
Q: Sari perlu 10 kartu "Semoga Lekas Sembuh" untuk teman yang sakit dan 5 kartu "Selamat Juara" untuk tim futsal. Berapa prosedur baru yang harus dia tulis?
A: Nol! Prosedur BuatKartu yang sama bisa dipakai; dia cukup memanggilnya 15 kali dengan parameter acara dan nama yang berbeda-beda.
Q: Temanmu berkata, "Parameter dan nilai balik itu sama saja." Bagaimana kamu meluruskannya?
A: Keduanya berbeda arah: parameter adalah bahan yang masuk ke prosedur sebelum langkah-langkahnya berjalan, sedangkan nilai balik adalah hasil yang keluar setelah semua langkah selesai.
:::', NULL, NULL, 8, 0.6, '["k2_modularity", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_reading_intro_en_v2', 'k5_networks_communication', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'How the Internet Delivers Your Messages', 'When you send a funny picture to a friend, join a video call with your grandma, or play an online game, information races from one computer to another — sometimes across the whole world — in less than a second. It doesn''t ride in a truck, and it doesn''t fly in one big piece. It travels using a trick so clever that once you know it, you''ll never look at the internet the same way again.

## The Big Idea: Chop It, Label It, Send It

A network is a group of computers connected so they can share information — you already know that part. Here''s the new part: networks almost never send a message in one whole chunk. Instead, the sending computer **chops the message into small pieces called packets**.

Each packet is like a little envelope. Inside is one small piece of your message. On the outside are two important labels:

- **The address** — which computer this packet needs to reach
- **The number** — which piece of the message this is (piece 1, piece 2, piece 3...)

But chopping and labeling only work if every computer plays by the same rules. Those shared rules are called a **protocol**. A protocol answers questions like: How should packets be labeled? Where should each one go next? How does the receiving computer put the pieces back together? It''s just like a board game — the game only works because every player follows the same rules.

### Follow Along: The Puppy Photo

Imagine you just got a new puppy, and you send a photo of her to your best friend. Here is what happens the moment you tap send:

1. Your tablet chops the photo into lots of small packets.
2. Each packet gets your friend''s address and a piece number.
3. The packets zoom out of your house through your router.
4. Inside the internet, machines called **routers** read each address and pass the packet one step closer to your friend — like relay runners passing a baton.
5. The packets might take different paths, but they all end up at your friend''s tablet.
6. Your friend''s tablet reads the numbers, puts the pieces back in order, and — ding! — the puppy photo appears.

All of that usually happens in less than a second.

::: check
Q: Why does a computer chop a big message into small packets instead of sending it in one piece?
A: Small pieces are easier to send, and each one can find its own path. If one piece gets lost, only that little piece has to be sent again — not the whole message.
Q: What two labels does every packet carry?
A: The address of the computer it is going to, and a number that shows which piece of the message it is.
:::

Ready to find out what happens when a packet shows up late — or disappears completely? That''s exactly what the deeper dive is about.', NULL, NULL, 5, 0.3, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_diagram_en_v2', 'k5_networks_communication', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Journey of a Packet', 'Here is the trip a drawing takes when you send it from your tablet to a friend''s tablet. Even a small drawing gets chopped into packets before it travels.

```
[Your Tablet]                 [Friend''s Tablet]
      |                               ^
  chop it up                     put pieces
 [P1][P2][P3]                     in order
      |                               ^
      v                               |
 +--------+     ~~ Internet ~~    +--------+
 | Router |--->[R]--->[R]--->[R]->| Router |
 +--------+                       +--------+
```

Legend

- **[P1] [P2] [P3]** — packets: small numbered pieces of the drawing
- **[R]** — a router inside the internet that passes packets along
- **--->** — the direction the packets travel
- **~~ Internet ~~** — many networks connected together
- **+--------+ boxes** — the router in each home that connects it to the internet

How to read it

1. Start at the top left: your tablet chops the drawing into three packets — P1, P2, and P3.
2. Follow the arrows down: your home router sends the packets into the internet.
3. Each [R] reads the address on a packet and passes it one hop closer to your friend. Different packets may pass through different [R]s.
4. The packets reach your friend''s home router and travel up to the tablet.
5. At the top right, the tablet uses the packet numbers to put the pieces in order — and the whole drawing appears.

::: tip
Next time a video call freezes for a moment, picture this diagram: some packets are stuck in a traffic jam between the [R]s. Wait a few seconds — the protocol is already sorting it out.
:::', NULL, NULL, 3, 0.4, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_audio_en_v2', 'k5_networks_communication', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Postcards, Packets, and the Internet''s Rules', NULL, NULL, 'Imagine you have a pen pal who lives far away, and you want to send her a long story you wrote. The story is much too big to fit on one postcard. So here is your clever plan. You copy the story onto ten postcards. On every single postcard, you write your pen pal''s address, and you also write a number in the corner: one, two, three, all the way up to ten. Then you drop them all in the mailbox.

Here is the interesting part. The postcards might not travel together. Some might ride on one mail truck, and some on another. Postcard number seven might even arrive before postcard number two. But that is okay. Because you numbered them, your pen pal can lay them all out and put the story back in the right order.

And if postcard number four never shows up? Your pen pal writes back and says, please send number four again. You only resend that one card, not the whole story.

This is almost exactly how the internet works. When you send a photo, a message, or a move in an online game, your device chops the information into small pieces called packets. Every packet carries the address of where it is going, plus a number that shows its place in line. Machines called routers read the addresses and pass the packets along, hop by hop, until they arrive. Then the device at the other end uses the numbers to put everything back together, usually in less than a second.

The rules for all of this, like how to number the pieces, how to address them, and how to ask for a missing one again, are called a protocol. A protocol is a set of rules that every computer agrees to follow, the same way everyone in a card game agrees to the rules before playing. Without shared rules, the computers could not understand each other at all.

So here is a question for you. When one packet gets lost on its way across the internet, does the sender have to send the whole message again? Think about it for a second.

The answer is no. Because every packet is numbered, the receiving device simply asks for the one missing piece, and only that little packet makes the trip again. Chop it, label it, send it, and rebuild it. That is how your messages travel the world.', 4, 0.45, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_reading_deep_en_v2', 'k5_networks_communication', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Packets and Protocols, Step by Step', 'Quick recap: networks chop messages into small labeled pieces called **packets**, and computers follow shared rules called **protocols** to send them and put them back together.

## Worked Example: A Song Travels to Your Cousin

Your cousin moved to another city, and your class recorded itself singing a song for her birthday. You press send on the recording. Let''s slow way down and watch every step.

1. **Chop.** Your computer splits the recording into eight packets. Call them P1 through P8.
2. **Label.** Every packet gets your cousin''s address and its number. P5''s label basically says, "I am piece 5 of 8, going to Cousin''s tablet."
3. **Send.** The packets leave through your router, one after another.
4. **Hop.** Inside the internet, routers act like helpful crossing guards. Each router reads a packet''s address and points it down the best road at that moment.
5. **Split up.** The internet is busy! P1 through P4 take one road. P5 runs into a traffic jam of other people''s packets, so a router sends it down a different road.
6. **Arrive out of order.** At your cousin''s tablet, the packets show up like this: P1, P2, P3, P4, P6, P7, P5, P8. P5 came in late!
7. **Sort.** No problem. The protocol says: line the packets up by number. P5 slides right into its spot.
8. **Check and rebuild.** Now imagine P3 never arrived at all. The protocol has a rule for that too: your cousin''s tablet sends a tiny message back that means "please resend piece 3." Your computer sends just P3 again. Once all eight pieces are in place, the song plays — and your cousin hears the whole class singing.

Notice what did NOT have to happen: nobody resent the whole song, and nobody planned one perfect road ahead of time. The rules handled everything.

## A Common Mix-Up

::: misconception
**The wrong idea:** "My message travels through the internet in one whole piece, along one single wire, like a train on one track."
**The truth:** Your message is chopped into many packets, and each packet can travel a different path through the network. Some arrive early, some arrive late, and a lost one gets resent. The receiving computer uses the packet numbers to rebuild your message perfectly — so it *feels* like it traveled in one piece, even though it never did.
:::

## Where This Takes You

This idea — break information into pieces, send the pieces through many devices, and rebuild them at the other end — is the heart of the computer science standard CSTA 1B-NI-04, and it explains things you see every single day. When a video pauses to load, packets are arriving slower than the video is playing. When a message says "failed — tap to retry," packets could not get through and the protocol is asking to try again. As you keep studying computing, you''ll spot this same trick everywhere: split a big job into small labeled pieces, and agree on rules for putting them back together.

::: check
Q: Two packets from the same message take completely different roads through the internet. Will the message still come out right? Why?
A: Yes. Every packet carries the address and its piece number, so no matter which road each one takes, the receiving computer can sort them all back into the correct order.
Q: Why do computers need protocols instead of each computer just sending data its own way?
A: A protocol is a set of rules both computers agree on — how to number pieces, how to address them, and how to ask for a missing piece again. Without the same rules, the receiving computer would not know how to rebuild the message.
:::', NULL, NULL, 8, 0.6, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_reading_intro_id_v2', 'k5_networks_communication', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Paket dan Protokol: Rahasia Pesan Berkelana di Jaringan', 'Pernahkah kamu mengirim foto atau stiker lucu ke teman, lalu balasannya datang hanya beberapa detik kemudian? Padahal temanmu mungkin berada di kota lain yang jauh. Di balik layar, ada trik hebat yang membuat pesanmu bisa berkelana secepat itu.

## Ide Besar: Data Dipotong Menjadi Paket dan Diatur oleh Protokol

Di kelas sebelumnya kamu sudah tahu bahwa perangkat seperti HP, tablet, dan laptop bisa saling terhubung membentuk jaringan. Sekarang kita intip rahasianya: data tidak pernah dikirim dalam satu bongkahan besar. Sebelum berangkat, data dipotong menjadi potongan-potongan kecil yang disebut **paket**.

Setiap paket mirip amplop kecil yang berisi:

- sepotong kecil dari data (misalnya sepotong gambar)
- alamat tujuan (harus pergi ke perangkat mana)
- alamat pengirim (berasal dari mana)
- nomor urut (dia potongan yang ke berapa)

Supaya jutaan perangkat di seluruh dunia tidak bingung, semuanya sepakat memakai **protokol**, yaitu aturan bersama tentang cara mengirim dan menerima paket. Mirip aturan permainan: kalau semua pemain mengikuti aturan yang sama, permainan berjalan lancar walaupun pemainnya baru pertama kali bertemu. Kemampuan menjelaskan perjalanan data seperti ini adalah bagian dari capaian belajar informatika JKI-K5-1.

### Contoh yang Bisa Kamu Ikuti

Bayangkan kamu mengirim foto gambar hasil karyamu ke sepupu:

1. Tabletmu memotong foto itu menjadi empat paket: P1, P2, P3, dan P4.
2. Setiap paket diberi alamat tujuan, alamat pengirim, dan nomor urut.
3. Paket-paket berangkat. P1 dan P4 lewat jalur cepat, sedangkan P2 dan P3 dialihkan ke jalur lain karena jalur pertama sedang ramai.
4. Di tablet sepupumu, paket tiba dengan urutan acak: P3, P1, P4, lalu P2.
5. Berkat nomor urut, tabletnya menyusun ulang menjadi P1-P2-P3-P4, dan foto tampil utuh.

Sepupumu tidak pernah tahu fotonya sempat terpotong-potong di jalan. Semuanya terjadi otomatis dalam sekejap.

::: check
Q: Mengapa data dipotong menjadi paket-paket kecil sebelum dikirim?
A: Paket kecil lebih mudah dikirim, bisa memilih jalur yang berbeda-beda, dan jika satu paket hilang, hanya paket itu yang perlu dikirim ulang, bukan seluruh data.
Q: Apa tugas protokol dalam jaringan?
A: Protokol adalah aturan bersama yang dipakai semua perangkat agar cara mengirim dan menerima paket sama, sehingga perangkat yang berbeda-beda tetap saling mengerti.
:::

Di bacaan berikutnya, kita akan mengikuti perjalanan satu pesan langkah demi langkah, termasuk apa yang terjadi kalau ada paket yang tersesat di tengah jalan.', NULL, NULL, 5, 0.3, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_diagram_id_v2', 'k5_networks_communication', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Perjalanan Paket dari Rumahmu ke Temanmu', 'Diagram ini menunjukkan perjalanan sebuah pesan dari tabletmu sampai ke laptop temanmu. Bacalah dari atas ke bawah, mengikuti arah panah.

```
 [Tabletmu]
     |
     |  pesan dipotong: [P1][P2][P3]
     v
 (Router Rumah)
   |    |    |
  P1   P2   P3     * tiap paket boleh
   |    |    |       lewat jalur berbeda
 ~~~~ INTERNET ~~~~
    \   |   /
     v  v  v
 (Router Tujuan)
     |
     v
 [Laptop Temanmu]  susun ulang: P1+P2+P3
```

Legend:

- `[ ]` = perangkat, yaitu pengirim atau penerima pesan
- `( )` = router, petugas yang membaca alamat dan memilihkan jalur untuk paket
- `P1, P2, P3` = paket data, masing-masing punya nomor urut
- `|`, `v`, `\`, `/` = arah perjalanan paket
- `~~~~ INTERNET ~~~~` = jaringan raksasa yang berisi banyak sekali jalur
- `*` = catatan tambahan pada diagram

Cara membaca diagramnya:

1. Mulai dari kotak paling atas: tabletmu memotong pesan menjadi tiga paket, yaitu P1, P2, dan P3.
2. Paket turun ke router rumah. Router membaca alamat tujuan pada setiap paket, lalu memilihkan jalur, seperti petugas lalu lintas.
3. Di dalam internet, ketiga paket boleh berpencar dan melewati jalur yang berbeda-beda.
4. Router tujuan menangkap paket-paket yang datang, lalu meneruskannya ke perangkat yang alamatnya cocok.
5. Laptop temanmu menyusun P1, P2, dan P3 sesuai nomor urut sehingga pesan kembali utuh.

::: tip
Kalau video yang kamu tonton tersendat-sendat, biasanya itu tanda banyak paket datang terlambat. Coba mendekat ke router di rumahmu; jarak yang lebih dekat biasanya membuat paket sampai lebih lancar.
:::', NULL, NULL, 3, 0.4, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_audio_id_v2', 'k5_networks_communication', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Rahasia Paket: Bagaimana Data Sampai ke Tujuan', NULL, NULL, 'Hai! Hari ini kita membongkar sebuah rahasia: bagaimana pesan, foto, dan video bisa berkelana melewati jaringan sampai ke perangkat lain, bahkan yang letaknya sangat jauh.

Begini ceritanya. Data tidak pernah dikirim dalam satu gumpalan besar. Sebelum berangkat, data dipotong menjadi potongan-potongan kecil yang disebut paket. Setiap paket membawa tiga hal penting: sepotong kecil data, alamat tujuannya, dan nomor urut. Nomor urut itu penting sekali, karena paket-paket bisa tiba tidak berurutan, dan perangkat penerima harus bisa menyusunnya kembali.

Supaya kamu terbayang, dengarkan cerita ini. Bayangkan nenekmu ingin mengirimkan puzzle seratus keping lewat pos, tetapi kotaknya terlalu besar untuk satu amplop. Jadi nenek membagi kepingan puzzle itu ke dalam sepuluh amplop kecil. Di setiap amplop, nenek menulis alamat rumahmu, alamat rumah nenek, dan sebuah nomor: amplop satu dari sepuluh, amplop dua dari sepuluh, dan seterusnya. Amplop-amplop itu mungkin naik truk pos yang berbeda dan tiba di hari yang berbeda. Amplop tujuh bisa saja datang lebih dulu daripada amplop dua. Tapi kamu tidak khawatir, karena setiap amplop punya nomor. Kalau amplop lima tidak kunjung datang, kamu tinggal mengabari nenek, dan nenek hanya perlu mengirim ulang amplop lima, bukan seluruh puzzle. Setelah sepuluh amplop lengkap, kamu menyusun kepingannya, dan jadilah gambar yang utuh.

Persis seperti itulah paket bekerja di dalam jaringan, hanya saja jutaan kali lebih cepat.

Lalu, apa itu protokol? Protokol adalah aturan bersama yang disepakati semua perangkat. Aturan itu mengatur cara menyapa sebelum mengirim, cara memberi nomor pada paket, dan cara meminta kirim ulang kalau ada paket yang hilang. Karena semua perangkat memakai aturan yang sama, HP, tablet, dan laptop dari pembuat mana pun bisa saling memahami, seperti pemain yang mengikuti aturan permainan yang sama.

Sekarang, pertanyaan penutup untukmu. Kalau paket-paket sebuah foto tiba tidak berurutan, bagaimana perangkat penerima tahu cara menyusunnya kembali? Coba pikirkan sebentar.

Jawabannya: dengan membaca nomor urut di setiap paket. Perangkat menyusun paket dari nomor terkecil sampai terbesar, sehingga foto kembali utuh, persis seperti kamu menyusun amplop-amplop puzzle kiriman nenek.', 4, 0.45, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_networks_communication_reading_deep_id_v2', 'k5_networks_communication', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Mengikuti Perjalanan Paket Selangkah demi Selangkah', 'Kamu sudah tahu ide besarnya: data dipotong menjadi paket-paket kecil, dan protokol adalah aturan bersama yang membuat semua perangkat saling mengerti. Sekarang kita ikuti satu pesan dari awal sampai akhir, termasuk saat terjadi masalah di tengah jalan.

## Contoh Lengkap: Pesan Suara Ulang Tahun untuk Raka

Bayangkan kamu merekam pesan suara "Selamat ulang tahun, Raka!" lalu menekan tombol kirim. Inilah yang terjadi di belakang layar:

1. **Memotong.** HP-mu memotong rekaman menjadi tiga paket: paket 1, paket 2, dan paket 3. Setiap paket diberi alamat HP Raka, alamat HP-mu, dan nomor urut.
2. **Bersalaman dulu.** Sebelum paket berangkat, protokol menyuruh HP-mu "menyapa" lebih dahulu: "Halo, aku mau mengirim pesan. Siap menerima?" HP Raka menjawab: "Siap!" Ini seperti aturan sopan santun sebelum mulai berbicara.
3. **Berangkat lewat jalur berbeda.** Paket 1 dan paket 2 lewat satu jalur. Jalur itu tiba-tiba ramai, jadi router mengalihkan paket 3 ke jalur lain.
4. **Ada yang hilang!** Paket 1 dan 2 tiba dengan selamat, tetapi paket 3 tersesat dan tidak pernah sampai.
5. **Minta kirim ulang.** HP Raka memeriksa nomor urut: paket 1 ada, paket 2 ada, paket 3 tidak ada. Sesuai protokol, HP Raka mengirim kabar: "Paket nomor 3 belum sampai, tolong kirim lagi." HP-mu langsung mengirim salinan paket 3.
6. **Menyusun ulang.** Setelah ketiganya lengkap, HP Raka menyusun paket sesuai nomor urut, lalu memutar pesan suaramu secara utuh.

Perhatikan: kamu dan Raka tidak melakukan apa-apa. Semua langkah itu dijalankan perangkat secara otomatis, karena keduanya patuh pada protokol yang sama.

## Miskonsepsi yang Sering Terjadi

::: misconception
Anggapan keliru: "Pesan berjalan di internet sebagai satu kiriman utuh, seperti satu surat di dalam satu amplop besar. Kalau ada bagian yang hilang di jalan, seluruh pesan rusak dan harus dikirim ulang dari awal."
Yang benar: pesan selalu dipecah menjadi banyak paket kecil. Paket-paket boleh melewati jalur yang berbeda dan boleh tiba tidak berurutan. Nomor urut membuat perangkat penerima bisa menyusunnya kembali dengan benar, dan jika ada paket yang hilang, hanya paket itu yang dikirim ulang, bukan seluruh pesan.
:::

## Ke Mana Ilmu Ini Membawamu

Pemahaman tentang paket dan protokol adalah bekal penting untuk pelajaran informatika di jenjang berikutnya, misalnya saat kamu nanti belajar lebih dalam tentang internet, keamanan data, dan cara kerja aplikasi favoritmu. Cara berpikirnya juga berguna di luar komputer: memecah pekerjaan besar menjadi bagian-bagian kecil yang diberi nomor, lalu menyepakati aturan bersama, adalah strategi hebat untuk kerja kelompok di kelas. Mulai sekarang, setiap kali video call-mu lancar atau fotomu terkirim, kamu tahu ada ribuan paket kecil yang sedang patuh pada aturan yang sama.

::: check
Q: Paket-paket sebuah foto tiba dengan urutan 2, 4, 1, 3. Apa yang dilakukan perangkat penerima agar fotonya tetap benar?
A: Perangkat membaca nomor urut pada setiap paket, lalu menyusunnya kembali menjadi 1, 2, 3, 4 sebelum menampilkan foto, sehingga hasilnya tetap utuh.
Q: HP buatan pabrik A dan laptop buatan pabrik B tetap bisa saling berkirim data. Mengapa bisa begitu?
A: Karena keduanya mengikuti protokol yang sama. Aturan mengirim dan menerima paketnya seragam, jadi perangkat dari pembuat mana pun tetap bisa saling memahami.
:::', NULL, NULL, 8, 0.6, '["k2_networks_communication", "k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_reading_intro_en_v2', 'k5_program_development', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Plan It, Write It, Test It, Fix It', 'Have you ever explained a game to a younger kid, and they still got mixed up halfway through? It''s usually not because they weren''t listening — it''s because one step in your explanation was missing or out of order. Every app and video game you''ve ever used was built by people who ran into the exact same problem, and they solved it with a four-step trick you''re about to learn.

## The Big Idea: Programs Are Built in a Loop

Programmers almost never get a program right on the first try — and they don''t expect to! Instead, they work in a cycle with four steps:

1. **Plan** — Decide what your program should do *before* you write anything. What''s the goal?
2. **Write** — Put your instructions in order, one small, clear step at a time.
3. **Test** — Try the instructions out for real and watch closely what happens.
4. **Debug** — When something goes wrong (that''s called a **bug**), find the exact step that caused it and fix just that part. Then test again!

Notice that it''s a *loop*, not a straight line. Test, find a bug, fix it, test again — around and around until the program works. It''s like making a paper airplane: you fold it, throw it, watch it nose-dive, adjust one fold, and throw it again. You don''t crumple up the whole plane because of one bad fold.

## A Tiny Example You Can Try

Pretend your friend is a "drawing robot" who does *exactly* what your instruction list says — nothing more, nothing less. You want them to draw a smiley face, so you write:

1. Draw two dots for eyes.
2. Draw a curved line for a mouth.
3. Draw a big circle around the eyes and the mouth.

Now you **test** it. Your friend draws two dots... somewhere in the middle of the paper. Then a mouth... a bit too far away. Then they try to draw a circle around everything, and it comes out huge and lopsided. Bug found!

Time to **debug**. The problem is the *order*: with no face to aim for, the eyes and mouth ended up in odd places. So you move step 3 to the top:

1. Draw a big circle.
2. Draw two dots for eyes inside the circle.
3. Draw a curved line for a mouth under the eyes.

Test again — and this time, a perfect smiley appears. You didn''t start over; you found the one broken part and fixed only that. That''s exactly what real programmers do.

::: check
Q: What are the four steps programmers repeat when they build a program?
A: Plan, write, test, and debug — then keep testing and fixing until it works.
Q: In the smiley face example, why did testing help more than just re-reading the steps?
A: Watching the test showed exactly where things went wrong, so you knew which step to fix instead of guessing.
:::

Ready to see the whole cycle in action on a bigger challenge? The next reading walks through a full build, bug hunt and all.', NULL, NULL, 5, 0.3, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_diagram_en_v2', 'k5_program_development', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Program-Building Loop at a Glance', 'Programmers travel the same loop again and again until their program works. This picture shows the whole journey — including the secret path from DEBUG back up to TEST.

```
        +------------------+
        | 1. PLAN          |  What should it do?
        +------------------+
                 |
                 v
        +------------------+
        | 2. WRITE         |  List the steps
        +------------------+  in order.
                 |
                 v
        +------------------+
   +--->| 3. TEST          |  Try it for real!
   |    +------------------+
   |             |
   |       Did it work?
   |        /        \
   |      YES         NO
   |       |           |
   |       v           v
   |  +--------+  +------------------+
   |  | DONE!  |  | 4. DEBUG         |
   |  +--------+  | Find + fix 1 bug |
   |              +------------------+
   |                       |
   +-----------------------+
```

Legend:

- Each box is one step of the program-building cycle.
- The arrows (v and --->) mean "go to the next step."
- "Did it work?" is the question you ask after every test.
- YES and NO are the two paths your test result can take.
- The tall arrow on the left is the loop: after debugging, you always go back and test again.

How to read it:

1. Start at the top: **PLAN** what your program should do.
2. Move down to **WRITE** and put your steps in order.
3. Arrive at **TEST** and try the program for real.
4. Ask the question: did it work? If YES, you''re done — celebrate and share it!
5. If NO, drop down to **DEBUG**: find the broken step and fix just that one thing.
6. Follow the tall left arrow back up to TEST, and go around again.

::: tip
Fix one bug at a time, then test right away. If you change three things at once and the test passes, you won''t know which fix did the job — and if it fails, you won''t know which change broke it!
:::', NULL, NULL, 3, 0.4, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_audio_en_v2', 'k5_program_development', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Four-Step Secret Behind Every Program', NULL, NULL, 'Have you ever made up a secret handshake or a clapping game with a friend? If you have, then you already think like a programmer. You just didn''t know it yet.

Programmers build programs using four steps, and they repeat them like a loop. Step one is plan: decide what you want your program to do before you start. Step two is write: put your instructions in order, one small step at a time. Step three is test: try it out for real and watch what happens. And step four is debug: when something goes wrong, find the exact step that caused the problem and fix it. Then you test again, and again, until it works.

Here''s what that sounds like in real life. Imagine you and your friend invent a clapping game with eight moves that ends in a high five. You plan it together, you agree on the moves, and then you test it slowly. Clap, clap, snap, tap your shoulders, clap, and then comes the spin. But after the spin, you''re both facing the wrong way, and the high five completely misses! That''s a bug: one broken step in a list of good ones.

Now, here''s the important part. You don''t throw away the whole game. Seven of the eight moves worked great. You debug just the spin. Instead of spinning halfway, you spin all the way around, so you end up facing each other again. Then you test one more time, and the high five lands perfectly.

That''s the big secret of programming. Nobody gets it right on the first try, not even the people who make your favorite games. A bug never means you failed. It just means it''s time for one more trip around the loop. Fix one thing, test again, and keep going until it works.

So here''s your recap question. What are the four steps programmers repeat when they build a program? The answer is plan, write, test, and debug. And remember, it''s a loop, so after every fix, you always test again.', 4, 0.45, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_reading_deep_en_v2', 'k5_program_development', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'One More Trip Around the Loop: Debugging Like a Pro', 'Quick recap: programmers build things in a loop — **plan, write, test, debug** — and they go around the loop as many times as it takes. Now let''s run the whole cycle on one bigger project, from start to finish.

## Worked Example: The Classroom Robot Pet

Imagine a rainy-day recess game. Your friend plays a "robot pet" who wears a blindfold and follows your instruction list *exactly*. The mission: get the robot pet from the classroom door to the reading corner without bumping any desks.

**Step 1 — Plan.** Before writing anything, you study the room. The path goes forward past two desks, turns right at the bookshelf, and ends at the rug. Now you know exactly what the program has to do.

**Step 2 — Write.** You write the instruction list:

1. Walk 4 steps forward.
2. Turn right.
3. Walk 3 steps forward.
4. Turn left.
5. Walk 2 steps forward.

**Step 3 — Test.** Your robot pet starts walking. Instructions 1 and 2 go perfectly... but during instruction 3 — *bump* — right into a desk. You stop the test and write down exactly what you saw: "Worked until instruction 3. The third forward step hit the desk."

**Step 4 — Debug.** Here''s the systematic part: you don''t touch instructions 1, 2, 4, or 5, because you have no proof they''re broken. You change only instruction 3: "Walk 3 steps forward" becomes "Walk 2 steps forward."

**Test again.** This time the robot pet glides past the desk, turns left... and stops just short of the rug. A second bug! But it''s a *different* bug, further along the path — which proves your first fix worked. You change instruction 5 from 2 steps to 3, test one more time, and the robot pet flops happily onto the reading rug. Mission complete.

That''s real debugging: test, spot exactly where it breaks, change one thing, test again. Testing and fixing a program until it runs the way you intended is such an important skill that it has its own official spot in computer science standards (CSTA 1B-AP-15).

## The Mistake Almost Everyone Makes

::: misconception
Wrong idea: "My program has a bug. That means I messed up, and I should erase everything and start over."
The truth: bugs are a normal, expected part of programming — even professional programmers find bugs in their work every single day. A bug doesn''t mean *you* failed; it means the program needs one more trip around the loop. Erasing everything actually makes things worse, because you throw away the steps that were already working. Keep what works, fix the one step that''s broken, and test again.
:::

## Where This Leads

The plan-write-test-debug loop is the capstone of this part of your programming journey, and what you learn here transfers everywhere. When you later build things in a block-coding tool or a real programming language, you''ll use this exact loop every single time. It even works outside of computers: scientists test and adjust experiments, writers draft and revise stories, and inventors build and improve prototypes — all loops, just like yours.

::: check
Q: You test a 10-step program and it goes wrong at step 4. Should you rewrite all 10 steps? Why or why not?
A: No. Steps 1 through 3 already proved they work, so keep them. Look closely at step 4, fix just that part, and test again.
Q: Your instruction list works when you test it yourself but fails when a friend tries it. What is probably happening, and what should you do?
A: Some steps are probably unclear, so your friend understands them differently than you do. Watch exactly where their try goes wrong, rewrite that step to be more exact, and test it again with them.
:::', NULL, NULL, 8, 0.6, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_reading_intro_id_v2', 'k5_program_development', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Rencana, Tulis, Uji, Perbaiki: Cara Membuat Program', 'Pernahkah kamu menyusun menara balok yang tiba-tiba roboh, lalu menyusunnya lagi dengan cara berbeda sampai berdiri kokoh? Para pembuat program bekerja persis seperti itu: mencoba, memeriksa, lalu memperbaiki. Di pelajaran ini kamu akan belajar membuat program dengan cara yang rapi dan teratur, bukan asal jadi.

## Ide Besar: Program Hebat Tidak Jadi dalam Sekali Coba

Di kelas sebelumnya kamu sudah pandai menyusun daftar instruksi sederhana. Sekarang kita naik satu tingkat: membuat program lewat empat tahap yang selalu diulang oleh programmer di seluruh dunia.

1. **Rencana** — tentukan tujuannya. Program ini untuk apa? Seperti apa hasil akhirnya kalau berhasil?
2. **Tulis** — susun daftar instruksinya langkah demi langkah, dengan urutan yang jelas.
3. **Uji** — jalankan programnya! Ikuti instruksi persis seperti yang tertulis, atau minta teman mencobanya.
4. **Perbaiki** — kalau hasilnya belum sesuai rencana, berarti ada *bug*, yaitu kesalahan di dalam program. Temukan, betulkan, lalu uji lagi.

Empat tahap ini seperti roda yang terus berputar: uji, temukan bug, perbaiki, lalu uji lagi — sampai programmu benar-benar bekerja.

## Ayo Coba: Program Memberi Makan Ikan

Bayangkan kelasmu punya akuarium, dan kamu ingin adik kelas bisa memberi makan ikan tanpa bantuanmu. **Rencana:** tujuannya jelas — ikan mendapat satu sendok kecil pakan. **Tulis:** kamu menyusun daftar instruksi ini:

1. Ambil toples pakan dari rak.
2. Taburkan satu sendok kecil pakan ke akuarium.
3. Kembalikan toples ke rak.

**Uji:** adik kelas mencobanya... dan dia bingung di langkah 2. Pakannya tidak bisa keluar sama sekali. Kenapa? Karena tidak ada instruksi *membuka tutup toples*! Itulah bug-nya. **Perbaiki:** kamu menambahkan langkah baru setelah langkah 1: "Buka tutup toples." Lalu uji lagi — dan kali ini ikan-ikan makan dengan lahap. Programmu berhasil!

Perhatikan satu hal penting: menemukan bug bukan berarti kamu gagal. Justru karena programnya diuji, bug itu ketemu dan bisa diperbaiki.

::: check
Q: Sebutkan empat tahap membuat program secara urut!
A: Rencana, tulis, uji, dan perbaiki — lalu uji lagi sampai program bekerja dengan benar.
Q: Pada program memberi makan ikan, bagaimana bug bisa ditemukan?
A: Lewat tahap uji: saat adik kelas mengikuti instruksi persis seperti tertulis, ternyata ada langkah penting yang hilang, yaitu membuka tutup toples.
:::

Di bacaan berikutnya, kita akan menjadi detektif bug dan membedah satu contoh lengkap dari rencana sampai programnya benar-benar jadi.', NULL, NULL, 5, 0.3, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_diagram_id_v2', 'k5_program_development', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Perjalanan Membuat Program', 'Diagram ini adalah peta perjalanan sebuah program: dari ide di kepalamu sampai program yang benar-benar bekerja. Perhatikan bahwa jalurnya tidak selalu lurus — ada putaran yang boleh kamu lewati berkali-kali.

```
+-------------+
|  1 RENCANA  |
+-------------+
       |
       v
+-------------+
|   2 TULIS   |
+-------------+
       |
       v
+-------------+   ada bug?    +--------------+
|    3 UJI    |-------------->|  4 PERBAIKI  |
+-------------+               +--------------+
   |      ^                          |
   |      +-------- uji lagi --------+
   | tidak ada bug
   v
+-------------+
|  SELESAI!   |
+-------------+
```

Legenda:

- Kotak = satu tahap dalam membuat program.
- Panah (--> dan v) = urutan menuju tahap berikutnya.
- Jalur "ada bug?" = jalan yang diambil kalau pengujian menemukan kesalahan.
- Jalur "uji lagi" = setelah memperbaiki, program wajib diuji ulang.
- SELESAI! = program sudah bekerja sesuai rencana.

Cara membaca diagram:

1. Mulai dari kotak paling atas, **1 RENCANA**: tentukan tujuan programmu dan hasil akhir yang diharapkan.
2. Ikuti panah turun ke **2 TULIS**: susun daftar instruksi langkah demi langkah.
3. Turun lagi ke **3 UJI**: jalankan instruksinya persis seperti tertulis.
4. Kalau pengujian menemukan bug, ikuti jalur "ada bug?" ke kanan menuju **4 PERBAIKI**, lalu kembali lewat jalur "uji lagi" ke kotak UJI. Putaran ini boleh terjadi berkali-kali.
5. Kalau pengujian tidak menemukan bug, ikuti panah "tidak ada bug" ke bawah menuju **SELESAI!** — programmu siap dipakai.

::: tip
Tempel peta ini di dekat mejamu saat mengerjakan proyek. Setiap kali selesai memperbaiki sesuatu, tunjuk kotak UJI dan tanya dirimu: "Sudah kuuji ulang, belum?" Perbaikan yang belum diuji ulang belum boleh disebut selesai.
:::', NULL, NULL, 3, 0.4, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_audio_id_v2', 'k5_program_development', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Empat Tahap Membuat Program yang Berhasil', NULL, NULL, 'Hai! Hari ini kita akan mengobrol tentang cara para programmer membuat program yang benar-benar bekerja. Rahasianya bukan langsung jadi dalam sekali coba, melainkan empat tahap yang diulang-ulang: rencana, tulis, uji, dan perbaiki.

Tahap pertama, rencana. Sebelum menulis apa pun, tentukan dulu tujuan programmu. Apa yang harus terjadi kalau program itu berhasil? Tahap kedua, tulis. Susun instruksimu langkah demi langkah, dengan urutan yang jelas. Tahap ketiga, uji. Jalankan instruksinya persis seperti yang tertulis, tanpa menebak atau menambah-nambahi. Tahap keempat, perbaiki. Kalau hasilnya belum sesuai rencana, berarti ada bug, alias kesalahan. Temukan bug itu, betulkan, lalu uji lagi. Begitu terus, seperti roda yang berputar, sampai programmu bekerja dengan benar.

Sekarang, mari kita coba dengan satu contoh. Bayangkan kamu menulis program membuat segelas susu cokelat untuk adikmu. Rencananya: segelas susu cokelat yang manis dan tercampur rata. Instruksinya kamu tulis begini. Langkah satu, tuang susu ke dalam gelas. Langkah dua, aduk dengan sendok. Langkah tiga, masukkan dua sendok bubuk cokelat. Selesai menulis, kamu mengujinya. Kamu ikuti persis: tuang susu, aduk, lalu masukkan bubuk cokelat. Hasilnya? Bubuk cokelatnya mengambang di atas, dan susunya tidak manis sama sekali. Ada bug! Coba telusuri langkah demi langkah. Ternyata urutannya salah: kamu mengaduk sebelum bubuk cokelatnya masuk. Perbaikannya mudah: pindahkan langkah mengaduk ke paling akhir. Lalu uji sekali lagi. Tuang susu, masukkan bubuk cokelat, aduk. Dan kali ini susu cokelatnya tercampur rata dan rasanya pas. Programmu berhasil!

Ingat, menemukan bug bukan berarti kamu gagal. Semua programmer, bahkan yang paling hebat sekalipun, menemukan bug hampir setiap hari. Justru kalau kamu rajin menguji, bug lebih cepat ketemu dan lebih mudah diperbaiki. Satu kebiasaan penting: ubah satu hal saja setiap kali, lalu uji ulang, supaya kamu tahu perubahan mana yang berhasil.

Sebelum kita tutup, coba jawab pertanyaan ini. Apa empat tahap membuat program, dan apa yang kamu lakukan kalau pengujian menemukan bug? Jawabannya: rencana, tulis, uji, dan perbaiki. Kalau ada bug, perbaiki satu hal, lalu uji lagi, sampai program bekerja sesuai rencana. Selamat mencoba, programmer cilik!', 4, 0.45, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_program_development_reading_deep_id_v2', 'k5_program_development', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Menjadi Detektif Bug: Membedah Program dari Awal sampai Jadi', 'Kamu sudah tahu ide besarnya: program dibuat lewat empat tahap — rencana, tulis, uji, perbaiki — yang diulang sampai hasilnya benar. Sekarang mari kita jalani keempat tahap itu pelan-pelan dalam satu proyek utuh.

## Contoh Lengkap: Program Tarian Robot

Untuk pentas seni, kamu dan Sinta membuat pertunjukan "robot menari". Sinta menjadi robotnya; kamu menjadi programmer yang menulis instruksi geraknya.

**Tahap 1 — Rencana.** Tujuan: robot menari delapan hitungan dan berakhir menghadap penonton sambil melambai. Kamu juga menentukan gerak yang boleh dipakai: maju, mundur, putar ke kiri, putar ke kanan, tepuk, dan lambai.

**Tahap 2 — Tulis.** Kamu menyusun daftar instruksi:

1. Maju dua langkah.
2. Tepuk tangan dua kali.
3. Mundur dua langkah.
4. Putar ke kanan setengah putaran.
5. Tepuk tangan dua kali.
6. Lambaikan tangan.

**Tahap 3 — Uji.** Sinta mengikuti setiap instruksi persis seperti tertulis, tanpa menebak-nebak. Hasilnya: tariannya bagus... tapi di akhir, Sinta melambai sambil *membelakangi* penonton! Ada bug.

**Tahap 4 — Perbaiki.** Jangan buru-buru mengubah banyak hal. Telusuri langkah satu per satu sambil membayangkan arah hadap Sinta: di langkah 1 sampai 3 dia masih menghadap penonton; di langkah 4 dia berputar setengah putaran, jadi sekarang membelakangi penonton — dan tidak ada instruksi untuk berputar kembali. Ketemu! Kamu menambahkan langkah baru sebelum lambaian: "Putar ke kanan setengah putaran lagi." Lalu uji ulang dari awal. Kali ini Sinta berakhir menghadap penonton, melambai, dan kalian berdua tersenyum lebar.

Cara kerja runtut seperti ini — merencanakan, menulis, menguji, lalu memperbaiki dengan teliti — adalah inti dari standar belajar AP-K5-5, dan inilah kebiasaan para programmer sungguhan. Tiga kebiasaan detektif bug yang patut ditiru:

- Uji dengan mengikuti instruksi *persis seperti tertulis*, bukan seperti yang ada di kepalamu.
- Telusuri langkah demi langkah untuk menemukan di titik mana hasilnya mulai melenceng.
- Ubah satu hal saja, lalu uji lagi. Kalau mengubah banyak hal sekaligus, kamu tidak tahu perubahan mana yang berhasil.

## Salah Paham yang Sering Terjadi

::: misconception
Banyak yang mengira: "Programmer hebat menulis program yang langsung benar. Kalau programku ada bug, berarti aku tidak berbakat." Ini keliru. Hampir semua program — termasuk buatan programmer profesional — punya bug pada percobaan pertama. Bug bukan tanda kegagalan; bug adalah bagian normal dari membuat program. Justru kalau kamu menemukan bug saat menguji, itu artinya pengujianmu berhasil melakukan tugasnya. Programmer hebat bukan yang tidak pernah salah, melainkan yang rajin menguji dan sabar memperbaiki.
:::

## Ke Mana Keterampilan Ini Membawamu

Siklus rencana-tulis-uji-perbaiki tidak berhenti di pelajaran ini. Kebiasaan yang sama akan kamu pakai saat menggarap proyek yang lebih besar: game buatanmu sendiri, percobaan sains, bahkan karangan bahasa Indonesia yang kamu baca ulang lalu perbaiki. Dan kelak, saat kamu mulai menulis program dengan bahasa pemrograman sungguhan, kamu akan menemukan bahwa tahapannya tetap sama — hanya alatnya yang berubah.

::: check
Q: Rara mengubah tiga instruksi sekaligus, dan programnya tetap salah. Apa saran terbaik yang bisa kamu berikan padanya?
A: Kembalikan dulu perubahannya, lalu ubah satu instruksi saja setiap kali dan uji ulang setelah tiap perubahan, supaya jelas perubahan mana yang memperbaiki atau justru merusak program.
Q: Program tarianmu berjalan mulus saat kamu sendiri yang mencoba, tetapi gagal saat diikuti temanmu. Apa kemungkinan penyebabnya, dan apa yang harus dilakukan?
A: Kemungkinan ada langkah yang hanya ada di kepalamu dan belum tertulis, karena tanpa sadar kamu mengisinya sendiri saat mencoba. Minta temanmu mengikuti instruksi persis seperti tertulis, telusuri langkah demi langkah, lalu tambahkan instruksi yang hilang.
:::', NULL, NULL, 8, 0.6, '["k2_program_development", "k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_intro_en_v2', 'k5_variables', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Boxes With Labels: How Variables Remember Things', 'Have you ever noticed that a video game always knows your score, your player name, and whether the music is on? There are no tiny people inside the game writing things down. The game uses **variables** — and once you understand them, you will see them hiding in games, apps, and even your classroom.

## The Big Idea: Labeled Boxes That Hold One Thing

You already know that a variable is like a box with a name written on its label. Now it is time for two big upgrades.

**Upgrade 1: Boxes come in different types.**

- A **word box** holds words, like a name: *Nibbles*.
- A **number box** holds numbers, like *7*.
- A **yes/no box** holds only an answer: *yes* or *no*.

Picking the right type of box for the job is part of thinking like a programmer. You would not keep soup in a backpack, and you would not keep a number in a yes/no box.

**Upgrade 2: You can change what is inside.** Putting a value into a box is called **assignment**. There is one important rule: a box holds exactly *one* thing. When you put a new thing in, the old thing disappears. It is not hiding underneath — it is gone.

### Follow Along: The Class Hamster

Your class gets a hamster, and you are in charge of the record boxes. Follow this instruction list and picture each box changing:

1. Make a word box labeled **pet name**. Put *Nibbles* inside.
2. Make a number box labeled **treats today**. Put *0* inside.
3. Make a yes/no box labeled **asleep**. Put *yes* inside.
4. Nibbles wakes up! Put *no* into **asleep**. The *yes* is gone.
5. You feed Nibbles a treat. Put *1* into **treats today**. The *0* is gone.
6. Snack time again! Put *2* into **treats today**.

Now check yourself: at the end, **pet name** holds *Nibbles*, **treats today** holds *2*, and **asleep** holds *no*. Each box still holds exactly one thing — just the newest one.

::: check
Q: A number box already holds 3. You put 5 into it. What is inside the box now?
A: Only the 5. Assignment replaces the old value, so the 3 is gone.
Q: Which type of box should hold the answer to "Did I brush my teeth today?"
A: A yes/no box, because the only possible answers are yes or no.
:::

In the deep dive, you will keep score for a whole field-day game, step by step, and discover why some boxes only work in one special place.', NULL, NULL, 5, 0.3, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_diagram_en_v2', 'k5_variables', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'A Game''s Memory, Drawn as Boxes', 'Here is what a game''s memory looks like if you draw it: three variable boxes of different types, sitting inside the game they belong to. One new value is about to be dropped into the score box.

```
+---------- INSIDE THE MAZE GAME (scope) ----------+
|                                                  |
|  +----------+  +----------+  +-----------+       |
|  | player   |  | score    |  | music on? |       |
|  | [ Milo ] |  | [ 12 ]   |  | [ yes ]   |       |
|  | word     |  | number   |  | yes/no    |       |
|  +----------+  +----------+  +-----------+       |
|                      ^                           |
|                      |                           |
|              put 15 in the box                   |
|              (the old 12 is gone)                |
+--------------------------------------------------+
```

Legend:

- **Big outer box** = the maze game itself; everything inside it is the game''s *scope*, the place where these boxes live and work
- **Small boxes** = variables, each with its name on the top line
- **[ ]** = the value the box is holding right now
- **Bottom word in each box** (word, number, yes/no) = the box''s *type*
- **^ and | arrow** = an assignment happening: a new value traveling up into a box

Walkthrough:

1. Start with the big outer border. It tells you these three boxes belong to the maze game and work only inside it.
2. Read each small box top to bottom: its name, its current value in [ ], and its type.
3. Check that every value matches its type: *Milo* is a word, *12* is a number, *yes* is a yes/no answer.
4. Follow the arrow pointing at the **score** box. A new value, *15*, is being assigned.
5. Picture the moment after: the box shows [ 15 ], and the 12 has vanished — a variable holds only one value at a time.

::: tip
When you invent a variable, say three things out loud: its name, its type, and its starting value. For example: "stickers, number box, starts at 0." If you can''t say all three, your box isn''t ready yet.
:::', NULL, NULL, 3, 0.4, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_audio_en_v2', 'k5_variables', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Variables Are Boxes That Hold Exactly One Thing', NULL, NULL, 'Have you ever kept score for a game, or counted stickers on a chart? Then you already know the secret behind one of the biggest ideas in computer science: variables.

A variable is like a box with a name written on the label. The box holds exactly one thing at a time. Computers use variables to remember everything, like your score, your player name, and whether the sound is on.

Here is the first big idea: boxes come in different types. A word box holds words, like a name. A number box holds numbers, like how many points you have. And a yes-or-no box holds just one answer, yes or no. Picking the right type of box for the job is part of thinking like a programmer.

The second big idea is called assignment. Assignment means putting a value into the box. But there is a rule: when the new thing goes in, the old thing disappears. The box never holds two things at once.

Let me give you an example. Imagine your teacher keeps three boxes on a shelf. A word box called star helper. A number box called sticker count. And a yes-or-no box called indoor recess. In the morning, the teacher puts the name Ava into star helper, puts zero into sticker count, and puts no into indoor recess. Your class earns a sticker, so the teacher puts one into sticker count, and the zero is gone. Later the count becomes two, then three. Then it starts to rain, so the teacher changes indoor recess to yes.

One last idea is called scope. Scope means where a box lives and who can use it. The boxes on your classroom shelf belong only to your classroom. The class next door has its own sticker count box, and the two never mix. But the trophy case in the hallway belongs to the whole school, so everyone shares it. Variables work the same way. Some belong to one small part of a program, and some are shared by everything.

Now, one question to check your thinking. If the sticker count box holds three, and the teacher puts in four, what is inside the box, and what happened to the three?

Here is the answer. The box holds only the four. The three was replaced, and it is gone, because a variable holds exactly one thing at a time.', 4, 0.45, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_deep_en_v2', 'k5_variables', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Changing the Box: Assignment, Types, and Where Boxes Live', 'Quick recap: a variable is a labeled box that holds exactly one thing — a word, a number, or a yes/no — and assignment means putting a new value in, which pushes the old value out forever.

## Worked Example: Scorekeeper at Field Day

It is field day, and you are the official scorekeeper for the bean bag toss. Here is your instruction list for one player''s turn:

1. Make a word box called **player** and put the player''s name inside.
2. Make a number box called **throws left** and put *3* inside.
3. Make a number box called **turn points** and put *0* inside.
4. For each throw: take the number in **throws left**, subtract 1, and put the new number back in. If the bag lands in the hoop, take the number in **turn points**, add 2, and put the new number back in.
5. When **throws left** holds *0*, the turn is over. Add **turn points** to the big **team score** poster, then erase the turn boxes for the next player.

Now let''s trace Maya''s turn, one step at a time:

| Step | player | throws left | turn points |
| --- | --- | --- | --- |
| Start of turn | Maya | 3 | 0 |
| Throw 1: in the hoop! | Maya | 2 | 2 |
| Throw 2: misses | Maya | 1 | 2 |
| Throw 3: in the hoop! | Maya | 0 | 4 |

The turn is over, so you add 4 to the **team score** poster and erase the turn boxes.

Notice something sneaky here. **throws left** and **turn points** are *turn boxes* — they only exist during one player''s turn, and they get wiped clean when the turn ends. But **team score** lives on the big poster all day, where every player and every parent can see it. This idea — *where* a box lives and *who* can use it — is called **scope**. Small boxes for small jobs, big boxes for the whole game.

## Common Misconception

Lots of learners believe a variable keeps a history of everything it ever held. Let''s fix that.

::: misconception
Wrong idea: "A variable remembers everything that was ever put inside it, like a diary."
The truth: a variable holds only ONE value at a time. When Maya''s turn points went from 0 to 2 to 4, the box never held two numbers at once — each new number replaced the old one, and the old one was gone for good. If you want to keep old values around, you need extra boxes to store them in.
:::

## Where This Leads

Everything you practiced here — naming boxes clearly, choosing the right type, changing values with assignment, and knowing where a box lives — is exactly the skill described in the CSTA standard 1B-AP-09: creating variables that store and change data. When you start building programs in a block language or, later on, typing real code, you will create variables on your very first day. The scorekeeper habits you built today will transfer straight into every program you ever write: games that track lives, apps that remember names, and quizzes that count points.

::: check
Q: During Maya''s turn, the throws left box went 3, then 2, then 1, then 0. How many values did that box hold at any one moment?
A: Exactly one. Each new number replaced the old one through assignment; the box never held two numbers at the same time.
Q: After Maya''s turn ends, the next scorekeeper wants to look inside Maya''s turn points box. Why can''t they?
A: That box''s scope was one turn — it was erased when the turn ended. Only the team score poster, whose scope is the whole day, still shows Maya''s points.
:::', NULL, NULL, 8, 0.6, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_intro_id_v2', 'k5_variables', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Variabel: Kotak Pintar dengan Isi Bermacam-macam', 'Pernahkah kamu memainkan game merawat hewan peliharaan di tablet? Game itu selalu ingat nama hewanmu, seberapa lapar dia, dan apakah dia sedang tidur atau tidak. Game bisa mengingat semua itu karena menyimpannya di dalam **variabel** — dan hari ini kamu akan belajar memakainya seperti pembuat game sungguhan.

## Kotak Berlabel dengan Isi Bermacam-macam

Waktu di kelas kecil dulu, kamu sudah belajar bahwa variabel itu seperti **kotak berlabel**: kotak punya nama, dan di dalamnya tersimpan satu hal. Sekarang ada tiga hal baru yang seru:

1. **Jenis isi bisa berbeda-beda.** Ada kotak berisi *angka* (misalnya 7 atau 100), ada yang berisi *teks* alias kata (misalnya "Oyen"), dan ada yang berisi *benar-salah* (isinya hanya punya dua kemungkinan: benar atau salah).
2. **Isi kotak bisa diganti.** Mengisi atau mengganti isi kotak disebut *penugasan*. Ingat: satu kotak hanya muat satu isi. Kalau isi baru masuk, isi lama keluar dan hilang.
3. **Setiap kotak punya wilayahnya.** Kotak skor di permainanmu bukan kotak yang sama dengan kotak skor di permainan temanmu, walaupun labelnya sama-sama "skor".

| Jenis isi | Contoh |
| --- | --- |
| Angka | 7, 100, 0 |
| Teks (kata) | "Oyen", "halo" |
| Benar-salah | benar, salah |

## Contoh: Merawat Kucing Virtual

Ayo ikuti daftar instruksi ini pelan-pelan. Bayangkan setiap variabel sebagai kotak sungguhan di atas meja.

1. Buat kotak bernama **nama_kucing**, isi dengan teks "Oyen".
2. Buat kotak bernama **rasa_lapar**, isi dengan angka 7.
3. Buat kotak bernama **sedang_tidur**, isi dengan salah.
4. Kamu memberi makan Oyen. Ganti isi **rasa_lapar** menjadi 2.
5. Oyen kenyang lalu tertidur. Ganti isi **sedang_tidur** menjadi benar.

Sekarang periksa mejamu: **nama_kucing** berisi "Oyen", **rasa_lapar** berisi 2 (angka 7 sudah hilang!), dan **sedang_tidur** berisi benar.

::: check
Q: Kotak sedang_tidur berisi salah. Apa jenis isinya?
A: Jenis benar-salah, karena isinya hanya punya dua kemungkinan: benar atau salah.
Q: Isi rasa_lapar tadinya 7, lalu diganti menjadi 2. Apakah angka 7 masih ada di dalam kotak?
A: Tidak. Isi baru menggantikan isi lama, jadi sekarang kotak hanya berisi angka 2.
:::

Di bacaan berikutnya, kamu akan mengikuti satu permainan lengkap langkah demi langkah dan menyelidiki lebih dalam soal "wilayah" tempat sebuah variabel berlaku.', NULL, NULL, 5, 0.3, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_diagram_id_v2', 'k5_variables', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Variabel di Bazar Kue Kelas', 'Diagram ini menggambarkan tiga variabel yang dipakai saat kelas 5 mengadakan bazar kue. Baca dari atas ke bawah, lalu ikuti tanda panahnya.

```
           WILAYAH: Bazar Kue Kelas 5
+----------------------------------------------+
|  nama_kue      stok_kue       masih_buka     |
|  +--------+    +---------+    +-----------+  |
|  | "Bolu" |    | 10 -> 7 |    |   benar   |  |
|  +--------+    +---------+    +-----------+  |
|    (teks)        (angka)      (benar/salah)  |
|                                              |
|  3 kue terjual ==> isi stok_kue diganti      |
+----------------------------------------------+
   Kotak-kotak ini hanya berlaku di bazar ini
```

Legenda:

- Kotak kecil bergaris = satu variabel
- Tulisan di atas kotak kecil = nama (label) variabel
- Tanda kutip di dalam kotak = isi berjenis teks
- Tanda -> = penugasan: isi lama diganti isi baru
- Tanda ==> = kejadian yang membuat isi diganti
- Kotak besar yang mengelilingi semuanya = wilayah tempat variabel berlaku
- Tulisan dalam kurung di bawah kotak = jenis isi

Cara membaca diagram:

1. Baca nama di atas setiap kotak kecil: nama_kue, stok_kue, dan masih_buka — itulah tiga variabel milik bazar.
2. Lihat isi setiap kotak, lalu cocokkan dengan jenisnya yang tertulis di bawah kotak: teks, angka, dan benar-salah.
3. Ikuti tanda -> di kotak stok_kue: tadinya 10, lalu 3 kue terjual, sehingga isinya diganti menjadi 7. Angka 10 sudah hilang dari kotak.
4. Perhatikan kotak besar yang mengelilingi semuanya: ketiga variabel ini hanya berlaku di bazar kelas 5.
5. Kalau kelas lain membuka bazar sendiri, mereka punya kotak stok_kue sendiri yang tidak terpengaruh oleh kotak di diagram ini.

::: tip
Beri variabel nama yang menceritakan isinya. Dari nama masih_buka kamu langsung bisa menebak isinya pasti benar atau salah, dan dari stok_kue kamu tahu isinya pasti angka. Nama yang jelas membuat daftar instruksimu mudah dibaca siapa pun.
:::', NULL, NULL, 3, 0.4, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_audio_id_v2', 'k5_variables', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Cerita Celengan: Mendengarkan Cara Kerja Variabel', NULL, NULL, 'Hai, senang kamu ikut mendengarkan. Hari ini kita mengobrol tentang variabel, si kotak penyimpan yang pintar.

Kamu mungkin masih ingat, variabel itu seperti kotak yang diberi label nama, dan di dalamnya kita menyimpan satu hal. Sekarang kita naik satu tingkat, karena ternyata isi kotak itu bisa bermacam-macam jenisnya. Ada isi berupa angka, misalnya lima ribu. Ada isi berupa kata atau teks, misalnya sebuah nama. Dan ada isi berupa benar atau salah, seperti jawaban untuk pertanyaan ya atau tidak.

Ayo kita coba dengan cerita menabung. Bayangkan kamu punya celengan ayam di kamar. Kita buat tiga variabel untuk celengan itu. Pertama, variabel nama celengan, isinya kata, yaitu Si Gendut. Kedua, variabel jumlah tabungan, isinya angka, yaitu lima ribu. Ketiga, variabel sudah penuh, isinya salah, karena celengan masih hampir kosong.

Hari Minggu kamu mendapat uang saku dan menabung dua ribu. Sekarang kita melakukan penugasan, yaitu mengganti isi variabel. Isi jumlah tabungan diganti menjadi tujuh ribu. Nah, ini bagian pentingnya. Angka lima ribu yang lama tidak tinggal di dalam kotak. Begitu isi baru masuk, isi lama hilang. Satu variabel hanya menyimpan satu isi, yaitu isi yang paling baru.

Lalu apa itu wilayah variabel? Begini. Adikmu juga punya celengan sendiri, dengan variabel jumlah tabungan miliknya sendiri. Ketika tabunganmu berubah menjadi tujuh ribu, tabungan adikmu tidak ikut berubah sedikit pun. Namanya boleh sama, tetapi kotaknya berbeda, karena masing-masing hanya berlaku di wilayahnya sendiri. Variabel milik celenganmu hanya berlaku untuk celenganmu.

Jadi, ingat tiga hal penting. Pertama, variabel punya jenis isi, yaitu angka, teks, atau benar salah. Kedua, penugasan artinya mengganti isi, dan isi lama akan tertimpa oleh isi baru. Ketiga, setiap variabel punya wilayah berlakunya sendiri.

Sekarang pertanyaan penutup untukmu. Jika variabel jumlah tabungan berisi tujuh ribu, lalu kamu menabung lagi sehingga isinya diganti menjadi sepuluh ribu, apakah angka tujuh ribu masih ada di dalam kotak? Jawabannya, tidak ada lagi. Isi baru menggantikan isi lama, jadi sekarang kotak hanya berisi sepuluh ribu. Sampai jumpa di latihan berikutnya.', 4, 0.45, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k5_variables_reading_deep_id_v2', 'k5_variables', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Mengganti Isi Kotak dan Menjelajahi Wilayah Variabel', 'Kamu sudah tahu bahwa variabel adalah kotak berlabel yang isinya bisa berupa angka, teks, atau benar-salah, dan isinya bisa diganti lewat penugasan. Sekarang kita buktikan lewat satu permainan lengkap.

## Tebak Kata Langkah demi Langkah

Kelas 5A bermain tebak kata. Sebelum mulai, Bu Guru menyiapkan tiga variabel di papan tulis:

- **kata_rahasia** diisi teks "JERAPAH"
- **sisa_kesempatan** diisi angka 3
- **sudah_tertebak** diisi salah

Permainan berjalan begini:

1. Dinda menebak "GAJAH". Salah! Instruksinya: ganti isi **sisa_kesempatan** menjadi 2.
2. Bima menebak "KUDA". Salah lagi! Ganti isi **sisa_kesempatan** menjadi 1.
3. Sari menebak "JERAPAH". Benar! Ganti isi **sudah_tertebak** menjadi benar.

Kalau kita catat isi kotak di setiap langkah, jadinya seperti ini:

| Saat | sisa_kesempatan | sudah_tertebak |
| --- | --- | --- |
| Awal | 3 | salah |
| Setelah tebakan 1 | 2 | salah |
| Setelah tebakan 2 | 1 | salah |
| Setelah tebakan 3 | 1 | benar |

Perhatikan: setiap penugasan mengganti isi lama, dan yang tersimpan selalu isi *terakhir*.

Nah, ini bagian serunya. Di ruang sebelah, kelas 5B juga bermain tebak kata, dan mereka juga punya variabel **sisa_kesempatan** berisi 3. Ketika kotak milik 5A berubah menjadi 1, kotak milik 5B tetap 3. Labelnya sama, tetapi kotaknya berbeda, karena masing-masing hanya berlaku di *wilayah* permainannya sendiri. Inilah yang disebut **wilayah variabel** (dalam pemrograman dikenal sebagai *scope*).

## Salah Paham yang Sering Terjadi

Sebelum membahas salah paham utamanya, ingat juga soal jenis isi: angka 7 bisa dipakai berhitung, sedangkan teks "7" hanya bisa dibaca seperti kata biasa. Jadi jenis isi bukan sekadar hiasan — jenis menentukan apa yang bisa kita lakukan dengan isinya.

::: misconception
Keliru: "Kalau isi variabel diganti, isi yang lama masih tersimpan di dasar kotak. Jadi kotak berisi tumpukan semua isi yang pernah dimasukkan."
Yang benar: satu variabel hanya menyimpan SATU isi pada satu waktu. Saat penugasan terjadi, isi baru menimpa isi lama, dan isi lama hilang. Kalau isi lama masih dibutuhkan, siapkan kotak lain — misalnya kotak **skor_sebelumnya** untuk menampung skor lama sebelum diganti.
:::

## Ke Mana Ilmu Ini Membawamu

Keterampilan memakai variabel dengan berbagai jenis data — sesuai standar AP-K5-3 — adalah bekal yang akan terus kamu pakai. Saat nanti membuat game di aplikasi pemrograman balok seperti Scratch, kamu akan langsung mengenali variabel skor, nyawa, dan nama pemain. Dan ketika suatu hari kamu menulis kode sungguhan, ide tentang jenis data, penugasan, dan wilayah variabel ini akan terasa seperti teman lama.

::: check
Q: Permainan A dan permainan B sama-sama punya variabel skor. Skor permainan A diganti menjadi 50. Kalau skor permainan B tadinya 0, sekarang isinya berapa?
A: Tetap 0. Walaupun labelnya sama, keduanya kotak yang berbeda karena berada di wilayah permainan yang berbeda.
Q: Variabel poin diisi 10, lalu diganti menjadi 4, lalu diganti lagi menjadi 9. Berapa isi akhirnya, dan ke mana perginya angka 10?
A: Isi akhirnya 9. Angka 10 (dan juga 4) sudah tertimpa dan hilang — variabel hanya menyimpan isi yang paling terakhir.
:::', NULL, NULL, 8, 0.6, '["k2_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_reading_intro_en_v2', 'k8_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Fast or Slow? Comparing Algorithms', 'Ever typed a friend''s name into your phone and had it pop up before you finished the second letter? Somewhere, a programmer chose an algorithm that could dig through thousands of contacts in a blink. Two apps can both give the right answer — the difference between "instant" and "laggy" is which algorithm they run.

## Correct is not the same as efficient

You already know an algorithm is a precise, ordered list of steps that solves a problem. The new question at this level is: **what does it cost to run?** Computer scientists track two costs:

- **Time** — how many steps the algorithm performs.
- **Space** — how much memory it uses while it works.

Here''s the key insight: cost depends on the **size of the input**. An algorithm that feels instant on 10 items can crawl on 10,000. So instead of asking "is it fast?", we ask a sharper question: *how does the number of steps grow as the input grows?*

## A tale of two searches

Say your contacts app stores 16 names in alphabetical order and you search for "Zoe".

**Plan A — check one by one:**

```
for each name in the list:
    if name is "Zoe": stop — found it!
```

Worst case, Zoe is the very last name: **16 checks**. With 1,000 contacts, the worst case becomes 1,000 checks. The work grows exactly as fast as the list does.

**Plan B — halve the list** (this works because the list is sorted):

```
look at the middle name
if "Zoe" comes later in the alphabet:
    throw away the first half
otherwise:
    throw away the second half
repeat on whatever is left
```

Each check cuts the problem in half: 16 → 8 → 4 → 2 → 1. That''s about **4 checks** instead of 16. With 1,000 contacts? About 10 checks. Same problem, same correct answer — wildly different cost.

::: check
Q: Using Plan A on a list of 1,000 contacts, how many checks could you need in the worst case?
A: 1,000 — in the worst case you check every single name once.
Q: Why does Plan B stay fast even on huge lists?
A: Every check throws away half of what''s left, so doubling the list only adds about one more check.
:::

Searching is only half the story — in the deeper dive you''ll count steps precisely and meet the other big lever: spending extra *memory* to buy back *time*.', NULL, NULL, 5, 0.3, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_diagram_en_v2', 'k8_algorithms', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Two Ways to Guess a Number', 'When two algorithms solve the same problem, the clearest way to compare them is to count their steps side by side. This diagram pits two strategies for a number-guessing game against each other.

```
       GUESS THE SECRET NUMBER (1 to 100)

+--------------------+    +---------------------+
| Plan A: one by one |    | Plan B: cut in half |
+--------------------+    +---------------------+
          |                          |
          v                          v
 [1]->[2]->[3]-> ... ->[?]      [ 50? ] too high
                                     |
 worst case: 100 guesses             v
                                [ 25? ] too low
 steps grow as fast as               |
 the range grows                     v
                                [ 37? ] ...
                                     |
                                     v
                          found in about 7 guesses
```

Legend:

- Box at the top of each column = one competing algorithm (plan)
- [n] = a single guess, which costs one step of work
- -> = move on to the next guess
- | and v = follow that plan''s steps downward, in order
- "worst case" = the most steps a plan could ever need

How to read it:

1. Both plans hunt the same secret number between 1 and 100. A helper answers only "too high", "too low", or "correct".
2. Plan A (left column) tries 1, then 2, then 3, and so on. If the secret is 100, that takes 100 guesses — the worst case.
3. Plan B (right column) always guesses the middle of the numbers still possible. "Too high" or "too low" instantly throws away half of them.
4. Follow Plan B downward: 100 possibilities → 50 → 25 → 12 → 6 → 3 → 1. About 7 guesses, guaranteed.
5. Now stretch the range to 1,000. Plan A''s worst case becomes 1,000 guesses; Plan B needs only about 10. The bigger the input, the more the halving plan wins.

::: tip
You don''t need a stopwatch to compare algorithms. Count each plan''s steps on a small input, then ask: "What if the input were 10 times bigger?" The plan whose step count grows slowest is usually your winner.
:::', NULL, NULL, 3, 0.4, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_audio_en_v2', 'k8_algorithms', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Time and Space Trade-off', NULL, NULL, 'Here''s a situation you''ve probably lived through. Your class of thirty students is voting on a movie for a party, and you''re in charge of finding the winner.

One way to do it: keep nothing written down. Ask which movies were suggested, then take the first movie and walk around the room asking all thirty classmates whether that''s their vote, and count the yeses. Then do another full lap for the second movie, another for the third, and so on. If five movies were suggested, that''s five full laps around the room — a hundred and fifty questions. It works, but it''s slow, and it gets slower fast if the class grows or more movies get suggested.

Now a second way: grab a sheet of paper. Walk the room exactly once. Each time someone says a title, make a tally mark next to it, adding the title to the sheet if it''s new. One lap, thirty answers, done. The biggest tally is the winner.

Both plans are algorithms, and both get the right answer. The difference is cost. Computer scientists measure two costs. Time means how many steps you take. Space means how much memory, or in this case paper, you use while working. The first plan uses almost no paper but takes tons of steps. The second uses extra paper but finishes in a single pass. You spent space to save time, and that deal is called a time and space trade-off.

Programmers make this trade constantly. Games store ready-made map data so levels load quickly. Apps keep information waiting in memory so a search feels instant. There is rarely one perfect algorithm. There''s the best one for how much time and how much memory you can afford.

The key habit is this: before trusting an algorithm, ask how its steps grow when the input grows. Thirty students today might be three hundred at the whole-school vote tomorrow.

So here''s your recap question. When an algorithm uses extra memory so it can finish in fewer steps, what do we call that? It''s a time and space trade-off: spending space, like the tally sheet, to save time, like all those extra laps around the room.', 4, 0.45, '["k5_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_algorithms_reading_deep_en_v2', 'k8_algorithms', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Counting Steps and Trading Space for Speed', 'Two correct algorithms can solve the same problem at very different costs, and cost comes in two currencies: time (steps) and space (memory). Often you can pay more of one to save the other.

## Worked example: catching a duplicate song

Your playlist app should warn you before you add a song twice. Take this playlist: **Lift, Echo, Nova, Echo**.

**Plan A — compare every pair:**

```
for each song A in the playlist:
    for each song B that comes after A:
        if A is the same as B: report a duplicate
```

Walk it through:

1. Lift vs Echo — different.
2. Lift vs Nova — different.
3. Lift vs Echo — different.
4. Echo vs Nova — different.
5. Echo vs Echo — **duplicate!** Found on comparison 5.

With 4 songs, a full check is 3 + 2 + 1 = 6 comparisons. Watch how that grows:

| Songs | Plan A comparisons | Plan B steps |
| --- | --- | --- |
| 4 | 6 | 4 |
| 10 | 45 | 10 |
| 100 | 4,950 | 100 |

**Plan B — keep a "seen" checklist**, a structure that answers "have I seen this before?" in about one quick step:

```
seen = empty checklist
for each song in the playlist:
    if song is already in seen: report a duplicate
    otherwise: add song to seen
```

Walk it: seen starts empty → add Lift → add Echo → add Nova → Echo is already in seen — **duplicate found in 4 steps**.

But notice the price. On a 100-song playlist, Plan B builds an extra checklist holding up to 100 names, while Plan A needs almost no extra memory at all. Plan B **spends space to save time**. That deal — memory for speed, or speed for memory — is the **time/space trade-off**, and it''s everywhere: games store precomputed level data so scenes load instantly, while some apps recalculate things slowly on purpose to fit in less memory.

## Common misconception

::: misconception
Wrong belief: "Shorter code is faster code." Plan A above has fewer lines than Plan B, yet on 100 songs Plan A performs about 4,950 comparisons while Plan B performs about 100 steps. Efficiency isn''t about how many lines you typed — it''s about how many steps actually run, and how that count grows as the input grows.
:::

## Where this goes next

Comparing algorithms by counting their steps and sizing their memory is the skill described in the CSTA 2-AP-10 standard, and what you learn here transfers to every programming project you take on from now — in any language, on any device. The moment your code handles real amounts of data — every photo on a phone, every player on a game server — these growth patterns decide whether your program feels instant or unusable. Later, in high-school CS, these ideas grow into formal tools like Big-O notation, but the habit stays the same: before you trust an algorithm, ask what it costs.

::: check
Q: A 6-song playlist is checked with Plan A (compare every pair). How many comparisons are needed in the worst case?
A: 5 + 4 + 3 + 2 + 1 = 15 comparisons.
Q: Plan B finds duplicates much faster. What does it pay for that speed, and what is that deal called?
A: It pays in space — extra memory for the "seen" checklist, up to one entry per song. That deal is a time/space trade-off.
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
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_reading_intro_en_v2', 'k8_computing_systems_devices', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Meet the Team Inside Your Device', 'Every time you tap "jump" in a game, send a meme to a friend, or open your camera, a tiny team inside your device springs into action and finishes the job in a fraction of a second. Once you know who is on that team and what each member does, you can explain why apps lag, why devices "run out of memory," and what actually makes one phone faster than another.

## The Big Idea: Every Device Is a Team

Every computing device — phone, laptop, game console, even a smartwatch — is built from the same four kinds of parts:

- **Input devices** bring information *in*: touchscreen, keyboard, mouse, microphone, camera.
- **The CPU (central processing unit)** is the decision-maker. It runs instructions one after another, incredibly fast, doing the math and making the choices.
- **Memory** holds information. **RAM** is fast, temporary workspace that empties when the power goes off. **Storage** (a drive) is slower but keeps files permanently.
- **Output devices** send results *out*: screen, speakers, vibration motor.

Think of a group project. One classmate collects everyone''s ideas (input), one does the actual work (CPU), the whiteboard holds the notes you are using right now (RAM), the class binder stores finished work for later (storage), and one classmate presents the result (output). The project only works when information moves smoothly between team members — and that is exactly how a computer works too.

## A Worked Example: One Jump in a Game

Here is what happens, in order, when you press the jump button in a platformer:

```
WHEN jump button is pressed:         # INPUT
    read player position from RAM    # MEMORY
    calculate the new position       # CPU
    write new position back to RAM   # MEMORY
    draw the player higher on screen # OUTPUT
```

That whole loop can run about 60 times per second, which is why the jump feels instant. Notice the pattern: **input → CPU and memory working together → output**. Almost everything your device does follows this same path.

::: check
Q: Which part of the device decides how high the player should jump after the button press?
A: The CPU. It runs the instructions that calculate the new position; the button only reports that a press happened.
Q: While you play, the character''s position lives in RAM, not storage. Why does that make sense?
A: The position changes constantly and only matters while the game is running, so it belongs in fast, temporary RAM. Storage is for things that must survive after the game closes, like save files.
:::

In the deeper reading, you will trace a single chat message through every part of the system and learn how to spot which part is slowing everything down.', NULL, NULL, 5, 0.3, '["k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_diagram_en_v2', 'k8_computing_systems_devices', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Data Path: How Information Moves Inside a Device', 'This map shows how data travels between the four kinds of parts inside any computing device. Every arrow is a road that data can take, and the CPU sits in the middle of all the traffic.

```
+-----------+     +----------+     +-----------+
|   INPUT   | --> |   CPU    | --> |  OUTPUT   |
| keyboard, |     | decides, |     |  screen,  |
| touch,mic |     | computes |     | speakers  |
+-----------+     +----------+     +-----------+
                    ^      |
                    |      v
                 +------------+
                 |    RAM     |
                 | fast, gone |
                 | at poweroff|
                 +------------+
                    ^      |
                    |      v
                 +------------+
                 |  STORAGE   |
                 |  slower,   |
                 |  permanent |
                 +------------+
```

Legend:

- Boxes = the main parts of the system, with a short description inside
- --> = data flowing in one direction only
- Paired ^ and v arrows = data flowing in both directions (reading and writing)
- RAM = fast temporary memory; STORAGE = the permanent drive

How to read the map — follow what happens when you tap a photo thumbnail in your gallery:

1. Start at INPUT: your tap becomes a signal that travels along the arrow to the CPU.
2. The CPU requests the photo file from STORAGE — follow the paired arrows down through RAM and back.
3. The CPU places the photo data in RAM, its fast workspace, so it can work on it quickly.
4. The CPU decodes the image, reading and writing RAM many times (that is why those arrows point both ways).
5. Finish at OUTPUT: the CPU sends the final picture along the arrow to the screen.

::: tip
When a device feels slow, use this map to guess the bottleneck. Long loading times usually point to the STORAGE path. Stuttering with many apps open usually means RAM is full. Closing unused apps frees up RAM — that is why it so often helps.
:::', NULL, NULL, 3, 0.4, '["k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_audio_en_v2', 'k8_computing_systems_devices', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'What Happens Inside When You Ask for a Song', NULL, NULL, 'Have you ever asked a smart speaker to play your favorite song, and the music just starts, like magic? It is not magic. It is a team of parts working together, and once you can name the players on that team, you can figure out what any computing device is doing, and even why it sometimes gets slow.

Every device, from a phone to a game console to that smart speaker, has the same four kinds of parts. Input devices bring information in. Think of a microphone, a keyboard, or a touchscreen. The CPU, which stands for central processing unit, is the decision maker. It runs instructions incredibly fast, doing all the math and making all the choices. Memory holds information, and there are two kinds. RAM is fast, temporary workspace that gets wiped when the power turns off. Storage is slower, but it keeps your files safe permanently. Finally, output devices send results back out, like a screen or a speaker.

Now let''s follow that song request through the system. First, the microphone, an input device, picks up your voice and turns it into a signal. The CPU takes that signal and works out what you asked for. To do that thinking, it uses RAM like scratch paper, holding the sound data while it processes it. Once the CPU knows which song you want, it fetches the music file, loads chunks of it into RAM, and turns that data into sound. Then the speaker, an output device, plays it. Input, then processing with memory, then output. That same journey happens billions of times a day inside every device you own.

Here is why this matters to you. When something lags or freezes, you do not have to shrug and say the device is being weird. You can ask which part of the team is falling behind. Is the CPU overloaded with work? Is the RAM completely full? Or is the storage or the network too slow to keep up?

So here is your recap question. When you ask a speaker to play a song, which part figures out what you actually asked for, and which part holds the sound data while that thinking happens? The answer is that the CPU figures out your request, and RAM holds the data in fast, temporary workspace while the CPU works on it.', 4, 0.45, '["k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_reading_deep_en_v2', 'k8_computing_systems_devices', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Tracing One Chat Message Through the System', 'Quick recap: every device is a team of input, CPU, memory, and output parts, and almost everything it does follows the path input → processing (CPU + memory) → output.

## Worked Example: One Chat Message, Step by Step

Let''s trace exactly what happens between "you tap keys" and "your message is on its way."

1. **Input.** You tap letters on the touchscreen. Each tap becomes a tiny electrical signal sent to the CPU.
2. **Memory (RAM).** The CPU keeps the growing message in RAM — fast, temporary workspace — so your letters stay put while you type.
3. **CPU.** At the same time, the CPU runs autocorrect: it compares each word against a dictionary that was loaded from storage into RAM, and decides whether to swap it.
4. **Output (screen).** The CPU tells the screen to redraw, so you see each letter appear the instant you type it.
5. **Input again.** You tap Send.
6. **Output (network).** The CPU packages the message and hands it to the Wi-Fi chip. The network is interesting: it acts as output when your message leaves and as input when the reply arrives.
7. **Storage.** The app writes the message into your chat history on storage, so it is still there tomorrow even after a restart.

The same trip in pseudocode:

```
LOOP while typing:
    key = read touch input          # INPUT
    add key to message in RAM       # MEMORY
    check word with autocorrect     # CPU
    redraw the screen               # OUTPUT
WHEN send is tapped:
    pass message to Wi-Fi chip      # OUTPUT (network)
    save message to chat history    # STORAGE
```

The skill you are building is *analysis*: at any moment, you can name which part is working and which part it is talking to.

## Common Misconception: More Storage Means More Speed

::: misconception
Wrong belief: "A phone with 256 GB is faster than a phone with 128 GB, because bigger numbers mean better."
The truth: storage size only controls how much you can *keep* — photos, apps, videos. Speed mostly comes from the CPU (how quickly it runs instructions) and RAM (how much fast workspace it has). A device slows down when RAM fills up and the system starts borrowing slow storage as backup workspace, or when one slow part makes the fast parts wait. That slowest link in the chain is called the **bottleneck**.
:::

## Where This Leads

What you learn here transfers straight into real life. When a device lags, you can now ask "which part is the bottleneck — CPU, RAM, storage, or the network?" instead of just guessing. It also transfers to analyzing how a device''s design serves (or frustrates) the people using it and recommending improvements — which is exactly the skill described in the CSTA standard 2-CS-01. Finally, it is the foundation for later topics like operating systems, computer networks, and even building your own PC.

::: check
Q: Your game runs smoothly on its own, but stutters when five other apps are open. Using the parts of the system, explain the most likely cause.
A: The extra apps fill up RAM, so the system starts using slow storage as overflow workspace. The CPU then has to wait on slow memory transfers, which causes the stutter.
Q: A laptop has a very fast CPU but an old, slow storage drive. Predict what the user experiences, and name the bottleneck.
A: Programs run fine once they are loaded, but opening apps and large files feels slow, because the fast CPU sits idle waiting for data from the drive. The storage drive is the bottleneck.
:::', NULL, NULL, 8, 0.6, '["k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_reading_intro_id_v2', 'k8_computing_systems_devices', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'CPU, Memori, dan I/O: Tim di Balik Layar Perangkatmu', 'Pernah kesal karena HP mendadak lemot padahal kamu sedang seru bermain game? Atau penasaran kenapa laptop temanmu bisa membuka aplikasi lebih cepat daripada punyamu? Jawabannya tersembunyi di cara bagian-bagian dalam perangkatmu — CPU, memori, dan perangkat input-output — bekerja sama seperti sebuah tim.

## Tim Inti di Dalam Setiap Perangkat

Bayangkan komputer atau HP-mu sebagai kelompok kerja proyek di kelas. Supaya proyek berjalan lancar, setiap anggota punya peran yang jelas:

- **CPU (Central Processing Unit)** adalah ketua kelompok. Dialah yang benar-benar mengerjakan tugas: menghitung, membandingkan, dan memutuskan langkah berikutnya. CPU sangat cepat, tetapi hanya bisa mengerjakan data yang ada di dekatnya.
- **RAM (memori kerja)** adalah meja kerja si ketua. Semua bahan yang sedang dikerjakan diletakkan di sini supaya cepat diambil. Meja ini luasnya terbatas, dan isinya dibersihkan setiap kali perangkat dimatikan.
- **Penyimpanan (storage)** adalah lemari arsip. Muat banyak sekali berkas dan isinya awet walau perangkat mati, tetapi mengambil sesuatu dari lemari lebih lambat daripada dari meja.
- **Perangkat I/O (input/output)** adalah kurir informasi. Layar sentuh, keyboard, dan mikrofon membawa data *masuk*; layar dan speaker membawa hasil *keluar*.

Sesuai capaian SK-K8-2, tugasmu di level ini bukan sekadar menghafal nama komponen, melainkan menganalisis bagaimana mereka saling berinteraksi ketika perangkat bekerja.

## Contoh: Mengetik "Halo!" di Aplikasi Chat

Coba ikuti perjalanan satu huruf saat kamu mengetik pesan:

```
KETIKA layar disentuh:
  baca posisi sentuhan         // input masuk
  tentukan huruf yang ditekan  // CPU mengolah
  tambahkan huruf ke pesan     // disimpan di RAM
  gambar ulang kotak pesan     // output ke layar
```

Empat langkah ini terjadi setiap kali jarimu menyentuh satu tombol — dan selesai dalam sepersekian detik. Input, proses, memori, output: pola ini berulang terus, dari mengetik pesan sampai menjalankan game 3D.

::: check
Q: Saat kamu mengetik huruf di aplikasi chat, komponen mana yang bertugas menentukan huruf apa yang kamu tekan?
A: CPU. Perangkat input hanya mengirim sinyal posisi sentuhan; CPU yang mengolah sinyal itu menjadi huruf.
Q: Mengapa data yang sedang dikerjakan disimpan di RAM, bukan langsung di penyimpanan?
A: Karena RAM jauh lebih cepat diakses CPU. Penyimpanan memang muat lebih banyak dan tahan lama, tetapi terlalu lambat untuk pekerjaan yang sedang berlangsung.
:::

Di materi pendalaman, kamu akan melacak perjalanan data langkah demi langkah dan belajar menemukan bagian mana yang membuat perangkat terasa lambat.', NULL, NULL, 5, 0.3, '["k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_diagram_id_v2', 'k8_computing_systems_devices', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Aliran Data di Dalam Komputer', 'Semua yang terjadi di dalam perangkatmu bisa dirangkum dalam satu peta aliran data. Diagram ini menunjukkan bagaimana CPU, RAM, penyimpanan, dan perangkat I/O saling terhubung.

```
[INPUT] ------> +------------------+ ------> [OUTPUT]
sentuhan,       |       CPU        |         layar,
keyboard        |  pengolah utama  |         speaker
                +---------+--------+
                          ^
                          | baca/tulis (sangat cepat)
                          v
                +------------------+
                |       RAM        |
                |   memori kerja   |
                +---------+--------+
                          ^
                          | muat/simpan (lebih lambat)
                          v
                +------------------+
                |   PENYIMPANAN    |
                | (jangka panjang) |
                +------------------+
```

Legend:

- Kotak bergaris (+---+): komponen utama di dalam perangkat.
- [INPUT] dan [OUTPUT]: pintu masuk dan keluar data.
- Tanda panah (-->): aliran sinyal satu arah.
- Tanda ^ dan v pada garis tegak: jalur data dua arah.
- Tulisan di samping garis: kecepatan jalur tersebut.

Cara membaca diagram, dengan contoh membuka foto di galeri:

1. Kamu mengetuk gambar mini foto — sinyal masuk lewat jalur [INPUT] menuju CPU.
2. CPU mencari file foto di kotak PENYIMPANAN paling bawah.
3. File disalin naik melewati jalur "muat/simpan" menuju RAM.
4. CPU membaca data dari RAM lewat jalur "baca/tulis" dan mengolahnya menjadi gambar utuh.
5. Hasilnya dikirim lewat jalur [OUTPUT] — foto muncul di layar.

::: tip
Kalau perangkat terasa lambat, telusuri peta ini dari bawah ke atas dan tanyakan: jalur mana yang sedang macet? Ingat, data selalu harus "naik" dulu dari penyimpanan ke RAM sebelum CPU bisa mengolahnya.
:::', NULL, NULL, 3, 0.4, '["k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_audio_id_v2', 'k8_computing_systems_devices', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Perjalanan Sebuah Lagu di Dalam Ponselmu', NULL, NULL, 'Pernahkah kamu bertanya-tanya apa yang terjadi di dalam ponselmu saat kamu memutar sebuah lagu? Dalam waktu kurang dari satu detik, ada kerja sama yang rapi antara tiga pemain utama, yaitu CPU, memori, dan perangkat input-output.

Mari kita bahas satu per satu. CPU adalah pusat pengolah, semacam otak yang mengerjakan semua perhitungan. Memori kerja, yang biasa disebut RAM, adalah tempat data disimpan sementara supaya CPU bisa mengambilnya dengan sangat cepat. Sedangkan perangkat input dan output adalah jalur keluar-masuk informasi. Layar sentuh dan tombol membawa perintahmu masuk, sementara layar dan speaker membawa hasilnya keluar.

Sekarang kita ikuti perjalanan satu lagu. Saat jarimu menyentuh tombol putar, layar sentuh bekerja sebagai perangkat input. Ia mengubah sentuhanmu menjadi sinyal dan mengirimkannya ke CPU. CPU lalu mencari file lagu itu di penyimpanan, tempat semua datamu disimpan untuk jangka panjang. Karena penyimpanan bekerja lebih lambat, CPU tidak memproses langsung dari sana. Ia menyalin potongan lagu ke RAM terlebih dahulu. Dari RAM, CPU membaca data sedikit demi sedikit, mengubah kode digital menjadi sinyal suara, lalu mengirimkannya ke speaker. Speaker adalah perangkat output, dan akhirnya musik pun terdengar di telingamu.

Yang menarik, pola ini berulang untuk hampir semua hal yang kamu lakukan dengan perangkat. Input masuk, CPU mengolah dengan bantuan RAM, lalu output keluar. Kalau salah satu bagian kewalahan, misalnya RAM penuh karena terlalu banyak aplikasi terbuka, seluruh sistem ikut melambat. Itulah sebabnya menutup aplikasi yang tidak dipakai sering membuat ponsel terasa lebih cepat. Kemampuan menganalisis seperti ini membuatmu bukan sekadar pemakai perangkat, melainkan orang yang benar-benar paham cara kerjanya.

Sebelum selesai, coba jawab pertanyaan ini. Mengapa lagu harus disalin dulu dari penyimpanan ke RAM sebelum diputar? Jawabannya, karena RAM jauh lebih cepat diakses daripada penyimpanan, sehingga CPU bisa membaca data lagu tanpa tersendat, dan musik pun mengalir mulus tanpa terputus-putus.', 4, 0.45, '["k5_computing_systems_devices"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_computing_systems_devices_reading_deep_id_v2', 'k8_computing_systems_devices', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Melacak Perjalanan Data dan Menemukan Titik Sempit', 'Inti besarnya: setiap perangkat bekerja dengan pola yang sama — perangkat input membawa data masuk, CPU mengolahnya dengan bantuan RAM, lalu hasilnya keluar lewat perangkat output. Sekarang kita pakai pola itu untuk menganalisis masalah nyata: game yang patah-patah.

## Contoh Lengkap: Menganalisis Game yang Patah-Patah

Bayangkan kamu membuka game balap *Balap Kilat* di HP, sementara banyak aplikasi lain masih terbuka. Mari lacak apa yang terjadi:

1. Kamu mengetuk ikon game. Layar sentuh (input) mengirim sinyal ke CPU.
2. CPU meminta file game dari penyimpanan, lalu menyalinnya ke RAM.
3. Setelah data siap di RAM, CPU mulai menjalankan perulangan inti game:

```
ULANGI 60 kali per detik:
  BACA input pemain          // I/O masuk
  AMBIL data mobil dari RAM  // memori
  HITUNG posisi baru mobil   // CPU bekerja
  TULIS hasil ke RAM         // memori
  KIRIM gambar ke layar      // I/O keluar
```

4. Masalahnya: RAM sudah hampir penuh oleh aplikasi lain. Data game yang tidak muat terpaksa "dititipkan" sementara ke penyimpanan.
5. Setiap kali CPU butuh data titipan itu, ia harus menunggu penyimpanan yang jauh lebih lambat. Perulangan yang seharusnya berjalan 60 kali per detik jadi tersendat — dan di layar, game terlihat patah-patah.

Dari analisis ini muncul ide penting: **kecepatan sebuah sistem ditentukan oleh bagian paling lambat di jalurnya** — sering disebut *bottleneck* atau titik sempit. CPU secepat apa pun tidak berguna kalau ia terus menunggu data datang.

## Miskonsepsi yang Sering Muncul

::: misconception
Keliru: "HP dengan penyimpanan 256 GB pasti lebih ngebut daripada HP 64 GB."
Faktanya, angka GB pada penyimpanan hanya menunjukkan berapa banyak file yang bisa disimpan, bukan seberapa cepat perangkat bekerja. Kecepatan respons lebih ditentukan oleh CPU dan kapasitas RAM. HP 256 GB dengan RAM kecil tetap bisa terasa lambat, sementara HP 64 GB dengan RAM lega bisa terasa gesit.
:::

## Ke Mana Ilmu Ini Membawamu

Kemampuan melacak jalur input-proses-output akan terbawa jauh melampaui pelajaran ini. Saat menulis program yang lebih besar nanti, kamu akan paham kenapa kode tertentu terasa lambat dan bagaimana memperbaikinya. Saat memilih atau merawat perangkat, kamu bisa membaca spesifikasi secara kritis, bukan sekadar tergiur angka besar. Pola analisis yang sama juga menjadi fondasi materi informatika tingkat lanjut, seperti jaringan komputer dan pengembangan aplikasi.

::: check
Q: Temanmu mengedit video sambil membuka 15 tab browser, lalu aplikasinya mulai tersendat. Komponen mana yang paling mungkin menjadi titik sempit, dan mengapa?
A: RAM. Video dan banyak tab sama-sama memakan memori kerja; ketika RAM penuh, sistem bolak-balik menitipkan data ke penyimpanan yang lambat, sehingga semuanya ikut tersendat.
Q: Mengapa menambah kapasitas penyimpanan tidak menyembuhkan game yang patah-patah, tetapi menutup aplikasi lain sering berhasil?
A: Karena masalahnya ada di RAM yang penuh, bukan di ruang penyimpanan. Menutup aplikasi mengosongkan RAM, sehingga data game bisa tinggal di memori cepat dan CPU tidak perlu menunggu.
:::', NULL, NULL, 8, 0.6, '["k5_computing_systems_devices"]'::jsonb);
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
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_reading_intro_en_v2', 'k8_culture', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Think Before You Tap: Privacy, Security, and Ethics', 'You''ve probably tapped "Allow" on a pop-up without reading it, just to get into a game faster. But every one of those taps is a real decision: you''re deciding who gets your location, your photos, or your friends list. Learning to pause and evaluate those choices is one of the most useful computing skills you''ll ever pick up.

## The Big Idea: Every App Asks Three Questions (Even If It Doesn''t Say So)

Apps and websites aren''t magic — they''re built by people, and those people made choices about your data. When you evaluate any piece of technology, you can run it through three lenses:

- **Privacy** — What information does it collect about me, and who can see it?
- **Security** — How well is that information protected from people who shouldn''t have it?
- **Ethics** — Is this fair? Could it help some people while harming others?

Computer scientists weigh these same three lenses when they design software. It''s such a core skill that it has its own standard — CSTA 2-IC-21, which is all about discussing the *tradeoffs* in computing choices. Notice that word: most technology isn''t purely good or purely bad. A location feature can help you find your friends *and* let a stranger track you. Your job is to weigh both sides.

## A Worked Example: The Suspicious Quiz App

Say you install a trivia game called BrainBlast. On first launch it asks for three permissions: your **microphone**, your **contacts**, and your **location**. Instead of tapping Allow-Allow-Allow, run a quick mental program:

```
for each permission the app requests:
    ask: "does a feature I actually use need this?"
    if yes:
        allow it
    else:
        deny it and check if the app still works
```

Walk through it:

1. **Microphone** — BrainBlast has a voice-answer mode you like. Needed? Yes. Allow.
2. **Contacts** — The app says it wants to "find your friends," but you''d rather add friends by username. Needed? No. Deny.
3. **Location** — A trivia game has no map and no local features. Needed? No — this one is a red flag. Deny, and maybe check the app''s privacy policy to see what it collects and why.

You just did a real privacy evaluation. The app still runs fine, and you gave away exactly as much information as you chose to — no more.

::: check
Q: What are the three lenses you can use to evaluate any app or feature?
A: Privacy (what data is collected and who sees it), security (how the data is protected), and ethics (whether it''s fair and avoids harm).
Q: A drawing app asks for permission to read your text messages. Using the permission-check steps, what should you do?
A: Ask whether any feature you actually use needs your messages. A drawing app doesn''t, so deny the permission and check that the app still works.
:::

In the deeper read, you''ll flip roles — from user to builder — and evaluate an app your own team is designing.', NULL, NULL, 5, 0.3, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_diagram_en_v2', 'k8_culture', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Three-Lens Check for Any App or Feature', 'Before you use a new app — or ship a feature your own team built — run it through the three-lens check. This diagram shows the whole evaluation as one flow, top to bottom.

```
        +---------------------------+
        |  New app or new feature   |
        +-------------+-------------+
                      |
                      v
        +---------------------------+
        | PRIVACY: what data does   |
        | it collect? who sees it?  |
        +-------------+-------------+
                      |
                      v
        +---------------------------+
        | SECURITY: how is the data |
        | protected from attackers? |
        +-------------+-------------+
                      |
                      v
        +---------------------------+
        | ETHICS: is it fair? could |
        | it harm anyone?           |
        +------+-------------+------+
               |             |
            all OK      problem found
               |             |
               v             v
        +-----------+  +-------------+
        |  use it / |  |  change it  |
        |  ship it  |  |  or say no  |
        +-----------+  +-------------+
```

Legend:

- Boxes (drawn with +, -, and |) = one stage of the check: the thing being judged, a lens with its key questions, or a final decision
- Vertical arrows (| and v) = the order you move through the lenses
- "all OK" path = every lens passed
- "problem found" path = at least one lens raised a concern

How to read it:

1. Start at the top with whatever you''re evaluating — an app you might install or a feature your group wants to build.
2. Privacy lens: list the data it collects and who can see it.
3. Security lens: figure out how that data is stored and protected.
4. Ethics lens: ask who benefits, who could be harmed, and whether it''s fair.
5. Follow the branch. All clear? Use or ship it. Problem found? Change the design and run the check again — or walk away.

::: tip
Failing a lens doesn''t always mean "delete the app forever." Often one small change — denying a permission, switching to nicknames, making a feature opt-in — turns "problem found" into "all OK." Fix, re-check, repeat.
:::', NULL, NULL, 3, 0.4, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_audio_en_v2', 'k8_culture', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Three Questions Every App Should Answer', NULL, NULL, 'Have you ever wondered how a free app makes money when you never pay a cent? That question is a great doorway into today''s idea. Every app is built by people, and those people make choices about your information. Your job is to evaluate those choices instead of just accepting them.

There are three questions that turn you into a sharp evaluator. First, privacy: what information does this app collect about me, and who gets to see it? Second, security: how well is that information protected from people who should never have it? Third, ethics: is this fair, and could it help some people while hurting others?

Here''s an example you can try in your head. Imagine you download a free music app, and the first thing it asks is, can I access your contact list? Pause right there. Run the privacy question: does a music app need your contacts just to play songs? No. Maybe it wants them to suggest friends, but that''s optional, and you could add friends by username instead. Now the security question: if the app copies your contacts to its servers, and those servers get hacked, it''s not just your information that leaks. Your friends'' names and numbers leak too, even though they never installed the app. And that''s where the ethics question shows up: is it fair for a company to collect information about people who never agreed to anything? Probably not.

Notice that you didn''t need to write a single line of code to do any of that. You just asked three questions and weighed the tradeoffs. Sometimes the answer is, yes, this feature is worth it. Sometimes it''s, no thanks, deny. Either way, the choice becomes yours instead of the app''s.

Let''s end with a quick recap question. What are the three lenses for evaluating any app or feature? The answer: privacy, meaning what data is collected and who can see it. Security, meaning how that data is protected. And ethics, meaning whether the technology is fair and avoids causing harm. Keep asking those three questions, and you''ll be evaluating technology the way a computer scientist does.', 4, 0.45, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_reading_deep_en_v2', 'k8_culture', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'From User to Builder: Evaluating Your Own App Ideas', 'Quick recap: you can evaluate any piece of technology through three lenses — **privacy**, **security**, and **ethics** — and almost every design involves tradeoffs, not a simple good-or-bad answer.

## Worked Example: Your Team Builds StepSquad

Your class is running a fitness challenge, and your group project is an app called StepSquad. It reads step counts from each student''s phone and shows a class leaderboard. Sounds fun — now evaluate it like a professional, step by step.

**Step 1 — List the data.** StepSquad collects each student''s name, daily step count, and the device it came from. Rule of thumb: you can''t protect data you haven''t listed.

**Step 2 — Privacy lens.** Does the leaderboard need real names? No — nicknames work fine. Does everyone need to see everyone''s exact numbers? Also no. Decision: show nicknames, and let each student choose whether their count is visible or hidden.

**Step 3 — Security lens.** Where do the step counts live, and who can read them? Sketch the access rule before you code anything:

```
function viewSteps(requester, student):
    if requester == student:
        return fullHistory(student)
    if requester == teacher:
        return weeklyTotal(student)
    return "not allowed"
```

Notice the last line. Good security defaults to "not allowed" and only opens doors on purpose.

**Step 4 — Ethics lens.** Who could this harm? A student without a phone can''t join at all. A student with an injury would sit at the bottom of a public ranking every single day, in front of the whole class. Decision: score by team averages instead of individual ranks, and let anyone log steps manually or borrow a class device.

**Step 5 — Decide, and say the tradeoff out loud.** "We''re keeping the leaderboard because it motivates people, but we made it team-based and opt-in because a public individual ranking could hurt some classmates." That sentence *is* the evaluation.

## A Common Misconception

::: misconception
Wrong belief: "If an app is popular or made by a famous company, experts already made sure it''s private, secure, and fair — so I don''t have to check."
Correction: Popularity is not proof. Companies make tradeoffs that can favor themselves, because data is valuable — it powers ads and recommendations. Default settings often share more than you would choose, and even careful companies get hacked or make unfair design calls. You are part of the checking system: read the permissions, question the defaults, and push back when a design would harm someone.
:::

## Where This Leads

This is the last Social Impacts stop in this curriculum, but the three-lens habit never retires. It transfers straight into high-school computer science, where you''ll weigh the impacts of bigger systems like recommendation algorithms and facial recognition. It transfers into every group project where you build something real people will use. And it transfers into daily life every single time an app asks you for one more permission.

::: check
Q: Your team wants to add photo uploads to StepSquad so students can post workout selfies. Give one privacy question, one security question, and one ethics question to ask before building it.
A: Privacy: who can see the photos, and can a student delete theirs? Security: where are the photos stored and how are they protected from leaks? Ethics: what happens if someone uploads a photo of a classmate who never agreed to it?
Q: A feature passes the privacy and security lenses but fails the ethics lens. Should your team ship it anyway? Explain.
A: No. All three lenses matter — a feature can protect data perfectly and still treat people unfairly, like a public ranking that embarrasses students who can''t participate. Redesign it or drop it.
:::', NULL, NULL, 8, 0.6, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_reading_intro_id_v2', 'k8_culture', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Tiga Lensa untuk Menilai Dunia Digitalmu', 'Pernahkah kamu mengunduh game gratis, lalu tiba-tiba muncul permintaan: "Izinkan aplikasi mengakses lokasimu?" Kebanyakan orang langsung menekan "Izinkan" supaya bisa cepat bermain. Padahal, di balik satu ketukan itu ada keputusan penting tentang siapa yang boleh tahu tentang dirimu.

## Tiga Lensa: Privasi, Keamanan, Etika

Setiap teknologi yang kamu pakai — game, aplikasi chat, media sosial — punya dampak pada orang-orang yang memakainya. Untuk menilai dampak itu, kita bisa memakai **tiga lensa**:

- **Privasi**: data apa tentang diriku yang dikumpulkan, dan siapa yang bisa melihatnya?
- **Keamanan**: apakah akun dan perangkatku terlindungi dari orang yang tidak berhak?
- **Etika**: apakah ada orang yang bisa dirugikan — teman, keluarga, bahkan orang yang tidak kukenal?

Di kelas-kelas sebelumnya kamu sudah belajar aturan dasar seperti "jangan bagikan kata sandi". Sekarang tingkatnya naik: kamu tidak hanya mengikuti aturan, tetapi **mengevaluasi** sendiri — menimbang untung-ruginya sebelum memutuskan. Mirip seperti mencari bug: diperiksa satu per satu, bukan asal tebak.

## Contoh: Game yang Minta Izin Macam-Macam

Bayangkan kamu memasang game balap bernama *Petualang Kota*. Saat pertama dibuka, game ini meminta tiga izin: kamera, lokasi, dan daftar kontak. Yuk kita evaluasi dengan logika sederhana:

```
untuk setiap izin yang diminta:
    jika izin itu mendukung fitur utama game:
        boleh dipertimbangkan
    jika tidak:
        tolak dulu, cari tahu alasannya
```

- **Kamera**: game ini punya fitur foto untuk avatar. Masuk akal, boleh dipertimbangkan.
- **Lokasi**: tidak ada fitur peta atau balapan antarkota. Janggal, tolak.
- **Kontak**: untuk apa game balap tahu nomor teman-temanku? Sangat janggal, tolak dan waspada.

Hasil evaluasinya: game tetap bisa dimainkan, tetapi kamu hanya memberikan data yang benar-benar diperlukan. Itulah bedanya pengguna yang bijak dengan pengguna yang asal ketuk.

::: check
Q: Game balap meminta akses daftar kontak. Lensa mana yang paling terusik, dan mengapa?
A: Lensa privasi — daftar kontak berisi data orang lain dan tidak dibutuhkan oleh fitur balapan, jadi permintaan itu janggal dan sebaiknya ditolak.
Q: Apa bedanya "mengikuti aturan" dengan "mengevaluasi" saat memakai teknologi?
A: Mengikuti aturan berarti menjalankan larangan yang sudah dibuat orang lain; mengevaluasi berarti menimbang sendiri risiko privasi, keamanan, dan etika sebelum memutuskan.
:::

Kalau tiga lensa ini sudah terasa masuk akal, lanjutkan ke bacaan berikutnya — di sana kita membedah satu aplikasi secara utuh, dari pendaftaran sampai keputusan akhir satu kelas.', NULL, NULL, 5, 0.3, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_diagram_id_v2', 'k8_culture', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Alur Penyaringan Tiga Lensa', 'Sebelum menekan "Izinkan", "Unduh", atau "Bagikan", bayangkan permintaan itu harus melewati tiga penyaring berurutan. Diagram ini menunjukkan alurnya.

```
   [ APLIKASI / PERMINTAAN / KONTEN BARU ]
      |
      v
   +-----------------------------+
   | LENSA 1: PRIVASI            |
   | Data apa yang diminta?      |
   +-----------------------------+
      | wajar           | janggal
      v                 +----> ! STOP
   +-----------------------------+
   | LENSA 2: KEAMANAN           |
   | Apakah akunku terlindungi?  |
   +-----------------------------+
      | aman            | rentan
      v                 +----> ! STOP
   +-----------------------------+
   | LENSA 3: ETIKA              |
   | Adakah yang bisa dirugikan? |
   +-----------------------------+
      | tidak ada       | ada
      v                 +----> ! STOP
   ( LANJUTKAN dengan bijak )
```

Legend:

- **[ ]** — titik awal: sesuatu yang baru muncul di layarmu
- **Kotak +--+** — lensa penyaring berisi satu pertanyaan kunci
- **| dan v** — alur turun ke pemeriksaan berikutnya
- **+---->** — cabang keluar ketika ditemukan tanda janggal
- **! STOP** — berhenti dulu: pikir ulang, atur ulang, atau tanya orang dewasa tepercaya
- **( )** — hasil akhir jika lolos semua lensa

Cara membaca diagram:

1. Mulai dari atas: ada aplikasi baru, permintaan izin, atau konten yang ingin kamu bagikan.
2. Lewati Lensa 1 (privasi): jika data yang diminta wajar untuk fiturnya, turun ke bawah; jika janggal, ikuti cabang ke ! STOP.
3. Lewati Lensa 2 (keamanan): pastikan akunmu terlindungi — kata sandi kuat dan tidak dibagikan; jika rentan, keluar ke ! STOP.
4. Lewati Lensa 3 (etika): pikirkan siapa yang mungkin dirugikan, termasuk orang yang tidak ada di layar; jika ada, keluar ke ! STOP.
5. Lolos ketiganya? Lanjutkan dengan bijak — tetap pilih pengaturan yang paling aman.

::: tip
Coba sekarang: buka menu izin aplikasi di ponselmu, lalu jalankan alur ini untuk setiap izin yang aktif. Izin yang tidak lolos Lensa 1 boleh langsung kamu cabut — aplikasinya biasanya tetap berfungsi dengan baik.
:::', NULL, NULL, 3, 0.4, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_audio_id_v2', 'k8_culture', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Berpikir Dulu Sebelum Mengetuk Izinkan', NULL, NULL, 'Halo! Coba ingat, kapan terakhir kali kamu mengikuti kuis daring, misalnya kuis untuk menebak karakter film yang paling mirip denganmu? Kuis seperti itu terasa seru dan sepertinya tidak berbahaya. Tapi hari ini kita akan berpikir selangkah lebih dalam, karena di balik hal-hal kecil seperti itu ada pelajaran besar tentang dampak teknologi pada hidup kita.

Setiap kali kamu memakai aplikasi atau layanan daring, ada tiga hal yang perlu kamu timbang. Pertama, privasi. Tanyakan: data apa tentang diriku yang dikumpulkan, dan siapa saja yang bisa melihatnya? Kedua, keamanan. Tanyakan: apakah akun dan perangkatku terlindungi dari orang yang tidak berhak? Ketiga, etika. Tanyakan: apakah ada orang yang bisa dirugikan oleh keputusanku, termasuk orang yang tidak kukenal?

Sekarang kembali ke kuis tadi. Bayangkan kuis itu meminta nama lengkap, tanggal lahir, dan nama sekolahmu, katanya supaya hasil kuisnya lebih akurat. Mari kita evaluasi bersama. Apakah menebak karakter film benar-benar membutuhkan tanggal lahirmu? Tentu tidak. Lalu untuk apa data itu diminta? Bisa jadi untuk dijual ke pengiklan. Bisa juga lebih buruk: dipakai orang untuk menebak kata sandimu, karena banyak orang memakai tanggal lahir sebagai kata sandi. Gabungan nama sekolah dan tanggal lahir juga cukup bagi orang asing untuk mencari tahu siapa kamu dan di mana kamu berada. Dan kalau kuis itu meminta akses ke daftar temanmu, kamu bukan hanya membagikan datamu sendiri, tapi juga data teman-temanmu, tanpa izin mereka. Itu sudah masuk wilayah etika.

Kabar baiknya, mengevaluasi bukan berarti menolak semua teknologi. Artinya kamu menimbang manfaat dan risikonya, lalu memutuskan dengan sadar. Kadang keputusannya adalah tetap memakai, tapi dengan data seminimal mungkin dan pengaturan yang lebih ketat. Kadang keputusannya adalah berhenti dan mencari pilihan lain. Yang penting, kamulah yang memegang kendali, bukan aplikasinya.

Sebelum kita tutup, satu pertanyaan untukmu. Sebuah aplikasi meminta data lebih banyak daripada yang dibutuhkan fiturnya. Apa yang sebaiknya kamu lakukan? Jawabannya: berhenti sejenak, tanyakan untuk apa data itu diperlukan, tolak permintaan yang tidak masuk akal, dan jika masih ragu, ajak orang dewasa yang kamu percaya untuk menimbang bersama. Karena di dunia digital, berpikir sebelum mengetuk adalah bentuk kecerdasan yang sesungguhnya.', 4, 0.45, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_culture_reading_deep_id_v2', 'k8_culture', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Membedah Sebuah Aplikasi dengan Tiga Lensa', 'Kamu sudah mengenal tiga lensa untuk menilai teknologi: privasi, keamanan, dan etika. Kali ini kita memakai ketiganya untuk membedah satu kasus utuh — dari pertanyaan pertama sampai keputusan akhir.

## Studi Kasus: Kelas Ingin Memakai Aplikasi TemanKita

Kelasmu sedang mengerjakan proyek IPA berkelompok. Ketua kelas mengusulkan aplikasi (fiktif) bernama *TemanKita* untuk membagi tugas dan mengatur jadwal. Sebelum semua orang membuat akun, kalian sepakat mengevaluasinya dulu, langkah demi langkah.

**Langkah 1 — Pasang lensa privasi.** Saat mendaftar, TemanKita meminta nama lengkap, tanggal lahir, nama sekolah, dan izin lokasi yang selalu aktif. Untuk aplikasi pembagi tugas, lokasi yang selalu aktif jelas berlebihan. Gabungan nama sekolah dan tanggal lahir pun cukup bagi orang asing untuk menebak siapa kamu dan di mana kamu biasa berada.

**Langkah 2 — Pasang lensa keamanan.** Kalian mengecek perlindungan akunnya. Ternyata TemanKita membolehkan kata sandi hanya 4 angka dan tidak punya verifikasi tambahan. Artinya, akun mudah dibobol kalau ada yang iseng menebak-nebak.

**Langkah 3 — Pasang lensa etika.** Ada fitur "papan peringkat keaktifan" yang menampilkan siapa anggota paling rajin dan paling jarang muncul ke seluruh kelas. Kedengarannya memotivasi, tetapi pikirkan: teman yang sinyal internet di rumahnya buruk akan selalu tampak "malas" dan bisa jadi bahan ejekan. Fitur yang sah pun bisa merugikan seseorang.

**Langkah 4 — Timbang, lalu putuskan.** Mengevaluasi bukan sekadar menjawab ya atau tidak. Pilihan kalian: menolak aplikasi, memakai apa adanya, atau memakai dengan syarat. Logikanya kira-kira begini:

```
jika manfaat > risiko yang tersisa setelah diatur:
    pakai dengan aturan kelas
jika tidak:
    cari aplikasi pengganti
```

Kelasmu memilih "pakai dengan syarat", dengan kesepakatan berikut:

| Lensa | Temuan | Tindakan kelas |
| --- | --- | --- |
| Privasi | Lokasi selalu aktif, data lahir diminta | Matikan izin lokasi, pakai nama panggilan |
| Keamanan | Kata sandi 4 angka diperbolehkan | Semua wajib kata sandi panjang dan rahasia |
| Etika | Papan peringkat bisa jadi bahan ejekan | Sepakat: peringkat bukan alat mengejek |

Inilah evaluasi yang sesungguhnya: kalian tetap menikmati manfaat teknologi, tetapi risikonya dikendalikan dengan sadar.

## Miskonsepsi yang Sering Muncul

::: misconception
Anggapan keliru: "Aku tidak punya rahasia apa-apa, jadi privasi bukan urusanku."
Yang benar: privasi bukan soal menyembunyikan hal buruk, melainkan soal **kendali**. Potongan data yang kelihatan sepele — nama sekolah, jadwal les, foto seragam — bisa digabungkan orang lain menjadi gambaran lengkap tentang dirimu, lalu dipakai untuk penipuan, akun palsu, atau mengganggu keselamatanmu. Kamu berhak menentukan siapa boleh tahu apa tentang dirimu, sama seperti kamu berhak menutup pintu kamarmu.
:::

## Ke Mana Keterampilan Ini Membawamu

Kebiasaan menimbang privasi, keamanan, dan etika — inti dari capaian **DSI-K8-2** — tidak berhenti di pelajaran ini. Keterampilan ini akan terus kamu pakai setiap kali memilih aplikasi baru, membuat konten, atau nanti ketika kamu sendiri yang merancang program: pembuat teknologi yang baik selalu bertanya "siapa yang bisa dirugikan oleh karyaku?". Semakin sering dilatih, semakin otomatis kebiasaan ini bekerja — seperti menoleh ke kanan dan kiri sebelum menyeberang jalan.

::: check
Q: Sebuah aplikasi belajar gratis merekam suara siswa "untuk meningkatkan layanan". Sebutkan satu risiko privasi dan satu pertanyaan etika yang perlu diajukan sebelum sekolah memakainya.
A: Risiko privasi: rekaman suara adalah data pribadi yang bisa bocor atau dipakai tanpa izin. Pertanyaan etika: apakah siswa dan orang tua diberi tahu dengan jelas dan boleh menolak tanpa dirugikan?
Q: Enam anggota kelompok memakai satu akun dengan satu kata sandi bersama. Apa masalahnya dari lensa keamanan dan lensa etika?
A: Keamanan: semakin banyak orang tahu kata sandi, semakin besar peluang bocor. Etika: kalau satu orang menyalahgunakan akun, semua anggota ikut tertuduh karena jejaknya tidak bisa dibedakan.
:::', NULL, NULL, 8, 0.6, '["k5_culture"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_reading_intro_en_v2', 'k8_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Cleaning Up Messy Data: From Raw Numbers to Real Answers', 'Every app on your phone is quietly collecting data: your game stats, your streaming history, your step count. But here is the secret nobody shows you on the dashboard — raw data is almost always a mess, and before anyone can turn it into a slick chart, someone has to clean it up and do the math. In this lesson, that someone is you.

## The big idea: raw data is not ready data

When you collect data in the real world — a class survey, a sensor, a game log — it arrives with problems: typos, blanks, duplicates, and answers written five different ways. Data analysis really has two jobs:

1. **Clean and transform** the data so every value is consistent and trustworthy.
2. **Analyze** it with statistics like the *mean* (average), *median* (middle value), and *mode* (most common value) to find the story inside.

This is exactly what the computing standard CSTA 2-DA-08 is about: transforming collected data to make it more useful and reliable.

### A quick worked example

Suppose your class surveys six students: "How many hours did you sleep last night?" The raw answers come back like this:

```
"8", "seven", "8.5 hrs", "", "9", "7.5"
```

A computer cannot average the word "seven" or a blank answer. So you run a cleaning pass:

```
for each answer:
    if blank        -> mark as MISSING (skip it)
    if it is a word -> convert to a number ("seven" -> 7)
    if it has units -> strip them ("8.5 hrs" -> 8.5)
```

Cleaned data: 8, 7, 8.5, 9, 7.5 — five usable values, plus one marked missing.

- **Mean:** (8 + 7 + 8.5 + 9 + 7.5) / 5 = 40 / 5 = **8 hours**
- **Median:** sort them (7, 7.5, 8, 8.5, 9) — the middle value is **8 hours**

Now the data is clean and summarized — ready to become a chart instead of a headache.

::: check
Q: Why do we convert "8.5 hrs" to plain 8.5 before analyzing?
A: Computers can only do math on numbers, so every value in a column must have the same consistent format.
Q: A survey answer is blank. Should you count it as 0?
A: No. A blank means the data is missing, not zero. Counting it as 0 would wrongly drag the average down, so mark it missing and leave it out of the math.
:::

Ready for more? The deep dive walks through a full messy dataset — duplicates, fake zeros, wrong units and all — and shows how sloppy cleaning leads to wrong answers.', NULL, NULL, 5, 0.3, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_diagram_en_v2', 'k8_data_collection', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Data Pipeline at a Glance', 'Every polished chart you have seen in an app or on a science-fair poster has a hidden assembly line behind it. This diagram shows the whole journey of a data project, from messy raw numbers to a story you can share.

```
+-----------+    +-----------+    +-----------+
| RAW DATA  |--->|   CLEAN   |--->| TRANSFORM |
| survey,   |    | fix typos |    | convert   |
| sensors,  |    | drop dups |    | units,    |
| app logs  |    | flag gaps |    | sort/group|
+-----------+    +-----------+    +-----------+
                                        |
                                        v
+-----------+    +-----------+    +-----------+
|   SHARE   |<---| VISUALIZE |<---|  ANALYZE  |
| explain   |    | bar chart |    | mean,     |
| the story |    | line plot |    | median,   |
|           |    |           |    | mode      |
+-----------+    +-----------+    +-----------+
```

Legend:
- Each box = one stage of the data pipeline
- ---> and <--- = the direction the data flows
- | and v = the flow turning the corner from TRANSFORM down to ANALYZE
- Small text inside a box = examples of what happens at that stage

How to read it:
1. Start at RAW DATA: numbers arrive from surveys, sensors, or app logs — full of typos, duplicates, and gaps.
2. CLEAN fixes what is broken: correct typos, delete duplicate rows, and flag missing values instead of pretending they are zeros.
3. TRANSFORM reshapes the clean data: convert units so everything matches, then sort or group values so they are chart-ready.
4. ANALYZE runs the statistics: mean, median, and mode squeeze many numbers into a few meaningful ones.
5. VISUALIZE turns those results into a bar chart or line plot that human eyes can understand in seconds.
6. SHARE is the goal of everything upstream: explaining what the data actually says — and what it does not.

::: tip
Never clean your only copy. Duplicate the raw data first and clean the copy, keeping a short note of every change, like "removed 2 duplicate rows" or "marked 1 value missing." If you make a mistake you can start over, and anyone can verify your work.
:::', NULL, NULL, 3, 0.4, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_audio_en_v2', 'k8_data_collection', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Why Clean Data Beats Messy Data', NULL, NULL, 'Imagine you and three friends decide to figure out who is the best at your favorite racing game. You each play ten races and write down your finishing times in a shared note. Sounds simple, right? But when you open that note, it is chaos. One friend wrote her times in minutes when everyone else used seconds. Another accidentally pasted the same race twice. And one race just says crashed, because the game froze.

This is the most important secret in data analysis: real data is almost always messy, and you cannot trust any average, chart, or conclusion until you have cleaned it up.

Cleaning data means a few specific things. You remove duplicates, so nothing counts twice. You fix format problems, like converting minutes to seconds so everything uses the same units. And you handle missing values honestly. That crashed race is not a time of zero. A zero would make someone look impossibly fast. It is simply missing, so you set it aside and leave it out of the math.

Once the data is clean, the statistics can do their job. The mean, which is the average, adds everything up and divides by the count. The median is the middle value when you put the numbers in order. Here is why you need both. If one race time is a wild outlier, like a typo that says nine thousand seconds, the mean gets dragged way off, but the median barely notices. Comparing the two helps you spot when something in your data is off.

After cleaning and analyzing, you can transform the data for a chart, maybe sorting racers from fastest to slowest, and finally share what you found. Clean first, calculate second, chart third. That order is the whole game.

So here is your recap question. A friend says a blank answer in our data is basically the same as zero, so let''s just type in zero. Is your friend right? No. A blank means the measurement is missing, but a zero is a real value that changes your average. Mark it missing, leave it out of the calculation, and your results stay honest.', 4, 0.45, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_reading_deep_en_v2', 'k8_data_collection', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Data Detective: A Full Cleaning and Analysis Walkthrough', 'Quick recap: real-world data arrives messy, and your job is to clean and transform it *before* you calculate anything — otherwise your statistics quietly lie to you.

## Worked example: the step-count showdown

Your PE class is running a friendly step-count competition. Five students paste Tuesday''s numbers into a shared spreadsheet:

| Student | Steps |
| --- | --- |
| Ava | 9,200 |
| Ben | 8500 |
| Ben | 8500 |
| Chen | 0 |
| Dee | 7.4 |
| Eli | 11000 |

Let''s clean it properly, step by step.

**Step 1 — Remove duplicates.** Ben''s row appears twice because he submitted twice. Keep one copy. Left in, he would count double.

**Step 2 — Investigate suspicious values.** Chen''s 0 looks like data, but ask: did Chen really take zero steps? No — his phone was dead all day. That is *missing data*, not a measurement. Mark it MISSING instead of keeping a fake zero.

**Step 3 — Fix unit mix-ups.** Dee''s 7.4 cannot be a step count. She copied the *kilometers* number her app showed. Do not guess — ask her to check the app''s actual step count. It says 9700, so replace 7.4 with 9700.

**Step 4 — Standardize the format.** Strip the comma from "9,200" so every value is a plain number the computer can process.

Clean data: 9200, 8500, 9700, 11000 (Chen: missing).

**Step 5 — Analyze.**
- Mean: (9200 + 8500 + 9700 + 11000) / 4 = 38400 / 4 = **9600 steps**
- Median: sorted, the values are 8500, 9200, 9700, 11000 — the middle two average to **9450 steps**

**Step 6 — Transform for the chart.** To visualize, you might sort students from most to fewest steps, or add a new column like "steps / 1000" so the chart axis reads cleanly.

Now compare with the lazy version. Keeping the duplicate and the fake zero (and dropping Dee entirely) gives (9200 + 8500 + 8500 + 0 + 11000) / 5 = 37200 / 5 = **7440 steps** — over two thousand steps below the honest answer. Same class, same day, wrong conclusion.

## The "cleaning is cheating" trap

::: misconception
Wrong belief: "Editing data before analyzing it is cheating — you should use exactly what was collected."
Correction: Fixing genuine errors — duplicates, typos, wrong units, fake zeros — makes your results *more* honest, not less. What would actually be cheating is deleting correct values just because you dislike them. The rule: fix errors, never fix answers, and write down every change you make so anyone can check your work.
:::

## Where this leads

This is the last data-analysis stop in this course, but the skill transfers everywhere. In high school science, you will clean lab measurements before graphing them. In statistics and future data-science classes, "prepare the data first" is step one of every project. And if you ever train a machine-learning model, you will discover its predictions are only as good as the cleaned data you feed it. Messy in, nonsense out — that rule follows you for life.

::: check
Q: A dataset of 30 quiz scores (max 100) contains one typo: 985. Which statistic is distorted more, the mean or the median, and why?
A: The mean, because it adds every value, so one giant number pulls it way up. The median depends only on the middle position of the sorted list, so it barely moves.
Q: A teammate wants to replace all missing values with 0 so the table "looks complete." What is the risk, and what is a better plan?
A: Zeros get treated as real measurements and drag the mean down. Better: mark the values as missing, leave them out of calculations, and report how many were missing.
:::', NULL, NULL, 8, 0.6, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_reading_intro_id_v2', 'k8_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Dari Data Mentah ke Grafik: Bersihkan Dulu, Baru Hitung', 'Pernah membaca di aplikasi game favoritmu bahwa "rata-rata pemain online 2 jam per hari"? Angka seperti itu tidak muncul begitu saja. Ada yang mengumpulkan datanya, merapikannya, lalu menghitungnya — dan di materi ini kamu akan belajar melakukan hal yang sama.

## Ide Besar: Data Mentah Hampir Selalu Berantakan

Saat kamu mengumpulkan data dari dunia nyata — lewat formulir online, wawancara, atau catatan aplikasi — hasilnya jarang langsung rapi. Ada yang salah ketik, ada jawaban kosong, ada yang menjawab dua kali, dan ada nilai yang terlalu ekstrem sampai mencurigakan (nilai seperti ini disebut **pencilan** atau *outlier*).

Karena itu, analisis data selalu melewati jalur yang sama:

1. **Kumpulkan** data mentah.
2. **Bersihkan**: perbaiki salah ketik, tangani nilai kosong, cek pencilan.
3. **Transformasi**: ubah bentuknya — urutkan, kelompokkan, atau samakan satuannya — supaya siap dihitung.
4. **Analisis**: hitung statistik seperti rata-rata (mean), median, dan modus.
5. **Visualisasikan** hasilnya dalam grafik.

Kemampuan membersihkan dan mengubah data sebelum divisualisasikan inilah inti dari standar AD-K8-2.

## Contoh Kecil: Survei Waktu Bermain Game

Kamu menyurvei 8 teman: "Berapa menit kamu bermain game kemarin?" Jawaban mentahnya:

```
60, 45, "sembilan puluh", 30, 60, (kosong), 600, 75
```

Ayo bersihkan satu per satu:

- "sembilan puluh" → ubah menjadi angka: **90**
- (kosong) → temanmu lupa mengisi; jangan ditebak, keluarkan dari hitungan
- 600 → sepuluh jam bermain? Cek ulang ke orangnya — ternyata salah ketik, maksudnya **60**

Data bersih: 30, 45, 60, 60, 60, 75, 90. Sekarang statistiknya bisa dihitung:

- Rata-rata = 420 ÷ 7 = **60 menit**
- Median (nilai tengah setelah data diurutkan) = **60 menit**

Logika pembersihannya bisa ditulis sebagai pseudocode:

```
untuk setiap jawaban dalam data:
    jika jawaban kosong -> tandai sebagai hilang
    jika jawaban berupa kata -> ubah menjadi angka
    jika jawaban sangat ekstrem -> periksa ulang sumbernya
```

::: check
Q: Mengapa data harus dibersihkan dulu sebelum dihitung rata-ratanya?
A: Karena salah ketik, nilai kosong, dan pencilan bisa membuat hasil hitungan menyesatkan — misalnya angka 600 yang ternyata salah ketik akan menaikkan rata-rata secara tidak adil.
Q: Data bersih waktu bermain adalah 30, 45, 60, 60, 60, 75, 90. Berapa modusnya, dan apa artinya?
A: Modusnya 60 menit — nilai yang paling sering muncul, artinya bermain 60 menit adalah jawaban paling umum di kelompok itu.
:::

Di materi pendalaman, kamu akan mengolah kumpulan data yang lebih besar dan lebih berantakan — lengkap dengan duplikat, pencilan, dan keputusan memilih grafik.', NULL, NULL, 5, 0.3, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_diagram_id_v2', 'k8_data_collection', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Jalur Analisis Data dalam Satu Gambar', 'Semua proyek analisis data — dari survei kelas sampai statistik di dalam game — mengikuti jalur yang sama. Diagram ini menunjukkan perjalanan data dari kondisi mentah sampai menjadi grafik.

```
+------------+   +------------+   +--------------+
| DATA       |   | BERSIHKAN  |   | TRANSFORMASI |
| MENTAH     |-->| x duplikat |-->| urutkan      |
| survei/    |   | x kosong   |   | kelompokkan  |
| aplikasi   |   | ? pencilan |   +------+-------+
+------------+   +------------+          |
                                         v
  +---------------+           +----------------+
  | VISUALISASI   |           | ANALISIS       |
  | grafik batang |<----------| rata-rata,     |
  | grafik garis  |           | median, modus  |
  +---------------+           +----------------+
```

Legend:

- Kotak = satu tahap dalam jalur analisis data
- --> dan v = arah aliran data dari tahap ke tahap
- <-- = hasil analisis diteruskan untuk digambar
- x = entri bermasalah yang dibuang atau diperbaiki
- ? = nilai pencilan yang harus dicek kebenarannya dulu

Cara membaca diagram:

1. Mulai dari kotak DATA MENTAH: hasil survei atau catatan aplikasi masuk apa adanya, lengkap dengan kesalahannya.
2. Di tahap BERSIHKAN, duplikat dan nilai kosong ditangani (tanda x), sedangkan pencilan dicek dulu (tanda ?), bukan langsung dihapus.
3. Tahap TRANSFORMASI menyiapkan data: diurutkan atau dikelompokkan supaya mudah dihitung.
4. Data yang sudah rapi mengalir turun ke tahap ANALISIS untuk dihitung rata-rata, median, dan modusnya.
5. Hasil hitungan diteruskan ke VISUALISASI dan digambar sebagai grafik batang atau garis.

::: tip
Saat bekerja di spreadsheet, urutkan dulu datamu dari terkecil ke terbesar. Nilai kosong, salah ketik, dan pencilan akan langsung terlihat berkumpul di ujung atas atau bawah daftar — jauh lebih cepat daripada memeriksa baris satu per satu.
:::', NULL, NULL, 3, 0.4, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_audio_id_v2', 'k8_data_collection', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Mengapa Data Harus Dibersihkan Sebelum Dihitung', NULL, NULL, 'Bayangkan kamu dan kelompokmu mendapat proyek dari sekolah: mencari tahu jajanan apa yang paling laku di kantin, supaya kantin bisa menambah stok dengan tepat. Selama lima hari kalian mencatat berapa porsi setiap jajanan yang terjual. Kedengarannya gampang, kan? Tapi begitu semua catatan dikumpulkan, masalahnya mulai muncul.

Di hari Selasa, ada dua catatan untuk risol dengan angka yang sama, karena dua anggota kelompok ternyata mencatat penjualan yang sama. Di hari Rabu, kolom penjualan bakwan kosong, karena pencatatnya sakit. Dan di hari Kamis, tertulis sembilan ratus porsi siomay, padahal biasanya hanya sekitar sembilan puluh. Kalau angka-angka ini langsung kamu masukkan ke grafik, kesimpulanmu bisa salah besar.

Inilah ide penting dalam analisis data: data mentah hampir selalu berantakan, jadi harus dibersihkan dulu sebelum dihitung dan divisualisasikan. Membersihkan data artinya tiga hal. Pertama, hapus data yang tercatat dua kali, supaya tidak dihitung dobel. Kedua, tangani nilai yang kosong dengan jujur. Jangan asal diisi nol, karena bakwan bukannya tidak laku sama sekali, datanya saja yang tidak tercatat. Ketiga, periksa nilai yang terlalu ekstrem, yang biasa disebut pencilan. Angka sembilan ratus itu perlu ditanyakan ulang ke pencatatnya. Kalau ternyata salah ketik, perbaiki. Kalau ternyata benar, misalnya karena hari itu ada acara sekolah, biarkan saja, tapi ingat bahwa nilai itu akan menarik rata-rata ke atas.

Setelah data bersih, barulah kamu menghitung statistiknya. Rata-rata memberi tahu penjualan tipikal setiap hari. Median, yaitu nilai tengah setelah data diurutkan, lebih aman dipakai kalau ada pencilan yang nyata. Terakhir, kamu bisa mengubah bentuk datanya, misalnya mengelompokkan penjualan per jenis jajanan, lalu menggambarnya menjadi grafik batang yang jelas dan meyakinkan.

Jadi urutannya selalu sama: kumpulkan, bersihkan, ubah bentuk, hitung, baru gambarkan. Urutan ini berlaku untuk proyek kantin, data game, sampai penelitian sungguhan.

Sekarang satu pertanyaan singkat untukmu. Kalau ada satu hari yang datanya kosong, mengapa kamu tidak boleh langsung mengisinya dengan nol? Jawabannya: karena nol berarti benar-benar tidak ada penjualan, padahal yang terjadi hanyalah datanya tidak tercatat. Mengisi nol akan menyeret rata-rata turun dan membuat kesimpulanmu tidak menggambarkan kenyataan.', 4, 0.45, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_data_collection_reading_deep_id_v2', 'k8_data_collection', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Studi Kasus: Merapikan Data Tantangan Jalan Kaki', 'Kamu sudah tahu jalurnya: kumpulkan → bersihkan → transformasi → analisis → visualisasikan. Sekarang kita terapkan pada data yang lebih besar dan lebih "kotor".

## Contoh Lengkap: Tantangan Jalan Kaki Kelas

Kelasmu mengadakan tantangan jalan kaki selama seminggu. Setiap siswa melaporkan rata-rata langkah hariannya lewat formulir online. Sepuluh baris data mentah masuk:

| Nama | Langkah per hari |
| --- | --- |
| Aca | 7500 |
| Bima | 6000 |
| Bima | 6000 |
| Cika | 85000 |
| Dedi | (kosong) |
| Eno | 4.500 |
| Fira | 9000 |
| Gani | 7000 |
| Hana | 8000 |
| Iman | 6500 |

**Langkah 1 — hapus duplikat.** Bima mengisi formulir dua kali. Hitung dia satu kali saja; kalau tidak, datanya "memberi suara" dobel.

**Langkah 2 — tangani nilai kosong.** Dedi tidak mengisi angka. Jangan diganti 0 (dia bukan tidak berjalan sama sekali!) — tanyakan ulang, atau keluarkan barisnya dari hitungan.

**Langkah 3 — periksa pencilan.** 85.000 langkah itu sekitar 60 km sehari — hampir mustahil untuk siswa. Setelah dikonfirmasi ke Cika, ternyata jarinya kepencet: maksudnya **8.500**.

**Langkah 4 — samakan format.** "4.500" milik Eno ditulis dengan titik; samakan menjadi 4500 agar bisa dihitung komputer.

Data bersih (8 siswa): 4500, 6000, 6500, 7000, 7500, 8000, 8500, 9000.

**Langkah 5 — transformasi untuk grafik.** Kelompokkan ke kategori supaya grafik batangnya mudah dibaca:

| Kategori | Rentang langkah | Jumlah siswa |
| --- | --- | --- |
| Santai | di bawah 5000 | 1 |
| Aktif | 5000-7999 | 4 |
| Super aktif | 8000 ke atas | 3 |

**Langkah 6 — hitung statistik.**

- Rata-rata = 57.000 ÷ 8 = **7.125 langkah**
- Median = (7000 + 7500) ÷ 2 = **7.250 langkah**

Logika pembersihannya dalam pseudocode:

```
data_bersih = []
untuk setiap baris dalam data_mentah:
    jika baris sudah ada di data_bersih -> lewati
    jika kolom langkah kosong -> catat, jangan isi 0
    jika langkah > 40000 -> konfirmasi ke pemiliknya
    masukkan baris ke data_bersih
```

## Miskonsepsi yang Sering Terjadi

::: misconception
Keyakinan yang salah: "Nilai kosong atau aneh boleh langsung dihapus, atau diisi 0, supaya hitungan cepat selesai."
Yang benar: setiap nilai janggal harus diperiksa dulu. Nilai kosong yang diisi 0 akan menyeret rata-rata turun padahal orangnya hanya lupa mengisi. Pencilan yang ternyata salah ketik harus diperbaiki, bukan dibuang. Tetapi kalau pencilan itu nyata — misalnya ada siswa yang memang atlet jalan cepat — datanya tetap sah; gunakan median agar analisismu tidak terlalu terpengaruh satu nilai ekstrem.
:::

## Ke Mana Keterampilan Ini Membawamu

Jalur bersihkan-transformasi-analisis yang kamu latih di sini adalah kebiasaan kerja yang sama dengan yang dipakai ilmuwan data sungguhan. Apa yang kamu pelajari di sini langsung terpakai saat mengolah hasil percobaan IPA, merapikan spreadsheet proyek kelompok, dan nanti saat belajar sains data serta pemrograman analisis di jenjang berikutnya. Bahkan saat membaca berita berisi grafik, kamu jadi terbiasa bertanya: "Datanya sudah dibersihkan dengan jujur, belum?"

::: check
Q: Seorang temanmu mengisi nilai kosong milik Dedi dengan 0, lalu menghitung ulang rata-rata. Apa akibatnya pada hasil analisis?
A: Rata-rata anjlok menjadi 57.000 ÷ 9 ≈ 6.333 langkah, padahal Dedi bukan tidak berjalan — datanya hanya tidak tercatat. Kesimpulan kelas jadi tidak menggambarkan kenyataan.
Q: Kapan median lebih tepat dipakai daripada rata-rata?
A: Saat ada pencilan yang nyata dan tidak bisa "diperbaiki" — median hampir tidak terpengaruh nilai ekstrem, jadi lebih mewakili data yang tipikal.
:::', NULL, NULL, 8, 0.6, '["k5_data_collection"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_intro_en_v2', 'k8_modularity', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Modular Programs: Build Big Things from Small Parts', 'Open a game on your phone and you''re running code written by dozens of people who never touched each other''s work. How is that possible without total chaos? It''s the same trick that saves a good group project: split the job into parts, give each part one clear role, and agree on exactly how the parts connect.

## The Big Idea: Modules and Layers

A **module** is a chunk of a program with one clear job and a simple "front door" — you hand it what it needs, and it hands back a result. You don''t need to know what happens inside. Hiding the messy details behind a simple name is called **abstraction**.

Big programs stack modules in **layers**:

- **Top layer:** the main program. It reads like a plan: do this, then this.
- **Middle layer:** feature modules that do the real work.
- **Bottom layer:** small helpers that the modules share.

Here''s a mini quiz game built this way:

```
main:
  score = 0
  repeat 3 times:
    q = pick_question()
    guess = ask_player(q)
    if check_answer(q, guess):
      score = score + 10
  show_result(score)
```

Notice that `main` never explains *how* questions get picked or answers get checked. It just calls modules by name, like a project leader handing out jobs.

Now follow along with a real change. Players complain that typing "PARIS" gets marked wrong when the answer is "paris". Where do you fix it? Only inside `check_answer`:

```
check_answer(q, guess):
  return lowercase(guess) == lowercase(q.answer)
```

One module changed. `main`, `pick_question`, and `show_result` never even notice. That''s the power move of modularity: any module can be fixed, upgraded, or completely rewritten without breaking the rest of the program — as long as its front door stays the same.

::: check
Q: Why can we rewrite the inside of check_answer without touching main?
A: Because main only depends on check_answer''s front door — its name, its inputs, and its output. As long as those stay the same, the inside can change freely.
Q: What does abstraction hide, and what does it leave visible?
A: It hides the messy details of how a module works and leaves visible only a simple name and interface that other code can call.
:::

In the deeper material, you''ll build a whole game out of modules — and hunt down a bug that hides in a different module than the one where it shows up.', NULL, NULL, 5, 0.3, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_diagram_en_v2', 'k8_modularity', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'A Modular App, Layer by Layer', 'Every big app is a stack of layers: a plan on top, feature modules in the middle, and tiny helpers at the bottom. Here''s that stack for a simple music player.

```
+--------------------------------------------------+
| LAYER 1: MAIN PROGRAM                            |
| "start music app, play workout mix"              |
+------------+---------------------+---------------+
             |                     |
             v                     v
+----------------------+  +----------------------+
| LAYER 2: PLAYLIST    |  | LAYER 2: PLAYER      |
| pick_next_song()     |  | play(song)           |
+----------+-----------+  +-----------+----------+
           |                          |
           v                          v
+--------------------------------------------------+
| LAYER 3: HELPERS                                 |
| shuffle(list)  load_file(name)  set_volume(n)    |
+--------------------------------------------------+
```

Legend

- **Box** = one module or layer with a single clear job
- **| and v** = a call: the upper part asks the lower part to do work and gets a result back
- **name()** = the module''s front door (its interface), the only part other layers see
- **LAYER 1 to 3** = top is the overall plan, bottom is the fine detail

How to read it

1. Start at Layer 1. It reads like a to-do list and knows nothing about how songs are stored or played.
2. Follow an arrow down: Layer 1 calls `pick_next_song()` and simply trusts it to return a song.
3. The Playlist module does its job by calling helpers below it, like `shuffle(list)`.
4. Results flow back **up** the same arrows: helpers answer modules, modules answer main.
5. When debugging, ride the arrows: a wrong song on screen at Layer 1 might come from a mistake made down in `shuffle(list)` and passed upward.

::: tip
Design top-down, build bottom-up: write Layer 1 first, pretending every module below already exists. It forces you to decide each module''s front door before you write a single line of its insides.
:::', NULL, NULL, 3, 0.4, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_audio_en_v2', 'k8_modularity', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'How Modules Keep Big Programs Under Control', NULL, NULL, 'Today let''s talk about modularity, the art of building one big program out of small parts that each do one job well.

Imagine your class is putting on a talent show. Nobody sane tries to run the whole thing alone. You split into teams. There''s a stage crew, a ticket team, and a snack stand. Each team has one clear job, and each team has a simple way to talk to the others. The organizer doesn''t need to know how the stage crew hangs the lights. She just says the show starts at seven, be ready. That simple agreement between teams is called an interface, and ignoring the details behind it is called abstraction.

Programs work exactly the same way. A big game is not one giant wall of code. It''s a stack of modules. At the top sits a main program that reads like a plan. Below it sit modules for handling input, running the rules, and drawing the screen. Below those sit tiny helpers. Each layer only needs to know the front door of the layer below it, never the insides. That means you can fix or completely rewrite one module, and as long as its front door stays the same, nothing else breaks.

Now for the tricky part, which is debugging. On show night, the snack stand runs out of juice. Is that the snack team''s fault? Maybe not. Maybe the ticket team reported fifty guests when they actually sold ninety, so the snack team bought too little. The problem appeared at the snack stand, but it started at the ticket table. Bugs in modular programs travel the same way. A wrong value gets created in one module, gets passed along, and only becomes visible somewhere else. So a good debugger tests each module alone, then checks the handoffs between them.

Here''s your recap question. When a bug shows up in one module, why shouldn''t you search only that module? Here''s the answer. Because modules pass data to each other, a mistake made early can travel downstream and appear later. Test each module on its own, and if they all pass, the bug is hiding in a handoff between them.', 4, 0.45, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_deep_en_v2', 'k8_modularity', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Debugging Across Modules: Follow the Data', 'Quick recap: a modular program is built from parts that each have one clear job and a simple front door (an **interface**), stacked in layers so each layer can ignore the details below it.

## Worked Example: Space Dodger, Module by Module

Let''s build a game where a ship dodges falling asteroids. Step one in modular design: write the top layer first, as if the modules already exist.

```
main:
  ship = setup_ship()
  score = 0
  game_over = false
  repeat until game_over:
    key = get_input()
    ship = move_ship(ship, key)
    if hit_asteroid(ship):
      game_over = true
    update_score(score, 1)
    draw_screen(ship, score)
```

Each name is a module with one job: `get_input` handles the keyboard, `move_ship` and `hit_asteroid` handle the rules, `draw_screen` handles the display. Organizing a program into procedures with parameters like this is exactly the skill described in the CSTA 2-AP-14 standard.

You build each module, run the game... and the score on screen never leaves 0. Time to debug **across** modules. The rule: follow the data.

1. **Start at the symptom.** `draw_screen` shows 0. Test it alone: call `draw_screen(ship, 50)`. It shows 50. This module is fine.
2. **Move one handoff upstream.** What feeds the score into `draw_screen`? The variable `score` in `main`.
3. **Test the producer.** Call `update_score(0, 1)` by itself. It returns 1. This module is fine too!
4. **Check the handoff itself.** Look at the call in `main`: it says `update_score(score, 1)` — it computes the new score and then *throws the answer away*. It should be `score = update_score(score, 1)`.

Both modules passed their solo tests. The bug lived in the **connection** between them. That''s the big debugging lesson of modular programs: test each module alone, then test the handoffs.

## The Misconception That Wastes Debugging Time

::: misconception
Wrong belief: "The bug must be inside the module where the problem shows up, so that''s the only place to look."
Reality: modules pass data to each other, so a mistake made early in the chain travels downstream and only becomes *visible* later. A broken score display usually isn''t a display bug. Test each module on its own with known inputs; if every module passes, inspect the handoffs — the calls, the arguments going in, and what happens to the values coming back.
:::

## Where This Leads

There''s no next concept stacked on this one in your curriculum — this is where modularity levels up into real practice, and everything here transfers straight to real-world programming. Professional apps are thousands of modules connected by interfaces, and programmers spend much of their day doing exactly what you just did: trusting front doors, testing parts in isolation, and tracing data across handoffs. The same habits carry into high-school CS, into using code libraries written by total strangers, and into any team project where your module has to click into someone else''s.

::: check
Q: Your drawing module and your scoring module both pass their solo tests, but the game still shows the wrong score. Where do you look next, and why?
A: At the handoffs between modules: whether main passes the right arguments into each call, whether it stores the returned values, and whether the calls happen in the right order. Solo tests prove the insides work, so a remaining bug must live in the connections.
Q: You rewrite hit_asteroid with fancier, more accurate math. What must stay exactly the same so main keeps working without edits?
A: Its interface: the module''s name, the inputs it accepts (the ship), and the kind of result it returns (true or false). Main depends only on that front door, never on the insides.
:::', NULL, NULL, 8, 0.6, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_intro_id_v2', 'k8_modularity', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Membangun Program dari Modul-Modul Kecil', 'Coba pikirkan game atau aplikasi chat favoritmu. Aplikasi sebesar itu tidak ditulis sebagai satu gulungan kode raksasa oleh satu orang, melainkan disusun dari puluhan bagian kecil yang dikerjakan oleh tim yang berbeda-beda. Kalau kamu paham cara kerja bagian-bagian ini, kamu bisa membangun programmu sendiri dengan cara yang sama rapinya.

## Ide Besar: Program Tersusun dari Modul

**Modul** adalah bagian program yang punya satu tugas jelas, misalnya "periksa jawaban" atau "tampilkan skor". Setiap modul bisa dibuat, diuji, dan diperbaiki sendiri-sendiri, lalu digabungkan menjadi program utuh — mirip kerja kelompok yang membagi tugas dengan adil.

Yang membuat modul benar-benar hebat adalah **abstraksi**: kamu bisa *memakai* sebuah modul tanpa perlu tahu isi dalamnya. Sama seperti kamu menekan tombol "kirim" di aplikasi chat tanpa perlu tahu bagaimana pesan berjalan lewat internet. Dalam program besar, modul-modul tersusun menjadi **lapisan abstraksi**: lapisan atas memanggil lapisan di bawahnya, dan setiap lapisan menyembunyikan detail kerjanya sendiri.

### Contoh: Game Kuis Sains

Perhatikan program utama sebuah game kuis:

```
program KuisSains
  soal = ambilSoal()
  jawaban = tanyaPemain(soal)
  benar = periksaJawaban(soal, jawaban)
  perbaruiSkor(benar)
```

Program utama ini terbaca seperti daftar isi: empat baris, empat modul, masing-masing satu tugas. Sekarang intip isi salah satu modulnya:

```
fungsi periksaJawaban(soal, jawaban)
  kembalikan jawaban == soal.kunci
```

Program utama tidak peduli *bagaimana* periksaJawaban bekerja — ia hanya percaya bahwa modul itu mengembalikan benar atau salah. Suatu hari kamu bisa memperbarui isinya (misalnya agar huruf besar-kecil tidak berpengaruh) tanpa mengubah satu baris pun di program utama. Itulah kekuatan abstraksi.

::: check
Q: Apa ciri utama sebuah modul yang baik?
A: Punya satu tugas yang jelas, sehingga bisa dibuat, diuji, dan diperbaiki terpisah dari bagian program yang lain.
Q: Mengapa program utama KuisSains tidak perlu diubah saat isi fungsi periksaJawaban diperbaiki?
A: Karena program utama hanya memanggil nama modul dan memakai hasilnya. Selama nama dan jenis hasilnya tetap sama, isi modul bebas diubah — itulah abstraksi.
:::

Di materi pendalaman, kamu akan berlatih keterampilan detektif yang paling berguna bagi programmer: melacak bug yang bersembunyi di antara modul-modul.', NULL, NULL, 5, 0.3, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_diagram_id_v2', 'k8_modularity', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Tiga Lapisan Abstraksi di Aplikasi Pemutar Musik', 'Program modular biasanya disusun berlapis, seperti kue lapis: setiap lapisan punya tugas sendiri dan hanya "berbicara" dengan lapisan tepat di bawahnya. Diagram ini menunjukkan tiga lapisan abstraksi pada sebuah aplikasi pemutar musik sederhana.

```
+--------------------------------------------+
|        LAPISAN TAMPILAN (UI)               |
|   [ tombolPutar ]    [ daftarLagu ]        |
+---------------------+----------------------+
                      |  panggil fungsi
                      v
+--------------------------------------------+
|        LAPISAN LOGIKA                      |
|   [ putarLagu() ]    [ acakUrutan() ]      |
+---------------------+----------------------+
                      |  minta / kirim data
                      v
+--------------------------------------------+
|        LAPISAN DATA                        |
|   [ bacaLagu() ]     [ simpanDaftar() ]    |
+--------------------------------------------+
```

Legend:
- Kotak besar = satu lapisan abstraksi
- [ nama ] = modul (fungsi) yang tinggal di lapisan itu
- | dan v = arah panggilan, dari lapisan atas ke lapisan di bawahnya
- Tulisan di samping garis = apa yang melewati perbatasan antar-lapisan

Cara membaca diagram:

1. Mulai dari lapisan paling atas: inilah bagian yang dilihat dan disentuh pemakai, seperti tombol putar dan daftar lagu.
2. Saat tombolPutar ditekan, lapisan tampilan tidak memutar musik sendiri; ia memanggil putarLagu() di lapisan logika.
3. putarLagu() juga tidak membuka file sendiri; ia meminta bacaLagu() di lapisan data untuk melakukannya.
4. Data lagu lalu mengalir balik ke atas melewati perbatasan yang sama, sampai musik terdengar.
5. Perhatikan: setiap lapisan hanya mengenal lapisan tepat di bawahnya. Lapisan tampilan bahkan tidak tahu lapisan data itu ada — itulah abstraksi berlapis.

::: tip
Saat program berlapis seperti ini error, telusuri panah dari atas ke bawah dan periksa data di setiap perbatasan. Perbatasan pertama tempat data mulai terlihat aneh menunjukkan modul mana yang perlu kamu buka dan perbaiki.
:::', NULL, NULL, 3, 0.4, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_audio_id_v2', 'k8_modularity', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Modularitas: Kerja Tim di Dalam Program', NULL, NULL, 'Bayangkan kelasmu mendapat tugas membuat video pendek untuk pentas seni. Kalian membagi pekerjaan: satu orang menulis naskah, satu orang mengambil gambar dengan kamera, satu orang mengedit, dan satu orang mengurus musik. Setiap orang punya satu tugas yang jelas, dan hasil kerjanya diserahkan ke orang berikutnya. Menariknya, si editor tidak perlu tahu pengaturan kamera yang dipakai. Dia hanya perlu menerima rekaman yang bagus. Begitu juga si penulis naskah tidak perlu paham aplikasi edit video.

Program komputer yang baik bekerja dengan cara yang sama persis. Program besar dipecah menjadi modul, yaitu bagian-bagian kecil yang masing-masing punya satu tugas jelas. Ada modul yang mengurus tampilan, ada yang menghitung, ada yang menyimpan data. Setiap modul bisa dibuat dan diuji sendiri-sendiri. Dan seperti tim video tadi, satu modul bisa memakai modul lain tanpa perlu tahu isi dalamnya. Kemampuan menyembunyikan detail ini disebut abstraksi. Modul-modul juga sering disusun bertingkat, dan susunan ini disebut lapisan abstraksi. Lapisan atas memanggil lapisan di bawahnya, dan setiap lapisan menyimpan rahasia dapurnya masing-masing.

Sekarang bagian serunya: mencari kesalahan. Misalnya video akhir kalian ternyata tidak ada suaranya. Apakah editornya yang salah? Belum tentu. Cara paling cerdas adalah memeriksa hasil di setiap serah terima. Dengarkan dulu rekaman mentah dari kamera. Kalau rekaman mentahnya sudah tidak bersuara, masalahnya ada di proses pengambilan gambar, bukan di proses edit. Kalau rekaman mentahnya normal, barulah kita curiga pada tahap edit. Men-debug program modular bekerja persis seperti ini. Kesalahan yang terlihat di satu modul sering kali bersumber dari modul sebelumnya. Jadi periksa data di setiap perbatasan modul, temukan titik pertama data mulai salah, dan di situlah modul yang perlu diperbaiki.

Pertanyaan penutup untukmu. Kalau hasil akhir sebuah program salah, apakah bug pasti berada di modul yang menampilkan hasil itu? Jawabannya, belum tentu. Modul itu mungkin hanya menerima data yang sudah salah dari modul sebelumnya. Cara memastikannya adalah memeriksa data di setiap perbatasan modul, sampai kamu menemukan tempat pertama data berubah menjadi salah.', 4, 0.45, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_modularity_reading_deep_id_v2', 'k8_modularity', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Melacak Bug Lintas Modul: Kasus Diskon di Aplikasi Kantin', 'Program modular tersusun dari modul-modul bertugas tunggal yang saling memanggil lewat lapisan abstraksi. Sekarang saatnya keterampilan tingkat lanjut: menemukan bug yang gejalanya muncul di satu modul, padahal sumbernya ada di modul lain.

## Studi Kasus: Bug Diskon di Aplikasi KantinKu

Bayangkan aplikasi pemesanan jajan sekolah bernama KantinKu dengan empat modul:

```
program KantinKu
  tampilkanMenu()
  tambahKeKeranjang("risoles", 2)
  tambahKeKeranjang("es teh", 1)
  total = hitungTotal(keranjang)
  bayar(total)
```

Laporan bug masuk: risoles sedang promo dari 3000 menjadi 2000, tetapi total belanja tetap memakai harga lama. Pesanan di atas menampilkan total 9000, padahal seharusnya 7000.

Ikuti langkah debug lintas modul berikut:

1. **Reproduksi bug.** Jalankan pesanan yang sama. Benar, total 9000.
2. **Periksa perbatasan modul.** Cetak isi keranjang tepat setelah tambahKeKeranjang berjalan. Hasilnya: risoles tersimpan dengan harga 3000. Data sudah salah *sebelum* masuk ke hitungTotal!
3. **Bebaskan tersangka yang tidak bersalah.** Uji hitungTotal sendirian dengan keranjang buatan yang berisi harga benar. Hasilnya tepat. Berarti hitungTotal aman.
4. **Buka modul sumber.** Kini tinggal satu tersangka: tambahKeKeranjang.

Isi tambahKeKeranjang ternyata seperti ini:

```
fungsi tambahKeKeranjang(nama, jumlah)
  harga = daftarHargaLama[nama]    // <- bug!
  keranjang.tambah(nama, harga, jumlah)
```

Modul ini masih mengambil harga dari daftar lama, bukan daftar harga promo. Ganti satu baris menjadi daftarHargaTerbaru[nama], dan bug hilang — tanpa menyentuh tiga modul lainnya.

Pelajaran pentingnya: **gejala muncul di hilir, tetapi sumbernya sering ada di hulu.** Periksa data di setiap perbatasan modul untuk menemukan titik pertama data mulai salah.

## Miskonsepsi Umum

::: misconception
Anggapan keliru: "Kalau angka yang salah keluar dari hitungTotal, berarti bug pasti ada di dalam hitungTotal."
Faktanya, modul tempat gejala terlihat belum tentu modul sumber masalah. hitungTotal bisa bekerja sempurna tetapi menerima data yang sudah rusak dari modul sebelumnya. Karena itu, lacak aliran data dari modul ke modul, dan uji tiap modul dengan input buatan sebelum menuduhnya bersalah.
:::

## Ke Mana Keterampilan Ini Membawamu

Kemampuan merancang program modular dengan lapisan abstraksi — bagian dari standar AP-K8-5 — adalah bekal langsung untuk proyek yang lebih besar. Saat nanti kamu memakai bahasa pemrograman sungguhan, kamu akan bertemu fungsi, library, dan API: semuanya adalah modul buatan orang lain yang kamu pakai lewat abstraksi, tanpa perlu tahu isi dalamnya. Cara berpikir "cek data di perbatasan" yang kamu latih di sini juga menjadi cara para profesional men-debug sistem besar, dari game online sampai aplikasi bank.

::: check
Q: Skor di game buatan timmu kadang tampil minus, dan modul tampilkanSkor yang menampilkannya. Apa langkah pertama yang paling tepat?
A: Periksa nilai skor yang diterima tampilkanSkor di perbatasan modul. Kalau nilainya sudah minus sebelum masuk, sumber bug ada di modul penghitung skor, bukan di tampilkanSkor.
Q: Mengapa menguji satu modul dengan input buatan lebih cepat menemukan bug daripada menjalankan seluruh program berulang-ulang?
A: Input buatan mengisolasi modul itu: kamu tahu persis data yang masuk. Kalau hasilnya salah, bug pasti ada di modul itu; kalau hasilnya benar, modul itu bisa dicoret dari daftar tersangka.
:::', NULL, NULL, 8, 0.6, '["k5_modularity", "k8_algorithms"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_reading_intro_en_v2', 'k8_networks_communication', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'How Your Messages Travel the Internet', 'You tap send on a meme, and two seconds later a friend across town is laughing at it. That picture left your phone, crossed Wi-Fi signals and cables, and rebuilt itself perfectly on another screen. It is not magic — it is a delivery system with strict rules, and once you know them, mysteries like game lag suddenly make sense.

## The Internet Is a Giant Delivery Service

Three ideas run the whole show:

- **IP addresses.** Every device on a network gets an address — a house number for the internet. It looks something like `192.168.1.7`. No address, no delivery.
- **Packets.** Networks never send a photo in one giant chunk. They chop it into small numbered pieces called *packets*, ship each piece separately, and rebuild everything at the other end.
- **Protocols.** A protocol is an agreement about how to communicate: how addresses are written, how to say "got it," and what to do when a piece goes missing. Your phone and a server in another country can cooperate because both follow the same rules — the way a group project only works when everyone agrees on how to share files.

### A tiny example you can trace

Say you text your project group: "Meet in the library at 4!" Your phone roughly does this:

```
message = "Meet in the library at 4!"
packets = split(message into small pieces)

for each packet in packets:
    packet.from   = my_address
    packet.to     = friend_address
    packet.number = position (1, 2, 3, ...)
    send(packet)
```

Each packet travels on its own — packet 2 might even take a different route than packet 1. Your friend''s phone collects them, sorts them by number, and shows the full message. If packet 3 never arrives, the phone asks for packet 3 again — not the whole message.

One more rule matters: **security**. Your packets pass through machines you do not own, so good protocols *encrypt* (scramble) the contents. Strangers along the route can tell data went by, but they cannot read it.

::: check
Q: Why do networks split a photo into packets instead of sending it as one big piece?
A: Small numbered pieces can share the network fairly, take different routes, and if one gets lost, only that piece is resent instead of the whole photo.
Q: What labels does every packet need so it can arrive and be put back in order?
A: A destination IP address (plus the sender''s address for replies) and a number showing its position in the original message.
:::

Next, you will follow a single game move through routers, a handshake, and a lost packet — and see exactly why encryption keeps snoopers guessing.', NULL, NULL, 5, 0.3, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_diagram_en_v2', 'k8_networks_communication', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Trip One Message Takes', 'Every message you send follows a path like the one below — out of your device, through a chain of routers, to its destination, and back. Trace one short message''s trip from a phone to a game server.

```
[Your Phone]                 [Game Server]
 192.168.1.7                  203.0.113.9
     |                             ^
     | P1 P2 P3                    |
     v                             |
+---------+   +----------+   +----------+
|  Home   |==>| Router A |==>| Router B |
| Router  |   +----------+   +----------+
+---------+
     ^
     +==== "Got it!" (ACK) reply comes back
```

**Legend**

- `[Your Phone]` and `[Game Server]` — devices, each with its own IP address shown below it
- `P1 P2 P3` — one message split into three numbered packets
- Boxes — routers, the machines that pass packets along
- `==>` — packets moving toward the destination
- `|`, `v`, `^` — the direction the data is flowing
- `(ACK)` — a tiny confirmation packet meaning "got it"

**How to read it**

1. The phone splits the message into packets P1, P2, and P3, stamping each with its own address (from), the server''s address (to), and a number.
2. Packets leave through the home router — the doorway between your house''s network and the internet.
3. Routers A and B each read only the *to* address and forward the packets onward. Different packets may take different paths.
4. The server collects the packets and uses the numbers to rebuild the message in the right order.
5. The server fires back a tiny ACK. If any packet went missing, the phone learns it here and resends just that piece.

::: tip
Next time a video call freezes, picture this diagram: some packets are arriving late or getting lost along the way. Waiting a few seconds gives the protocol time to resend them — often faster than hanging up and rejoining.
:::', NULL, NULL, 3, 0.4, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_audio_en_v2', 'k8_networks_communication', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'The Internet''s Delivery Rules', NULL, NULL, 'Imagine you just filmed a short birthday video for your cousin in another city, and you hit send. What actually happens in the next two seconds?

First, your phone does not send the video in one piece. It chops it into thousands of tiny chunks called packets. Think of it like mailing a very long story written across numbered postcards. Every postcard gets three things: your cousin''s address, your return address, and a number that shows where it belongs in the story.

On the internet, those addresses are called IP addresses. Every phone, laptop, and game console on a network has one, like a house number for devices. Without an address, nothing can be delivered.

Next, the packets start hopping. They travel from your phone to your home router, and then through a chain of routers spread across the internet. Routers work like post offices. They never read your story. They only read the address on each packet and pass it toward the next stop. Different packets can even take completely different routes and still end up in the same place.

When the packets arrive, your cousin''s phone sorts them by number and rebuilds the video. If postcard number fifty-three never shows up, her phone notices the gap and asks your phone to resend just that one piece, not the whole video. All of this works because both phones follow the same shared rules, called protocols. A protocol is simply an agreement about how to talk: how to address things, how to confirm delivery, and what to do when something gets lost.

One last rule keeps you safe. Good apps encrypt your packets, which means they scramble them into a secret code. Machines along the route can tell that data passed by, but they cannot read your video. And remember that people can fake who a message is from, so a strange link asking for your password deserves suspicion, no matter how official it looks.

Here is your recap question. When a video is split into packets, how does the receiving phone put it back together, and what happens if one packet goes missing? The answer: every packet carries a number, so the phone sorts them into order, and if a number is missing, it simply asks for that one packet to be sent again.', 4, 0.45, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_reading_deep_en_v2', 'k8_networks_communication', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Packets, Addresses, and Staying Safe Online', 'Quick recap: the internet moves data by chopping it into addressed, numbered packets, and devices everywhere cooperate by following shared protocols.

## Worked example: one jump in an online game

You press the jump button in a multiplayer game. Here is the full trip, step by step.

1. **Find the address.** Your game knows the server''s name, `play.blockworld.example`, but names are for humans. A lookup service called **DNS** acts like the internet''s contact list and returns the server''s IP address: `203.0.113.9`.
2. **Shake hands.** Before real data flows, the two computers run a quick handshake — roughly "Hello?" / "Hello, I hear you." / "Great, let''s go." Both sides now agree a connection exists. Modeling exchanges like this is exactly what the CSTA standard 2-NI-04 asks you to be able to do.
3. **Pack and stamp.** Your jump becomes a small chunk of data, split into packets. Each one is stamped with your IP, the server''s IP, and a sequence number — then encrypted so only the server can read it.
4. **Hop by hop.** Routers between you and the server read only the *to* address and forward each packet toward its destination. Different packets may take different routes.
5. **Rebuild and confirm.** The server sorts arriving packets by number. In pseudocode:

```
expected = 1
when a packet arrives:
    if packet.number == expected:
        keep it
        expected = expected + 1
    else:
        request_again(expected)
```

6. **Recover from loss.** If packet 3 got dropped by a busy router, the server requests just packet 3 again. Your device resends it, the server confirms with a tiny "got it" reply (an **ACK**), and your character jumps — all in a few milliseconds.

Notice the security built in along the way: encryption keeps the contents private, and the handshake helps make sure you are talking to the machine you think you are. That second idea matters for *you* too. A packet carries a real sender address, but an email can display any name it wants — that is how **phishing** works: a message pretending to be from your game or school, trying to trick you into typing your password. Strong, unique passwords plus healthy suspicion of "urgent" links are your personal protocol.

## A belief worth deleting

::: misconception
Wrong belief: "My message travels in one piece, down one path, straight to my friend — like a ball rolling through a single tube."
Actually, your message is split into many packets, and each packet can take a *different* route through many routers. They are reassembled by number at the destination. This is why the internet keeps working even when a cable is cut or a router fails — packets flow around the damage, like students taking a different hallway when one is blocked.
:::

## Where this leads

This is the last networking stop in this course, but what you learned here transfers far. High-school networking and cybersecurity courses dig deeper into these exact ideas — TCP/IP, DNS, and encryption — and you now own the mental model they build on. It also transfers straight into daily life: you can explain why the lock icon in a browser matters, why games lag, and why a "click here now!" message deserves a careful look at who really sent it.

::: check
Q: A five-packet message arrives as packets 1, 2, 4, 5. What does the receiving protocol do, and why is that faster than starting over?
A: It spots the gap at number 3 and requests only packet 3 again. Resending one small packet takes far less time and network space than resending all five.
Q: You are on café Wi-Fi, and a stranger on the same network records your traffic while you use an encrypted site. What can they learn, and what stays hidden?
A: They can see that encrypted packets are flowing between your device and that server''s address, but the scrambled contents — your messages, passwords, and clicks — are unreadable without the secret key.
:::', NULL, NULL, 8, 0.6, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_reading_intro_id_v2', 'k8_networks_communication', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Bagaimana Pesanmu Menemukan Jalan di Internet', 'Pernah heran kenapa pesan yang kamu kirim bisa sampai ke teman di kota lain dalam waktu kurang dari sedetik? Atau kenapa game online tiba-tiba lag padahal Wi-Fi menyala? Di balik semua itu ada jaringan komputer yang bekerja dengan aturan yang sangat rapi, dan kali ini kamu akan membongkar cara kerjanya.

## Ide Besar: Alamat, Paket, dan Aturan Main

Bayangkan internet seperti kota raksasa yang penuh jalan dan kurir. Supaya data bisa sampai ke tujuan, ada tiga bahan utama:

1. **Alamat IP** — setiap perangkat yang terhubung ke jaringan punya alamat, mirip alamat rumah. Bentuknya deretan angka, misalnya `192.168.1.7`. Tanpa alamat ini, data tidak tahu harus diantar ke mana.
2. **Paket** — pesan tidak dikirim utuh, melainkan dipecah menjadi potongan-potongan kecil. Setiap paket membawa alamat tujuan dan nomor urut, seperti amplop kecil yang diberi label.
3. **Protokol** — aturan main yang disepakati semua perangkat. Berkat protokol seperti TCP/IP dan HTTP, HP merek apa pun bisa "ngobrol" dengan server mana pun, karena semuanya memakai bahasa dan tata cara yang sama.

Karena datamu melewati banyak perangkat milik orang lain di perjalanan, jaringan juga butuh pengaman: ada protokol yang mengunci data dengan **enkripsi** (misalnya HTTPS), dan ada kebiasaan aman yang perlu kamu jaga sendiri, seperti kata sandi yang kuat. Kemampuan memodelkan cara kerja jaringan dan keamanannya seperti ini adalah bagian dari capaian belajar JKI-K8-2.

## Contoh Kecil: Mengirim Pengumuman ke Grup

Misalkan kamu mengirim pesan "Latihan futsal jam 4, jangan telat!" ke grup kelas. Kira-kira begini yang dilakukan HP-mu:

```
pesan = "Latihan futsal jam 4, jangan telat!"
paket = pecah(pesan, ukuran_kecil)
untuk setiap p dalam paket:
    tempel_label(p, nomor_urut, alamat_ip_tujuan)
    kirim(p)

// di HP temanmu:
tunggu semua paket datang
susun_ulang(paket, berdasarkan = nomor_urut)
tampilkan(pesan)
```

Perhatikan dua hal: paket boleh datang tidak berurutan (nomor urut yang membereskannya), dan kalau ada paket yang hilang, HP temanmu tinggal minta kiriman ulang untuk paket itu saja — bukan seluruh pesan.

::: check
Q: Apa fungsi alamat IP dalam pengiriman data?
A: Alamat IP menunjukkan perangkat tujuan, seperti alamat rumah, sehingga setiap paket data tahu ke mana harus diantar.
Q: Mengapa pesan panjang dipecah menjadi paket-paket kecil?
A: Paket kecil bisa dikirim lewat jalur berbeda-beda, dan kalau ada yang rusak atau hilang, cukup paket itu saja yang dikirim ulang, bukan seluruh pesan.
:::

Di materi pendalaman berikutnya, kamu akan mengikuti perjalanan lengkap sebuah permintaan halaman web, dari mengetik alamat sampai halaman muncul di layar, termasuk peran gembok HTTPS.', NULL, NULL, 5, 0.3, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_diagram_id_v2', 'k8_networks_communication', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Perjalanan Paket dari HP ke Server', 'Diagram ini menunjukkan perjalanan sebuah pesan chat dari HP-mu menuju server, lalu balasannya kembali. Perhatikan bahwa pesan berangkat sebagai paket-paket bernomor.

```
[HP Kamu]     [Router Wi-Fi]       [Server Chat]
192.168.1.7    (di rumahmu)         103.24.5.80
    |                |                   |
    |----paket #1--->|                   |
    |----paket #2--->|==== internet ====>|
    |                |  (rute bisa beda) |
    |<-------- balasan: "sampai!" -------|
```

Legend:
- `[ ]` = perangkat di jaringan (HP, router, server)
- angka bertitik (mis. `192.168.1.7`) = alamat IP perangkat
- `( )` = keterangan tambahan
- `|` = titik masuk/keluar data di tiap perangkat
- `---->` = arah pergerakan paket
- `====>` = jalur internet yang dilalui paket antar kota/negara
- `#1`, `#2` = nomor urut paket

Cara membaca diagram:

1. Mulai dari kiri: HP-mu memecah pesan menjadi paket `#1` dan `#2`, masing-masing diberi alamat IP tujuan.
2. Kedua paket dikirim dulu ke router Wi-Fi di rumahmu, gerbang keluar menuju internet.
3. Router meneruskan paket ke internet; setiap paket boleh menempuh rute yang berbeda.
4. Server chat di alamat `103.24.5.80` menerima paket, menyusunnya sesuai nomor urut, lalu memproses pesannya.
5. Server mengirim balasan "sampai!" menempuh arah sebaliknya sampai ke HP-mu, itulah tanda centang di aplikasi chat.

::: tip
Alamat yang diawali `192.168.` adalah alamat lokal di jaringan rumah atau sekolahmu, bukan alamat yang terlihat oleh seluruh internet. Coba cek alamat IP perangkatmu di menu pengaturan Wi-Fi, lalu bandingkan dengan perangkat lain di rumah: awalannya biasanya sama, hanya angka terakhirnya yang berbeda.
:::', NULL, NULL, 3, 0.4, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_audio_id_v2', 'k8_networks_communication', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Perjalanan Sebuah Foto di Jaringan', NULL, NULL, 'Halo! Hari ini kita ngobrol tentang sesuatu yang kamu pakai setiap hari tapi jarang kamu pikirkan, yaitu jaringan komputer.

Bayangkan kamu baru selesai kerja kelompok, lalu memotret papan tulis yang penuh catatan penting dan mengirim foto itu ke grup chat kelas. Dalam hitungan detik, semua temanmu menerimanya. Apa yang sebenarnya terjadi di belakang layar?

Pertama, ponselmu tidak mengirim foto itu utuh dalam satu bongkahan. Foto dipecah menjadi ratusan potongan kecil yang disebut paket. Setiap paket seperti kepingan puzzle yang dimasukkan ke amplop. Di setiap amplop tertulis dua hal penting, yaitu alamat tujuan dan nomor urut kepingannya.

Alamat tujuan itu disebut alamat IP. Setiap perangkat yang terhubung ke jaringan punya alamat IP, mirip alamat rumah. Tanpa alamat ini, paket tidak tahu harus diantar ke mana.

Kedua, paket-paket itu berangkat lewat router di rumahmu, lalu melompat dari satu perangkat jaringan ke perangkat lain di internet. Yang menarik, kepingan-kepingan itu tidak harus lewat jalan yang sama. Ada yang lewat jalur cepat, ada yang memutar. Begitu tiba di ponsel temanmu, nomor urut di tiap amplop dipakai untuk menyusun kembali kepingan menjadi foto yang utuh. Kalau ada kepingan yang hilang di jalan, ponsel temanmu akan meminta kiriman ulang untuk kepingan itu saja, bukan seluruh foto.

Ketiga, semua ini bisa berjalan karena ada protokol, yaitu aturan main yang disepakati semua perangkat. Mirip kerja kelompok. Kalau semua anggota sepakat cara membagi tugas dan cara melapor, pekerjaan jadi lancar walaupun anggotanya berbeda-beda.

Satu hal lagi. Karena datamu melewati banyak perangkat milik orang lain, keamanan itu penting. Gunakan kata sandi yang kuat, jangan asal mengklik tautan yang mencurigakan, dan pastikan sambungan situs terenkripsi sebelum kamu memasukkan data pribadi.

Sekarang pertanyaan pengingat untukmu. Apa tiga bahan utama yang membuat pesanmu selalu sampai ke tujuan?

Jawabannya: alamat IP sebagai alamat tujuan, paket sebagai potongan kecil data yang diberi nomor urut, dan protokol sebagai aturan main bersama yang dipahami semua perangkat. Kalau kamu ingat tiga hal itu, kamu sudah memegang kerangka dasar cara internet bekerja.', 4, 0.45, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_networks_communication_reading_deep_id_v2', 'k8_networks_communication', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Di Balik Layar: Protokol, DNS, dan Gembok HTTPS', 'Ingat ide besarnya: data bergerak sebagai paket-paket kecil bernomor, diantar ke alamat IP tujuan, dan semuanya diatur oleh protokol yang disepakati bersama. Sekarang kita ikuti satu perjalanan lengkap.

## Membuka Situs Web, Langkah demi Langkah

Bayangkan kamu mengetik `sekolahku.sch.id` di browser untuk melihat jadwal ujian. Inilah yang terjadi:

1. **Tanya DNS dulu.** Router dan perangkat jaringan hanya paham alamat IP berupa angka, bukan nama situs. Jadi browser bertanya ke layanan bernama **DNS**: "Situs `sekolahku.sch.id` alamat IP-nya berapa?" DNS menjawab, misalnya `103.24.5.80`. DNS mirip daftar kontak di HP: kamu mencari nama, yang dipakai untuk menelepon tetap nomornya.
2. **Salaman dulu (handshake).** Sebelum bertukar data, HP-mu dan server berkenalan singkat memakai protokol TCP: "Siap terima data?" — "Siap!" Ini memastikan kedua pihak sepakat aturan mainnya.
3. **Kirim permintaan.** Browser mengirim permintaan lewat protokol HTTPS: "Tolong kirim halaman jadwal ujian." Huruf S berarti permintaan dan balasannya **dienkripsi**, alias diacak agar tidak bisa dibaca orang di tengah jalan.
4. **Server membalas dengan paket bernomor.** Halaman web dipecah menjadi banyak paket. Paket-paket itu boleh menempuh rute berbeda di internet.
5. **Susun ulang dan periksa.** HP-mu menyusun paket sesuai nomor urut. Kalau paket nomor tertentu tidak kunjung datang, HP-mu minta kiriman ulang khusus paket itu.

Kalau ditulis sebagai pseudocode:

```
alamat_ip = tanya_dns("sekolahku.sch.id")
sambungan = buka_koneksi(alamat_ip)      // salaman TCP
kirim(sambungan, "minta halaman jadwal") // lewat HTTPS

selama halaman belum lengkap:
    paket = terima(sambungan)
    jika ada nomor paket yang bolong:
        minta_kirim_ulang(nomor_yang_hilang)
    susun(paket, berdasarkan = nomor_urut)

tampilkan(halaman)
```

Semua ini terjadi dalam hitungan sepersekian detik, setiap kali kamu membuka situs atau aplikasi apa pun.

## Miskonsepsi yang Sering Muncul

::: misconception
Banyak orang mengira: "Kalau ada ikon gembok (HTTPS) di browser, berarti situsnya pasti aman dan bisa dipercaya sepenuhnya."
Yang benar: gembok hanya berarti data **terenkripsi selama perjalanan**, sehingga tidak bisa diintip orang di tengah jalur. Gembok tidak menjamin pemilik situsnya jujur — situs penipuan pun bisa memakai HTTPS. Jadi tetap periksa ejaan alamat situs baik-baik (misalnya `bank-ku.com` palsu vs `bankku.co.id` asli), dan jangan memasukkan kata sandi hanya karena melihat gembok.
:::

## Ke Mana Ilmu Ini Membawamu

Apa yang kamu pelajari di sini langsung terpakai dalam kehidupan digitalmu sehari-hari: kamu jadi bisa menebak kenapa video call patah-patah (paket terlambat atau hilang), kenapa situs tertentu tidak bisa dibuka (masalah DNS), dan kapan sebuah tautan pantas dicurigai. Model berpikir "alamat, paket, protokol" ini juga menjadi fondasi kalau nanti di jenjang berikutnya kamu mendalami jaringan komputer, pemrograman web, atau keamanan siber — semuanya dibangun di atas kerangka yang sama.

::: check
Q: Paket nomor 3 dari 5 hilang di tengah jalan. Apa yang terjadi di perangkat penerima, dan mengapa seluruh pesan tidak perlu dikirim ulang?
A: Penerima melihat dari nomor urut bahwa paket 3 belum datang, lalu meminta pengirim mengirim ulang paket 3 saja. Nomor urut membuat penerima tahu persis bagian mana yang bolong, sehingga paket lain yang sudah sampai tidak terbuang.
Q: Mengapa komputer tetap membutuhkan DNS padahal kita sudah mengetik nama situsnya dengan benar?
A: Perangkat jaringan mengantar data berdasarkan alamat IP berupa angka, bukan nama. DNS bertugas menerjemahkan nama yang mudah diingat manusia menjadi alamat IP yang dipahami mesin.
:::', NULL, NULL, 8, 0.6, '["k5_networks_communication"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_reading_intro_en_v2', 'k8_program_development', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Build, Test, Improve: How Real Programs Grow', 'Every game you play and every app you use gets updates — bug fixes, new features, version 4.2 replacing 4.1. That is not because the developers messed up. It is because real software is never built in one perfect attempt: it grows version by version, and in this lesson you will learn to build your own projects the same way.

## The Big Idea: Build in Loops

**Iterative design** means building a program in repeated rounds instead of one giant effort. One round looks like this: plan a small piece, build it, test it, collect feedback, improve it. Then you go around again. Each trip around the loop produces a new version of your program that is a little better than the last.

The second half of the idea is **version control**: saving a snapshot of your project every time it improves, along with a short message about what changed. Snapshots let you rewind when a new change breaks something — and, as you will see in the deeper read, they let a whole team build one program together without stepping on each other''s work.

### Follow Along: Three Versions of a Quiz Question

Here is version 1 of a math quiz — the simplest thing that could possibly work:

```
ask "What is 7 x 8?"
get answer
if answer is 56:
    show "Correct!"
```

You test it on a friend. Their feedback: typing a wrong answer does nothing at all, which feels broken. So you improve it and save **version 2** with the message "add wrong-answer response":

```
if answer is 56:
    show "Correct!"
else:
    show "Not quite -- try again"
```

The next round of feedback is "I want to know my score." So **version 3** adds `score = score + 1` inside the correct branch and shows the total at the end. Three loops, three saved snapshots, and a quiz that keeps getting better — that is iterative design in action.

::: check
Q: What are the main steps of one round of iterative design?
A: Plan a small piece, build it, test it, gather feedback, and improve it — then repeat the loop.
Q: Why save a new version with a short message every time the program improves?
A: The message records what changed, and the snapshot lets you rewind to a working version if a later change breaks something.
:::

Ready to see how three people can build one app at the same time without deleting each other''s work? That is exactly what the deeper read covers next.', NULL, NULL, 5, 0.3, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_diagram_en_v2', 'k8_program_development', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'The Iteration Loop and the Team Timeline', 'Iterative design is a loop you travel again and again — and version control quietly records every lap. This one picture shows both ideas and how a team fits in.

```
              THE ITERATION LOOP
+------+   +-------+   +------+   +----------+
| PLAN |-->| BUILD |-->| TEST |-->| FEEDBACK |
+------+   +-------+   +------+   +----------+
   ^                                    |
   |          +---------+               |
   +----------| IMPROVE |<--------------+
              +---------+
      (each full trip = one new version)

        TEAM HISTORY (version control)
main    o----o--------------o----o-->
              \             /
branch         o---o---o--o
```

Legend:

- Boxes (PLAN, BUILD, TEST, FEEDBACK, IMPROVE): the five stages of one design round
- Arrows (-->, <--, |, ^): the direction you move between stages
- o: one commit — a saved snapshot of the project with a short message
- \ : a branch splitting off so a teammate can work on their own copy
- / : that branch merging its finished work back in
- main: the team''s shared, official version of the project
- branch: one teammate''s personal working copy
- Text in ( ): a note about what the loop produces

How to read it:

1. Start at PLAN: pick one small feature to add next.
2. Follow the arrows through BUILD and TEST — make the piece work, then try to break it.
3. FEEDBACK comes from teammates and users; the arrow carries what they said down to IMPROVE.
4. IMPROVE points back to PLAN: one full trip around the loop equals one new, better version.
5. On the bottom timeline, read left to right: each o is a commit. The \ shows a teammate branching off main to work separately, and the / shows their tested changes merging back into the shared project.

::: tip
Write every commit message so it finishes the sentence "This change will..." — for example, "add a score counter." Future you, and your teammates, will always know exactly what each snapshot did.
:::', NULL, NULL, 3, 0.4, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_audio_en_v2', 'k8_program_development', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Why the Best Programs Are Never Finished on the First Try', NULL, NULL, 'Have you ever noticed that the apps on your phone are always updating? Version four point one, then version four point two, then another update a week later. That is not because the people who made them are careless. It is because that is exactly how software is supposed to be built: in rounds, not in one perfect shot.

The idea is called iterative design. Instead of trying to build a whole program at once, you build one small piece, test it, gather feedback, improve it, and go around again. Every trip around that loop gives you a new, slightly better version of your program.

Here is an example. Imagine you and a friend are making a simple maze game. Your first version just lets the player move around the screen. You test it and spot a problem right away: the player can walk straight through the walls. That is not a disaster. That is useful information. You fix the wall code, then save the project with a short note that says, fixed walls so they block the player. That note, plus the saved snapshot, is what version control is all about. It works like a save point in a video game. If a later change breaks everything, you can rewind to the last version that worked.

Version control also makes teamwork possible. While you were fixing walls, your friend was adding sound effects on their own copy of the project. When you are both done, you merge the two copies together, and now the game has solid walls and sound. Nobody overwrote anybody''s work, and the project history shows exactly who changed what, and why.

Then comes the best part. You share the game with classmates and collect their feedback. Maybe they say the maze is too easy. That feedback becomes the plan for your next trip around the loop.

Time for one recap question. What are the steps of one round of iterative design, and what does version control add? Here is the answer. You plan a small piece, build it, test it, gather feedback, and improve it. And version control saves a snapshot of every version, so you can rewind mistakes and safely combine your teammates'' work.', 4, 0.45, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_reading_deep_en_v2', 'k8_program_development', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Coding Together: Branches, Merges, and Feedback', 'Quick recap: programs grow through repeated plan-build-test-feedback loops, and version control saves a snapshot of every improvement. Now let''s see how those two ideas let an entire team share one project.

## Worked Example: Three Coders, One App

Maya, Jayden, and you are building **Homework Buddy**, an app that reminds students about assignments. Here is how the project moves, step by step.

1. **Set up a shared project.** The team creates one project with version history turned on. The official copy is called **main**.
2. **Branch out.** Each person makes a personal copy of main, called a *branch*. You take the reminder feature, Maya takes the task list, and Jayden takes the app''s look.
3. **Commit small and often.** Every finished piece gets saved with a clear message:

| Who | Commit message |
| --- | --- |
| You | Add 7 pm reminder alert |
| Maya | Add task list screen |
| Jayden | Change buttons to blue |

4. **Test before merging.** Each person runs their own branch first, to make sure their piece works on its own.
5. **Merge back into main.** The tool combines everyone''s changes automatically — until Maya and Jayden both edit the same home-screen title line. The tool cannot choose between them, so it flags a *merge conflict*. They look at both versions side by side, agree on one title, and save that as the merged result. Nobody''s work gets silently deleted.
6. **Get user feedback and loop again.** The team gives the app to five classmates. One says the reminder is "too easy to swipe away and forget." That comment becomes the plan for iteration two. Seeking and using feedback from teammates and users to refine a program is exactly what the CSTA standard 2-AP-15 expects of middle-school programmers.

## The "First Try" Trap

Many students treat old versions like embarrassing evidence of mistakes. It is actually the opposite.

::: misconception
Wrong belief: "Good programmers write the whole program correctly on the first try, so needing lots of versions means you are bad at coding."
Correction: Professional teams release many small versions on purpose. Iteration is the method, not the mistake. Skilled programmers actually make their first versions smaller, so they can test, get feedback, and improve faster.
:::

If your project history is full of small commits, that is a sign you are working like a real developer.

## Where This Skill Leads

What you learn here transfers far beyond this course. The workflow you just practiced — branching, committing, merging, and feedback loops — is exactly how professional version control tools work, and it is how every app, game, and website you use actually gets built. It also transfers to any group project at all: shared documents, videos, or a band writing a song all go smoother with saved versions, small labeled changes, and honest feedback rounds.

::: check
Q: Two teammates each changed the same greeting line on their own branches. What happens at merge time, and how should they fix it?
A: The tool reports a merge conflict on that line because it cannot choose for them; they compare both changes together, decide what the app should actually say, and save that agreed version as the merge result.
Q: Why is committing "Add reminder alert" as its own small save better than one giant "finished everything" save at the end?
A: Small commits make it easy to find exactly which change caused a bug and to rewind just that one change, without throwing away everyone else''s finished work.
:::', NULL, NULL, 8, 0.6, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_reading_intro_id_v2', 'k8_program_development', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Membangun Program Selangkah demi Selangkah', 'Pernah dapat notifikasi "pembaruan tersedia" dari game atau aplikasi favoritmu? Itu tandanya para pengembangnya tidak pernah benar-benar "selesai" — mereka terus memperbaiki dan menambah fitur sedikit demi sedikit. Di materi ini, kamu akan belajar bekerja seperti mereka: membangun program secara bertahap, menyimpan setiap versinya, dan bekerja sama dalam tim.

## Ide Besar: Program Tumbuh Lewat Iterasi

Program yang bagus jarang sekali jadi dalam satu kali tulis. Pengembang bekerja dalam **siklus iterasi**: rancang idenya, bangun versi sederhana, uji coba, kumpulkan masukan, lalu perbaiki. Siklus ini diulang terus sampai programnya makin baik. Dalam kurikulum informatika, cara kerja ini dikenal sebagai standar AP-K8-6: mengembangkan program secara bertahap dan kolaboratif.

Ada tiga kebiasaan penting:

- **Desain iteratif** — mulai dari versi paling sederhana yang bisa jalan, lalu tingkatkan selangkah demi selangkah.
- **Kontrol versi** — simpan setiap versi dengan catatan perubahan, supaya kamu bisa kembali ke versi lama kalau versi baru bermasalah.
- **Kolaborasi** — bagi tugas dengan tim, lalu gabungkan hasil kerja masing-masing dengan rapi.

Bayangkan seperti kerja kelompok membuat mading: ada draf pertama, masukan teman, revisi, dan pembagian tugas. Bedanya, di pemrograman semua jejak perubahan bisa dicatat dengan teratur.

## Contoh: Game Tebak Angka, Versi demi Versi

Misalkan kamu membuat game tebak angka. Versi pertama dibuat sesederhana mungkin:

```
VERSI 1
angka_rahasia = 7
minta tebakan dari pemain
jika tebakan = angka_rahasia:
    tampilkan "Benar!"
jika tidak:
    tampilkan "Salah!"
```

Kamu simpan sebagai **v1** dengan catatan "tebak angka dasar". Lalu temanmu mencoba. Masukannya: "Cuma boleh nebak sekali? Dan nggak ada petunjuk sama sekali!" Dari umpan balik itu, kamu merancang perbaikan dan membuat **v2**:

```
VERSI 2
angka_rahasia = acak 1 sampai 10
ulangi sampai tebakan benar:
    minta tebakan dari pemain
    jika tebakan > angka_rahasia:
        tampilkan "Terlalu besar"
    jika tebakan < angka_rahasia:
        tampilkan "Terlalu kecil"
tampilkan "Benar! Kamu hebat!"
```

Perhatikan polanya: bangun, uji, dengar masukan, perbaiki, simpan versi baru. Kalau v2 ternyata error, kamu tinggal kembali ke v1 tanpa panik — itulah gunanya kontrol versi.

::: check
Q: Mengapa lebih baik memulai dari versi program yang paling sederhana?
A: Versi sederhana cepat selesai dan bisa langsung diuji, sehingga kamu cepat tahu apa yang perlu diperbaiki sebelum menambah fitur yang rumit.
Q: Apa gunanya menyimpan setiap versi program dengan catatan perubahan?
A: Kamu bisa melacak apa yang berubah di tiap versi dan kembali ke versi lama yang masih berfungsi jika versi baru bermasalah.
:::

Di materi pendalaman, kamu akan melihat bagaimana siklus ini dijalankan oleh satu tim penuh — lengkap dengan pembagian tugas, penggabungan kode, dan cara memakai riwayat versi saat ada masalah.', NULL, NULL, 5, 0.3, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_diagram_id_v2', 'k8_program_development', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Siklus Iterasi dan Riwayat Versi', 'Diagram ini menunjukkan siklus pengembangan program secara iteratif, plus riwayat versi yang terus tumbuh setiap kali siklusnya berputar satu kali.

```
         SIKLUS PENGEMBANGAN PROGRAM
+----------+    +----------+    +----------+
| RANCANG  |--->|  BANGUN  |--->|   UJI    |
|ide & alur|    |tulis kode|    |coba jalan|
+----------+    +----------+    +----------+
     ^                               |
     |                               v
+----------+                   +----------+
| PERBAIKI |<------------------| MASUKAN  |
|  revisi  |                   |dari teman|
+----------+                   +----------+
     |
     | simpan tiap putaran
     v
[v1]---[v2]---[v3]--->...    RIWAYAT VERSI
```

Legenda:

- Kotak: satu tahap dalam siklus pengembangan program
- Panah ---> atau v : urutan langkah yang diikuti
- [v1], [v2], [v3]: versi program yang tersimpan
- ... : siklus terus berulang, versi terus bertambah

Cara membaca diagram:

1. Mulai dari kotak RANCANG: tentukan ide dan alur program versi sederhana.
2. Ikuti panah ke BANGUN (tulis kodenya) lalu ke UJI (jalankan dan coba).
3. Dari UJI, hasilnya turun ke MASUKAN: teman atau pengguna memberi tahu apa yang kurang.
4. MASUKAN mengalir ke PERBAIKI, lalu panah naik kembali ke RANCANG — di sinilah putaran baru dimulai.
5. Setiap kali satu putaran selesai, program disimpan sebagai versi baru: dari [v1] ke [v2], ke [v3], dan seterusnya. Deretan inilah riwayat versimu.

::: tip
Biasakan menulis catatan singkat dan jelas setiap menyimpan versi, misalnya "menambah skor tertinggi" — bukan "update2_final_beneran". Saat program bermasalah, catatan yang rapi membuatmu menemukan penyebabnya dalam hitungan menit, bukan berjam-jam.
:::', NULL, NULL, 3, 0.4, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_audio_id_v2', 'k8_program_development', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Mengapa Program Hebat Lahir dari Banyak Versi', NULL, NULL, 'Pernahkah kamu memperhatikan bahwa game dan aplikasi favoritmu terus mendapat pembaruan? Versi satu titik nol, lalu satu titik satu, lalu dua titik nol. Itu bukan karena pembuatnya ceroboh. Justru begitulah cara program yang hebat dibuat: sedikit demi sedikit, versi demi versi.

Inilah ide besarnya. Program yang baik tidak lahir sekali jadi. Program tumbuh lewat siklus yang disebut iterasi. Pertama, kamu merancang ide yang sederhana. Kedua, kamu membangunnya menjadi program yang bisa berjalan. Ketiga, kamu mengujinya dan meminta orang lain mencobanya. Keempat, kamu mendengarkan masukan mereka, lalu memperbaiki programmu. Setelah itu, siklusnya berputar lagi dari awal.

Supaya lebih terbayang, misalkan kamu dan temanmu membuat game labirin sederhana. Versi pertama hanya punya satu level, dan tokohnya cuma bisa bergerak ke empat arah. Sederhana sekali, tapi sudah bisa dimainkan. Kalian menyimpannya sebagai versi satu, lengkap dengan catatan singkat tentang isinya. Lalu kalian meminta teman sekelas mencobanya. Ternyata katanya labirinnya terlalu sulit dan tidak ada petunjuk arah. Nah, itu masukan yang berharga. Temanmu lalu mengerjakan fitur petunjuk arah, sementara kamu membuat level kedua. Kalian bekerja di salinan masing-masing supaya tidak saling menimpa pekerjaan, lalu menggabungkan hasilnya menjadi versi dua.

Di sinilah kontrol versi menyelamatkanmu. Suatu hari, setelah menambahkan fitur baru, game kalian tiba-tiba macet. Karena setiap versi tersimpan rapi dengan catatannya, kalian tinggal kembali ke versi sebelumnya yang masih berjalan normal, lalu mencari penyebab masalahnya dengan tenang. Tanpa riwayat versi, kalian mungkin harus menulis ulang semuanya dari nol.

Jadi, ingat tiga kebiasaan ini. Bangun program secara bertahap. Simpan setiap versi dengan catatan yang jelas. Dan bagi tugas dengan timmu secara rapi, lalu gabungkan hasilnya dengan hati-hati.

Sekarang, pertanyaan penutup untukmu. Kalau versi baru programmu tiba-tiba rusak, apa untungnya kamu punya riwayat versi yang tersimpan rapi? Jawabannya: kamu bisa kembali ke versi lama yang masih berfungsi, membandingkan apa saja yang berubah, dan menemukan penyebab kerusakan tanpa harus mengulang semuanya dari awal. Itulah kekuatan pengembangan program yang iteratif.', 4, 0.45, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_program_development_reading_deep_id_v2', 'k8_program_development', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Kerja Tim, Iterasi, dan Riwayat Versi dalam Proyek Nyata', 'Ide besarnya: program berkembang lewat siklus rancang–bangun–uji–perbaiki, dan setiap versinya dicatat supaya tim bisa bekerja sama tanpa saling menimpa pekerjaan. Sekarang kita lihat bagaimana satu tim benar-benar menjalankannya dari awal sampai akhir.

## Contoh Lengkap: Aplikasi Piket Kelas Bertiga

Kamu, Sinta, dan Raka membuat aplikasi jadwal piket untuk kelas. Beginilah jalannya proyek, langkah demi langkah.

**Langkah 1 — Rancang bersama.** Kalian sepakat versi pertama cukup menampilkan siapa yang piket hari ini. Fitur keren seperti pengingat otomatis disimpan untuk iterasi berikutnya.

**Langkah 2 — Bangun versi 1.** Kamu menulis inti programnya:

```
jadwal = {Senin: [Aldi, Bima], Selasa: [Cika, Dewi], ...}
hari_ini = ambil nama hari
tampilkan "Piket hari ini: " + jadwal[hari_ini]
```

Versi ini disimpan ke penyimpanan bersama dengan catatan: "v1 — menampilkan piket harian".

**Langkah 3 — Bagi tugas di salinan terpisah.** Sinta ingin menambah pengingat otomatis; Raka menemukan bug nama ganda. Masing-masing bekerja di salinan kerja sendiri (dalam alat kontrol versi, salinan seperti ini disebut *branch* atau cabang), jadi program utama tetap aman meski pekerjaan mereka belum selesai.

```
modul pengingat (dikerjakan Sinta):
  untuk setiap siswa di jadwal[hari_ini]:
    kirim pesan "Hari ini giliran piketmu!"
```

**Langkah 4 — Uji, lalu gabungkan.** Sinta menguji modulnya, Raka menguji perbaikannya. Setelah keduanya lolos, hasilnya digabungkan ke program utama. Riwayat versinya kini berbunyi:

```
v1  "menampilkan piket harian"      - kamu
v2  "memperbaiki nama ganda"        - Raka
v3  "menambah pengingat otomatis"   - Sinta
```

**Langkah 5 — Uji gabungan dan dengar pengguna.** Kalian menguji ulang seluruh aplikasi, sebab dua perubahan yang benar sendiri-sendiri bisa saja bertabrakan setelah digabung. Setelah aplikasi dipakai seminggu, teman sekelas memberi masukan: "Bisa nggak tukar jadwal kalau lagi sakit?" Masukan itu menjadi bahan iterasi berikutnya. Siklusnya berputar lagi.

## Miskonsepsi yang Sering Muncul

::: misconception
Keliru: "Programmer andal menulis kode sekali jadi. Kalau masih harus merevisi berkali-kali, berarti kurang jago."
Faktanya justru sebaliknya: pengembang profesional sengaja bekerja dalam iterasi. Game dan aplikasi besar dirilis dengan versi awal yang sederhana, lalu terus diperbaiki lewat pembaruan demi pembaruan. Merevisi bukan tanda kegagalan — itulah cara program berkualitas dibuat. Yang membedakan pemula dan ahli bukan jumlah revisinya, melainkan seberapa rapi mereka mencatat dan menguji setiap perubahan.
:::

## Ke Mana Keterampilan Ini Membawamu

Kebiasaan iterasi dan kontrol versi ini akan terpakai di hampir semua proyek yang lebih besar nanti. Saat kamu membangun aplikasi atau game yang lebih kompleks di jenjang berikutnya, alat kontrol versi profesional yang dipakai pengembang sungguhan bekerja persis dengan pola yang baru kamu pelajari: simpan, catat, cabangkan, gabungkan. Bahkan di luar pemrograman — misalnya menulis makalah kelompok di dokumen daring — riwayat versi dan pembagian tugas memakai logika yang sama.

::: check
Q: Tim kamu mengerjakan dua fitur sekaligus di salinan kerja yang terpisah. Apa yang harus dilakukan sebelum dan sesudah menggabungkannya?
A: Uji setiap fitur di salinannya masing-masing dulu, gabungkan, lalu uji ulang program secara keseluruhan — karena dua perubahan yang benar secara terpisah tetap bisa saling mengganggu setelah digabung.
Q: Setelah pembaruan ke v5, aplikasi tim tiba-tiba rusak, padahal v4 masih normal. Bagaimana riwayat versi membantu?
A: Bandingkan perubahan antara v4 dan v5 untuk menemukan penyebab kerusakan, dan sementara mencarinya, kembalikan aplikasi ke v4 supaya pengguna tetap bisa memakainya.
:::', NULL, NULL, 8, 0.6, '["k5_program_development", "k8_modularity"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_reading_intro_en_v2', 'k8_variables', 'en', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'One Name, Many Values: Lists and Where Variables Live', 'Open your favorite music app and it remembers every song in your playlist — not just one. Your favorite game tracks every item in your backpack and every player on your team. A variable that holds a single value can''t do any of that, so today we upgrade.

## One Name, Many Values

So far, a variable has been a labeled box holding one thing: a number, a word, or a true/false. A **list** is a variable that holds a whole row of values, in order, under a single name:

```
playlist = ["Levitate", "Stardust", "Echo"]
```

Three songs, one variable. With a list you can:

- read one item by its position: `playlist[0]` is `"Levitate"` — positions start counting at **0**, not 1
- add items to the end while the program runs
- remove items from any position
- count everything with `length(playlist)`

That last part is the superpower. With separate variables like `song1`, `song2`, `song3`, your program is stuck at exactly three songs forever. With a list, the same code works whether the playlist has 3 songs or 3,000.

There''s a second upgrade coming, too: as your programs grow into multiple functions, every variable gets a *home* — called its **scope** — that decides which parts of the program can use it. Think of it like a group project: some notes go on the shared class whiteboard for everyone, and some stay in your own notebook.

## Follow Along: Editing the Playlist

Trace this pseudocode line by line and predict each output before reading the answer:

```
playlist = ["Levitate", "Stardust", "Echo"]
say length(playlist)          # -> 3
add "Night Drive" to playlist
say length(playlist)          # -> 4
say playlist[0]               # -> Levitate
remove playlist[1]
say playlist                  # -> Levitate, Echo, Night Drive
```

The tricky line is `remove playlist[1]`. Position 1 is the *second* item, so `"Stardust"` gets removed — not `"Levitate"`. After that, everything behind it slides forward one position: `"Echo"` is now at position 1.

::: check
Q: In `colors = ["red", "green", "blue"]`, what is `colors[1]`?
A: "green" — positions start at 0, so position 1 is the second item in the list.
Q: Why is one list better than separate variables like song1, song2, and song3?
A: A list keeps all the values in order under one name, lets you add or remove items while the program runs, and lets you count or step through them even when you don''t know ahead of time how many there will be.
:::

Lists are only half the story — the deeper read shows what happens when several functions share (or secretly *don''t* share) variables, and why knowing where a variable lives will save you from the most confusing bugs in multi-function programs.', NULL, NULL, 5, 0.3, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_diagram_en_v2', 'k8_variables', 'en', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Variable Zones: Who Can See What', 'A program with functions is like a set of nested zones, and a variable can only be used inside the zone where it was created. This diagram maps a tiny pet-sitting app so you can see who lives where.

```
+------------- PROGRAM: the global zone ------------+
| pets = ["Milo", "Nova"]    <- global list         |
|                                                   |
|   +------ function add_pet(name) -------+         |
|   | note = "saved!"        <- local     |         |
|   | add name to pets    ===> global     |         |
|   +-------------------------------------+         |
|                                                   |
|   +------ function count_pets() --------+         |
|   | total = length(pets)   <- local     |         |
|   | return total        ===> answer out |         |
|   +-------------------------------------+         |
+---------------------------------------------------+
```

Legend

- Outer box = the whole program (the global zone)
- Inner boxes = one function each (a local zone)
- `<-` = a note telling you where that variable lives
- `===>` = an action whose effect reaches outside the local zone
- `[ ]` = a list: one variable holding several values

How to read it

1. Start with the outer box. `pets` is created at the top level, so it''s global — both inner boxes can see it and use it.
2. Look inside `add_pet`. The variable `note` is created there, so it''s local: it exists only while that function runs, then it''s gone.
3. Follow the first `===>` arrow. `add name to pets` reaches out and changes the global list, so that change survives after the function ends.
4. Look inside `count_pets`. `total` is local, but it''s calculated *from* the global list — inner zones can look outward.
5. Follow the second `===>` arrow. `return total` sends the *value* out of the box, even though the variable `total` itself stays trapped inside and vanishes.
6. Notice what''s missing: nothing outside a box can look in. The main program can never use `note` or `total` directly.

::: tip
When you hit a "variable is not defined" error, ask yourself: which box was this variable born in? If it was born inside a function and you need it elsewhere, either `return` the value or create the variable out in the global zone instead.
:::', NULL, NULL, 3, 0.4, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_audio_en_v2', 'k8_variables', 'en', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Lists, Scope, and the Movie Night Voting App', NULL, NULL, 'Have you ever helped plan something with a group, like a class movie night? Keep that in mind, because today we''re talking about two ideas that make bigger programs possible: variables that hold whole lists of things, and the idea that every variable has a home.

First, lists. Up to now, your variables have held one thing at a time. One number. One word. But imagine building a voting app for that movie night. Thirty classmates each vote for a movie. You do not want thirty separate variables. Instead, you create one variable called votes, and you make it a list. A list is a single variable that holds many values in order. When the app starts, votes is empty. Every time someone votes, the program adds their choice to the end of the list. At any moment, you can ask the list how many items it holds, or read the first vote, or the last one. One name, many values.

The second idea is scope, which is just a fancy word for where a variable lives. Think about a group project. There is the shared class document that everyone can see and edit, and there is your own scratch paper that only you use. Programs work the same way. A variable created at the top of your program, like the votes list, is like the shared document. It is global, and every function in the program can see it. But a variable created inside a function is like scratch paper. Say you write a function called count votes, and inside it you create a variable called tally to add things up. That tally belongs to the function. When the function finishes, the scratch paper gets tossed. The rest of the program never sees tally. That is a good thing: functions written by different people will not accidentally mess with each other''s variables, even when they pick the same names.

So remember: lists let one variable hold a whole collection, and scope decides which parts of your program can touch which variable.

Here is your recap question. Inside a function, you create a variable called tally. After the function finishes, can the main program still use tally? Think about the scratch paper. The answer is no. Tally was local to the function, so it disappeared the moment the function ended. If you need that value later, have the function return it, or store it in a variable that lives at the top level of your program.', 4, 0.45, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_reading_deep_en_v2', 'k8_variables', 'en', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Inside the Loot Tracker: Lists, Scope, and Local Variables', 'Quick recap of the big idea: a list lets one variable hold many values in order, and every variable has a home — its **scope** — that decides which parts of a program can use it. Now let''s watch scope actually matter in a program with more than one function.

## Worked Example: The Loot Tracker

Here''s a small game program. One list lives at the top level; two functions do the work:

```
inventory = ["sword", "shield"]      # global

function add_loot(item):
    note = item + " added!"          # local
    add item to inventory
    say note

function count_loot():
    total = length(inventory)        # local
    return total

add_loot("potion")
say count_loot()
say note                             # crash!
```

Step through it like the computer does:

1. The program starts. `inventory` is created at the top level — outside every function — so it''s **global**: every function can see it and change it.
2. `add_loot("potion")` runs. Inside the function, `item` holds `"potion"` and a brand-new variable `note` is created. Both are **local**: they exist only while this function is running. The function adds `"potion"` to `inventory` and says `potion added!`.
3. The function ends. Here''s the key moment: `note` and `item` are thrown away, but the change to `inventory` **survives**, because `inventory` lives outside the function. It now holds three items.
4. `count_loot()` runs. Its local `total` becomes 3, gets returned, and then `total` is thrown away too. The *value* 3 escaped through `return`; the *variable* didn''t.
5. `say note` crashes. Out here at the top level, `note` simply doesn''t exist. It was born inside `add_loot` and died when that function finished.

The rule of thumb: **variables created inside a function are local and vanish when it ends; variables created at the top level are global and stick around.** If a function needs to hand a value back, `return` it.

## The Misconception That Bites Everyone

::: misconception
Wrong belief: "If two variables have the same name, they''re the same variable everywhere in the program."
The truth: the same name in different scopes means *different variables*. A `heal_player` function and a `save_game` function could each create their own local `count` — two separate boxes that never touch. Changing one does nothing to the other, and neither exists outside its function. What makes two variables "the same" isn''t their name; it''s the scope they were created in.
:::

This is actually a feature, not a hazard. In a group project, four teammates can each write their own functions using handy names like `total` or `temp` without smashing each other''s work — exactly what scope is for.

## Where This Leads

Everything here transfers straight into real programming languages. Python lists and JavaScript arrays work almost exactly like our pseudocode lists, and their local/global scope rules match the loot tracker''s behavior line for line. This skill — creating clearly named variables that store different types of data, from single numbers to whole lists — is what the CSTA 2-AP-09 standard describes, and it''s the foundation for every larger project you''ll build: apps with user lists, games with inventories, and team codebases where dozens of functions coexist without their variables colliding.

::: check
Q: `scores = [10, 20]` is global. `function boost()` creates a local `bonus = 5` and adds `bonus` to `scores`. After calling `boost()` twice, what does `scores` hold, and does `bonus` still exist?
A: `scores` is [10, 20, 5, 5] — changes to the global list survive after each call. `bonus` no longer exists; it was local, so it was created and destroyed each time the function ran.
Q: Two functions each create a local variable named `total`. One sets it to 3, the other to 100. Do they interfere with each other?
A: No. Same name, different scopes — each function gets its own separate `total`, and each one disappears when its function finishes.
:::', NULL, NULL, 8, 0.6, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_reading_intro_id_v2', 'k8_variables', 'id', 'reading', '["vark_reading", "motiv_logical"]'::jsonb, 'Variabel Naik Level: List dan Lingkup', 'Pernah membuka aplikasi musik dan melihat playlist berisi puluhan lagu? Di balik layar, semua judul itu tidak disimpan dalam puluhan variabel terpisah, melainkan dalam **satu variabel** yang bisa menampung banyak nilai. Dan karena aplikasi besar dibangun dari banyak fungsi, setiap variabel juga punya "wilayah kekuasaan" sendiri — di mana ia boleh dipakai, dan di mana ia tidak dikenal.

## Satu Variabel, Banyak Nilai — Plus Aturan Wilayahnya

Sampai sekarang, kamu terbiasa dengan variabel yang menyimpan satu nilai: satu angka, satu kata. Program sungguhan butuh lebih dari itu. Di sinilah **list** (daftar) berperan: satu variabel yang isinya berderet-deret nilai.

Dua hal penting tentang list:

- Setiap nilai punya nomor urut yang disebut **indeks**, dan indeks dimulai dari **0**, bukan 1.
- Isi list bisa berubah: kamu bisa menambah, menghapus, atau mengganti nilainya kapan saja.

Hal kedua adalah **lingkup** (*scope*). Ketika program dipecah menjadi beberapa fungsi, muncul pertanyaan: variabel ini milik siapa? Aturannya:

- **Variabel global** dibuat di luar semua fungsi. Semua fungsi bisa melihat dan memakainya.
- **Variabel lokal** dibuat di dalam sebuah fungsi. Ia lahir saat fungsi dipanggil, dan lenyap saat fungsi selesai.

Kemampuan memilih tipe data yang tepat dan mengatur lingkup variabel seperti ini adalah inti dari standar belajar AP-K8-4.

Coba ikuti contoh aplikasi musik mini ini:

```
playlist = ["Bintang", "Hujan", "Senja"]   // list, global

fungsi putarAcak():
    pilihan = acak(0, panjang(playlist) - 1)   // lokal
    tampilkan "Memutar: " + playlist[pilihan]

tambahkan "Fajar" ke playlist
putarAcak()
```

Jalankan di kepala:

1. `playlist` dibuat sebagai list global berisi 3 lagu.
2. `"Fajar"` ditambahkan, sehingga panjang list menjadi 4.
3. Saat `putarAcak()` dipanggil, variabel lokal `pilihan` lahir — misalnya bernilai 2.
4. `playlist[2]` adalah `"Senja"`, jadi layar menampilkan `Memutar: Senja`.
5. Fungsi selesai — `pilihan` lenyap, tetapi `playlist` tetap ada karena ia global.

::: check
Q: Jika playlist = ["Bintang", "Hujan", "Senja"], apa isi playlist[1]?
A: "Hujan". Indeks list dimulai dari 0, jadi playlist[0] adalah "Bintang" dan playlist[1] adalah "Hujan".
Q: Mengapa variabel pilihan tidak bisa dipakai di luar fungsi putarAcak?
A: Karena pilihan adalah variabel lokal — lingkupnya hanya di dalam fungsi itu, dan ia lenyap begitu fungsi selesai.
:::

Di materi pendalaman, kita akan membedah satu program multi-fungsi utuh dan melihat jebakan lingkup yang paling sering menjerat programmer pemula.', NULL, NULL, 5, 0.3, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_diagram_id_v2', 'k8_variables', 'id', 'diagram', '["vark_visual", "vark_kinesthetic", "motiv_logical"]'::jsonb, 'Peta Lingkup: Di Mana Variabel Hidup', 'Cara paling gampang memahami lingkup adalah membayangkannya sebagai kotak di dalam kotak. Diagram ini memetakan sebuah game sederhana: variabel mana hidup di mana, dan siapa boleh mengakses apa.

```
+--------------------------------------------+
|          PROGRAM (lingkup global)          |
|                                            |
|  skor = 0                                  |
|  inventori = ["peta", "obor"]              |
|        ^              ^                    |
|        |              |                    |
|  +-----+-----+   +----+--------+           |
|  | fungsi    |   | fungsi      |           |
|  | tambahSkor|   | ambilBarang |           |
|  | bonus = 5 |   | slot = 2    |           |
|  | (lokal)   |   | (lokal)     |           |
|  +-----------+   +-------------+           |
+--------------------------------------------+
```

Legend:

- Kotak terluar = seluruh program; variabel di sini bersifat global.
- Kotak kecil = satu fungsi; variabel di dalamnya bersifat lokal.
- `^` dan `|` = jalur akses: fungsi boleh membaca dan mengubah variabel global di atasnya.
- `["peta", "obor"]` = list, satu variabel yang berisi banyak nilai.
- `(lokal)` = variabel yang lahir saat fungsi dipanggil dan lenyap saat fungsi selesai.

Cara membaca diagram:

1. Mulai dari kotak terluar: `skor` dan `inventori` dibuat di lingkup global, jadi seluruh program mengenalnya.
2. Perhatikan `inventori`: ia sebuah list, satu nama yang menampung dua nilai sekaligus.
3. Masuk ke kotak `tambahSkor`: variabel `bonus` hanya dikenal di dalam kotak itu.
4. Ikuti panah ke atas: kedua fungsi bebas menjangkau `skor` dan `inventori` karena keduanya global.
5. Coba tarik garis dari `tambahSkor` ke `slot` — tidak ada jalurnya. Variabel lokal satu fungsi tidak terlihat dari fungsi lain.

::: tip
Saat programmu mulai membingungkan, gambar ulang peta kotak seperti ini di kertas. Kalau ada variabel yang perlu "keluar" dari kotaknya, itu tanda kamu membutuhkan variabel global, parameter, atau nilai balik.
:::', NULL, NULL, 3, 0.4, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_audio_id_v2', 'k8_variables', 'id', 'audio', '["vark_auditory", "motiv_social"]'::jsonb, 'Mengenal List dan Lingkup Variabel', NULL, NULL, 'Halo! Hari ini kita ngobrol tentang dua kemampuan baru variabel: menampung banyak nilai sekaligus, dan punya wilayahnya sendiri di dalam program.

Bayangkan kamu dan teman sekelompok memakai aplikasi daftar tugas untuk proyek IPA. Di balik aplikasi itu, semua tugas tidak disimpan di variabel yang terpisah-pisah. Ada satu variabel bernama daftar tugas, dan isinya berderet: cari bahan, buat poster, latihan presentasi. Variabel yang isinya berderet seperti ini disebut list. Setiap isi punya nomor urut yang disebut indeks, dan ingat, indeks dimulai dari nol, bukan dari satu. Jadi tugas pertama, yaitu cari bahan, ada di indeks nol.

Sekarang bagian keduanya, yaitu lingkup variabel. Program yang besar dibagi menjadi beberapa fungsi, dan setiap variabel punya wilayah tempat ia dikenal. Begini analoginya. Variabel global itu seperti tulisan di papan tulis kelas: siapa pun di kelas bisa membacanya dan mengubahnya. Variabel lokal itu seperti coretan di kertas pribadimu: hanya kamu yang tahu, dan begitu pelajaran selesai, kertas itu kamu buang.

Kembali ke aplikasi tadi. Daftar tugas dibuat sebagai variabel global, karena semua fungsi perlu memakainya. Lalu ada fungsi tambah tugas. Di dalamnya, ada variabel lokal bernama pesan, yang menyusun kalimat konfirmasi seperti: tugas baru berhasil ditambahkan. Begitu fungsi tambah tugas selesai bekerja, variabel pesan langsung lenyap. Tapi tenang, daftar tugas tetap utuh, karena ia hidup di papan tulis, di wilayah global.

Kenapa aturan ini penting? Kalau semua variabel dibuat global, program besar cepat jadi kacau, karena fungsi mana pun bisa tidak sengaja mengubah data milik fungsi lain. Aturan praktisnya begini: buat variabel selokal mungkin, dan gunakan global hanya untuk data yang memang harus dipakai bersama oleh banyak fungsi.

Sebelum tutup, satu pertanyaan singkat untukmu. Kalau sebuah variabel dibuat di dalam sebuah fungsi, apakah fungsi lain bisa ikut memakainya? Jawabannya: tidak bisa. Variabel itu lokal, wilayahnya hanya di dalam fungsi tempat ia dibuat, dan ia lenyap saat fungsinya selesai. Kalau datanya perlu dipakai bersama, simpan di variabel global atau di dalam list global. Sampai jumpa di latihan berikutnya!', 4, 0.45, '["k5_variables"]'::jsonb);
INSERT INTO learning_materials (id, concept_id, language, modality, archetype_tags, title, body, media_url, transcript, estimated_minutes, difficulty, prerequisites_assumed) VALUES ('k8_variables_reading_deep_id_v2', 'k8_variables', 'id', 'reading', '["vark_reading", "motiv_logical", "motiv_explorer"]'::jsonb, 'Membedah Program Multi-Fungsi: Global, Lokal, dan List', 'Ide besarnya: list membuat satu variabel bisa menampung banyak nilai, dan lingkup menentukan di wilayah mana sebuah variabel dikenal — global untuk seluruh program, lokal hanya di dalam satu fungsi.

## Membedah Aplikasi Kas Kelas Langkah demi Langkah

Bayangkan kelasmu membuat aplikasi sederhana untuk mencatat uang kas. Programnya punya dua variabel global dan dua fungsi:

```
kasKelas = 0          // global: total uang
riwayat  = []         // global: list catatan, awalnya kosong

fungsi setor(nama, jumlah):
    catatan = nama + " setor " + jumlah   // lokal
    tambahkan catatan ke riwayat
    kasKelas = kasKelas + jumlah

fungsi laporan():
    untuk setiap catatan di riwayat:
        tampilkan catatan
    tampilkan "Total: " + kasKelas

setor("Raka", 5000)
setor("Sinta", 10000)
laporan()
```

Mari lacak isi memori langkah demi langkah:

| Langkah | kasKelas | riwayat |
| --- | --- | --- |
| Awal program | 0 | [] |
| setor("Raka", 5000) selesai | 5000 | ["Raka setor 5000"] |
| setor("Sinta", 10000) selesai | 15000 | ["Raka setor 5000", "Sinta setor 10000"] |

Perhatikan apa yang terjadi di dalam `setor("Raka", 5000)`:

1. Variabel lokal `catatan` lahir dengan isi `"Raka setor 5000"`.
2. Isi `catatan` dimasukkan ke list global `riwayat` — datanya selamat.
3. `kasKelas` (global) diperbarui menjadi 5000.
4. Fungsi selesai; `catatan` lenyap. Tak masalah, karena isinya sudah tersimpan di `riwayat`.

Saat `setor` dipanggil kedua kalinya, lahir `catatan` yang **baru** dari nol. Variabel lokal tidak mengingat apa pun dari panggilan sebelumnya — mengingat jangka panjang adalah tugas variabel global dan list.

## Miskonsepsi yang Sering Muncul

::: misconception
Keliru: "Kalau dua variabel namanya sama, berarti itu variabel yang sama, di mana pun ia ditulis."
Yang benar: nama hanyalah label; lingkuplah yang menentukan identitas variabel. `catatan` di dalam `setor` dan `catatan` di dalam perulangan `laporan` adalah dua variabel lokal yang **berbeda dan terpisah** — masing-masing hidup di "kotak" fungsinya sendiri. Mengubah yang satu tidak menyentuh yang lain. Dua fungsi hanya bisa berbagi data lewat variabel global, atau lewat parameter dan nilai balik.
:::

## Ke Mana Ilmu Ini Membawamu

Pola yang baru kamu latih — memilih antara global dan lokal, lalu menampung data berkelompok dalam list — adalah pola yang sama persis dengan yang dipakai di bahasa pemrograman sungguhan seperti Python dan JavaScript. Saat nanti kamu membangun aplikasi atau game yang lebih besar, kemampuan menjaga data tetap rapi lintas banyak fungsi inilah yang membedakan program yang mudah dikembangkan dari program yang kusut. Ilmu ini juga menjadi fondasi untuk struktur data yang lebih kaya, seperti tabel data dan objek, yang akan kamu temui di jenjang berikutnya.

::: check
Q: Fungsi setor dan laporan sama-sama memakai nama variabel catatan. Apakah keduanya bisa saling menimpa?
A: Tidak. Keduanya variabel lokal di fungsinya masing-masing, jadi berada di lingkup terpisah. Mereka hanya bisa "bertemu" lewat data yang disimpan di variabel global seperti riwayat.
Q: Mengapa kasKelas dan riwayat dibuat global, sementara catatan dibiarkan lokal?
A: Karena kasKelas dan riwayat harus bertahan lama dan dipakai bersama oleh lebih dari satu fungsi, sedangkan catatan hanya dibutuhkan sebentar di dalam setor. Aturan praktisnya: buat variabel selokal mungkin, dan jadikan global hanya jika datanya memang harus dibagi.
:::', NULL, NULL, 8, 0.6, '["k5_variables"]'::jsonb);
COMMIT;