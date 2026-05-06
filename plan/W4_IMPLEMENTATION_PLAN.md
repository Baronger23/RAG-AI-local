# W4: Build an AI That Actually Answers — Implementation Plan

**Project:** GeekBrain Q&A System  
**Duration:** May 3-8, 2026 (5 days)  
**Target Score:** 10/10 (Base) + 1/1 (Bonus)  
**Status:** Plan v1.0 — Ready for execution

---

## Executive Summary

Build a progressive RAG + Tool-Augmented AI system that answers questions about GeekBrain in four cumulative levels:

| Level | Capability | Target |
|-------|-----------|--------|
| **L1** | Single-document retrieval (Simple RAG) | 2 points |
| **L2** | Multi-source synthesis + conflict resolution | 3 points |
| **L3** | Retrieval + Database + Real-time API tools | 4 points |
| **L4** | Multi-turn memory + context preservation | 1 point |
| **Bonus** | Observability Dashboard OR Agent Reasoning OR KB Sync | +0.5-1.0 |

**Base Score Path:** L1 (2) + L2 (3) + L3 (4) + L4 (1) = **10 points guaranteed** if all levels work reliably.

---

## Technology Stack

### Core Components

| Component | Choice | Why |
|-----------|--------|-----|
| **LLM** | Claude 3.5 Sonnet via AWS Bedrock | Reliable, fast, excellent reasoning for tool routing |
| **Embedding Model** | Amazon Titan Embeddings v2 | Native Bedrock integration, no extra API calls |
| **Vector Store & Retrieval** | Bedrock Knowledge Bases + Hybrid Search | AWS-managed, handles chunking/syncing automatically |
| **Framework** | LangChain (Python) | Best tool orchestration, clear control flow, mature |
| **Database** | SQLite (Dev) → PostgreSQL (Optional) | seed_data.py pre-built for SQLite; PostgreSQL ready if needed |
| **API Framework** | FastAPI | Fast, Starlette-based, good for local testing |
| **Observability** | CloudWatch Logs + Local Logging | Bedrock logs in CloudWatch, custom JSON logs in code |

### Development Environment

```
Project Root: d:\Xbrain\RAG\W4\
├── data_package/          # Provided data
│   ├── docs/              # 36 knowledge base markdown files
│   ├── csv/               # Structured data
│   └── scripts/           # seed_data.py, monitoring_api.py
├── src/                   # Our codebase (to create)
│   ├── config.py          # AWS, LLM, database settings
│   ├── rag_pipeline.py    # L1-L2: Retrieval logic
│   ├── tools.py           # L3: Tool definitions (DB, API, metrics)
│   ├── agent.py           # L3: Tool routing via LangChain
│   ├── memory.py          # L4: Conversation context management
│   └── main.py            # Entry point / CLI / UI
├── tests/
│   ├── test_l1.py         # L1 test questions
│   ├── test_l2.py         # L2 test questions
│   ├── test_l3.py         # L3 test questions
│   └── test_l4.py         # L4 test questions
├── docs/
│   └── W4_evidence.md     # CRITICAL: Evidence Pack for grading
├── logs/                  # Local logs for debugging
└── plan/
    └── W4_IMPLEMENTATION_PLAN.md  # This file
```

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                               │
│                    (Question / Turn)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │     Memory Manager (L4)         │
        │ (Conversation history lookup)   │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────────────────────────────┐
        │           Question Router                               │
        │  (Determine: RAG-only vs Tool-augmented)                │
        └────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │    L1-L2: Bedrock KB            │
        │    (Retrieve chunks)            │
        │    - Vector Search              │
        │    - Hybrid (BM25 + semantic)   │
        │    - Metadata filtering         │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────────────────────────────┐
        │           Tool Routing (L3)                             │
        │  Does question need tools?                              │
        │  - NO → Send chunks to LLM (L1-L2 path)                │
        │  - YES → Plan tools, execute, aggregate                │
        └────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │    Tools Execution (L3)         │
        ├─────────────────────────────────┤
        │ • Database Query Tool           │
        │   (Cost, SLA, incidents data)   │
        ├─────────────────────────────────┤
        │ • Service Metrics Tool          │
        │   (Current latency, error rate) │
        ├─────────────────────────────────┤
        │ • Incident History Tool         │
        │ • Team Info Tool                │
        ├─────────────────────────────────┤
        │ ┌─────────────┐  ┌────────────┐ │
        │ │   SQLite    │  │ Monitoring │ │
        │ │   Database  │  │    API     │ │
        │ └─────────────┘  └────────────┘ │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────────────────────────────┐
        │      LLM Processing (Claude Sonnet)                     │
        │  Input:                                                 │
        │  - System prompt (context, tone, conflict resolution)   │
        │  - Retrieved chunks (L1-L2)                             │
        │  - Tool results (L3)                                    │
        │  - Conversation history (L4)                            │
        │                                                         │
        │  Output:                                                │
        │  - Final answer                                         │
        │  - Source citations (L1-L2)                             │
        │  - Reasoning trace (L3+)                                │
        └────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────────────────────────────┐
        │         Response Formatter                              │
        │  - Cite sources (L1-L2)                                 │
        │  - Include tool traces (L3)                             │
        │  - Store in memory (L4)                                 │
        │  - Log for observability                                │
        └────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │      USER OUTPUT                │
        │   (Answer + Reasoning)          │
        └────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Setup & Data Exploration (Tuesday, May 3)

