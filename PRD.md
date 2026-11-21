# Risk Terminal — Product Requirements Document (PRD)

## Metadata

- **Project Name:** Risk Terminal
- **Repository:** `risk-terminal`
- **Version:** 0.1 MVP
- **Status:** Active
- **Owner:** Personal use
- **Primary User:** Owner / operator pribadi
- **Target Platform:** Mobile-first web dashboard, later可 dibungkus jadi PWA/APK
- **Core Constraint:** Harus bisa dikembangkan dan dijalankan dengan sumber daya minimal: HP Android, GitHub, free tier, tanpa database SQL di MVP.

---

## 1. Latar Belakang

Risk Terminal adalah dashboard pribadi untuk memantau kondisi makroekonomi dan risiko geopolitik yang dapat memengaruhi harga, supply chain, biaya input, kurs, dan keputusan bisnis sehari-hari.

Produk ini dibuat untuk pengguna yang tertarik pada makroekonomi, geopolitik, supply chain, dan teknologi, tetapi memiliki keterbatasan perangkat dan budget. Oleh karena itu, sistem harus sederhana, gratis, otomatis, dan mudah dirawat.

---

## 2. Tujuan Produk

Risk Terminal harus mampu menjawab 3 pertanyaan utama:

1. **Bagaimana kondisi makroekonomi hari ini?**
2. **Apakah ada risiko geopolitik yang dapat mengganggu harga, pasokan, atau perdagangan?**
3. **Apa aksi praktis yang sebaiknya dilakukan?**

### Tujuan Bisnis / Personal

- Memberikan early warning terhadap tekanan kurs dan komoditas.
- Membantu pengguna memahami dampak berita geopolitik terhadap ekonomi riil.
- Menjadi portofolio teknis dan analitis yang kredibel.
- Dapat dijalankan otomatis tanpa memerlukan server berbayar.
- Dapat dibungkus menjadi aplikasi mobile sederhana di kemudian hari.

---

## 3. Non-Goals / Di Luar Scope MVP

MVP **tidak** mencakup:

- Database SQL.
- Login user.
- Multi-user collaboration.
- Real-time tick data seperti trading terminal profesional.
- Rekomendasi investasi otomatis.
- Model ekonometrika kompleks.
- Backend API berbayar.
- Aplikasi native Android/iOS penuh.
- Scraping situs yang melanggar ToS.
- Penyimpanan secrets/API key di dalam kode.

---

## 4. Prinsip Produk

1. **Mobile-first**
   - UI harus nyaman dibuka di HP layar kecil.
   - Satu kolom, kartu besar, font terbaca, minim klik.

2. **Terminal style**
   - Dark mode.
   - Nuansa dashboard risiko / command center.
   - Warna status: hijau, kuning, merah.

3. **Simple before smart**
   - Gunakan rule-based scoring dulu.
   - Jangan masuk ke model AI/ML kompleks di MVP.

4. **Free and sustainable**
   - Gunakan GitHub Actions sebagai scheduler.
   - Gunakan JSON sebagai storage utama.
   - Hindari dependency berat.

5. **Explainable**
   - Setiap skor risiko harus bisa dijelaskan komponen penyusunnya.
   - Kode diberi komentar bahasa Indonesia agar mudah dipahami.

6. **Safe by default**
   - Tidak menyimpan API key di kode.
   - Menggunakan `.env`, `.env.example`, dan GitHub Secrets.
   - Pipeline harus aman dijalankan berulang kali / idempotent.

---

## 5. Pengguna

### Primary User

Pengguna pribadi yang ingin memantau:

- Kurs USD/IDR.
- Harga komoditas utama.
- Berita geopolitik.
- Risiko supply chain.
- Dampak ekonomi terhadap keputusan kerja/bisnis.

### Secondary Viewer

Orang lain yang diberi link dashboard, misalnya:

- Rekan kerja.
- Atasan.
- Calon recruiter / portofolio reviewer.

Secondary viewer hanya melihat, tidak mengedit konfigurasi di MVP.

---

## 6. Scope MVP

MVP terdiri dari:

