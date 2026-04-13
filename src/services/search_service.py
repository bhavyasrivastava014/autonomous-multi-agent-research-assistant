"""Search service using DuckDuckGo HTML endpoints with resilient fallbacks."""

from __future__ import annotations

import asyncio
from typing import Any, Iterable, List, Optional
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from src.core.config import settings
from src.core.logger import logger
from src.exceptions import SearchError
from src.models.schemas import SearchResult
from src.utils.helpers import retry_on_error


class SearchService:
    """Performs web search and normalizes results."""

    def __init__(self, client: Optional[DDGS] = None, session: Optional[requests.Session] = None):
        self.client = client
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    @retry_on_error(max_attempts=3, exceptions=(SearchError,))
    async def search(self, query: str, max_results: int | None = None) -> List[SearchResult]:
        query = query.strip()
        if max_results is None:
            max_results = settings.search_max_results

        logger.info("Searching for '{}'", query)
        if not query:
            return []

        try:
            strategies: list[tuple[str, Any]] = []

            if self.client is not None:
                strategies.append(("injected_ddgs", lambda: self._search_with_client(self.client, query, max_results)))
            else:
                strategies.extend(
                    [
                        ("duckduckgo_html", lambda: self._search_duckduckgo_html(query, max_results)),
                        ("duckduckgo_lite", lambda: self._search_duckduckgo_lite(query, max_results)),
                        ("ddgs_html", lambda: self._search_with_client(DDGS(timeout=settings.search_timeout), query, max_results, "html")),
                        ("ddgs_lite", lambda: self._search_with_client(DDGS(timeout=settings.search_timeout), query, max_results, "lite")),
                    ]
                )

            strategy_errors: list[str] = []
            for strategy_name, strategy in strategies:
                try:
                    raw_results = await asyncio.to_thread(strategy)
                except Exception as exc:
                    logger.warning("Search strategy '{}' failed: {}", strategy_name, exc)
                    strategy_errors.append(f"{strategy_name}: {exc}")
                    continue

                results = self._normalize_results(raw_results)
                if results:
                    logger.info("Search returned {} results using '{}'", len(results), strategy_name)
                    return results

                logger.warning("Search strategy '{}' returned no results", strategy_name)

            if strategy_errors:
                logger.warning("Search strategies encountered errors: {}", "; ".join(strategy_errors))

            logger.warning("Search returned no results for '{}'", query)
            return []
        except Exception as exc:
            logger.exception("Search failed for '{}'", query)
            raise SearchError(str(exc), source="duckduckgo") from exc

    def _search_with_client(
        self,
        client: DDGS,
        query: str,
        max_results: int,
        backend: str | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "keywords": query,
            "max_results": max_results,
            "region": "wt-wt",
            "safesearch": "moderate",
        }
        if backend is not None:
            kwargs["backend"] = backend

        try:
            raw_results = client.text(**kwargs)
        except TypeError:
            # Support simple test doubles that may only accept query/max_results.
            raw_results = client.text(query, max_results=max_results)

        return list(raw_results or [])

    def _search_duckduckgo_html(self, query: str, max_results: int) -> list[dict[str, str]]:
        response = self.session.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "wt-wt"},
            timeout=settings.search_timeout,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []

        for result in soup.select("div.result"):
            title_link = result.select_one("a.result__a")
            snippet_node = result.select_one(".result__snippet")
            if title_link is None:
                continue

            url = self._extract_result_url(title_link.get("href", ""))
            if not url:
                continue

            title = title_link.get_text(" ", strip=True)
            snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
            results.append({"title": title, "href": url, "body": snippet})

            if len(results) >= max_results:
                break

        return results

    def _search_duckduckgo_lite(self, query: str, max_results: int) -> list[dict[str, str]]:
        response = self.session.post(
            "https://lite.duckduckgo.com/lite/",
            data={"q": query, "kl": "wt-wt"},
            timeout=settings.search_timeout,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []
        current: dict[str, str] | None = None

        for row in soup.select("table tr"):
            link = row.select_one("a[href]")
            snippet_cell = row.select_one(".result-snippet")

            if link:
                url = self._extract_result_url(link.get("href", ""))
                if not url:
                    current = None
                    continue

                current = {
                    "title": link.get_text(" ", strip=True),
                    "href": url,
                    "body": "",
                }
                results.append(current)
                if len(results) >= max_results:
                    break
                continue

            if snippet_cell and current is not None:
                current["body"] = snippet_cell.get_text(" ", strip=True)

        return results[:max_results]

    def _extract_result_url(self, raw_url: str) -> str:
        raw_url = raw_url.strip()
        if not raw_url:
            return ""

        parsed = urlparse(raw_url)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            return unquote(target)

        if raw_url.startswith("//"):
            return f"https:{raw_url}"

        return raw_url

    def _normalize_results(self, raw_results: Iterable[dict[str, Any]]) -> List[SearchResult]:
        normalized: list[SearchResult] = []

        for item in raw_results:
            title = (item.get("title") or "No Title").strip()
            url = (item.get("href") or item.get("url") or "").strip()
            snippet = (item.get("body") or item.get("snippet") or "").strip() or "No snippet available."

            if not url:
                logger.debug("Skipping search result without URL: {}", item)
                continue

            try:
                normalized.append(
                    SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        content=f"{title}. {snippet}".strip(),
                    )
                )
            except Exception:
                logger.debug("Skipping invalid search result payload: {}", item, exc_info=True)

        return normalized
