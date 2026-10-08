"""
Modul fetcher untuk data komoditas.
Mengambil harga komoditas dari sumber publik.
Jika API gagal, menggunakan data dummy (fallback).
Komoditas: Brent crude oil, Gold, CPO.
"""

import logging
from datetime import datetime, timezone, timedelta

import requests

logger = logging.getLogger(__name__)

# Zona waktu Indonesia (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))


def fetch_brent():
    """
    Mengambil harga Brent Crude Oil.
    Mengembalikan dictionary sesuai struktur PRD FR-03.
    """
    # Sumber publik yang mungkin: tidak ada API gratis yang stabil tanpa key.
    # Untuk MVP, gunakan fallback dummy agar pipeline tetap berjalan.
    # Implementasi nyata bisa ditambahkan nanti jika ada sumber gratis.
    return _fallback_commodity(
        symbol="BRENT",
        name="Brent Crude Oil",
        price=82.4,
        unit="USD/bbl",
    )


def fetch_gold():
    """
    Mengambil harga Gold.
    """
    return _fallback_commodity(
        symbol="GOLD",
        name="Gold",
        price=2650.0,
        unit="USD/oz",
    )


def fetch_cpo():
    """
    Mengambil harga CPO (Crude Palm Oil).
    """
    return _fallback_commodity(
        symbol="CPO",
        name="Crude Palm Oil",
        price=920.0,
        unit="USD/MT",
    )


def fetch_all():
    """
    Mengambil semua komoditas watchlist.
    Mengembalikan list dictionary.
    """
    commodities = [
        fetch_brent(),
        fetch_gold(),
        fetch_cpo(),
    ]
    return commodities


def _fallback_commodity(symbol, name, price, unit):
    """
    Data dummy untuk komoditas jika API gagal.
    """
    as_of = datetime.now(WIB).strftime("%Y-%m-%dT%H:%M:%S+07:00")
    return {
        "symbol": symbol,
        "name": name,
        "price": price,
        "unit": unit,
        "change_1d_pct": None,
        "change_7d_pct": None,
        "as_of": as_of,
        "source": "fallback",
    }