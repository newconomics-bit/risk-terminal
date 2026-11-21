"""
Modul fetcher untuk data USD/IDR.
Mengambil kurs dari API publik open.er-api.com.
Jika API gagal, menggunakan data dummy (fallback).
"""

import logging
from datetime import datetime, timezone, timedelta

import requests

logger = logging.getLogger(__name__)

# Zona waktu Indonesia (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))


def fetch_usdidr():
    """
    Mengambil kurs USD/IDR dari API publik open.er-api.com.
    Mengembalikan dictionary sesuai struktur PRD FR-02.
    Jika API gagal, mengembalikan data dummy dengan source 'fallback'.
    """
    url = "https://open.er-api.com/v6/latest/USD"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Validasi struktur respons API
        if data.get("result") != "success" or "rates" not in data:
            raise ValueError("Respons API tidak sesuai ekspektasi")

        rate = data["rates"].get("IDR")
        if rate is None:
            raise ValueError("Kurs IDR tidak ditemukan dalam respons API")

        as_of = datetime.now(WIB).strftime("%Y-%m-%dT%H:%M:%S+07:00")

        return {
            "symbol": "USDIDR",
            "rate": rate,
            "change_1d_pct": None,
            "change_7d_pct": None,
            "as_of": as_of,
            "source": "open.er-api.com",
        }

    except Exception as e:
        # Fallback: gunakan data dummy agar pipeline tetap berjalan
        logger.warning(
            "Gagal fetch USD/IDR dari API (%s). Menggunakan fallback dummy.", e
        )
        return _fallback_usdidr()


def _fallback_usdidr():
    """
    Data dummy untuk USD/IDR jika API gagal.
    """
    as_of = datetime.now(WIB).strftime("%Y-%m-%dT%H:%M:%S+07:00")
    return {
        "symbol": "USDIDR",
        "rate": 16250.0,
        "change_1d_pct": None,
        "change_7d_pct": None,
        "as_of": as_of,
        "source": "fallback",
    }