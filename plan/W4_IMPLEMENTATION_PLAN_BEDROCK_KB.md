# W4: Build an AI That Actually Answers — Implementation Plan
## Bedrock KB + Custom Prompt Architecture

**Project:** GeekBrain Q&A System  
**Duration:** May 3-8, 2026 (5 days)  
**Target Score:** 10/10 (Base) + 0.5-1.0 (Bonus)  
**Architecture:** Bedrock Knowledge Bases + LangChain + Tool Routing  
**Status:** Plan v2.0 — Bedrock KB Focused

---

## Executive Summary

Build a **progressive RAG + Tool-Augmented AI system** using **AWS Bedrock managed Knowledge Bases** for retrieval:

| Level | Capability | Architecture |
|-------|-----------|--------------|
| **L1** | Single-doc retrieval | Bedrock KB Retrieve API → Custom Prompt → Bedrock LLM |
| **L2** | Multi-source synthesis + conflict resolution | Increase K + Improved system prompt + Metadata filtering |
| **L3** | Retrieval + Database + Real-time API tools | LangChain agent + Tool orchestration |
| **L4** | Multi-turn memory + context preservation | ConversationMemory class |
| **Bonus** | Observability OR Agent Reasoning OR KB Sync | +0.5-1.0 |

**Base Score Path:** L1 (2) + L2 (3) + L3 (4) + L4 (1) = **10 points guaranteed**.

---

## Technology Stack

### Core Components

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Retrieval** | Bedrock Knowledge Bases | Managed chunking, embedding, vector store. Hybrid search (BM25 + semantic) built-in. |
| **Embedding** | Amazon Titan Embeddings v2 | Native Bedrock service. No extra API keys. High quality. |
| **LLM** | Claude 3.5 Sonnet (Bedrock) | Reliable, fast, excellent for tool calling & reasoning |
| **Framework** | LangChain (Python) | Clean tool orchestration, good logging, mature ecosystem |
| **Database** | SQLite (local) → RDS (optional) | seed_data.py pre-built. Fast iteration. |
| **Tools** | Database + Monitoring API | L3 tool execution for real data |
| **Storage** | S3 bucket | KB documents live here. Bedrock syncs automatically. |

### Project Structure

```
d:\Xbrain\RAG\W4\
├── data_package/
│   ├── knowledge_base/              # 36 markdown files (copied to S3)
│   ├── structured_data/             # CSV files
│   │   ├── monthly_costs.csv
│   │   ├── incidents.csv
│   │   ├── sla_targets.csv
│   │   └── daily_metrics.csv
│   └── scripts/
│       ├── seed_data.py             # Load CSV → SQLite
│       └── monitoring_api.py        # Live metrics API
│
├── src/                             # Our code (to create)
│   ├── config.py                    # AWS, Bedrock KB, paths
│   ├── kb_setup.py                  # One-time: Create KB, sync
│   ├── rag_pipeline.py              # L1-L2: Retrieve, prompt, LLM
│   ├── tools.py                     # L3: Database + API tools
│   ├── agent.py                     # L3-L4: LangChain agent
│   ├── memory.py                    # L4: Conversation memory
│   ├── logger.py                    # JSON logging
│   └── main.py                      # CLI entry point
│
├── tests/
│   ├── test_l1.py                   # L1 test questions (5)
│   ├── test_l2.py                   # L2 test questions (3)
│   ├── test_l3.py                   # L3 test questions (4)
│   └── test_l4.py                   # L4 conversation test
│
├── docs/
│   ├── W4_evidence.md               # CRITICAL: Evidence Pack
│   └── data_exploration.md
│
├── logs/
│   └── .gitkeep
│
└── plan/
    └── W4_IMPLEMENTATION_PLAN_BEDROCK_KB.md  # This file
```

---

## Architecture Overview

### System Diagram: Bedrock KB + LangChain

