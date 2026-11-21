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
Implementasi fetcher USD/IDR dengan fallback, penyimpanan JSON, dan pipeline runner.

### Acceptance Criteria
- [x] `src/fetchers/fx.py` dengan `fetch_usdidr()` dan fallback.
- [x] `src/utils/io.py` untuk save/load JSON.
- [x] `scripts/run_pipeline.py` menjalankan fetch FX dan simpan `data/latest.json`.
- [x] Pipeline menghasilkan output sesuai schema FR-06.

### Catatan
FX pipeline berjalan. Selanjutnya Wave 2: Commodities.

---

## Wave 2 — Commodities Pipeline

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Fetcher untuk Brent, Gold, CPO dengan struktur konsisten dan fallback.

### Acceptance Criteria
- [x] `src/fetchers/commodities.py` dengan `fetch_all()`.
- [x] Output per komoditas sesuai schema FR-03.
- [x] Pipeline terintegrasi di `run_pipeline.py`.

### Catatan
Komoditas terintegrasi. Selanjutnya Wave 3: News/Geopolitics.

---

## Wave 3 — News & Geopolitical Signals

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Fetcher RSS feed, filter keyword geopolitik, risk weight per event.

### Acceptance Criteria
- [x] `src/fetchers/news.py` dengan `fetch_news()`.
- [x] RSS feed: BBC, Al Jazeera, AP News (Reuters dihapus: 404).
- [x] Keyword matching dari `config/settings.yaml`.
- [x] Output events dengan `risk_weight` tertinggi.

### Catatan
News pipeline berjalan. Selanjutnya Wave 4: Risk Scorer.

---

## Wave 4 — Risk Scorer & Dashboard

**Status:** DONE

**Tanggal:** 2026-10-04

### Deskripsi
Perhitungan skor risiko 0-100 dan dashboard Streamlit mobile-first.

### Acceptance Criteria
- [x] `src/analysis/scorer.py` dengan `calculate_score()`.
- [x] Komponen: currency, commodity, geopolitical, uncertainty penalty.
- [x] Level: GREEN (0-49), YELLOW (50-69), RED (70-100).
- [x] `app/streamlit_app.py` dengan 6 section per FR-08.
- [x] Output `data/latest.json` lengkap sesuai schema FR-06.

### Catatan
Dashboard berfungsi. Selanjutnya Wave 5: Automation & Polish.

---

## Wave 5 — Automation & Polish (In-Progress)

**Status:** IN-PROGRESS

**Tanggal:** 2026-10-04

### Deskripsi
GitHub Actions scheduling, notifikasi Telegram, PWA/APK guide, dan hotfix stabilitas.

### Acceptance Criteria
- [ ] `.github/workflows/fetch-data.yml` jadwal harian 23:00 UTC.
- [ ] Notifikasi Telegram opsional via `src/notify/telegram.py`.
- [ ] Dokumentasi PWA/APK di `docs/pwa-guide.md`.
- [x] **Hotfix**: `scripts/run_pipeline.py` bootstrap `sys.path` untuk CI.
- [x] **Hotfix**: `src/fetchers/news.py` requests timeout + hapus feed Reuters 404.
- [x] **Hotfix**: `app/streamlit_app.py` hapus `st.set_page_config` duplikat, perbaiki link berita.

### Catatan
Wave 5 fokus pada otomatisasi dan finishing. Hotfix sudah diterapkan untuk stabilitas pipeline dan dashboard.
