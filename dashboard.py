"""
Streamlit Dashboard for Kleros Autonomous Discovery Agent.
"""

import json
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.agent import DEFAULT_QUERY, KlerosAgent
from src.database import DatabaseManager

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Kleros - Free AI Resource Discovery Agent",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Dark glassmorphism theme */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    .hero-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .offer-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .offer-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 0.5rem;
    }
    
    .badge-api { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; }
    .badge-ide { background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: white; }
    .badge-chat { background: linear-gradient(135deg, #10b981, #047857); color: white; }
    .badge-student { background: linear-gradient(135deg, #f59e0b, #b45309); color: white; }
    .badge-geo { background: rgba(255, 255, 255, 0.1); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.2); }
    .badge-us { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }

    .claim-btn {
        display: inline-block;
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white !important;
        padding: 0.4rem 1rem;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.85rem;
        margin-top: 0.75rem;
    }
    .claim-btn:hover {
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db():
    return DatabaseManager()


db = get_db()

# Title Header
st.markdown("""
<div class="hero-card">
    <h1 style="margin: 0; font-size: 2.2rem; background: linear-gradient(90deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🏛️ KLEROS: Autonomous Discovery Agent
    </h1>
    <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem; margin-bottom: 0;">
        Finds, extracts, and validates free LLM API credits, IDE subscriptions, and student deals.
    </p>
</div>
""", unsafe_allow_html=True)

# Search Control Bar
col_q, col_btn = st.columns([4, 1])
with col_q:
    search_query = st.text_input(
        "Search Query",
        value=DEFAULT_QUERY,
        placeholder="Enter topic to discover free AI credits..."
    )

with col_btn:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    run_agent = st.button("🚀 Run Agent", use_container_width=True, type="primary")

# Sidebar Controls
st.sidebar.title("🎛️ Agent Controls & Filters")

max_pages = st.sidebar.slider("Max Web Pages to Process", min_value=1, max_value=10, value=5)
max_results = st.sidebar.slider("Max Search Results", min_value=5, max_value=25, value=10)

st.sidebar.markdown("---")
st.sidebar.subheader("Filter Offers")

selected_type = st.sidebar.selectbox(
    "Offer Type",
    ["All", "API", "IDE", "Chat", "Student"]
)

selected_region = st.sidebar.selectbox(
    "Eligible Region",
    ["All", "Global", "US", "Europe", "Asia"]
)

# Run Agent Logic
if run_agent:
    st.markdown("### 🔄 Agent Execution Live Feed")
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    def update_progress(step: str, msg: str, pct: float):
        progress_bar.progress(pct)
        status_text.markdown(f"**[{step}]**: {msg}")

    try:
        agent = KlerosAgent()
        result = agent.run(
            query=search_query,
            max_results=max_results,
            max_pages=max_pages,
            progress_callback=update_progress
        )
        st.success(f"Agent Execution Complete! Discovered {result['valid_offers_count']} offers ({result['new_offers_count']} new saved).")
    except Exception as e:
        st.error(f"Error during execution: {e}")

# Load Statistics
stats = db.get_stats()

# Stats Counter Section
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Offers", stats.get("total_offers", 0))
c2.metric("New Today", stats.get("new_today", 0))
c3.metric("API Credits", stats.get("by_type", {}).get("api", 0))
c4.metric("IDE Credits", stats.get("by_type", {}).get("ide", 0))
c5.metric("Chat Subscriptions", stats.get("by_type", {}).get("chat", 0))

st.markdown("---")

# Query Database
offers = db.get_offers(
    offer_type=selected_type if selected_type != "All" else None,
    region=selected_region if selected_region != "All" else None,
    is_valid_only=True
)

st.subheader(f"Discovered Free Offers ({len(offers)})")

# Export CSV Section
if offers:
    df = pd.DataFrame(offers)
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Export Offers CSV",
        data=csv_data,
        file_name="kleros_free_ai_offers.csv",
        mime="text/csv",
        use_container_width=True
    )

if not offers:
    st.info("No offers found matching your current filter. Click **🚀 Run Agent** to discover new deals!")
else:
    # Display offer cards in 2-column grid
    col_a, col_b = st.columns(2)
    for idx, offer in enumerate(offers):
        target_col = col_a if idx % 2 == 0 else col_b
        with target_col:
            off_type = offer.get("offer_type", "api").lower()
            badge_class = f"badge-{off_type}" if off_type in ["api", "ide", "chat", "student"] else "badge-api"
            
            geo_restricted = offer.get("geo_restricted", False)
            regions = offer.get("eligible_regions", ["global"])
            geo_badge_class = "badge-us" if ("us" in regions or "usa" in regions) and len(regions) == 1 else "badge-geo"
            geo_label = "⚠️ US-Only" if geo_badge_class == "badge-us" else f"🌐 {', '.join(regions).upper()}"

            st.markdown(f"""
            <div class="offer-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span class="badge {badge_class}">{off_type.upper()}</span>
                        <span class="badge {geo_badge_class}">{geo_label}</span>
                    </div>
                    <span style="color: #64748b; font-size: 0.8rem;">{offer.get('date_posted') or 'Active'}</span>
                </div>
                <h3 style="color: #f1f5f9; font-size: 1.15rem; margin-top: 0.6rem; margin-bottom: 0.3rem;">
                    {offer.get('name')}
                </h3>
                <p style="color: #38bdf8; font-weight: 600; font-size: 0.95rem; margin: 0.2rem 0;">
                    🎁 {offer.get('value') or 'Free Deal'}
                </p>
                <p style="color: #94a3b8; font-size: 0.88rem; margin-top: 0.4rem; line-height: 1.4;">
                    {offer.get('description') or 'No description provided.'}
                </p>
                <a href="{offer.get('url')}" target="_blank" class="claim-btn">
                    Claim Deal ↗
                </a>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem; padding: 1rem;'>"
    "⚡ Powered by <b>Google Gemini 2.0 Flash</b> + <b>DuckDuckGo</b> + <b>Jina Reader</b> | Licensed under GPL-3.0"
    "</div>",
    unsafe_allow_html=True
)
