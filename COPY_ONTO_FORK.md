# Copy these onto https://github.com/KillingTheMost/contextgem

From this folder:

| This file | Put it here on the fork |
|---|---|
| `streamlit_app.py` | `/streamlit_app.py` (replace) |
| `fixtures/MSA-2025-NOR-4417_ContextGem_test.txt` | `/fixtures/MSA-2025-NOR-4417_ContextGem_test.txt` |
| `fixtures/MSA-2025-NOR-4417_gold_labels.json` | `/fixtures/MSA-2025-NOR-4417_gold_labels.json` |
| `gem_instructions.txt` | `/gem_instructions.txt` |
| `RACE.md` | `/RACE.md` |

Then push `main` and reboot the Streamlit Cloud app.

Do not replace the `contextgem/` package directory. The app imports the installed library.
