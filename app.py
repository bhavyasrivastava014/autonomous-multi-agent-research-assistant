# app.py
import streamlit as st
import time
from agent import ResearchAgent
from knowledge_base import ResearchKnowledgeBase

# Page configuration
st.set_page_config(
    page_title="Autonomous Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #374151;
        margin-top: 1.5rem;
    }
    .source-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #3B82F6;
    }
    .stButton button {
        width: 100%;
        background-color: #3B82F6;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = ResearchAgent()
    st.session_state.kb = ResearchKnowledgeBase()
    st.session_state.research_history = []

# Header
st.markdown('<h1 class="main-header">🤖 Autonomous Research Assistant</h1>', unsafe_allow_html=True)
st.markdown("### An AI-powered system for automated information retrieval and synthesis")

# Sidebar
with st.sidebar:
    st.markdown("### 🔧 Settings")
    
    max_results = st.slider("Max results per search", 3, 10, 5)
    
    st.markdown("---")
    st.markdown("### 📊 Knowledge Base")
    
    if st.button("View KB Stats"):
        stats = st.session_state.kb.get_statistics()
        st.info(f"📚 Documents: {stats['total_documents']}")
    
    st.markdown("---")
    st.markdown("### 🧭 Quick Queries")
    
    quick_queries = [
        "What is agentic AI?",
        "Latest developments in quantum computing",
        "Explain LangGraph architecture",
        "Multi-agent systems tutorial"
    ]
    
    for q in quick_queries:
        if st.button(f"🔍 {q}"):
            st.session_state.research_input = q

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Research Query")
    
    # Query input
    query = st.text_area(
        "Enter your research question:",
        height=120,
        placeholder="e.g., 'Explain the concept of multi-agent systems with recent examples'",
        key="research_input"
    )
    
    # Research button
    col1_1, col1_2 = st.columns(2)
    with col1_1:
        research_btn = st.button("🚀 Start Research", type="primary", use_container_width=True)
    with col1_2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)

with col2:
    st.markdown("### ℹ️ How it works")
    st.info("""
    1. **Search**: Queries multiple sources
    2. **Analyze**: Extracts key information
    3. **Synthesize**: Combines findings
    4. **Cite**: Provides all sources
    """)
    
    st.markdown("### ⚡ Features")
    st.markdown("""
    - 🔍 Multi-source search
    - 🧠 Knowledge caching
    - 📚 Source tracking
    - 🔄 Self-improving
    """)

# Handle research request
if research_btn and query:
    with st.spinner("🔍 Searching the web..."):
        time.sleep(0.5)  # Simulate processing
        
        # Check knowledge base first
        similar = st.session_state.kb.find_similar_research(query)
        
        if similar:
            st.success("📚 Found similar past research!")
            with st.expander("View similar research"):
                for research in similar[:2]:
                    st.markdown(f"**Query:** {research['query']}")
                    st.markdown(f"**Summary:** {research['summary'][:200]}...")
                    st.markdown("---")
        
        # Perform new research
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        
        result = st.session_state.agent.research(query, max_results=max_results)
        
        # Store in knowledge base
        st.session_state.kb.store_research(query, result)
        
        # Add to history
        st.session_state.research_history.append({
            "query": query,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sources_count": len(result.get("sources", []))
        })
    
    # Display results
    st.markdown("---")
    st.markdown('<h2 class="sub-header">📊 Research Results</h2>', unsafe_allow_html=True)
    
    if result["status"] == "success":
        # Summary
        with st.expander("📝 Executive Summary", expanded=True):
            st.write(result["summary"])
        
        # Sources
        st.markdown("### 🔗 Sources Found")
        for source in result["sources"]:
            with st.container():
                st.markdown(f"""
                <div class="source-card">
                    <h4>📄 {source['title']}</h4>
                    <p><em>Rank: #{source['rank']}</em></p>
                    <p>{source['preview']}</p>
                    <p><small><a href="{source['url']}" target="_blank">🔗 Visit Source</a></small></p>
                </div>
                """, unsafe_allow_html=True)
        
        # Stats
        st.markdown("### 📈 Statistics")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Total Sources", result["stats"]["total_sources"])
        with col_stat2:
            st.metric("Sources Used", result["stats"]["top_sources_used"])
        with col_stat3:
            st.metric("Status", "Completed")
    
    else:
        st.error("❌ No results found. Try rephrasing your query.")

# Handle clear
if clear_btn:
    st.session_state.research_input = ""
    st.rerun()

# Research History
if st.session_state.research_history:
    st.markdown("---")
    st.markdown("### 📜 Recent Research")
    
    history_cols = st.columns(3)
    for i, item in enumerate(st.session_state.research_history[-3:]):
        with history_cols[i % 3]:
            st.info(f"""
            **Query:** {item['query'][:50]}...
            \n**When:** {item['timestamp']}
            \n**Sources:** {item['sources_count']}
            """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6B7280;'>"
    "🤖 Autonomous Research Assistant | Built with Python & Streamlit"
    "</div>",
    unsafe_allow_html=True
)

# Quick run test
if __name__ == "__main__":
    # This allows you to run: streamlit run app.py
    pass
