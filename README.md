# FOUNDER-0

**An autonomous agent pipeline that takes a one-sentence startup idea and ships a real, running product.**

Give it an idea. It researches the competitive landscape, builds a knowledge graph of the market gap, synthesizes a product concept, writes and deploys a working MVP inside an isolated cloud sandbox, and hands back a live URL — with every step's real output visible, not simulated.

Built for the Daytona HackSprint Singapore.

---

## What it actually does

Most "AI builds a startup" demos are a single LLM call dressed up in a nice UI. FOUNDER-0 is a 13-stage pipeline where each stage does one real, verifiable thing and hands structured output to the next:

| Stage | What happens |
|---|---|
| **Market Recon** | Classifies the idea into a market category and surfaces real named competitors, live-search-augmented where possible |
| **Competitor Enrichment** | Best-effort live fetch of each competitor's site for real metadata |
| **Opportunity Graph** | Ingests competitors, features, and complaints into a live Neo4j knowledge graph |
| **Whitespace Analysis** | Queries the graph to find the specific, underserved gap in the market |
| **Ideation** | An LLM (hosted on **Nosana's decentralized GPU network**) synthesizes a product name, tagline, pitch, and feature set grounded in the actual whitespace found |
| **Spec Generation** | Turns the product concept into a concrete technical feature spec |
| **MVP Scaffold** | Provisions a real, isolated **Daytona sandbox** and stages a zero-dependency starter template |
| **MVP Code Generation** | The Nosana LLM generates every piece of the MVP's actual content — hero copy and each feature's HTML + interactive JS — nothing here is a hardcoded template |
| **Build & Test** | Runs a real syntax check and a real HTTP health check against the server running inside the sandbox |
| **Self-Heal Loop** | If something's broken, feeds the real error back to the LLM for a bounded, targeted repair — and degrades honestly to a working baseline if repair doesn't succeed, rather than faking a pass |
| **Deploy Preview** | Polls the sandbox with real HTTP requests until the MVP is confirmed reachable, then exposes it |
| **Screenshot + Report** | Captures the live app and assembles a pitch-ready summary of the whole run |

The MVP itself is deliberately boring on purpose: plain HTML, CSS, and vanilla JavaScript served by a zero-dependency Node server. No build step, no TypeScript compiler, no framework — because the one thing an AI-generated app cannot afford to do live in front of judges is fail a build for a reason that has nothing to do with the actual product.

### Why this is a real integration, not a demo skin

- **Daytona** isn't a wrapper around `subprocess.run` — it's the official `daytona` Python SDK, provisioning a real isolated sandbox with its own filesystem and process execution, with a real public preview URL. A failed command comes back as a failed command; nothing here silently reports success it didn't earn.
- **Nosana** generates the actual product content live — the hero copy and every feature's markup/behavior are model output, not a filled-in template.
- **Neo4j** holds a real, queryable graph that the whitespace analysis stage runs actual Cypher against to find the market gap — it's not decoration.
- Every stage is independently logged, timestamped, and streamed to the dashboard in real time, so a judge (or you, debugging at 3am) can see exactly what happened and why.

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt --break-system-packages
cd frontend && npm install && cd ..
```

### 2. Configure your `.env`

Copy the provided `.env` (already present) or start from scratch:

```dotenv
MOCK_MODE=true                # true = zero external accounts needed, full offline dry-run
DATABASE_URL=sqlite+aiosqlite:///./founder0.db

DAYTONA_API_KEY=
DAYTONA_API_URL=https://app.daytona.io/api
DAYTONA_TARGET=us

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

NOSANA_API_KEY=
NOSANA_BASE_URL=https://api.nosana.io/v1
NOSANA_MODEL_ID=deepseek-coder

FALLBACK_LLM_PROVIDER=anthropic
FALLBACK_LLM_API_KEY=
```

**Run with `MOCK_MODE=true` first.** Every stage has a realistic offline fallback, so you can verify the whole pipeline works before spending a single API call. Flip it to `false` only once you've confirmed a clean mock run.

### 3. (Optional) Start Neo4j locally

```bash
docker-compose up -d neo4j
```

If you skip this, the graph stage runs against an in-memory fallback — fine for a dry run, but you'll want real Neo4j for the live demo so the graph visualization actually has something to show.

### 4. Seed the baseline knowledge graph

```bash
python -m orchestrator.seed_graph
```

This populates the graph with a baseline set of known competitors/features so early runs land in an already-connected graph instead of starting from nothing.

### 5. Run it

**Backend:**
```bash
uvicorn orchestrator.main:app --reload --port 8000
```

**Frontend dashboard:**
```bash
cd frontend && npm run dev
```

**Or from the CLI, no dashboard needed:**
```bash
python -m cli.founder0 run "an app that predicts the stock market"
python -m cli.founder0 list
python -m cli.founder0 status <run_id>
python -m cli.founder0 replay <run_id>
```

The CLI streams every stage's live log output to your terminal and prints the final preview URL and generated report path on completion.

---

## Repo structure

```
orchestrator/
├── main.py                # FastAPI app — REST + WebSocket API
├── state_machine.py        # The 13-stage pipeline orchestration
├── models.py                # Typed I/O for every stage
├── stages/                  # One file per pipeline stage
├── clients/
│   ├── web_search_client.py # Best-effort live search + curated fixture fallback
│   ├── daytona_client.py    # Real Daytona SDK integration
│   ├── nosana_client.py     # Real Nosana LLM integration, with fallback provider
│   ├── neo4j_client.py
│   └── fallback_llm_client.py
└── seed_graph.py
templates/
└── vanilla-static-starter/  # The zero-build HTML/CSS/JS MVP template
fixtures/market_recon/       # Offline category fixtures used in MOCK_MODE
frontend/                    # React dashboard — live pipeline + graph view
cli/founder0.py               # Terminal interface
```

---

## Honesty note on MOCK_MODE

`MOCK_MODE=true` is not a lesser demo path bolted on as an afterthought — it's how this project could be built and iterated on without burning API quota on every test, and it's the reason the pipeline can be verified end-to-end offline before ever touching a live key. Every client (`web_search_client`, `nosana_client`, `daytona_client`) makes that switch explicit and logs which mode it's running in — nothing pretends to be live when it isn't.

## Known limitations

- Live web search (used in Market Recon when not relying on curated fixtures) is best-effort against a free, unauthenticated endpoint — it can be rate-limited or blocked, in which case the stage falls back to curated fixture data and says so in the logs.
- The self-heal loop is bounded (2 retries by default) and degrades to a clean baseline page rather than retrying indefinitely — a working generic MVP beats a stuck pipeline.
- The MVP template is intentionally minimal (landing page + waitlist signup) so that generation and build verification stay fast and reliable during a live run.
