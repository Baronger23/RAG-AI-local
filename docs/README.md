# GeekBrain W4: AI That Actually Answers — Implementation

Complete working implementation of a RAG + Tool-Augmented AI system for GeekBrain infrastructure Q&A.

## 📋 Project Structure

```
W4/
├── src/
│   ├── __init__.py              # Package init
│   ├── config.py                # Configuration (AWS, DB, API endpoints)
│   ├── logger.py                # Logging setup
│   ├── knowledge_base.py        # KB loader (L1-L2)
│   ├── rag_pipeline.py          # Retrieval pipeline (L1-L2)
│   ├── tools.py                 # Database and API tools (L3)
│   ├── agent.py                 # Agent orchestration (L3-L4)
│   └── main.py                  # CLI entry point
├── tests/
│   └── test_all.py              # Comprehensive test suite (L1-L4)
├── data_package/                # Pre-loaded data (36 docs, 4 CSVs)
│   ├── knowledge_base/          # 36 markdown documents
│   ├── structured_data/         # monthly_costs.csv, incidents.csv, etc.
│   └── scripts/
│       ├── seed_data.py         # Load CSV → SQLite
│       ├── monitoring_api.py    # Live API endpoints
│       └── pyproject.toml
├── plan/
│   └── W4_IMPLEMENTATION_PLAN.md # Detailed execution plan
├── logs/                        # Runtime logs
├── docs/
│   ├── README.md                # This file
│   └── W4_evidence.md           # Evidence pack (for trainers)
├── requirements.txt             # Python dependencies
├── setup.py                     # Setup assistant
└── .env.example                 # Environment template

```

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
cd d:\Xbrain\RAG\W4
pip install -r requirements.txt
```

### Step 2: Seed the Database

```bash
cd data_package/scripts
python seed_data.py --db-type sqlite
```

This creates `data_package/geekbrain.db` with 4 tables:
- `monthly_costs` — 36 rows (6 services × 6 months)
- `incidents` — 8 incidents with details
- `sla_targets` — 18 SLA records
- `daily_metrics` — 540 rows of daily metrics

### Step 3: Start the Monitoring API

```bash
cd data_package/scripts
uvicorn monitoring_api:app --reload --port 8000
```

Visit `http://localhost:8000/docs` to see all endpoints.

### Step 4: Run Tests (Current Mode: Mock LLM)

```bash
python tests/test_all.py
```

This runs 19 tests across L1-L4 levels without needing AWS.

### Step 5: Try Interactive Mode

```bash
python src/main.py
```

Ask questions like:
- "Who is the Team Platform lead?"
- "What was PaymentGW's Q1 cost?"
- "Is PaymentGW within its SLA?"

## 🔐 AWS Setup (When Ready - Optional for Testing)

When you have AWS credentials:

### Option A: Environment Variables (Per-Session)

```powershell
$env:AWS_ACCESS_KEY_ID = "your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-access-key"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

### Option B: .env File (Persistent)

Create `.env` in project root:

```
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_KB_ID=kb-xxxxx
S3_BUCKET=geekbrain-kb-us-east-1
MODE=cloud
```

### Option C: AWS CLI Config (System-Wide)

```bash
aws configure
```

Then restart Python to pick up credentials.

## 🏗️ Architecture

### Mode Levels

The system operates in different modes based on AWS availability:

| Mode | AWS Credentials | Bedrock KB | Local KB | API | Use Case |
|------|---|---|---|---|---|
| **mock** | ❌ | ❌ | ✅ (mock retrieval) | Local | Development/testing |
| **local** | ✅ (optional) | ❌ | ✅ (real retrieval) | Real | Local development |
| **cloud** | ✅ | ✅ | ❌ | Real | Production |

### Processing Levels

```
Question Input
    ↓
L1 (Simple RAG)
  - Retrieve from KB
  - LLM generation
  - Source citation
    ↓ (if complex)
L2 (Multi-Source RAG)
  - Retrieve more docs
  - Conflict detection
  - Smart synthesis
    ↓ (if data-driven)
L3 (Tool-Augmented RAG)
  - Tool selection
  - Database queries
  - API calls
  - Data aggregation
    ↓ (if multi-turn)
L4 (Memory-Aware)
  - Conversation context
  - Entity extraction
  - Pronoun resolution
```

## 📊 Testing

### Run All Tests

```bash
python tests/test_all.py
```

Output shows:
- ✅/❌ status per test
- Answer snippets
- Sources cited
- Summary statistics

### Example Test Output

```
L1 TESTS: Simple Retrieval
========================================

