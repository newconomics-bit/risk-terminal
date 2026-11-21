# Status Proyek Risk Terminal

## Wave 0 — Repository Skeleton dan Dokumentasi

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Membuat fondasi repository agar pengembangan bisa dimulai dengan struktur yang jelas.

### Acceptance Criteria
- [x] Repo memiliki `PRD.md`.
- [x] Repo memiliki `README.md` yang merujuk ke PRD.
- [x] `.gitignore` sudah mengecualikan `.env`, cache, venv, raw data sementara.
- [x] `.env.example` tersedia.
- [x] `requirements.txt` tersedia.
- [x] `config/settings.yaml` tersedia.
- [x] Folder `src`, `app`, `scripts`, `data`, `docs`, `.github/workflows` tersedia.
- [x] `docs/STATUS.md` tersedia dan menunjukkan Wave 0 done.

### Catatan
Struktur dasar repo sudah siap. Fokus berikutnya adalah Wave 1: FX Pipeline Minimum.

---

## Wave 1 — FX Pipeline Minimum

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Implementasi pipeline FX minimum: fetch USD/IDR, simpan ke JSON, scoring dasar.

### Acceptance Criteria
- [x] `src/fetchers/fx.py` fetch USD/IDR dari API publik.
- [x] Fallback data statis jika API gagal.
- [x] `src/analysis/scorer.py` menghitung currency_stress.
- [x] `scripts/run_pipeline.py` menjalankan pipeline end-to-end.
- [x] Output `data/latest.json` valid.

### Catatan
Pipeline FX berjalan. Selanjutnya Wave 2: Commodities.

---

## Wave 2 — Commodities Pipeline

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Menambahkan pipeline komoditas: Brent, Gold, CPO.

### Acceptance Criteria
- [x] `src/fetchers/commodities.py` fetch Brent, Gold, CPO.
- [x] Fallback data statis per komoditas.
- [x] Scorer menghitung commodity_stress.
- [x] Pipeline terintegrasi di `run_pipeline.py`.

### Catatan
Komoditas terintegrasi. Selanjutnya Wave 3: Geopolitical News.

---

## Wave 3 — Geopolitical News Pipeline

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Mengambil berita geopolitik dari RSS feed, filter keyword, hitung risk weight.

### Acceptance Criteria
- [x] `src/fetchers/news.py` fetch dari BBC, Al Jazeera, AP News.
- [x] Filter keyword dari `config/settings.yaml`.
- [x] Setiap event memiliki `risk_weight` tertinggi dari keyword match.
- [x] Scorer menghitung geopolitical_stress.

### Catatan
News pipeline berjalan. Selanjutnya Wave 4: Streamlit Dashboard.

---

## Wave 4 — Streamlit Dashboard

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Dashboard mobile-first dark theme menampilkan data dari `data/latest.json`.

### Acceptance Criteria
- [x] `app/streamlit_app.py` dengan 6 section: Header, Today's Brief, Market Pulse, Geopolitical Signals, Risk Components, Disclaimer.
- [x] Mobile-first responsive, dark theme.
- [x] Metric cards untuk USD/IDR dan komoditas.
- [x] Expander untuk detail berita geopolitik.
- [x] Fallback badge untuk data statis.

### Catatan
Dashboard siap. Selanjutnya Wave 5: CI/CD & Polish.

---

## Wave 5 — CI/CD, Polish & Hardening

**Status:** IN-PROGRESS

**Tanggal:** 2026-11-21

### Deskripsi
GitHub Actions workflow, self-check, hardening pipeline, dokumentasi.

### Acceptance Criteria
- [x] `.github/workflows/ci.yml` menjalankan pipeline scheduled + manual.
- [x] Self-check: `python -m compileall src scripts app` + `python scripts/run_pipeline.py --dry-run`.
- [x] Hotfix CI 44x gagal:
    - `scripts/run_pipeline.py`: bootstrap `sys.path` + `socket.setdefaulttimeout(15)` sebelum import `src`.
    - `src/fetchers/news.py`: RSS via `requests.get(timeout=10)` + `feedparser.parse(resp.content)` dalam try/except; feed Reuters 404 dihapus.
    - `app/streamlit_app.py`: hapus `st.set_page_config` ganda di `main()`; perbaiki link berita ke `[Baca selengkapnya]({link})`.
    - `docs/STATUS.md`: update Wave 1-4 done, Wave 5 in-progress + catatan hotfix.

### Catatan
Hotfix diterapkan, self-check lokal lolos. PR dibuat untuk review.
