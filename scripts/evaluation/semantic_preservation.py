from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.enum_models import (
    AdherenceCodes,
    AdmissionPathway,
    AssessmentContext,
    AtrialFibrillationOrFlutter,
    BleedingReason,
    DischargeDestination,
    DischargeFacilityDepartment,
    FunctionalScore,
    HospitalizedIn,
    ImagingType,
    Medications,
    MRsScore,
    MTiciScore,
    PerforationProcedures,
    RiskFactor,
    Sex,
    SpecificFinding,
    StrokeEtiology,
    StrokeType,
    SwallowingScreeningDone,
    SwallowingScreeningTiming,
    SwallowingScreeningType,
    TimingMetricCodes,
    VitalSigns,
)


def _missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and not value.strip()


def _as_bool(value: Any) -> bool | None:
    if _missing(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "t"}:
        return True
    if text in {"false", "0", "no", "n", "f"}:
        return False
    return None


def _as_number(value: Any) -> int | float | None:
    if _missing(value):
        return None
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def _as_datetime(value: Any) -> str | None:
    if _missing(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    if getattr(parsed, "tzinfo", None) is not None:
        parsed = parsed.tz_convert(None)
    return parsed.isoformat(timespec="seconds")


def _coding_tuple(coding: Any) -> tuple[str | None, str | None]:
    if coding is None:
        return (None, None)
    if isinstance(coding, dict):
        return coding.get("system"), coding.get("code")
    return getattr(coding, "system", None), getattr(coding, "code", None)


def _enum_coding(member: Any) -> tuple[str | None, str | None]:
    return _coding_tuple(member.to_coding())


def _concept_has(concept: dict | None, expected: tuple[str | None, str | None]) -> bool:
    return isinstance(concept, dict) and any(
        _coding_tuple(coding) == expected for coding in concept.get("coding") or []
    )


def _resources(bundle: dict, resource_type: str | None = None) -> list[dict]:
    result = []
    for entry in bundle.get("entry") or []:
        resource = entry.get("resource") if isinstance(entry, dict) else None
        if isinstance(resource, dict) and (
            resource_type is None or resource.get("resourceType") == resource_type
        ):
            result.append(resource)
    return result


def _has_profile(resource: dict, suffix: str) -> bool:
    return any(
        str(profile).endswith(suffix)
        for profile in ((resource.get("meta") or {}).get("profile") or [])
    )


def _profile_resources(bundle: dict, resource_type: str, suffix: str) -> list[dict]:
    return [
        resource
        for resource in _resources(bundle, resource_type)
        if _has_profile(resource, suffix)
    ]


def _extensions(resource: dict, suffix: str) -> list[dict]:
    return [
        ext
        for ext in (resource.get("extension") or [])
        if isinstance(ext, dict) and str(ext.get("url", "")).endswith(suffix)
    ]


def _extension_code(resource: dict, suffix: str, expected: tuple[str | None, str | None]) -> bool:
    return any(
        _concept_has(ext.get("valueCodeableConcept"), expected)
        for ext in _extensions(resource, suffix)
    )


def _extension_bool(resource: dict, suffix: str, expected: bool) -> bool:
    return any(ext.get("valueBoolean") is expected for ext in _extensions(resource, suffix))


def _find_observation(bundle: dict, code_member: Any, context: Any | None = None) -> dict | None:
    expected_code = _enum_coding(code_member)
    for obs in _resources(bundle, "Observation"):
        if not _concept_has(obs.get("code"), expected_code):
            continue
        if context is not None and not _extension_code(
            obs, "observation-timing-context-ext", _enum_coding(context)
        ):
            continue
        return obs
    return None


def _obs_integer(bundle: dict, code_member: Any, expected: Any, context: Any | None = None) -> bool:
    obs = _find_observation(bundle, code_member, context)
    return bool(obs and _as_number(obs.get("valueInteger")) == _as_number(expected))


def _obs_quantity(bundle: dict, code_member: Any, expected: Any) -> bool:
    obs = _find_observation(bundle, code_member)
    return bool(
        obs
        and _as_number((obs.get("valueQuantity") or {}).get("value"))
        == _as_number(expected)
    )


def _obs_code(bundle: dict, code_member: Any, value_member: Any, context: Any | None = None) -> bool:
    obs = _find_observation(bundle, code_member, context)
    return bool(
        obs and _concept_has(obs.get("valueCodeableConcept"), _enum_coding(value_member))
    )


def _bp_component(bundle: dict, component_member: Any, expected: Any) -> bool:
    obs = _find_observation(bundle, VitalSigns.TAKE_VS)
    if not obs:
        return False
    expected_code = _enum_coding(component_member)
    for component in obs.get("component") or []:
        if _concept_has(component.get("code"), expected_code):
            return (
                _as_number((component.get("valueQuantity") or {}).get("value"))
                == _as_number(expected)
            )
    return False


def _encounter(bundle: dict) -> dict | None:
    items = _profile_resources(bundle, "Encounter", "stroke-encounter-profile")
    return items[0] if items else None


def _stroke_condition(bundle: dict) -> dict | None:
    items = _profile_resources(bundle, "Condition", "stroke-diagnosis-condition-profile")
    return items[0] if items else None


def _find_procedure(bundle: dict, code_member: Any) -> dict | None:
    expected = _enum_coding(code_member)
    for procedure in _resources(bundle, "Procedure"):
        if _concept_has(procedure.get("code"), expected):
            return procedure
    return None


RISK_FACTORS = {
    "risk_hypertension": RiskFactor.Hypertension,
    "risk_diabetes": RiskFactor.Diabetes,
    "risk_hyperlipidemia": RiskFactor.Hyperlipidemia,
    "risk_previous_stroke": RiskFactor.PreviousStroke,
    "risk_previous_ischemic_stroke": RiskFactor.PreviousIschemicStroke,
    "risk_previous_hemorrhagic_stroke": RiskFactor.PreviousHemorrhagicStroke,
    "risk_atrial_fibrillation": RiskFactor.AtrialFibrillation,
    "risk_coronary_artery_disease_or_myocardial_infarction": RiskFactor.CoronaryArteryDisease,
}

PRIOR_MEDS = {
    "before_onset_antidiabetics": Medications.ANTIDIABETIC,
    "before_onset_antihypertensives": Medications.ANTIHYPERTENSIVE,
    "before_onset_any_anticoagulant": Medications.ANTICOAGULANT,
    "before_onset_any_antiplatelet": Medications.ANTIPLATELET,
    "before_onset_asa": Medications.ASA,
    "before_onset_clopidogrel": Medications.CLOPIDOGREL,
    "before_onset_contraception": Medications.CONTRACEPTION,
    "before_onset_other_anticoagulant": Medications.OTHER_ANTICOAGULANT,
    "before_onset_statin": Medications.STATIN,
    "before_onset_warfarin": Medications.WARFARIN,
}

DISCHARGE_MEDS = {
    "discharge_any_anticoagulant": Medications.ANTICOAGULANT,
    "discharge_any_antiplatelet": Medications.ANTIPLATELET,
    "discharge_heparin": Medications.HEPARIN,
    "discharge_asa": Medications.ASA,
    "discharge_clopidogrel": Medications.CLOPIDOGREL,
    "discharge_other": Medications.OTHER_MEDICATION,
    "discharge_statin": Medications.STATIN,
    "discharge_warfarin": Medications.WARFARIN,
}

STROKE_ETIOLOGY = {
    "stroke_etiology_cardioembolism": StrokeEtiology.CARDIOEMBOLYSM,
    "stroke_etiology_la_atherosclerosis": StrokeEtiology.ATHEROSCLEROSIS,
    "stroke_etiology_lacunar": StrokeEtiology.LACUNAR,
    "stroke_etiology_cryptogenic_stroke": StrokeEtiology.CRYPTOGENIC_STROKE,
    "stroke_etiology_other": StrokeEtiology.OTHER,
}

BLEEDING_REASONS = {
    "bleeding_reason_aneurysm": BleedingReason.ANEURYSM,
    "bleeding_reason_malformation": BleedingReason.MALFORMATION,
    "bleeding_reason_other": BleedingReason.OTHER,
}

SUPPORTED_FIELDS = {
    "case", "sex", "age", "hospital_timestamp", "discharge_date",
    "arrival_mode_id", "discharge_destination", "discharge_facility_department",
    "post_acute_care", "hospitalized_in", "wakeup_stroke", "stroke_type",
    "nihss_score", "prestroke_mrs", "discharge_mrs", "three_m_mrs",
    "discharge_nihss_score", "systolic_pressure", "diastolic_pressure",
    "imaging_type", "imaging_timestamp", "thrombolysis", "bolus_timestamp",
    "thrombectomy", "puncture_timestamp", "reperfusion_timestamp",
    "mtici_score", "atrial_fibrillation_or_flutter",
    "swallowing_screening_done", "swallowing_screening_type",
    "swallowing_screening_timing", "door_to_needle", "door_to_groin",
    *RISK_FACTORS.keys(), *PRIOR_MEDS.keys(), *DISCHARGE_MEDS.keys(),
    *STROKE_ETIOLOGY.keys(), *BLEEDING_REASONS.keys(),
}


def _patient_identifier(bundle: dict, expected: Any) -> bool:
    return any(
        str(identifier.get("value")) == str(expected)
        for patient in _resources(bundle, "Patient")
        for identifier in patient.get("identifier") or []
    )


def _patient_sex(bundle: dict, expected: Any) -> bool:
    member = Sex.by_id(str(expected))
    return bool(
        member and any(
            _extension_code(patient, "gender-snomed-ext", _enum_coding(member))
            for patient in _resources(bundle, "Patient")
        )
    )


def _encounter_admission_code(bundle: dict, element: str, member: Any) -> bool:
    encounter = _encounter(bundle)
    return bool(
        encounter
        and _concept_has((encounter.get("admission") or {}).get(element), _enum_coding(member))
    )


def _encounter_extension_code(bundle: dict, suffix: str, member: Any) -> bool:
    encounter = _encounter(bundle)
    return bool(encounter and _extension_code(encounter, suffix, _enum_coding(member)))


def _encounter_extension_bool(bundle: dict, suffix: str, expected: bool) -> bool:
    encounter = _encounter(bundle)
    return bool(encounter and _extension_bool(encounter, suffix, expected))


def _encounter_period(bundle: dict, element: str, expected: Any) -> bool:
    encounter = _encounter(bundle)
    return bool(
        encounter
        and _as_datetime((encounter.get("actualPeriod") or {}).get(element))
        == _as_datetime(expected)
    )


def _risk_factor(bundle: dict, field: str, value: Any) -> bool:
    expected = _as_bool(value)
    member = RISK_FACTORS[field]
    status = "inactive"
    if expected is True:
        status = "remission" if field in {
            "risk_previous_stroke",
            "risk_previous_ischemic_stroke",
            "risk_previous_hemorrhagic_stroke",
        } else "active"
    for condition in _profile_resources(
        bundle, "Condition", "stroke-risk-factor-condition-profile"
    ):
        if not _concept_has(condition.get("code"), _enum_coding(member)):
            continue
        coding = ((condition.get("clinicalStatus") or {}).get("coding") or [{}])[0]
        return coding.get("code") == status
    return False


def _prior_med(bundle: dict, field: str, value: Any) -> bool:
    expected = _as_bool(value)
    medication_code = _enum_coding(PRIOR_MEDS[field])
    adherence = AdherenceCodes.TAKING if expected is True else AdherenceCodes.NOT_TAKING
    for statement in _profile_resources(
        bundle, "MedicationStatement", "prior-medication-statement-profile"
    ):
        medication = ((statement.get("medication") or {}).get("concept") or {})
        if not _concept_has(medication, medication_code):
            continue
        adherence_concept = ((statement.get("adherence") or {}).get("code") or {})
        return _concept_has(adherence_concept, _enum_coding(adherence))
    return False


def _discharge_med(bundle: dict, field: str, value: Any) -> bool:
    expected = _as_bool(value)
    medication_code = _enum_coding(DISCHARGE_MEDS[field])
    found = any(
        _concept_has(((request.get("medication") or {}).get("concept") or {}), medication_code)
        for request in _profile_resources(
            bundle, "MedicationRequest", "discharge-medication-request-profile"
        )
    )
    return found if expected is True else not found


def _positive_condition_extension(
    bundle: dict, suffix: str, member: Any, value: Any
) -> bool | None:
    if _as_bool(value) is not True:
        return None
    condition = _stroke_condition(bundle)
    return bool(condition and _extension_code(condition, suffix, _enum_coding(member)))


def _procedure_status(bundle: dict, code_member: Any, value: Any) -> bool:
    procedure = _find_procedure(bundle, code_member)
    expected = _as_bool(value)
    return bool(
        procedure
        and procedure.get("status") == ("completed" if expected is True else "not-done")
    )


def _procedure_time(bundle: dict, code_member: Any, value: Any, key: str) -> bool:
    procedure = _find_procedure(bundle, code_member)
    if not procedure:
        return False
    if key == "dateTime":
        actual = procedure.get("occurrenceDateTime")
    else:
        actual = (procedure.get("occurrencePeriod") or {}).get(key)
    return _as_datetime(actual) == _as_datetime(value)


def _imaging_type(bundle: dict, value: Any) -> bool:
    member = ImagingType.by_id(str(value))
    return bool(member and _find_procedure(bundle, member))


def _imaging_timestamp(bundle: dict, value: Any) -> bool:
    expected = _as_datetime(value)
    for procedure in _resources(bundle, "Procedure"):
        actual = _as_datetime(procedure.get("occurrenceDateTime"))
        if actual != expected:
            continue
        if any(
            _concept_has(procedure.get("code"), _enum_coding(member))
            for member in ImagingType
        ):
            return True
    return False


def _hospitalized_in(bundle: dict, value: Any) -> bool:
    member = HospitalizedIn.by_id(str(value))
    return bool(
        member and any(
            _extension_code(location, "initial-care-intensity-ext", _enum_coding(member))
            for location in _profile_resources(
                bundle, "Location", "hospitalized-location-profile"
            )
        )
    )


def _swallowing(bundle: dict, field: str, value: Any) -> bool:
    procedures = _profile_resources(bundle, "Procedure", "stroke-swallow-procedure-profile")
    if not procedures:
        return False
    procedure = procedures[0]

    if field == "swallowing_screening_done":
        member = SwallowingScreeningDone.by_id(str(value))
        if member == SwallowingScreeningDone.YES:
            return procedure.get("status") == "completed"
        if member in {SwallowingScreeningDone.NO, SwallowingScreeningDone.NOT_APPLICABLE}:
            return procedure.get("status") == "not-done"
        return procedure.get("status") == "unknown"

    if field == "swallowing_screening_type":
        member = SwallowingScreeningType.by_id(str(value))
        return bool(member and _concept_has(procedure.get("code"), _enum_coding(member)))

    member = SwallowingScreeningTiming.by_id(str(value))
    return bool(
        member
        and _extension_code(
            procedure, "procedure-timing-context-ext", _enum_coding(member)
        )
    )


def _check(field: str, value: Any, bundle: dict) -> bool | None:
    if field == "case":
        return _patient_identifier(bundle, value)
    if field == "sex":
        return _patient_sex(bundle, value)
    if field == "age":
        return _obs_integer(bundle, FunctionalScore.AGE, value)
    if field == "hospital_timestamp":
        return _encounter_period(bundle, "start", value)
    if field == "discharge_date":
        return _encounter_period(bundle, "end", value)
    if field == "arrival_mode_id":
        member = AdmissionPathway.by_id(str(value))
        return bool(member and _encounter_admission_code(bundle, "admitSource", member))
    if field == "discharge_destination":
        member = DischargeDestination.by_id(str(value))
        return bool(member and _encounter_admission_code(bundle, "dischargeDisposition", member))
    if field == "discharge_facility_department":
        member = DischargeFacilityDepartment.by_id(str(value))
        return bool(
            member
            and _encounter_extension_code(
                bundle, "discharge-department-service-ext", member
            )
        )
    if field == "post_acute_care":
        expected = _as_bool(value)
        return None if expected is None else _encounter_extension_bool(
            bundle, "required-post-acute-care-ext", expected
        )
    if field == "hospitalized_in":
        return _hospitalized_in(bundle, value)
    if field == "stroke_type":
        member = StrokeType.by_id(str(value))
        condition = _stroke_condition(bundle)
        return bool(
            member and condition and _concept_has(condition.get("code"), _enum_coding(member))
        )
    if field == "wakeup_stroke":
        expected = _as_bool(value)
        condition = _stroke_condition(bundle)
        return None if expected is None else bool(
            condition and _extension_bool(condition, "wakeup-stroke-ext", expected)
        )
    if field == "nihss_score":
        return _obs_integer(bundle, FunctionalScore.NIHSS, value, AssessmentContext.ADMISSION)
    if field == "discharge_nihss_score":
        return _obs_integer(bundle, FunctionalScore.NIHSS, value, AssessmentContext.DISCHARGE)
    if field in {"prestroke_mrs", "discharge_mrs", "three_m_mrs"}:
        member = MRsScore.by_id(str(int(float(value))))
        context = {
            "prestroke_mrs": AssessmentContext.PRESTROKE,
            "discharge_mrs": AssessmentContext.DISCHARGE,
            "three_m_mrs": AssessmentContext.THREE_MONTHS,
        }[field]
        return bool(member and _obs_code(bundle, FunctionalScore.MRS, member, context))
    if field == "systolic_pressure":
        return _bp_component(bundle, VitalSigns.SYSTOLIC, value)
    if field == "diastolic_pressure":
        return _bp_component(bundle, VitalSigns.DIASTOLIC, value)
    if field == "imaging_type":
        return _imaging_type(bundle, value)
    if field == "imaging_timestamp":
        return _imaging_timestamp(bundle, value)
    if field == "thrombolysis":
        return _procedure_status(bundle, PerforationProcedures.THROMBOLYSIS, value)
    if field == "bolus_timestamp":
        return _procedure_time(bundle, PerforationProcedures.THROMBOLYSIS, value, "start")
    if field == "thrombectomy":
        return _procedure_status(bundle, PerforationProcedures.THROMBECTOMY, value)
    if field == "puncture_timestamp":
        return _procedure_time(bundle, PerforationProcedures.THROMBECTOMY, value, "start")
    if field == "reperfusion_timestamp":
        return _procedure_time(bundle, PerforationProcedures.THROMBECTOMY, value, "end")
    if field == "mtici_score":
        member = MTiciScore.by_id(str(value))
        return bool(member and _obs_code(bundle, SpecificFinding.MTICI, member))
    if field == "atrial_fibrillation_or_flutter":
        member = AtrialFibrillationOrFlutter.by_id(str(value))
        return bool(
            member and _obs_code(bundle, SpecificFinding.ATRIAL_FIBRILLATION_FLUTTER, member)
        )
    if field == "door_to_needle":
        return _obs_quantity(bundle, TimingMetricCodes.DOOR_TO_NEEDLE, value)
    if field == "door_to_groin":
        return _obs_quantity(bundle, TimingMetricCodes.DOOR_TO_GROIN, value)
    if field in RISK_FACTORS:
        return None if _as_bool(value) is None else _risk_factor(bundle, field, value)
    if field in PRIOR_MEDS:
        return None if _as_bool(value) is None else _prior_med(bundle, field, value)
    if field in DISCHARGE_MEDS:
        return None if _as_bool(value) is None else _discharge_med(bundle, field, value)
    if field in STROKE_ETIOLOGY:
        return _positive_condition_extension(
            bundle, "ischemic-stroke-etiology-ext", STROKE_ETIOLOGY[field], value
        )
    if field in BLEEDING_REASONS:
        return _positive_condition_extension(
            bundle,
            "hemorrhagic-stroke-bleeding-reason-ext",
            BLEEDING_REASONS[field],
            value,
        )
    if field.startswith("swallowing_screening_"):
        return _swallowing(bundle, field, value)
    return None


def _transaction_bundle_path(bundle_dir: Path, case: str) -> Path | None:
    for candidate in (
        bundle_dir / f"{case}.json",
        bundle_dir / f"{case}.transaction.json",
    ):
        if candidate.exists():
            return candidate
    return None


def evaluate_semantic_preservation(csv_path: Path, bundle_dir: Path) -> dict:
    """Compare normalized source values with their serialized FHIR representation.

    The returned report is aggregate-only: it contains counts and rates, never
    patient-level source or target values.
    """
    df = pd.read_csv(csv_path, encoding="utf-8")
    per_field: dict[str, Counter] = {}
    comparable = matched = mismatched = missing_bundles = 0

    for idx, row in df.iterrows():
        raw_case = row.get("case")
        case = str(raw_case if not _missing(raw_case) else f"case_{idx + 1}")
        bundle_path = _transaction_bundle_path(bundle_dir, case)
        if bundle_path is None:
            missing_bundles += 1
            continue

        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        for field in df.columns:
            if field not in SUPPORTED_FIELDS:
                continue
            value = row.get(field)
            if _missing(value):
                continue

            result = _check(field, value, bundle)
            if result is None:
                continue

            comparable += 1
            stats = per_field.setdefault(field, Counter())
            stats["comparable"] += 1
            if result:
                matched += 1
                stats["matched"] += 1
            else:
                mismatched += 1
                stats["mismatched"] += 1

    by_field = {}
    for field, stats in sorted(per_field.items()):
        n = stats["comparable"]
        by_field[field] = {
            "comparable": n,
            "matched": stats["matched"],
            "mismatched": stats["mismatched"],
            "preservationRate": (stats["matched"] / n) if n else None,
        }

    supported = sorted(field for field in df.columns if field in SUPPORTED_FIELDS)
    unsupported = sorted(field for field in df.columns if field not in SUPPORTED_FIELDS)

    return {
        "rows": len(df),
        "missingTransactionBundles": missing_bundles,
        "supportedFields": supported,
        "unsupportedFields": unsupported,
        "comparableSourceValues": comparable,
        "matchedValues": matched,
        "mismatchedValues": mismatched,
        "preservationRate": (matched / comparable) if comparable else None,
        "byField": by_field,
    }
