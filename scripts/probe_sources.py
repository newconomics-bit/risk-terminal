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
    """Probe AllTick API untuk emas (XAUUSD) dan WTI (USOIL).
    
    Docs: https://alltick.co/apis/en/api-reference/forex/trade-tick
    Endpoint: https://quote.alltick.co/quote-b-api/trade-tick
    Symbol codes dari code list: XAUUSD (emas/USD), USOIL (WTI crude oil)
    """
    result = {"available": False, "gold_usd": {}, "wti_usd": {}, "verdict": "failed"}

    if not token:
        log.warning("ALLTICK_TOKEN kosong, skip AllTick")
        return result

    headers = {"User-Agent": "RiskTerminal-Probe/1.0"}
    base_url = "https://quote.alltick.co/quote-b-api/trade-tick"

    # Symbol codes per AllTick code list (Google Sheets)
    # Gold: XAUUSD (emas/USD), WTI: USOIL
    symbols = [
        ("XAUUSD", "gold_usd"),
        ("USOIL", "wti_usd"),
    ]

    for symbol, name in symbols:
        try:
            # AllTick query format per docs
            query_data = {
                "trace": f"probe_{symbol.lower()}",
                "data": {"symbol_list": [{"code": symbol}]}
            }
            params = {"token": token, "query": json.dumps(query_data)}

            resp = requests.get(base_url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Parse response per AllTick schema
            price = None
            ts = None

            if isinstance(data, dict) and data.get("ret") == 200:
                tick_list = data.get("data", {}).get("tick_list", [])
                if tick_list:
                    tick = tick_list[0]
                    price = tick.get("price")
                    ts = tick.get("tick_time")

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
    """Download dan parse World Bank Pink Sheet untuk CPO (Palm Oil).
    
    File: CMO-Historical-Data-Monthly.xlsx dari thedocs.worldbank.org
    Sheet target: "AFOSHEET" (agriculture), "Monthly Prices", "Monthly Indices"
    Cari baris label mengandung "palm oil" (case-insensitive) di kolom 1
    """
    result = {
        "available": False,
        "cpo_month": None,
        "cpo_usd_per_mt": None,
        "verdict": "failed",
        "debug": {
            "sheet_names": [],
            "searched_sheets": [],
            "commodity_labels_found": {},
            "palm_oil_matches": [],
            "sample_rows_around_match": [],
        }
    }

    # URL World Bank Commodity Markets - file historis
    url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"

    try:
        log.info(f"Mencoba download Pink Sheet dari: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        # Cek apakah file Excel
        content_type = resp.headers.get("Content-Type", "")
        if "spreadsheet" not in content_type and "excel" not in content_type and not url.endswith(".xlsx"):
            log.info(f"Bukan file Excel, skip: {content_type}")
            result["debug"]["error"] = f"Bukan file Excel: {content_type}"
            return result

        # Parse Excel di memory
        wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=True, data_only=True)

        # Debug: catat semua nama sheet
        result["debug"]["sheet_names"] = wb.sheetnames
        log.info(f"Sheet names: {wb.sheetnames}")

        # Coba semua sheet yang relevan untuk mencari palm oil
        # Prioritas: AFOSHEET (agriculture), Monthly Prices, Monthly Indices
        target_sheets = []
        for sheet_name in wb.sheetnames:
            lower = sheet_name.strip().lower()
            if lower in ("afosheet", "monthly prices", "monthly indices"):
                target_sheets.append(sheet_name)
        if not target_sheets:
            target_sheets = wb.sheetnames
        
        result["debug"]["searched_sheets"] = target_sheets
        log.info(f"Sheets to search: {target_sheets}")

        cpo_price = None
        cpo_month = None
        found_sheet = None
        
        for target_sheet in target_sheets:
            log.info(f"Mencari di sheet: {target_sheet}")
            ws = wb[target_sheet]
            
            # Baca semua baris
            all_rows = []
            for row in ws.iter_rows(values_only=True):
                all_rows.append(list(row) if row else [])
            
            # Debug: log first 10 rows of this sheet
            log.info(f"  First 10 rows of {target_sheet}:")
            for i, row in enumerate(all_rows[:10]):
                if row:
                    cols = [str(c)[:50] if c else "None" for c in row[:5]]
                    log.info(f"    Row {i}: {cols}")
            
            # Cari label komoditas di kolom 1 (kolom 0 kosong untuk label)
            commodity_labels = []
            for idx, row in enumerate(all_rows):
                if len(row) > 1 and row[1] and not row[0]:
                    val = str(row[1]).strip()
                    # Skip unit rows like "($/bbl)"
                    if not val.startswith("(") and not val.replace(".", "").replace("-", "").isdigit():
                        commodity_labels.append({"row": idx, "label": val})
            
            result["debug"]["commodity_labels_found"][target_sheet] = commodity_labels
            log.info(f"  Found {len(commodity_labels)} commodity labels in {target_sheet}")
            for cl in commodity_labels:
                log.info(f"    Row {cl['row']}: {cl['label']}")
            
            # Cari palm oil di kolom 1
            for idx, row in enumerate(all_rows):
                if len(row) > 1 and row[1]:
                    cell_val = str(row[1]).strip().lower()
                    if "palm oil" in cell_val:
                        log.info(f"  Found 'palm oil' at row {idx}: {row[1]}")
                        match_info = {
                            "sheet": target_sheet,
                            "row": idx,
                            "label": str(row[1]),
                            "column": 1,
                        }
                        result["debug"]["palm_oil_matches"].append(match_info)
                        
                        # Ekstrak harga dari baris data berikutnya
                        # Data rows: date in col 0 (format YYYYM##), price in col 1
                        for data_idx in range(idx + 1, len(all_rows)):
                            data_row = all_rows[data_idx]
                            if not data_row or not data_row[0]:
                                continue
                            date_str = str(data_row[0]).strip()
                            # Check if date format matches YYYYM## (e.g., 2024M01)
                            if len(date_str) >= 6 and date_str[4] == 'M' and date_str[:4].isdigit() and date_str[5:].isdigit():
                                # This is a data row, get the last non-null price in the row
                                for val in reversed(data_row[1:]):
                                    if val is not None:
                                        try:
                                            cpo_price = float(val)
                                            cpo_month = date_str
                                            break
                                        except (ValueError, TypeError):
                                            continue
                                if cpo_price:
                                    break
                        if cpo_price:
                            found_sheet = target_sheet
                            break
            
            if cpo_price:
                break

        # Debug: ambil sample rows di sekitar match pertama
        if result["debug"]["palm_oil_matches"]:
            first_match = result["debug"]["palm_oil_matches"][0]
            match_sheet = first_match["sheet"]
            match_row = first_match["row"]
            ws = wb[match_sheet]
            all_rows = []
            for row in ws.iter_rows(values_only=True):
                all_rows.append(list(row) if row else [])
            
            start = max(0, match_row - 2)
            end = min(len(all_rows), match_row + 3)
            for i in range(start, end):
                row = all_rows[i]
                if row:
                    result["debug"]["sample_rows_around_match"].append({
                        "row_index": i,
                        "col0": str(row[0]) if row[0] else None,
                        "col1": str(row[1]) if len(row) > 1 and row[1] else None,
                    })

        if cpo_price and CPO_MIN <= cpo_price <= CPO_MAX:
            result["available"] = True
            result["cpo_usd_per_mt"] = cpo_price
            result["cpo_month"] = cpo_month
            result["verdict"] = "ok"
            log.info(f"Pink Sheet CPO (Palm Oil) dari sheet '{found_sheet}': {cpo_price} USD/MT ({cpo_month})")
        else:
            log.warning(f"CPO price tidak valid atau tidak ditemukan: {cpo_price}")
            if not result["debug"].get("error"):
                result["debug"]["error"] = f"Price invalid or not found: {cpo_price}"

    except Exception as e:
        log.warning(f"Pink Sheet probe gagal: {e}")
        result["debug"]["error"] = str(e)

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