"""
RAG Pipeline for L1 (Simple Retrieval) and L2 (Multi-Source Retrieval)
Handles document retrieval and LLM augmentation
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests

from config import (
    BEDROCK_KB_ID,
    BEDROCK_MODEL_ID,
    AWS_ENABLED,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    MODE,
    RETRIEVAL_K,
)
from knowledge_base import kb
from logger import logger


class MockLLM:
    """Mock LLM for testing without AWS credentials"""

    def __init__(self):
        self.model_id = "mock-claude-3.5-sonnet"

    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        """
        Mock LLM response based on user query pattern
        This is for testing - will be replaced by real Bedrock LLM
        """
        # Simple pattern matching for common test questions
        if "team platform lead" in user_prompt.lower():
            return "Alex Chen is the Team Platform lead (from team_platform.md)."

        if "api rate limit" in user_prompt.lower():
            return "The API rate limit for PaymentGW is 1000 requests per second (from api_reference_v2.md, updated from v1 which specified 500)."

        if "paymentgw cost" in user_prompt.lower() and "q1" in user_prompt.lower():
            return "PaymentGW's Q1 2026 total cost was $16,500 (Jan: $4,200 + Feb: $4,800 + Mar: $7,500)."

        if "paymentgw latency" in user_prompt.lower() and "sla" in user_prompt.lower():
            return "PaymentGW's latency SLA (target) is 200ms p99. Current latency is approximately 185ms, which is within SLA."

        # Default: just acknowledge the question
        return f"I found relevant information about your question: {user_prompt[:100]}..."


class BedrockLLM:
    """Real LLM via AWS Bedrock"""

    def __init__(self):
        try:
            import boto3

            self.client = boto3.client("bedrock-runtime")
            self.model_id = BEDROCK_MODEL_ID
            logger.info(f"Initialized Bedrock LLM: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock LLM: {e}")
            raise

    def invoke(self, system_prompt: str, user_prompt: str, messages: List[Dict] = None) -> str:
        """Call Claude via Bedrock Converse API"""
        try:
            # Prepare messages for Converse API
            if messages is None:
                msgs = [{"role": "user", "content": [{"text": user_prompt}]}]
            else:
                # Converse API expects content to be a list of parts
                msgs = []
                for m in messages:
                    if isinstance(m.get("content"), str):
                        msgs.append({"role": m["role"], "content": [{"text": m["content"]}]})
                    else:
                        msgs.append(m)

            response = self.client.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=msgs,
                inferenceConfig={
                    "maxTokens": LLM_MAX_TOKENS,
                    "temperature": LLM_TEMPERATURE,
                }
            )

            return response["output"]["message"]["content"][0]["text"]
        except Exception as e:
            logger.error(f"Bedrock LLM error: {e}")
            raise


class L1Retriever:
    """L1: Simple document retrieval with LLM augmentation"""

    def __init__(self):
        # Initialize LLM based on mode
        if MODE == "mock" or not AWS_ENABLED:
            self.llm = MockLLM()
            logger.info("Using Mock LLM (no AWS credentials)")
        else:
            try:
                self.llm = BedrockLLM()
            except Exception as e:
                logger.warning(f"Bedrock LLM initialization failed: {e}, falling back to Mock LLM")
                self.llm = MockLLM()

        # Initialize Bedrock Agent client for retrieval
        self.bedrock_agent_runtime = None
        if MODE == "cloud" and AWS_ENABLED and BEDROCK_KB_ID:
            try:
                import boto3
                self.bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")
                logger.info(f"Initialized Bedrock Agent Runtime for KB: {BEDROCK_KB_ID}")
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock Agent Runtime: {e}")

    def retrieve_chunks(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge base chunks for query"""
        if top_k is None:
            top_k = RETRIEVAL_K

        start_time = time.time()
        chunks = []

        # Strategy 1: Use Bedrock Knowledge Base (Cloud Mode)
        if self.bedrock_agent_runtime and BEDROCK_KB_ID:
            try:
                logger.info(f"Retrieving from Bedrock KB: {BEDROCK_KB_ID}")
                response = self.bedrock_agent_runtime.retrieve(
                    knowledgeBaseId=BEDROCK_KB_ID,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': top_k
                        }
                    }
                )

                for result in response.get('retrievalResults', []):
                    # Extract source from S3 URI or metadata
                    s3_uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
                    source = s3_uri.split('/')[-1] if s3_uri else "unknown_source"
                    
                    chunks.append({
                        "source": source,
                        "content": result.get('content', {}).get('text', ''),
                        "relevance_score": result.get('score', 0),
                        "title": source.replace(".md", "").replace("_", " ").title()
                    })
            except Exception as e:
                logger.error(f"Bedrock KB retrieval failed: {e}")

        # Strategy 2: Fallback to local KB if cloud fails or in local mode
        if not chunks:
            logger.info("Retrieving from local Knowledge Base")
            results = kb.retrieve(query, top_k=top_k)
            for doc, score in results:
                chunks.append({
                    "source": doc.filename,
                    "title": doc.title,
                    "content": doc.content,
                    "relevance_score": score,
                    "summary": doc.summary,
                })

        duration = (time.time() - start_time) * 1000
        logger.info(
            f"Retrieved {len(chunks)} chunks for query in {duration:.2f}ms",
            extra={"query": query, "chunk_count": len(chunks)},
        )

        return chunks

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        L1 pipeline: Retrieve → Augment → Generate
        Returns answer with source citations
        """
        logger.info(f"L1: Processing question: {question}")

        # Step 1: Retrieve chunks
        chunks = self.retrieve_chunks(question, top_k=RETRIEVAL_K)

        if not chunks:
            logger.warning(f"No chunks retrieved for: {question}")
            return {
                "answer": "I couldn't find relevant information in the knowledge base for your question.",
                "sources": [],
                "level": "L1",
                "success": False,
            }

        # Step 2: Build context from chunks
        context_parts = []
        sources = []
        for chunk in chunks:
            context_parts.append(f"[Source: {chunk['source']}]\n{chunk['content']}")
            sources.append(chunk["source"])

        context = "\n\n".join(context_parts)

        # Step 3: Build system prompt for L1 (simple retrieval)
        system_prompt = """You are a helpful assistant answering questions about GeekBrain infrastructure.

