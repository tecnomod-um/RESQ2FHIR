"""Deterministic XHTML narrative generation for the RESQ discharge document.

Narratives are derived exclusively from FHIR resources registered in the
StrokeCaseContext. Local references are resolved inside the case so generated
text does not expose internal urn:uuid values when the target is available.
"""

from __future__ import annotations

import html
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from fhir.resources.composition import CompositionSection
from fhir.resources.narrative import Narrative

from scripts.discharge_summary.ehds_model import DocumentSection
from scripts.modeling_context import StrokeCaseContext, StrokeCaseResource


EMPTY_REASON_TEXT = {
    "nilknown": "No known information exists for this section.",
    "notasked": "This information was not collected.",
    "unavailable": "The information was expected but is unavailable.",
    "notfound": "The information could not be located.",
    "withheld": "The information is not available for disclosure.",
}

ASSESSMENT_CONTEXT_EXTENSION = (
    "http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext"
)
INITIAL_CARE_INTENSITY_EXTENSION = (
    "http://tecnomod-um.org/StructureDefinition/initial-care-intensity-ext"
)
DISCHARGE_FACILITY_TYPE_EXTENSION = (
    "http://tecnomod-um.org/StructureDefinition/discharge-facility-type-ext"
)
DISCHARGE_DEPARTMENT_EXTENSION = (
    "http://tecnomod-um.org/StructureDefinition/discharge-department-service-ext"
)
REQUIRED_POST_ACUTE_CARE_EXTENSION = (
    "http://tecnomod-um.org/StructureDefinition/required-post-acute-care-ext"
)

_TRAILING_SEMANTIC_TAG = re.compile(
    r"\s+\((?:disorder|finding|procedure|substance|observable entity|"
    r"qualifier value|body structure|physical object|environment)\)\s*$",
    flags=re.IGNORECASE,
)


def build_section_narrative(
    *,
    context: StrokeCaseContext,
    section_key: DocumentSection,
    title: str,
    records: tuple[StrokeCaseResource, ...],
    children: tuple[CompositionSection, ...],
    empty_reason: str | None,
) -> Narrative:
    """Build a section-specific generated narrative."""

    if not records and not children:
        message = EMPTY_REASON_TEXT.get(
            empty_reason or "unavailable",
            "No information is available for this section.",
        )
        return _narrative(title=None, paragraphs=(message,))

    if section_key == DocumentSection.PATIENT_HISTORY:
        return _build_patient_history_narrative(
            context=context,
            title=title,
            records=records,
        )

    if section_key in {
        DocumentSection.ENCOUNTER_INFORMATION,
        DocumentSection.DISCHARGE_DETAILS,
    }:
        return _build_encounter_section_narrative(
            context=context,
            title=title,
            records=records,
            children=children,
        )

    items = tuple(
        resource_summary(record.resource, context)
        for record in records
    )
    child_titles = tuple(str(child.title) for child in children)
    return _narrative(title=title, items=items, child_titles=child_titles)


def resource_summary(resource: Any, context: StrokeCaseContext) -> str:
    """Render one resource as concise clinical prose."""

    resource_type = resource.get_resource_type()
    if resource_type == "Condition":
        return condition_summary(resource)
    if resource_type == "Observation":
        return observation_summary(resource)
    if resource_type == "Procedure":
        return procedure_summary(resource)
    if resource_type == "MedicationRequest":
        return medication_request_summary(resource, context)
    if resource_type == "MedicationAdministration":
        return medication_administration_summary(resource, context)
    if resource_type == "MedicationStatement":
        return medication_statement_summary(resource, context)
    if resource_type == "DiagnosticReport":
        return f"Diagnostic report: {clinical_label(resource.code)}."
    if resource_type == "Encounter":
        return encounter_summary(resource, context)
    if resource_type == "Location":
        return location_summary(resource)
    if resource_type == "Appointment":
        return "A follow-up appointment was recorded."
    if resource_type == "CarePlan":
        return "A care plan was recorded."
    if resource_type == "ServiceRequest":
        return f"Requested service: {clinical_label(resource.code)}."
    if resource_type == "AllergyIntolerance":
        return f"Allergy or intolerance: {clinical_label(resource.code)}."
    if resource_type == "Flag":
        return f"Medical alert: {clinical_label(resource.code)}."
    if resource_type in {"Device", "DeviceAssociation"}:
        return "A medical device or implant was recorded."
    return resource_type


