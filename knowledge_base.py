# knowledge_base.py
import chromadb
from sentence_transformers import SentenceTransformer
import json
import hashlib
from typing import List, Dict, Any, Optional
import os

class ResearchKnowledgeBase:
    def __init__(self, persist_directory: str = "./data/knowledge_db"):
        """Initialize knowledge base with vector storage"""
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embedding model
        print("📚 Loading embedding model...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("research_cache")
            print("✅ Loaded existing knowledge base")
        except:
            self.collection = self.client.create_collection("research_cache")
            print("✅ Created new knowledge base")
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for content"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def store_research(self, query: str, research_data: Dict[str, Any]):
        """Store research results in knowledge base"""
        
        # Prepare data
        content = json.dumps({
            "query": query,
            "summary": research_data.get("summary", ""),
            "sources": research_data.get("sources", [])
        })
        
        # Generate embedding
        embedding = self.embedder.encode(content).tolist()
        
        # Generate ID
        doc_id = self._generate_id(query + content)
        
        # Store in collection
        self.collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "query": query,
                "timestamp": research_data.get("stats", {}).get("timestamp", ""),
                "source_count": len(research_data.get("sources", [])),
                "type": "research"
            }],
            ids=[doc_id]
        )
        
        print(f"💾 Stored research in knowledge base: {doc_id}")
        return doc_id
    
    def find_similar_research(self, query: str, threshold: float = 0.7, max_results: int = 3):
        """Find similar past research"""
        
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results
        similar_research = []
        
        if results and results.get('documents'):
            distances = results.get('distances', [[]])
            for i in range(len(results['documents'][0])):
                try:
                    doc_content = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = distances[0][i] if distances and len(distances[0]) > i else None
                    
                    # Parse the document
                    research_data = json.loads(doc_content)

                    # Convert distance to similarity if available (Chroma uses cosine distance by default)
                    similarity = 1.0 - distance if distance is not None else None
                    if similarity is not None and similarity < threshold:
                        continue
                    
                    similar_research.append({
                        "query": research_data["query"],
                        "summary": research_data["summary"],
                        "sources": research_data["sources"][:2],  # Top 2 sources
                        "metadata": metadata,
                        "similarity_score": similarity if similarity is not None else 0.0
                    })
                except:
                    continue
        
        return similar_research
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "status": "active",
                "storage_path": "./data/knowledge_db"
            }
        except:
            return {"total_documents": 0, "status": "inactive"}

# Quick test
if __name__ == "__main__":
    print("🧪 Testing Knowledge Base...")
    
    kb = ResearchKnowledgeBase()
    
    # Test storing
    test_data = {
        "summary": "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
        "sources": [
            {"title": "LangGraph Docs", "url": "https://example.com", "preview": "..."}
        ],
        "stats": {"timestamp": "2024-01-01 12:00:00"}
    }
    
    doc_id = kb.store_research("What is LangGraph?", test_data)
    print(f"Stored with ID: {doc_id}")
    
    # Test retrieval
    similar = kb.find_similar_research("Tell me about LangGraph")
    print(f"Found {len(similar)} similar research entries")
    
    # Get stats
    stats = kb.get_statistics()
    print(f"Knowledge Base Stats: {stats}")
