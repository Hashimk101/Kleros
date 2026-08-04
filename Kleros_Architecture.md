Perfect! Now I understand exactly what you need. Here's the architecture MD file for AI-assisted development:

---

# 🏛️ KLEROS: Autonomous Discovery Agent for Free AI Resources

## 📋 Project Overview

### What is Kleros?
Kleros is an autonomous, on-demand discovery agent that finds, extracts, and validates free LLM APIs, IDE credits, and chat subscriptions specifically for students.

### The Problem It Solves
Free AI resources expire fast and are buried in noise. Students waste hours hunting for:
- Free API credits (OpenRouter, Gemini, Claude, etc.)
- IDE credits (Zed, Antigravity, Cursor, etc.)
- Chat subscriptions (Gemini Student, ChatGPT Edu, etc.)
- Student-specific programs

Kleros does the hunting so students don't have to.

### Target Userbase
- **Primary:** Students looking for free AI resources
- **Secondary:** Developers, educators, researchers
- **Tertiary:** Anyone wanting to discover free AI tools

### Core Value Proposition
> *"Free AI resources expire fast and are buried in noise. This agent does the hunting so you don't waste hours searching."*

---

## 🎯 Project Scope

### ✅ IN SCOPE
- LLM APIs (OpenRouter, AgentRouter, Gemini, Claude)
- IDE credits (Zed, Antigravity, Cursor, VS Code)
- Chat subscriptions (Gemini Student, ChatGPT Edu, Claude Pro)
- Student-specific programs
- Global and student-verified deals

### ❌ OUT OF SCOPE
- GPU compute credits
- Fine-tuning credits
- Vector databases
- Non-LLM AI tools
- Paid tiers
- Enterprise offers
- USA/Canada-only offers (filtered out)

### ⚠️ GEOGRAPHIC FOCUS
- **Prioritize:** Global offers, student-verified deals
- **Filter:** Auto-hide USA/Canada-only offers
- **Flag:** Show geo-restrictions clearly when present

---

## 🏗️ Core Architecture

### High-Level Flow (5 Steps)

```
1. SEARCH → 2. FETCH → 3. EXTRACT → 4. FILTER → 5. DISPLAY
```

### Component Breakdown

Each component is independent and can be modified or replaced:

| Component | Responsibility | Can Be Modified To |
|-----------|---------------|-------------------|
| **Search Router** | Find URLs from multiple sources | Add more search sources, change ranking |
| **Content Fetcher** | Get page content via Jina | Use different rendering engine, add fallbacks |
| **LLM Extractor** | Extract structured offers | Change prompts, add more LLM providers |
| **Filter Engine** | Validate and filter offers | Add custom rules, change filtering logic |
| **Database** | Store and retrieve offers | Switch to different DB, change schema |
| **Dashboard** | Display results to user | Change UI, add more views |

---

## 📊 Component Specifications

### 1. SEARCH ROUTER

**Purpose:** Find URLs that might contain free offers

**Input:**
- Search query (string)
- Optional: max_results (integer, default 10-20)

**Output:**
- List of URLs with metadata:
  - URL
  - Title
  - Snippet/Description
  - Source (which search engine found it)
  - Date (if available)

**Tools Used:**
- **Primary:** DuckDuckGo (via duckduckgo-search library)
  - Unlimited queries
  - No API key needed
  - Async support
  - Add 1-2s delays between requests
  - Returns: title, href, body

- **Fallback:** SearXNG (public instances)
  - Aggregates Google/Bing/Brave results
  - No API key needed
  - Use 3-5 public instances from searx.space
  - Rotate instances every 5 queries
  - JSON API at /search?format=json

**Key Behaviors:**
1. Try DDG first (primary)
2. If DDG returns <3 results → fallback to SearXNG
3. Parallel search possible (DDG + SearXNG together)
4. Deduplicate results by URL
5. Return unique URLs only

**Modification Points:**
- Add more search sources (Google CSE, Serper, etc.)
- Change primary/fallback order
- Adjust number of results per source

---

### 2. CONTENT FETCHER

