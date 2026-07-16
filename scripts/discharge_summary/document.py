"""FHIR R5 document builder aligned with Xt-EHR EHDSDischargeReport."""

from __future__ import annotations

import html
from collections import deque
from datetime import datetime, timezone
from typing import Any, Iterable

from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.composition import Composition, CompositionSection
from fhir.resources.identifier import Identifier
from fhir.resources.meta import Meta
from fhir.resources.narrative import Narrative
from fhir.resources.reference import Reference

from scripts.discharge_summary.clinical_synthesis import (
    build_clinical_synthesis_narrative,
)
from scripts.discharge_summary.ehds_model import (
    DOCUMENT_SECTION_DEFINITIONS,
    ROOT_SECTION_ORDER,
    CodeKey,
    DocumentSection,
    DocumentSectionDefinition,
    child_sections,
)
from scripts.discharge_summary.narrative import build_section_narrative
from scripts.modeling_context import StrokeCaseContext, StrokeCaseResource
from scripts.utils import get_uuid


LIST_EMPTY_REASON = "http://terminology.hl7.org/CodeSystem/list-empty-reason"
RESQ_COMPOSITION_PROFILE = (
    "http://tecnomod-um.org/StructureDefinition/"
    "resq-stroke-discharge-composition"
)
DISCHARGE_SUMMARY_TYPE = CodeableConcept(
    coding=[
        Coding(
            system="http://loinc.org",
            code="18842-5",
            display="Discharge summary",
        )
    ]
)


def build_discharge_composition(context: StrokeCaseContext) -> Composition:
    """Build the EHDS-aligned RESQ FHIR R5 Composition."""

    sections = [
        section
        for section_key in ROOT_SECTION_ORDER
        if (
            section := _build_document_section(
                context=context,
                section_key=section_key,
            )
        )
        is not None
    ]

    composition = Composition(
        status="final",
        type=DISCHARGE_SUMMARY_TYPE,
        subject=[Reference(reference=context.patient_ref)],
        encounter=(
            Reference(reference=context.encounter_ref)
            if context.encounter_ref
            else None
        ),
        date=datetime.now(timezone.utc),
        author=(
            [Reference(reference=context.organization_ref)]
            if context.organization_ref
            else []
        ),
        custodian=(
            Reference(reference=context.organization_ref)
            if context.organization_ref
            else None
        ),
        title="Stroke Hospital Discharge Summary",
        language="en",
        version="1",
        section=sections,
        meta=Meta(profile=[RESQ_COMPOSITION_PROFILE]),
        identifier=[
            Identifier(
                system="https://stroke.qualityregistry.org/",
                value=str(context.case_id),
            )
        ],
    )
    composition.text = _build_composition_text(composition)
    return composition


def _build_document_section(
    context: StrokeCaseContext,
    section_key: DocumentSection,
) -> CompositionSection | None:
    definition = DOCUMENT_SECTION_DEFINITIONS[section_key]

    if section_key == DocumentSection.CLINICAL_SYNTHESIS:
        synthesis = build_clinical_synthesis_narrative(context)
        if synthesis is None:
            return None
        return CompositionSection(
            title=definition.title,
            code=_section_code(definition),
            text=synthesis,
        )

    records = _records_for_document_section(context, definition)
    nested_sections = tuple(
        child
        for child_key in child_sections(section_key)
        if (
            child := _build_document_section(context, child_key)
        )
        is not None
    )

    has_content = bool(records or nested_sections)
    if not has_content and not definition.required:
        return None

    section = CompositionSection(
        title=definition.title,
        code=_section_code(definition),
        text=build_section_narrative(
            context=context,
            section_key=section_key,
            title=definition.title,
            records=records,
            children=nested_sections,
            empty_reason=None if has_content else definition.empty_reason,
        ),
    )

    if records:
        section.entry = [
            Reference(reference=record.full_url)
            for record in records
        ]
    if nested_sections:
        section.section = list(nested_sections)
    if not has_content:
        section.emptyReason = _build_empty_reason(definition)

    return section


def _section_code(definition: DocumentSectionDefinition) -> CodeableConcept:
    return CodeableConcept(
        coding=[
            Coding(
                system=definition.system,
                code=definition.code,
                display=definition.display,
            )
        ]
    )


