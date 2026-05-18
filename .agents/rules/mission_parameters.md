---
trigger: always_on
---

Project Name: Vanguard Milano.

Tech Stack: Python 3.11, Google Gemini 2.5 Flash (via Gemini API — google-generativeai SDK), FastAPI, Streamlit, Docker.

Agentic Framework: Gemini automatic function calling (enable_automatic_function_calling=True) with three Python tools: search_live_news, check_hub_capacity, execute_x402_settlement.

News Intelligence: ANSA RSS + BBC Europe RSS feeds with Italian/English keyword filtering.

Payments: X402 USDC programmable payment simulation (production → Coinbase CDP Wallet API).

Deployment Target: Vultr Ubuntu VM (Docker container, ports 8501 Streamlit / 8000 FastAPI).

Rule: Always read infrastructure IDs and API keys exclusively from the .env file.