**Purpose:** Get clean content from URLs

**Input:**
- List of URLs from Search Router

**Output:**
- Markdown content for each URL
- Clean, readable text (no HTML, no JavaScript)
- Ready for LLM extraction

**Tools Used:**
- **Jina Reader API** (primary)
  - URL format: `https://r.jina.ai/{target_url}`
  - No API key required
  - Free (no known rate limits)
  - Renders JavaScript (handles React/SPA)
  - Returns clean markdown
  - Bypasses Cloudflare
  - Strips ads/navigation

- **Headers to use:**
  - `User-Agent`: Standard browser user agent
  - `Accept`: text/html,application/xhtml+xml

**Key Behaviors:**
1. For each URL → call Jina Reader
2. Keep ALL content (no length filtering)
3. Process URLs in parallel (async)
4. No discarding based on content length
5. No discarding based on site type
6. If Jina fails → skip URL (no fallback needed)

**Modification Points:**
- Add fallback content fetcher (Trafilatura, BeautifulSoup)
- Implement content validation rules
- Change parallelization strategy

---

### 3. LLM EXTRACTOR

**Purpose:** Extract structured offers from page content

**Input:**
- Markdown content from Content Fetcher
- Optional: Search query context

**Output:**
- Structured JSON offer objects:
  - `name`: The offer name (required)
  - `url`: The URL (required)
  - `offer_type`: "api" | "ide" | "chat" | "student" (required)
  - `value`: Free credits/value description
  - `geo_restricted`: boolean
  - `eligible_regions`: ["global", "us", "europe", etc.]
  - `date_posted`: YYYY-MM-DD or null
  - `source_type`: "blog" | "forum" | "official" | "social"
  - `description`: Brief description of the offer

**Tools Used:**
- **Primary:** Google AI Studio (Gemini 2.0 Flash)
  - Free tier: 15 RPM, 1M TPM
  - No credit card required
  - Best reasoning for extraction
  - Fast response times

- **Fallback:** OpenRouter
  - Access to free models (Qwen3-Coder, Gemini Flash, etc.)
  - No credit card required
  - Unified API
  - Check /models?sort=pricing-low for free models

**Prompt Structure:**

```
You are an AI that finds free student resources. Extract structured data from these search results.

Search Results:
[Content from page]

Extract any offers that match these types:
- LLM API credits (OpenRouter, Gemini, Claude, etc.)
- IDE credits (Zed, Antigravity, Cursor, etc.)
- Chat subscriptions (Gemini Student, ChatGPT Edu, etc.)
- Student-specific programs

Return a JSON array. Each object must have:
- name: The offer name
- url: The URL
- offer_type: "api" or "ide" or "chat" or "student"
- value: The free credits/value (e.g., "$100 credits")
- geo_restricted: true/false
- eligible_regions: ["global"] or ["us", "europe"] etc.
- date_posted: YYYY-MM-DD if available, else null
- source_type: "blog" or "forum" or "official"

Return ONLY the JSON array, nothing else.
```

**Key Behaviors:**
1. Send each page content to Gemini
2. Parse JSON response
3. Validate required fields (name, url, offer_type)
4. If Gemini fails → use OpenRouter fallback
5. If both fail → skip this page
6. Process pages sequentially (avoid rate limits)

**Modification Points:**
- Change prompt structure
- Add more LLM providers (Groq, Cohere, etc.)
- Add retry logic with exponential backoff
- Implement streaming extraction

---

### 4. FILTER ENGINE

**Purpose:** Keep only valid, relevant offers

**Input:**
- Raw offers from LLM Extractor

**Output:**
- Clean, validated offers

**Filtering Rules:**

1. **Required Fields**
   - `name`: Must exist and not be empty
   - `url`: Must exist and be a valid URL
   - `offer_type`: Must be one of: api, ide, chat, student

2. **Type Validation**
   - Only keep: API, IDE, Chat, Student
   - Reject everything else

3. **Geo-Restriction Filter**
   - Auto-hide USA/Canada-only offers
   - Prioritize: "global" > "europe" > "asia" > "us"
   - Flag US-only offers with a warning
   - Do not discard US-only (just mark them)

