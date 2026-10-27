"""Reconcile normalized contract semantics before Bundle finalization.

The transformation is intentionally resource-oriented, so a small number of
normalized assertions can otherwise be lost when the source value that implies
a resource is present while its companion boolean is absent, or when resource
construction is nested under an unrelated branch.  This module repairs those
cases before the shared case context is indexed and serialized.

The repair is idempotent: running it more than once does not create duplicate
resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fhir.resources.codeableconcept import CodeableConcept

from scripts.enum_models import (
    CarotidStenosisLevel,
    DischargeSection,
    ImagingType,
    NoThrombectomyReason,
    NoThrombolysisReason,
    PerforationProcedures,
)
from scripts.fhir_resources.diagnosticReport import (
    build_carotid_arteries_imaging_diagnostic_report,
)
from scripts.fhir_resources.observation import build_observation_carotid_stenosis
from scripts.fhir_resources.procedure import (
    build_carotid_imaging_procedure,
    build_thrombectomy_procedure,
    build_thrombolysis_procedure,
)
from scripts.utils import safe_get, safe_get_bool

if TYPE_CHECKING:
    from scripts.modeling_context import StrokeCaseContext


STROKE_DIAGNOSIS_PROFILE = (
    "http://qualityregistry.org/StructureDefinition/stroke-diagnosis-condition-profile"
)


def _resource_type(resource: Any) -> str | None:
    getter = getattr(resource, "get_resource_type", None)
    return getter() if callable(getter) else None


def _concept_has(concept: Any, member: Any) -> bool:
    if concept is None or member is None:
        return False
    for coding in getattr(concept, "coding", None) or []:
        if (
            getattr(coding, "system", None) == member.system
            and getattr(coding, "code", None) == member.code
        ):
            return True
    return False


def _iter_entries(context: "StrokeCaseContext"):
    for entry in context.transaction_entries:
        if entry.resource is None:
            continue
        yield str(entry.fullUrl) if entry.fullUrl is not None else "", entry.resource


def _find_procedure(context: "StrokeCaseContext", member: Any):
    for full_url, resource in _iter_entries(context):
        if _resource_type(resource) != "Procedure":
            continue
        if _concept_has(getattr(resource, "code", None), member):
            return full_url, resource
    return None, None


def _find_profile_resource(
    context: "StrokeCaseContext",
    resource_type: str,
    profile_url: str,
) -> tuple[str | None, Any | None]:
    for full_url, resource in _iter_entries(context):
        if _resource_type(resource) != resource_type:
            continue
        profiles = getattr(getattr(resource, "meta", None), "profile", None) or []
        if profile_url in [str(profile) for profile in profiles]:
            return full_url, resource
    return None, None


def _set_status_reason(procedure: Any, reason: Any) -> None:
    procedure.status = "not-done"
    procedure.statusReason = CodeableConcept(coding=[reason.to_coding()])


def _repair_no_thrombolysis_reason(context: "StrokeCaseContext") -> None:
    raw_reason = safe_get(context.raw, "no_thrombolysis_reason", required=False)
    if raw_reason is None:
        return

    reason = NoThrombolysisReason.by_id(str(raw_reason))
    _, procedure = _find_procedure(context, PerforationProcedures.THROMBOLYSIS)

    if procedure is not None:
        _set_status_reason(procedure, reason)
        return

    condition_ref, _ = _find_profile_resource(
        context,
        "Condition",
        STROKE_DIAGNOSIS_PROFILE,
    )
    if context.patient_ref is None or context.encounter_ref is None:
        return

    procedure = build_thrombolysis_procedure(
        patient_ref=context.patient_ref,
        encounter_ref=context.encounter_ref,
        condition_ref=condition_ref or "",
        thrombolysis=False,
        post_acute_care=False,
        no_thrombolysis_reason_id=reason,
    )
    context.add_resource(
        procedure,
        sections=(DischargeSection.SIGNIFICANT_PROCEDURES,),
    )


def _repair_no_thrombectomy_reason(context: "StrokeCaseContext") -> None:
    raw_reason = safe_get(context.raw, "no_thrombectomy_reason", required=False)
    if raw_reason is None:
        return

    reason = NoThrombectomyReason.by_id(str(raw_reason))
    _, procedure = _find_procedure(context, PerforationProcedures.THROMBECTOMY)

    if procedure is not None:
        _set_status_reason(procedure, reason)
        return

    condition_ref, _ = _find_profile_resource(
        context,
        "Condition",
        STROKE_DIAGNOSIS_PROFILE,
    )
    if context.patient_ref is None or context.encounter_ref is None:
        return

    procedure = build_thrombectomy_procedure(
        thrombectomy=False,
        post_acute_care=False,
        patient_ref=context.patient_ref,
        encounter_ref=context.encounter_ref,
        condition_ref=condition_ref or "",
        no_thrombectomy_reason_id=reason,
        transfer_timestamp=safe_get(context.raw, "transfer_timestamp", required=False),
    )
    context.add_resource(
        procedure,
        sections=(DischargeSection.SIGNIFICANT_PROCEDURES,),
    )


def _repair_carotid_imaging(context: "StrokeCaseContext") -> None:
    carotid_imaging = safe_get_bool(
        context.raw,
        "carotid_arteries_imaging",
        required=False,
        default=False,
    )
    if carotid_imaging is not True:
        return

    _, existing = _find_procedure(context, ImagingType.CAROTID)
    if existing is not None:
        return

    if context.patient_ref is None or context.encounter_ref is None:
        return

    carotid_stenosis = safe_get_bool(
        context.raw,
        "carotid_stenosis",
        required=False,
        default=False,
    )
    stenosis_level_raw = safe_get(
        context.raw,
        "carotid_stenosis_level",
        required=False,
    )
    stenosis_level = (
        CarotidStenosisLevel.by_id(str(stenosis_level_raw))
        if stenosis_level_raw is not None
        else None
    )

    observation = build_observation_carotid_stenosis(
        patient_ref=context.patient_ref,
        encounter_ref=context.encounter_ref,
        carotid_stenosis=carotid_stenosis,
        carotid_stenosis_level=stenosis_level,
    )
    observation_ref = context.add_resource(
        observation,
        sections=(DischargeSection.SIGNIFICANT_RESULTS,),
    )

    report = build_carotid_arteries_imaging_diagnostic_report(
        patient_ref=context.patient_ref,
        encounter_ref=context.encounter_ref,
        observation_ref=observation_ref,
    )
    report_ref = context.add_resource(
        report,
        sections=(DischargeSection.SIGNIFICANT_RESULTS,),
    )

    procedure = build_carotid_imaging_procedure(
        patient_ref=context.patient_ref,
        encounter_ref=context.encounter_ref,
        diagnostic_report_ref=report_ref,
        carotid_arteries_imaging_done=True,
    )
    context.add_resource(procedure)


def repair_semantic_contract(context: "StrokeCaseContext") -> None:
    """Ensure reversible normalized assertions are represented in FHIR.

    Repairs three transformation defects detected by full-contract semantic
    preservation evaluation:

    * a populated no-thrombolysis reason must survive even when the treatment
      boolean is false or absent;
    * a populated no-thrombectomy reason must create/repair a not-done
      thrombectomy Procedure even when the treatment boolean is absent;
    * positive carotid imaging must not depend on the unrelated
      ``post_acute_care`` branch.
    """

    _repair_no_thrombolysis_reason(context)
    _repair_no_thrombectomy_reason(context)
    _repair_carotid_imaging(context)
