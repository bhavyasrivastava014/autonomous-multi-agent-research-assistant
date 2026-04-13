"""LLM synthesis service with graceful fallback."""

from __future__ import annotations

from typing import Iterable, Optional

from src.core.config import settings
from src.core.logger import logger
from src.exceptions import LLMError
from src.models.schemas import SearchResult
from src.utils.helpers import retry_on_error


class LLMService:
    """Creates executive summaries from search evidence."""

    def __init__(self, client: object | None = None):
        self.client = client

    @retry_on_error(max_attempts=2, exceptions=(LLMError,))
    async def synthesize(
        self,
        query: str,
        search_results: Iterable[SearchResult],
        related_research: Optional[list[dict]] = None,
    ) -> str:
        results = list(search_results)
        if not results:
            raise LLMError("No search results available for synthesis.", model=settings.llm_model)

        if not settings.llm_enabled or not settings.active_llm_api_key:
            logger.info("LLM disabled or API key missing; using extractive fallback")
            return self._fallback_summary(results, related_research or [])

        prompt = self._build_prompt(query, results, related_research or [])

        try:
            if settings.llm_provider.lower() == "groq":
                client = self.client
                if client is None:
                    from groq import AsyncGroq

                    client = AsyncGroq(api_key=settings.groq_api_key)
                response = await client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You write concise, evidence-grounded research summaries."},
                        {"role": "user", "content": prompt},
                    ],
                    model=settings.llm_model,
                    temperature=settings.llm_temperature,
                    max_tokens=900,
                )
                synthesis = response.choices[0].message.content or ""
            elif settings.llm_provider.lower() == "openai":
                client = self.client
                if client is None:
                    from openai import AsyncOpenAI

                    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.search_timeout)
                response = await client.responses.create(model=settings.llm_model, input=prompt)
                synthesis = getattr(response, "output_text", "") or ""
            else:
                raise LLMError(f"Unsupported provider: {settings.llm_provider}", model=settings.llm_model)

            synthesis = synthesis.strip()
            if not synthesis:
                raise LLMError("Empty response returned by LLM.", model=settings.llm_model)

            logger.info("LLM synthesis complete")
            return synthesis
        except LLMError:
            raise
        except Exception as exc:
            logger.exception("LLM synthesis failed")
            raise LLMError(str(exc), model=settings.llm_model) from exc

    def _build_prompt(
        self,
        query: str,
        search_results: list[SearchResult],
        related_research: list[dict],
    ) -> str:
        source_context = "\n\n".join(
            [
                f"Source {index}\nTitle: {result.title}\nURL: {result.url}\nSnippet: {result.snippet[:500]}"
                for index, result in enumerate(search_results[:5], start=1)
            ]
        )
        history_context = ""
        if related_research:
            history_context = "\n\nPrevious relevant research:\n" + "\n".join(
                [
                    f"- Query: {item['query']}\n  Summary: {item['summary'][:280]}"
                    for item in related_research[:2]
                ]
            )
        return (
            "Create a concise executive summary that answers the question, highlights common themes, "
            "and mentions uncertainty when evidence is weak.\n\n"
            f"Question: {query}\n\n"
            f"Evidence:\n{source_context}{history_context}"
        )

    def _fallback_summary(self, search_results: list[SearchResult], related_research: list[dict]) -> str:
        lines = ["Executive summary:"]
        for result in search_results[:3]:
            lines.append(f"- {result.title}: {result.snippet[:220]}")
        if related_research:
            lines.append("")
            lines.append("Related prior research:")
            for item in related_research[:2]:
                lines.append(f"- {item['query']}: {item['summary'][:180]}")
        lines.append("")
        lines.append("Note: This summary uses the built-in fallback because an LLM is not configured.")
        return "\n".join(lines)
