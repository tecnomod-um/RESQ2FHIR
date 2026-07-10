from __future__ import annotations

import html
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.composition import Composition, CompositionSection
from fhir.resources.meta import Meta
from fhir.resources.narrative import Narrative
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier

from scripts.discharge_summary.sections import (
    SECTION_DEFINITIONS,
    SECTION_ORDER,
)
from scripts.enum_models import DischargeSection
from scripts.modeling_context import StrokeCaseContext, StrokeCaseResource
from scripts.utils import get_uuid


DISCHARGE_SUMMARY_TYPE = CodeableConcept(
    coding=[
        Coding(
            system="http://loinc.org",
            code="34105-7",
            display="Hospital Discharge summary",
        )
    ]
)

def build_discharge_composition(
    context: StrokeCaseContext,
) -> Composition:
    """Build the Composition resource from section assignments."""

    sections = []

    for section_key in SECTION_ORDER:
        section = _build_section(
            context=context,
            section_key=section_key,
        )

        if section is not None:
            sections.append(section)

    composition = Composition(
        status="final",
        type=DISCHARGE_SUMMARY_TYPE,
        subject=[Reference(reference=context.patient_ref)],
        encounter=Reference(reference=context.encounter_ref) if context.encounter_ref else None,
        date=datetime.now(timezone.utc),
        author=[ Reference(reference=context.organization_ref)] if context.organization_ref  else [],
        custodian=Reference(reference=context.organization_ref) if context.organization_ref else None,
        title="Stroke Hospital Discharge Summary",
        section=sections,
        meta=Meta(
            profile=[
                "http://tecnomod-um.org/StructureDefinition/resq-stroke-discharge-composition"
            ]
        ),
        identifier=[Identifier(system="https://stroke.qualityregistry.org", value=str(context.case_id))]


    )

    composition.text = _build_composition_text(
        composition
    )

    return composition

def _build_section(
    context: StrokeCaseContext,
    section_key: DischargeSection,
) -> CompositionSection | None:
    definition = SECTION_DEFINITIONS[section_key]
    records = context.resources_for_section(section_key)

    if not records and not definition.required:
        return None

    section = CompositionSection(
        title=definition.title,
        code=CodeableConcept(
            coding=[
                Coding(
                    system=definition.system,
                    code=definition.code,
                    display=definition.display,
                )
            ]
        ),
        text=_build_section_text(
            title=definition.title,
            records=records,
        ),
    )

    if records:
        section.entry = [
            Reference(reference=record.full_url)
            for record in records
        ]
    else:
        section.emptyReason = CodeableConcept(
            coding=[
                Coding(
                    system="http://terminology.hl7.org/CodeSystem/list-empty-reason",
                    code="unavailable",
                    display="Unavailable",
                )
            ]
        )

    return section

def _build_section_text(
    title: str,
    records: tuple[StrokeCaseResource, ...],
) -> Narrative:
    if not records:
        div = (
            f'<div xmlns="http://www.w3.org/1999/xhtml">'
            f"<p>No structured entries available for "
            f"{html.escape(title)}.</p>"
            f"</div>"
        )

        return Narrative(
            status="generated",
            div=div,
        )

    items = "".join(
        f"<li>{html.escape(_resource_summary(record.resource))}</li>"
        for record in records
    )

    div = (
        f'<div xmlns="http://www.w3.org/1999/xhtml">'
        f"<ul>{items}</ul>"
        f"</div>"
    )

    return Narrative(
        status="generated",
        div=div,
    )


def _build_composition_text(
    composition: Composition,
) -> Narrative:
    div = (
        f'<div xmlns="http://www.w3.org/1999/xhtml">'
        f"<p>{html.escape(composition.title)}</p>"
        f"</div>"
    )

    return Narrative(
        status="generated",
        div=div,
    )

def build_discharge_document_bundle(
    context: StrokeCaseContext,
) -> Bundle:
    """Build a FHIR document Bundle for the stroke discharge summary."""

    composition_ref = get_uuid()

    composition = build_discharge_composition(
        context=context,
    )

    document_full_urls = _collect_document_full_urls(
        context=context,
    )

    entries: list[BundleEntry] = [
        BundleEntry(
            fullUrl=composition_ref,
            resource=composition,
        )
    ]

    for record in context.resources:
        if record.full_url in document_full_urls:
            entries.append(
                BundleEntry(
                    fullUrl=record.full_url,
                    resource=record.resource,
                )
            )

    return Bundle(
        type="document",
        timestamp=datetime.now(timezone.utc),
        entry=entries,
        identifier=Identifier(system="https://stroke.qualityregistry.org", value=str(context.case_id))
    )

