"""
Normalize Slovak/RES-Q CSV exports to the internal registry contract.

The FHIR builders expect a stable set of field names and enum identifiers.
This adapter keeps source-specific spellings, booleans, and labels out of the
FHIR transformation layer.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from scripts import enum_models as enums


logger = logging.getLogger(__name__)


COLUMN_ALIASES = {
    "case_id": "case",
    "arrival_mode": "arrival_mode_id",
    "aspects_score": "aspect_score",
    "cha2ds2_vasc_score": "chads2_vasc_score",
    "discharge_to_three_m_contact": "discharge_to_three_month_contact",
    "iv_antihypertensive_timestamp": "iv_antihypertensive_timing",
    "infratentorial_hemorrhage": "ich_infratentorial",
    "supratentorial_hemorrhage": "ich_supratentorial",
    "ich_subarachnoid_hemorrhage": "subarachnoid_hemorrhage",
    "perfusion_deficit_found": "perfusion_found",
    "perfusion_deficit_anterior": "perfusion_anterior",
    "perfusion_deficit_posterior": "perfusion_posterior",
    "perfusion_deficit_carotid": "perfusion_carotid",
    "perfusion_deficit_bilateral_stenosis": "perfusion_bilateral_stenosis",
    "perfusion_core_volume": "perfusion_volume",
    "carotid_endarterectomy": "carotid_endardectomy",
    "carotid_endarterectomy_timing": "carotid_endardectomy_timing",
}


FIELD_ENUMS = {
    "sex": enums.Sex,
    "admission_department": enums.AdmissionDepartment,
    "arrival_mode_id": enums.AdmissionPathway,
    "atrial_fibrillation_or_flutter": enums.AtrialFibrillationOrFlutter,
    "carotid_stenosis_level": enums.CarotidStenosisLevel,
    "discharge_destination": enums.DischargeDestination,
    "discharge_facility_department": enums.DischargeFacilityDepartment,
    "discharge_facility_type": enums.DischargeFacilityType,
    "first_contact_place": enums.FirstContactPlace,
    "gcs_level": enums.GCSScore,
    "hospitalized_in": enums.HospitalizedIn,
    "imaging_done": enums.ImagingDone,
    "imaging_type": enums.ImagingType,
    "inr_mode": enums.INRmode,
    "insulin_on_hyperglycemia_timing": enums.InsulinOnHyperglycemiaTiming,
    "ivt_application_department": enums.IvtApplicationDepartment,
    "ivt_drug": enums.IvtDrug,
    "mtici_score": enums.MTiciScore,
    "no_anticoagulant_reversal_reason": enums.NoAnticoagulantReversalReason,
    "no_anticoagulants_reason": enums.NoAnticoagulantReason,
    "no_ich_treatment_reason": enums.NoIchTreatmentReason,
    "no_thrombectomy_reason": enums.NoThrombectomyReason,
    "no_thrombolysis_reason": enums.NoThrombolysisReason,
    "paracetamol_on_fever": enums.ParacetamolOnFever,
    "paracetamol_on_fever_timing": enums.ParacetamolOnFeverTiming,
    "post_neurosurgery_imaging": enums.PostNeurosurgeryImaging,
    "post_recanalization_imaging": enums.PostRecanalizationImaging,
    "stroke_management_appointment": enums.ManagementAppointment,
    "stroke_mimics_diagnosis": enums.MimicsDiagnosis,
    "stroke_type": enums.StrokeType,
    "swallowing_screening_done": enums.SwallowingScreeningDone,
    "swallowing_screening_performer": enums.ScreeningPerformer,
    "swallowing_screening_timing": enums.SwallowingScreeningTiming,
    "swallowing_screening_type": enums.SwallowingScreeningType,
    "three_m_mode_contact": enums.ThreeMonthContactMode,
    "tia_clinical_symptoms": enums.TiaClinicalSymptoms,
    "tia_symptoms_duration": enums.TiaSymptomDuration,
}


EXPLICIT_VALUE_ALIASES = {
    "sex": {"male": "1", "female": "2", "other": "3"},
    "admission_department": {
        "neurology": "1",
        "neurosurgery": "2",
        "critical care icu": "3",
        "critical care/icu": "3",
        "icu": "3",
        "internal medicine": "4",
        "other": "5",
    },
    "arrival_mode_id": {
        "ems from home scene": "1",
        "ems from home/scene": "1",
        "private transportation from home scene": "2",
        "private transportation from home/scene": "2",
        "stroke center": "3",
        "another hospital": "4",
        "ems from gp": "5",
        "private transportation from gp": "6",
        "inhospital stroke": "7",
    },
    "atrial_fibrillation_or_flutter": {
        "known af": "1",
        "detected": "2",
        "no af": "3",
        "not screened": "4",
    },
    "first_contact_place": {
        "radiology": "1",
        "emergency": "2",
        "outpatient clinic": "3",
        "outpatient": "3",
        "other": "4",
    },
    "hospitalized_in": {
        "icu stroke unit": "1",
        "icu/stroke unit": "1",
        "monitored bed": "2",
        "standard bed": "3",
    },
    "imaging_done": {"yes": "1", "no": "2", "elsewhere": "3"},
    "imaging_type": {
        "ct": "1",
        "ct cta": "2",
        "ct cta perfusion": "3",
        "mr": "4",
        "mr dwi flair": "4",
        "mr dwi/flair": "4",
        "mr mra": "5",
        "mr dwi flair mra": "5",
        "mr dwi/flair mra": "5",
        "mr dwi flair mra perfusion": "6",
        "mr dwi/flair mra perfusion": "6",
    },
    "inr_mode": {
        "lab": "1",
        "laboratory": "1",
        "point of care": "2",
        "point of care device": "2",
        "not done": "3",
    },
    "ivt_application_department": {
        "radiology": "1",
        "icu": "2",
        "stroke unit or icu": "2",
        "emergency": "3",
        "other": "4",
    },
    "stroke_type": {
        "ischemic": "1",
        "intracerebral hemorrhage": "2",
        "transient ischemic": "3",
        "subarachnoid hemorrhage": "4",
        "cerebral venous thrombosis": "5",
        "stroke mimics": "6",
        "undetermined": "7",
    },
    "discharge_destination": {
        "home": "1",
        "same hospital": "2",
        "another hospital": "3",
        "other hospital": "3",
        "social care": "4",
        "dead": "5",
        "against medical advice": "6",
    },
    "discharge_facility_department": {
        "acute rehabilitation": "1",
        "post care bed": "2",
        "post-care bed": "2",
        "neurology": "3",
        "another department": "4",
    },
    "discharge_facility_type": {
        "same hospital": "1",
        "primary center": "2",
        "comprehensive center": "3",
        "other hospital": "4",
        "another hospital": "4",
    },
    "gcs_level": {
        "severe injury": "1",
        "moderate injury": "2",
        "mild injury": "3",
    },
    "three_m_mode_contact": {
        "telemedicine": "1",
        "visiting the clinic": "2",
        "clinic": "2",
        "mobile app": "3",
        "web app": "4",
        "no response": "5",
        "not contacted": "6",
    },
    "carotid_stenosis_level": {
        "50 to 70": "1",
        "over 70": "2",
        "below 50": "3",
        "under 50": "3",
        "occlusion": "4",
    },
    "no_thrombectomy_reason": {
        "done elsewhere": "1",
        "time window": "2",
        "mild deficit": "3",
        "no large vessel occlusion": "4",
        "disability": "5",
        "consent": "6",
        "cost of treatment": "7",
        "transferred elsewhere": "8",
        "not available": "9",
        "technically not possible": "10",
        "no angiography": "11",
        "other": "13",
        "low aspect score": "14",
    },
    "no_thrombolysis_reason": {
        "done elsewhere": "1",
        "time window": "2",
        "mild deficit": "3",
        "consent": "4",
        "only mt": "5",
        "cost of treatment": "6",
        "transferred elsewhere": "7",
        "not available": "8",
        "other": "9",
        "lesion developed": "10",
        "disability": "11",
        "previous bleeding": "12",
        "anticoagulant use": "13",
    },
    "swallowing_screening_done": {
        "yes": "1",
        "no": "2",
        "not applicable": "3",
    },
    "swallowing_screening_performer": {
        "nurse": "1",
        "doctor": "2",
        "speech therapist": "3",
        "other": "4",
    },
    "swallowing_screening_timing": {
        "within 4 hour": "1",
        "within 24 hour": "2",
        "after 24 hour": "3",
    },
    "swallowing_screening_type": {
        "guss": "1",
        "assist": "2",
        "water test": "3",
        "other": "4",
    },
    "stroke_management_appointment": {
        "scheduled": "1",
        "not scheduled": "2",
        "not recommended": "3",
    },
    "tia_clinical_symptoms": {
        "motor": "1",
        "speech disturbance": "2",
        "visual": "3",
        "other": "4",
    },
    "tia_symptoms_duration": {"< 10 minutes": "1", "10 to 59 minutes": "2", ">= 60 minutes": "3"},
}


TRUE_VALUES = {"true", "t", "1", "yes", "y", "si", "sí", "verdadero", "pravda", "ano", "áno"}
FALSE_VALUES = {"false", "f", "0", "no", "n", "falso", "nepravda", "nie"}


def _key(value: Any) -> str:
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9<>=%]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value.strip() == ""


def normalize_scalar(value: Any) -> Any:
    if _is_missing(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        normalized = _key(stripped)
        if normalized in TRUE_VALUES:
            return True
        if normalized in FALSE_VALUES:
            return False
        return stripped
    return value


def normalize_temporal_value(value: Any) -> Any:
    if _is_missing(value):
        return None
    if isinstance(value, str) and re.fullmatch(r"\d{4}\s+q[1-4]", value.strip(), flags=re.IGNORECASE):
        return None
    return value


def _enum_lookup(enum_cls: type[enums.ConceptEnum]) -> dict[str, str]:
    lookup = {}
    for member in enum_cls:
        for candidate in (member.id, member.code, member.display, member.name):
            lookup[_key(candidate)] = member.id
    return lookup


def normalize_enum_value(field: str, value: Any) -> Any:
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        return value

    normalized = _key(value)
    if field in EXPLICIT_VALUE_ALIASES and normalized in EXPLICIT_VALUE_ALIASES[field]:
        return EXPLICIT_VALUE_ALIASES[field][normalized]

    enum_cls = FIELD_ENUMS.get(field)
    if enum_cls is None:
        return value

    lookup = _enum_lookup(enum_cls)
    return lookup.get(normalized, value)


def normalize_slovak_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    normalized = df.rename(columns=COLUMN_ALIASES).copy()
    duplicate_columns = normalized.columns[normalized.columns.duplicated()].tolist()
    if duplicate_columns:
        normalized = normalized.loc[:, ~normalized.columns.duplicated()]

    for column in normalized.columns:
        normalized[column] = normalized[column].map(normalize_scalar)
        if column.endswith("_date") or column.endswith("_timestamp") or column in {"discharge_date"}:
            normalized[column] = normalized[column].map(normalize_temporal_value)
        if column in FIELD_ENUMS:
            normalized[column] = normalized[column].map(lambda value, field=column: normalize_enum_value(field, value))

    report = {
        "rows": len(normalized),
        "columns": len(normalized.columns),
        "renamedColumns": {src: dst for src, dst in COLUMN_ALIASES.items() if src in df.columns},
        "droppedDuplicateColumns": duplicate_columns,
    }
    return normalized, report


def normalize_slovak_csv(input_path: Path, output_path: Path) -> dict[str, Any]:
    input_path = Path(input_path)
    output_path = Path(output_path)
    try:
        df = pd.read_csv(input_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(input_path, encoding="utf-8-sig")

    normalized, report = normalize_slovak_dataframe(df)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output_path, index=False, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Slovak/RES-Q CSV to the internal registry contract")
    parser.add_argument("--input", "-i", required=True, help="Path to source CSV")
    parser.add_argument("--output", "-o", required=True, help="Path to normalized CSV")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    report = normalize_slovak_csv(Path(args.input), Path(args.output))
    logger.info("Normalized %s rows into %s", report["rows"], args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