**Goal:** Understand the data, verify all components work in isolation.

**Tasks:**

1. **Knowledge Base Exploration (1 hour)**
   - [ ] Read all 36 markdown documents
   - [ ] Create a mapping: which docs cover the same topics?
   - [ ] Identify conflicts (e.g., API rate limits, team structure changes)
   - [ ] Extract key facts for manual Q&A testing

2. **Data Layer Setup (1.5 hours)**
   - [ ] Navigate to `data_package/scripts/`
   - [ ] Run `seed_data.py`:
     ```bash
     cd data_package/scripts
     python seed_data.py --db-type sqlite
     ```
   - [ ] Verify SQLite database created at `data_package/geekbrain.db`
   - [ ] Test queries:
     ```sql
     SELECT * FROM monthly_costs WHERE service_name = 'PaymentGW' AND month = '2026-03';
     -- Expected: $7,500
     
     SELECT * FROM sla_targets WHERE service_name = 'PaymentGW';
     -- Expected: latency_p99_ms = 200
     ```

3. **Monitoring API Exploration (1 hour)**
   - [ ] Start the API:
     ```bash
     cd data_package/scripts
     uvicorn monitoring_api:app --port 8000
     ```
   - [ ] Hit each endpoint with curl/Postman and document responses:
     - `GET /services` — all available services
     - `GET /metrics/{service_name}` — current latency, error rate, RPS
     - `GET /status/{service_name}` — health status
     - `GET /incident/{service_name}` — recent incidents
   - [ ] Note: **Data ONLY from API = current latency, real-time status**. This is L3 material.

4. **AWS Bedrock Verification (1 hour)**
   - [ ] Confirm AWS CLI configured: `aws sts get-caller-identity`
   - [ ] Verify Bedrock model access: `aws bedrock list-foundation-models`
   - [ ] Test a simple Bedrock API call (no KB yet):
     ```python
     import boto3
     client = boto3.client('bedrock-runtime', region_name='us-east-1')
     response = client.invoke_model(
         modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
         body=json.dumps({"prompt": "Say hello"}),
     )
     print(response['body'].read())
     ```
   - [ ] Confirm S3 bucket exists for KB documents

5. **Deliverable:** `docs/data_exploration.md` with:
   - List of all 36 docs and their main topics
   - Identified conflicts (with line numbers)
   - Sample query results from database
   - API endpoint catalog + example responses

---

### Phase 2: L1 & L2 Implementation (Wednesday-Thursday, May 4-5)

**Goal:** Achieve reliable single-doc and multi-doc retrieval with conflict resolution.

#### L1: Simple Retrieval (Target: Wed evening)

**Architecture Decision:**
- Use **Bedrock KB + Retrieve API + Custom Prompt** (hybrid approach)
- Why: AWS handles chunking/indexing (fast), we control retrieval & prompting (quality)

**Steps:**

1. **Upload Documents to S3 (1 hour)**
   ```bash
   # Create S3 bucket if not exists
   aws s3 mb s3://geekbrain-kb-{your-region}
   
   # Upload all markdown files
   aws s3 sync data_package/docs/ s3://geekbrain-kb-{your-region}/docs/
   
   # Verify upload
   aws s3 ls s3://geekbrain-kb-{your-region}/docs/ | wc -l
   # Should show ~36 files
   ```

2. **Create Bedrock Knowledge Base (1 hour)**
   ```python
   # src/setup_kb.py
   import boto3
   import json
   
   bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
   
   # Create KB
   response = bedrock_agent.create_knowledge_base(
       name='GeekBrain-KB',
       description='Knowledge base for GeekBrain services',
       roleArn='arn:aws:iam::YOUR_ACCOUNT:role/YOUR_BEDROCK_ROLE',
       knowledgeBaseConfiguration={
           'type': 'VECTOR',
           'vectorKnowledgeBaseConfiguration': {
               'embeddingModel': {
                   'provider': 'BEDROCK',
                   'modelIdentifier': 'amazon.titan-embed-text-v2:0'
               }
           }
       },
       storageConfiguration={
           'type': 'OPENSEARCH_SERVERLESS',
           'opensearchServerlessConfiguration': {
               'collectionArn': 'arn:aws:aoss:us-east-1:YOUR_ACCOUNT:collection/...'
           }
       }
   )
   
   kb_id = response['knowledgeBase']['id']
   print(f"KB Created: {kb_id}")
   ```

3. **Sync Data Source (1-2 hours)**
   ```python
   # Attach S3 data source to KB
   response = bedrock_agent.create_data_source(
       knowledgeBaseId=kb_id,
       name='GeekBrain-Docs',
       description='Markdown documents about GeekBrain services',
       dataSourceConfiguration={
           'type': 'S3',
           's3Configuration': {
               'bucketArn': 'arn:aws:s3:::geekbrain-kb-{region}',
               'inclusionPatterns': ['*.md']
           }
       }
   )
   
   # Start ingestion
   data_source_id = response['dataSource']['id']
   bedrock_agent.start_ingestion_job(
       dataSourceId=data_source_id,
       knowledgeBaseId=kb_id
   )
   ```
   - **Wait for ingestion to complete** (check status every 30s)