```
┌──────────────────────────────────────────────────────────┐
│                    USER QUESTION                          │
│              "Who is Team Platform lead?"                 │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   ConversationMemory    │
        │   (L4 - track turns)    │
        └────────────┬────────────┘
                     │
        ┌────────────▼─────────────────────────────────────┐
        │   L1-L2: Bedrock KB Retrieval                    │
        │                                                   │
        │  bedrock_agent.retrieve(                          │
        │    knowledgeBaseId="kb-xxx",                      │
        │    retrievalQuery="Who leads Team Platform?",     │
        │    numberOfResults=10,                           │
        │    overrideSearchType="HYBRID"  # BM25 + vector  │
        │  )                                                │
        │                                                   │
        │  Returns: [                                       │
        │    {"content": "...", "source": "team_platform.md"},
        │    {"content": "...", "source": "org_structure.md"},
        │    ...                                            │
        │  ]                                                │
        └────────────┬─────────────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────────────┐
        │   Tool Router (L3)                                │
        │   Does question need tools?                       │
        │   - "Who leads?" → NO (just RAG)                  │
        │   - "What was Q1 cost?" → YES (DB tool)           │
        │   - "Current latency?" → YES (API tool)           │
        │   - "Is cost within budget?" → YES (both)         │
        └────────────┬─────────────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────────────┐
        │   LLM Processing (Claude 3.5 Sonnet)             │
        │                                                   │
        │   Input:                                          │
        │   - System prompt (instructions, conflict rules)  │
        │   - Retrieved chunks (from Bedrock KB)            │
        │   - Tool results (if any)                         │
        │   - Conversation history (if L4)                  │
        │                                                   │
        │   Output:                                         │
        │   - Final answer: "Alex Chen leads Team Platform" │
        │   - Citation: "from team_platform.md"             │
        │   - Reasoning: (if L3 tool used)                  │
        └────────────┬─────────────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────────────┐
        │   Response Formatting                             │
        │   - Add sources                                   │
        │   - Add tool trace (if L3)                        │
        │   - Store in memory (if L4)                       │
        │   - Log to CloudWatch/local                       │
        └────────────┬─────────────────────────────────────┘
                     │
        ┌────────────▼──────────────────────────────────┐
        │   USER OUTPUT                                  │
        │   "Alex Chen (from team_platform.md)"          │
        └─────────────────────────────────────────────────┘
```

---

## Phase 1: Setup & Knowledge Base Creation (Tuesday, May 3)

### Goal
Get Bedrock Knowledge Base running with all 36 docs synced, database seeded, monitoring API running.

### Tasks

#### 1.1: Data Exploration (1.5 hours)

- [ ] Read all 36 markdown files from `data_package/knowledge_base/`
- [ ] Create mapping: which docs cover same topics?
- [ ] Identify conflicts: API rate limits, policies, team structure
- [ ] Extract key facts for manual validation later

**Deliverable:** `docs/data_exploration.md` with doc map + conflicts identified

---

#### 1.2: Database Setup (1 hour)

```bash
cd d:\Xbrain\RAG\W4\data_package\scripts

# Seed SQLite database from CSV
python seed_data.py --db-type sqlite

# Verify database created
ls -la ../geekbrain.db

# Quick test queries
sqlite3 ../geekbrain.db
> SELECT service, total_cost FROM monthly_costs WHERE month = '2026-03' ORDER BY total_cost DESC;
# PaymentGW should show 8100
```

**Checklist:**
- [ ] Database file exists
- [ ] 4 tables created (monthly_costs, incidents, sla_targets, daily_metrics)
- [ ] Data loads correctly
- [ ] Sample queries return expected numbers

---

#### 1.3: Monitoring API Setup (1 hour)

```bash
cd d:\Xbrain\RAG\W4\data_package\scripts

# Start monitoring API
uvicorn monitoring_api:app --reload --port 8000

# In another terminal, test endpoints
curl http://localhost:8000/services
curl http://localhost:8000/metrics/PaymentGW
curl http://localhost:8000/status/PaymentGW
curl http://localhost:8000/incidents?service=OrderSvc
```

**Expected responses:**
- `/services` → list of 6 services
- `/metrics/{service}` → latency_p99, error_rate, requests_per_min
- `/status/{service}` → health, uptime, active alerts
- `/incidents` → incident history

**Checklist:**
- [ ] API starts without errors
- [ ] All endpoints respond
- [ ] Data is fresh (from mock generator)

---

#### 1.4: AWS Bedrock Verification (30 mins)

```bash
# Verify AWS CLI configured
aws sts get-caller-identity
# Should show your Account, UserId, Arn

# List available Bedrock models
aws bedrock list-foundation-models --region us-east-1 | grep claude-3-5

# Test simple Bedrock call
python
>>> import boto3
>>> client = boto3.client('bedrock-runtime', region_name='us-east-1')
>>> # (Will test properly in Phase 2)
```

**Checklist:**
- [ ] AWS credentials configured (us-east-1)
- [ ] Bedrock access verified
- [ ] Claude 3.5 Sonnet model available

---

#### 1.5: S3 Setup & Upload Documents (1.5 hours)

```bash
# Create S3 bucket for KB documents
aws s3 mb s3://geekbrain-kb-{your-account-id}

# Copy all markdown files to S3
aws s3 sync d:\Xbrain\RAG\W4\data_package\knowledge_base/ \
    s3://geekbrain-kb-{your-account-id}/docs/ \
    --exclude "*" --include "*.md"

# Verify upload
aws s3 ls s3://geekbrain-kb-{your-account-id}/docs/ | wc -l
# Should show ~36 files
```

**Checklist:**
- [ ] S3 bucket created
- [ ] All 36 markdown files uploaded
- [ ] S3 files readable by Bedrock

---

#### 1.6: Create Bedrock Knowledge Base (2-3 hours including sync wait)