def condition_summary(resource: Any) -> str:
    label = clinical_label(getattr(resource, "code", None))
    status = _first_code_display(getattr(resource, "clinicalStatus", None))
    if status and status.lower() not in {"active", "unknown"}:
        return f"{label} ({status.lower()})."
    return f"{label}."


def procedure_summary(resource: Any) -> str:
    label = clinical_label(getattr(resource, "code", None))
    status = getattr(resource, "status", None)
    if status == "completed":
        return f"{label} was completed."
    if status:
        return f"{label}, status: {status}."
    return f"{label}."


def observation_summary(resource: Any) -> str:
    label = clinical_label(getattr(resource, "code", None))
    context_label = observation_context_label(resource)
    prefix = f"{label} {context_label}" if context_label else label

    components = getattr(resource, "component", None) or ()
    if components:
        blood_pressure = _blood_pressure_summary(components, context_label)
        if blood_pressure:
            return blood_pressure
        values = join_clinical(
            tuple(_observation_component_summary(component) for component in components)
        )
        return f"{prefix}: {values}."

    value = observation_value_display(resource)
    if value is None:
        return f"{prefix}."
    return f"{prefix}: {value}."


def medication_request_summary(resource: Any, context: StrokeCaseContext) -> str:
    name, ingredients = medication_details(
        getattr(resource, "medication", None), context
    )
    return f"Discharge medication: {_medication_name_with_ingredients(name, ingredients)}."


def medication_statement_summary(resource: Any, context: StrokeCaseContext) -> str:
    name, ingredients = medication_details(
        getattr(resource, "medication", None), context
    )
    detail = _medication_name_with_ingredients(name, ingredients)
    adherence = _first_code_display(
        getattr(getattr(resource, "adherence", None), "code", None)
    )
    if adherence:
        return f"Prior medication: {detail} ({adherence.lower()})."
    return f"Prior medication: {detail}."


def medication_administration_summary(
    resource: Any,
    context: StrokeCaseContext,
) -> str:
    name, ingredients = medication_details(
        getattr(resource, "medication", None), context
    )
    detail = _medication_name_with_ingredients(name, ingredients)
    dose = dose_display(resource)
    status = getattr(resource, "status", None)

    if dose and status == "completed":
        return f"{detail} was administered at a dose of {dose}."
    if dose:
        return f"{detail} was administered at a dose of {dose}; status: {status}."
    if status == "completed":
        return f"{detail} was administered."
    if status:
        return f"{detail} administration status: {status}."
    return f"{detail} was administered."


