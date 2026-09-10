# ContextGem online app (Gemini Flash)

Web UI around [ContextGem](https://contextgem.dev/) that sends the whole document to **Gemini Flash** via a Google AI Studio API key.

ContextGem is Python. Google AI Studio cannot run this library in the prompt box. This app is the hosted version: Streamlit UI → ContextGem → `gemini/gemini-3.8-flash`.

## Local run

```bash
cd contextgem-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

1. Create a key at https://aistudio.google.com/apikey
2. Paste it in the sidebar
3. Paste or upload a document
4. Pick a preset (contract / invoice / general) or define fields
5. Click **Extract with Gemini Flash**

## Deploy online

### A. Streamlit Community Cloud (easiest)

1. Push this folder to a public GitHub repo
2. Go to https://share.streamlit.io and deploy `app.py`
3. Users paste their own AI Studio key in the sidebar

Optional: store *your* key as a secret named `GEMINI_API_KEY` and read it in `app.py` if you want a private internal tool.

### B. Hugging Face Spaces

1. New Space → SDK **Streamlit**
2. Upload these files
3. Space builds from `requirements.txt`

### C. Cloud Run (Google Cloud)

```bash
gcloud run deploy contextgem-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=AIza...
```

Do **not** put the API key in the image. Use Cloud Run env vars or Secret Manager.

Dockerfile already listens on port `8080`.

## Model id

LiteLLM (used by ContextGem) needs the AI Studio prefix:

```
gemini/gemini-3.8-flash
```

`gemini-3.8-flash` without `gemini/` is treated as Vertex AI and will fail with a credentials error.

If 3.8 is unavailable on your key, switch the sidebar to **Gemini 2.5 Flash** or **gemini-flash-latest**.

## Limits

- One document at a time (ContextGem’s design)
- Gemini Flash context is ~1M tokens — fine for typical contracts/reports, not a 10k-page corpus
- PDF text comes from `pypdf` (no OCR). Scanned PDFs will be empty unless you OCR first
- Public deployments: make users bring their own key, or you pay for their tokens
