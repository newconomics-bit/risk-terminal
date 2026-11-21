#!/usr/bin/env python3
"""
Probe commodity data sources untuk verifikasi kualitas data.
Menulis hasil ke data/probes/YYYY-MM-DD.json.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import openpyxl

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Konstanta untuk validasi harga
GOLD_MIN, GOLD_MAX = 2000, 3500  # USD/oz
WTI_MIN, WTI_MAX = 50, 120       # USD/bbl
CPO_MIN, CPO_MAX = 500, 1500     # USD/MT


def _probe_alltick(token: str) -> dict:
    """Probe AllTick API untuk emas (XAUUSD) dan WTI (USOil)."""
    result = {"available": False, "gold_usd": {}, "wti_usd": {}, "verdict": "failed"}

    if not token:
        log.warning("ALLTICK_TOKEN kosong, skip AllTick")
        return result

    headers = {"User-Agent": "RiskTerminal-Probe/1.0"}
    base_url = "https://quote.tradeswitcher.com/quote/tick"

    for symbol, name in [("XAUUSD", "gold_usd"), ("USOil", "wti_usd")]:
        try:
            # AllTick query format
            query = {"trace": f"probe_{symbol.lower()}", "symbol": symbol}
            params = {"token": token, "query": json.dumps(query)}

            resp = requests.get(base_url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Parse response - struktur tergantung API AllTick
            price = None
            ts = None

            if isinstance(data, dict):
                # Coba berbagai struktur response
                if "data" in data and isinstance(data["data"], dict):
                    price = data["data"].get("price") or data["data"].get("last")
                    ts = data["data"].get("timestamp") or data["data"].get("time")
                elif "price" in data:
                    price = data["price"]
                    ts = data.get("timestamp") or data.get("time")

            if price is not None:
                price = float(price)
                result[name] = {
                    "price": price,
                    "timestamp": ts,
                    "symbol": symbol,
                }
                log.info(f"AllTick {symbol}: {price} (ts={ts})")
            else:
                log.warning(f"AllTick {symbol}: price tidak ditemukan di response: {data}")

        except Exception as e:
            log.warning(f"AllTick {symbol} gagal: {e}")

    # Tentukan verdict
    gold_ok = "gold_usd" in result and result["gold_usd"] and GOLD_MIN <= result["gold_usd"]["price"] <= GOLD_MAX
    wti_ok = "wti_usd" in result and result["wti_usd"] and WTI_MIN <= result["wti_usd"]["price"] <= WTI_MAX

    if gold_ok and wti_ok:
        result["verdict"] = "looks_real"
        result["available"] = True
    elif ("gold_usd" in result and result["gold_usd"]) or ("wti_usd" in result and result["wti_usd"]):
        result["verdict"] = "looks_simulated"
        result["available"] = True
    else:
        result["verdict"] = "failed"

    return result


def _probe_pink_sheet() -> dict:
    """Download dan parse World Bank Pink Sheet untuk CPO."""
    result = {"available": False, "cpo_month": None, "cpo_usd_per_mt": None, "verdict": "failed"}

    # URL World Bank Commodity Markets - file historis
    # Biasanya: https://www.worldbank.org/en/research/commodity-markets
    # File: CMO-Historical-Data-Monthly.xlsx atau serupa
    urls_to_try = [
        "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx",
        "https://www.worldbank.org/en/research/commodity-markets",  # Halaman utama, perlu scraping
    ]

    for url in urls_to_try:
        try:
            log.info(f"Mencoba download Pink Sheet dari: {url}")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()

            # Cek apakah file Excel
            content_type = resp.headers.get("Content-Type", "")
            if "spreadsheet" not in content_type and "excel" not in content_type and not url.endswith(".xlsx"):
                log.info(f"Bukan file Excel, skip: {content_type}")
                continue

            # Parse Excel di memory
            wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=True, data_only=True)

            # Cari sheet yang berisi CPO (biasanya "Energy" atau "Agriculture")
            cpo_price = None
            cpo_month = None

            for sheet_name in wb.sheetnames:
                if any(kw in sheet_name.lower() for kw in ["energy", "agri", "palm", "cpo", "vegetable"]):
                    ws = wb[sheet_name]
                    # Cari baris header dan data CPO
                    for row in ws.iter_rows(values_only=True):
                        if not row or not row[0]:
                            continue
                        cell_val = str(row[0]).lower()
                        if "crude palm oil" in cell_val or "cpo" == cell_val.strip().lower():
                            # Asumsi kolom terakhir = bulan terbaru
                            for val in reversed(row[1:]):
                                if val is not None:
                                    try:
                                        cpo_price = float(val)
                                        # Coba ambil bulan dari header
                                        break
                                    except (ValueError, TypeError):
                                        continue
                            if cpo_price:
                                break

            if cpo_price and CPO_MIN <= cpo_price <= CPO_MAX:
                result["available"] = True
                result["cpo_usd_per_mt"] = cpo_price
                result["cpo_month"] = cpo_month or datetime.now().strftime("%Y-%m")
                result["verdict"] = "ok"
                log.info(f"Pink Sheet CPO: {cpo_price} USD/MT ({result['cpo_month']})")
                break
            else:
                log.warning(f"CPO price tidak valid atau tidak ditemukan: {cpo_price}")

        except Exception as e:
            log.warning(f"Pink Sheet probe gagal ({url}): {e}")
            continue

    return result


def main():
    probed_at = datetime.now(timezone.utc).isoformat()

    # 1. Probe AllTick
    alltick_token = os.getenv("ALLTICK_TOKEN", "").strip()
    alltick_result = _probe_alltick(alltick_token)

    # 2. Probe Pink Sheet
    pink_result = _probe_pink_sheet()

    # 3. Susun output
    output = {
        "probed_at": probed_at,
        "alltick": alltick_result,
        "pink_sheet": pink_result,
    }

    # 4. Tulis ke file
    out_dir = Path("data/probes")
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    out_file = out_dir / f"{date_str}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info(f"Probe selesai. Hasil: {out_file}")
    log.info(f"AllTick: {alltick_result['verdict']}")
    log.info(f"Pink Sheet: {pink_result['verdict']}")


if __name__ == "__main__":
    import io  # Import di sini untuk openpyxl
    main()