4. **Deduplication**
   - Remove offers with same URL
   - Keep the first occurrence

5. **Date Filtering (Optional)**
   - If date exists, check if within last 90 days
   - No date → keep it (might still be valid)

**Modification Points:**
- Add custom filtering rules
- Change geo-prioritization logic
- Add blacklist/whitelist for URLs
- Add validity checks (URL reachability)

---

### 5. DATABASE

**Purpose:** Store and cache offers

**Input:**
- Validated offers from Filter Engine

**Output:**
- Saved offers (success/failure status)

**Tools Used:**
- **SQLite** (local database)
  - No setup required
  - Single file: `offers.db`
  - Local-only storage
  - Suitable for personal use

**Schema:**

```
offers:
  - id: INTEGER PRIMARY KEY
  - name: TEXT NOT NULL
  - url: TEXT UNIQUE NOT NULL
  - offer_type: TEXT (api|ide|chat|student)
  - value: TEXT
  - description: TEXT
  - geo_restricted: BOOLEAN
  - eligible_regions: TEXT (JSON array)
  - date_posted: DATE
  - source_type: TEXT (blog|forum|official|social)
  - source_url: TEXT
  - is_valid: BOOLEAN
  - created_at: TIMESTAMP
  - last_seen: TIMESTAMP
```

**Indexes:**
- `idx_offers_type` on `offer_type`
- `idx_offers_date` on `date_posted`
- `idx_offers_valid` on `is_valid`

**Key Behaviors:**
1. Before inserting, check if URL already exists
2. If exists → update `last_seen` timestamp
3. If new → insert with `created_at` timestamp
4. Keep history of offers found

**Modification Points:**
- Switch to Supabase (cloud database)
- Add more tables (search_history, user_preferences)
- Change storage format (JSON, Parquet)

---

### 6. DASHBOARD

**Purpose:** Display results to user

**Input:**
- Offers from Database
- User interactions (filters, searches)

**Output:**
- Interactive UI

**Tools Used:**
- **Streamlit**
  - Free hosting
  - Python-native
  - Perfect for personal dashboards
  - No frontend experience needed

**UI Layout:**

```
Top Section:
- Project Title: "🏛️ Kleros: Free AI Resource Finder"
- Search Query Input Box (default: "free LLM API credits IDE subscriptions for students 2026")
- "🚀 Run Agent" Button

Stats Section:
- Total offers found
- New offers today
- Breakdown by type

Filter Section:
- Type Filter: All | API | IDE | Chat | Student
- Geo Filter: All | Global | US | Europe | Asia

Results Section:
- Offer Cards (grid or list view)
  - Name
  - Type badge
  - Value description
  - Geo restriction flag
  - Date (if available)
  - Link to source
  - Brief description

Footer:
- "⚡ Powered by Gemini + DuckDuckGo + Jina Reader"
- GitHub link
```

**Key Behaviors:**
1. Show progress during agent execution
   - 🔍 Searching...
   - 📄 Fetching content...
   - 🧠 Extracting offers...
   - ✅ Done!
2. Display results in cards
3. Allow filtering and sorting
4. Show stats and metrics

**Modification Points:**
- Add dark/light theme toggle
- Add export to CSV
- Add email alerts
- Add historical trends

---

## 🔄 Data Flow Examples

### Example 1: Zed IDE Student Offer

```
1. SEARCH
   Query: "Zed IDE student free credits"
   → DuckDuckGo returns:
      - "Zed Student Plan Announcement" (dev.to blog)
      - "Zed IDE Pricing" (zed.dev/pricing)
      - "Zed for Students" (reddit thread)

2. FETCH
   → Jina Reader on each URL:
      - dev.to article → Clean markdown
      - zed.dev/pricing → Rendered React page
      - reddit thread → Clean text

3. EXTRACT
   → Gemini processes each page:
      - dev.to: "Zed offers free credits to students"
      - pricing page: "Student plan: $0/month"
      - reddit: "I got Zed for free with .edu email"

4. FILTER
   → Validate offers:
      - "Zed Student Plan" → valid (api credits)
      - Remove duplicates
      - Flag: "global" (not US-only)

5. DISPLAY
   → Show in dashboard:
      - Name: "Zed IDE Student Plan"
      - Type: IDE
      - Value: "Free IDE credits"
      - Geo: Global
      - Link: dev.to announcement
```