def _resource_summary(resource: Any) -> str:
    resource_type = resource.get_resource_type()

    if resource_type == "Condition":
        return f"Condition: {_code_display(resource.code)}"

    if resource_type == "Observation":
        return _observation_summary(resource)

    if resource_type == "Procedure":
        status = getattr(resource, "status", None)
        return f"Procedure: {_code_display(resource.code)} ({status})"

    if resource_type == "MedicationRequest":
        return (
            "Discharge medication: "
            f"{_medication_display(resource.medication)}"
        )

    if resource_type == "MedicationAdministration":
        status = getattr(resource, "status", None)
        return (
            "Medication administration: "
            f"{_medication_display(resource.medication)} ({status})"
        )

    if resource_type == "MedicationStatement":
        return (
            "Medication statement: "
            f"{_medication_display(resource.medication)}"
        )

    if resource_type == "DiagnosticReport":
        return f"Diagnostic report: {_code_display(resource.code)}"

    if resource_type == "Encounter":
        return "Encounter discharge details"

    if resource_type == "Location":
        return "Care location"

    if resource_type == "Appointment":
        return "Follow-up appointment"

    return resource_type


def _observation_summary(resource: Any) -> str:
    label = _code_display(resource.code)

    if getattr(resource, "valueInteger", None) is not None:
        return f"Observation: {label} = {resource.valueInteger}"

    if getattr(resource, "valueBoolean", None) is not None:
        return f"Observation: {label} = {resource.valueBoolean}"

    if getattr(resource, "valueCodeableConcept", None) is not None:
        return (
            f"Observation: {label} = "
            f"{_code_display(resource.valueCodeableConcept)}"
        )

    if getattr(resource, "valueQuantity", None) is not None:
        quantity = resource.valueQuantity
        return (
            f"Observation: {label} = "
            f"{getattr(quantity, 'value', '')} "
            f"{getattr(quantity, 'unit', '')}"
        ).strip()

    return f"Observation: {label}"


def _code_display(codeable_concept: Any) -> str:
    if codeable_concept is None:
        return "Unknown"

    text = getattr(codeable_concept, "text", None)

    if text:
        return str(text)

    codings = getattr(codeable_concept, "coding", None) or []

    if codings:
        coding = codings[0]
        return (
            getattr(coding, "display", None)
            or getattr(coding, "code", None)
            or "Unknown"
        )

    return "Unknown"


def _medication_display(medication: Any) -> str:
    if medication is None:
        return "Unknown"

    concept = getattr(medication, "concept", None)

    if concept is not None:
        return _code_display(concept)

    reference = getattr(medication, "reference", None)

    if reference is not None:
        return getattr(reference, "reference", "Unknown")

    return "Unknown"

def _collect_document_full_urls(
    context: StrokeCaseContext,
) -> set[str]:
    """Collect section entries and all local resources they reference."""

    selected: set[str] = set()

    for section_key in SECTION_ORDER:
        for record in context.resources_for_section(section_key):
            selected.add(record.full_url)

    if context.patient_ref:
        selected.add(context.patient_ref)

    if context.encounter_ref:
        selected.add(context.encounter_ref)

    if context.organization_ref:
        selected.add(context.organization_ref)

    return _expand_with_local_references(
        context=context,
        initial_full_urls=selected,
    )


def _expand_with_local_references(
    context: StrokeCaseContext,
    initial_full_urls: set[str],
) -> set[str]:
    resolved = set(initial_full_urls)
    queue = deque(initial_full_urls)

    while queue:
        full_url = queue.popleft()
        record = context.get_resource(full_url)

        if record is None:
            continue

        for reference in _extract_references(record.resource):
            if (
                reference in context.resources_by_full_url
                and reference not in resolved
            ):
                resolved.add(reference)
                queue.append(reference)

    return resolved


def _extract_references(resource: Any) -> set[str]:
    """Extract all Reference.reference values from a FHIR resource."""

    if hasattr(resource, "model_dump"):
        data = resource.model_dump(
            by_alias=True,
            exclude_none=True,
        )
    elif hasattr(resource, "dict"):
        data = resource.dict(
            by_alias=True,
            exclude_none=True,
        )
    else:
        return set()

    return _extract_references_from_data(data)


def _extract_references_from_data(data: Any) -> set[str]:
    references: set[str] = set()

    if isinstance(data, dict):
        reference_value = data.get("reference")

        if isinstance(reference_value, str):
            references.add(reference_value)

        for value in data.values():
            references.update(
                _extract_references_from_data(value)
            )

    elif isinstance(data, list):
        for item in data:
            references.update(
                _extract_references_from_data(item)
            )

    return references