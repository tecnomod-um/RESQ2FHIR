"""FHIR R5 registry answers for NCZI 2024 discharge medication questions.

A positive answer is represented by the existing MedicationRequest builder.
Negative and unknown answers are *not* medication orders: they are explicit
Observations about what the 2024 discharge register recorded.

Local Observation codes require definition in the authoritative RES-Q FHIR IG.
"""
from __future__ import annotations

from collections.abc import Mapping

from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.reference import Reference

from scripts.enum_models import Medications
from scripts.utils import safe_get_bool


STATUS_CODE_SYSTEM = (
    "http://qualityregistry.org/CodeSystem/"
    "discharge-medication-prescription-status-cs"
)

# The individual yes/no entries present in the 2024 Slovak source.
# Do not include derived "any" anticoagulant/antiplatelet fields here,
# because they are not independent original yes/no answers.
DISCHARGE_MEDICATION_2024 = {
    "discharge_asa": Medications.ASA,
    "discharge_clopidogrel": Medications.CLOPIDOGREL,
    "discharge_warfarin": Medications.WARFARIN,
    "discharge_heparin": Medications.HEPARIN,
    "discharge_doak": Medications.DOAC,
    "discharge_statin": Medications.STATIN,
    "discharge_other": Medications.OTHER_MEDICATION,
    "discharge_antidepressants": Medications.ANTIDEPRESSANT,
}


def _concept(system: str, code: str, display: str) -> CodeableConcept:
    return CodeableConcept(coding=[Coding(
        system=system, code=code, display=display,
    )])


def build_discharge_medication_answer(
    *,
    medication: Medications,
    answer: bool | None,
    patient_ref: str,
    encounter_ref: str,
) -> Observation:
    """Represent explicit NO, or documented UNKNOWN, without fabricating an order.

    TRUE remains a positive MedicationRequest in the existing workflow.
    UNKNOWN uses dataAbsentReason and never valueBoolean=false.
    """
    if answer is True:
        raise ValueError(
            "A prescribed medication should be represented by MedicationRequest"
        )

    observation = Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=_concept(
            STATUS_CODE_SYSTEM,
            "medication-prescribed-at-discharge",
            "Medication prescribed at discharge (registry answer)",
        ),
        component=[ObservationComponent(
            code=_concept(
                STATUS_CODE_SYSTEM,
                "medication-class",
                "Medication class queried at discharge",
            ),
            valueCodeableConcept=CodeableConcept(coding=[medication.to_coding()]),
        )],
    )
    if answer is False:
        observation.valueBoolean = False
    else:
        observation.dataAbsentReason = _concept(
            "http://terminology.hl7.org/CodeSystem/data-absent-reason",
            "unknown",
            "Unknown",
        )
    return observation


def build_discharge_medication_answers_2024(
    *,
    raw: Mapping[str, object],
    patient_ref: str,
    encounter_ref: str,
) -> list[Observation]:
    """Encode 2024 source answers, preserving true/false/unknown.

    - TRUE: existing MedicationRequest; not duplicated as Observation.
    - FALSE: explicit negative Observation.valueBoolean=false.
    - Field present with None: explicit Observation.dataAbsentReason=unknown.
    - Field absent from raw contract: no assertion; do not invent "unknown".

    The 2024 normalizer emits a stable column for each in-scope source field.
    Thus blank values in an included column are recorded as unknown. This is
    deliberately distinct from a field absent in a non-NCZI input contract.
    """
    answers = []
    for key, medication in DISCHARGE_MEDICATION_2024.items():
        if key not in raw:
            continue
        answer = safe_get_bool(raw, key, required=False)
        if answer is True:
            continue
        answers.append(build_discharge_medication_answer(
            medication=medication,
            answer=answer,
            patient_ref=patient_ref,
            encounter_ref=encounter_ref,
        ))
    return answers


def build_any_discharge_medication_answer(
    *, answer: bool | None, patient_ref: str, encounter_ref: str,
) -> Observation:
    """Represent the independent all-medications yes/no/unknown question."""
    obs = Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=_concept(
            STATUS_CODE_SYSTEM,
            "any-medication-prescribed-at-discharge",
            "Any medication prescribed at discharge (registry answer)",
        ),
    )
    if answer is None:
        obs.dataAbsentReason = _concept(
            "http://terminology.hl7.org/CodeSystem/data-absent-reason",
            "unknown",
            "Unknown",
        )
    else:
        obs.valueBoolean = answer
    return obs