1. Pipeline pengambilan data.
2. Perhitungan skor risiko sederhana.
3. Penyimpanan hasil ke JSON.
4. Dashboard Streamlit mobile-first.
5. Otomatisasi harian via GitHub Actions.
6. Notifikasi Telegram opsional.
7. Panduan pembungkusan menjadi PWA/APK sederhana.

---

## 7. Functional Requirements

### FR-01: Konfigurasi Pusat

Sistem harus memiliki file konfigurasi pusat di:

```text
config/settings.yaml
```

Konfigurasi minimal berisi:

- Base currency.
- Quote currency.
- Watchlist komoditas.
- Keyword geopolitik.
- Threshold alert.
- Threshold skor risiko kuning dan merah.

Contoh struktur:

```yaml
market:
  base_currency: USD
  quote_currency: IDR
  lookback_days: 30

commodities:
  watchlist:
    - brent
    - gold
    - cpo

geopolitics:
  keywords:
    - red sea
    - suez
    - malacca
    - south china sea
    - tariff
    - sanction
    - export control
    - brics
    - de-dollarization
    - supply chain

alerts:
  usdidr_move_pct: 1.5
  commodity_move_pct: 3.0
  risk_score_yellow: 50
  risk_score_red: 70
```

---

### FR-02: Fetcher Kurs USD/IDR

Sistem harus memiliki modul untuk mengambil kurs USD/IDR.

File:

```text
src/fetchers/fx.py
```

Sumber data prioritas:

- API gratis tanpa key, misalnya `open.er-api.com`.
- Jika gagal, gunakan fallback dummy data dengan struktur sama.

Output minimal:

```json
{
  "symbol": "USDIDR",
  "rate": 16250,
  "change_1d_pct": 0.8,
  "change_7d_pct": 2.1,
  "as_of": "2026-10-04T06:00:00+07:00",
  "source": "open.er-api.com"
}
```

Jika data historis belum tersedia, `change_7d_pct` boleh diisi `null` atau dihitung dari histori JSON yang tersimpan sebelumnya.

---

### FR-03: Fetcher Komoditas

Sistem harus memiliki modul untuk mengambil harga komoditas.

File:

```text
src/fetchers/commodities.py
```

Komoditas MVP:

- Brent crude oil.
- Gold.
- CPO.

Sumber data:

- Gunakan sumber publik yang stabil jika tersedia.
- Jika sumber tidak stabil atau membutuhkan key, buat fallback dummy data.
- Struktur output harus konsisten.

Output per komoditas:

```json
{
  "symbol": "BRENT",
  "name": "Brent Crude Oil",
  "price": 82.4,
  "unit": "USD/bbl",
  "change_1d_pct": 1.9,
  "change_7d_pct": null,
  "as_of": "2026-10-04T06:00:00+07:00",
  "source": "fallback"
}
```

---

### FR-04: Fetcher Berita Geopolitik

Sistem harus memiliki modul untuk membaca RSS feed dan memfilter berita berdasarkan keyword.

File:

```text
src/fetchers/news.py
```

Sumber RSS prioritas:

- Reuters World/Business jika feed tersedia.
- AP News.
- BBC Business.
- Al Jazeera Economy.
- Sumber publik lain yang legal dan stabil.

Filter keyword diambil dari `config/settings.yaml`.

Output event:

```json
{
  "title": "Kapal kargo alami gangguan di Laut Merah",
  "link": "https://example.com/news",
  "source": "Reuters",
  "published_at": "2026-10-04T05:30:00Z",
  "tags": ["red_sea", "shipping", "supply_chain"],
  "risk_weight": 30,
  "matched_keywords": ["red sea", "supply chain"]
}
```

Bobot risiko keyword awal:

| Keyword / Topik | Risk Weight |
|---|---:|
| red sea | 30 |
| suez | 25 |
| malacca | 25 |
| south china sea | 30 |
| tariff | 20 |
| sanction | 25 |
| export control | 25 |
| brics | 10 |
| de-dollarization | 10 |
| supply chain | 20 |

Jika satu berita mengandung banyak keyword, ambil risk weight tertinggi, bukan penjumlahan berlebihan.