4. **Build L1 RAG Pipeline (2 hours)**
   ```python
   # src/rag_pipeline.py
   import boto3
   import json
   from typing import List, Dict
   
   class L1Retriever:
       def __init__(self, kb_id: str):
           self.kb_id = kb_id
           self.bedrock_agent = boto3.client('bedrock-agent-runtime')
           self.bedrock_llm = boto3.client('bedrock-runtime')
       
       def retrieve_chunks(self, query: str, top_k: int = 5) -> List[Dict]:
           """Retrieve relevant chunks from KB"""
           response = self.bedrock_agent.retrieve(
               knowledgeBaseId=self.kb_id,
               retrievalQuery=query,
               retrievalConfiguration={
                   'vectorSearchConfiguration': {
                       'numberOfResults': top_k,
                       'overrideSearchType': 'HYBRID'  # Vector + BM25
                   }
               }
           )
           
           return response['retrievalResults']
       
       def answer_question(self, question: str) -> Dict:
           """L1 pipeline: Retrieve → Augment → Generate"""
           chunks = self.retrieve_chunks(question)
           
           # Format context
           context = "\n\n".join([
               f"[Source: {chunk['metadata']['source']}]\n{chunk['content']}"
               for chunk in chunks
           ])
           
           # Build prompt
           system_prompt = """You are a helpful assistant answering questions about GeekBrain.
           Rules:
           - Answer ONLY using the provided context
           - Always cite the source document
           - If you don't know, say so
           """
           
           user_prompt = f"""Question: {question}
           
   Context:
   {context}
   
   Provide a clear answer citing the source document."""
           
           # Call LLM
           response = self.bedrock_llm.invoke_model(
               modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
               body=json.dumps({
                   'anthropic_version': 'bedrock-2023-06-01',
                   'max_tokens': 500,
                   'system': system_prompt,
                   'messages': [{
                       'role': 'user',
                       'content': user_prompt
                   }]
               })
           )
           
           answer = json.loads(response['body'].read())['content'][0]['text']
           
           return {
               'answer': answer,
               'sources': [chunk['metadata']['source'] for chunk in chunks],
               'chunks_retrieved': len(chunks)
           }
   ```

5. **Test L1 (30 mins)**
   - Test questions (from knowledge base):
     - ✓ "Who is the Team Platform lead?" → "Alex Chen" (from team_platform.md)
     - ✓ "What is GeekBrain's API rate limit for PaymentGW?" → "1000 req/sec" (from api_policy.md)
     - ✓ "Describe the OrderSvc architecture" → (from service docs)
   
   **Pass Criteria:**
   - ✓ Answer is factually correct
   - ✓ Source document is cited
   - ✓ System works end-to-end without errors

---

#### L2: Multi-Source Retrieval (Target: Thu morning)

**Key Insight:** L2 is mostly about improving L1 through **smarter retrieval** and **better prompting**. The architecture doesn't change much.

**What changes:**

1. **Increase Retrieval K (30 mins)**
   ```python
   # In L1Retriever.retrieve_chunks()
   numberOfResults=10  # Changed from 5
   overrideSearchType='HYBRID'  # Ensures BM25 + Vector hybrid search
   ```

2. **Improve System Prompt for Conflict Resolution (1 hour)**
   ```python
   system_prompt = """You are a helpful assistant answering questions about GeekBrain.
   
   When you receive multiple documents:
   1. Check document dates and version numbers
   2. Prefer the MOST RECENT version unless explicitly told otherwise
   3. If sources conflict, explain the conflict and state which you trust
   4. Example: "API v1 specifies 500 req/sec, but API v2 (updated 2026-04-15) specifies 1000. I'm citing v2 as current."
   
   Rules:
   - Answer ONLY using provided context
   - Always cite sources
   - When documents conflict, explain the resolution
   - If uncertain, say so
   """
   ```

3. **Add Metadata Filtering (1 hour)**
   ```python
   def retrieve_chunks(self, query: str, top_k: int = 10, 
                       exclude_archived: bool = True) -> List[Dict]:
       """Retrieve with metadata filtering"""
       response = self.bedrock_agent.retrieve(
           knowledgeBaseId=self.kb_id,
           retrievalQuery=query,
           retrievalConfiguration={
               'vectorSearchConfiguration': {
                   'numberOfResults': top_k,
                   'overrideSearchType': 'HYBRID',
                   'filter': {  # NEW: filter out archived docs
                       'not': {
                           'key': 'metadata.status',
                           'value': 'archived'
                       }
                   } if exclude_archived else None
               }
           }
       )
   ```

4. **Test L2 (1 hour)**
   - Conflict resolution test:
     - ✓ "What is PaymentGW API rate limit?" 
       - System retrieves both v1 (500) and v2 (1000)
       - Identifies v2 as newer
       - Answers "1000 (current version)" with citation
   
   - Multi-doc test:
     - ✓ "Can Team Commerce deploy a fix on Friday night?"
       - Retrieves: deployment_policy.md, incident_response_policy.md, team_commerce.md
       - Synthesizes: "Yes, if it meets P1 criteria (see policy) and team has on-call approval (see team)"
   
   **Pass Criteria:**
   - ✓ Conflict correctly identified and resolved
   - ✓ Multiple sources synthesized
   - ✓ Source citations clear

---

### Phase 3: L3 Implementation (Thursday afternoon, May 5)