Create `src/kb_setup.py`:

```python
import boto3
import json
import time
from botocore.exceptions import ClientError

def create_bedrock_kb():
    """One-time setup: Create Bedrock Knowledge Base"""
    
    client = boto3.client('bedrock-agent', region_name='us-east-1')
    
    kb_name = 'geekbrain-kb'
    
    try:
        # Create Knowledge Base
        print("Creating Knowledge Base...")
        response = client.create_knowledge_base(
            name=kb_name,
            description='GeekBrain knowledge base for Q&A system',
            roleArn='arn:aws:iam::ACCOUNT_ID:role/bedrock-kb-role',  # Create this role manually
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
                    'collectionArn': 'arn:aws:aoss:us-east-1:ACCOUNT_ID:collection/geekbrain-kb'
                    # Create OpenSearch collection manually or programmatically
                }
            }
        )
        
        kb_id = response['knowledgeBase']['id']
        print(f"✓ Knowledge Base created: {kb_id}")
        
        # Add data source (S3)
        print("Adding S3 data source...")
        ds_response = client.create_data_source(
            knowledgeBaseId=kb_id,
            name='geekbrain-docs',
            description='Markdown documents from data_package',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': 'arn:aws:s3:::geekbrain-kb-ACCOUNT_ID',
                    'inclusionPatterns': ['*.md']
                }
            }
        )
        
        data_source_id = ds_response['dataSource']['id']
        print(f"✓ Data source created: {data_source_id}")
        
        # Start ingestion
        print("Starting KB ingestion (this may take 5-10 mins)...")
        ingest_response = client.start_ingestion_job(
            dataSourceId=data_source_id,
            knowledgeBaseId=kb_id
        )
        
        ingest_job_id = ingest_response['ingestionJob']['ingestionJobId']
        
        # Wait for ingestion to complete
        max_wait = 600  # 10 minutes
        elapsed = 0
        while elapsed < max_wait:
            status_response = client.get_ingestion_job(
                dataSourceId=data_source_id,
                ingestionJobId=ingest_job_id,
                knowledgeBaseId=kb_id
            )
            
            status = status_response['ingestionJob']['status']
            print(f"  Status: {status} ({elapsed}s elapsed)")
            
            if status == 'COMPLETE':
                print("✓ Ingestion complete!")
                break
            elif status == 'FAILED':
                print(f"✗ Ingestion failed: {status_response['ingestionJob']}")
                break
            
            time.sleep(15)
            elapsed += 15
        
        # Save KB ID for later use
        with open('src/kb_id.txt', 'w') as f:
            f.write(kb_id)
        
        print(f"\n✓✓✓ Setup complete! KB ID saved to src/kb_id.txt")
        return kb_id
        
    except ClientError as e:
        print(f"Error: {e}")
        return None

if __name__ == '__main__':
    create_bedrock_kb()
```

Run setup:
```bash
cd d:\Xbrain\RAG\W4
python src/kb_setup.py
```

**Checklist:**
- [ ] Knowledge Base created
- [ ] Data source added
- [ ] Ingestion started
- [ ] Wait for ingestion to complete (COMPLETE status)
- [ ] KB ID saved

---

### Phase 1 Deliverables

✓ Database seeded with CSV data  
✓ Monitoring API running locally  
✓ AWS Bedrock access verified  
✓ S3 bucket with 36 markdown files  
✓ Bedrock Knowledge Base created + synced  
✓ KB ID saved for Phase 2  
✓ `docs/data_exploration.md` with conflict map

**EOD Tuesday:** All infrastructure ready. KB syncing or just finished.

---

## Phase 2: L1 & L2 Implementation (Wednesday-Thursday, May 4-5)

### L1: Simple Retrieval via Bedrock KB

#### 2.1: Build L1 Retriever (2 hours)

Create `src/rag_pipeline.py`:

```python
import boto3
import json
from typing import List, Dict

class L1Retriever:
    """L1-L2: Retrieve from Bedrock KB, build prompt, call LLM"""
    
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    
    def retrieve_chunks(self, query: str, top_k: int = 5, 
                       exclude_archived: bool = True) -> List[Dict]:
        """
        Retrieve chunks from Bedrock KB using Retrieve API.
        
        Hybrid search: combines vector search (semantic) + BM25 (keyword).
        """
        filter_config = None
        if exclude_archived:
            filter_config = {
                'not': {
                    'key': 'metadata.status',
                    'value': 'archived'
                }
            }
        
        response = self.bedrock_agent_runtime.retrieve(
            knowledgeBaseId=self.kb_id,
            retrievalQuery=query,
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': top_k,
                    'overrideSearchType': 'HYBRID'  # Vector + BM25
                }
            }
        )
        
        results = []
        for item in response['retrievalResults']:
            results.append({
                'content': item['content'],
                'source': item['metadata'].get('source', 'unknown'),
                'score': item.get('score', 0),
                'metadata': item.get('metadata', {})
            })
        
        return results
    
    def answer_question(self, question: str, top_k: int = 5) -> Dict:
        """
        L1 Pipeline:
        1. Retrieve chunks from KB
        2. Build context
        3. Create prompt
        4. Call Bedrock LLM
        5. Format response
        """
        
        # Step 1: Retrieve
        chunks = self.retrieve_chunks(question, top_k=top_k)
        
        if not chunks:
            return {
                'answer': 'No relevant information found.',
                'sources': [],
                'chunks_retrieved': 0,
                'level': 'L1',
                'success': False
            }
        
        # Step 2: Build context
        context_parts = []
        sources = set()
        for chunk in chunks:
            context_parts.append(
                f"[Source: {chunk['source']}]\n{chunk['content']}"
            )
            sources.add(chunk['source'])
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 3: Create system prompt
        system_prompt = """You are a helpful assistant answering questions about GeekBrain, a fintech startup.

Rules:
1. Answer ONLY using the provided context
2. Always cite the source document
3. If the context doesn't contain the answer, say "I don't have enough information"
4. Be concise and factual
5. Format citations as [Source: filename]"""
        
        # Step 4: Create user prompt
        user_prompt = f"""Question: {question}

Context:
{context}

Please provide a clear, factual answer citing the source document."""
        
        # Step 5: Call Bedrock LLM
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-06-01',
                'max_tokens': 500,
                'system': system_prompt,
                'messages': [
                    {
                        'role': 'user',
                        'content': user_prompt
                    }
                ]
            })
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text']
        
        # Step 6: Format response
        return {
            'answer': answer,
            'sources': list(sources),
            'chunks_retrieved': len(chunks),
            'level': 'L1',
            'success': True
        }
```

---

#### 2.2: Test L1 (1 hour)

Create `tests/test_l1.py`:

```python
import sys
sys.path.insert(0, 'src')
from rag_pipeline import L1Retriever

# Load KB ID
with open('src/kb_id.txt') as f:
    kb_id = f.read().strip()

retriever = L1Retriever(kb_id)

# Test questions
test_cases = [
    ("Who is the Team Platform lead?", "Alex Chen"),
    ("What is GeekBrain's latency SLA for p99?", "200"),
    ("Describe the OrderSvc architecture", "microservice"),
    ("What is the API rate limit for PaymentGW?", "1000"),
    ("When was the last incident in Q1?", "2026"),
]

print("=" * 60)
print("L1 TESTS: Single-Document Retrieval")
print("=" * 60)

passed = 0
for question, expected_keyword in test_cases:
    print(f"\n[TEST] {question}")
    result = retriever.answer_question(question)
    
    print(f"Answer: {result['answer'][:200]}...")
    print(f"Sources: {result['sources']}")
    print(f"Chunks: {result['chunks_retrieved']}")
    
    # Check if expected keyword in answer
    if expected_keyword.lower() in result['answer'].lower():
        print("✓ PASS")
        passed += 1
    else:
        print(f"✗ FAIL (expected '{expected_keyword}')")

print(f"\n{passed}/{len(test_cases)} tests passed")
```

Run tests:
```bash
cd d:\Xbrain\RAG\W4
python tests/test_l1.py
```

**Pass Criteria:**
- ✓ All 5 questions answered correctly
- ✓ Sources cited
- ✓ Answers use context only

---

### L2: Multi-Source Retrieval & Conflict Resolution

#### 2.3: Improve L1 for L2 (1.5 hours)

Key changes in `src/rag_pipeline.py`:

```python
class L2Retriever(L1Retriever):
    """L2: Improved retrieval + conflict detection"""
    
    def retrieve_chunks(self, query: str, top_k: int = 10,  # Increased from 5
                       exclude_archived: bool = True) -> List[Dict]:
        """L2: Retrieve more chunks to find conflicts"""
        return super().retrieve_chunks(query, top_k=top_k, exclude_archived=exclude_archived)
    
    def answer_question(self, question: str, top_k: int = 10) -> Dict:
        """L2: Multi-source synthesis + conflict resolution"""
        
        # Retrieve with increased K
        chunks = self.retrieve_chunks(question, top_k=top_k)
        
        # Build context
        context_parts = []
        sources = set()
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['source']}]\n{chunk['content']}"
            )
            sources.add(chunk['source'])
        
        context = "\n\n---\n\n".join(context_parts)
        
        # L2: Enhanced system prompt for conflict resolution
        system_prompt = """You are an expert assistant answering questions about GeekBrain.

When you receive multiple documents:
1. Read them carefully
2. Check document dates, version numbers, and "last updated" fields
3. If sources provide CONFLICTING information:
   - Identify the conflict: "API v1 says X, but API v2 says Y"
   - Determine which is current: "v2 was updated on 2026-04-15, so it's newer"
   - State your choice: "I'm citing v2 as the current version"

4. If sources provide COMPLEMENTARY information:
   - Synthesize: combine facts from multiple sources
   - Example: "Team A owns X (from team_structure.md), and their SLA is Y (from policy.md)"

Rules:
- Always use only provided context
- When uncertain about version/currency, state the assumption
- Cite all relevant sources
- Be precise with numbers and dates"""
        
        # Create user prompt
        user_prompt = f"""Question: {question}

Available sources:
{context}

Please:
1. If there are conflicting answers, identify and resolve the conflict
2. If multiple sources say the same thing, cite all of them
3. If the answer spans multiple documents, show how they connect"""
        
        # Call LLM
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-06-01',
                'max_tokens': 1000,  # Increased for synthesis
                'system': system_prompt,
                'messages': [{
                    'role': 'user',
                    'content': user_prompt
                }]
            })
        )
        
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text']
        
        return {
            'answer': answer,
            'sources': list(sources),
            'chunks_retrieved': len(chunks),
            'level': 'L2',
            'success': True
        }
```

