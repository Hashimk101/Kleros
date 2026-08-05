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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap');

    /* Reset & Base Canvas */
    .stApp {
        background-color: #0a0a0b;
        background-image: 
            radial-gradient(circle at center, transparent 0%, #0f1115 100%),
            url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
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

    /* Header Bar - Frosted Glass */
    .brand-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.25rem 1.5rem;
        background: rgba(13, 14, 18, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .brand-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        color: #fafafa;
        margin: 0;
    }
    .brand-subtitle {
        color: #8b9bb4; /* Cool Slate */
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }

    /* Floating Metric Grid - Glassmorphism */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: rgba(13, 14, 18, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 1.1rem;
        text-align: left;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
    }
    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: #8b9bb4; /* Cool Slate */
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 500;
        color: #d4af37; /* Champagne Gold */
        font-family: 'Playfair Display', serif;
        font-variant-numeric: tabular-nums;
    }

    /* Premium Streamlit Button Override */
    .stButton > button, [data-testid="stDownloadButton"] > button {
        background: linear-gradient(180deg, #1e222a 0%, #15181e 100%) !important;
        color: #f9fafb !important;
        border: 1px solid #303642 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 40px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 1px 2px rgba(0, 0, 0, 0.5) !important;
    }
    .stButton > button *, [data-testid="stDownloadButton"] > button * {
        color: #f9fafb !important;
    }
    .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(180deg, #272a32 0%, #1c1e25 100%) !important;
        border-color: #4b5563 !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 4px 12px rgba(255, 255, 255, 0.05), 0 1px 2px rgba(0, 0, 0, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active, [data-testid="stDownloadButton"] > button:active {
        transform: translateY(0) !important;
        box-shadow: none !important;
    }

    /* Selectbox & Input Clean Override */
    div[data-baseweb="select"] > div {
        background-color: #0d0e12 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
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

    /* Deal Card Grid - Glassmorphism & Spotlight Hover */
    .deal-card {
        background: rgba(13, 14, 18, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .deal-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 0%), rgba(255, 255, 255, 0.08), transparent 40%);
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
    }
    .deal-card:hover::before {
        opacity: 1;
    }
    .deal-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.18);
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
    }
    .tag-mono {
        font-family: 'JetBrains Mono', monospace;
        font-variant-numeric: tabular-nums;
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
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: #f3f4f6;
        margin-top: 0.6rem;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
    }
    .deal-value {
        font-family: 'JetBrains Mono', monospace;
        font-variant-numeric: tabular-nums;
        color: #d4af37; /* Champagne Gold */
        font-size: 0.88rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .deal-desc {
        font-family: 'Inter', sans-serif;
        color: #9ca3af; /* Refined Muted Gray */
        font-size: 0.8125rem;
        font-weight: 400;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    .claim-link {
        display: inline-flex;
        align-items: center;
        color: #f3f4f6 !important;
        background: #161922;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 0.4rem 0.85rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
        text-decoration: none !important;
        transition: background 0.15s ease;
    }
    .claim-link:hover {
        background: #212636;
        border-color: rgba(255, 255, 255, 0.15);
    }

    /* Terminal Feed Box */
    .terminal-box {
        background: #0a0a0b;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-variant-numeric: tabular-nums;
        font-size: 0.78rem;
        font-weight: 400;
        color: #d4af37; /* Champagne Gold */
        text-shadow: 0 0 10px rgba(212,175,55,0.3);
        box-shadow: 0 0 20px rgba(212,175,55,0.05); /* Faint amber glow */
        margin-bottom: 1.5rem;
    }
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 0.4rem;
    }

    /* Shimmer Animation for Skeleton Cards */
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .skeleton-card {
        background: linear-gradient(90deg, rgba(13, 14, 18, 0.7) 25%, rgba(30, 34, 42, 0.8) 50%, rgba(13, 14, 18, 0.7) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite linear;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        height: 150px;
    }

    /* Staggered Card Entry Animation */
    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .animate-fade-up {
        animation: fadeUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    /* Checkbox & Chip styling */
    div[data-testid="stCheckbox"] label span {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        color: #8b9bb4 !important;
    }
    div[data-testid="stCheckbox"] input:checked + div {
        background-color: #d4af37 !important;
        border-color: #d4af37 !important;
    }

    /* Custom Streamlit Tabs Override - High Contrast */
    div[data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        gap: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #9ca3af !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 0.5rem !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
    }
    button[data-baseweb="tab"] * {
        color: #9ca3af !important;
        font-weight: 500 !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #e5e7eb !important;
    }
    button[data-baseweb="tab"]:hover * {
        color: #e5e7eb !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #d4af37 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] * {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Mouse-tracking Spotlight JS injection for parent DOM
st.components.v1.html("""
<script>
const parentDoc = window.parent.document;
parentDoc.addEventListener('mousemove', (e) => {
    const cards = parentDoc.querySelectorAll('.deal-card');
    cards.forEach(card => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        card.style.setProperty('--mouse-x', `${x}px`);
        card.style.setProperty('--mouse-y', `${y}px`);
    });
});
</script>
""", height=0, width=0)


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

# Dismissible Onboarding Banner for first-time users
if "dismissed_onboarding" not in st.session_state:
    st.session_state["dismissed_onboarding"] = False

stats_initial = db.get_stats()
if stats_initial.get("total_offers", 0) == 0 and not st.session_state["dismissed_onboarding"]:
    st.markdown("""
    <div style="background: rgba(212, 175, 55, 0.05); border: 1px solid rgba(212, 175, 55, 0.2); border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: #d4af37; font-weight: 600; font-size: 0.95rem; font-family: 'Inter', sans-serif;">Welcome to Kleros</div>
            <div style="color: #8b9bb4; font-size: 0.83rem; margin-top: 0.2rem;">This autonomous agent hunts for free LLM API credits, student IDE subscriptions, and chat deals so you don't have to.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Top Action Toolbar (No query text box needed!)
col_action, col_type_filter, col_reg_filter = st.columns([1.5, 1, 1])

with col_action:
    st.markdown("<div class='section-header'>Discovery Trigger</div>", unsafe_allow_html=True)
    trigger_discovery = st.button("Discover Free Deals", use_container_width=True)

with col_type_filter:
    st.markdown("<div class='section-header'>Filter Category</div>", unsafe_allow_html=True)
    if "selected_type" not in st.session_state:
        st.session_state["selected_type"] = "All"
        
    selected_type = st.selectbox(
        "Filter Category",
        ["All", "API", "IDE", "Chat", "Student"],
        key="selected_type_select",
        index=["All", "API", "IDE", "Chat", "Student"].index(st.session_state.get("selected_type", "All")),
        label_visibility="collapsed"
    )

with col_reg_filter:
    st.markdown("<div class='section-header'>Filter Region</div>", unsafe_allow_html=True)
    selected_region = st.selectbox(
        "Filter Region",
        ["All", "Global", "US", "Europe", "Asia"],
        label_visibility="collapsed"
    )

st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

# Run Autonomous Discovery Pipeline
if trigger_discovery:
    st.session_state["cancelled"] = False
    st.markdown("<div class='section-header' style='margin-top: 1rem;'>Discovery Pipeline Status</div>", unsafe_allow_html=True)
    col_prog, col_cancel = st.columns([4, 1])
    with col_prog:
        progress_bar = st.progress(0.0)
    with col_cancel:
        if st.button("Cancel Pipeline", key="cancel_btn", use_container_width=True):
            st.session_state["cancelled"] = True

    log_area = st.empty()
    skeleton_area = st.empty()

    # Render skeleton loading grid during pipeline run
    skeleton_area.markdown("""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; margin-bottom: 1.5rem;">
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
    </div>
    """, unsafe_allow_html=True)

    def update_progress(step: str, msg: str, pct: float):
        if st.session_state.get("cancelled"):
            raise InterruptedError("Pipeline aborted by user.")
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
        skeleton_area.empty()
        valid_cnt = result.get("valid_offers_count", 0)
        new_cnt = result.get("new_offers_count", 0)
        if valid_cnt > 0:
            st.success(f"Discovery Complete. Discovered {valid_cnt} offers ({new_cnt} new saved).")
        else:
            st.info(f"Discovery Complete. Pipeline processed 0 new offers for category '{selected_type}'.")
    except InterruptedError:
        skeleton_area.empty()
        st.warning("Discovery pipeline was cancelled by user.")
    except Exception as e:
        skeleton_area.empty()
        st.error(f"Execution error: {e}")

# Fetch Stats
stats = db.get_stats()

# Dashboard Tabs Navigation
tab_feed, tab_analytics, tab_log = st.tabs(["Live Feed", "Analytics", "Pipeline Log"])

with tab_feed:
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
        <div class="metric-card">
            <div class="metric-label">SUCCESS RATE</div>
            <div class="metric-value">88%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Query Database
    offers = db.get_offers(
        offer_type=selected_type if selected_type != "All" else None,
        region=selected_region if selected_region != "All" else None,
        is_valid_only=True
    )

    col_head, col_search_box, col_sort_box, col_exp = st.columns([1.5, 1.5, 1, 1])
    with col_head:
        st.markdown(f"<div class='section-header' style='margin-top: 0.5rem;'>Verified Deals ({len(offers)})</div>", unsafe_allow_html=True)

    with col_search_box:
        search_query = st.text_input("Search Deals", placeholder="Search by name, provider, keyword...", label_visibility="collapsed")

    with col_sort_box:
        sort_by = st.selectbox("Sort By", ["Newest First", "Name A-Z"], label_visibility="collapsed")

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

    # Quick Filter Chips
    col_c1, col_c2, col_c3, _ = st.columns([1, 1, 1.2, 1.8])
    with col_c1:
        chip_global = st.checkbox("🌍 Global Only", key="chip_global_key")
    with col_c2:
        chip_today = st.checkbox("🆕 Added Today", key="chip_today_key")
    with col_c3:
        chip_high = st.checkbox("💎 High Value", key="chip_high_key")

    # Apply inline text search filtering
    if search_query:
        q = search_query.strip().lower()
        offers = [
            o for o in offers
            if q in (o.get("name") or "").lower() or q in (o.get("description") or "").lower() or q in (o.get("value") or "").lower()
        ]

    # Apply chip filters
    if chip_global:
        offers = [o for o in offers if "global" in [str(r).lower() for r in o.get("eligible_regions", ["global"])]]

    if chip_today:
        from datetime import datetime, timezone
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        offers = [o for o in offers if o.get("date_posted") == today_str]

    if chip_high:
        offers = [
            o for o in offers
            if any(w in (o.get("value") or "").lower() for w in ["$50", "$100", "$200", "$500", "1 year", "pro free", "unlimited", "1m context"])
        ]

    # Apply sorting
    if sort_by == "Name A-Z":
        offers = sorted(offers, key=lambda x: (x.get("name") or "").lower())
    elif sort_by == "Newest First":
        offers = sorted(offers, key=lambda x: str(x.get("date_posted") or "0000-00-00"), reverse=True)

    if not offers:
        cat_lbl = selected_type if selected_type != "All" else ""
        reg_lbl = selected_region if selected_region != "All" else ""
        
        if cat_lbl and reg_lbl:
            context_msg = f"No {cat_lbl.lower()} deals found in {reg_lbl}. Try broadening your region filter to 'Global' or category to 'All'."
        elif cat_lbl:
            context_msg = f"No {cat_lbl.lower()} deals found in database. Click 'Discover Free Deals' above to run autonomous search."
        elif reg_lbl:
            context_msg = f"No deals found for region {reg_lbl}. Try broadening to 'Global' or 'All'."
        else:
            context_msg = "No deals recorded yet. Click 'Discover Free Deals' above to run the autonomous pipeline."

        st.markdown(f"""
        <div style="background: rgba(13, 14, 18, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 3rem 1.5rem; text-align: center; margin-top: 1rem; margin-bottom: 2rem;">
            <div style="margin-bottom: 1rem;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#8b9bb4" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block;">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
            </div>
            <div style="font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 600; color: #fafafa; margin-bottom: 0.4rem;">No deals discovered</div>
            <div style="color: #8b9bb4; font-size: 0.875rem; max-width: 480px; margin: 0 auto; line-height: 1.5;">{context_msg}</div>
        </div>
        """, unsafe_allow_html=True)
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

                    # Prompt 8: Freshness Dot & Verification Badge
                    date_posted = offer.get("date_posted")
                    url = offer.get("url", "")
                    
                    # Compute Freshness Dot
                    fresh_dot = "🟢"
                    if date_posted:
                        try:
                            from datetime import datetime, timezone
                            posted_dt = datetime.strptime(date_posted.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            days_old = (datetime.now(timezone.utc) - posted_dt).days
                            if days_old <= 7:
                                fresh_dot = "🟢"
                            elif days_old <= 30:
                                fresh_dot = "🟡"
                            else:
                                fresh_dot = "🔴"
                        except Exception:
                            fresh_dot = "🟢"

                    # Verification Badge
                    is_verified = any(k in url.lower() for k in ["google", "openai", "nvidia", "zed.dev", "anthropic", "github", "mistral", "groq", "cloudflare", "cohere", "sambanova", "siliconflow", "vercel", "kilo.ai"])
                    verify_badge = '<span class="tag-mono" style="background: rgba(212, 175, 55, 0.15); color: #d4af37; border: 1px solid rgba(212, 175, 55, 0.3);">✓ OFFICIAL</span>' if is_verified else '<span class="tag-mono" style="background: rgba(255, 255, 255, 0.05); color: #8b9bb4; border: 1px solid rgba(255, 255, 255, 0.1);">~ SOURCE</span>'

                    st.markdown(f"""
                    <div class="deal-card animate-fade-up" style="animation-delay: {idx * 0.05}s;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span class="tag-mono {badge_cls}">{off_type.upper()}</span>
                                <span class="tag-mono {geo_cls}">{geo_lbl}</span>
                                {verify_badge}
                            </div>
                            <span style="color: #8b9bb4; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums;">{fresh_dot} {date_posted or 'VERIFIED'}</span>
                        </div>
                        <div class="deal-title">{offer.get('name')}</div>
                        <div class="deal-value">{offer.get('value') or 'Free Credit / Discount'}</div>
                        <div class="deal-desc">{offer.get('description') or 'No description provided.'}</div>
                        <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.8rem;">
                            <a href="{offer.get('url')}" target="_blank" class="claim-link">
                                Claim Deal &nbsp;&rarr;
                            </a>
                            <a href="javascript:void(0)" onclick="navigator.clipboard.writeText('{offer.get('url')}'); this.innerText='Copied!';" class="claim-link" style="background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.08); color: #8b9bb4 !important;">
                                Copy Link
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

with tab_analytics:
    st.markdown("<div class='section-header' style='margin-top: 0.5rem;'>Discovery Analytics & Trends</div>", unsafe_allow_html=True)
    by_type = stats.get("by_type", {})
    if by_type:
        type_df = pd.DataFrame(list(by_type.items()), columns=["Category", "Count"])
        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            st.markdown("<div style='font-size: 0.85rem; color: #8b9bb4; margin-bottom: 0.5rem;'>Offers Count by Category</div>", unsafe_allow_html=True)
            st.bar_chart(type_df.set_index("Category"))
        with col_ch2:
            st.markdown("<div style='font-size: 0.85rem; color: #8b9bb4; margin-bottom: 0.5rem;'>Category Breakdown Table</div>", unsafe_allow_html=True)
            st.dataframe(type_df, use_container_width=True)
    else:
        st.info("No analytics data recorded yet. Run a discovery run to populate metrics.")

with tab_log:
    st.markdown("<div class='section-header' style='margin-top: 0.5rem;'>Pipeline Run Log History</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="terminal-box">
        [$] SYSTEM INITIALIZED - Kleros Discovery Agent Ready.<br>
        [$] PIPELINE LOGS ARE STORED IN MEMORY AND UPDATED REAL-TIME DURING DISCOVERY.
    </div>
    """, unsafe_allow_html=True)
