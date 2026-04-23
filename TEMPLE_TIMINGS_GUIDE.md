# 🕉️ Temple Data & Timings Guide

## Problem: Kashi Vishwanath Temple Timings

The issue is that **temple timing information is not always available in structured databases**. NamanDarshan.com displays timing information dynamically on their website, but this data isn't always present in their API responses.

## Solution: Multi-Layered Approach

Your AI Agent has **3 ways to retrieve temple timing information**:

### 1️⃣ **Local Database (Fastest)**
```
Agent Tool: get_temple_info(name="Kashi Vishwanath Temple", city="Varanasi")
```
- ✅ Checks Excel database (data/namandarshan_data.xlsx)
- ⚠️ Limited data (temples added manually)
- 💾 Cached data, no external calls

**Result**: Returns structured temple data if available

---

### 2️⃣ **NamanDarshan.com Web Scraping (Recommended)**

#### Option A: Search NamanDarshan Pages
```
Agent Tool: nd_web_search(query="Kashi Vishwanath temple timings")
```
- Searches across all namandarshan.com pages
- Returns matching results with snippets
- **Output**: List of relevant pages

#### Option B: Fetch Specific Page
```
Agent Tool: nd_fetch_page(path_or_url="/temples/kashi-vishwanath-temple")
```
- Fetches the full page content
- Extracts readable text (removes HTML/scripts)
- **Output**: Complete page text including timing info if available

**Example Response**:
```json
{
  "url": "https://namandarshan.com/temples/kashi-vishwanath-temple",
  "title": "Kashi Vishwanath Temple - NamanDarshan",
  "text": "Opening hours...\nTemple timings...\n[timing details here]"
}
```

---

### 3️⃣ **NamanDarshan API (Structured Data)**

```
Agent Tool: nd_get_darshan(slug="kashi-vishwanath-temple")
```
- Fetches structured JSON data from api.namandarshan.com
- Includes services, bookings, VIP darshan info
- **Limited timing info** (may not have opening/closing times)

---

## 🤖 How the Agent Uses These Tools

When you ask: *"What are the timings for Kashi Vishwanath Temple?"*

The agent will:

1. **Try local database first** - Check Excel for pre-stored data
2. **If not found** - Automatically search NamanDarshan.com
3. **Fetch the page** - Extract timing info from web pages
4. **Fall back to Google** - General web search if needed

---

## 📊 Data Flow Architecture

```
User Query: "Kashi Vishwanath timings?"
        ↓
    ┌───────────────────────────────────────────┐
    │  1. get_temple_info()                      │
    │     └─→ Check: data/namandarshan_data.xlsx │
    └───────────────────────────────────────────┘
        ↓ (If not found)
    ┌──────────────────────────────────────────────┐
    │  2. nd_web_search()                          │
    │     └─→ Search: namandarshan.com             │
    └──────────────────────────────────────────────┘
        ↓ (Get matching URLs)
    ┌──────────────────────────────────────────────┐
    │  3. nd_fetch_page()                          │
    │     └─→ Extract text from best match         │
    └──────────────────────────────────────────────┘
        ↓
    📝 Return timing info to user
```

---

## ✅ How to Enrich Temple Data

### Method 1: Run the Fetch Script (Automated)
```bash
cd /Backend
python ../scripts/fetch_kashi_temple.py
```
- Downloads temple data from API
- Adds to Excel if missing
- Caches page content

### Method 2: Manual Excel Update
1. Open `data/namandarshan_data.xlsx`
2. Go to **Temples** sheet
3. Add rows with:
   - Name, City, State
   - Deity, Website
   - Opening_Time, Closing_Time
   - Special_Timings, Contact

### Method 3: User Provides During Chat
Agent can remember: `update_session_context(temple_timings="5 AM - 8 PM daily")`

---

## 🛠️ Configuration

### Environment Variables
```bash
# .env file
NAMANDARSHAN_BASE_URL=https://namandarshan.com
ENABLE_NAMANDARSHAN_SCRAPE=true
SCRAPE_MAX_PAGES=8
SCRAPE_TIMEOUT_SEC=10
```

### Tools Configuration
All tools are defined in `Backend/tools.py`:
- `nd_web_search` - Site-limited search
- `nd_fetch_page` - Page scraping
- `nd_get_darshan` - API data
- `google_search` - General web search (fallback)

---

## 📋 Real Example: Kashi Vishwanath

**URL on NamanDarshan**: https://namandarshan.com/temples/kashi-vishwanath-temple

**Available Information**:
- ✅ VIP Darshan booking options
- ✅ Crowd management services
- ✅ Pickup assistance details
- ⚠️ Timing info (may be in page content)

**Agent Actions**:
```
→ nd_web_search("Kashi Vishwanath temple timings")
→ nd_fetch_page("/temples/kashi-vishwanath-temple")
→ Extract timings from page text
→ Return to user
```

---

## 🔄 Caching Strategy

All fetches are **cached for 5 minutes** to avoid:
- Hammering the website
- Slow responses
- Rate limiting

Cache locations:
- Local pages: `_cache` in namandarshan_scrape.py
- API responses: `_cache` in namandarshan_api.py

---

## 🎯 Next Steps

1. ✅ **Already Done**: Temples sheet added to Excel
2. **Test**: Ask agent for temple timings
3. **Enhance**: Run scraping scripts to populate more temples
4. **Monitor**: Check agent logs for tool usage patterns

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Temple not found" | Try `nd_web_search()` - checks namandarshan.com |
| Incomplete timing data | Use `nd_fetch_page()` directly for full page content |
| Missing Excel sheet | Automatically created on first temple fetch |
| Page scraping fails | Website structure may have changed; use API fallback |

---

## 🎓 Learning Resources

- **NamanDarshan.com**: Browse temples and services
- **API Documentation**: Check api.namandarshan.com for available endpoints
- **Code**: See `Backend/tools.py` for all available agent tools
- **Data Scripts**: `scripts/fetch_kashi_temple.py` for data collection
