# AI Inventory Copilot (Sarvam AI demo)

Multilingual voice assistant for Indian retail shops. Speak a question in
Hindi/Tamil/etc. → Sarvam STT transcribes → an LLM tool-calling agent runs
deterministic inventory math (reorder point, safety stock, forecast) → the
answer is spoken back via Sarvam TTS in the same language.

## Run locally
```bash
pip install -r requirements.txt
cp .env.example .env   # then paste your SARVAM_API_KEY into .env
streamlit run app.py
```

## Deploy (Streamlit Community Cloud — free, ~2 min)
Streamlit apps need a persistent server, so they can't run on Vercel
(serverless/stateless). Streamlit Community Cloud is the equivalent:

1. Push this repo to GitHub (public or private).
2. Go to https://share.streamlit.io → "New app" → pick this repo → main file `app.py`.
3. In the app's "Secrets" settings, add:
   ```
   SARVAM_API_KEY = "your-key-here"
   ```
4. Deploy. You get a public `*.streamlit.app` URL.

## Files
- `app.py` — Streamlit dashboard + voice UI
- `agent.py` — LLM tool-calling orchestration (never invents numbers)
- `inventory_tools.py` — deterministic reorder point / safety stock / forecast math
- `sarvam_client.py` — Sarvam STT / TTS / chat wrappers
- `data.py` — synthetic product + sales dataset for the demo
