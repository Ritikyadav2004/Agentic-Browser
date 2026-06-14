# AI Shopping Agent

Autonomous AI-powered shopping recommendation agent. Given a natural language query
(e.g. *"Best laptop under ₹50,000 for coding"*), the system parses intent with Claude,
scrapes live product data from Amazon, Flipkart, Croma, Reliance Digital, and IKEA using
Playwright, normalizes and stores the results, then uses Claude again to compare and rank
products, returning a best/budget/premium recommendation with a full comparison table.
                                  
## Architecture

```
backend/
 ├── main.py                  # FastAPI app entrypoint
 ├── config.py                 # Settings (env-based)
 ├── routes/
 │    ├── products.py          # /search-products, /compare-products
 │    └── history.py           # /search-history, /recommendations
 ├── agents/
 │    ├── planner_agent.py      # Intent parsing (category/budget/purpose) via Claude
 │    ├── shopping_agent.py      # Orchestrates concurrent scraping
 │    ├── ranking_agent.py       # Claude-based comparison & ranking
 │    └── workflow.py            # LangGraph state machine wiring everything together
 ├── tools/
 │    ├── base_scraper.py
 │    ├── amazon_scraper.py
 │    ├── flipkart_scraper.py
 │    ├── croma_scraper.py
 │    ├── reliance_digital_scraper.py
 │    ├── ikea_scraper.py
 │    └── scraper_registry.py
 ├── services/
 │    ├── claude_service.py      # Anthropic API wrapper + JSON extraction
 │    └── browser_manager.py     # Shared Playwright browser + anti-blocking
 ├── memory/
 │    └── memory_manager.py       # ChromaDB vector memory of past searches
 ├── database/
 │    ├── mongodb.py
 │    └── redis_client.py
 └── models/
      └── schemas.py              # Pydantic request/response models

frontend/
 ├── app/                       # Next.js App Router pages
 ├── components/                # SearchBar, FiltersPanel, ProductCard, ComparisonTable, etc.
 ├── lib/api.ts                 # Fetch helpers
 └── types/api.ts               # TypeScript types mirroring backend schemas
```

## LangGraph Workflow

```
START
 → parse_query              (planner agent: category, budget, purpose, preferences)
 → search_and_scrape         (concurrent Playwright scraping across sites, Redis cached)
 → normalize_data             (dedupe/filter, persist raw products to MongoDB)
 → compare_and_rank            (Claude compares price/performance/ratings/durability/value/fit)
 → generate_recommendation      (persist recommendation to MongoDB)
 → save_memory                   (search history in MongoDB + vector memory in ChromaDB)
END
```

## Setup

### 1. Infrastructure (MongoDB + Redis)

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY

uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Visit http://localhost:3000.

## API Endpoints

- `POST /api/search-products` — `{ "query": "Best laptop under ₹50k for coding", "user_id": "anonymous" }`
  Runs the full LangGraph workflow and returns parsed query, products, and recommendation.
- `POST /api/compare-products` — `{ "products": [...], "purpose": "coding", "budget": 50000 }`
  Ranks a manually supplied product list.
- `GET /api/search-history?user_id=anonymous` — recent search history.
- `GET /api/recommendations?user_id=anonymous` — recent stored recommendations.

## Notes on Scraping

- E-commerce sites frequently change their DOM structure and may show CAPTCHAs.
  Selectors in the scrapers are best-effort and may need periodic updates.
- Anti-blocking measures include: rotating user agents, randomized viewports,
  stealth JS overrides (hiding `navigator.webdriver`), Indian locale/geolocation,
  and randomized delays between actions.
- Each scraper retries up to 3 times with exponential backoff and fails gracefully
  (returns an empty list) so one broken site doesn't break the whole pipeline.
- Results are cached in Redis (per category/budget/purpose) to reduce repeated scraping.