---

### Example 2: Gemini API Free Credits

```
1. SEARCH
   Query: "Gemini API free credits students"
   → DuckDuckGo returns:
      - "Google AI Studio pricing" (official)
      - "Gemini free tier" (blog post)
      - "How to get Gemini API" (forum)

2. FETCH
   → Jina Reader:
      - aistudio.google.com → Renders React SPA
      - blog.google → Static blog post
      - forum thread → Clean text

3. EXTRACT
   → Gemini processes:
      - Official page: "$300 free credits"
      - Blog: "Gemini 2.0 Flash free"
      - Forum: "I got free credits"

4. FILTER
   → Validate:
      - "Google AI Studio Free Tier" → valid
      - Type: API
      - Value: "$300 credits"
      - Geo: Global (with restrictions)

5. DISPLAY
   → Show in dashboard:
      - Name: "Google AI Studio Free Credits"
      - Type: API
      - Value: "$300 free credits"
      - Geo: Check eligibility
      - Link: Official pricing page
```

---

### Example 3: Mixed Results (Forum + Blog + Official)

```
1. SEARCH
   Query: "free ChatGPT Edu student"
   → Results from DDG + SearXNG:
      - Official: openai.com/chatgpt/edu
      - Blog: "ChatGPT Edu announced"
      - Forum: Reddit discussion
      - News: TechCrunch article

2. FETCH
   → Jina Reader on all:
      - Official page → Rendered React
      - Blog → Static HTML
      - Reddit → Clean text
      - TechCrunch → Static article

3. EXTRACT
   → Gemini processes all pages:
      - Official: "Free for students"
      - Blog: "ChatGPT Edu free tier"
      - Reddit: "I got access"
      - News: "OpenAI launches Edu"

4. FILTER
   → Validate:
      - "ChatGPT Edu" → valid
      - Type: Chat
      - Value: "Free subscription"
      - Geo: US-only (flag it)
      - Keep despite US restriction

5. DISPLAY
   → Show in dashboard:
      - Name: "ChatGPT Edu"
      - Type: Chat
      - Value: "Free for students"
      - Geo: ⚠️ US-only (flagged)
      - Link: Official page
      - Note: "US-only, alternative: Gemini Student"
```

---

## ⚡ Rate Limiting Strategy

### By Service

| Service | Limit | Strategy |
|---------|-------|----------|
| **Gemini** | 15 RPM, 1M TPM | Add 2-3s delay between requests |
| **OpenRouter** | Varies by model | Rotate free models |
| **DuckDuckGo** | Unenforced | Add 1-2s delay between requests |
| **SearXNG** | Per instance | Rotate instances every 5 queries |
| **Jina Reader** | No known limit | None needed |

### Recommended Delays

```python
# Between search requests
delay_search = 1.0  # seconds

# Between LLM requests  
delay_llm = 2.0  # seconds

# Between fetch requests
delay_fetch = 0.5  # seconds (parallel processing)
```

### Fallback Strategy

1. **Gemini fails** → OpenRouter fallback
2. **OpenRouter fails** → Skip this page
3. **DDG rate limited** → SearXNG fallback
4. **SearXNG fails** → Try different instance
5. **Jina Reader fails** → Skip URL

---

## 📁 Configuration

### Environment Variables (.env)

```
# Required
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional (defaults)
MAX_RESULTS=10
MAX_PAGES=5
SEARCH_DELAY=1
LLM_DELAY=2
DATE_FILTER_DAYS=90
```

### Constants

