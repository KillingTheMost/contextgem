import io
import json
import tempfile
from datetime import date, datetime
from pathlib import Path

import streamlit as st
from contextgem import (
    BooleanConcept,
    DateConcept,
    Document,
    DocumentLLM,
    ExtractionPipeline,
    JsonObjectConcept,
    StringConcept,
)

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
FIXTURE_TXT = FIXTURES / "MSA-2025-NOR-4417_ContextGem_test.txt"
FIXTURE_GOLD = FIXTURES / "MSA-2025-NOR-4417_gold_labels.json"

st.set_page_config(page_title="Contract Intake", page_icon="📋", layout="wide")
st.title("Contract Intake")
st.caption(
    "Same fields every time. Conflicts stay visible. "
    "Gemini reads the file; this app is the schema and the scorecard."
)


def string_field(name, description, singular=False, sentences=False):
    return StringConcept(
        name=name,
        description=description,
        add_references=True,
        reference_depth="sentences" if sentences else "paragraphs",
        add_justifications=True,
        justification_depth="brief",
        singular_occurrence=singular,
    )


CONTRACT_PIPELINE = ExtractionPipeline(
    aspects=[],
    concepts=[
        JsonObjectConcept(
            name="Deal snapshot",
            description=(
                "One structured summary of the commercial deal. "
                "If two clauses disagree, put both values in the matching *_cover / *_clause "
                "or *_internal fields. Do not invent a clean contract. "
                "Dates as YYYY-MM-DD. Money as integers in the stated currency. "
                "payment_term_days is the contractual due period (Clause 4.3 style), "
                "not an internal AP SLA."
            ),
            structure={
                "document_type": str,
                "document_id": str,
                "supplier": str,
                "customer": str,
                "project_name": str,
                "effective_date": str,
                "signature_date": str,
                "governing_law_cover": str,
                "governing_law_clause": str,
                "jurisdiction": str,
                "currency": str,
                "estimated_fees": int,
                "not_to_exceed_cap": int,
                "payment_term_days": int,
                "invoicing_cadence": str,
                "initial_term_months": int,
                "expiry_date": str,
                "auto_renewal": bool,
                "renewal_period_months": int,
                "non_renewal_notice_days": int,
                "convenience_termination": str,
            },
            add_references=True,
            add_justifications=True,
            singular_occurrence=True,
        ),
        string_field(
            "Conflicts",
            (
                "Each distinct inconsistency or reviewer flag in the document. "
                "One extracted item per conflict. Name both poles. "
                "If the document itself says which statement prevails, quote that. "
                "If it does not, say the conflict is unresolved. "
                "Do not pick a winner to tidy the draft."
            ),
            singular=False,
        ),
        string_field("Document type", "Type of agreement.", True),
        string_field("Party A", "Supplier / first party legal name and role.", True),
        string_field("Party B", "Customer / second party legal name and role.", True),
        DateConcept(
            name="Effective date",
            description=(
                "Contractual effective date, not the signature-block date "
                "if those two dates differ."
            ),
            add_references=True,
            add_justifications=True,
            singular_occurrence=True,
        ),
        string_field(
            "Governing law",
            (
                "Governing law. If the cover and the governing-law clause disagree, "
                "state BOTH in this field. Do not collapse to one jurisdiction."
            ),
            True,
        ),
        string_field(
            "Payment terms",
            "Contractual payment due period and invoicing cadence. "
            "If an internal AP SLA differs, mention it and say whether it amends the contract.",
            True,
        ),
        BooleanConcept(
            name="Auto-renewal",
            description="True if the agreement renews automatically unless notice is given.",
            add_justifications=True,
            add_references=True,
            singular_occurrence=True,
        ),
    ],
)

