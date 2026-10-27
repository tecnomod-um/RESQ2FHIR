from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.enum_models import (
    AdmissionPathway,
    ImagingDone,
    ImagingType,
    NoThrombectomyReason,
    NoThrombolysisReason,
    ProcedureNotDoneReason,
    RiskFactor,
    ThrombectomyComplications,
)

from . import semantic_preservation as base


EXTRA_FIELDS = {
    "carotid_arteries_imaging",
    "imaging_done",
    "inhospital_stroke",
    "mt_complications_perforation",
    "no_thrombectomy_reason",
    "no_thrombolysis_reason",
    "onset_timestamp",
    "provider",
    "provider_id",
    "risk_smoker_last_10_years",
}

SUPPORTED_FIELDS = set(base.SUPPORTED_FIELDS) | EXTRA_FIELDS


def _clinical_status_code(condition: dict) -> str | None:
    codings = ((condition.get("clinicalStatus") or {}).get("coding") or [])
    return codings[0].get("code") if codings else None


def _organization_candidates(bundle: dict) -> list[dict]:
    """Return source-provider Organization resources from the transaction Bundle."""
    candidates = []
    for organization in base._resources(bundle, "Organization"):
        identifiers = organization.get("identifier") or []
        if any(
            identifier.get("system") == "https://stroke.qualityregistry.org"
            for identifier in identifiers
            if isinstance(identifier, dict)
        ):
            candidates.append(organization)
    return candidates


def _provider_name(bundle: dict, value: Any) -> bool:
    expected = str(value).strip().replace(" ", "-")
    return any(
        str(organization.get("name", "")) == expected
        for organization in _organization_candidates(bundle)
    )


def _provider_id(bundle: dict, value: Any) -> bool:
    expected = str(value).strip()
    return any(
        str(identifier.get("value", "")) == expected
        for organization in _organization_candidates(bundle)
        for identifier in organization.get("identifier") or []
        if isinstance(identifier, dict)
        and identifier.get("system") == "https://stroke.qualityregistry.org"
    )


def _carotid_arteries_imaging(bundle: dict, value: Any) -> bool | None:
    expected = base._as_bool(value)
    if expected is None:
        return None

    procedures = base._profile_resources(
        bundle, "Procedure", "stroke-carotid-imaging-procedure-profile"
    )
    if not procedures:
        procedures = [
            procedure
            for procedure in base._resources(bundle, "Procedure")
            if base._concept_has(
                procedure.get("code"), base._enum_coding(ImagingType.CAROTID)
            )
        ]

    if expected:
        return any(procedure.get("status") == "completed" for procedure in procedures)

    # A negative source assertion is preserved either by omitting the optional
    # carotid-imaging resource or by explicitly serializing a not-done Procedure.
    return not procedures or any(
        procedure.get("status") == "not-done" for procedure in procedures
    )


def _brain_imaging_procedures(bundle: dict) -> list[dict]:
    expected_codes = {
        base._enum_coding(member)
        for member in ImagingType
        if member != ImagingType.CAROTID
    }
    return [
        procedure
        for procedure in base._resources(bundle, "Procedure")
        if any(
            base._concept_has(procedure.get("code"), expected)
            for expected in expected_codes
        )
    ]


def _imaging_done(bundle: dict, value: Any) -> bool:
    member = ImagingDone.by_id(str(value))
    if member is None:
        return False

    procedures = _brain_imaging_procedures(bundle)
    if not procedures:
        return False

    if member == ImagingDone.YES:
        return any(procedure.get("status") == "completed" for procedure in procedures)
    if member == ImagingDone.NO:
        return any(procedure.get("status") == "not-done" for procedure in procedures)
    if member == ImagingDone.ELSEWHERE:
        expected_reason = base._enum_coding(ProcedureNotDoneReason.DONE_ELSEWHERE)
        return any(
            base._concept_has(procedure.get("statusReason"), expected_reason)
            for procedure in procedures
        )
    return False


def _inhospital_stroke(bundle: dict, value: Any) -> bool | None:
    expected = base._as_bool(value)
    if expected is None:
        return None

    encounter = base._encounter(bundle)
    if encounter is None:
        return False

    admit_source = (encounter.get("admission") or {}).get("admitSource")
    serialized = base._concept_has(
        admit_source, base._enum_coding(AdmissionPathway.INHOSPITAL_STROKE)
    )
    return serialized is expected


def _procedure_status_reason(bundle: dict, procedure_code: Any, reason: Any) -> bool:
    procedure = base._find_procedure(bundle, procedure_code)
    return bool(
        procedure
        and base._concept_has(
            procedure.get("statusReason"), base._enum_coding(reason)
        )
    )


def _thrombectomy_perforation(bundle: dict, value: Any) -> bool | None:
    expected = base._as_bool(value)
    if expected is None:
        return None

    procedure = base._find_procedure(bundle, base.PerforationProcedures.THROMBECTOMY)
    if procedure is None:
        return False

    perforation_code = base._enum_coding(ThrombectomyComplications.PERFORATION)
    found = any(
        base._concept_has(complication.get("concept"), perforation_code)
        for complication in procedure.get("complication") or []
        if isinstance(complication, dict)
    )
    return found is expected


def _onset_timestamp(bundle: dict, value: Any) -> bool:
    condition = base._stroke_condition(bundle)
    return bool(
        condition
        and base._as_datetime(condition.get("onsetDateTime"))
        == base._as_datetime(value)
    )


