"""Unit tests for services."""
import pytest
from unittest.mock import patch, AsyncMock
from src.services.search_service import SearchService
from src.services.llm_service import LLMService
from src.services.kb_service import KBService

@pytest.mark.asyncio
async def test_search_service(mock_search_service):
    """Test search service."""
    service = SearchService()
    results = await service.search("test query")
    assert len(results) > 0
    assert 'title' in results[0]

@pytest.mark.asyncio
async def test_llm_service():
    """Test LLM service (mocked)."""
    with patch('src.services.llm_service.AsyncGroq') as MockGroq:
        mock_client = MockGroq.return_value
        mock_client.chat.completions.create.return_value = AsyncMock(choices=[AsyncMock(message=AsyncMock(content="test"))])
        
        service = LLMService()
        synthesis = await service.synthesize("test", [])
        assert "test" in synthesis

def test_kb_service(mock_kb_service):
    """Test KB service."""
    service = KBService()
    stats = service.get_statistics()
    assert isinstance(stats, dict)

