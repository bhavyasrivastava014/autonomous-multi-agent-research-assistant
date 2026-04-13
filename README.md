# 🤖 Autonomous Research Agent - Production Ready

## 🎯 Features
- **Modular Architecture**: Services (search/llm/kb), agents, models, config/logging
- **LLM Synthesis**: Groq Llama3 for intelligent summaries
- **Async Pipeline**: Fast concurrent search + synthesis
- **Vector KB**: ChromaDB persistence + similarity search
- **Error Handling/Retries**: Custom exceptions, tenacity
- **Structured Logging**: loguru (console/file/JSON)
- **Pydantic Validation**: Schemas for all data
- **Tests**: pytest (80%+ coverage)
- **Streamlit UI**: Production-ready interface

## 🚀 Quick Start
1. **Setup .env**:
   ```
   cp .env.example .env
   # Edit .env: Add GROQ_API_KEY from https://console.groq.com/keys
   ```

2. **Install**:
   ```
   pip install -r requirements.txt
   ```

3. **Run**:
   ```
   streamlit run src/api/app.py
   ```
   Open http://localhost:8501

4. **Test**:
   ```
   pytest --cov=src --cov-report=html
   ```

## 🏗️ Architecture
```
AutonomousResearchAgent/
├── src/
│   ├── core/ (config, logger)
│   ├── models/ (pydantic schemas)
│   ├── services/ (search, llm, kb)
│   ├── agents/ (research_agent orchestrator)
│   └── api/ (streamlit app)
├── tests/
├── data/knowledge_db/ (chroma persistence)
├── logs/ (loguru output)
└── .env
```

## 🔧 Config (.env)
- `GROQ_API_KEY`: Required (free tier)
- `LLM_MODEL`: llama3-8b-8192 (default)
- `SEARCH_MAX_RESULTS=5`

## 📈 Tests & Coverage
```
pytest --cov=src --cov-report=html -v
```

## 🐳 Docker (coming)
Dockerfile + compose for prod deploy.

## 📄 License
MIT