---

### FR-05: Risk Scorer

Sistem harus memiliki modul perhitungan skor risiko.

File:

```text
src/analysis/scorer.py
```

Skor risiko berada pada rentang 0–100.

Komponen skor:

#### 1. Currency Stress

Berdasarkan perubahan USD/IDR:

| Kondisi | Poin |
|---|---:|
| change_1d_pct >= 1.0 | +10 |
| change_1d_pct >= 2.0 | +20 |
| change_1d_pct >= 3.0 | +30 |
| change_7d_pct >= 5.0 | +20 |

Gunakan poin tertinggi yang terpenuhi, bukan akumulasi semua tier.

#### 2. Commodity Stress

Untuk setiap komoditas watchlist:

| Kondisi | Poin |
|---|---:|
| change_1d_pct >= 3.0 | +10 |

Cap total commodity stress: 30 poin.

#### 3. Geopolitical News Stress

Berdasarkan berita yang terfilter:

- Jumlahkan risk weight event.
- Cap total geopolitical stress: 40 poin.

#### 4. Volatility / Missing Data Penalty

Opsional sederhana:

- Jika banyak data memakai fallback dummy, tambahkan +5 sampai +10 sebagai uncertainty penalty.

Level status:

| Skor | Level |
|---:|---|
| 0–49 | GREEN |
| 50–69 | YELLOW |
| 70–100 | RED |

Threshold dapat dibaca dari `config/settings.yaml`.

Output scorer:

```json
{
  "score": 58,
  "level": "YELLOW",
  "headline": "Rupiah melemah dan risiko jalur pelayaran meningkat",
  "recommended_action": "Pantau supplier dan tahan pembelian besar sampai tren kurs lebih jelas.",
  "components": {
    "currency_stress": 20,
    "commodity_stress": 10,
    "geopolitical_stress": 25,
    "uncertainty_penalty": 3
  }
}
```

---

### FR-06: Output JSON Terbaru

Pipeline harus menghasilkan file:

```text
data/latest.json
```

Struktur minimal:

```json
{
  "meta": {
    "generated_at": "2026-10-04T06:00:00+07:00",
    "timezone": "Asia/Jakarta",
    "version": "0.1.0",
    "pipeline_run_id": "manual-or-gha"
  },
  "status": {
    "level": "YELLOW",
    "score": 58,
    "headline": "Rupiah melemah dan risiko jalur pelayaran meningkat",
    "recommended_action": "Pantau supplier dan tahan pembelian besar sampai tren kurs lebih jelas."
  },
  "market": {
    "fx": {
      "usdidr": {
        "symbol": "USDIDR",
        "rate": 16250,
        "change_1d_pct": 0.8,
        "change_7d_pct": 2.1,
        "as_of": "2026-10-04T06:00:00+07:00",
        "source": "open.er-api.com"
      }
    },
    "commodities": [
      {
        "symbol": "BRENT",
        "name": "Brent Crude Oil",
        "price": 82.4,
        "unit": "USD/bbl",
        "change_1d_pct": 1.9,
        "change_7d_pct": null,
        "as_of": "2026-10-04T06:00:00+07:00",
        "source": "fallback"
      }
    ]
  },
  "geopolitics": {
    "events": [],
    "keyword_counts": {},
    "top_tags": []
  },
  "impact": {
    "import_cost_pressure": "MEDIUM",
    "input_price_risk": "MEDIUM",
    "supply_chain_risk": "MEDIUM"
  }
}
```

Pipeline juga harus menyimpan salinan harian ke:

```text
data/history/YYYY-MM-DD.json
```

Aturan:

- Jika file history hari yang sama sudah ada, overwrite dengan data terbaru.
- Jangan menyimpan data terlalu granular di MVP.
- Jangan commit file besar tanpa perlu.

---

### FR-07: Pipeline Runner

Sistem harus memiliki script utama:

```text
scripts/run_pipeline.py
```

Fungsi pipeline:

