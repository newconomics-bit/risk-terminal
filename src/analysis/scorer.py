"""
Modul perhitungan skor risiko.
Skor berada pada rentang 0–100.
Komponen:
  1. Currency stress (berdasarkan perubahan USD/IDR).
  2. Commodity stress (berdasarkan perubahan komoditas watchlist).
  3. Geopolitical news stress (berdasarkan risk weight berita).
  4. Volatility / missing data penalty.
"""

import logging
import os
import yaml

from src.utils.io import load_json

logger = logging.getLogger(__name__)


def _load_config():
    """
    Memuat konfigurasi dari config/settings.yaml.
    """
    config_path = "config/settings.yaml"
    if not os.path.exists(config_path):
        logger.warning("File konfigurasi %s tidak ditemukan.", config_path)
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_thresholds():
    """
    Mengambil threshold alert dari konfigurasi.
    """
    config = _load_config()
    alerts = config.get("alerts", {})

    thresholds = {
        "usdidr_move_pct": alerts.get("usdidr_move_pct", 1.5),
        "commodity_move_pct": alerts.get("commodity_move_pct", 3.0),
        "risk_score_yellow": alerts.get("risk_score_yellow", 50),
        "risk_score_red": alerts.get("risk_score_red", 70),
    }

    return thresholds


def _calc_currency_stress(fx_data):
    """
    Menghitung skor tekanan kurs.
    Menggunakan poin tertinggi yang terpenuhi, bukan akumulasi.
    """
    if fx_data is None:
        return 0

    change_1d = fx_data.get("change_1d_pct")
    change_7d = fx_data.get("change_7d_pct")

    # Hapus logika berbahaya: gunakan abs() agar pergerakan naik/turun sama-sama menambah skor.
    score_1d = 0
    if change_1d is not None:
        abs_1d = abs(float(change_1d))
        if abs_1d >= 3.0:
            score_1d = 30
        elif abs_1d >= 2.0:
            score_1d = 20
        elif abs_1d >= 1.0:
            score_1d = 10

    score_7d = 0
    if change_7d is not None:
        abs_7d = abs(float(change_7d))
        if abs_7d >= 5.0:
            score_7d = 20

    # Ambil skor tertinggi, bukan penjumlahan.
    return max(score_1d, score_7d)


def _calc_commodity_stress(commodities):
    """
    Menghitung skor tekanan komoditas.
    Cap total: 30 poin.
    """
    if not commodities:
        return 0

    total = 0
    for commodity in commodities:
        change_1d = commodity.get("change_1d_pct")
        if change_1d is not None:
            abs_change = abs(float(change_1d))
            if abs_change >= 3.0:
                total += 10

    # Cap total commodity stress: 30 poin.
    return min(total, 30)


def _calc_geopolitical_stress(news_data):
    """
    Menghitung skor tekanan geopolitik.
    Jumlahkan risk weight event, cap total: 40 poin.
    """
    if not news_data or not news_data.get("events"):
        return 0

    events = news_data.get("events", [])
    total = sum(event.get("risk_weight", 0) for event in events)

    # Cap total geopolitical stress: 40 poin.
    return min(total, 40)


def _calc_uncertainty_penalty(latest_data):
    """
    Menghitung penalti ketidakpastian jika banyak data fallback.
    """
    fallback_count = 0

    # Cek FX
    fx = latest_data.get("market", {}).get("fx", {}).get("usdidr", {})
    if fx.get("source") == "fallback":
        fallback_count += 1

    # Cek komoditas
    commodities = latest_data.get("market", {}).get("commodities", [])
    for commodity in commodities:
        if commodity.get("source") == "fallback":
            fallback_count += 1

    # Berita: jika event kosong dan tidak ada fallback, tidak dihitung sebagai uncertainty.
    # Tetapi jika fetch_news menggunakan fallback, kita tidak bisa deteksi secara langsung
    # karena struktur output tidak menyebutkan source fallback untuk berita.
    # Untuk MVP, gunakan jumlah fallback dari FX dan komoditas sebagai proxy.

    if fallback_count == 0:
        return 0
    elif fallback_count <= 2:
        return 5
    else:
        return 10


def calculate_score(latest_data):
    """
    Menghitung skor risiko berdasarkan data latest.json.
    Mengembalikan dictionary score, level, headline, recommended_action, components.
    """
    thresholds = _get_thresholds()

    fx_data = latest_data.get("market", {}).get("fx", {}).get("usdidr")
    commodities = latest_data.get("market", {}).get("commodities", [])
    news_data = latest_data.get("geopolitics", {})

    currency_stress = _calc_currency_stress(fx_data)
    commodity_stress = _calc_commodity_stress(commodities)
    geopolitical_stress = _calc_geopolitical_stress(news_data)
    uncertainty_penalty = _calc_uncertainty_penalty(latest_data)

    total_score = currency_stress + commodity_stress + geopolitical_stress + uncertainty_penalty
    # Cap total skor maksimal 100.
    total_score = min(total_score, 100)

    # Tentukan level berdasarkan threshold.
    if total_score >= thresholds["risk_score_red"]:
        level = "RED"
    elif total_score >= thresholds["risk_score_yellow"]:
        level = "YELLOW"
    else:
        level = "GREEN"

    # Buat headline dan recommended action berdasarkan level dan komponen dominan.
    headline, recommended_action = _build_narrative(
        level, currency_stress, commodity_stress, geopolitical_stress
    )

    result = {
        "score": total_score,
        "level": level,
        "headline": headline,
        "recommended_action": recommended_action,
        "components": {
            "currency_stress": currency_stress,
            "commodity_stress": commodity_stress,
            "geopolitical_stress": geopolitical_stress,
            "uncertainty_penalty": uncertainty_penalty,
        },
    }

    return result


def _build_narrative(level, currency_stress, commodity_stress, geopolitical_stress):
    """
    Membuat headline dan recommended action berdasarkan level dan komponen dominan.
    """
    if level == "GREEN":
        headline = "Kondisi relatif stabil."
        recommended_action = "Kondisi relatif stabil. Lanjutkan pemantauan rutin."
        return headline, recommended_action

    if level == "RED":
        headline = "Risiko tinggi. Tinjau ulang supplier, stok, kontrak harga, dan eksposur valuta asing."
        recommended_action = (
            "Risiko tinggi. Tinjau ulang supplier, stok, kontrak harga, "
            "dan eksposur valuta asing."
        )

    elif level == "YELLOW":
        headline = "Waspadai tekanan kurs dan biaya input."
        recommended_action = (
            "Waspadai tekanan kurs dan biaya input. "
            "Tahan pembelian besar sampai tren lebih jelas."
        )

    # Sesuaikan narrative jika ada komponen dominan.
    dominant = max(
        [currency_stress, commodity_stress, geopolitical_stress],
        default=0,
    )

    if dominant == currency_stress and currency_stress > 0:
        if "Prioraskan hedging sederhana" not in recommended_action:
            recommended_action += " Prioritaskan hedging sederhana dan pantau kurs."

    if dominant == geopolitical_stress and geopolitical_stress > 0:
        if "Pantau jalur pelayaran" not in recommended_action:
            recommended_action += " Pantau jalur pelayaran dan lead time pengiriman."

    if dominant == commodity_stress and commodity_stress > 0:
        if "Tinjau harga kontrak" not in recommended_action:
            recommended_action += " Tinjau harga kontrak dan stok cadangan."

    return headline, recommended_action