---

#### 2.4: Test L2 (1 hour)

Create `tests/test_l2.py`:

```python
import sys
sys.path.insert(0, 'src')
from rag_pipeline import L2Retriever

with open('src/kb_id.txt') as f:
    kb_id = f.read().strip()

retriever = L2Retriever(kb_id)

test_cases = [
    {
        'question': 'What is PaymentGW API rate limit?',
        'expected': 'Should resolve v1 (500) vs v2 (1000) to v2 as current'
    },
    {
        'question': 'Can Team Commerce deploy a fix on Friday night?',
        'expected': 'Synthesizes: deployment policy + incident response + team info'
    },
    {
        'question': 'Which services are in critical tier and what are their SLAs?',
        'expected': 'Multi-doc synthesis from service docs + policy'
    },
]

print("=" * 60)
print("L2 TESTS: Multi-Source Retrieval")
print("=" * 60)

for test in test_cases:
    print(f"\n[TEST] {test['question']}")
    result = retriever.answer_question(test['question'])
    
    print(f"Answer: {result['answer'][:300]}...")
    print(f"Sources ({len(result['sources'])}): {result['sources']}")
    print(f"Expected: {test['expected']}")
    print("✓ MANUAL REVIEW")
```

**Pass Criteria:**
- ✓ Conflicts identified ("v1 vs v2")
- ✓ Latest version preferred
- ✓ Multiple docs synthesized
- ✓ Sources cited clearly

---

### Phase 2 Deliverables

✓ L1 working: 5/5 questions correct  
✓ L2 working: conflict resolution + synthesis  
✓ 36 docs in Bedrock KB, synced  
✓ Both retrievers tested

**EOD Thursday (afternoon):** L1-L2 fully working, ready for L3.

---

## Phase 3: L3 Implementation (Thursday afternoon - Friday morning)

### Goal
Add tool execution for data-driven questions requiring database or API calls.

#### 3.1: Define Tool Functions (1 hour)

Create `src/tools.py`:

```python
import sqlite3
import requests
import json
from typing import Dict, List, Any

class DataTools:
    """Tool functions for L3 agent"""
    
    def __init__(self, db_path: str, api_base: str = 'http://localhost:8000'):
        self.db_path = db_path
        self.api_base = api_base
    
    def database_query(self, query: str) -> Dict[str, Any]:
        """
        Execute SQL query.
        Use for: costs, SLAs, incidents, metrics trends
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
            return {'status': 'error', 'error': str(e)}
    
    def service_metrics(self, service_name: str) -> Dict[str, Any]:
        """
        Get current metrics for a service.
        Use for: real-time health, current performance
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
        """Get current status of a service"""
        try:
            response = requests.get(
                f'{self.api_base}/status/{service_name}',
                timeout=5
            )
            return response.json()
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def incident_history(self, service_name: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent incidents for a service"""
        query = f"SELECT * FROM incidents WHERE service = '{service_name}' ORDER BY date DESC LIMIT {limit}"
        return self.database_query(query)
```

---

#### 3.2: Build L3 Agent with LangChain (2 hours)

Create `src/agent.py`:

```python
import sys
sys.path.insert(0, 'src')

from langchain.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.chat_models import BedrockChat
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from rag_pipeline import L2Retriever
from tools import DataTools
import json

class L3Agent:
    """L3: Retriever + Tool Routing + LangChain Agent"""
    
    def __init__(self, kb_id: str, db_path: str):
        self.retriever = L2Retriever(kb_id)
        self.tools_instance = DataTools(db_path)
        self.llm = BedrockChat(
            model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
            region_name='us-east-1'
        )
        self.tools = self._create_tools()
    
    def _create_tools(self):
        """Create LangChain tool definitions"""
        
        @tool
        def database_query(sql_query: str) -> str:
            """
            Execute a SQL query against GeekBrain database.
            Use for: historical costs, incidents, SLAs, metric trends.
            Example: SELECT SUM(total_cost) FROM monthly_costs WHERE service='PaymentGW'
            """
            result = self.tools_instance.database_query(sql_query)
            return json.dumps(result)
        
        @tool
        def service_metrics(service_name: str) -> str:
            """
            Get current live metrics for a service.
            Returns: latency_p99, error_rate, requests_per_min, availability
            Use for: current performance, real-time health
            """
            result = self.tools_instance.service_metrics(service_name)
            return json.dumps(result)
        
        @tool
        def service_status(service_name: str) -> str:
            """Get current status (healthy/degraded/down) for a service"""
            result = self.tools_instance.service_status(service_name)
            return json.dumps(result)
        
        @tool
        def incident_history(service_name: str) -> str:
            """Get recent incidents for a service"""
            result = self.tools_instance.incident_history(service_name)
            return json.dumps(result)
        
        return [database_query, service_metrics, service_status, incident_history]
    
    def process_query(self, question: str) -> Dict:
        """
        L3 Pipeline:
        1. Retrieve KB chunks
        2. Check if tools needed
        3. If yes: let LLM decide which tools, execute them
        4. Synthesize final answer
        """
        
        # Step 1: Retrieve from KB
        kb_chunks = self.retriever.retrieve_chunks(question, top_k=10)
        kb_context = "\n\n".join([
            f"[{c['source']}]\n{c['content']}"
            for c in kb_chunks
        ])
        
        # Step 2: Create system prompt for tool routing
        system_prompt = """You are an expert system engineer answering questions about GeekBrain infrastructure.

You have access to:
1. Knowledge Base: company docs, policies, team structure, architecture
2. Database: historical data (costs, incidents, SLAs, metrics from Jan-Mar 2026)
3. Monitoring API: current live metrics (latency, error rates, status)

Strategy:
- For CURRENT data ("now", "today", "live"): use service_metrics or service_status
- For HISTORICAL data ("Q1", "March", "last 30 days"): use database_query
- For POLICY/STRUCTURE ("SLA", "team", "process"): use knowledge base
- For COMPARISONS: get data from both sources

IMPORTANT: Always call tools to ground answers in real data. Show your reasoning.
Example: "PaymentGW Q1 total = SELECT SUM(total_cost) for 3 months = $7500 + $8200 + $8100 = $23800"

Format tool outputs in your answer so trainer can verify the data."""
        
        # Step 3: Create agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt),
            ('user', f"""Knowledge base context:
{kb_context}

Question: {question}

Use tools to gather real data. Show your work in the answer."""),
            MessagesPlaceholder(variable_name='agent_scratchpad')
        ])
        
        # Step 4: Create and run agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        
        result = executor.invoke({'input': question})
        
        return {
            'answer': result['output'],
            'kb_sources': [c['source'] for c in kb_chunks],
            'level': 'L3',
            'success': True
        }
```

---

#### 3.3: Test L3 Tools (1.5 hours)

Create `tests/test_l3.py`:

```python
import sys
sys.path.insert(0, 'src')
from agent import L3Agent

with open('src/kb_id.txt') as f:
    kb_id = f.read().strip()

agent = L3Agent(
    kb_id=kb_id,
    db_path='d:\\Xbrain\\RAG\\W4\\data_package\\geekbrain.db'
)

test_cases = [
    {
        'question': "What was PaymentGW's total infrastructure cost in Q1 2026?",
        'expected_tool': 'database_query',
        'expected_answer': '23800'  # 7500 + 8200 + 8100
    },
    {
        'question': "What is OrderSvc's current p99 latency?",
        'expected_tool': 'service_metrics',
        'expected_answer': 'ms'
    },
    {
        'question': "How many incidents did NotificationSvc have in Q1?",
        'expected_tool': 'database_query',
        'expected_answer': 'incident'
    },
    {
        'question': "Is PaymentGW's current latency within its 200ms SLA?",
        'expected_tool': 'service_metrics',
        'expected_answer': 'yes|no|within|above'
    },
]

print("=" * 60)
print("L3 TESTS: Retrieval + Tools")
print("=" * 60)

for test in test_cases:
    print(f"\n[TEST] {test['question']}")
    result = agent.process_query(test['question'])
    
    print(f"Answer: {result['answer'][:300]}...")
    print(f"Expected tool: {test['expected_tool']}")
    print(f"Expected in answer: {test['expected_answer']}")
    print("✓ MANUAL REVIEW - Check tool was called and data is accurate")
```

Run tests:
```bash
python tests/test_l3.py
```

**Pass Criteria:**
- ✓ Tools called for appropriate questions
- ✓ Numerical data is accurate
- ✓ Tool results shown in answer
- ✓ KB context still used where relevant