1. Load konfigurasi.
2. Fetch FX.
3. Fetch commodities.
4. Fetch news.
5. Hitung skor risiko.
6. Susun payload `latest.json`.
7. Simpan ke `data/latest.json`.
8. Simpan ke `data/history/YYYY-MM-DD.json`.
9. Print ringkasan ke console.

Pipeline harus mendukung mode:

```bash
python scripts/run_pipeline.py
```

dan idealnya:

```bash
python scripts/run_pipeline.py --dry-run
```

`--dry-run` berarti:

- Tidak menulis file ke disk, atau menulis ke temporary output.
- Cocok untuk self-check Kilo Code.

---

### FR-08: Dashboard Streamlit

Sistem harus memiliki dashboard:

```text
app/streamlit_app.py
```

Dashboard membaca:

```text
data/latest.json
```

Jika file belum ada, tampilkan pesan onboarding:

> Data belum tersedia. Jalankan pipeline terlebih dahulu atau tunggu GitHub Actions selesai berjalan.

Dashboard harus mobile-first.

#### Section 1: Header

Tampilkan:

- Nama produk: Risk Terminal.
- Tanggal dan waktu generated.
- Status level: GREEN / YELLOW / RED.
- Skor risiko.

Contoh:

```text
RISK TERMINAL
2026-10-04 06:00 WIB
STATUS: YELLOW
SCORE: 58/100
```

#### Section 2: Today’s Brief

Tampilkan:

- Headline risiko.
- Recommended action.
- Ringkasan tekanan import cost / input price / supply chain.

#### Section 3: Market Pulse

Tampilkan metrik:

- USD/IDR.
- Brent.
- Gold.
- CPO.

Gunakan `st.metric` jika memungkinkan.

Tampilkan:

- Nilai terkini.
- Perubahan 1 hari.
- Sumber data.
- Badge jika memakai fallback.

#### Section 4: Geopolitical Signals

Tampilkan daftar berita/event:

- Judul.
- Sumber.
- Waktu.
- Tag.
- Risk weight.

Gunakan expander agar tidak penuh di HP.

#### Section 5: Risk Components

Tampilkan breakdown skor:

- Currency stress.
- Commodity stress.
- Geopolitical stress.
- Uncertainty penalty.

#### Section 6: Footer / Disclaimer

Tampilkan disclaimer:

> Proyek ini untuk edukasi dan analisis pribadi. Bukan rekomendasi keuangan atau investasi.

---

### FR-09: Otomatisasi GitHub Actions

Sistem harus memiliki workflow:

```text
.github/workflows/fetch-data.yml
```

Fungsi:

- Menjalankan pipeline secara terjadwal.
- Default jadwal: setiap hari pukul 23.00 UTC, setara 06.00 WIB.
- Mendukung manual trigger via `workflow_dispatch`.
- Melakukan commit otomatis jika ada perubahan file di folder `data/`.

Workflow minimal:

```yaml
name: Fetch Macro Geo Data

on:
  schedule:
    - cron: "0 23 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install -r requirements.txt

      - run: python scripts/run_pipeline.py

      - name: Commit data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "chore: update risk terminal data"
          git push
```

Catatan:

- Jika tidak ada perubahan data, jangan buat commit kosong.
- Workflow tidak boleh gagal hanya karena satu sumber berita tidak tersedia, selama fallback berfungsi.

---

### FR-10: Telegram Alert Opsional

Sistem boleh memiliki modul notifikasi:

```text
src/notify/telegram.py
```

Fungsi:

- Mengirim ringkasan status ke Telegram.
- Hanya dikirim jika status YELLOW atau RED, kecuali dikonfigurasi lain.

Environment variables:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Aturan:

- Jika secrets tidak ada, pipeline tetap jalan normal tanpa error fatal.
- Jangan pernah menaruh token di kode.
- Pesan harus singkat dan mobile-friendly.

Contoh pesan:

```text
RISK TERMINAL: YELLOW
Score: 58/100

USD/IDR: 16,250 (+0.8%)
Brent: 82.4 (+1.9%)

Top signal:
- Gangguan pelayaran di Laut Merah
- Isu tarif perdagangan

Action:
Pantau supplier dan tahan pembelian besar sampai tren kurs jelas.
```

---

