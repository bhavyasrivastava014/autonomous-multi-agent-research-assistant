# agent.py
from dataclasses import dataclass
from typing import List, Dict, Any
from duckduckgo_search import DDGS
import time

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    content: str = ""
    timestamp: str = ""

class ResearchAgent:
    def __init__(self):
        self.search_client = DDGS()
        self.session_history = []
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform web search and return results"""
        print(f"🔍 Searching for: {query}")
        
        try:
            results = []
            search_response = self.search_client.text(query, max_results=max_results)
            
            for item in search_response:
                result = SearchResult(
                    title=item.get('title', 'No Title'),
                    url=item.get('href', ''),
                    snippet=item.get('body', ''),
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                result.content = f"{result.title}. {result.snippet}"
                results.append(result)
            
            # Log to history
            self.session_history.append({
                "query": query,
                "results_count": len(results),
                "timestamp": time.time()
            })
            
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def extract_key_info(self, results: List[SearchResult]) -> str:
        """Extract key information from search results"""
        if not results:
            return "No information found."
        
        # Combine content from top results
        combined_content = "\n\n---\n\n".join([
            f"Source: {r.title}\nURL: {r.url}\nContent: {r.snippet[:300]}..."
            for r in results[:3]
        ])
        
        # Simple summary (in real project, use LLM here)
        summary_parts = []
        for r in results[:3]:
            summary_parts.append(f"• {r.title}: {r.snippet[:150]}...")
        
        return "\n".join(summary_parts)
    
    def research(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Main research pipeline"""
        print(f"\n🚀 Starting research: {query}")
        print("-" * 50)
        
        # Step 1: Search
        search_results = self.search(query, max_results=max_results)
        
        # Step 2: Extract information
        if search_results:
            summary = self.extract_key_info(search_results)
            
            # Format response
            response = {
                "status": "success",
                "query": query,
                "summary": summary,
                "sources": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "preview": r.snippet[:200] + "...",
                        "rank": i + 1
                    }
                    for i, r in enumerate(search_results[:5])
                ],
                "stats": {
                    "total_sources": len(search_results),
                    "top_sources_used": min(5, len(search_results)),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        else:
            response = {
                "status": "error",
                "query": query,
                "summary": "No results found for this query.",
                "sources": [],
                "stats": {"total_sources": 0, "top_sources_used": 0}
            }
        
        return response

# Quick test function
def test_agent():
    """Test the agent"""
    print("🧪 Testing Research Agent...")
    agent = ResearchAgent()
    
    # Test with a simple query
    test_query = "What is LangGraph?"
    result = agent.research(test_query)
    
    print(f"\n📊 Results for: {result['query']}")
    print(f"Status: {result['status']}")
    print(f"\n📝 Summary:\n{result['summary']}")
    
    if result['sources']:
        print(f"\n🔗 Top Sources:")
        for source in result['sources'][:2]:
            print(f"  {source['rank']}. {source['title']}")
            print(f"     URL: {source['url']}")
            print(f"     Preview: {source['preview']}")
            print()

if __name__ == "__main__":
    test_agent()