def _records_for_document_section(
    context: StrokeCaseContext,
    definition: DocumentSectionDefinition,
) -> tuple[StrokeCaseResource, ...]:
    """Resolve direct entries using internal sections and semantic codes."""

    source_sections = set(definition.source_sections)
    records: list[StrokeCaseResource] = []
    seen: set[str] = set()

    def add(record: StrokeCaseResource | None) -> None:
        if record is None or record.full_url in seen:
            return
        records.append(record)
        seen.add(record.full_url)

    if definition.include_encounter and context.encounter_ref:
        add(context.get_resource(context.encounter_ref))

    for record in context.resources:
        if source_sections.intersection(record.sections):
            add(record)
            continue
        if definition.entry_match_codes and _resource_matches_codes(
            record.resource,
            definition.entry_match_codes,
        ):
            add(record)

    return tuple(records)


def _resource_matches_codes(
    resource: Any,
    expected_codes: frozenset[CodeKey],
) -> bool:
    codeable_concept = getattr(resource, "code", None)
    for coding in getattr(codeable_concept, "coding", None) or ():
        system = getattr(coding, "system", None)
        code = getattr(coding, "code", None)
        if isinstance(system, str) and isinstance(code, str):
            if (system, code) in expected_codes:
                return True
    return False


def _build_empty_reason(
    definition: DocumentSectionDefinition,
) -> CodeableConcept:
    return CodeableConcept(
        coding=[
            Coding(
                system=LIST_EMPTY_REASON,
                code=definition.empty_reason,
                display=definition.empty_reason_display,
            )
        ]
    )


def _build_composition_text(composition: Composition) -> Narrative:
    return Narrative(
        status="generated",
        div=(
            '<div xmlns="http://www.w3.org/1999/xhtml">'
            f"<p>{html.escape(composition.title)}</p>"
            "</div>"
        ),
    )


def build_discharge_document_bundle(context: StrokeCaseContext) -> Bundle:
    """Build a self-contained FHIR R5 document Bundle."""

    composition_ref = get_uuid()
    composition = build_discharge_composition(context=context)
    document_full_urls = _collect_document_full_urls(context, composition)

    entries: list[BundleEntry] = [
        BundleEntry(fullUrl=composition_ref, resource=composition)
    ]
    entries.extend(
        BundleEntry(fullUrl=record.full_url, resource=record.resource)
        for record in context.resources
        if record.full_url in document_full_urls
    )

    return Bundle(
        type="document",
        timestamp=datetime.now(timezone.utc),
        entry=entries,
        identifier=Identifier(
            system="https://stroke.qualityregistry.org/",
            value=str(context.case_id),
        ),
    )


def _collect_document_full_urls(
    context: StrokeCaseContext,
    composition: Composition,
) -> set[str]:
    selected = _composition_entry_references(composition)
    for reference in (
        context.patient_ref,
        context.encounter_ref,
        context.organization_ref,
    ):
        if reference:
            selected.add(reference)
    return _expand_with_local_references(context, selected)


def _composition_entry_references(composition: Composition) -> set[str]:
    references: set[str] = set()

    def visit(sections: Iterable[CompositionSection] | None) -> None:
        for section in sections or ():
            for entry in getattr(section, "entry", None) or ():
                reference = getattr(entry, "reference", None)
                if isinstance(reference, str):
                    references.add(reference)
            visit(getattr(section, "section", None))

    visit(composition.section)
    return references


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
    if hasattr(resource, "model_dump"):
        data = resource.model_dump(by_alias=True, exclude_none=True)
    elif hasattr(resource, "dict"):
        data = resource.dict(by_alias=True, exclude_none=True)
    else:
        return set()
    return _extract_references_from_data(data)


def _extract_references_from_data(data: Any) -> set[str]:
    references: set[str] = set()
    if isinstance(data, dict):
        reference = data.get("reference")
        if isinstance(reference, str):
            references.add(reference)
        for value in data.values():
            references.update(_extract_references_from_data(value))
    elif isinstance(data, list):
        for item in data:
            references.update(_extract_references_from_data(item))
    return references