```python
# Search
DEFAULT_QUERY = "free LLM API credits IDE subscriptions for students 2026"
MAX_SEARCH_RESULTS = 10-20
MIN_SEARCH_RESULTS = 3  # If less, use fallback

# Fetch
MAX_PAGES_TO_FETCH = 5  # Process top N URLs
PARALLEL_FETCH = True  # Fetch multiple URLs at once

# LLM
PRIMARY_LLM = "Gemini 2.0 Flash"
FALLBACK_LLM = "OpenRouter (free models)"
MAX_RETRIES = 2

# Filtering
PRIORITY_REGIONS = ["global", "europe", "asia", "us"]
MAX_AGE_DAYS = 90  # Ignore offers older than this

# Database
DB_PATH = "offers.db"
CACHE_DAYS = 7  # Don't re-process same URL within 7 days
```

---

## 🔧 Development Notes

### Local Setup

1. Clone the repository
2. Create `.env` file with API keys
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `streamlit run dashboard.py`

### Project Structure

```
kleros/
├── src/
│   ├── search.py       # Search Router
│   ├── fetch.py        # Content Fetcher
│   ├── extractor.py    # LLM Extractor
│   ├── filter.py       # Filter Engine
│   ├── database.py     # Database operations
│   └── agent.py        # Main orchestrator
├── dashboard.py        # Streamlit UI
├── .env                # API keys (not committed)
├── .env.example        # Template
├── requirements.txt    # Dependencies
├── README.md           # Documentation
└── LICENSE             # GPL-3.0
```

### Error Handling Expectations

The AI implementing this should handle:

1. **Missing API keys** → Show clear error message
2. **Rate limiting** → Add delays and retry
3. **Failed requests** → Log and continue
4. **Malformed JSON** → Parse safely
5. **Empty results** → Show "No offers found" message
6. **Network errors** → Retry with backoff
7. **Invalid URLs** → Skip gracefully

---

## 🎯 Development Priorities

### Phase 1: Core MVP
- [ ] Search Router (DDG + SearXNG)
- [ ] Content Fetcher (Jina Reader)
- [ ] LLM Extractor (Gemini + OpenRouter)
- [ ] Filter Engine (basic rules)
- [ ] SQLite Database
- [ ] Streamlit Dashboard

### Phase 2: Enhancements
- [ ] Geo-prioritization
- [ ] Deduplication
- [ ] Date filtering
- [ ] Progress indicators
- [ ] Better error handling

### Phase 3: Polish
- [ ] Caching
- [ ] Export functionality
- [ ] Statistics
- [ ] Dark mode (optional)

---

## 📝 Notes for AI Implementation

1. **Search:** Implement DDG first, SearXNG as fallback
2. **Fetch:** Jina Reader only, no fallbacks needed
3. **Extract:** Gemini primary, OpenRouter fallback
4. **Filter:** Start with required fields + deduplication
5. **Database:** SQLite with schema provided
6. **Dashboard:** Streamlit with basic layout
7. **Error Handling:** Graceful degradation
8. **Rate Limits:** Respect all free tier limits

---

## 🎓 Summary for Students (Target Users)

Kleros is for students who:
- Want free AI resources but don't know where to find them
- Waste hours searching for expired offers
- Need student-verified deals
- Want to filter out USA/Canada-only offers

Kleros finds:
- Free API credits (OpenRouter, Gemini, Claude)
- Free IDE credits (Zed, Antigravity, Cursor)
- Free chat subscriptions (Gemini Student, ChatGPT Edu)
- Student-specific programs

Kleros runs:
- On-demand (click "Run")
- Locally (on your machine)
- For free (all services have free tiers)

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0**.

This means:
- ✅ You can use, modify, and distribute this code
- ✅ You must include the original copyright notice
- ✅ Any derivative works must also be open source
- ✅ You must disclose your source code
- ✅ You must state any changes you made

---

## 🙏 Acknowledgements

- Built with Google Gemini 2.0 Flash
- Search powered by DuckDuckGo & SearXNG
- Content rendering by Jina Reader
- Dashboard powered by Streamlit
- Inspired by the need for accessible AI tools

---

*This document is for AI-assisted development. The AI should generate code based on this architecture, not copy it directly.*