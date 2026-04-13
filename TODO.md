# Fix ModuleNotFoundError: No module named 'src' - Relative Imports Plan

## Progress Tracker
- [x] 1. Edit src/api/app.py (Streamlit app - primary error source)

- [x] 2. Edit src/agents/research_agent.py (agent core)
- [x] 3. Edit src/services/search_service.py, llm_service.py, kb_service.py
- [x] 4. Edit src/utils/helpers.py, src/models/schemas.py
- [x] 5. Update tests/* if needed
- [ ] 6. Test: streamlit run src/api/app.py
- [ ] 7. pip install -r requirements.txt if deps missing
- [ ] 8. pytest tests/

## Notes
- Convert all `from src.xxx` → `from .xxx` (relative imports)
- Run as: streamlit run src/api/app.py (from project root)
- Requires .env with GROQ_API_KEY

Updated: Step 1 complete after confirmation.

