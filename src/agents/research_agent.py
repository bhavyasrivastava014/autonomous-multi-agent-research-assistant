"""Main research agent orchestrating services."""

from __future__ import annotations

from typing import Optional

from src.core.config import settings
from src.core.logger import logger
from src.exceptions import KnowledgeBaseError, LLMError, ResearchError, SearchError
from src.models.schemas import ResearchResponse, Source, Stats
from src.services.kb_service import KBService
from src.services.llm_service import LLMService
from src.services.search_service import SearchService
from src.utils.helpers import time_execution


class ResearchAgent:
    """Coordinates search, synthesis, and persistence."""

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        llm_service: Optional[LLMService] = None,
        kb_service: Optional[KBService] = None,
    ):
        self.search = search_service or SearchService()
        self.llm = llm_service or LLMService()
        self.kb = kb_service or KBService()
        self.session_history: list[dict] = []

    @time_execution
    async def research(self, query: str, max_results: int | None = None) -> ResearchResponse:
        query = query.strip()
        if not query:
            raise ResearchError("Query cannot be empty.")

        if max_results is None:
            max_results = settings.search_max_results

        logger.info("Starting research for '{}'", query)

        related_research = []
        try:
            related_research = self.kb.find_similar_research(query)
        except KnowledgeBaseError:
            logger.warning("Continuing without similar research context", exc_info=True)

        try:
            search_results = await self.search.search(query, max_results)
        except SearchError as exc:
            logger.exception("Search stage failed")
            raise ResearchError(f"Search failed: {exc}") from exc

        if search_results:
            try:
                summary = await self.llm.synthesize(query, search_results, related_research)
                synthesis_strategy = "llm" if settings.llm_enabled and settings.active_llm_api_key else "extractive"
            except LLMError:
                logger.warning("Falling back after LLM failure", exc_info=True)
                summary = self.llm._fallback_summary(search_results, related_research)
                synthesis_strategy = "extractive"
        else:
            logger.warning("Search returned no results for '{}'; using no-results fallback", query)
            summary, synthesis_strategy = await self._synthesize_without_search_results(query, related_research)

        sources = self._build_sources(search_results)

        response = ResearchResponse(
            status="success",
            query=query,
            summary=summary,
            sources=sources,
            stats=Stats(
                total_sources=len(search_results),
                top_sources_used=len(sources),
                synthesis_strategy=synthesis_strategy,
                used_cached_context=bool(related_research),
            ),
            related_research=related_research,
        )

        try:
            self.kb.store_research(query, response.model_dump(mode="json"))
        except KnowledgeBaseError:
            logger.warning("Research completed but cache write failed", exc_info=True)

        self.session_history.append(
            {
                "query": query,
                "sources_count": len(search_results),
                "timestamp": response.stats.timestamp.isoformat(),
            }
        )

        logger.info("Research completed with {} sources", len(sources))
        return response

    async def _synthesize_without_search_results(
        self,
        query: str,
        related_research: list[dict],
    ) -> tuple[str, str]:
        if settings.llm_enabled and settings.active_llm_api_key:
            try:
                summary = await self._llm_summary_without_search(query, related_research)
                return summary, "llm_no_search_fallback"
            except LLMError:
                logger.warning("LLM no-search fallback failed", exc_info=True)

        return self._build_no_results_summary(query, related_research), "no_search_fallback"

    async def _llm_summary_without_search(self, query: str, related_research: list[dict]) -> str:
        history_context = ""
        if related_research:
            history_context = "\n\nRelevant cached research:\n" + "\n".join(
                [
                    f"- Query: {item['query']}\n  Summary: {item['summary'][:280]}"
                    for item in related_research[:2]
                ]
            )

        prompt = (
            "No live web search results were available for this request.\n"
            "Answer the question cautiously using general knowledge and any cached context below.\n"
            "State clearly that the answer could not be verified with live search and avoid fabricated citations.\n\n"
            f"Question: {query}{history_context}"
        )

        try:
            if settings.llm_provider.lower() == "groq":
                client = self.llm.client
                if client is None:
                    from groq import AsyncGroq

                    client = AsyncGroq(api_key=settings.groq_api_key)
                response = await client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a careful research assistant. Be transparent about uncertainty.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    model=settings.llm_model,
                    temperature=settings.llm_temperature,
                    max_tokens=700,
                )
                synthesis = response.choices[0].message.content or ""
            elif settings.llm_provider.lower() == "openai":
                client = self.llm.client
                if client is None:
                    from openai import AsyncOpenAI

                    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.search_timeout)
                response = await client.responses.create(model=settings.llm_model, input=prompt)
                synthesis = getattr(response, "output_text", "") or ""
            else:
                raise LLMError(f"Unsupported provider: {settings.llm_provider}", model=settings.llm_model)
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(str(exc), model=settings.llm_model) from exc

        synthesis = synthesis.strip()
        if not synthesis:
            raise LLMError("Empty response returned by LLM.", model=settings.llm_model)

        return synthesis

    def _build_no_results_summary(self, query: str, related_research: list[dict]) -> str:
        lines = [
            f"No live web search results were returned for: {query}",
            "",
            "The app stayed responsive and generated this fallback response instead of stopping at the search step.",
            "This means the answer could not be verified against fresh web sources.",
        ]

        if related_research:
            lines.extend(
                [
                    "",
                    "Relevant cached research:",
                ]
            )
            for item in related_research[:2]:
                lines.append(f"- {item['query']}: {item['summary'][:220]}")
        else:
            lines.extend(
                [
                    "",
                    "No cached research was available either.",
                ]
            )

        lines.extend(
            [
                "",
                "Try a more specific query, check network access, or verify the DuckDuckGo backend availability.",
            ]
        )
        return "\n".join(lines)

    def _build_sources(self, search_results) -> list[Source]:
        return [
            Source(
                title=result.title,
                url=result.url,
                snippet=result.snippet,
                rank=index,
                preview=result.snippet[:200] + ("..." if len(result.snippet) > 200 else ""),
            )
            for index, result in enumerate(search_results[:5], start=1)
        ]