### FR-11: PWA / APK Readiness

MVP tidak wajib menghasilkan file APK langsung, tetapi harus mempersiapkan jalur pembungkusan.

Requirement:

- Dashboard harus bisa dibuka di browser HP.
- UI harus cocok untuk Add to Home Screen / PWA.
- Harus ada dokumentasi cara membungkus menjadi APK sederhana.

File dokumentasi:

```text
docs/PACKAGING.md
```

Isi minimal:

- Cara deploy Streamlit ke Streamlit Community Cloud.
- Cara buka di HP.
- Cara Add to Home Screen.
- Cara konversi URL menjadi APK menggunakan WebView converter eksternal.
- Catatan bahwa APK hasil wrapper bukan native app penuh.

---

## 8. Non-Functional Requirements

### NFR-01: Resource Efficiency

- Harus bisa dikembangkan dari HP Android kelas entry-level.
- Hindari library berat di MVP.
- Hindari proses yang memakan RAM besar.

### NFR-02: Maintainability

- Kode harus modular.
- Setiap file harus punya tanggung jawab jelas.
- Komentar bahasa Indonesia wajib ada di bagian penting.

### NFR-03: Reliability

- Fetcher harus punya error handling.
- Jika satu sumber gagal, gunakan fallback.
- Pipeline tidak boleh crash hanya karena satu news feed kosong.

### NFR-04: Security

- Secrets hanya lewat environment variable / GitHub Secrets.
- `.env` harus ada di `.gitignore`.
- `.env.example` harus disediakan.

### NFR-05: Portability

- Struktur repo harus mudah dipindahkan ke laptop/PC jika nanti upgrade perangkat.
- Tidak boleh bergantung pada satu mesin lokal.

### NFR-06: Auditability

- Setiap run pipeline harus menyertakan timestamp.
- History harian disimpan agar bisa dilihat tren sederhana.

---

## 9. Arsitektur Sistem

### Alur Utama

```text
GitHub Actions cron
   ↓
scripts/run_pipeline.py
   ↓
src/fetchers/fx.py
src/fetchers/commodities.py
src/fetchers/news.py
   ↓
src/analysis/scorer.py
   ↓
data/latest.json
data/history/YYYY-MM-DD.json
   ↓
app/streamlit_app.py
   ↓
Mobile browser / PWA / WebView APK
   ↓
Optional: src/notify/telegram.py
```

### Storage Strategy

MVP menggunakan:

- JSON file.
- Git history.
- Folder `data/history/`.

Tidak menggunakan:

- SQLite.
- PostgreSQL.
- MySQL.
- Supabase.
- Firebase.

Database baru dipertimbangkan jika:

- Data histori sudah terlalu besar.
- Butuh query cepat lintas tanggal.
- Butuh multi-user/login.
- Butuh alert rule yang disimpan permanen.

---

## 10. Struktur Repository

Struktur wajib:

```text
risk-terminal/
├── PRD.md
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── config/
│   └── settings.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── history/
├── docs/
│   ├── STATUS.md
│   └── PACKAGING.md
├── src/
│   ├── fetchers/
│   │   ├── fx.py
│   │   ├── commodities.py
│   │   └── news.py
│   ├── analysis/
│   │   └── scorer.py
│   ├── notify/
│   │   └── telegram.py
│   └── utils/
│       ├── io.py
│       └── logging.py
├── app/
│   └── streamlit_app.py
├── scripts/
│   └── run_pipeline.py
└── .github/
    └── workflows/
        └── fetch-data.yml
```

Aturan folder:

- Folder kosong boleh diisi `.gitkeep`.
- Jangan commit file secret.
- Jangan commit cache atau virtual environment.

---

## 11. UI/UX Specification

### Desain Visual

- Dark background.
- Aksen warna:
  - Hijau untuk GREEN.
  - Kuning/amber untuk YELLOW.
  - Merah untuk RED.
- Font angka sebaiknya monospace jika memungkinkan.
- Gunakan kartu besar.
- Hindari tabel lebar yang merusak tampilan HP.

### Layout Mobile

Satu kolom vertikal:

1. Header status.
2. Today’s brief.
3. Market pulse.
4. Geopolitical signals.
5. Risk components.
6. Disclaimer.

### Interaksi

- Minimal scroll.
- Expand/collapse untuk detail berita.
- Tidak perlu form input di MVP.
- Tidak perlu login.

### Tone Bahasa

- Singkat.
- Operasional.
- Bukan akademis berat.
- Contoh:
  - “Tekanan biaya input: SEDANG”
  - “Aksi: pantau supplier, tahan pembelian besar”

---

## 12. Risk Scoring Specification

### Formula Sederhana

```text
total_score =
  currency_stress
  + commodity_stress
  + geopolitical_stress
  + uncertainty_penalty
```

Cap:

```text
max 100
```

### Level Mapping

```text
0–49  = GREEN
50–69 = YELLOW
70–100 = RED
```

### Recommended Action Logic

Contoh rule:

#### GREEN

```text
Kondisi relatif stabil. Lanjutkan pemantauan rutin.
```

#### YELLOW

```text
Waspadai tekanan kurs dan biaya input. Tahan pembelian besar sampai tren lebih jelas.
```

#### RED

```text
Risiko tinggi. Tinjau ulang supplier, stok, kontrak harga, dan eksposur valuta asing.
```

Jika geopolitical stress tinggi:

```text
Pantau jalur pelayaran dan lead time pengiriman.
```

Jika currency stress tinggi:

```text
Prioritaskan hedging sederhana, percepat pembayaran impor jika menguntungkan, atau tunda pembelian non-esensial.
```

---

## 13. Data Contract

File `data/latest.json` harus selalu mengikuti schema minimal di FR-06.

Aturan:

- Field wajib tidak boleh hilang.
- Jika data tidak tersedia, isi `null`.
- Jangan mengubah nama field tanpa memperbarui dashboard.
- Versi schema dicatat di `meta.version`.

---

## 14. Configuration Contract

File `config/settings.yaml` adalah sumber kebenaran untuk:

- Watchlist.
- Keyword.
- Threshold.
- Currency pair.

Kode tidak boleh hardcode keyword atau threshold di dalam function jika sudah ada di config.

---

## 15. Logging dan Error Handling

Modul logging:

```text
src/utils/logging.py
```

Minimum:

- Log info saat pipeline mulai.
- Log warning jika fetcher memakai fallback.
- Log error jika modul kritis gagal.
- Log info saat file JSON disimpan.

Pipeline tidak boleh menampilkan traceback mentah ke user akhir di dashboard.

---

## 16. Testing Strategy

MVP tidak wajib unit test lengkap, tetapi harus punya self-check.

### Self-check Minimum

1. Syntax check Python:

```bash
python -m compileall src scripts app
```

2. Pipeline dry-run:

```bash
python scripts/run_pipeline.py --dry-run
```

3. Validasi JSON:

- File `data/latest.json` bisa diparse.
- Field wajib ada.

4. Streamlit smoke check:

- `app/streamlit_app.py` tidak error saat dijalankan.
- Jika `latest.json` tidak ada, app tetap menampilkan pesan ramah.

---

## 17. Wave Plan

Pengerjaan dibagi per wave. Kilo Code harus menyelesaikan wave demi wave sesuai acceptance criteria.

---

### Wave 0 — Repository Skeleton dan Dokumentasi

#### Goal

Membuat fondasi repo agar Kilo Code punya struktur jelas.

#### Deliverables

- `PRD.md`
- `README.md`
- `.gitignore`
- `.env.example`
- `requirements.txt`
- `config/settings.yaml`
- Folder struktur dasar.
- `docs/STATUS.md`

#### Acceptance Criteria

- [ ] Repo memiliki `PRD.md`.
- [ ] Repo memiliki `README.md` yang merujuk ke PRD.
- [ ] `.gitignore` sudah mengecualikan `.env`, cache, venv, raw data sementara.
- [ ] `.env.example` tersedia.
- [ ] `requirements.txt` tersedia.
- [ ] `config/settings.yaml` tersedia.
- [ ] Folder `src`, `app`, `scripts`, `data`, `docs`, `.github/workflows` tersedia.
- [ ] `docs/STATUS.md` tersedia dan menunjukkan Wave 0 done.

