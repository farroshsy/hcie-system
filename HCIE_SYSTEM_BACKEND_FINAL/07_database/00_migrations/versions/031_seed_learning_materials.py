"""Seed one reading-modality learning material per concept, in English and
Indonesian, tagged with the most-relevant learner archetypes.

Revision ID: 031_seed_learning_materials
Revises: 030_seed_archetype_tags_and_id_translations
Create Date: 2026-06-02 00:00:00.000000

This is the first content seed for the new ``learning_materials`` table.
We intentionally start small:

- One reading-modality material per concept, hand-authored in EN and ID.
- Tagged with ``vark_reading`` + a logical-or-explorer motivational tag,
  plus a concept-area-appropriate VARK tag where the content really
  *invites* a non-reading representation (e.g. networks → diagram is a
  fairer second VARK tag than visual+kinesthetic).
- Markdown bodies are short (3–6 minutes estimated read) so the
  "Material → Practice" flow stays sub-10 minutes per session.

Follow-up migrations will add video, audio, and interactive materials.
"""

from alembic import op
import sqlalchemy as sa
import json


revision = "031_seed_learning_materials"
down_revision = "030_seed_archetype_tags_and_id_translations"
branch_labels = None
depends_on = None


# (concept_id, en_title, en_body_md, id_title, id_body_md, archetype_tags)
MATERIALS = [
    # ── Algorithms ────────────────────────────────────────────────────────
    (
        "k2_algorithms", 3,
        "What is an algorithm?",
        """An **algorithm** is a clear set of steps to solve a problem.

Cooking instant noodles is an algorithm:

1. Boil water.
2. Open the packet.
3. Pour the noodles in.
4. Add seasoning.
5. Wait 3 minutes.

The order matters. If you add seasoning before pouring the noodles, the result is wrong. Programmers write algorithms the same way: a sequence of small, exact steps that always lead to the same outcome when the input is the same.

**Try to spot one:** brushing your teeth, tying your shoes, and walking to the school gate are all algorithms you do without thinking. The skill we are building is *writing* them down so a computer (or a friend) can follow them.""",
        "Apa itu algoritma?",
        """**Algoritma** adalah serangkaian langkah yang jelas untuk menyelesaikan suatu masalah.

Memasak mi instan adalah algoritma:

1. Rebus air.
2. Buka bungkus.
3. Masukkan mi.
4. Tambahkan bumbu.
5. Tunggu 3 menit.

Urutannya penting. Jika kamu menambahkan bumbu sebelum memasukkan mi, hasilnya akan salah. Programmer menulis algoritma dengan cara yang sama: urutan langkah-langkah kecil yang tepat yang selalu menghasilkan hasil yang sama jika masukannya sama.

**Coba kenali:** menyikat gigi, mengikat tali sepatu, dan berjalan ke gerbang sekolah semuanya adalah algoritma yang kamu lakukan tanpa berpikir. Keterampilan yang sedang kita bangun adalah *menuliskannya* agar komputer (atau teman) bisa mengikutinya.""",
        ["vark_reading", "vark_kinesthetic", "motiv_logical", "motiv_explorer"],
    ),
    (
        "k5_algorithms", 4,
        "Tracing and choosing efficient algorithms",
        """At this level we look at **two new skills**: *tracing* an algorithm step-by-step, and *choosing* between competing approaches.

### Tracing a loop

```
total = 0
repeat 5 times:
    total = total + 2
```

After each pass `total` becomes 2, 4, 6, 8, 10. The final value is **10**. We literally walk through every iteration to see what happens.

### Choosing the better approach

Suppose you have a sorted list of 100 names and need to find "Zainul":

- **Linear search**: check from the start — up to 100 steps.
- **Binary search**: open at the middle, decide whether to go left or right, halve the remaining list — about 7 steps.

Both work. Only one *scales*. As you write more programs you'll keep asking "is there a faster way?" — that question is the heart of algorithm design.""",
        "Menelusuri dan memilih algoritma efisien",
        """Pada tingkat ini kita mempelajari **dua keterampilan baru**: *menelusuri* algoritma langkah demi langkah, dan *memilih* di antara beberapa pendekatan.

### Menelusuri sebuah loop

```
total = 0
ulangi 5 kali:
    total = total + 2
```

Setelah tiap putaran, `total` menjadi 2, 4, 6, 8, 10. Nilai akhirnya adalah **10**. Kita benar-benar menelusuri setiap iterasi untuk melihat apa yang terjadi.

### Memilih pendekatan yang lebih baik

Misalkan kamu punya daftar 100 nama yang sudah terurut dan harus mencari "Zainul":

- **Pencarian linier**: periksa dari awal — sampai 100 langkah.
- **Pencarian biner**: buka di tengah, putuskan ke kiri atau kanan, bagi sisa daftar menjadi dua — sekitar 7 langkah.

Keduanya berhasil. Hanya satu yang *bisa diskalakan*. Saat kamu menulis lebih banyak program, kamu akan terus bertanya "apakah ada cara yang lebih cepat?" — pertanyaan itu adalah inti dari desain algoritma.""",
        ["vark_reading", "vark_kinesthetic", "motiv_logical", "behav_pathfinder"],
    ),
    (
        "k8_algorithms", 5,
        "Reasoning about efficiency",
        """When we say "Algorithm A is O(n²) and Algorithm B is O(n log n)", we're describing **how the work grows as the input gets bigger**, not the exact number of steps.

Imagine sorting a list of 1,000,000 items:

| Algorithm | Operations (approx.) |
| --- | --- |
| Bubble sort — O(n²) | 1,000,000,000,000 |
| Merge sort — O(n log n) | 20,000,000 |

That difference is the gap between 11 days and 0.02 seconds.

### Worst-case is what we usually quote

We measure the *worst-case* because that's the guarantee. An algorithm that's fast 99% of the time but catastrophically slow 1% of the time is unsafe for production. Whenever you read about a new algorithm, ask: *what is its worst-case behaviour?*

### The other dimension: memory

Speed isn't everything. Some algorithms are fast but greedy with memory. **Dynamic programming**, for example, trades memory (storing partial results) for speed.""",
        "Berpikir tentang efisiensi",
        """Ketika kita mengatakan "Algoritma A adalah O(n²) dan Algoritma B adalah O(n log n)", kita sedang menggambarkan **bagaimana pekerjaan tumbuh saat input membesar**, bukan jumlah langkah tepatnya.

Bayangkan mengurutkan daftar 1.000.000 item:

| Algoritma | Operasi (perkiraan) |
| --- | --- |
| Bubble sort — O(n²) | 1.000.000.000.000 |
| Merge sort — O(n log n) | 20.000.000 |

Perbedaannya adalah selisih antara 11 hari dan 0,02 detik.

### Worst-case yang biasanya dikutip

Kita mengukur *worst-case* karena itulah jaminannya. Algoritma yang cepat 99% waktu tapi sangat lambat 1% waktu tidak aman untuk produksi. Setiap kali kamu membaca tentang algoritma baru, tanyakan: *bagaimana perilaku worst-case-nya?*

### Dimensi lain: memori

Kecepatan bukan segalanya. Beberapa algoritma cepat tapi rakus memori. **Pemrograman dinamis** (DP), misalnya, mengorbankan memori (menyimpan hasil parsial) demi kecepatan.""",
        ["vark_reading", "motiv_logical", "behav_partner"],
    ),
    (
        "k12_algorithms", 6,
        "Designing for worst-case, not average-case",
        """At this level we move from *using* algorithms to *designing* them. The two questions you'll learn to answer cleanly:

1. **Is this correct?** Does the algorithm always terminate, and always return the right answer for valid input?
2. **Is this efficient?** What's the worst-case time and memory?

### Why worst-case dominates real engineering

Quicksort has an average-case of O(n log n) but a worst-case of O(n²) on already-sorted input. That worst-case appeared in real systems often enough that mainstream language standard libraries now use *introsort* — quicksort with a guard that swaps to heapsort when recursion depth exceeds a threshold. The change cost a tiny amount of average-case speed in exchange for a guarantee.

Designing for worst-case is how you make systems that don't surprise you in production.""",
        "Merancang untuk worst-case, bukan rata-rata",
        """Pada tingkat ini kita beralih dari *menggunakan* algoritma ke *merancangnya*. Dua pertanyaan yang harus dijawab dengan bersih:

1. **Apakah ini benar?** Apakah algoritmanya selalu berakhir, dan selalu mengembalikan jawaban tepat untuk input valid?
2. **Apakah ini efisien?** Berapa waktu dan memori worst-case-nya?

### Mengapa worst-case mendominasi rekayasa nyata

Quicksort memiliki average-case O(n log n) tapi worst-case O(n²) pada input yang sudah terurut. Worst-case itu cukup sering muncul di sistem nyata sehingga sekarang library standar bahasa utama menggunakan *introsort* — quicksort dengan pengaman yang beralih ke heapsort saat kedalaman rekursi melebihi ambang batas. Perubahan itu mengorbankan sedikit kecepatan rata-rata demi jaminan.

Merancang untuk worst-case adalah cara membangun sistem yang tidak mengejutkanmu di produksi.""",
        ["vark_reading", "motiv_logical", "behav_pathfinder"],
    ),

    # ── Control Structures ───────────────────────────────────────────────
    (
        "k2_control", 3,
        "Loops and conditions in everyday life",
        """Programs need to **make decisions** and **repeat actions**. Two simple building blocks do most of the work.

### The conditional (`if`)

```
IF it is raining:
    take an umbrella
```

The umbrella step only runs if the condition is true.

### The loop

```
REPEAT 10 times:
    water the next plant
```

The watering step runs ten times in a row. Both blocks let one short program describe a wide range of behaviour.""",
        "Loop dan kondisi dalam hidup sehari-hari",
        """Program perlu **membuat keputusan** dan **mengulang tindakan**. Dua blok bangunan sederhana melakukan sebagian besar pekerjaan.

### Kondisional (`if`)

```
JIKA hujan:
    bawa payung
```

Langkah membawa payung hanya berjalan jika kondisinya benar.

### Loop

```
ULANGI 10 kali:
    siram tanaman berikutnya
```

Langkah menyiram berjalan sepuluh kali berturut-turut. Kedua blok ini memungkinkan satu program pendek menggambarkan berbagai perilaku.""",
        ["vark_reading", "vark_kinesthetic", "motiv_logical"],
    ),
    (
        "k5_control", 4,
        "While loops and if-else",
        """A **while** loop keeps running as long as a condition is true:

```
score = 7
while score < 10:
    score = score + 1
```

Trace it: score is 7 (run), 8 (run), 9 (run), 10 (stop). The loop body ran 3 times.

**`if-else`** picks between two paths:

```
if score >= 75:
    print("Pass")
else:
    print("Fail")
```

If `score = 60`, only the `else` branch runs.

Both constructs are tools to express decisions concisely. Reading code at this level means walking through the values in your head, one line at a time.""",
        "While loop dan if-else",
        """**While** loop terus berjalan selama kondisinya benar:

```
score = 7
while score < 10:
    score = score + 1
```

Telusuri: score 7 (jalan), 8 (jalan), 9 (jalan), 10 (stop). Badan loop berjalan 3 kali.

**`if-else`** memilih antara dua jalur:

```
if score >= 75:
    cetak("Lulus")
else:
    cetak("Tidak Lulus")
```

Jika `score = 60`, hanya cabang `else` yang berjalan.

Keduanya adalah alat untuk mengekspresikan keputusan secara ringkas. Membaca kode pada tingkat ini berarti menelusuri nilai-nilai di pikiranmu, satu baris pada satu waktu.""",
        ["vark_reading", "motiv_logical", "behav_participant"],
    ),
    (
        "k8_control", 5,
        "Nested loops and boolean logic",
        """### Nested loops

When one loop sits inside another, the iterations multiply:

```
for i in [1, 2, 3, 4]:
    for j in [A, B, C]:
        print(i, j)
```

Outer runs 4 times; inner runs 3 times per outer iteration; total prints = 12.

### Boolean operators

```
(age >= 13) AND (has_permission == True)
```

- `AND`: both must be true.
- `OR`: at least one must be true.
- `NOT`: flips the result.

Combining them gives you precise control over which code runs.

### Event-driven code

In a UI, code attached to `onClick` only runs when the user clicks. It's still a conditional — the condition is just "did this event happen?" The control flow is *driven* by user actions rather than a single top-to-bottom run.""",
        "Loop bersarang dan logika boolean",
        """### Loop bersarang

Saat satu loop ada di dalam loop lain, iterasinya berlipat:

```
for i in [1, 2, 3, 4]:
    for j in [A, B, C]:
        cetak(i, j)
```

Loop luar berjalan 4 kali; loop dalam berjalan 3 kali per iterasi luar; total cetakan = 12.

### Operator boolean

```
(umur >= 13) AND (punya_izin == True)
```

- `AND`: keduanya harus benar.
- `OR`: setidaknya satu harus benar.
- `NOT`: membalik hasilnya.

Mengkombinasikannya memberimu kontrol presisi atas kode mana yang berjalan.

### Kode berbasis event

Dalam UI, kode yang terpasang pada `onClick` hanya berjalan saat pengguna mengklik. Itu tetap kondisional — kondisinya hanyalah "apakah event ini terjadi?". Alur kontrolnya *digerakkan* oleh tindakan pengguna, bukan satu kali jalan dari atas ke bawah.""",
        ["vark_reading", "motiv_logical", "behav_pathfinder"],
    ),
    (
        "k12_control", 5,
        "Reasoning about complexity from control flow",
        """Looking at code, you should be able to *predict* its complexity by reading the loop structure:

```
for i in range(n):           # n iterations
    for j in range(n):       # n iterations
        do_constant_work()   # O(1)
```

→ **O(n²)** total. Two nested n-loops with constant work inside = quadratic.

```
for i in range(n):           # n iterations
    do_log_work(n)           # O(log n) per iteration
```

→ **O(n log n)** — common in good sorting algorithms.

The skill is reading control flow as a *cost expression*. Most performance bugs come from a hidden inner loop the author didn't see.""",
        "Berpikir tentang kompleksitas dari alur kontrol",
        """Saat melihat kode, kamu harus bisa *memprediksi* kompleksitasnya dengan membaca struktur loop:

```
for i in range(n):           # n iterasi
    for j in range(n):       # n iterasi
        kerja_konstan()      # O(1)
```

→ **O(n²)** total. Dua n-loop bersarang dengan kerja konstan di dalam = kuadratik.

```
for i in range(n):           # n iterasi
    kerja_log(n)             # O(log n) per iterasi
```

→ **O(n log n)** — umum di algoritma pengurutan yang baik.

Keterampilannya adalah membaca alur kontrol sebagai *ekspresi biaya*. Sebagian besar bug performa muncul dari loop dalam tersembunyi yang tidak dilihat penulisnya.""",
        ["vark_reading", "motiv_logical", "behav_partner"],
    ),

    # ── Variables ────────────────────────────────────────────────────────
    (
        "k2_variables", 3,
        "What is a variable?",
        """A **variable** is a named box that holds a value.

```
lives = 3
score = 0
name = "Adi"
```

Each name on the left is a label. The value on the right is what the label points to. You can change what's inside the box without changing the label:

```
lives = 3
lives = lives - 1   # now lives is 2
```

The variable is the same `lives`; the value just updated. This is what makes a program able to *remember* and *change* during a single run.""",
        "Apa itu variabel?",
        """**Variabel** adalah kotak bernama yang menyimpan nilai.

```
nyawa = 3
nilai = 0
nama = "Adi"
```

Tiap nama di sebelah kiri adalah label. Nilai di sebelah kanan adalah apa yang ditunjuk label itu. Kamu bisa mengubah isi kotaknya tanpa mengubah labelnya:

```
nyawa = 3
nyawa = nyawa - 1   # sekarang nyawa adalah 2
```

Variabelnya tetap `nyawa` yang sama; nilainya yang berubah. Inilah yang membuat program bisa *mengingat* dan *berubah* selama satu kali jalan.""",
        ["vark_reading", "motiv_solitary", "motiv_logical"],
    ),
    (
        "k5_variables", 4,
        "Data types and assignment",
        """Variables aren't just numbers. Each variable has a **type**:

| Type | Example | Notes |
| --- | --- | --- |
| Integer | `42` | Whole numbers only |
| Float | `85.5` | Decimal numbers |
| Boolean | `True` / `False` | Yes/no values |
| String | `"Halo"` | Text — quoted |

The right type matters: a student's average score of 85.5 won't fit in an integer; storing it as a string blocks arithmetic.

### Assignment is one-way

```
x = 10
x = x + 3
```

Read this as "take the current value of x, add 3, store the result back in x". Not as math equality. After the second line, `x` is 13.""",
        "Tipe data dan penugasan",
        """Variabel tidak hanya berupa angka. Setiap variabel memiliki **tipe**:

| Tipe | Contoh | Catatan |
| --- | --- | --- |
| Integer | `42` | Hanya bilangan bulat |
| Float | `85.5` | Bilangan desimal |
| Boolean | `True` / `False` | Nilai ya/tidak |
| String | `"Halo"` | Teks — dengan kutip |

Tipe yang tepat itu penting: rata-rata nilai siswa 85.5 tidak muat di integer; menyimpannya sebagai string memblokir operasi aritmatika.

### Penugasan itu satu arah

```
x = 10
x = x + 3
```

Bacalah ini sebagai "ambil nilai x saat ini, tambah 3, simpan hasilnya kembali ke x". Bukan kesetaraan matematika. Setelah baris kedua, `x` adalah 13.""",
        ["vark_reading", "motiv_logical", "motiv_solitary"],
    ),
    (
        "k8_variables", 5,
        "Scope, lists, and structured data",
        """### Scope

A variable declared inside a function is **local** to it:

```
def f():
    x = 5      # local
    return x

f()
print(x)       # ERROR — x doesn't exist out here
```

Globals exist for the whole program; locals exist only while the function runs. Keeping things local is good practice — fewer accidental conflicts.

### Lists

```
names = ["Adi", "Budi", "Citra"]
names[1]   # → "Budi"  (indexes start at 0)
```

Lists let one variable hold many values in order. You'll combine them with loops constantly:

```
for n in names:
    print(n)
```

### Dictionaries (bonus)

```
ages = {"Adi": 14, "Budi": 13}
ages["Adi"]   # → 14
```

Dictionaries map a key to a value — a powerful next step once lists feel comfortable.""",
        "Cakupan, list, dan data terstruktur",
        """### Cakupan (Scope)

Variabel yang dideklarasikan di dalam fungsi bersifat **lokal**:

```
def f():
    x = 5      # lokal
    return x

f()
cetak(x)       # ERROR — x tidak ada di sini
```

Variabel global ada selama seluruh program; lokal hanya ada selama fungsi berjalan. Menjaga variabel tetap lokal adalah praktik yang baik — lebih sedikit konflik tidak sengaja.

### List

```
nama = ["Adi", "Budi", "Citra"]
nama[1]   # → "Budi"  (indeks mulai dari 0)
```

List memungkinkan satu variabel menyimpan banyak nilai berurutan. Kamu akan menggabungkannya dengan loop terus-menerus:

```
for n in nama:
    cetak(n)
```

### Dictionary (bonus)

```
umur = {"Adi": 14, "Budi": 13}
umur["Adi"]   # → 14
```

Dictionary memetakan kunci ke nilai — langkah berikutnya yang kuat saat kamu sudah nyaman dengan list.""",
        ["vark_reading", "motiv_logical", "behav_pathfinder"],
    ),

    # ── Modularity ───────────────────────────────────────────────────────
    (
        "k2_modularity", 3,
        "Breaking problems into pieces",
        """A big task is easier when you split it into small ones. Cleaning your room:

- Tidy the desk.
- Organize the books.
- Sweep the floor.

This is called **decomposition** — and it's exactly how programmers approach hard problems. Each small piece can be solved on its own.

### Naming and reusing

Once you teach a robot how to "wave hello", you can call that move five times without re-explaining it. The same idea in code is called a **procedure** or a **function**. Decomposition and reuse are two sides of the same coin.""",
        "Memecah masalah jadi bagian-bagian",
        """Tugas besar jadi lebih mudah saat kamu memecahnya menjadi beberapa yang kecil. Membersihkan kamar:

- Rapikan meja.
- Susun buku.
- Sapu lantai.

Ini disebut **dekomposisi** — dan persis itulah cara programmer mendekati masalah sulit. Setiap bagian kecil bisa diselesaikan sendiri-sendiri.

### Memberi nama dan menggunakan kembali

Begitu kamu mengajari robot cara "lambaikan halo", kamu bisa memanggil gerakan itu lima kali tanpa menjelaskannya lagi. Ide yang sama dalam kode disebut **prosedur** atau **fungsi**. Dekomposisi dan penggunaan kembali adalah dua sisi mata uang yang sama.""",
        ["vark_reading", "motiv_solitary", "behav_partner"],
    ),
    (
        "k5_modularity", 4,
        "Functions with parameters and return values",
        """A **function** is a reusable named block of code. It takes inputs (*parameters*) and gives back an output (*return value*):

```
def greet(name):
    print("Halo", name)

def square(n):
    return n * n
```

`greet("Siti")` prints `Halo Siti`. `square(4)` evaluates to `16`.

### Why functions exist

- **Don't repeat yourself.** If you'd write the same 5 lines in three places, write it once and call it three times.
- **Clear names.** `compute_grade(score)` reads better than 20 lines of math.
- **Easier testing.** A function with a return value can be tested in isolation.

A program built from many small, well-named functions is easier to read than the same program as one long script.""",
        "Fungsi dengan parameter dan nilai kembali",
        """**Fungsi** adalah blok kode bernama yang bisa digunakan kembali. Ia menerima input (*parameter*) dan mengembalikan output (*nilai kembali*):

```
def greet(name):
    cetak("Halo", name)

def kuadrat(n):
    return n * n
```

`greet("Siti")` mencetak `Halo Siti`. `kuadrat(4)` menghasilkan `16`.

### Mengapa fungsi ada

- **Jangan ulangi diri sendiri.** Jika kamu akan menulis 5 baris yang sama di tiga tempat, tulis sekali dan panggil tiga kali.
- **Nama yang jelas.** `hitung_nilai(skor)` lebih mudah dibaca dari 20 baris matematika.
- **Testing lebih mudah.** Fungsi dengan nilai kembali bisa diuji secara terpisah.

Program yang dibangun dari banyak fungsi kecil bernama bagus lebih mudah dibaca dari program yang sama sebagai satu skrip panjang.""",
        ["vark_reading", "motiv_logical", "behav_partner"],
    ),
    (
        "k8_modularity", 5,
        "Abstraction and refactoring",
        """The harder skill at this level is *deciding what to extract* into a function. A useful rule:

> If you see the same 5+ lines in three places, extract them.

### Abstraction = hiding details behind a name

Once `compute_grade(score)` exists, the rest of your code doesn't care how it's calculated. The function becomes a contract: "give me a score, I'll give you a grade". Months later when you change the grading rule, only one place needs to change.

### Refactoring

Refactoring is the discipline of improving structure *without* changing behaviour. Tests are the safety net: if the function passes the same tests before and after the refactor, the behaviour is preserved.

Modular, well-named, tested code is what separates "homework" from "production".""",
        "Abstraksi dan refactoring",
        """Keterampilan yang lebih sulit di tingkat ini adalah *memutuskan apa yang harus diekstrak* menjadi fungsi. Aturan yang berguna:

> Jika kamu melihat 5+ baris yang sama di tiga tempat, ekstraklah.

### Abstraksi = menyembunyikan detail di balik sebuah nama

Begitu `hitung_nilai(skor)` ada, sisa kodemu tidak peduli bagaimana ia dihitung. Fungsinya menjadi kontrak: "beri saya skor, saya beri kamu nilai". Berbulan-bulan kemudian saat kamu mengubah aturan penilaian, hanya satu tempat yang perlu diubah.

### Refactoring

Refactoring adalah disiplin memperbaiki struktur *tanpa* mengubah perilaku. Tes adalah jaring pengaman: jika fungsinya lulus tes yang sama sebelum dan sesudah refaktor, perilakunya terjaga.

Kode modular, bernama bagus, dan teruji inilah yang membedakan "tugas sekolah" dari "produksi".""",
        ["vark_reading", "motiv_logical", "behav_pathfinder"],
    ),

    # ── Program Development ──────────────────────────────────────────────
    (
        "k2_program_development", 3,
        "Read, run, debug",
        """The shortest workflow in programming is **read → run → debug**.

1. **Read** what's already there.
2. **Run** the program and watch what happens.
3. **Debug** if the output doesn't match your expectation.

Debugging at this stage is mostly about *noticing the difference*: I expected "Halo Adi", I got "Halo Adi Adi" — so something repeated. Each gap between expectation and reality is a clue.""",
        "Baca, jalankan, debug",
        """Alur kerja terpendek dalam pemrograman adalah **baca → jalankan → debug**.

1. **Baca** apa yang sudah ada.
2. **Jalankan** programnya dan lihat apa yang terjadi.
3. **Debug** jika output tidak sesuai harapanmu.

Debug pada tahap ini sebagian besar adalah *memperhatikan perbedaan*: saya berharap "Halo Adi", saya dapat "Halo Adi Adi" — jadi ada sesuatu yang berulang. Setiap kesenjangan antara harapan dan kenyataan adalah petunjuk.""",
        ["vark_reading", "vark_kinesthetic", "behav_participant"],
    ),
    (
        "k5_program_development", 4,
        "Plan → write → test → debug",
        """Real programs aren't written start-to-finish. The cycle is:

1. **Plan** — write what you want to happen in plain language first.
2. **Write** a small piece of code.
3. **Test** it with sample input.
4. **Debug** if it's wrong.
5. **Repeat** for the next piece.

Beginners often skip step 1 and jump to writing. That makes step 4 painful because the goal wasn't pinned down. Two minutes of planning saves twenty of debugging.""",
        "Rencanakan → tulis → uji → debug",
        """Program nyata tidak ditulis dari awal sampai akhir sekaligus. Siklusnya:

1. **Rencanakan** — tulis apa yang kamu mau terjadi dalam bahasa biasa dulu.
2. **Tulis** sepotong kecil kode.
3. **Uji** dengan input contoh.
4. **Debug** jika salah.
5. **Ulangi** untuk potongan berikutnya.

Pemula sering melewati langkah 1 dan langsung menulis. Itu membuat langkah 4 menyakitkan karena tujuannya belum diikat. Dua menit perencanaan menghemat dua puluh menit debug.""",
        ["vark_reading", "motiv_logical", "behav_pathfinder"],
    ),
    (
        "k8_program_development", 5,
        "Iterative development with version control",
        """Once programs grow, two practices change everything:

### Iterative development

Build a tiny working version first, then add one feature at a time. Each version *works*. Compare with building everything at once and discovering at the end that it doesn't run.

### Version control (Git)

A version-control system records every change you commit, lets you go back to any old version, and lets multiple people work on the same code without overwriting each other.

```
git add file.py
git commit -m "add login form"
git push
```

Three commands cover most day-to-day use. Branches let you try risky changes without breaking the working version.""",
        "Pengembangan iteratif dengan version control",
        """Begitu program membesar, dua praktik mengubah segalanya:

### Pengembangan iteratif

Bangun versi kecil yang bekerja dulu, lalu tambah satu fitur pada satu waktu. Setiap versi *bekerja*. Bandingkan dengan membangun semuanya sekaligus dan menemukan di akhir bahwa ia tidak berjalan.

### Version control (Git)

Sistem version control merekam setiap perubahan yang kamu commit, memungkinkanmu kembali ke versi lama mana pun, dan memungkinkan banyak orang bekerja pada kode yang sama tanpa saling menimpa.

```
git add file.py
git commit -m "tambah formulir login"
git push
```

Tiga perintah ini sudah mencakup sebagian besar penggunaan harian. Branch memungkinkanmu mencoba perubahan berisiko tanpa merusak versi yang bekerja.""",
        ["vark_reading", "motiv_logical", "behav_partner"],
    ),

    # ── Computing Systems ────────────────────────────────────────────────
    (
        "k2_computing_systems_devices", 3,
        "Hardware vs software",
        """**Hardware** is the physical part of a computer — what you can touch: keyboard, screen, hard drive, USB cable.

**Software** is the instructions stored digitally — what you cannot touch: an app on your phone, a game, a web browser.

### Input and output

- **Input devices** send data into the computer: keyboard, mouse, microphone.
- **Output devices** show data from the computer: screen, speaker, printer.

A touchscreen is both — it shows output and accepts input.""",
        "Perangkat keras vs perangkat lunak",
        """**Perangkat keras (hardware)** adalah bagian fisik komputer — yang bisa kamu sentuh: keyboard, layar, hard drive, kabel USB.

**Perangkat lunak (software)** adalah instruksi yang tersimpan secara digital — yang tidak bisa kamu sentuh: aplikasi di HP, game, browser web.

### Input dan output

- **Perangkat input** mengirim data ke komputer: keyboard, mouse, mikrofon.
- **Perangkat output** menampilkan data dari komputer: layar, speaker, printer.

Layar sentuh adalah keduanya — ia menampilkan output dan menerima input.""",
        ["vark_reading", "vark_visual", "vark_kinesthetic"],
    ),
    (
        "k5_computing_systems_devices", 4,
        "CPU, RAM, and storage",
        """A computer's three main jobs sit in three different places:

| Component | Job | Speed | Volatile? |
| --- | --- | --- | --- |
| **CPU** | Execute instructions | Very fast | — |
| **RAM** | Hold active data while running | Fast | Yes — empties when off |
| **Storage** (SSD/HDD) | Keep files between runs | Slow | No — survives reboots |

When you open a document, it loads from storage into RAM. The CPU reads and writes RAM millions of times per second. When you close without saving, the changes still in RAM disappear.

That's why "save your work" is the rule — it copies your changes from RAM back to storage.""",
        "CPU, RAM, dan penyimpanan",
        """Tiga tugas utama komputer ada di tiga tempat berbeda:

| Komponen | Tugas | Kecepatan | Volatil? |
| --- | --- | --- | --- |
| **CPU** | Eksekusi instruksi | Sangat cepat | — |
| **RAM** | Menyimpan data aktif saat berjalan | Cepat | Ya — kosong saat mati |
| **Penyimpanan** (SSD/HDD) | Simpan file antar sesi | Lambat | Tidak — bertahan saat restart |

Saat kamu membuka dokumen, ia dimuat dari penyimpanan ke RAM. CPU membaca dan menulis RAM jutaan kali per detik. Saat kamu menutup tanpa menyimpan, perubahan yang masih di RAM hilang.

Karena itu "simpan pekerjaanmu" adalah aturan utama — ia menyalin perubahan dari RAM kembali ke penyimpanan.""",
        ["vark_reading", "vark_visual", "motiv_logical"],
    ),
    (
        "k8_computing_systems_devices", 5,
        "Operating systems and the fetch-decode-execute cycle",
        """The **operating system (OS)** is the program that runs other programs. It:

- Manages memory between apps so they don't trample each other.
- Talks to hardware (printer, network, screen) through drivers.
- Manages the file system.
- Schedules which program gets CPU time next.

It does **not** itself execute the *fetch-decode-execute* cycle — that's the CPU's hardware loop:

1. **Fetch** the next instruction from RAM.
2. **Decode** what kind of instruction it is.
3. **Execute** it.
4. Repeat — billions of times per second.

The OS hands instructions to the CPU; the CPU runs them.""",
        "Sistem operasi dan siklus fetch-decode-execute",
        """**Sistem operasi (OS)** adalah program yang menjalankan program lain. Ia:

- Mengelola memori antar aplikasi agar tidak saling mengganggu.
- Berbicara ke perangkat keras (printer, jaringan, layar) lewat driver.
- Mengelola file system.
- Menjadwalkan program mana yang dapat waktu CPU berikutnya.

Ia **tidak** menjalankan sendiri siklus *fetch-decode-execute* itu — itu adalah loop perangkat keras CPU:

1. **Fetch** instruksi berikutnya dari RAM.
2. **Decode** jenis instruksi apa itu.
3. **Execute** instruksinya.
4. Ulangi — milyaran kali per detik.

OS menyerahkan instruksi ke CPU; CPU menjalankannya.""",
        ["vark_reading", "motiv_logical", "behav_partner"],
    ),

    # ── Networks ─────────────────────────────────────────────────────────
    (
        "k2_networks_communication", 3,
        "Networks and the internet",
        """Two or more computers that are connected so they can share data form a **network**.

A school computer lab where three computers share files is a small network. The **internet** is the world's biggest network — it's "a network of networks" that links billions of devices so they can exchange data.

When you visit a website, your device sends a request through the internet to a faraway computer (a *server*) and gets data back. That round trip can finish in a tenth of a second — even when the server is on the other side of the world.""",
        "Jaringan dan internet",
        """Dua atau lebih komputer yang terhubung sehingga bisa berbagi data membentuk **jaringan**.

Lab komputer sekolah dimana tiga komputer berbagi file adalah jaringan kecil. **Internet** adalah jaringan terbesar di dunia — ia adalah "jaringan dari jaringan-jaringan" yang menghubungkan miliaran perangkat agar bisa bertukar data.

Saat kamu mengunjungi situs web, perangkatmu mengirim permintaan lewat internet ke komputer yang jauh (sebuah *server*) dan menerima data kembali. Perjalanan bolak-balik itu bisa selesai dalam sepersepuluh detik — bahkan ketika servernya ada di sisi lain dunia.""",
        ["vark_reading", "vark_visual", "motiv_explorer"],
    ),
    (
        "k5_networks_communication", 4,
        "Protocols and packets",
        """A **protocol** is a set of rules for communication. When two computers don't share a protocol, they can't talk — like two people speaking different languages without a translator.

- **HTTP**: how browsers and web servers exchange pages.
- **SMTP**: how email is sent.
- **TCP/IP**: the underlying transport everything rides on.

### Packets

The internet doesn't send a file in one giant chunk. It splits it into **packets** — small fragments — and each packet can travel its own path. If one packet gets lost or delayed, only that one is re-sent. The pieces are reassembled in order at the destination.

This is why the internet is fast *and* resilient: a broken cable in one country doesn't stop traffic; packets just route around it.""",
        "Protokol dan paket",
        """**Protokol** adalah seperangkat aturan untuk komunikasi. Saat dua komputer tidak berbagi protokol, mereka tidak bisa berbicara — seperti dua orang yang berbicara bahasa berbeda tanpa penerjemah.

- **HTTP**: bagaimana browser dan server web bertukar halaman.
- **SMTP**: bagaimana email dikirim.
- **TCP/IP**: transport dasar yang menjalankan semuanya.

### Paket

Internet tidak mengirim file dalam satu potongan besar. Ia memecahnya menjadi **paket** — fragmen kecil — dan setiap paket bisa menempuh jalurnya sendiri. Jika satu paket hilang atau terlambat, hanya yang itu dikirim ulang. Potongan-potongannya disusun kembali sesuai urutan di tujuan.

Inilah mengapa internet cepat *dan* tangguh: kabel putus di satu negara tidak menghentikan lalu lintas; paket-paket dialihkan saja.""",
        ["vark_reading", "vark_visual", "motiv_explorer"],
    ),
    (
        "k8_networks_communication", 5,
        "IP addressing and basic cybersecurity",
        """### IP addresses

Every device on a network has an **IP address** — a unique number that lets packets find it. `192.168.1.5` is a typical local address; the public internet uses globally unique addresses.

Routers use IP addresses the way a postal service uses house numbers: read the destination and forward the packet on the next hop.

### Cybersecurity basics

Three threats you'll keep seeing:

- **Phishing**: fake messages pretending to be your bank, school, or government, asking for passwords. Defence: never trust an unsolicited link; type the address yourself.
- **Malware**: programs that do harm if you run them. Defence: don't run code from untrusted sources.
- **Weak passwords**: short or common passwords get cracked in seconds. Defence: long, unique passwords, ideally managed by a password manager.

Security is mostly about *habits*, not gadgets.""",
        "Pengalamatan IP dan dasar keamanan siber",
        """### Alamat IP

Setiap perangkat di jaringan memiliki **alamat IP** — angka unik yang memungkinkan paket menemukannya. `192.168.1.5` adalah alamat lokal khas; internet publik menggunakan alamat unik secara global.

Router menggunakan alamat IP seperti layanan pos menggunakan nomor rumah: baca tujuan dan teruskan paket di lompatan berikutnya.

### Dasar keamanan siber

Tiga ancaman yang akan terus kamu lihat:

- **Phishing**: pesan palsu berpura-pura jadi bank, sekolah, atau pemerintah, meminta password. Pertahanan: jangan pernah percaya tautan yang tidak diminta; ketik alamatnya sendiri.
- **Malware**: program yang merusak jika kamu menjalankannya. Pertahanan: jangan jalankan kode dari sumber tidak terpercaya.
- **Password lemah**: password pendek atau umum bisa dipecahkan dalam hitungan detik. Pertahanan: password panjang, unik, idealnya dikelola password manager.

Keamanan sebagian besar tentang *kebiasaan*, bukan perangkat.""",
        ["vark_reading", "motiv_logical", "behav_partner"],
    ),

    # ── Data Analysis ────────────────────────────────────────────────────
    (
        "k2_data_collection", 3,
        "Collecting and reading data",
        """**Data** is information you can count or sort. To answer "which fruit is most popular in our class?", you can't just guess — you need to *collect* the data:

- Ask each student their favourite fruit.
- Record the answer (a tally mark works).
- Count totals.

A simple bar chart shows the result at a glance:

```
Mango   ████████ 8
Banana  █████ 5
Apple   ███ 3
```

Mango wins because its bar is tallest. The data answered the question.""",
        "Mengumpulkan dan membaca data",
        """**Data** adalah informasi yang bisa kamu hitung atau urutkan. Untuk menjawab "buah mana yang paling populer di kelas kita?", kamu tidak bisa hanya menebak — kamu perlu *mengumpulkan* datanya:

- Tanya setiap siswa buah favoritnya.
- Catat jawabannya (tally mark bisa).
- Hitung totalnya.

Diagram batang sederhana menampilkan hasilnya secara langsung:

```
Mangga  ████████ 8
Pisang  █████ 5
Apel    ███ 3
```

Mangga menang karena batangnya paling tinggi. Datanya menjawab pertanyaannya.""",
        ["vark_reading", "vark_visual", "behav_participant"],
    ),
    (
        "k5_data_collection", 4,
        "Patterns, trends, and the correlation trap",
        """Once data is collected, the next step is *finding patterns*.

Temperatures over 7 days: 28, 30, 29, 31, 30, 32, 31. Day-to-day it fluctuates, but the overall direction is **up**. We say the temperature is *trending* upward.

### Correlation ≠ causation

You may notice that students who eat breakfast score higher on tests. That is a **correlation**: two things move together. It does *not* prove breakfast causes the higher scores — maybe both are caused by a third thing (more sleep, more supportive parents).

Confusing the two is the most common data-analysis mistake in the world. Trained scientists make it all the time. The cure is asking: *what other explanation fits this data?*""",
        "Pola, tren, dan jebakan korelasi",
        """Begitu data terkumpul, langkah berikutnya adalah *menemukan pola*.

Suhu selama 7 hari: 28, 30, 29, 31, 30, 32, 31. Hari per hari ia berfluktuasi, tapi arah keseluruhannya **naik**. Kita katakan suhunya sedang *tren* naik.

### Korelasi ≠ kausalitas

Kamu mungkin memperhatikan siswa yang sarapan punya nilai tes lebih tinggi. Itu adalah **korelasi**: dua hal bergerak bersama. Itu *tidak* membuktikan sarapan menyebabkan nilai lebih tinggi — mungkin keduanya disebabkan hal ketiga (tidur lebih nyenyak, orang tua lebih suportif).

Mengacaukan keduanya adalah kesalahan analisis data paling umum di dunia. Ilmuwan terlatih melakukannya terus-menerus. Obatnya adalah bertanya: *penjelasan lain apa yang cocok dengan data ini?*""",
        ["vark_reading", "motiv_logical", "behav_pathfinder"],
    ),
    (
        "k8_data_collection", 5,
        "Statistical thinking and sampling bias",
        """Real data analysis is messy. Two skills matter most:

### Sampling bias

If you survey only students in the computer lab about their technology use, you'll over-estimate how much the average student uses technology — because students in the computer lab self-select for being technology-comfortable. Your sample doesn't represent the population.

Good sampling is **random** and **representative**. Convenience samples (whoever you happen to ask) are biased by default.

### Cleaning data

Real data has missing values, typos, and outliers. Before any analysis you check:

- Are there `NULL` or blank rows?
- Are there impossible values (age = 250)?
- Are there outliers — and if so, are they real or measurement errors?

Skipping cleaning gives you wrong answers with confidence.""",
        "Berpikir statistik dan bias sampling",
        """Analisis data nyata itu berantakan. Dua keterampilan paling penting:

### Bias sampling

Jika kamu hanya mensurvei siswa di lab komputer tentang penggunaan teknologi mereka, kamu akan terlalu meninggikan estimasi penggunaan teknologi siswa rata-rata — karena siswa di lab komputer memilih diri sendiri sebagai yang nyaman dengan teknologi. Sampelmu tidak merepresentasikan populasinya.

Sampling yang baik bersifat **acak** dan **representatif**. Sampel konvenien (siapa saja yang kebetulan kamu tanya) bias secara default.

### Membersihkan data

Data nyata memiliki nilai hilang, typo, dan outlier. Sebelum analisis apapun kamu periksa:

- Adakah baris `NULL` atau kosong?
- Adakah nilai mustahil (umur = 250)?
- Adakah outlier — dan jika ya, apakah nyata atau error pengukuran?

Melewati pembersihan memberi kamu jawaban salah dengan percaya diri.""",
        ["vark_reading", "motiv_logical", "behav_partner"],
    ),
    (
        "k12_data_collection", 5,
        "Machine learning, training data, and bias",
        """A **machine learning** model learns patterns from a training dataset. Two things matter:

### Train / test split

You hold out a **test set** the model never sees during training. After training, you measure performance on the test set — that's your estimate of how well the model will work on real, future data. Evaluating only on the training set measures memorisation, not learning.

### Bias in, bias out

If a loan-approval model is trained on historical decisions and those decisions were biased against a group, the model learns the bias and **scales it up**. The model doesn't know it's being unfair; it's just predicting the pattern in its training data.

This is the central ethics issue in AI today: the model is only as fair as the data it was given.""",
        "Machine learning, data pelatihan, dan bias",
        """Sebuah model **machine learning** belajar pola dari dataset pelatihan. Dua hal penting:

### Pemisahan train / test

Kamu menyisihkan sebuah **test set** yang tidak pernah dilihat model selama pelatihan. Setelah pelatihan, kamu mengukur performa pada test set — itu adalah estimasi seberapa baik model akan bekerja pada data nyata di masa depan. Mengevaluasi hanya pada set pelatihan mengukur hafalan, bukan pembelajaran.

### Bias masuk, bias keluar

Jika sebuah model persetujuan pinjaman dilatih pada keputusan historis dan keputusan-keputusan itu bias terhadap suatu kelompok, model akan belajar biasnya dan **memperbesarnya**. Model tidak tahu ia tidak adil; ia hanya memprediksi pola di data pelatihannya.

Inilah isu etika sentral di AI hari ini: model hanya seadil data yang diberikan padanya.""",
        ["vark_reading", "motiv_logical", "behav_pathfinder", "motiv_explorer"],
    ),

    # ── Social Impacts ───────────────────────────────────────────────────
    (
        "k2_culture", 3,
        "Technology in everyday life",
        """Technology is a tool. Its effects depend on **how** it's used.

A smartphone helps you contact family far away. The same phone, used during dinner, can make you ignore the family next to you. Both are real effects of the same tool.

### Online safety basics

- Personal information like your home address or full name shouldn't be shared in public posts.
- If something online makes you uncomfortable, tell a trusted adult.
- Strangers online aren't always who they say they are.

These three habits prevent most problems young learners face online.""",
        "Teknologi dalam hidup sehari-hari",
        """Teknologi adalah alat. Efeknya tergantung **bagaimana** ia digunakan.

Sebuah smartphone membantumu menghubungi keluarga yang jauh. Telepon yang sama, digunakan saat makan malam, bisa membuatmu mengabaikan keluarga di sebelahmu. Keduanya adalah efek nyata dari alat yang sama.

### Dasar keamanan online

- Informasi pribadi seperti alamat rumahmu atau nama lengkap tidak boleh dibagikan di postingan publik.
- Jika sesuatu online membuatmu tidak nyaman, beri tahu orang dewasa yang dipercaya.
- Orang asing online tidak selalu siapa yang mereka katakan.

Tiga kebiasaan ini mencegah sebagian besar masalah yang dihadapi pelajar muda online.""",
        ["vark_reading", "motiv_social", "behav_participant"],
    ),
    (
        "k5_culture", 4,
        "Digital citizenship and intellectual property",
        """Being a **digital citizen** means using technology responsibly. Two ideas at this stage:

### Plagiarism

Copying someone's paragraph from a website and submitting it as your own is *plagiarism*. The internet hasn't changed the rule; it's just made copying easier. If you use someone else's words, you cite the source.

### Footprint

Anything you post online is hard to fully remove. Even after you delete it, copies might already exist (screenshots, archives, search caches). The general rule: don't post anything you wouldn't want a future employer or school to read.

Both ideas come down to the same point: be the digital citizen you'd want others to be.""",
        "Kewarganegaraan digital dan kekayaan intelektual",
        """Menjadi **warga digital** berarti menggunakan teknologi dengan bertanggung jawab. Dua gagasan pada tahap ini:

### Plagiarisme

Menyalin paragraf seseorang dari situs web dan menyerahkannya sebagai milikmu adalah *plagiarisme*. Internet tidak mengubah aturannya; hanya membuat penyalinan lebih mudah. Jika kamu menggunakan kata-kata orang lain, sebutkan sumbernya.

### Jejak

Apa pun yang kamu posting online sulit dihapus sepenuhnya. Bahkan setelah kamu hapus, salinan mungkin sudah ada (screenshot, arsip, cache pencarian). Aturan umum: jangan posting apa pun yang tidak ingin kamu baca oleh pemberi kerja atau sekolah masa depan.

Kedua gagasan ini bermuara pada hal yang sama: jadilah warga digital seperti yang kamu inginkan orang lain.""",
        ["vark_reading", "motiv_social", "behav_partner"],
    ),
    (
        "k8_culture", 5,
        "Privacy, ethics, and algorithmic bias",
        """At this stage we move from "be careful online" to *evaluating the ethics of computing systems themselves*.

### Privacy

A free app is usually free because your data is the product. Map apps track your location; social media tracks who you talk to; smart speakers send audio to a cloud. None of this is inherently wrong — the question is whether you've meaningfully consented and what's done with the data.

### Algorithmic bias

A hiring algorithm trained on data that historically favoured men will recommend men. A face-recognition model trained mostly on light-skinned faces will work worse on dark-skinned faces. These aren't bugs in the math; they're consequences of the training data. *Whose data the algorithm was given matters as much as the algorithm itself.*

Asking "who benefits from this system, and who is harmed?" is now part of being technically literate.""",
        "Privasi, etika, dan bias algoritmik",
        """Pada tahap ini kita beralih dari "berhati-hati online" ke *mengevaluasi etika sistem komputasi itu sendiri*.

### Privasi

Aplikasi gratis biasanya gratis karena datamulah produknya. Aplikasi peta melacak lokasimu; media sosial melacak siapa yang kamu ajak bicara; speaker pintar mengirim audio ke cloud. Tidak ada yang inheren salah dengan ini — pertanyaannya adalah apakah kamu telah memberi persetujuan yang berarti dan apa yang dilakukan dengan datanya.

### Bias algoritmik

Algoritma perekrutan yang dilatih pada data yang secara historis lebih memihak laki-laki akan merekomendasikan laki-laki. Model pengenalan wajah yang dilatih mayoritas pada wajah berkulit terang akan bekerja lebih buruk pada wajah berkulit gelap. Ini bukan bug di matematikanya; ini konsekuensi data pelatihannya. *Data siapa yang diberikan ke algoritma sama pentingnya dengan algoritmanya sendiri.*

Bertanya "siapa yang diuntungkan sistem ini, dan siapa yang dirugikan?" sekarang adalah bagian dari literasi teknis.""",
        ["vark_reading", "motiv_social", "motiv_explorer", "behav_pathfinder"],
    ),
]