def encounter_summary(resource: Any, context: StrokeCaseContext) -> str:
    """Describe encounter period, locations and discharge disposition."""

    sentences: list[str] = []
    period = getattr(resource, "actualPeriod", None)
    start = getattr(period, "start", None) if period else None
    end = getattr(period, "end", None) if period else None
    if start and end:
        sentences.append(
            f"Encounter from {format_fhir_datetime(start)} to {format_fhir_datetime(end)}"
        )
    elif start:
        sentences.append(f"Encounter started {format_fhir_datetime(start)}")
    elif end:
        sentences.append(f"Encounter ended {format_fhir_datetime(end)}")

    locations: list[str] = []
    for encounter_location in getattr(resource, "location", None) or ():
        reference = getattr(
            getattr(encounter_location, "location", None), "reference", None
        )
        location = resolve_resource(context, reference)
        if location is not None:
            label = location_summary(location)
            if label and label not in locations:
                locations.append(label)
    if locations:
        sentences.append(f"Care locations: {join_clinical(tuple(locations))}")

    admission = getattr(resource, "admission", None)
    disposition_concept = getattr(admission, "dischargeDisposition", None)
    disposition = clinical_label(disposition_concept)
    facility_type = extension_code_display(resource, DISCHARGE_FACILITY_TYPE_EXTENSION)
    department = extension_code_display(resource, DISCHARGE_DEPARTMENT_EXTENSION)

    if disposition != "Unknown":
        destination = (
            "within the same hospital"
            if _has_code(disposition_concept, "37729005")
            else lower_first(disposition)
        )
        if department:
            sentences.append(
                f"The patient was transferred {destination} to "
                f"{clean_display(department).lower()}"
            )
        elif facility_type:
            sentences.append(
                f"The patient was discharged to {clean_display(facility_type).lower()}"
            )
        else:
            sentences.append(f"Discharge disposition: {destination}")

    post_acute = extension_boolean(resource, REQUIRED_POST_ACUTE_CARE_EXTENSION)
    if post_acute is True:
        sentences.append("Post-acute care was required")
    elif post_acute is False:
        sentences.append("Post-acute care was not required")

    if not sentences:
        return "Encounter information."
    return ". ".join(sentence.rstrip(".") for sentence in sentences) + "."


def location_summary(resource: Any) -> str:
    labels = [
        clinical_label(concept)
        for concept in getattr(resource, "type", None) or ()
    ]
    labels = [label for label in labels if label != "Unknown"]
    intensity = extension_code_display(resource, INITIAL_CARE_INTENSITY_EXTENSION)
    if intensity:
        labels.append(clean_display(intensity))
    if labels:
        return join_clinical(tuple(dict.fromkeys(labels)))
    return "care location"


def medication_details(
    medication: Any,
    context: StrokeCaseContext,
) -> tuple[str, tuple[str, ...]]:
    """Resolve a CodeableReference and return medication name and ingredients."""

    if medication is None:
        return "unknown medication", ()

    concept = getattr(medication, "concept", None)
    if concept is not None:
        return clinical_label(concept), ()

    reference = getattr(
        getattr(medication, "reference", None), "reference", None
    )
    resolved = resolve_resource(context, reference)
    if resolved is None:
        return "unknown medication", ()

    name = clinical_label(getattr(resolved, "code", None))
    ingredients: list[str] = []
    for ingredient in getattr(resolved, "ingredient", None) or ():
        item = getattr(ingredient, "item", None)
        ingredient_concept = getattr(item, "concept", None)
        if ingredient_concept is None:
            continue
        ingredient_name = clinical_label(ingredient_concept)
        if ingredient_name != "Unknown" and ingredient_name not in ingredients:
            ingredients.append(ingredient_name)
    return name, tuple(ingredients)


def dose_display(resource: Any) -> str | None:
    dose = getattr(getattr(resource, "dosage", None), "dose", None)
    if dose is None:
        return None
    value = getattr(dose, "value", None)
    unit = getattr(dose, "unit", None) or getattr(dose, "code", None)
    if value is None:
        return None
    return f"{format_number(value)} {unit}" if unit else format_number(value)


def observation_value_display(resource: Any) -> str | None:
    for attribute in (
        "valueInteger", "valueDecimal", "valueBoolean", "valueString"
    ):
        value = getattr(resource, attribute, None)
        if value is not None:
            if isinstance(value, bool):
                return "yes" if value else "no"
            return format_number(value)

    concept = getattr(resource, "valueCodeableConcept", None)
    if concept is not None:
        coding = _first_coding(concept)
        code = getattr(coding, "code", None) if coding else None
        display = clean_display(getattr(coding, "display", None) if coding else None)
        if code and display and display != code:
            return f"{code}, {lower_first(display)}"
        return display or code or "Unknown"

    quantity = getattr(resource, "valueQuantity", None)
    if quantity is not None:
        value = getattr(quantity, "value", None)
        unit = getattr(quantity, "unit", None) or getattr(quantity, "code", None)
        if value is not None and unit:
            return f"{format_number(value)} {unit}"
        if value is not None:
            return format_number(value)
    return None