#### Commit Message

```text
chore: scaffold risk terminal repository
```

---

### Wave 1 — FX Pipeline Minimum

#### Goal

Pipeline bisa mengambil kurs USD/IDR dan menghasilkan JSON minimal.

#### Deliverables

- `src/fetchers/fx.py`
- `src/utils/io.py`
- `scripts/run_pipeline.py` versi awal
- `data/latest.json` contoh hasil run

#### Acceptance Criteria

- [ ] `fx.py` memiliki fungsi fetch kurs USD/IDR.
- [ ] Ada error handling dan fallback dummy.
- [ ] Pipeline bisa dijalankan.
- [ ] `data/latest.json` terbentuk.
- [ ] JSON minimal berisi `meta`, `status`, `market.fx.usdidr`.
- [ ] Tidak ada secret di kode.
- [ ] Komentar bahasa Indonesia ada di fungsi penting.

#### Commit Message

```text
feat: add fx fetcher and minimal pipeline
```

---

### Wave 2 — Commodities dan News Fetcher

#### Goal

Menambahkan data komoditas dan berita geopolitik.

#### Deliverables

- `src/fetchers/commodities.py`
- `src/fetchers/news.py`
- Update `scripts/run_pipeline.py`
- Update `data/latest.json`

#### Acceptance Criteria

- [ ] Commodities fetcher mengembalikan list minimal Brent, Gold, CPO.
- [ ] News fetcher membaca RSS dan memfilter keyword dari config.
- [ ] Jika RSS gagal, pipeline tetap jalan dengan event kosong atau fallback.
- [ ] `latest.json` berisi `market.commodities` dan `geopolitics.events`.
- [ ] Ada `keyword_counts` atau minimal top tags.
- [ ] Tidak ada hardcode keyword di luar config.

#### Commit Message

```text
feat: add commodity and geopolitical news fetchers
```

---

### Wave 3 — Risk Scorer

#### Goal

Menghitung skor risiko dan status GREEN/YELLOW/RED.

#### Deliverables

- `src/analysis/scorer.py`
- Update pipeline
- Update `latest.json`

#### Acceptance Criteria

- [ ] Scorer mengembalikan score 0–100.
- [ ] Level mengikuti threshold config.
- [ ] Headline自动生成 berdasarkan komponen dominan.
- [ ] Recommended action muncul sesuai level.
- [ ] `latest.json` memiliki `status` lengkap.
- [ ] Breakdown komponen skor tersedia.

#### Commit Message

```text
feat: add rule-based risk scorer
```

---

### Wave 4 — Streamlit Dashboard MVP

#### Goal

Menampilkan data JSON sebagai dashboard mobile-first.

#### Deliverables

- `app/streamlit_app.py`
- Update README dengan cara run lokal.

#### Acceptance Criteria

- [ ] Dashboard membaca `data/latest.json`.
- [ ] Jika file tidak ada, tampil pesan onboarding, bukan crash.
- [ ] Header menampilkan status, skor, waktu.
- [ ] Market pulse menampilkan USD/IDR dan komoditas.
- [ ] Geopolitical signals menampilkan berita/event.
- [ ] Risk components menampilkan breakdown skor.
- [ ] Disclaimer tampil.
- [ ] Layout nyaman di HP.

#### Commit Message

```text
feat: add mobile-first streamlit dashboard
```

---

### Wave 5 — GitHub Actions Automation

#### Goal

Pipeline jalan otomatis setiap hari.

#### Deliverables

- `.github/workflows/fetch-data.yml`

#### Acceptance Criteria

- [ ] Workflow terjadwal setiap hari 23.00 UTC.
- [ ] Workflow mendukung manual dispatch.
- [ ] Workflow install dependencies.
- [ ] Workflow menjalankan pipeline.
- [ ] Workflow commit perubahan di folder `data/` jika ada.
- [ ] Tidak commit jika tidak ada perubahan.
- [ ] Workflow tidak membutuhkan secret wajib untuk jalan dasar.