def upgrade():
    bind = op.get_bind()
    for (
        concept_id, est_min, en_title, en_body, id_title, id_body, tags,
    ) in MATERIALS:
        # Insert EN
        en_id = f"{concept_id}_reading_en_v1"
        exists = bind.execute(
            sa.text("SELECT 1 FROM learning_materials WHERE id = :id"), {"id": en_id}
        ).first()
        if not exists:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO learning_materials (
                        id, concept_id, language, modality, archetype_tags,
                        title, body, estimated_minutes, difficulty,
                        prerequisites_assumed, metadata
                    ) VALUES (
                        :id, :concept_id, 'en', 'reading', CAST(:tags AS jsonb),
                        :title, :body, :est_min, 0.4,
                        '[]'::jsonb, '{}'::jsonb
                    )
                    """
                ),
                {
                    "id": en_id,
                    "concept_id": concept_id,
                    "tags": json.dumps(tags),
                    "title": en_title,
                    "body": en_body,
                    "est_min": est_min,
                },
            )

        # Insert ID
        id_id = f"{concept_id}_reading_id_v1"
        exists = bind.execute(
            sa.text("SELECT 1 FROM learning_materials WHERE id = :id"), {"id": id_id}
        ).first()
        if not exists:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO learning_materials (
                        id, concept_id, language, modality, archetype_tags,
                        title, body, estimated_minutes, difficulty,
                        prerequisites_assumed, metadata
                    ) VALUES (
                        :id, :concept_id, 'id', 'reading', CAST(:tags AS jsonb),
                        :title, :body, :est_min, 0.4,
                        '[]'::jsonb, '{}'::jsonb
                    )
                    """
                ),
                {
                    "id": id_id,
                    "concept_id": concept_id,
                    "tags": json.dumps(tags),
                    "title": id_title,
                    "body": id_body,
                    "est_min": est_min,
                },
            )


def downgrade():
    bind = op.get_bind()
    for (concept_id, *_rest) in MATERIALS:
        bind.execute(
            sa.text("DELETE FROM learning_materials WHERE id IN (:en_id, :id_id)"),
            {
                "en_id": f"{concept_id}_reading_en_v1",
                "id_id": f"{concept_id}_reading_id_v1",
            },
        )