def observation_context_code(resource: Any) -> str | None:
    extension = find_extension(resource, ASSESSMENT_CONTEXT_EXTENSION)
    concept = getattr(extension, "valueCodeableConcept", None) if extension else None
    coding = _first_coding(concept)
    return getattr(coding, "code", None) if coding else None


def observation_context_label(resource: Any) -> str | None:
    return {
        "admission": "at admission",
        "discharge": "at discharge",
        "discharge-or-7-days": "at discharge or seven days",
        "3-month": "at three-month follow-up",
    }.get(observation_context_code(resource))


def resolve_resource(context: StrokeCaseContext, reference: str | None) -> Any | None:
    if not reference:
        return None
    record = context.get_resource(str(reference))
    return record.resource if record is not None else None


def clinical_label(codeable_concept: Any) -> str:
    return clean_display(code_display(codeable_concept)) or "Unknown"


def code_display(codeable_concept: Any) -> str:
    if codeable_concept is None:
        return "Unknown"
    text = getattr(codeable_concept, "text", None)
    if text:
        return str(text)
    coding = _first_coding(codeable_concept)
    if coding is not None:
        return str(
            getattr(coding, "display", None)
            or getattr(coding, "code", None)
            or "Unknown"
        )
    return "Unknown"


def extension_code_display(resource: Any, url: str) -> str | None:
    extension = find_extension(resource, url)
    if extension is None:
        return None
    value = code_display(getattr(extension, "valueCodeableConcept", None))
    return None if value == "Unknown" else value


def extension_boolean(resource: Any, url: str) -> bool | None:
    extension = find_extension(resource, url)
    value = getattr(extension, "valueBoolean", None) if extension else None
    return value if isinstance(value, bool) else None


def find_extension(resource: Any, url: str) -> Any | None:
    for extension in getattr(resource, "extension", None) or ():
        if getattr(extension, "url", None) == url:
            return extension
    return None


def join_clinical(values: Iterable[str]) -> str:
    items = [str(value) for value in values if value]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def clean_display(value: Any) -> str:
    if value is None:
        return ""
    return _TRAILING_SEMANTIC_TAG.sub("", str(value)).strip()


def lower_first(value: str) -> str:
    return value[:1].lower() + value[1:] if value else value


def format_number(value: Any) -> str:
    if isinstance(value, Decimal):
        normalized = value.normalize()
        if normalized == normalized.to_integral():
            return str(normalized.quantize(Decimal("1")))
        return format(normalized, "f")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def format_fhir_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M %Z").strip()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.strftime("%Y-%m-%d %H:%M %Z").strip()


def _build_patient_history_narrative(
    *,
    context: StrokeCaseContext,
    title: str,
    records: tuple[StrokeCaseResource, ...],
) -> Narrative:
    conditions: list[str] = []
    medications: list[str] = []
    other: list[str] = []

    for record in records:
        resource = record.resource
        resource_type = resource.get_resource_type()
        if resource_type == "Condition":
            label = clinical_label(getattr(resource, "code", None))
            if label not in conditions:
                conditions.append(label)
        elif resource_type == "MedicationStatement":
            name, _ = medication_details(getattr(resource, "medication", None), context)
            if name not in medications:
                medications.append(name)
        else:
            other.append(resource_summary(resource, context))

    paragraphs: list[str] = []
    if conditions:
        paragraphs.append(
            "Relevant medical history includes "
            f"{join_clinical(tuple(lower_first(item) for item in conditions))}."
        )
    if medications:
        paragraphs.append(
            "Prior medication included "
            f"{join_clinical(tuple(lower_first(item) for item in medications))}."
        )
    paragraphs.extend(other)
    return _narrative(title=title, paragraphs=tuple(paragraphs))


