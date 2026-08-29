# FOUNDER-0 🚀
### Autonomous Multi-Agent Venture Engine

FOUNDER-0 is an autonomous multi-agent pipeline that transforms a single one-sentence startup idea into:
1. **Real competitive market reconnaissance & user complaint scraping** (Oxylabs)
2. **Interactive Opportunity Knowledge Graph** (Neo4j)
3. **Structured whitespace & feature void analysis**
4. **Synthesized product concept & branding package** (Nosana GPU LLM)
5. **Technical component & data model specification**
6. **Isolated Next.js + SQLite application scaffold** (Daytona Sandbox)
7. **Autonomous feature code generation & self-healing build validation**
8. **Live deployed preview URL with health verification** (Daytona Preview)
9. **Headless screenshot capture & investor pitch deck** (HTML/CSS + QR code)
10. **45-second spoken pitch narration script**

---

## 1. System Architecture

```
+------------------------------------------------------------------------------------------------------------------------------------+
|                                                          FOUNDER-0 PIPELINE                                                        |
+------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                                    |
|  [1. IDEA_RECEIVED] --------> [2. MARKET_RECON] (Oxylabs Search / Complaints)                                                      |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [3. COMPETITOR_ENRICHMENT] (Oxylabs Deep Web Scraper)                                                   |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [4. OPPORTUNITY_GRAPH] (Neo4j Nodes & Edges MERGE)                                                      |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [5. WHITESPACE_ANALYSIS] (Cypher Gap & Sentiment Analysis)                                              |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [6. IDEATION & BRANDING] (Nosana LLM / Fallback LLM)                                                    |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [7. SPEC_GENERATION] (Structured UI/Data Component Spec)                                                |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [8. MVP_SCAFFOLD] (Daytona Sandbox / Next.js Starter)                                                   |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [9. MVP_CODE_GENERATION] (Parallel React Feature Gen)                                                   |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [10. MVP_BUILD_AND_TEST] (Daytona Build / Runtime Smoke)                                                |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [11. MVP_SELF_HEAL_LOOP] (Error Capture + Bounded Retry)                                                |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [12. MVP_DEPLOY_PREVIEW] (Daytona Public Preview URL)                                                   |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [13. SCREENSHOT_CAPTURE] (Playwright / Headless Browser)                                                |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [14. DECK_GENERATION] (Dynamic HTML/CSS/PDF Pitch Deck)                                                 |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                            [15. NARRATION_GENERATION] (45s Spoken Pitch + TTS Audio)                                               |
|                                      |                                                                                             |
|                                      v                                                                                             |
|                                [COMPLETE]                                                                                          |
+------------------------------------------------------------------------------------------------------------------------------------+
```

---

## 2. Quickstart (Zero-Dependency Mock Mode)

FOUNDER-0 works out of the box in **Mock Mode** (`MOCK_MODE=true` in `.env`) without requiring external API keys.

### 2.1 Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2.2 Run Backend & Orchestrator

```bash
python -m uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000 --reload
```

The orchestrator service will be live at `http://localhost:8000`.

### 2.3 Run Frontend Dashboard

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` to access the interactive web dashboard.

---

## 3. CLI Usage

The rich terminal CLI allows triggering runs, monitoring real-time streaming logs, and replaying:

```bash
# 1. Run a new idea end-to-end with live terminal logs
python cli/founder0.py run "an app for splitting bills with roommates who hate each other"

# 2. List all runs
python cli/founder0.py list

# 3. Inspect a specific run timeline
python cli/founder0.py status <run_id>

# 4. Replay a run from scratch
python cli/founder0.py replay <run_id>

# 5. Pre-seed baseline Neo4j opportunity graph
python cli/founder0.py seed-graph
```

---

## 4. Live Mode Configuration

To run live integrations against real APIs, set `MOCK_MODE=false` in `.env` and provide your credentials:

```env
MOCK_MODE=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./founder0.db

# Daytona API
DAYTONA_API_KEY=your_daytona_api_key
DAYTONA_SERVER_URL=https://app.daytona.io/api

# Oxylabs Search & Scrape
OXYLABS_USERNAME=your_oxylabs_username
OXYLABS_PASSWORD=your_oxylabs_password

# Neo4j Graph Database (docker-compose up -d)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Nosana GPU LLM Inference
NOSANA_API_KEY=your_nosana_key
NOSANA_BASE_URL=https://api.nosana.io/v1
NOSANA_MODEL_ID=deepseek-coder

# Fallback LLM Provider
FALLBACK_LLM_PROVIDER=anthropic
FALLBACK_LLM_API_KEY=your_anthropic_key
```

To launch local PostgreSQL and Neo4j instances:
```bash
docker-compose up -d
```

---

## 5. Running Tests

Run the unit tests for all 15 stages:
```bash
pytest tests/unit/ -v
```

Run the end-to-end integration test:
```bash
pytest tests/integration/ -v
```

---

## 6. Monorepo Structure

```
founder0/
├── orchestrator/
│   ├── main.py                 # FastAPI REST + WebSocket Server
│   ├── state_machine.py        # 15-Stage State Machine Coordinator
│   ├── database.py             # SQLAlchemy Async Engine (SQLite/Postgres)
│   ├── models.py               # ORM Tables & Pydantic Schemas
│   ├── config.py               # Environment Settings
│   ├── seed_graph.py           # Baseline Neo4j Seeding
│   ├── clients/
│   │   ├── daytona_client.py   # Daytona Sandbox Client & Local Sim
│   │   ├── oxylabs_client.py   # Oxylabs Realtime Search & Deep Scraper
│   │   ├── neo4j_client.py     # Parameterized Cypher & In-Memory Graph
│   │   ├── nosana_client.py    # Nosana GPU LLM Inference
│   │   └── fallback_llm_client.py # Anthropic / OpenAI Fallback
│   └── stages/
│       ├── market_recon.py
│       ├── competitor_enrichment.py
│       ├── opportunity_graph.py
│       ├── whitespace_analysis.py
│       ├── ideation.py
│       ├── naming_branding.py
│       ├── spec_generation.py
│       ├── mvp_scaffold.py
│       ├── mvp_codegen.py
│       ├── mvp_build_test.py
│       ├── mvp_self_heal.py
│       ├── mvp_deploy.py
│       ├── screenshot.py
│       ├── deck_generation.py
│       └── narration.py
├── templates/
│   └── nextjs-sqlite-starter/  # Next.js App Router + SQLite Starter
├── frontend/                   # React + Vite + Tailwind Dashboard
├── cli/
│   └── founder0.py             # Rich Terminal CLI
├── fixtures/                   # 5 Industry Benchmark Fixtures
├── tests/
│   ├── unit/
│   └── integration/
├── docker-compose.yml          # Postgres + Neo4j services
├── requirements.txt
└── README.md
```
