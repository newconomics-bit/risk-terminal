#!/usr/bin/env python3
"""
Pipeline runner untuk Risk Terminal.
Fungsi:
  1. Load konfigurasi.
  2. Fetch data FX.
  3. Fetch data komoditas.
  4. Fetch berita geopolitik.
  5. Hitung skor risiko.
  6. Susun payload latest.json.
  7. Simpan ke data/latest.json.
  8. Simpan salinan harian ke data/history/YYYY-MM-DD.json.
  9. Print ringkasan ke console.

Mendukung mode --dry-run untuk self-check tanpa menulis file.
"""

import argparse
import logging
from datetime import datetime, timezone, timedelta

from src.fetchers.fx import fetch_usdidr
from src.fetchers.commodities import fetch_all as fetch_commodities
from src.fetchers.news import fetch_news
from src.analysis.scorer import calculate_score
from src.utils.io import save_json

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Zona waktu Indonesia (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))


def run(dry_run=False):
    """
    Menjalankan pipeline lengkap: FX, komoditas, berita, scorer.
    """
    logger.info("Pipeline dimulai...")

    # Fetch data FX
    fx_data = fetch_usdidr()

    # Fetch data komoditas
    commodities = fetch_commodities()

    # Fetch berita geopolitik
    news_data = fetch_news()

    # Susun struktur latest.json
    now = datetime.now(WIB)
    meta = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
        "timezone": "Asia/Jakarta",
        "version": "0.1.0",
        "pipeline_run_id": "manual-or-gha",
    }

    # Susun data untuk scoring
    latest_for_scoring = {
        "market": {
            "fx": {
                "usdidr": fx_data,
            },
            "commodities": commodities,
        },
        "geopolitics": news_data,
    }

    # Hitung skor risiko
    status = calculate_score(latest_for_scoring)

    latest = {
        "meta": meta,
        "status": status,
        "market": {
            "fx": {
                "usdidr": fx_data,
            },
            "commodities": commodities,
        },
        "geopolitics": {
            "events": news_data.get("events", []),
            "keyword_counts": news_data.get("keyword_counts", {}),
            "top_tags": news_data.get("top_tags", []),
        },
        "impact": {
            "import_cost_pressure": _calc_impact_level(status["components"]["currency_stress"]),
            "input_price_risk": _calc_impact_level(status["components"]["commodity_stress"]),
            "supply_chain_risk": _calc_impact_level(status["components"]["geopolitical_stress"]),
        },
    }

    if dry_run:
        logger.info("Mode dry-run: data tidak ditulis ke disk.")
        import json

        print(json.dumps(latest, ensure_ascii=False, indent=2))
        return

    # Simpan ke data/latest.json
    save_json(latest, "data/latest.json")

    # Simpan salinan harian
    history_path = f"data/history/{now.strftime('%Y-%m-%d')}.json"
    save_json(latest, history_path)

    logger.info("Pipeline selesai. Score: %d (%s)", status["score"], status["level"])


def _calc_impact_level(score):
    """
    Menghitung level dampak berdasarkan skor komponen.
    Skor 0 = LOW, 1-19 = MEDIUM, 20+ = HIGH.
    """
    if score >= 20:
        return "HIGH"
    elif score >= 10:
        return "MEDIUM"
    else:
        return "LOW"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Risk Terminal Pipeline")
    parser.add_argument(
        "--dry-run", action="store_true", help="Jalankan tanpa menulis file ke disk"
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)