**Goal:** Add tool execution for data-driven questions.

**Key Questions L3 Must Answer:**
- "What was PaymentGW's total cost in Q1 2026?" → DB query → $7,500 + $8,200 + $8,100 = $23,800
- "Is PaymentGW's current latency better than Q1 average?" → API call + DB query → Compare
- "How many incidents did OrderSvc have in Q1?" → DB query → incident count

#### Architecture Decision

Use **LangChain with Bedrock + Tool Definitions**:
- Why: Clear tool routing, explicit function calling, good for logging/debugging
- LangChain handles: Tool selection, execution loop, result parsing
- We write: Tool functions, system prompt, tool descriptions

#### L3 Implementation Steps

1. **Define Tool Functions (1.5 hours)**
   ```python
   # src/tools.py
   import sqlite3
   import json
   import requests
   from typing import Dict, List, Any
   
   class DataTools:
       def __init__(self, db_path: str = 'data_package/geekbrain.db', 
                    api_base: str = 'http://localhost:8000'):
           self.db_path = db_path
           self.api_base = api_base
       
       def database_query(self, query: str) -> Dict[str, Any]:
           """
           Execute a SQL query against GeekBrain database.
           Returns structured results with row count.
           
           Use for: historical data, costs, SLAs, incidents, metrics trends
           Example: SELECT SUM(cost) FROM monthly_costs WHERE month LIKE '2026-01%'
           """
           try:
               conn = sqlite3.connect(self.db_path)
               conn.row_factory = sqlite3.Row
               cursor = conn.cursor()
               cursor.execute(query)
               rows = cursor.fetchall()
               conn.close()
               
               return {
                   'status': 'success',
                   'row_count': len(rows),
                   'data': [dict(row) for row in rows]
               }
           except Exception as e:
               return {
                   'status': 'error',
                   'error': str(e)
               }
       
       def service_metrics(self, service_name: str) -> Dict[str, Any]:
           """
           Get current live metrics for a service.
           Returns: latency_p50, latency_p99, error_rate, requests_per_min, uptime_pct
           
           Use for: real-time health checks, current performance
           Example: ServiceMetrics for PaymentGW → latency_p99=185ms (vs SLA 200ms)
           """
           try:
               response = requests.get(
                   f'{self.api_base}/metrics/{service_name}',
                   timeout=5
               )
               return response.json()
           except Exception as e:
               return {'status': 'error', 'error': str(e)}
       
       def service_status(self, service_name: str) -> Dict[str, Any]:
           """
           Get health status of a service.
           Returns: status (healthy/degraded/down), incident_count_24h, last_deployment
           """
           try:
               response = requests.get(
                   f'{self.api_base}/status/{service_name}',
                   timeout=5
               )
               return response.json()
           except Exception as e:
               return {'status': 'error', 'error': str(e)}
       
       def incident_history(self, service_name: str, limit: int = 10) -> Dict[str, Any]:
           """
           Get recent incidents for a service.
           Returns: incident_id, severity, duration_mins, root_cause, resolution, date
           """
           query = f"""
               SELECT * FROM incidents 
               WHERE service_name = '{service_name}'
               ORDER BY date DESC
               LIMIT {limit}
           """
           return self.database_query(query)
       
       def team_info(self, team_name: str) -> Dict[str, Any]:
           """
           Get team details from knowledge base (via DB or doc retrieval).
           Returns: team_lead, members, services_owned, on_call_schedule
           """
           # For now, returns best-effort from docs via RAG
           # Implementation: RAG query + parse results
           pass
   ```

2. **Register Tools with LangChain (1 hour)**
   ```python
   # src/agent.py
   from langchain.tools import Tool, StructuredTool
   from langchain.agents import AgentExecutor, create_tool_calling_agent
   from langchain_community.chat_models import BedrockChat
   from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
   from tools import DataTools
   
   class L3Agent:
       def __init__(self, kb_retriever, tools_instance: DataTools):
           self.retriever = kb_retriever
           self.tools_instance = tools_instance
           self.llm = BedrockChat(
               model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'
           )
           self.tools = self._create_tools()
       
       def _create_tools(self) -> List[Tool]:
           """Define tools for agent"""
           return [
               StructuredTool.from_function(
                   func=self.tools_instance.database_query,
                   name='database_query',
                   description='Execute SQL query against GeekBrain database. Use for costs, SLAs, incident history, metric trends.',
                   args_schema={...}  # JSON schema for parameters
               ),
               StructuredTool.from_function(
                   func=self.tools_instance.service_metrics,
                   name='service_metrics',
                   description='Get current live metrics (latency, error rate, RPS) for a service.',
                   args_schema={...}
               ),
               StructuredTool.from_function(
                   func=self.tools_instance.service_status,
                   name='service_status',
                   description='Get current health status of a service.',
                   args_schema={...}
               ),
               StructuredTool.from_function(
                   func=self.tools_instance.incident_history,
                   name='incident_history',
                   description='Get recent incidents for a service.',
                   args_schema={...}
               ),
           ]
       
       def process_query(self, question: str) -> Dict:
           """Process question through tool-augmented RAG"""
           
           # Step 1: Retrieve relevant docs (L1-L2 foundation)
           retrieval_results = self.retriever.retrieve_chunks(question, top_k=10)
           context = "\n\n".join([
               f"[{r['metadata']['source']}]\n{r['content']}"
               for r in retrieval_results
           ])
           
           # Step 2: Create prompt
           system_prompt = """You are an expert analyzing GeekBrain infrastructure.
           
   You have access to:
   - Knowledge base (documents about company policies, team structure, architecture)
   - Database (historical costs, incidents, SLAs, metrics)
   - Monitoring API (current service status and metrics)
   
   Strategy:
   1. If question asks for CURRENT data (now, today, live), use service_metrics or service_status
   2. If question asks for HISTORICAL data (Q1, March, past 30 days), use database_query
   3. If question asks about POLICY or STRUCTURE, use knowledge base context
   4. For COMPARISONS, gather data from both sources
   
   Always:
   - Call tools to ground answers in real data
   - Cite sources (document names, query results, API responses)
   - Show reasoning ("PaymentGW Q1 total = $7500+$8200+$8100 = $23800")
   - Flag uncertainties
           """
           
           prompt = ChatPromptTemplate.from_messages([
               ('system', system_prompt),
               ('user', f"""Question: {question}
   
   Knowledge base context:
   {context}
   
   Use tools to gather data. Show your work."""),
               MessagesPlaceholder(variable_name='agent_scratchpad')
           ])
           
           # Step 3: Create agent
           agent = create_tool_calling_agent(self.llm, self.tools, prompt)
           executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
           
           # Step 4: Execute
           result = executor.invoke({'input': question})
           
           return {
               'answer': result['output'],
               'kb_sources': [r['metadata']['source'] for r in retrieval_results],
               'tools_called': result.get('tool_calls', []),
               'reasoning': result.get('intermediate_steps', [])
           }
   ```

