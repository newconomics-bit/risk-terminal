#!/usr/bin/env python3
"""
Dashboard Streamlit untuk Risk Terminal.
Mobile-first, dark theme, menampilkan data dari data/latest.json.
"""

import json
import os
import logging

import streamlit as st

# Konfigurasi halaman harus menjadi perintah Streamlit pertama
st.set_page_config(
    page_title="Risk Terminal",
    page_icon="🌍",
    layout="centered",  # centered lebih cocok untuk mobile
)

# Konfigurasi logging
logger = logging.getLogger(__name__)

# Path data
LATEST_JSON_PATH = "data/latest.json"

# Warna status
STATUS_COLORS = {
    "GREEN": "#22c55e",   # hijau
    "YELLOW": "#f59e0b",  # kuning/amber
    "RED": "#ef4444",     # merah
}

# CSS untuk tampilan mobile-first dan dark theme
CUSTOM_CSS = """
<style>
/* Dark theme dasar */
.stApp {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Judul dan header */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}

/* Kartu status */
.status-card {
    background-color: #1e293b;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

/* Metric styling */
div[data-testid="stMetric"] {
    background-color: #1e293b;
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Badge fallback */
.badge-fallback {
    display: inline-block;
    background-color: #f59e0b;
    color: #0f172a;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 9999px;
    margin-left: 6px;
}

/* Disclaimer */
.disclaimer {
    font-size: 0.85rem;
    color: #94a3b8;
    text-align: center;
    margin-top: 24px;
    padding: 12px;
    background-color: #1e293b;
    border-radius: 8px;
}

/* Expandable sections */
.streamlit-expanderHeader {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
</style>
"""


