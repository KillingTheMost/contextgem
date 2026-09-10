"""Reusable ContextGem extraction presets."""

from contextgem import (
    Aspect,
    BooleanConcept,
    DateConcept,
    ExtractionPipeline,
    NumericalConcept,
    StringConcept,
)


def _string(name: str, description: str, singular: bool = False) -> StringConcept:
    return StringConcept(
        name=name,
        description=description,
        add_references=True,
        reference_depth="sentences",
        add_justifications=True,
        justification_depth="brief",
        singular_occurrence=singular,
    )


def contract_pipeline() -> ExtractionPipeline:
    return ExtractionPipeline(
        aspects=[
            Aspect(
                name="Parties",
                description="Who the parties are and their roles (customer, supplier, employer, etc.).",
                reference_depth="sentences",
            ),
            Aspect(
                name="Commercial terms",
                description="Fees, prices, payment terms, invoicing, and commercial obligations.",
                reference_depth="sentences",
            ),
            Aspect(
                name="Term and termination",
                description="Start date, duration, renewal, and how either party can terminate.",
                reference_depth="sentences",
            ),
        ],
        concepts=[
            _string("Document type", "Type of agreement (NDA, MSA, employment, lease, etc.).", True),
            _string("Party A", "First party name and role.", True),
            _string("Party B", "Second party name and role.", True),
            DateConcept(
                name="Effective date",
                description="Date the agreement starts or becomes effective.",
                add_references=True,
                add_justifications=True,
                singular_occurrence=True,
            ),
            _string("Governing law", "Jurisdiction whose law governs the agreement.", True),
            _string("Termination notice", "Notice period required to terminate.", True),
            _string("Payment terms", "When and how payment is due."),
            BooleanConcept(
                name="Auto-renewal",
                description="Whether the agreement renews automatically unless cancelled.",
                add_justifications=True,
                singular_occurrence=True,
            ),
        ],
    )


def invoice_pipeline() -> ExtractionPipeline:
    return ExtractionPipeline(
        concepts=[
            _string("Supplier", "Vendor or seller name.", True),
            _string("Customer", "Bill-to customer name.", True),
            _string("Invoice number", "Invoice or bill identifier.", True),
            DateConcept(
                name="Invoice date",
                description="Date printed on the invoice.",
                add_references=True,
                singular_occurrence=True,
            ),
            DateConcept(
                name="Due date",
                description="Payment due date.",
                add_references=True,
                singular_occurrence=True,
            ),
            NumericalConcept(
                name="Subtotal",
                description="Amount before tax, as a number only.",
                numeric_type="float",
                singular_occurrence=True,
            ),
            NumericalConcept(
                name="Tax",
                description="Tax amount as a number only.",
                numeric_type="float",
                singular_occurrence=True,
            ),
            NumericalConcept(
                name="Total",
                description="Total amount due as a number only.",
                numeric_type="float",
                singular_occurrence=True,
            ),
            _string("Currency", "Currency code or symbol (EUR, USD, £).", True),
            _string("Line items", "Each product or service line with quantity and price."),
        ]
    )


def general_pipeline() -> ExtractionPipeline:
    return ExtractionPipeline(
        aspects=[
            Aspect(
                name="Summary topics",
                description="Main topics or sections of the document.",
                reference_depth="paragraphs",
            )
        ],
        concepts=[
            _string("Title", "Document title or heading.", True),
            _string("Key people or organizations", "Named people, companies, or institutions."),
            DateConcept(
                name="Important dates",
                description="Any dates that matter in the document.",
                add_references=True,
            ),
            _string("Key facts", "Important facts, figures, or conclusions."),
            _string("Action items", "Tasks, deadlines, or next steps mentioned."),
        ],
    )


PRESETS = {
    "Contract / agreement": contract_pipeline,
    "Invoice / bill": invoice_pipeline,
    "General document": general_pipeline,
}


def custom_pipeline(fields: list[dict]) -> ExtractionPipeline:
    """Build a pipeline from user-defined fields: {name, description, type}."""
    concepts = []
    for field in fields:
        name = (field.get("name") or "").strip()
        desc = (field.get("description") or name).strip()
        kind = (field.get("type") or "string").lower()
        if not name:
            continue
        if kind == "date":
            concepts.append(
                DateConcept(
                    name=name,
                    description=desc,
                    add_references=True,
                    add_justifications=True,
                )
            )
        elif kind == "number":
            concepts.append(
                NumericalConcept(
                    name=name,
                    description=desc,
                    numeric_type="float",
                    add_references=True,
                    add_justifications=True,
                )
            )
        elif kind == "yes/no":
            concepts.append(
                BooleanConcept(
                    name=name,
                    description=desc,
                    add_justifications=True,
                )
            )
        else:
            concepts.append(_string(name, desc))
    return ExtractionPipeline(concepts=concepts)