---

### Phase 3 Deliverables

✓ L3 agent implemented with 4 tools  
✓ Tool routing working (decides when to use tools)  
✓ All 4 L3 test questions answered correctly  
✓ Database queries return correct numbers  
✓ API calls work  
✓ Tool execution logged

**EOD Friday morning:** L3 fully working.

---

## Phase 4: L4 & Evidence Pack (Friday morning - early afternoon)

### L4: Multi-Turn Conversation Memory

#### 4.1: Build Memory System (1 hour)

Create `src/memory.py`:

```python
from collections import deque
from typing import Dict, List

class ConversationMemory:
    """Store conversation turns for context"""
    
    def __init__(self, max_turns: int = 5):
        self.turns = deque(maxlen=max_turns)
    
    def add_turn(self, question: str, answer: str):
        """Store a Q&A pair"""
        self.turns.append({
            'question': question,
            'answer': answer[:300]  # Truncate for brevity
        })
    
    def get_context(self) -> str:
        """Return conversation history for LLM"""
        if not self.turns:
            return ""
        
        history = "Previous conversation:\n"
        for i, turn in enumerate(self.turns, 1):
            history += f"\nTurn {i}:\n"
            history += f"Q: {turn['question']}\n"
            history += f"A: {turn['answer']}\n"
        
        return history
    
    def clear(self):
        """Reset conversation"""
        self.turns.clear()
```

#### 4.2: Integrate Memory into Agent (1 hour)

Modify `src/agent.py`:

```python
class L3Agent:
    def __init__(self, kb_id: str, db_path: str):
        # ... existing init ...
        self.memory = ConversationMemory()
    
    def process_query(self, question: str, store_in_memory: bool = True) -> Dict:
        """L4: Include conversation history in prompt"""
        
        # Get conversation context
        conv_context = self.memory.get_context()
        
        # ... existing retrieval ...
        
        # Enhanced prompt with memory
        system_prompt = """...
IMPORTANT: This is part of a multi-turn conversation.
Reference the previous turns if available.
Resolve pronouns: "that service" = entity from earlier turn, etc."""
        
        # ... execute agent ...
        
        # Store turn in memory
        if store_in_memory:
            self.memory.add_turn(question, result['output'])
        
        return result
```

#### 4.3: Test L4 (30 mins)

```python
# Test multi-turn conversation
agent = L3Agent(kb_id, db_path)

turns = [
    "Which service had the highest infrastructure cost in March 2026?",
    "What was the main cause of the cost increase that month?",
    "Which team is responsible?",
    "Were there any incidents that month?",
]

for i, question in enumerate(turns, 1):
    print(f"\nTurn {i}: {question}")
    result = agent.process_query(question)
    print(f"Answer: {result['answer'][:200]}...")
    
    # Verify pronoun resolution
    if i > 1 and ('that' in question or 'which' in question):
        print("✓ Pronoun handled (check manually)")
```

**Pass Criteria:**
- ✓ Conversation flows naturally
- ✓ Pronouns ("that service", "their team") resolved correctly
- ✓ No re-explanation needed after Turn 1
- ✓ Context carried across 3-4 turns

---

### Evidence Pack Creation

#### 4.4: Screenshot L1-L4 (1.5 hours)

Gather evidence for `docs/W4_evidence.md`:

```markdown
# W4 Evidence Pack — Group [N]

## Cover

- **Group:** [number]
- **Members:** [names]
- **LLM:** Claude 3.5 Sonnet (AWS Bedrock)
- **Framework:** LangChain + Bedrock KB Retrieve API
- **Repository:** [GitHub link]

## Section 1: Architecture

[System diagram showing Bedrock KB → Retriever → LLM → Tools → Response]

Components:
- Bedrock KB: Manages 36 docs, retrieval via Retrieve API (vector + BM25)
- L1-L2 Retriever: Custom prompting + conflict resolution
- L3 Agent: LangChain tool orchestration
- L4 Memory: Conversation history management

## Section 2: Key Decisions

### Decision 1: Bedrock KB + Custom Prompt
**Chose:** AWS-managed Bedrock KB for retrieval, LangChain for prompting/tools
**Why:** Fast setup, managed chunking, full control over prompt engineering
**Learned:** Hybrid search (vector + BM25) catches edge cases pure vector search misses

### Decision 2: LangChain Tool Routing
**Chose:** LangChain agents instead of manual routing
**Why:** Proven, handles tool selection + execution loop
**Learned:** Tool descriptions must be very specific

### Decision 3: SQLite for Speed
**Chose:** Local SQLite instead of RDS
**Why:** Fast iteration, no DB ops overhead
**Learned:** Good enough for development, handles seed data easily

## Section 3: L1 Evidence

[Screenshot: "Who is Team Platform lead?" → "Alex Chen (from team_platform.md)"]

**Bedrock Retrieve API call (from logs):**
```
retrieve(
  knowledgeBaseId="kb-xyz",
  retrievalQuery="Who is Team Platform lead",
  numberOfResults=5
)