@st.cache_data
def load_latest_data():
    """
    Memuat data dari data/latest.json.
    Mengembalikan None jika file tidak ada atau gagal di-parse.
    """
    if not os.path.exists(LATEST_JSON_PATH):
        return None
    try:
        with open(LATEST_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Gagal memuat %s: %s", LATEST_JSON_PATH, e)
        return None


def render_header(data):
    """
    Section 1: Header status.
    Menampilkan nama produk, waktu generate, level status, dan skor.
    """
    meta = data.get("meta", {})
    status = data.get("status", {})

    generated_at = meta.get("generated_at", "N/A")
    level = status.get("level", "UNKNOWN")
    score = status.get("score", "N/A")

    level_color = STATUS_COLORS.get(level, "#94a3b8")

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Header card
    st.markdown(f"""
    <div class="status-card" style="border-left: 5px solid {level_color};">
        <h1 style="margin: 0; font-size: 1.5rem;">RISK TERMINAL</h1>
        <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 0.9rem;">
            {generated_at} WIB
        </p>
        <div style="margin-top: 12px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            <span style="
                background-color: {level_color};
                color: #0f172a;
                font-weight: 700;
                padding: 6px 14px;
                border-radius: 9999px;
                font-size: 0.9rem;
                text-transform: uppercase;
            ">STATUS: {level}</span>
            <span style="
                background-color: #334155;
                color: #f1f5f9;
                font-weight: 600;
                padding: 6px 14px;
                border-radius: 9999px;
                font-size: 0.9rem;
            ">SCORE: {score}/100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_todays_brief(data):
    """
    Section 2: Today's Brief.
    Menampilkan headline, recommended action, dan ringkasan dampak.
    """
    status = data.get("status", {})
    impact = data.get("impact", {})

    headline = status.get("headline", "")
    recommended_action = status.get("recommended_action", "")

    # Ringkasan dampak
    import_cost = impact.get("import_cost_pressure", "LOW")
    input_price = impact.get("input_price_risk", "LOW")
    supply_chain = impact.get("supply_chain_risk", "LOW")

    impact_colors = {
        "LOW": "#22c55e",
        "MEDIUM": "#f59e0b",
        "HIGH": "#ef4444",
    }

    st.markdown("### 📋 Today's Brief")
    st.markdown(f"""
    <div class="status-card">
        <p style="font-size: 1.05rem; font-weight: 500; margin: 0 0 10px 0;">{headline}</p>
        <p style="color: #cbd5e1; margin: 0 0 14px 0;">{recommended_action}</p>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span style="background-color: {impact_colors.get(import_cost, '#334155')}; color: #0f172a; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">
                Import cost: {import_cost}
            </span>
            <span style="background-color: {impact_colors.get(input_price, '#334155')}; color: #0f172a; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">
                Input price: {input_price}
            </span>
            <span style="background-color: {impact_colors.get(supply_chain, '#334155')}; color: #0f172a; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">
                Supply chain: {supply_chain}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_market_pulse(data):
    """
    Section 3: Market Pulse.
    Menampilkan metrik USD/IDR dan komoditas menggunakan st.metric.
    """
    st.markdown("### 📈 Market Pulse")

    market = data.get("market", {})

    # USD/IDR
    fx = market.get("fx", {}).get("usdidr", {})
    if fx:
        rate = fx.get("rate")
        change_1d = fx.get("change_1d_pct")
        change_7d = fx.get("change_7d_pct")
        source = fx.get("source", "unknown")

        # Format perubahan 1 hari
        delta_1d = None
        if change_1d is not None:
            delta_1d = f"{change_1d:+.2f}%" if isinstance(change_1d, (int, float)) else str(change_1d)

        # Badge fallback
        fallback_badge = '<span class="badge-fallback">FALLBACK</span>' if source == "fallback" else ""

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label=f"USD/IDR {fallback_badge}",
                value=f"{rate:,.2f}" if rate is not None else "N/A",
                delta=delta_1d,
            )
        with col2:
            st.caption(f"Sumber: {source}")

    # Komoditas
    commodities = market.get("commodities", [])
    if commodities:
        st.markdown("**Komoditas:**")
        for commodity in commodities:
            symbol = commodity.get("symbol", "")
            name = commodity.get("name", "")
            price = commodity.get("price")
            change_1d = commodity.get("change_1d_pct")
            unit = commodity.get("unit", "")
            source = commodity.get("source", "unknown")

            delta_1d = None
            if change_1d is not None:
                delta_1d = f"{change_1d:+.2f}%" if isinstance(change_1d, (int, float)) else str(change_1d)

            fallback_badge = '<span class="badge-fallback">FALLBACK</span>' if source == "fallback" else ""

            st.markdown(f"**{name} ({symbol}) {fallback_badge}**")
            st.metric(
                label=f"{unit}",
                value=f"{price:,.2f}" if price is not None else "N/A",
                delta=delta_1d,
            )
            st.caption(f"Sumber: {source}")


def render_geopolitical_signals(data):
    """
    Section 4: Geopolitical Signals.
    Menampilkan daftar berita/event menggunakan expander.
    """
    st.markdown("### 🌐 Geopolitical Signals")

    geopolitics = data.get("geopolitics", {})
    events = geopolitics.get("events", [])

    if not events:
        st.info("Tidak ada sinyal geopolitik yang terdeteksi pada cycle ini.")
        return

    for event in events:
        title = event.get("title", "Tanpa judul")
        source = event.get("source", "unknown")
        published_at = event.get("published_at", "N/A")
        risk_weight = event.get("risk_weight", 0)
        tags = event.get("tags", [])

        with st.expander(f"🔴 {title}"):
            st.write(f"**Sumber:** {source}")
            st.write(f"**Waktu:** {published_at}")
            st.write(f"**Risk Weight:** {risk_weight}")
            if tags:
                st.write(f"**Tags:** {', '.join(tags)}")
            link = event.get("link", "")
            if link:
                st.markdown(f"[Baca selengkapnya]({link})")


def render_risk_components(data):
    """
    Section 5: Risk Components.
    Menampilkan breakdown skor komponen.
    """
    st.markdown("### 🧮 Risk Components")

    status = data.get("status", {})
    components = status.get("components", {})

    currency = components.get("currency_stress", 0)
    commodity = components.get("commodity_stress", 0)
    geopolitical = components.get("geopolitical_stress", 0)
    uncertainty = components.get("uncertainty_penalty", 0)
    total = status.get("score", 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Currency", f"{currency}")
    with col2:
        st.metric("Commodity", f"{commodity}")
    with col3:
        st.metric("Geopolitical", f"{geopolitical}")
    with col4:
        st.metric("Uncertainty", f"{uncertainty}")

    st.caption(f"Total Score: {total}/100")


def render_disclaimer():
    """
    Section 6: Footer / Disclaimer.
    """
    st.markdown("""
    <div class="disclaimer">
        Proyek ini untuk edukasi dan analisis pribadi. Bukan rekomendasi keuangan atau investasi.
    </div>
    """, unsafe_allow_html=True)


def main():
    """
    Fungsi utama dashboard.
    """
    data = load_latest_data()

    if data is None:
        st.set_page_config(page_title="Risk Terminal", page_icon="🌍", layout="centered")
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        st.markdown("""
        <div class="status-card" style="text-align: center; padding: 40px 20px;">
            <h2 style="margin-bottom: 12px;">Data belum tersedia</h2>
            <p style="color: #cbd5e1;">
                Jalankan pipeline terlebih dahulu atau tunggu GitHub Actions selesai berjalan.
            </p>
            <p style="color: #94a3b8; font-size: 0.9rem;">
                Perintah: <code>python scripts/run_pipeline.py</code>
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    render_header(data)
    render_todays_brief(data)
    render_market_pulse(data)
    render_geopolitical_signals(data)
    render_risk_components(data)
    render_disclaimer()


if __name__ == "__main__":
    main()