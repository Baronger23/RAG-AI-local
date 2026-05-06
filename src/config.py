"""
Configuration for GeekBrain W4 AI System
Load from environment variables or use defaults
"""

import os
from pathlib import Path
from typing import Literal

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PACKAGE = PROJECT_ROOT / "data_package"
KNOWLEDGE_BASE_DIR = DATA_PACKAGE / "knowledge_base"
STRUCTURED_DATA_DIR = DATA_PACKAGE / "structured_data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

# Check if AWS credentials are available
AWS_ENABLED = bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)

# Bedrock Configuration
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")

# Load KB ID from file if not in environment
BEDROCK_KB_ID = os.getenv("BEDROCK_KB_ID", "")
if not BEDROCK_KB_ID:
    kb_id_path = Path(__file__).parent / "kb_id.txt"
    if kb_id_path.exists():
        BEDROCK_KB_ID = kb_id_path.read_text().strip()
BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"

# S3 Configuration (for knowledge base documents)
S3_BUCKET = os.getenv("S3_BUCKET", "geekbrain-kb-341515954788")
S3_KB_PREFIX = "docs/"

# OpenSearch Configuration (for Bedrock KB)
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "")
OPENSEARCH_COLLECTION = os.getenv("OPENSEARCH_COLLECTION", "geekbrain-kb")

# Database Configuration
DB_TYPE: Literal["sqlite", "postgres"] = os.getenv("DB_TYPE", "sqlite")  # type: ignore
SQLITE_PATH = os.getenv("SQLITE_PATH", str(DATA_PACKAGE / "geekbrain.db"))
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@localhost/geekbrain")

# Monitoring API Configuration
MONITORING_API_BASE = os.getenv("MONITORING_API_BASE", "http://localhost:8000")
MONITORING_API_TIMEOUT = int(os.getenv("MONITORING_API_TIMEOUT", "5"))

# RAG Configuration
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "10"))  # Number of chunks to retrieve
HYBRID_SEARCH = os.getenv("HYBRID_SEARCH", "true").lower() == "true"  # Use BM25 + vector

# LLM Configuration
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))

# Memory Configuration (L4)
MEMORY_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "5"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "geekbrain.log"
LOG_JSON = os.getenv("LOG_JSON", "false").lower() == "true"

# Mode Configuration
# "mock" = use local files + mock API (dev mode)
# "local" = use local files + real monitoring API
# "cloud" = use AWS Bedrock KB + real monitoring API
MODE: Literal["mock", "local", "cloud"] = os.getenv("MODE", "cloud")  # type: ignore

# Determine actual mode based on AWS availability
try:
    import boto3
    session = boto3.Session()
    credentials = session.get_credentials()
    AWS_ENABLED = credentials is not None
except ImportError:
    AWS_ENABLED = False

if not AWS_ENABLED:
    MODE = "mock"  # Force mock mode if AWS credentials missing
elif not BEDROCK_KB_ID:
    MODE = "local"  # Use local KB files even if AWS available

print(f"""
GeekBrain W4 Configuration
==========================
Mode: {MODE}
AWS Enabled: {AWS_ENABLED}
DB Type: {DB_TYPE}
Monitoring API: {MONITORING_API_BASE}
Log Level: {LOG_LEVEL}

Paths:
  Knowledge Base: {KNOWLEDGE_BASE_DIR}
  Structured Data: {STRUCTURED_DATA_DIR}
  Database (SQLite): {SQLITE_PATH if DB_TYPE == 'sqlite' else 'N/A'}
  Logs: {LOGS_DIR}
""")
