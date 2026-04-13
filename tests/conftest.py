"""Pytest fixtures."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock
from ..src.core.config import settings
from ..src.services.search_service import SearchService
from ..src.services.llm_service import LLMService
from ..src.services.kb_service import KBService
from ..src.agents.research_agent import ResearchAgent

@pytest.fixture
def mock_config():
    settings.groq_api_key = "test-key"

@pytest_asyncio.fixture
async def mock_search_service():
    service = Mock(spec=SearchService)
    service.search.return_value = AsyncMock(return_value=[
        {"title": "Test", "href": "http://test.com", "body": "test snippet"}
    ])
    return service

@pytest_asyncio.fixture
async def mock_llm_service():
    service = Mock(spec=LLMService)
    service.synthesize.return_value = AsyncMock(return_value="Test synthesis")
    return service

@pytest_asyncio.fixture
async def mock_kb_service():
    service = Mock(spec=KBService)
    return service

@pytest_asyncio.fixture
async def test_agent(mock_search_service, mock_llm_service, mock_kb_service):
    agent = ResearchAgent()
    agent.search = mock_search_service
    agent.llm = mock_llm_service
    agent.kb = mock_kb_service
    return agent

