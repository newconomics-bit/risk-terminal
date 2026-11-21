"""
Modul utilitas untuk operasi input/output.
Menangani pembacaan dan penulisan file JSON.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)


def save_json(data, path):
    """
    Menyimpan dictionary ke file JSON.
    Secara otomatis membuat direktori tujuan jika belum ada.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("JSON tersimpan di %s", path)


def load_json(path):
    """
    Memuat file JSON ke dalam dictionary.
    Mengembalikan None jika file tidak ditemukan.
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)