3. **Test Tool Routing (1.5 hours)**
   
   - **Test 1: Database Query Tool**
     ```
     Q: "What was PaymentGW's total infrastructure cost in Q1 2026?"
     Expected tool call: database_query("SELECT SUM(cost) FROM monthly_costs WHERE service_name='PaymentGW' AND month BETWEEN '2026-01' AND '2026-03'")
     Expected answer: $23,800
     Log check: ✓ Tool called ✓ Query executed ✓ Result returned
     ```
   
   - **Test 2: Service Metrics Tool**
     ```
     Q: "What is PaymentGW's current p99 latency?"
     Expected tool call: service_metrics("PaymentGW")
     Expected answer: ~185ms (from API)
     Log check: ✓ API called ✓ Response parsed ✓ Compared to SLA (200ms)
     ```
   
   - **Test 3: Multi-Tool Orchestration**
     ```
     Q: "Is PaymentGW's latency right now better or worse than Q1 average?"
     Expected tool calls:
       1. service_metrics("PaymentGW") → current = 185ms
       2. database_query("SELECT AVG(latency_p99) FROM daily_metrics WHERE service='PaymentGW' AND month BETWEEN '2026-01' AND '2026-03'") → Q1 avg = 195ms
     Expected answer: "Current (185ms) is better than Q1 average (195ms)"
     Log check: ✓ Both tools called ✓ Results synthesized ✓ Comparison made
     ```

   **Pass Criteria:**
   - ✓ Tools called for appropriate questions
   - ✓ Queries syntactically correct
   - ✓ Numerical answers are accurate
   - ✓ Reasoning shown in output

---

### Phase 4: L4 Implementation (Friday morning, May 6)

**Goal:** Add multi-turn memory for conversation context.

**Key Challenge:** Without memory, Turn 2 doesn't know what "its" service is from Turn 1.

#### L4 Strategy

Simple but effective: **Rolling Conversation Context**

```python
# src/memory.py
from collections import deque
from typing import List, Dict

class ConversationMemory:
    def __init__(self, max_turns: int = 5):
        """Keep last N turns for context"""
        self.turns = deque(maxlen=max_turns)
    
    def add_turn(self, question: str, answer: str, entities: Dict = None):
        """Store a Q&A pair with extracted entities"""
        self.turns.append({
            'question': question,
            'answer': answer,
            'entities': entities or {}  # {service: 'PaymentGW', team: 'Payments', etc}
        })
    
    def get_context(self) -> str:
        """Return conversation history as string for LLM"""
        if not self.turns:
            return ""
        
        history = "Previous conversation:\n"
        for i, turn in enumerate(self.turns, 1):
            history += f"\nTurn {i}:\n"
            history += f"Q: {turn['question']}\n"
            history += f"A: {turn['answer'][:200]}...\n"  # Truncate for brevity
        
        return history
    
    def extract_entities(self, answer: str) -> Dict:
        """Extract key entities (service names, teams, dates) from answer"""
        # Simple pattern matching for now
        entities = {}
        
        services = ['PaymentGW', 'OrderSvc', 'NotificationSvc', ...]  # from docs
        for service in services:
            if service.lower() in answer.lower():
                entities['service'] = service
        
        return entities
```

**Integrate into agent:**

