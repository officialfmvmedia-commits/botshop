# BotShop MVP
- Refresh catalog: `python3 ingest.py [pages_per_store=4]` (stores in stores.json, 250 products/page)
- Run: `python3 server.py [port=9393]` -> http://localhost:9393 (/, /agents, /api/*, /llms.txt, /openapi.json, POST /mcp)
- MCP stdio: `python3 mcp_stdio.py`
- Screenshots: `.venv/bin/python shots.py`
No dependencies beyond Python 3 stdlib (SQLite FTS5).
