"""Streamlit UI for the research assistant."""

from __future__ import annotations

import asyncio

import streamlit as st

from src.agents.research_agent import ResearchAgent
from src.core.config import settings
from src.core.logger import logger, setup_logger
from src.exceptions import ResearchError
from src.services.kb_service import KBService


AGENT_STATE_VERSION = 2


def _run_async(coro):
    return asyncio.run(coro)


def _init_state() -> None:
    setup_logger()
    if st.session_state.get("agent_state_version") != AGENT_STATE_VERSION:
        st.session_state.agent = ResearchAgent()
        st.session_state.agent_state_version = AGENT_STATE_VERSION
    if "kb" not in st.session_state:
        st.session_state.kb = KBService()
    if "history" not in st.session_state:
        st.session_state.history = []


def main() -> None:
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        .main-header { font-size: 2.5rem; color: #1E3A8A; text-align: center; }
        .source-card { background: #F3F4F6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border-left: 4px solid #3B82F6; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _init_state()
    logger.info("Streamlit app started")

    st.markdown('<h1 class="main-header">Autonomous Research Assistant</h1>', unsafe_allow_html=True)
    st.caption("Modular architecture with semantic memory, logging, and optional LLM synthesis")

    with st.sidebar:
        st.header("Settings")
        max_results = st.slider("Max Results", 3, 10, settings.search_max_results)

        st.header("Knowledge Base")
        if st.button("Refresh Stats"):
            try:
                stats = st.session_state.kb.get_statistics()
                st.metric("Documents", stats["total_documents"])
            except Exception as exc:
                st.error(f"Could not load KB stats: {exc}")

        st.header("LLM")
        provider = settings.llm_provider.upper()
        if settings.active_llm_api_key:
            st.success(f"{provider} synthesis enabled")
        else:
            st.warning("LLM key missing, extractive fallback will be used")

    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_area("Research Query", height=120, placeholder="Ask a research question...")
        run_research = st.button("Start Research", type="primary")
    with col2:
        st.info(
            "Pipeline:\n"
            "1. Search the web\n"
            "2. Reuse similar cached research\n"
            "3. Synthesize findings\n"
            "4. Persist the result"
        )

    if run_research and query:
        with st.spinner("Researching..."):
            try:
                result = _run_async(st.session_state.agent.research(query, max_results))
            except ResearchError as exc:
                logger.warning("Research failed: {}", exc)
                st.error(str(exc))
            except Exception as exc:
                logger.exception("Unexpected UI error")
                st.error(f"Unexpected error: {exc}")
            else:
                st.success("Research complete")
                st.markdown("### Executive Summary")
                st.write(result.summary)

                if result.related_research:
                    with st.expander("Similar previous research"):
                        for item in result.related_research[:2]:
                            st.write(f"**{item['query']}** ({item['similarity_score']:.2f})")
                            st.write(item["summary"][:300])

                st.markdown("### Sources")
                for source in result.sources:
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <h4>#{source.rank} {source.title}</h4>
                            <a href="{source.url}" target="_blank">{source.url}</a>
                            <p>{source.preview}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                metric1, metric2, metric3 = st.columns(3)
                with metric1:
                    st.metric("Sources", result.stats.total_sources)
                with metric2:
                    st.metric("Used", result.stats.top_sources_used)
                with metric3:
                    st.metric("Synthesis", result.stats.synthesis_strategy)

                st.session_state.history.append(
                    {
                        "query": query,
                        "status": result.status,
                        "timestamp": result.stats.timestamp.isoformat(),
                    }
                )

    if st.session_state.history:
        st.markdown("### History")
        for item in st.session_state.history[-5:]:
            st.caption(f"- {item['query'][:60]} ({item['status']})")

    st.markdown("---")
    st.caption(f"Logs: {settings.log_file}")


if __name__ == "__main__":
    main()
