"""ContextGem online extractor powered by Gemini Flash."""

from __future__ import annotations

import json

import streamlit as st

from extract import (
    FLASH_MODELS,
    document_to_results,
    make_llm,
    run_extraction,
    text_from_upload,
)
from presets import PRESETS, custom_pipeline

st.set_page_config(
    page_title="ContextGem · Gemini Flash",
    page_icon="💎",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.4rem; max-width: 1200px;}
      .result-card {border: 1px solid #e6e6e6; border-radius: 12px; padding: 0.9rem 1rem; margin-bottom: 0.7rem;}
      .muted {color: #667085; font-size: 0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💎 ContextGem")
st.caption("Extract structured fields from a document with Gemini Flash. Key stays in your browser session.")

with st.sidebar:
    st.header("Gemini")
    api_key = st.text_input(
        "Google AI Studio API key",
        type="password",
        help="Create a key at https://aistudio.google.com/apikey",
        placeholder="AIza…",
    )
    model_label = st.selectbox("Flash model", list(FLASH_MODELS.keys()))
    model = FLASH_MODELS[model_label]
    st.code(model, language="text")
    st.markdown(
        "[Get an API key](https://aistudio.google.com/apikey) · "
        "[ContextGem docs](https://contextgem.dev/)"
    )
    st.divider()
    st.caption(
        "The app calls the Gemini API from this server. "
        "Do not deploy a public instance with your key baked in — use Streamlit secrets or an env var."
    )

left, right = st.columns([1.05, 1], gap="large")

with left:
    st.subheader("1. Document")
    source = st.radio("Input", ["Paste text", "Upload file"], horizontal=True)
    raw_text = ""
    if source == "Paste text":
        raw_text = st.text_area(
            "Document text",
            height=260,
            placeholder="Paste a contract, invoice, report, email…",
        )
    else:
        uploaded = st.file_uploader(
            "TXT, MD, DOCX, or PDF",
            type=["txt", "md", "docx", "pdf"],
        )
        if uploaded:
            try:
                raw_text = text_from_upload(uploaded.name, uploaded.getvalue())
                st.success(f"Loaded {uploaded.name} · {len(raw_text):,} characters")
                with st.expander("Preview extracted text"):
                    st.text(raw_text[:4000] + ("…" if len(raw_text) > 4000 else ""))
            except Exception as exc:
                st.error(str(exc))

    st.subheader("2. What to extract")
    mode = st.radio(
        "Schema",
        ["Preset", "Custom fields"],
        horizontal=True,
    )

    extra_fields: list[dict] = []
    if mode == "Preset":
        preset_name = st.selectbox("Preset", list(PRESETS.keys()))
        pipeline = PRESETS[preset_name]()
        st.caption("Presets include references and short justifications.")
    else:
        preset_name = "Custom"
        n = st.number_input("Number of fields", min_value=1, max_value=12, value=4)
        for i in range(int(n)):
            c1, c2, c3 = st.columns([1.2, 2.2, 0.9])
            with c1:
                name = st.text_input(f"Name {i+1}", key=f"n{i}", placeholder="Governing law")
            with c2:
                desc = st.text_input(
                    f"Describe {i+1}",
                    key=f"d{i}",
                    placeholder="Jurisdiction that governs the contract",
                )
            with c3:
                kind = st.selectbox(
                    f"Type {i+1}",
                    ["string", "date", "number", "yes/no"],
                    key=f"t{i}",
                )
            extra_fields.append({"name": name, "description": desc, "type": kind})
        pipeline = custom_pipeline(extra_fields)

    run = st.button("Extract with Gemini Flash", type="primary", use_container_width=True)

with right:
    st.subheader("3. Results")
    if not run:
        st.info("Add a document and click Extract.")
    else:
        try:
            with st.spinner("Gemini Flash is reading the document…"):
                llm = make_llm(api_key, model)
                doc = run_extraction(raw_text, pipeline, llm)
                results = document_to_results(doc)
            st.session_state["last_results"] = results
            st.session_state["last_preset"] = preset_name
        except Exception as exc:
            st.error(str(exc))
            results = None

    results = st.session_state.get("last_results")
    if results:
        concept_rows = []
        for concept in results["concepts"]:
            if not concept["items"]:
                concept_rows.append(
                    {"Field": concept["name"], "Value": "—", "Why": "", "Source": ""}
                )
            for item in concept["items"]:
                concept_rows.append(
                    {
                        "Field": concept["name"],
                        "Value": item.get("value"),
                        "Why": item.get("justification", ""),
                        "Source": " | ".join(item.get("sources", [])[:2]),
                    }
                )
        if concept_rows:
            st.markdown("**Fields**")
            st.dataframe(concept_rows, use_container_width=True, hide_index=True)

        for aspect in results["aspects"]:
            st.markdown(f"**Section · {aspect['name']}**")
            texts = [item.get("value") for item in aspect["items"] if item.get("value")]
            if texts:
                for text in texts:
                    st.write(text)
            else:
                st.caption("No section text extracted.")
            nested_rows = []
            for concept in aspect.get("concepts") or []:
                for item in concept["items"]:
                    nested_rows.append(
                        {
                            "Field": concept["name"],
                            "Value": item.get("value"),
                            "Why": item.get("justification", ""),
                        }
                    )
            if nested_rows:
                st.dataframe(nested_rows, use_container_width=True, hide_index=True)

        st.download_button(
            "Download JSON",
            data=json.dumps(results, indent=2, ensure_ascii=False),
            file_name="contextgem-extract.json",
            mime="application/json",
            use_container_width=True,
        )
        with st.expander("Raw JSON"):
            st.json(results)
