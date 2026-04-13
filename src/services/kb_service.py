"""Knowledge base service wrapping ChromaDB."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from src.core.config import settings
from src.core.logger import logger
from src.exceptions import KnowledgeBaseError


class KBService:
    """Persistent semantic cache for previous research."""

    def __init__(
        self,
        embedder: Optional[SentenceTransformer] = None,
        client: Optional[chromadb.PersistentClient] = None,
    ):
        self.persist_dir = settings.knowledge_db_path
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.embedder = embedder or SentenceTransformer(settings.embedding_model)
            self.client = client or chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.client.get_or_create_collection("research_cache")
            logger.info("Knowledge base initialized at {}", self.persist_dir)
        except Exception as exc:
            logger.exception("Knowledge base initialization failed")
            raise KnowledgeBaseError("Failed to initialize knowledge base") from exc

    def _generate_id(self, content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()[:16]

    def store_research(self, query: str, research_data: Dict[str, Any]) -> str:
        try:
            content = json.dumps(
                {
                    "query": query,
                    "summary": research_data.get("summary", ""),
                    "sources": research_data.get("sources", []),
                },
                ensure_ascii=False,
            )
            embedding = self.embedder.encode(content).tolist()
            doc_id = self._generate_id(query + content)
            self.collection.upsert(
                embeddings=[embedding],
                documents=[content],
                metadatas=[
                    {
                        "query": query,
                        "timestamp": str(research_data.get("stats", {}).get("timestamp", "")),
                        "source_count": len(research_data.get("sources", [])),
                        "type": "research",
                    }
                ],
                ids=[doc_id],
            )
            logger.info("Stored research record {}", doc_id)
            return doc_id
        except Exception as exc:
            logger.exception("Failed to store research")
            raise KnowledgeBaseError("Failed to store research") from exc

    def find_similar_research(
        self,
        query: str,
        threshold: float | None = None,
        max_results: int = 3,
    ) -> List[Dict[str, Any]]:
        try:
            threshold = threshold if threshold is not None else settings.similarity_threshold
            query_embedding = self.embedder.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                include=["documents", "metadatas", "distances"],
            )
            similar: List[Dict[str, Any]] = []
            documents = results.get("documents") or [[]]
            metadatas = results.get("metadatas") or [[]]
            distances = results.get("distances") or [[]]

            for index, doc_content in enumerate(documents[0]):
                try:
                    similarity = 1.0 - distances[0][index]
                    if similarity < threshold:
                        continue
                    data = json.loads(doc_content)
                    similar.append(
                        {
                            "query": data["query"],
                            "summary": data["summary"],
                            "sources": data.get("sources", [])[:2],
                            "similarity_score": similarity,
                            "metadata": metadatas[0][index],
                        }
                    )
                except Exception:
                    logger.warning("Skipping malformed knowledge base record", exc_info=True)
            return similar
        except Exception as exc:
            logger.exception("Knowledge base similarity lookup failed")
            raise KnowledgeBaseError("Failed to query knowledge base") from exc

    def get_statistics(self) -> Dict[str, Any]:
        try:
            return {
                "total_documents": self.collection.count(),
                "status": "active",
                "storage_path": str(self.persist_dir),
            }
        except Exception as exc:
            logger.exception("Knowledge base statistics failed")
            raise KnowledgeBaseError("Failed to get statistics") from exc
