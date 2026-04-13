"""Custom exceptions for the research agent."""
from typing import Optional

class ResearchError(Exception):
    """Base exception for research agent errors."""

class SearchError(ResearchError):
    """Search-related errors."""
    def __init__(self, message: str, source: Optional[str] = None):
        self.source = source
        super().__init__(f"Search error ({source}): {message}")

class LLMError(ResearchError):
    """LLM service errors."""
    def __init__(self, message: str, model: Optional[str] = None):
        self.model = model
        super().__init__(f"LLM error ({model}): {message}")

class KnowledgeBaseError(ResearchError):
    """Knowledge base errors."""
    pass

class ConfigError(ResearchError):
    """Configuration errors."""
    pass