```python
# Modified src/agent.py
class L3Agent:
    def __init__(self, kb_retriever, tools_instance: DataTools, 
                 memory: ConversationMemory = None):
        # ... existing init ...
        self.memory = memory or ConversationMemory()
    
    def process_query(self, question: str) -> Dict:
        """L4: Include memory in context"""
        
        # Get conversation context
        conv_context = self.memory.get_context()
        
        # Build enhanced prompt
        system_prompt = """You are an expert analyzing GeekBrain infrastructure.
        
        IMPORTANT: Reference the previous conversation if available.
        When a user says 'that service', 'their team', 'the same issue', etc.,
        resolve it to the actual entity from earlier turns.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt),
            ('user', f"""{conv_context}

Current question: {question}

If this question references something from earlier, explain what you're referring to.
"""),
            MessagesPlaceholder(variable_name='agent_scratchpad')
        ])
        
        # ... execute agent ...
        
        # Store turn in memory
        self.memory.add_turn(
            question=question,
            answer=result['output'],
            entities=self._extract_entities(result['output'])
        )
        
        return result
```

**Test L4:**

```
Turn 1: "Which service had the highest infrastructure cost in March 2026?"
System: "PaymentGW at $8,100. [retrieves from DB]"

Turn 2: "What was the main cause of the cost increase that month?"
System: 
  - Recognizes "cost increase" = PaymentGW March spike
  - Queries incidents for PaymentGW in March
  - Finds root cause from postmortem
  - Answer: "[From previous turn] PaymentGW's spike was due to..."

Turn 3: "Which team is responsible?"
System:
  - Resolves "team" = owner of PaymentGW
  - Answers: "Payments team leads PaymentGW"

Turn 4: "Is the postmortem review deadline overdue?"
System:
  - Finds deadline from postmortem document
  - Compares to current date
  - Answers: "Yes/No, deadline was..."
```

**Pass Criteria:**
- ✓ Pronoun resolution ("that service" → correctly identified)
- ✓ Multi-turn conversation flows naturally
- ✓ No re-explanation needed after Turn 1

---

## Evidence Pack Structure (Critical!)

**File:** `docs/W4_evidence.md`

This is the deliverable trainers will re-grade after Friday. **Incomplete evidence = capped score.**

### Template Structure

```markdown
# W4 Evidence Pack — [Group Number]

## Cover

- **Group:** [number]
- **Members:** [names]
- **LLM:** Claude 3.5 Sonnet (AWS Bedrock)
- **Framework:** LangChain
- **Repository:** [GitHub link]

## Section 1: Architecture Overview

[Diagram of system]

Components:
- Bedrock KB: Knowledge base + retrieval
- Tools: Database, API, metrics
- LLM: Orchestration via LangChain
- Memory: Conversation context (L4)

Data Flow:
1. User question enters system
2. Memory manager checks conversation history (L4)
3. Retriever fetches knowledge base chunks
4. Question router decides: RAG-only or tool-augmented?
5. If tools needed: plan, execute, aggregate results
6. LLM synthesizes answer with system prompt
7. Response formatter adds citations + logs

[Screenshot: System running]

## Section 2: Key Decisions

### Decision 1: Bedrock KB + Custom Prompt
**What:** Use Bedrock's managed KB for retrieval, but keep LLM calls in our code
**Why:** AWS handles scaling, we keep full control over prompting
**Learned:** Hybrid search (BM25 + vector) catches questions that pure vector search misses

### Decision 2: SQLite for Development
**What:** Use seed_data.py's default SQLite instead of PostgreSQL
**Why:** Faster setup, no DB admin, good enough for 5 days
**Learned:** SQL schema auto-created; no migration complexity

### Decision 3: LangChain Tool Routing
**What:** Use LangChain's tool orchestration instead of building our own
**Why:** Proven, handles tool selection + execution loop
**Learned:** Tool descriptions must be very clear, or LLM picks wrong tool

### What Didn't Work
Tried: Pure vector search for retrieval
Problem: Questions mentioning specific error codes or SLA numbers were missed
Solution: Switched to HYBRID search (BM25 + vector)

## Section 3: L1 Evidence

**Screenshot: Correct Answer with Source**
[Show system output: "Who leads Team Platform?" → "Alex Chen (from team_platform.md)"]

**Proof of Retrieval:**
[Show CloudWatch logs or terminal output demonstrating Bedrock Retrieve API call + chunks returned]

## Section 4: L2 Evidence

**Screenshot: Conflict Resolution**
[Show system handling "API rate limit?" question — retrieves v1 (500) and v2 (1000), identifies v2 as current]

**How We Handle Conflicts:**
- System prompt instructs LLM to check document dates
- Metadata filtering can exclude archived documents
- When conflict detected, we cite both and explain preference

## Section 5: L3 Evidence

**Screenshot: Correct Numerical Answer**
[Show "PaymentGW Q1 2026 total cost?" → "$23,800"]

**Proof of Tool Execution:**
[Show tool call in logs]
```json
{
  "tool_name": "database_query",
  "query": "SELECT SUM(cost) FROM monthly_costs WHERE service_name='PaymentGW' AND month BETWEEN '2026-01' AND '2026-03'",
  "result": [
    {"SUM(cost)": 23800}
  ]
}
```

This is the proof that real data was retrieved, not hallucinated.

## Section 6: L4 Evidence (if attempted)

**Screenshot: 3-4 Turn Conversation**
```
Turn 1: User: "Which service had highest cost in March?"
System: "PaymentGW at $8,100"

Turn 2: User: "What caused the spike?"
System: "[Resolves 'spike' = PaymentGW March] Root cause: database migration overhead (from incident postmortem)"