✅ PASS [l1] Team Lead Query
  Question: Who is the Team Platform lead?
  Answer: Alex Chen is the Team Platform lead...
  Sources: team_platform.md

✅ PASS [l1] SLA Query
  Question: What is GeekBrain's SLA for latency?
  Answer: The latency SLA is 200ms p99...

...

📊 L1 Summary: 5/5 passed
```

### Individual Test Files

- `test_all.py` — Complete test suite (L1-L4)
- L1-L4 test cases are defined as lists of (name, question, expected_keyword)

## 💻 CLI Usage

### Interactive Mode

```bash
python src/main.py
```

Commands:
- `exit` — Quit
- `clear` — Clear memory
- `help` — Show help
- `entities` — Show extracted entities
- `memory` — Show conversation history

### Single Question

```bash
python src/main.py "Who leads Team Platform?"
python src/main.py "What was PaymentGW cost?" --level l3
```

### Batch Processing

Create `questions.txt`:
```
Who is the Team Platform lead?
What was PaymentGW's Q1 cost?
Is PaymentGW within its SLA?
```

Run:
```bash
python src/main.py --batch questions.txt --verbose
```

### Verbose Output

```bash
python src/main.py "Your question?" --verbose
```

Shows:
- Tool results
- Metadata (duration, chunks retrieved)
- Reasoning steps

## 🔧 Configuration

Edit `src/config.py` to customize:

```python
# LLM
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 1000

# Retrieval
RETRIEVAL_K = 10              # Number of chunks to retrieve
HYBRID_SEARCH = True          # BM25 + vector search

# Memory (L4)
MEMORY_MAX_TURNS = 5          # Keep last 5 turns

# Logging
LOG_LEVEL = "INFO"
LOG_JSON = False              # JSON or text format

# Mode
MODE = "auto"                 # mock, local, cloud, auto
```

## 🧠 How Each Level Works

### L1: Simple Retrieval

1. Load markdown documents from `knowledge_base/`
2. Keyword search (TF-IDF approximation)
3. Retrieve top-K chunks
4. Send to LLM with system prompt
5. Return answer + source citation

**Example:**
```
Q: Who is the Team Platform lead?
→ Search KB for "Team Platform"
→ Find team_platform.md
→ Retrieve chunk: "Lead: Alex Chen"
→ LLM generates answer with citation
A: Alex Chen (from team_platform.md)
```

### L2: Multi-Source Retrieval

1. Retrieve MORE chunks (K×2)
2. Detect conflicts (v1 vs v2, archived, etc.)
3. Annotate document status
4. Enhanced system prompt for conflict resolution
5. LLM chooses best source

**Example:**
```
Q: What is the API rate limit?
→ Retrieve: api_reference_v1_archived.md (500/sec) + api_reference_v2.md (1000/sec)
→ System prompt: prefer newer versions
→ LLM identifies v2 as current
A: 1000 requests per second (from api_reference_v2.md, updated from v1)
```

### L3: Tool-Augmented RAG

1. Analyze question for tool requirement
2. Select appropriate tools (database, API, KB)
3. Execute tools in parallel
4. Aggregate results
5. Synthesize into answer with reasoning

**Tools:**
- `database_query` — Execute SQL (costs, incidents, metrics history)
- `get_metrics` — Call monitoring API (current latency, errors)
- `get_status` — Service health status
- `get_incidents` — Incident history

**Example:**
```
Q: Is PaymentGW's current latency within SLA?
→ Tool 1: database_query("SELECT target FROM sla_targets WHERE service='PaymentGW' AND metric='latency_p99_ms'") → 200ms
→ Tool 2: get_metrics("PaymentGW") → current p99 = 185ms
→ Compare: 185ms < 200ms → YES
A: Yes, PaymentGW's latency (185ms) is within SLA target (200ms)
```

### L4: Multi-Turn Memory

1. Store question and answer in memory
2. Extract named entities (service, team, date)
3. On next turn, include conversation context
4. Resolve pronouns using entity history
5. Continue conversation naturally

**Example:**
```
Turn 1: Q: Which service had highest cost in March?
        A: PaymentGW at $7,500
        Memory: {service: PaymentGW, month: March}

Turn 2: Q: What caused that spike?
        A: [System recognizes "that" → PaymentGW from Turn 1]
           Database migration overhead based on incident postmortem
        Memory: {service: PaymentGW, cause: migration}

Turn 3: Q: Which team owns it?
        A: [System recognizes "it" → PaymentGW]
           Team Platform leads PaymentGW