Result: [
  {source: "team_platform.md", content: "...Alex Chen..."},
  ...
]
```

## Section 4: L2 Evidence

[Screenshot: API rate limit conflict resolved]

Question: "What is PaymentGW's API rate limit?"

System retrieves both:
- v1: "500 requests per second" (old_policy.md)
- v2: "1000 requests per second" (api_policy_v2.md, updated 2026-04-15)

Answer: "1000 requests per second (v2, updated 2026-04-15)"

## Section 5: L3 Evidence

[Screenshot: "PaymentGW Q1 cost?" → "$23,800"]

**Tool execution (from logs):**
```
Tool: database_query
Query: SELECT SUM(total_cost) FROM monthly_costs 
       WHERE service='PaymentGW' AND month BETWEEN '2026-01' AND '2026-03'

Result: [
  {SUM(total_cost): 23800}
]
```

Answer shows: "$23,800 (Jan: $7,500 + Feb: $8,200 + Mar: $8,100)"

## Section 6: L4 Evidence

[Screenshot: 4-turn conversation]

```
Turn 1: Q: "Highest cost service in March?"
        A: "PaymentGW at $8,100"

Turn 2: Q: "What caused the spike?"
        A: "[Resolves 'spike' = PaymentGW] Root cause: DB migration..."

Turn 3: Q: "Who handles that?"
        A: "[Resolves 'that' = PaymentGW] Payments team..."

Turn 4: Q: "Any incidents that month?"
        A: "[Resolves 'that month' = March] 2 incidents..."
```

## Section 7: Reflection

**Hardest Level:** L3 (tool routing + data accuracy)

**Would Change:**
- Would test tools earlier
- Would prepare S3 bucket on Day 1 to parallelize

---
```

---

### Phase 4 Deliverables

✓ L4 memory working (multi-turn conversation)  
✓ Evidence Pack complete with screenshots  
✓ Slides prepared from Evidence Pack  
✓ All tests passing (L1-L4)  
✓ Code committed to GitHub

---

## Timeline Summary

| Day | Phase | Focus | EOD Target |
|-----|-------|-------|-----------|
| **Tue** | 1 | KB setup, data exploration | KB synced + DB ready |
| **Wed** | 2 | L1-L2 retrieval | L1-L2 working (5/5 + 3/3 tests) |
| **Thu** | 2-3 | L2 → L3 tools | L3 partially working (1+ tool) |
| **Fri** | 3-4 | L3 complete, L4, Evidence | All working + Evidence Pack |

---

## Critical Path

1. ✅ Tuesday: Don't skip KB setup — it blocks everything else
2. ✅ Wednesday: Get L1 to 100% before L2 — if retrieval breaks, tools won't help
3. ✅ Thursday: Test tools early — you need Friday morning for L4 + evidence
4. ✅ Friday: L3 must be numerically accurate — trainer grades on precision

---

## Testing Checklist

### L1 (5 tests)
- [ ] "Who leads Team Platform?" → Alex Chen
- [ ] "SLA for latency?" → 200ms
- [ ] "OrderSvc architecture?" → [correct description]
- [ ] "Incident dates in Q1?" → [dates]
- [ ] "Incident severity policy?" → [from docs]

### L2 (3 tests)
- [ ] API rate limit conflict resolved (v1 vs v2)
- [ ] Multi-doc synthesis (deployment + policy + team)
- [ ] Services cross-reference (services + SLAs)

### L3 (4 tests)
- [ ] Q1 cost sum = $23,800 ✓ Accurate
- [ ] Current latency = X ms (from API)
- [ ] Q1 incident count = N (from DB)
- [ ] Is latency within SLA? (metrics + SLA comparison)

### L4 (4 turns)
- [ ] Turn 1: Identify entity (service, team)
- [ ] Turn 2: Reference "that" → correct resolution
- [ ] Turn 3: Chain pronoun references
- [ ] Turn 4: "that month" → correct date

---

## Success Metrics

| Metric | Target | Evidence |
|--------|--------|----------|
| **L1 accuracy** | 5/5 correct | Screenshots + logs |
| **L2 accuracy** | 3/3 correct | Conflict shown + resolved |
| **L3 accuracy** | 4/4 numerical correct | Tool call logs + verified data |
| **L4 fluency** | 4-turn conversation | Pronoun resolution visible |
| **Evidence** | Screenshots + reasoning | W4_evidence.md committed |
| **Live Demo** | No crashes, no hardcoding | Trainer asks novel questions |

---

**Deadline:** Thứ Sáu May 8, 2026, 14:00 (Presentation start time)

**Success Marker:** All 10 base points unlocked + 0-1 bonus points attempted.

Good luck! 🚀