Turn 3: User: "Who handles that?"
System: "[Resolves 'that' = PaymentGW] Payments team (from team_payments.md)"
```

**Memory Strategy:**
- Keep rolling window of last 5 turns
- Extract entities (service, team, date) from answers
- Include conversation history in system prompt

## Section 7: Reflection

**Hardest Level:** L3 (why: tool routing requires precise descriptions + real data accuracy)

**Would Change:** 
- Spent too long on KB setup; could have used Bedrock KB + simple retrieval from Day 1
- Would test tools earlier (Monday) instead of Thursday

```

---

## Testing Strategy

### Test Data Set

**L1 Tests (5 questions — easy, single doc):**
1. "Who is the Team Platform lead?" → Alex Chen
2. "What is GeekBrain's SLA for latency?" → 200ms p99
3. "Describe OrderSvc architecture" → [from service_order.md]
4. "When was the last postmortem filed?" → [date]
5. "What is the company's incident severity policy?" → [from policy]

**L2 Tests (3 questions — moderate, multi-doc or conflicts):**
1. "What is PaymentGW's API rate limit?" → (conflict: v1=500 vs v2=1000, resolve to 1000)
2. "Can Team Commerce deploy on Friday night?" → (combine: deployment policy + team + incident response)
3. "Which services are in the critical tier?" → (cross-reference multiple docs)

**L3 Tests (4 questions — numerical, tools required):**
1. "What was PaymentGW's total cost in Q1 2026?" → $23,800 (DB query)
2. "What is OrderSvc's current p99 latency?" → ~X ms (service_metrics API)
3. "How many incidents did NotificationSvc have in Q1?" → N (DB query)
4. "Is PaymentGW's current latency within SLA?" → Yes/No (metrics API + DB comparison)

**L4 Tests (1 conversation — 3-4 turns with pronouns):**
```
Turn 1: "Which service had highest cost in March?"
Turn 2: "What caused the spike?" (pronoun: "the spike" = the service from Turn 1)
Turn 3: "Which team owns that?" (pronoun: "that" = the service)
Turn 4: "Were there any incidents that month?" (pronoun: "that month" = March)
```

### Manual Testing Checklist

- [ ] L1: Single-doc retrieval works, source cited
- [ ] L2: Multi-doc synthesis works, conflicts resolved
- [ ] L3: Database queries return correct numbers
- [ ] L3: API calls to monitoring service work
- [ ] L3: Tool routing decisions are correct (RAG vs tool)
- [ ] L4: Memory persists across turns (if attempted)
- [ ] All: No errors, graceful handling of edge cases

---

## Critical Path Timeline

### **Tuesday, May 3 (8 hours available)**

| Time | Task | Owner | Status |
|------|------|-------|--------|
| 09:00-10:00 | Read all 36 docs + map conflicts | - | ⏳ |
| 10:00-11:30 | Run seed_data.py, verify database | - | ⏳ |
| 11:30-12:30 | Start monitoring API, explore endpoints | - | ⏳ |
| 12:30-13:30 | Lunch | - | ⏳ |
| 13:30-14:30 | Verify AWS Bedrock access | - | ⏳ |
| 14:30-17:00 | Upload docs to S3, start KB creation | - | ⏳ |
| 17:00-18:00 | Buffer / documentation | - | ⏳ |

**EOD Deliverable:** data_exploration.md with doc mapping + API catalog + DB verification

---

### **Wednesday, May 4 (8 hours available)**

| Time | Task | Owner | Status |
|------|------|--------|--------|
| 09:00-10:00 | Wait for KB sync to complete (or parallelize) | - | ⏳ |
| 10:00-12:00 | Build L1 retriever + system prompt | - | ⏳ |
| 12:00-13:00 | Lunch | - | ⏳ |
| 13:00-14:00 | Test L1 (5 test questions) | - | ⏳ |
| 14:00-15:00 | Debug retrieval issues if any | - | ⏳ |
| 15:00-17:00 | **STOP** — L1 must be 100% working before proceeding | - | ⏳ |
| 17:00-18:00 | L2 prep: increase K, improve prompt | - | ⏳ |

**EOD Deliverable:** L1 fully working, 5/5 test questions passing

---

### **Thursday, May 5 (7 hours available)**

| Time | Task | Owner | Status |
|------|------|--------|--------|
| 09:00-10:00 | Finish L2 (conflict resolution) | - | ⏳ |
| 10:00-11:00 | Test L2 (3 test questions) | - | ⏳ |
| 11:00-12:00 | Debug if needed | - | ⏳ |
| 12:00-13:00 | Lunch | - | ⏳ |
| 13:00-14:30 | Build L3 tools (DB + API) | - | ⏳ |
| 14:30-16:00 | Integrate LangChain tool routing | - | ⏳ |
| 16:00-17:00 | Test L3 (first tool call) | - | ⏳ |
| 17:00-18:00 | Buffer / early testing | - | ⏳ |

**EOD Deliverable:** L3 with ≥1 working tool

---

### **Friday, May 6 (4 hours available before demo)**

| Time | Task | Owner | Status |
|------|------|--------|--------|
| 08:00-09:00 | Complete L3 tests (all 4 questions) | - | ⏳ |
| 09:00-09:30 | L4 memory implementation (if time) | - | ⏳ |
| 09:30-10:00 | Final system tests end-to-end | - | ⏳ |
| 10:00-11:00 | Write Evidence Pack (screenshots + logs) | - | ⏳ |
| 11:00-12:00 | Prepare slides from Evidence Pack | - | ⏳ |
| 12:00-12:30 | Rehearsal + buffer | - | ⏳ |
| 12:30 | Post Evidence Pack commit link to Slack | - | ⏳ |
| 14:00+ | Presentations | - | ⏳ |

