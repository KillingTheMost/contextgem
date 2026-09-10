# Contract Intake — race notes

One sentence: same contract fields every time, conflicts left visible, tested on a dirty MSA we publish.

## What this is

A Streamlit intake app. Gemini reads the document. ContextGem only supplies the schema, citations, and the gold scorecard.

It is not “better than Gemini at reading.” A Thinking chat still wins a one-off lawyer question. This wins when the company needs the same JSON, a pass/fail harness, and clause quotes.

## Files to copy onto the fork

Overwrite / add on https://github.com/KillingTheMost/contextgem

```
streamlit_app.py                                              ← replace the file on the fork
fixtures/MSA-2025-NOR-4417_ContextGem_test.txt
fixtures/MSA-2025-NOR-4417_gold_labels.json
gem_instructions.txt
RACE.md
```

Streamlit Cloud already points at `streamlit_app.py`. Redeploy after push.

## Demo (8 minutes)

1. Sidebar → **Load race fixture**. Confirm ~40,000 characters. Nothing truncated.
2. Preset **Contract intake (race)**. Model **gemini-3.8-flash**. Extract.
3. Point at Deal snapshot + Conflicts. Norway and England both present.
4. Scorecard all PASS, or say what failed honestly.
5. Download JSON.
6. Optional: same file in a Gemini Gem using `gem_instructions.txt` — nicer prose, no harness.
7. Stop.

## What changed vs the old app

| Old | New |
|---|---|
| 3 aspects + 8 sentence-level concepts | No aspects. One JSON snapshot + Conflicts + a short header table |
| `gemini-2.5-flash` in the dropdown (404) | Removed |
| JSON = Field / Value / Why only | JSON includes sources and the snapshot object |
| Aspects computed for 63s, dropped from download | Aspects not requested |
| ~5 full-doc calls / 185K input tokens | `max_items_per_call=2` default |

## Gold checks

- Effective Date 2025-01-01
- Net 30, not Net 45 as the contract term
- 24-month term, not 36
- EUR 480,000 as fees, not USD 510,000
- Governing law: Norway **and** England & Wales
- Auto-renewal true

## Do not

- Paste Appendix X or gold answers into the Gem
- Claim this beat 3.8 Thinking on prose
- Leave 2.5 Flash selectable