#### Commit Message

```text
ci: schedule daily risk data pipeline
```

---

### Wave 6 — Telegram Alert Opsional

#### Goal

Mengirim notifikasi ke Telegram jika status YELLOW/RED.

#### Deliverables

- `src/notify/telegram.py`
- Update pipeline atau workflow.
- Update `.env.example`.

#### Acceptance Criteria

- [ ] Jika secret tidak ada, sistem skip notifikasi tanpa crash.
- [ ] Jika secret ada, pesan terkirim.
- [ ] Pesan ringkas dan mobile-friendly.
- [ ] Token tidak pernah tertulis di kode.
- [ ] Notifikasi default hanya untuk YELLOW/RED.

#### Commit Message

```text
feat: add optional telegram risk alerts
```

---

### Wave 7 — PWA/APK Packaging Guide

#### Goal

Menyiapkan jalur agar dashboard bisa dipakai seperti aplikasi HP.

#### Deliverables

- `docs/PACKAGING.md`
- Update README.

#### Acceptance Criteria

- [ ] Dokumentasi cara deploy Streamlit tersedia.
- [ ] Dokumentasi Add to Home Screen tersedia.
- [ ] Dokumentasi konversi URL ke APK WebView tersedia.
- [ ] Ada catatan keterbatasan wrapper APK.
- [ ] Tidak wajib membangun APK native di MVP.

#### Commit Message

```text
docs: add pwa and apk packaging guide
```

---

## 18. Definition of Done MVP

Risk Terminal dianggap selesai MVP jika:

- [ ] Semua Wave 0 sampai Wave 5 selesai.
- [ ] GitHub Actions bisa menjalankan pipeline otomatis.
- [ ] `data/latest.json` tersedia dan valid.
- [ ] Dashboard Streamlit bisa dibuka di HP.
- [ ] Tidak ada secret yang ter-commit.
- [ ] README menjelaskan cara pakai.
- [ ] STATUS.md menandai MVP done.
- [ ] Kode memiliki komentar bahasa Indonesia di bagian penting.
- [ ] Tidak ada database SQL yang dipakai.

Wave 6 dan Wave 7 adalah enhancement, tetapi sangat disarankan.

---

## 19. Future Scope / Backlog

Setelah MVP stabil, fitur lanjutan:

1. SQLite atau DuckDB untuk histori lebih rapi.
2. FastAPI backend jika butuh API resmi.
3. Login dan multi-user.
4. Alert rule custom per user.
5. Grafik tren 30/90 hari.
6. Integrasi data BPS/BI untuk inflasi lokal.
7. Tracking supplier lokal.
8. Sentiment analysis berita.
9. Ship tracking API untuk chokepoint.
10. Notifikasi email.
11. Native Android app.
12. Mode offline ringan.

---

## 20. AI Build Rules

Kilo Code atau AI coding agent wajib mematuhi aturan berikut:

1. `PRD.md` adalah sumber kebenaran tertinggi.
2. Kerjakan per wave.
3. Jangan loncat wave sebelum acceptance criteria wave aktif terpenuhi.
4. Jangan menambah database SQL di MVP.
5. Jangan menyimpan secrets di kode.
6. Gunakan komentar bahasa Indonesia.
7. Utamakan solusi sederhana dan gratis.
8. Jika ada ambiguitas, pilih opsi MVP paling sederhana dan catat asumsi di `docs/STATUS.md`.
9. Setiap iterasi harus melakukan self-check.
10. Jika self-check gagal, revisi sebelum commit.
11. Jika self-check lulus, commit dengan conventional commit message.
12. Perbarui `docs/STATUS.md` setiap selesai satu wave atau satu subtask penting.
13. Jangan menghapus file data histori tanpa instruksi eksplisit.
14. Jangan mengubah schema JSON tanpa memperbarui dashboard.
15. Jangan menambah dependency berat tanpa alasan jelas.

---

## 21. Disclaimer

Produk ini untuk edukasi, analisis pribadi, dan pemantauan risiko.  
Bukan rekomendasi investasi, bukan nasihat keuangan, dan bukan jaminan akurasi data.