def _build_encounter_section_narrative(
    *,
    context: StrokeCaseContext,
    title: str,
    records: tuple[StrokeCaseResource, ...],
    children: tuple[CompositionSection, ...],
) -> Narrative:
    return _narrative(
        title=title,
        paragraphs=tuple(resource_summary(record.resource, context) for record in records),
        child_titles=tuple(str(child.title) for child in children),
    )


def _blood_pressure_summary(
    components: Iterable[Any], context_label: str | None
) -> str | None:
    systolic = None
    diastolic = None
    unit = None
    for component in components:
        coding = _first_coding(getattr(component, "code", None))
        code = getattr(coding, "code", None) if coding else None
        quantity = getattr(component, "valueQuantity", None)
        value = getattr(quantity, "value", None) if quantity else None
        component_unit = (
            getattr(quantity, "unit", None) or getattr(quantity, "code", None)
        ) if quantity else None
        if code == "271649006":
            systolic = value
            unit = unit or component_unit
        elif code == "271650006":
            diastolic = value
            unit = unit or component_unit

    if systolic is None and diastolic is None:
        return None
    label = "Blood pressure"
    if context_label:
        label = f"{label} {context_label}"
    if systolic is not None and diastolic is not None:
        value = f"{format_number(systolic)}/{format_number(diastolic)}"
    elif systolic is not None:
        value = f"systolic {format_number(systolic)}"
    else:
        value = f"diastolic {format_number(diastolic)}"
    return f"{label}: {value}{f' {unit}' if unit else ''}."


def _observation_component_summary(component: Any) -> str:
    label = clinical_label(getattr(component, "code", None))
    for attribute in (
        "valueInteger", "valueDecimal", "valueBoolean", "valueString"
    ):
        value = getattr(component, attribute, None)
        if value is not None:
            return f"{label}: {format_number(value)}"
    concept = getattr(component, "valueCodeableConcept", None)
    if concept is not None:
        return f"{label}: {clinical_label(concept)}"
    quantity = getattr(component, "valueQuantity", None)
    if quantity is not None:
        value = getattr(quantity, "value", None)
        unit = getattr(quantity, "unit", None) or getattr(quantity, "code", None)
        return f"{label}: {format_number(value)}{f' {unit}' if unit else ''}"
    return label


def _medication_name_with_ingredients(
    name: str, ingredients: tuple[str, ...]
) -> str:
    if not ingredients:
        return name
    return f"{name}, containing {join_clinical(tuple(lower_first(i) for i in ingredients))}"


def _first_coding(codeable_concept: Any) -> Any | None:
    codings = getattr(codeable_concept, "coding", None) or ()
    return codings[0] if codings else None


def _first_code_display(codeable_concept: Any) -> str | None:
    value = code_display(codeable_concept)
    return None if value == "Unknown" else clean_display(value)


def _has_code(codeable_concept: Any, expected_code: str) -> bool:
    return any(
        getattr(coding, "code", None) == expected_code
        for coding in getattr(codeable_concept, "coding", None) or ()
    )


def _narrative(
    *,
    title: str | None,
    paragraphs: tuple[str, ...] = (),
    items: tuple[str, ...] = (),
    child_titles: tuple[str, ...] = (),
) -> Narrative:
    fragments: list[str] = []
    if title:
        fragments.append(f"<h2>{html.escape(title)}</h2>")
    for paragraph in paragraphs:
        if paragraph:
            fragments.append(f"<p>{html.escape(paragraph)}</p>")
    if items:
        fragments.append(
            "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"
        )
    if child_titles:
        fragments.append("<p>Structured subsections:</p>")
        fragments.append(
            "<ul>"
            + "".join(
                f"<li>{html.escape(child_title)}</li>"
                for child_title in child_titles
            )
            + "</ul>"
        )
    return Narrative(
        status="generated",
        div=(
            '<div xmlns="http://www.w3.org/1999/xhtml">'
            f"{''.join(fragments)}"
            "</div>"
        ),
    )
