"""
Swiss Minimalist Dashboard for Kleros Autonomous Discovery Agent.
Inspired by Linear and Vercel design systems.
"""

import json
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.agent import KlerosAgent, build_autonomous_query
from src.database import DatabaseManager

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Kleros - Autonomous Discovery Agent",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Swiss Minimalist CSS System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Reset & Base Canvas */
    .stApp {
        background-color: #08090a;
        color: #f3f4f6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Remove default sidebar space if collapsed */
    section[data-testid="stSidebar"] {
        display: none;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Header Bar */
    .brand-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #1f2228;
        margin-bottom: 2rem;
    }
    .brand-title {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #ffffff;
        margin: 0;
    }
    .brand-subtitle {
        color: #8a8f98;
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }

    /* Minimal Metric Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #0d0e12;
        border: 1px solid #1f2228;
        border-radius: 6px;
        padding: 1rem;
        text-align: left;
    }
    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: #6f747c;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f3f4f6;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Streamlit Button Override */
    .stButton > button {
        background-color: #ffffff !important;
        color: #08090a !important;
        border: 1px solid #ffffff !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.15s ease !important;
        height: 42px !important;
    }
    .stButton > button:hover {
        background-color: #e2e8f0 !important;
        border-color: #e2e8f0 !important;
        box-shadow: 0 0 12px rgba(255, 255, 255, 0.15) !important;
    }

    /* Selectbox & Input Clean Override */
    div[data-baseweb="select"] > div {
        background-color: #0d0e12 !important;
        border: 1px solid #1f2228 !important;
        border-radius: 6px !important;
        color: #f3f4f6 !important;
    }
    div[data-baseweb="select"] * {
        color: #f3f4f6 !important;
    }
    div[data-baseweb="select"]:focus-within > div {
        border-color: #4b5563 !important;
        box-shadow: none !important;
    }

    /* Deal Card Grid */
    .deal-card {
        background: #0d0e12;
        border: 1px solid #1f2228;
        border-radius: 6px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: border-color 0.15s ease;
    }
    .deal-card:hover {
        border-color: #374151;
    }
    .tag-mono {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 500;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        text-transform: uppercase;
        margin-right: 0.4rem;
        display: inline-block;
    }
    .tag-api { background: #1e293b; color: #38bdf8; border: 1px solid #334155; }
    .tag-ide { background: #2e1065; color: #c084fc; border: 1px solid #581c87; }
    .tag-chat { background: #064e3b; color: #34d399; border: 1px solid #065f46; }
    .tag-student { background: #451a03; color: #fbbf24; border: 1px solid #78350f; }
    .tag-geo { background: #111827; color: #9ca3af; border: 1px solid #1f2937; }
    .tag-us { background: #451212; color: #f87171; border: 1px solid #7f1d1d; }

    .deal-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f9fafb;
        margin-top: 0.6rem;
        margin-bottom: 0.3rem;
        letter-spacing: -0.01em;
    }
    .deal-value {
        font-family: 'JetBrains Mono', monospace;
        color: #10b981;
        font-size: 0.88rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .deal-desc {
        color: #8a8f98;
        font-size: 0.85rem;
        line-height: 1.45;
        margin-bottom: 1rem;
    }
    .claim-link {
        display: inline-flex;
        align-items: center;
        color: #f3f4f6 !important;
        background: #161922;
        border: 1px solid #272c38;
        padding: 0.4rem 0.85rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
        text-decoration: none !important;
        transition: background 0.15s ease;
    }
    .claim-link:hover {
        background: #212636;
        border-color: #3b4254;
    }

    /* Terminal Feed Box */
    .terminal-box {
        background: #050607;
        border: 1px solid #1f2228;
        border-radius: 6px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: #10b981;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db():
    return DatabaseManager()


db = get_db()

# Top Brand Header
st.markdown("""
<div class="brand-header">
    <div>
        <h1 class="brand-title">KLEROS / Autonomous Discovery Agent</h1>
        <div class="brand-subtitle">Autonomous discovery engine for free LLM API credits, IDE subscriptions, and student AI deals.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Action Toolbar (No query text box needed!)
col_action, col_type_filter, col_reg_filter = st.columns([1.5, 1, 1])

with col_action:
    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #6f747c; text-transform: uppercase; margin-bottom: 0.4rem;'>Discovery Trigger</div>", unsafe_allow_html=True)
    trigger_discovery = st.button("Discover Free Deals", use_container_width=True)

with col_type_filter:
    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #6f747c; text-transform: uppercase; margin-bottom: 0.4rem;'>Filter Category</div>", unsafe_allow_html=True)
    selected_type = st.selectbox(
        "Filter Category",
        ["All", "API", "IDE", "Chat", "Student"],
        label_visibility="collapsed"
    )

with col_reg_filter:
    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #6f747c; text-transform: uppercase; margin-bottom: 0.4rem;'>Filter Region</div>", unsafe_allow_html=True)
    selected_region = st.selectbox(
        "Filter Region",
        ["All", "Global", "US", "Europe", "Asia"],
        label_visibility="collapsed"
    )

st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

# Run Autonomous Discovery Pipeline
if trigger_discovery:
    st.markdown("### Discovery Pipeline Status")
    progress_bar = st.progress(0.0)
    log_area = st.empty()

    def update_progress(step: str, msg: str, pct: float):
        progress_bar.progress(pct)
        log_area.markdown(f"""
        <div class="terminal-box">
            [$] STEP [{step.upper()}] - {msg}
        </div>
        """, unsafe_allow_html=True)

    try:
        agent = KlerosAgent()
        # Autonomous query synthesis based on selected category!
        result = agent.run(
            category=selected_type,
            max_results=10,
            max_pages=5,
            progress_callback=update_progress
        )
        st.success(f"Discovery Complete. Discovered {result['valid_offers_count']} offers ({result['new_offers_count']} new saved).")
    except Exception as e:
        st.error(f"Execution error: {e}")

# Fetch Stats
stats = db.get_stats()

# Swiss Minimalist Metrics Section
st.markdown(f"""
<div class="metrics-grid">
    <div class="metric-card">
        <div class="metric-label">TOTAL DEALS</div>
        <div class="metric-value">{stats.get("total_offers", 0)}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">NEW TODAY</div>
        <div class="metric-value">{stats.get("new_today", 0)}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">API CREDITS</div>
        <div class="metric-value">{stats.get("by_type", {}).get("api", 0)}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">IDE CREDITS</div>
        <div class="metric-value">{stats.get("by_type", {}).get("ide", 0)}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">CHAT PLANS</div>
        <div class="metric-value">{stats.get("by_type", {}).get("chat", 0)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Query Database
offers = db.get_offers(
    offer_type=selected_type if selected_type != "All" else None,
    region=selected_region if selected_region != "All" else None,
    is_valid_only=True
)

col_head, col_exp = st.columns([3, 1])
with col_head:
    st.markdown(f"<h3 style='font-size: 1.1rem; font-weight: 600; color: #ffffff;'>Verified Deals ({len(offers)})</h3>", unsafe_allow_html=True)

with col_exp:
    if offers:
        df = pd.DataFrame(offers)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export CSV",
            data=csv_data,
            file_name="kleros_verified_deals.csv",
            mime="text/csv",
            use_container_width=True
        )

if not offers:
    st.info("No deals recorded for this filter. Click 'Discover Free Deals' above to run autonomous search.")
else:
    col_left, col_right = st.columns(2)
    for idx, offer in enumerate(offers):
        target_col = col_left if idx % 2 == 0 else col_right
        with target_col:
            off_type = offer.get("offer_type", "api").lower()
            badge_cls = f"tag-{off_type}" if off_type in ["api", "ide", "chat", "student"] else "tag-api"

            regions = offer.get("eligible_regions", ["global"])
            is_us = ("us" in regions or "usa" in regions) and len(regions) == 1
            geo_cls = "tag-us" if is_us else "tag-geo"
            geo_lbl = "US-ONLY" if is_us else ", ".join(regions).upper()

            st.markdown(f"""
            <div class="deal-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="tag-mono {badge_cls}">{off_type.upper()}</span>
                        <span class="tag-mono {geo_cls}">{geo_lbl}</span>
                    </div>
                    <span style="color: #6f747c; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;">{offer.get('date_posted') or 'VERIFIED'}</span>
                </div>
                <div class="deal-title">{offer.get('name')}</div>
                <div class="deal-value">{offer.get('value') or 'Free Credit / Discount'}</div>
                <div class="deal-desc">{offer.get('description') or 'No description provided.'}</div>
                <a href="{offer.get('url')}" target="_blank" class="claim-link">
                    Claim Deal &nbsp;&rarr;
                </a>
            </div>
            """, unsafe_allow_html=True)
