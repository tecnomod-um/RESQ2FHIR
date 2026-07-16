"""Deterministic clinical synthesis for the RESQ discharge document."""

from __future__ import annotations

import html
from typing import Any

from fhir.resources.narrative import Narrative

from scripts.discharge_summary.narrative import (
    clinical_label,
    join_clinical,
    lower_first,
    medication_administration_summary,
    medication_details,
    observation_context_code,
    observation_value_display,
)
from scripts.enum_models import DischargeSection
from scripts.modeling_context import StrokeCaseContext, StrokeCaseResource


AGE_CODE = "445518008"
NIHSS_CODE = "450743008"
MRS_CODE = "1255866005"


def build_clinical_synthesis_narrative(
    context: StrokeCaseContext,
) -> Narrative | None:
    """Create a concise clinical synthesis from already modeled FHIR resources."""

    sentences: list[str] = []

    demographics = _demographics(context)
    diagnosis = _primary_diagnosis(context)
    admission_nihss = _score_value(context, NIHSS_CODE, "admission")

    opening_parts: list[str] = []
    if demographics:
        opening_parts.append(demographics)
    if diagnosis:
        if opening_parts:
            opening_parts.append(f"was admitted with {lower_first(diagnosis)}")
        else:
            opening_parts.append(f"The patient was admitted with {lower_first(diagnosis)}")
    if opening_parts:
        sentence = " ".join(opening_parts)
        if admission_nihss is not None:
            sentence += f" and an admission NIHSS score of {admission_nihss}"
        sentences.append(sentence + ".")
    elif admission_nihss is not None:
        sentences.append(f"The admission NIHSS score was {admission_nihss}.")

    history = _relevant_history(context)
    if history:
        sentences.append(
            "Relevant medical history included "
            f"{join_clinical(tuple(lower_first(item) for item in history))}."
        )

    treatments = _treatments(context)
    if treatments:
        sentences.append(
            "Significant treatment included "
            f"{join_clinical(tuple(lower_first(item) for item in treatments))}."
        )

    discharge_nihss = _score_value(context, NIHSS_CODE, "discharge")
    discharge_mrs = _score_value(context, MRS_CODE, "discharge")
    if discharge_nihss is not None and discharge_mrs is not None:
        sentences.append(
            f"At discharge, the NIHSS score was {discharge_nihss} and the "
            f"modified Rankin Scale score was {discharge_mrs}."
        )
    elif discharge_nihss is not None:
        sentences.append(f"At discharge, the NIHSS score was {discharge_nihss}.")
    elif discharge_mrs is not None:
        sentences.append(
            f"At discharge, the modified Rankin Scale score was {discharge_mrs}."
        )

    medications = _discharge_medications(context)
    if medications:
        sentences.append(
            "Discharge medication included "
            f"{join_clinical(tuple(lower_first(item) for item in medications))}."
        )

    disposition = _disposition(context)
    if disposition:
        sentences.append(disposition)

    if not sentences:
        return None

    return Narrative(
        status="generated",
        div=(
            '<div xmlns="http://www.w3.org/1999/xhtml">'
            "<h2>Clinical Synthesis</h2>"
            f"<p>{html.escape(' '.join(sentences))}</p>"
            "</div>"
        ),
    )


def _demographics(context: StrokeCaseContext) -> str | None:
    age = _observation_value_by_code(context, AGE_CODE)
    patient = _patient(context)
    sex = None
    if patient is not None:
        for extension in getattr(patient, "extension", None) or ():
            concept = getattr(extension, "valueCodeableConcept", None)
            label = clinical_label(concept)
            if label.lower() in {"male", "female", "indeterminate sex"}:
                sex = label.lower()
                break

    if age is not None and sex:
        return f"An {age}-year-old {sex} patient"
    if age is not None:
        return f"An {age}-year-old patient"
    if sex:
        return f"A {sex} patient"
    return None


def _primary_diagnosis(context: StrokeCaseContext) -> str | None:
    for record in context.resources:
        if record.resource_type != "Condition":
            continue
        if DischargeSection.DIAGNOSTIC_SUMMARY in record.sections:
            return clinical_label(getattr(record.resource, "code", None))
    return None


def _relevant_history(context: StrokeCaseContext) -> tuple[str, ...]:
    values: list[str] = []
    for record in context.resources:
        if record.resource_type != "Condition":
            continue
        if not {
            DischargeSection.PATIENT_HISTORY,
            DischargeSection.PROBLEM_LIST,
        }.intersection(record.sections):
            continue
        label = clinical_label(getattr(record.resource, "code", None))
        if label not in values:
            values.append(label)
    return tuple(values)


def _treatments(context: StrokeCaseContext) -> tuple[str, ...]:
    values: list[str] = []
    for record in context.resources:
        if record.resource_type == "MedicationAdministration" and (
            DischargeSection.PHARMACOTHERAPY in record.sections
        ):
            summary = medication_administration_summary(record.resource, context)
            summary = summary.rstrip(".")
            if summary not in values:
                values.append(summary)
        elif record.resource_type == "Procedure" and (
            DischargeSection.SIGNIFICANT_PROCEDURES in record.sections
        ):
            label = clinical_label(getattr(record.resource, "code", None))
            if label not in values:
                values.append(label)
    return tuple(values)


def _discharge_medications(context: StrokeCaseContext) -> tuple[str, ...]:
    values: list[str] = []
    for record in context.resources:
        if record.resource_type != "MedicationRequest":
            continue
        if DischargeSection.DISCHARGE_MEDICATIONS not in record.sections:
            continue
        name, ingredients = medication_details(
            getattr(record.resource, "medication", None), context
        )
        label = name
        if ingredients:
            label = f"{name} containing {join_clinical(ingredients)}"
        if label not in values:
            values.append(label)
    return tuple(values)


def _disposition(context: StrokeCaseContext) -> str | None:
    encounter = _encounter(context)
    if encounter is None:
        return None
    admission = getattr(encounter, "admission", None)
    concept = getattr(admission, "dischargeDisposition", None)
    coding = (getattr(concept, "coding", None) or [None])[0]
    code = getattr(coding, "code", None) if coding else None
    display = clinical_label(concept)
    if code == "37729005":
        return "The patient was transferred within the same hospital."
    if display != "Unknown":
        return f"Discharge disposition was {lower_first(display)}."
    return None


def _score_value(
    context: StrokeCaseContext,
    code: str,
    assessment_context: str,
) -> str | None:
    for record in context.resources:
        resource = record.resource
        if record.resource_type != "Observation":
            continue
        if not _has_code(resource, code):
            continue
        if observation_context_code(resource) != assessment_context:
            continue
        value = observation_value_display(resource)
        if value is not None:
            return value.split(",", 1)[0]
    return None


def _observation_value_by_code(
    context: StrokeCaseContext,
    code: str,
) -> str | None:
    for record in context.resources:
        if record.resource_type == "Observation" and _has_code(record.resource, code):
            return observation_value_display(record.resource)
    return None


def _has_code(resource: Any, expected_code: str) -> bool:
    return any(
        getattr(coding, "code", None) == expected_code
        for coding in getattr(getattr(resource, "code", None), "coding", None) or ()
    )


def _patient(context: StrokeCaseContext) -> Any | None:
    if not context.patient_ref:
        return None
    record = context.get_resource(context.patient_ref)
    return record.resource if record else None


def _encounter(context: StrokeCaseContext) -> Any | None:
    if not context.encounter_ref:
        return None
    record = context.get_resource(context.encounter_ref)
    return record.resource if record else None
