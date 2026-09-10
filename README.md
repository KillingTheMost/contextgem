# Contract Intake

Streamlit app: Gemini reads the document. ContextGem supplies the schema, citations, and a gold scorecard.

This is not a fork of the ContextGem library. Install ContextGem from PyPI.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

1. Paste a Google AI Studio key.
2. Click **Load race fixture (MSA-2025-NOR-4417)** or upload a file.
3. Preset **Contract intake (race)**.
4. Model **gemini/gemini-3.8-flash**.
5. Extract. Check the scorecard.

Do not select `gemini-2.5-flash`. New keys get 404.

## Streamlit Cloud

Main file: `streamlit_app.py`  
Users bring their own AI Studio key.

## Files

```
streamlit_app.py
requirements.txt
Dockerfile
fixtures/MSA-2025-NOR-4417_ContextGem_test.txt
fixtures/MSA-2025-NOR-4417_gold_labels.json
gem_instructions.txt
RACE.md
```

`gem_instructions.txt` is the companion Gemini Gem (follow-up desk), not this app.

## Limits

- One document per run.
- Flash context is ~1M tokens. The race fixture is ~40k characters.
- PDFs via pypdf (no OCR).