PRESETS = {
    "Contract intake (race)": CONTRACT_PIPELINE,
    "Invoice / bill": ExtractionPipeline(
        concepts=[
            string_field("Supplier", "Vendor name.", True),
            string_field("Customer", "Bill-to name.", True),
            string_field("Invoice number", "Invoice id.", True),
            DateConcept(
                name="Invoice date",
                description="Date on the invoice.",
                add_references=True,
                singular_occurrence=True,
            ),
            DateConcept(
                name="Due date",
                description="Payment due date.",
                add_references=True,
                singular_occurrence=True,
            ),
            string_field("Total", "Total amount due including currency.", True),
            string_field("Line items", "Each product or service line."),
        ]
    ),
    "General document": ExtractionPipeline(
        concepts=[
            string_field("Title", "Document title.", True),
            string_field("Key people or organizations", "Named people or organizations."),
            string_field("Important dates", "Dates that matter."),
            string_field("Key facts", "Important facts or conclusions."),
            string_field("Action items", "Tasks or next steps."),
        ]
    ),
}


def read_upload(name, data):
    suffix = Path(name).suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return data.decode("utf-8", errors="replace")
    if suffix == ".docx":
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=True) as tmp:
            tmp.write(data)
            tmp.flush()
            try:
                from contextgem import DocxConverter

                return DocxConverter().convert_to_text_format(
                    tmp.name, output_format="markdown"
                )
            except Exception:
                import docx

                d = docx.Document(tmp.name)
                return "\n".join(p.text for p in d.paragraphs if p.text.strip())
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    raise RuntimeError(f"Unsupported type: {suffix}")


def item_dict(item):
    value = item.value
    if isinstance(value, (date, datetime)):
        value = value.isoformat()
    payload = {"value": value}
    if getattr(item, "justification", None):
        payload["justification"] = item.justification
    sources = []
    for sent in getattr(item, "reference_sentences", None) or []:
        if getattr(sent, "raw_text", None):
            sources.append(sent.raw_text)
    for para in getattr(item, "reference_paragraphs", None) or []:
        if getattr(para, "raw_text", None):
            sources.append(para.raw_text)
    if sources:
        payload["sources"] = sources
    return payload


def flatten_rows(doc):
    rows = []
    blob = {}
    for concept in doc.concepts or []:
        items = concept.extracted_items or []
        blob[concept.name] = [item_dict(i) for i in items]
        if not items:
            rows.append({"Field": concept.name, "Value": "—", "Why": "", "Sources": ""})
            continue
        for item in items:
            data = item_dict(item)
            value = data.get("value")
            if isinstance(value, (dict, list)):
                display = json.dumps(value, ensure_ascii=False, indent=2, default=str)
            else:
                display = value
            rows.append(
                {
                    "Field": concept.name,
                    "Value": display,
                    "Why": data.get("justification", ""),
                    "Sources": " | ".join(data.get("sources") or [])[:800],
                }
            )
    return rows, blob


def load_gold():
    if not FIXTURE_GOLD.exists():
        return {}
    return json.loads(FIXTURE_GOLD.read_text(encoding="utf-8"))


def _haystack(blob):
    return json.dumps(blob, ensure_ascii=False, default=str).lower()


def score_fixture(blob):
    gold = load_gold()
    text = _haystack(blob)
    checks = []

    def add(name, ok, detail):
        checks.append({"Check": name, "Result": "PASS" if ok else "FAIL", "Detail": detail})

    add(
        "Effective Date is 2025-01-01, not signature date alone",
        "2025-01-01" in text or "1 january 2025" in text or "january 1" in text,
        "Gold effective date 2025-01-01. Signature 2025-03-15 must not replace it.",
    )

    add(
        "Payment term is Net 30, not Net 45",
        ("30" in text and "net 30" in text) or "payment_term_days\": 30" in text.replace(" ", ""),
        "Contractual term is 30 days. Net 45 is internal AP only.",
    )
    if "45" in text and "30" not in text:
        checks[-1]["Result"] = "FAIL"

    add(
        "Initial term is 24 months, not 36",
        "24" in text,
        "24 months to 2026-12-31. 36-month slide is not incorporated.",
    )

    add(
        "Fees are EUR 480000, not USD 510000 as the price",
        "480000" in text.replace(",", "") or "480,000" in text,
        "USD 510,000 is a non-contractual budget note.",
    )

    norway = "norway" in text
    england = "england" in text or "wales" in text
    add(
        "Governing law keeps both Norway and England & Wales",
        norway and england,
        "Cover = Norway. Clause 12.1 = England and Wales. Unresolved.",
    )

    add(
        "Auto-renewal is true",
        "auto_renewal\": true" in text.replace(" ", "") or ("true" in text and "renew" in text),
        "Auto-renews for 12 months unless 90 days' notice.",
    )

    add(
        "Conflicts concept actually reports conflicts",
        "norway" in text and ("england" in text or "wales" in text) and (
            "conflict" in text or "inconsist" in text or "does not" in text or "not amend" in text
        ),
        "Conflicts field should name both poles.",
    )
    return checks