def _smoking_last_10_years(bundle: dict, value: Any) -> bool | None:
    """Read back the broad smoking-within-10-years assertion.

    The normalized source field is Boolean and does not retain the distinction
    between current and former smoking. Therefore a positive value accepts
    either a current-smoker or ex-smoker risk-factor representation. A negative
    value accepts either an explicit non-smoker concept or an inactive smoker
    condition. Absence of any reversible smoking representation is a mismatch,
    not a silent exclusion.
    """
    expected = base._as_bool(value)
    if expected is None:
        return None

    smoker = base._enum_coding(RiskFactor.Smoker)
    ex_smoker = base._enum_coding(RiskFactor.Ex_Smoker)
    non_smoker = base._enum_coding(RiskFactor.Non_Smoker)

    conditions = base._profile_resources(
        bundle, "Condition", "stroke-risk-factor-condition-profile"
    )

    if expected:
        return any(
            (
                base._concept_has(condition.get("code"), smoker)
                or base._concept_has(condition.get("code"), ex_smoker)
            )
            and _clinical_status_code(condition) != "inactive"
            for condition in conditions
        )

    return any(
        base._concept_has(condition.get("code"), non_smoker)
        or (
            base._concept_has(condition.get("code"), smoker)
            and _clinical_status_code(condition) == "inactive"
        )
        for condition in conditions
    )


def _check(field: str, value: Any, bundle: dict) -> bool | None:
    if field in base.SUPPORTED_FIELDS:
        return base._check(field, value, bundle)

    if field == "provider":
        return _provider_name(bundle, value)
    if field == "provider_id":
        return _provider_id(bundle, value)
    if field == "carotid_arteries_imaging":
        return _carotid_arteries_imaging(bundle, value)
    if field == "imaging_done":
        return _imaging_done(bundle, value)
    if field == "inhospital_stroke":
        return _inhospital_stroke(bundle, value)
    if field == "onset_timestamp":
        return _onset_timestamp(bundle, value)
    if field == "mt_complications_perforation":
        return _thrombectomy_perforation(bundle, value)
    if field == "no_thrombolysis_reason":
        member = NoThrombolysisReason.by_id(str(value))
        return bool(
            member
            and _procedure_status_reason(
                bundle, base.PerforationProcedures.THROMBOLYSIS, member
            )
        )
    if field == "no_thrombectomy_reason":
        member = NoThrombectomyReason.by_id(str(value))
        return bool(
            member
            and _procedure_status_reason(
                bundle, base.PerforationProcedures.THROMBECTOMY, member
            )
        )
    if field == "risk_smoker_last_10_years":
        return _smoking_last_10_years(bundle, value)
    return None


def _stroke_type_id(row: pd.Series) -> str | None:
    value = row.get("stroke_type")
    if base._missing(value):
        return None
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value).strip()


def _is_applicable(field: str, row: pd.Series) -> bool:
    if field in base.SUPPORTED_FIELDS:
        return base._is_applicable(field, row)

    thrombolysis = base._as_bool(row.get("thrombolysis"))
    thrombectomy = base._as_bool(row.get("thrombectomy"))
    wakeup_stroke = base._as_bool(row.get("wakeup_stroke"))

    if field == "onset_timestamp":
        # Wake-up strokes serialize sleep timing instead of source onset time.
        return wakeup_stroke is not True
    if field == "mt_complications_perforation":
        return thrombectomy is True
    if field == "no_thrombolysis_reason":
        return _stroke_type_id(row) == "1" and thrombolysis is not True
    if field == "no_thrombectomy_reason":
        return thrombectomy is not True
    return True


def evaluate_semantic_preservation(csv_path: Path, bundle_dir: Path) -> dict:
    """Evaluate all normalized fields with deterministic read-back comparators.

    Every normalized column is classified as supported or unsupported. Values
    are counted only when populated and contextually applicable. A supported
    field whose expected FHIR representation is absent is recorded as a
    mismatch rather than being dropped from the denominator.
    """
    df = pd.read_csv(csv_path, encoding="utf-8")
    per_field: dict[str, Counter] = {}
    comparable = matched = mismatched = missing_bundles = 0

    for idx, row in df.iterrows():
        raw_case = row.get("case")
        case = str(raw_case if not base._missing(raw_case) else f"case_{idx + 1}")
        bundle_path = base._transaction_bundle_path(bundle_dir, case)
        if bundle_path is None:
            missing_bundles += 1
            continue

        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        for field in df.columns:
            if field not in SUPPORTED_FIELDS:
                continue
            value = row.get(field)
            if base._missing(value):
                continue
            if not _is_applicable(field, row):
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

    normalized_fields = list(df.columns)
    supported = sorted(field for field in normalized_fields if field in SUPPORTED_FIELDS)
    unsupported = sorted(field for field in normalized_fields if field not in SUPPORTED_FIELDS)
    total_field_count = len(normalized_fields)

    return {
        "rows": len(df),
        "missingTransactionBundles": missing_bundles,
        "normalizedFieldCount": total_field_count,
        "supportedFieldCount": len(supported),
        "unsupportedFieldCount": len(unsupported),
        "fieldCoverageRate": (
            len(supported) / total_field_count if total_field_count else None
        ),
        "supportedFields": supported,
        "unsupportedFields": unsupported,
        "fieldsWithComparableValues": sorted(by_field),
        "comparableSourceValues": comparable,
        "matchedValues": matched,
        "mismatchedValues": mismatched,
        "preservationRate": (matched / comparable) if comparable else None,
        "byField": by_field,
    }