```

## 🗄️ Database Schema

Automatically created by `seed_data.py`:

### monthly_costs
```sql
service (TEXT)      — "PaymentGW", "OrderSvc", etc.
month (TEXT)        — "2026-01", "2026-02", etc.
compute_cost (REAL)
storage_cost (REAL)
network_cost (REAL)
third_party_cost (REAL)
total_cost (REAL)
```

### incidents
```sql
incident_id (TEXT)     — "INC-001", etc.
service (TEXT)
date (TEXT)            — "2026-03-05"
severity (TEXT)        — "P1", "P2", "P3"
duration_minutes (INT)
root_cause (TEXT)
resolution (TEXT)
team_responsible (TEXT)
reported_by (TEXT)
```

### sla_targets
```sql
service (TEXT)
metric (TEXT)          — "availability", "latency_p99_ms", "error_rate_percent"
target (REAL)
measurement_window (TEXT) — "monthly", "rolling_5min"
```

### daily_metrics
```sql
date (TEXT)                — "2026-01-01"
service (TEXT)
latency_p99_ms (REAL)
error_rate_percent (REAL)
requests_per_minute (INT)
availability_percent (REAL)
```

## 📡 Monitoring API Endpoints

Start with: `uvicorn monitoring_api:app --port 8000`

### Get All Services
```
GET /services
→ ["PaymentGW", "OrderSvc", "AuthSvc", "NotificationSvc", "ReportingSvc", "FraudDetector"]
```

### Get Service Metrics
```
GET /metrics/{service_name}
→ {
  "service": "PaymentGW",
  "latency_ms": {"p50": 45, "p95": 120, "p99": 185},
  "error_rate_percent": 0.08,
  "requests_per_minute": 12500,
  "cpu_utilization_percent": 62,
  "memory_utilization_percent": 71
}
```

### Get Service Status
```
GET /status/{service_name}
→ {
  "service": "PaymentGW",
  "status": "healthy",
  "uptime_percent_24h": 99.98,
  "uptime_percent_7d": 99.91,
  "uptime_percent_30d": 99.87,
  "last_incident": "2026-03-05",
  "active_alerts": []
}
```

### Get Incidents
```
GET /incidents
→ [incident records...]

GET /incidents/{service_name}
→ [incidents for service...]
```

## 🔍 Troubleshooting

### "Database file not found"

```bash
cd data_package/scripts
python seed_data.py --db-type sqlite
```

### "Monitoring API not reachable"

```bash
cd data_package/scripts
uvicorn monitoring_api:app --reload --port 8000
```

### "AWS credentials not found"

Set environment variables or create `.env` file (see AWS Setup section above).

### "MockLLM is being used, not real LLM"

This is normal! The system falls back to MockLLM when:
- AWS credentials are not set
- Bedrock KB is not configured
- MODE is set to "mock"

To use real Bedrock, set AWS credentials and MODE=cloud.

### "No chunks retrieved"

1. Check knowledge base loaded: `ls data_package/knowledge_base/`
2. Test retrieval: Check logs for retrieval errors
3. Try simpler question with more obvious keywords

## 📈 Performance Tips

1. **Increase RETRIEVAL_K** for complex questions needing multiple sources
2. **Use HYBRID_SEARCH = True** to catch keyword misses
3. **Filter by metadata** (exclude archived docs) to reduce noise
4. **Cache frequently accessed docs** in memory
5. **Batch process questions** with `--batch` for efficiency

## 🎯 Next Steps for Production

1. **Setup AWS:** Create S3 bucket, Bedrock KB, OpenSearch collection
2. **Enable real LLM:** Set AWS credentials and MODE=cloud
3. **Add observability dashboard:** Bonus A from W4_project_announcement.md
4. **Implement KB auto-sync:** Bonus C (S3 → Lambda → Bedrock)
5. **Add agent reasoning:** Bonus B (multi-step investigation)
6. **Production hardening:**
   - Error handling and retries
   - Rate limiting
   - Caching layer
   - Authentication
   - Request/response validation

## 📝 Documentation

- [W4 Implementation Plan](plan/W4_IMPLEMENTATION_PLAN.md) — Detailed architecture and roadmap
- [W4 Project Announcement](../W4_project_announcement.md) — Full project spec
- [Evidence Pack Template](docs/W4_evidence.md) — For Friday grading

## 🙋 Questions?

Check the logs:
```bash
cat logs/geekbrain.log
```

Or run with verbose output:
```bash
python src/main.py "Your question?" --verbose
```

---

**Ready to start?** Run `python setup.py` for a guided setup assistant.
