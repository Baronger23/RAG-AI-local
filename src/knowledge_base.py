"""
Knowledge Base Loader
Load markdown documents from local files (L1-L2 retrieval)
Supports mock (simple keyword search) and local (vector search simulation)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

from config import KNOWLEDGE_BASE_DIR, MODE
from logger import logger


class Document:
    """Represents a knowledge base document"""

    def __init__(self, filename: str, title: str, content: str, tags: List[str] = None):
        self.filename = filename
        self.title = title
        self.content = content
        self.tags = tags or []
        # Extract first 500 chars as summary
        self.summary = content[:500]

    def __repr__(self):
        return f"Document(filename={self.filename}, title={self.title})"


class KnowledgeBase:
    """Load and retrieve documents from knowledge base"""

    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.load_all_documents()
        logger.info(f"Loaded {len(self.documents)} documents from knowledge base")

    def load_all_documents(self):
        """Load all markdown files from knowledge_base directory"""
        if not KNOWLEDGE_BASE_DIR.exists():
            logger.warning(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
            return

        for md_file in KNOWLEDGE_BASE_DIR.glob("*.md"):
            try:
                self.load_document(md_file)
            except Exception as e:
                logger.error(f"Error loading document {md_file}: {e}")

    def load_document(self, filepath: Path):
        """Load a single markdown document"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from frontmatter or filename
        title_match = re.search(r'title:\s*"?([^"\n]+)"?', content)
        title = title_match.group(1) if title_match else filepath.stem

        # Extract tags/keywords from filename
        tags = self._extract_tags_from_filename(filepath.stem)

        doc = Document(
            filename=filepath.name,
            title=title,
            content=content,
            tags=tags,
        )

        self.documents[filepath.name] = doc

    def _extract_tags_from_filename(self, filename: str) -> List[str]:
        """Extract tags from filename for better retrieval"""
        parts = filename.split("_")
        tags = []

        if "service" in filename:
            # Extract service name: service_paymentgw.md -> paymentgw
            for part in parts:
                if part and part not in ["service"]:
                    tags.append(part)

        if "team" in filename:
            # Extract team name: team_platform.md -> platform
            for part in parts:
                if part and part != "team":
                    tags.append(part)

        if "postmortem" in filename:
            tags.append("incident")
            tags.append("postmortem")

        if any(x in filename for x in ["policy", "runbook", "guide", "handbook"]):
            tags.append("policy")

        return tags

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[Document, float]]:
        """
        Retrieve documents matching query (simple keyword matching + tag matching)
        Returns list of (Document, relevance_score) tuples sorted by relevance
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        results = []

        for doc in self.documents.values():
            score = 0.0

            # Keyword matching in content (TF-IDF approximation)
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()

            for term in query_terms:
                # Title match (higher weight)
                if term in title_lower:
                    score += 10.0

                # Content match (lower weight, but frequency-based)
                count = content_lower.count(term)
                score += count * 0.1

            # Tag matching (medium weight)
            for tag in doc.tags:
                if tag in query_terms:
                    score += 5.0

            # Penalize if document is very similar in length (avoid duplicates)
            if score > 0:
                results.append((doc, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def get_document_by_name(self, filename: str) -> Document:
        """Get a specific document by filename"""
        return self.documents.get(filename)

    def list_all_documents(self) -> List[Document]:
        """List all loaded documents"""
        return list(self.documents.values())

    def search_by_service(self, service_name: str) -> List[Document]:
        """Find all documents related to a specific service"""
        service_lower = service_name.lower()
        return [
            doc
            for doc in self.documents.values()
            if service_lower in doc.content.lower()
            or service_lower in [t.lower() for t in doc.tags]
        ]

    def search_by_team(self, team_name: str) -> List[Document]:
        """Find all documents related to a specific team"""
        team_lower = team_name.lower()
        return [
            doc
            for doc in self.documents.values()
            if team_lower in doc.content.lower() or team_lower in [t.lower() for t in doc.tags]
        ]


# Global KB instance
kb = KnowledgeBase()