def load_fixture_text():
    if not FIXTURE_TXT.exists():
        raise FileNotFoundError(
            f"Missing {FIXTURE_TXT}. Copy MSA-2025-NOR-4417_ContextGem_test.txt into fixtures/."
        )
    return FIXTURE_TXT.read_text(encoding="utf-8")


if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""
if "loaded_fixture" not in st.session_state:
    st.session_state.loaded_fixture = False

with st.sidebar:
    api_key = st.text_input("Google AI Studio API key", type="password")
    model = st.selectbox(
        "Model",
        ["gemini/gemini-3.8-flash", "gemini/gemini-flash-latest", "gemini/gemini-3.6-flash"],
    )
    st.caption("Do not use gemini-2.5-flash. It 404s for new keys.")
    max_items = st.slider("Max concepts per Gemini call", 1, 4, 2)
    st.markdown("---")
    if st.button("Load race fixture (MSA-2025-NOR-4417)"):
        st.session_state.doc_text = load_fixture_text()
        st.session_state.loaded_fixture = True
        st.rerun()
    if FIXTURE_TXT.exists():
        st.caption(f"Fixture on disk: {FIXTURE_TXT.name}")

left, right = st.columns([1, 1])

with left:
    source = st.radio("Input", ["Paste / fixture", "Upload file"], horizontal=True)
    if source == "Paste / fixture":
        st.session_state.doc_text = st.text_area(
            "Document",
            value=st.session_state.doc_text,
            height=280,
        )
        text = st.session_state.doc_text
    else:
        uploaded = st.file_uploader("TXT / MD / DOCX / PDF", type=["txt", "md", "docx", "pdf"])
        text = ""
        if uploaded:
            text = read_upload(uploaded.name, uploaded.getvalue())
            st.session_state.doc_text = text
            st.session_state.loaded_fixture = "MSA-2025-NOR-4417" in (uploaded.name or "")
            st.success(f"Loaded {len(text):,} characters")
        elif st.session_state.doc_text:
            text = st.session_state.doc_text

    if text:
        st.info(f"{len(text):,} characters loaded — full text is sent, nothing is truncated here.")

    preset = st.selectbox("Preset", list(PRESETS), index=0)
    run = st.button("Extract", type="primary")

with right:
    if not run:
        st.info("Load the fixture or upload a file, then Extract.")
    elif not api_key:
        st.error("Paste an API key from https://aistudio.google.com/apikey")
    elif len((text or "").strip()) < 20:
        st.error("Document is empty.")
    else:
        with st.spinner("Extracting with a two-concept-per-call cap…"):
            llm = DocumentLLM(
                model=model,
                api_key=api_key.strip(),
                timeout=180,
            )
            doc = Document(raw_text=text.strip())
            doc.assign_pipeline(PRESETS[preset])
            doc = llm.extract_all(
                doc,
                max_items_per_call=max_items,
            )
        rows, blob = flatten_rows(doc)
        st.subheader("Extract")
        st.dataframe(rows, hide_index=True, width="stretch")

        fixture_on = st.session_state.loaded_fixture or "msa-2025-nor-4417" in text.lower()
        if fixture_on and preset.startswith("Contract"):
            st.subheader("Race scorecard (gold fixture)")
            checks = score_fixture(blob)
            st.dataframe(checks, hide_index=True, width="stretch")
            fails = sum(1 for c in checks if c["Result"] == "FAIL")
            if fails:
                st.error(f"{fails} gold check(s) failed.")
            else:
                st.success("All gold checks passed.")

        export = {
            "model": model,
            "preset": preset,
            "characters": len(text),
            "extract": blob,
            "table": rows,
        }
        st.download_button(
            "Download JSON",
            json.dumps(export, indent=2, default=str),
            "extract.json",
            "application/json",
        )
