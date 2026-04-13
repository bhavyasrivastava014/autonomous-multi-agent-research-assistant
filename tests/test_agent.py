"""Integration tests for ResearchAgent."""
import pytest
from ..src.agents.research_agent import ResearchAgent
from ..src.models.schemas import ResearchResponse

@pytest.mark.asyncio
async def test_research_agent(test_agent):
    """Test full agent research pipeline."""
    result = await test_agent.research("test query")
    
    assert isinstance(result, ResearchResponse)
    assert result.status == "success"
    assert len(result.sources) > 0
    assert result.summary

@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test error handling."""
    agent = ResearchAgent()
    # Mock to raise error
    with pytest.raises(Exception):
        await agent.research("error query")