**EOD Deliverable:** Live demo + Evidence Pack + Slides

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| KB sync takes too long | Blocks L1 | Start S3 upload + KB creation Tuesday EOD; parallelize with other work |
| Tool descriptions too vague | LLM picks wrong tool | Write tool descriptions very explicitly; test with 2-3 examples per tool |
| Database queries slow or incorrect | L3 accuracy | Test all queries locally before integration; use EXPLAIN PLAN |
| API downtime (monitoring) | L3 tool fails | Build retry logic; log API errors; have fallback responses |
| Bedrock rate limits | Slow performance | Use caching where possible; monitor token usage |
| Memory exhaustion (L4) | System crashes | Implement max_turns limit (5 turns) to bound context |
| Time management | Incomplete L3/L4 | L1-L2 non-negotiable by Thursday; L3 critical; L4 is bonus |

---

## Bonus Opportunities

### Bonus A: Observability Dashboard (+0.5)

**What:** Build a UI showing system internals as it processes questions.

**Implementation (if time allows):**
```python
# src/observability.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get('/dashboard')
async def dashboard():
    """Return a simple HTML dashboard"""
    return HTMLResponse("""
    <html>
    <body>
    <h1>Query Trace</h1>
    <div id='trace'></div>
    <script>
    // WebSocket or polling to show:
    // - Retrieved chunks
    // - Tool calls
    // - LLM reasoning
    // - Final answer
    </script>
    </body>
    </html>
    """)
```

**Evidence:** Screenshot of dashboard showing a question being processed.

---

### Bonus B: Agent Reasoning (+0.5)

**What:** Handle open-ended investigation questions with multi-step reasoning.

**Example Question:** "Is NotificationSvc in a healthy state?"

**System should:**
1. Gather current metrics (latency, error rate, uptime)
2. Check against SLA targets
3. Look for recent incidents
4. Assess deployment recency
5. Produce a structured health report with reasoning visible

---

### Bonus C: KB Auto-Sync (+0.5)

**What:** Automatically re-sync knowledge base when documents change in S3.

**Implementation:**
- S3 event → Lambda → Bedrock StartIngestionJob
- Or: Jupyter notebook that manually triggers re-sync

---

## Success Criteria

### Must-Have (Non-Negotiable)

- [ ] L1 working: Single-doc retrieval + source citation
- [ ] L2 working: Multi-doc synthesis + conflict resolution
- [ ] L3 working: At least 1 correct numerically-grounded answer via tool
- [ ] Evidence Pack submitted with screenshots + logs
- [ ] Live demo runs without crashing
- [ ] Commits/code visible in GitHub

### Should-Have (High Priority)

- [ ] All L3 tools working (4/4 test questions)
- [ ] L4 basic memory working (conversation flows)
- [ ] Evidence Pack well-organized + clean screenshots
- [ ] Presentation slides follow evidence

### Nice-to-Have (Bonus)

- [ ] Observability dashboard (Bonus A)
- [ ] Multi-step agent reasoning (Bonus B)
- [ ] KB auto-sync (Bonus C)
- [ ] Error handling + edge cases

---

## Tools & Resources

| Tool | Purpose | Setup |
|------|---------|-------|
| **AWS Bedrock** | LLM + KB | `aws sts get-caller-identity` to verify |
| **LangChain** | Tool orchestration | `pip install langchain langchain-community boto3` |
| **SQLite3** | Database | Built-in; seed_data.py creates it |
| **FastAPI** | Local API | `pip install fastapi uvicorn` |
| **CloudWatch** | Logs | Built-in to AWS account |

---

## Key Files to Create

```
d:\Xbrain\RAG\W4\
├── src/
│   ├── __init__.py
│   ├── config.py                # AWS creds, model IDs, paths
│   ├── rag_pipeline.py          # L1-L2 retrieval
│   ├── tools.py                 # L3 tool definitions
│   ├── agent.py                 # L3-L4 LangChain agent
│   ├── memory.py                # L4 conversation memory
│   └── main.py                  # Entry point / CLI
├── tests/
│   ├── test_l1.py
│   ├── test_l2.py
│   ├── test_l3.py
│   └── test_l4.py
├── docs/
│   ├── W4_evidence.md           # CRITICAL: Evidence Pack
│   └── data_exploration.md      # Phase 1 findings
├── logs/
│   └── .gitkeep
└── plan/
    └── W4_IMPLEMENTATION_PLAN.md # This file
```

---

## Conclusion

This plan is a **sequential, risk-aware roadmap** from data exploration through a fully working RAG + Tool + Memory system. The critical path is:

1. **Understand data** (Tue)
2. **L1 working** (Wed)
3. **L2 working** (Wed evening)
4. **L3 working** (Thu-Fri morning)
5. **Evidence + presentation** (Fri morning)

**Target Score:** 10/10 base (L1-L4 all working) + 0.5-1.0 bonus if time allows.

**Key Principle:** Ship L1-L3 working before attempting anything else. Quality > quantity.