Rules:
- Answer ONLY using the provided context
- Always cite the source document name
- Be concise and accurate
- If you don't know the answer, say so clearly
- Do not make up or hallucinate information"""

        # Step 4: Build user prompt
        user_prompt = f"""Question: {question}

Context from knowledge base:
{context}

Please answer the question based on the context above. Always cite the source document."""

        # Step 5: Call LLM
        answer = self.llm.invoke(system_prompt, user_prompt)

        logger.info(f"L1 Answer: {answer[:100]}...")

        return {
            "answer": answer,
            "sources": list(set(sources)),  # Remove duplicates
            "chunks_retrieved": len(chunks),
            "level": "L1",
            "success": True,
        }


class L2Retriever(L1Retriever):
    """L2: Multi-source retrieval with conflict resolution"""

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        L2 pipeline: Retrieve (more chunks) → Detect conflicts → Generate
        Handles multi-document synthesis and conflict resolution
        """
        logger.info(f"L2: Processing question: {question}")

        # Step 1: Retrieve MORE chunks (L2 needs more sources)
        chunks = self.retrieve_chunks(question, top_k=min(15, RETRIEVAL_K * 2))

        if not chunks:
            logger.warning(f"No chunks retrieved for: {question}")
            return {
                "answer": "I couldn't find relevant information in the knowledge base for your question.",
                "sources": [],
                "level": "L2",
                "success": False,
            }

        # Step 2: Check for conflicts (different versions, dates, etc.)
        conflicts = self._detect_conflicts(chunks, question)

        # Step 3: Build context with conflict annotations
        context_parts = []
        sources = []
        for chunk in chunks:
            annotation = ""
            # Annotate archived/old documents
            if "archived" in chunk["source"].lower():
                annotation = " [ARCHIVED]"
            elif "v1" in chunk["source"].lower():
                annotation = " [v1 - OLD]"

            context_parts.append(
                f"[Source: {chunk['source']}{annotation}]\n{chunk['content']}"
            )
            sources.append(chunk["source"])

        context = "\n\n".join(context_parts)

        # Step 4: Build system prompt for L2 (conflict resolution)
        system_prompt = """You are an expert assistant analyzing GeekBrain infrastructure.

When multiple documents provide different information:
1. Check dates, version numbers, and document status
2. Prefer NEWER versions over older versions
3. Prefer non-archived documents
4. If you find a conflict, explain which source you're using and why

Rules:
- Answer ONLY using the provided context
- Always cite source documents
- When sources conflict, explain the conflict and state your resolution
- Be concise and accurate"""

        # Step 5: Build user prompt mentioning conflicts if found
        conflict_note = ""
        if conflicts:
            conflict_note = f"\n\nNOTE: I found potential conflicts between sources. Please resolve them:\n"
            conflict_note += "\n".join(conflicts)

        user_prompt = f"""Question: {question}{conflict_note}

Context from knowledge base:
{context}

Please answer using the context above. If multiple sources conflict, explain which you prefer and why."""

        # Step 6: Call LLM
        answer = self.llm.invoke(system_prompt, user_prompt)

        logger.info(f"L2 Answer: {answer[:100]}...")

        return {
            "answer": answer,
            "sources": list(set(sources)),
            "chunks_retrieved": len(chunks),
            "conflicts": conflicts,
            "level": "L2",
            "success": True,
        }

    def _detect_conflicts(self, chunks: List[Dict], question: str) -> List[str]:
        """Detect potential conflicts between retrieved documents"""
        conflicts = []

        # Check for version conflicts (v1 vs v2)
        sources_by_type = {}
        for chunk in chunks:
            source_type = chunk["source"].replace("_v1", "").replace("_v2", "").replace("_archived", "")
            if source_type not in sources_by_type:
                sources_by_type[source_type] = []
            sources_by_type[source_type].append(chunk["source"])

        for source_type, versions in sources_by_type.items():
            if len(versions) > 1:
                conflicts.append(f"Multiple versions found for {source_type}: {', '.join(versions)}")

        # Check for archived documents
        archived = [c["source"] for c in chunks if "archived" in c["source"].lower()]
        if archived:
            conflicts.append(f"Found archived documents (may be outdated): {', '.join(archived)}")

        return conflicts
