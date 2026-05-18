"""Normalize original Slovak registry CSV exports to the internal FHIR input contract."""

from __future__ import annotations

import argparse
import logging
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


COLUMN_MAPPING = {
    "ICO": "provider_id",
    "NAZOV": "provider",
    "NÁZOV NEMOCNICE SKRÁTENÝ": "hospital_name",
    "PACVEK": "age",
    "PACPOHLAVIE": "sex",
    "PACDATVYK": "onset_date",
    "PACCASVYK": "onset_time",
    "WAKE_UP_STROKE_1": "wakeup_stroke",
    "TRANSPORT_TYP": "inhospital_stroke",
    "TRANSPORT_SPE": "arrival_mode_id",
    "DATUM_LEKAR": "hospital_timestamp",
    "JIS_ARO": "hospitalized_in",
    "STAV_NHISS_2": "nihss_score",
    "STAV_M_RANKIN_2": "prestroke_mrs",
    "STAV_TK_SYSTOLICKY": "systolic_pressure",
    "STAV_TK_DIASTOLICKY": "diastolic_pressure",
    "OA_TIA": "risk_tia",
    "OA_ISCHEMICKA_CMP": "risk_previous_ischemic_stroke",
    "OA_HEMORAGICKA_CMP": "risk_previous_hemorrhagic_stroke",
    "OA_HYPERTENZIA": "risk_hypertension",
    "OA_HYPERLIPIDEMIA": "risk_hyperlipidemia",
    "OA_D_PAD": "risk_diabetes",
    "OA_D_INZULIN": "before_onset_antidiabetics",
    "OA_FAJCENIE": "risk_smoker_last_10_years",
    "OA_FIBRILACIA_PRED": "risk_atrial_fibrillation",
    "OA_IM": "risk_coronary_artery_disease_or_myocardial_infarction",
    "RA_CMP": "risk_previous_stroke",
    "OA_HYPERTENZIA_LIEC": "before_onset_antihypertensives",
    "OA_ANTIKOAGULANCIA": "before_onset_anticoagulants",
    "OA_ASPIRIN": "before_onset_asa",
    "OA_CLOPIDOGREL": "before_onset_clopidogrel",
    "OA_KONTRACEPTIVA": "before_onset_contraception",
    "OA_STATINY": "before_onset_statin",
    "CT_MR_VYSETRENIE": "imaging_type",
    "CT_ANGIO": "ct_angio",
    "CT_PERFUZNE": "ct_perfusion",
    "DATUM_CT": "imaging_timestamp",
    "KKD_TYP_SPEC": "stroke_type",
    "NL_TROMBOLYZA": "thrombolysis",
    "NL_DATUM_TROMBOLYZA": "bolus_timestamp",
    "DNTL_MIMO_CAS": "no_ivt_reason_time_window",
    "DNTL_DEFICIT": "no_ivt_reason_mild_deficit",
    "ENDO_VYKON": "thrombectomy",
    "DATUM_ENDO_V": "puncture_timestamp",
    "DATUM_REKANALIZACIE": "reperfusion_timestamp",
    "TICI": "mtici_score",
    "NMT_MIMO_CAS": "no_mt_reason_time_window",
    "DMT_DEFICIT": "no_mt_reason_mild_deficit",
    "DMT_PREMORBIDITA": "no_mt_reason_premorbidity",
    "REKANAL_KRVACANIE": "mt_complications_perforation",
    "ETIO_HEM_CMP": "bleeding_reasons",
    "UKON_FIB_PREDSIEN": "atrial_fibrillation_or_flutter",
    "KAROTIDA": "carotid_arteries_imaging",
    "ETIO_ISCH_CMP": "etiology",
    "DYSFAGIA_VYS": "swallowing_screening_done",
    "DYSFAGIA": "swallowing_screening_timing",
    "DYSFAGIA_SPEC": "swallowing_screening_type",
    "UKON_SPOSOB": "discharge_destination",
    "UKON_PREKLAD_VYBER": "discharge_facility_department",
    "UKON_DATUM": "discharge_date",
    "UKON_MRANKIN_2": "discharge_mrs",
    "UKON_MRANKIN_po 3 mesiacoch": "three_m_mrs",
    "UKON_NIHSS_2": "discharge_nihss_score",
    "UKON_ASA": "discharge_asa",
    "UKON_CLOPIDOGREL": "discharge_clopidogrel",
    "UKON_WARFARIN": "discharge_warfarin",
    "UKON_HEPARIN": "discharge_heparin",
    "UKON_DOAK": "discharge_doak",
    "UKON_STATIN": "discharge_statin",
    "UKON_NOOTROPIKA": "discharge_other",
    "UKON_ANTIDEPRESIVA": "discharge_other2",
}

SEX_MAP = {"1": "1", "2": "2", "9": "3"}
ARRIVAL_MODE_MAP = {"1": "1", "2": "2", "3": None}
HOSPITALIZED_IN_MAP = {"1": "1"}
INHOSPITAL_MAP = {"1": False, "2": False, "3": False, "4": True, "5": None}
BOOL_MAP = {"1": True, "2": False, "3": False}
SMOKER_MAP = {"3": True, "6": False, "8": True, "9": True}
STROKE_TYPE_MAP = {"5": "1", "4": "3", "2": "2", "3": "2", "1": "4", "6": "7"}
DISCHARGE_DESTINATION_MAP = {"1": "1", "3": "3", "2": "4", "4": "5"}
DISCHARGE_FACILITY_DEPARTMENT_MAP = {"1": "1", "2": "2", "4": "3", "9": "4"}
ATRIAL_FIBRILLATION_MAP = {"1": "1", "2": "3"}
SWALLOWING_DONE_MAP = {"1": "1", "2": "1", "3": "2"}
SWALLOWING_TIMING_MAP = {"1": "2", "2": "3"}
SWALLOWING_TYPE_MAP = {"1": "1", "2": "3", "3": "4", "4": "4", "5": "4", "6": "4"}
MTICI_MAP = {"000": "1", "010": "2", "02a": "3", "02b": "4", "030": "6"}
NO_THROMBOLYSIS_REASON_MAP = {"2": "1", "3": "7"}
NO_THROMBECTOMY_REASON_MAP = {"2": "1", "3": "8"}

BOOLEAN_COLUMNS = [
    "risk_tia", "wakeup_stroke", "risk_hyperlipidemia",
    "risk_previous_ischemic_stroke", "risk_previous_stroke",
    "risk_previous_hemorrhagic_stroke",
    "risk_coronary_artery_disease_or_myocardial_infarction",
    "risk_diabetes", "before_onset_antidiabetics", "risk_atrial_fibrillation",
    "risk_hypertension", "before_onset_antihypertensives",
    "before_onset_asa", "before_onset_clopidogrel", "before_onset_statin",
    "before_onset_contraception", "thrombolysis", "thrombectomy",
    "carotid_arteries_imaging", "discharge_asa", "discharge_clopidogrel",
    "discharge_warfarin", "discharge_doak", "discharge_heparin",
    "discharge_statin", "discharge_other", "discharge_other2",
    "mt_complications_perforation",
]

INTEGER_COLUMNS = [
    "age", "systolic_pressure", "diastolic_pressure", "nihss_score",
    "prestroke_mrs", "door_to_needle", "door_to_groin", "discharge_nihss_score",
]

OUTPUT_COLUMNS = [
    "case", "provider", "provider_id", "age", "sex", "wakeup_stroke",
    "inhospital_stroke", "onset_timestamp", "hospital_timestamp",
    "arrival_mode_id", "hospitalized_in", "nihss_score", "prestroke_mrs",
    "systolic_pressure", "diastolic_pressure", "risk_hyperlipidemia",
    "risk_previous_ischemic_stroke", "risk_previous_stroke",
    "risk_previous_hemorrhagic_stroke",
    "risk_coronary_artery_disease_or_myocardial_infarction", "risk_diabetes",
    "risk_atrial_fibrillation", "risk_hypertension", "risk_smoker_last_10_years",
    "before_onset_antidiabetics", "before_onset_antihypertensives",
    "before_onset_asa", "before_onset_clopidogrel", "before_onset_statin",
    "before_onset_contraception", "before_onset_warfarin",
    "before_onset_other_anticoagulant", "before_onset_any_antiplatelet",
    "before_onset_any_anticoagulant", "imaging_done", "imaging_type",
    "imaging_timestamp", "stroke_type", "thrombolysis", "bolus_timestamp",
    "door_to_needle", "no_thrombolysis_reason", "thrombectomy",
    "puncture_timestamp", "door_to_groin", "reperfusion_timestamp", "mtici_score",
    "no_thrombectomy_reason", "mt_complications_perforation",
    "bleeding_reason_aneurysm", "bleeding_reason_malformation",
    "bleeding_reason_other", "stroke_etiology_cardioembolism",
    "stroke_etiology_la_atherosclerosis", "stroke_etiology_lacunar",
    "stroke_etiology_cryptogenic_stroke", "stroke_etiology_other",
    "atrial_fibrillation_or_flutter", "carotid_arteries_imaging",
    "swallowing_screening_done", "swallowing_screening_timing",
    "swallowing_screening_type", "discharge_destination",
    "discharge_facility_department", "discharge_date", "discharge_mrs",
    "three_m_mrs", "discharge_nihss_score", "discharge_asa",
    "discharge_clopidogrel", "discharge_warfarin", "discharge_heparin",
    "discharge_statin", "discharge_other", "discharge_any_antiplatelet",
    "discharge_any_anticoagulant", "post_acute_care",
]


def _norm_header(value: str) -> str:
    return unicodedata.normalize("NFC", value).replace("\ufeff", "").replace("\xa0", " ").strip()


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value.strip() == ""


def _key(value: Any) -> str | None:
    if _is_missing(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def _map_value(value: Any, mapping: dict[str, Any]) -> Any:
    key = _key(value)
    return None if key is None else mapping.get(key)


def _to_bool(value: Any) -> bool | None:
    return _map_value(value, BOOL_MAP)


def _parse_datetime(value: Any) -> pd.Timestamp | None:
    if _is_missing(value):
        return None
    parsed = pd.to_datetime(value, format="%m/%d/%Y %H:%M", errors="coerce")
    if pd.isna(parsed):
        parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed


def _format_datetime(value: Any) -> str | None:
    parsed = _parse_datetime(value)
    return None if parsed is None else parsed.strftime("%Y-%m-%d %H:%M:%S")


def _combine_date_time(date_value: Any, time_value: Any) -> str | None:
    if _is_missing(date_value):
        return None
    date_text = str(date_value).split()[0]
    time_text = "00:00" if _is_missing(time_value) else str(time_value).strip()
    return _format_datetime(f"{date_text} {time_text}")


def _minute_difference(end_value: Any, start_value: Any) -> int | None:
    end = _parse_datetime(end_value)
    start = _parse_datetime(start_value)
    if end is None or start is None:
        return None
    return int((end - start).total_seconds() / 60)


def _last_mrs_digit(value: Any) -> int | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    if text.lower() == "exitus":
        return 6
    match = re.search(r"([0-6])\D*$", text)
    return int(match.group(1)) if match else None


def _disjunction(row: pd.Series, columns: list[str]) -> bool:
    return any(row.get(column) is True for column in columns)


def _rename_source_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    normalized_columns = {_norm_header(column): column for column in df.columns}
    out = df.copy()
    renamed = {}
    for source, target in COLUMN_MAPPING.items():
        source_norm = _norm_header(source)
        if source_norm in normalized_columns:
            real_column = normalized_columns[source_norm]
            out = out.rename(columns={real_column: target})
            renamed[real_column] = target
    return out, renamed


def normalize_sk_registry_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    df, renamed = _rename_source_columns(df)
    out = pd.DataFrame(index=df.index)
    empty = pd.Series(index=df.index, dtype=object)

    out["case"] = [f"sk-{idx + 1}" for idx in range(len(df))]
    out["provider_id"] = df.get("provider_id", empty)
    out["provider"] = df.get("provider", empty)
    if "hospital_name" in df:
        out["provider"] = out["provider"].fillna(df["hospital_name"])

    for column in ("age", "nihss_score", "prestroke_mrs", "systolic_pressure", "diastolic_pressure", "discharge_nihss_score"):
        if column in df:
            out[column] = pd.to_numeric(df[column], errors="coerce")

    out["sex"] = df.get("sex", empty).map(lambda value: _map_value(value, SEX_MAP))
    out["arrival_mode_id"] = df.get("arrival_mode_id", empty).map(lambda value: _map_value(value, ARRIVAL_MODE_MAP))
    out["hospitalized_in"] = df.get("hospitalized_in", empty).map(lambda value: _map_value(value, HOSPITALIZED_IN_MAP))
    out["inhospital_stroke"] = df.get("inhospital_stroke", empty).map(lambda value: _map_value(value, INHOSPITAL_MAP))
    out["risk_smoker_last_10_years"] = df.get("risk_smoker_last_10_years", empty).map(lambda value: _map_value(value, SMOKER_MAP))
    out["stroke_type"] = df.get("stroke_type", empty).map(lambda value: _map_value(value, STROKE_TYPE_MAP))
    out["discharge_destination"] = df.get("discharge_destination", empty).map(lambda value: _map_value(value, DISCHARGE_DESTINATION_MAP))
    out["discharge_facility_department"] = df.get("discharge_facility_department", empty).map(lambda value: _map_value(value, DISCHARGE_FACILITY_DEPARTMENT_MAP))
    out["atrial_fibrillation_or_flutter"] = df.get("atrial_fibrillation_or_flutter", empty).map(lambda value: _map_value(value, ATRIAL_FIBRILLATION_MAP))
    out["swallowing_screening_done"] = df.get("swallowing_screening_done", empty).map(lambda value: _map_value(value, SWALLOWING_DONE_MAP))
    out["swallowing_screening_timing"] = df.get("swallowing_screening_timing", empty).map(lambda value: _map_value(value, SWALLOWING_TIMING_MAP))
    out["swallowing_screening_type"] = df.get("swallowing_screening_type", empty).map(lambda value: _map_value(value, SWALLOWING_TYPE_MAP))
    out["mtici_score"] = df.get("mtici_score", empty).map(lambda value: _map_value(value, MTICI_MAP))

    for column in BOOLEAN_COLUMNS:
        if column in df:
            out[column] = df[column].map(_to_bool)

    out["risk_previous_ischemic_stroke"] = out.apply(lambda row: _disjunction(row, ["risk_previous_ischemic_stroke", "risk_tia"]), axis=1)
    out["risk_previous_stroke"] = out.apply(lambda row: _disjunction(row, ["risk_previous_ischemic_stroke", "risk_previous_hemorrhagic_stroke"]), axis=1)
    out["discharge_other"] = out.apply(lambda row: _disjunction(row, ["discharge_other", "discharge_other2"]), axis=1)
    out["before_onset_any_antiplatelet"] = out.apply(lambda row: _disjunction(row, ["before_onset_asa", "before_onset_clopidogrel"]), axis=1)
    out["discharge_any_antiplatelet"] = out.apply(lambda row: _disjunction(row, ["discharge_asa", "discharge_clopidogrel"]), axis=1)
    out["discharge_any_anticoagulant"] = out.apply(lambda row: _disjunction(row, ["discharge_warfarin", "discharge_heparin", "discharge_doak"]), axis=1)

    anticoagulant_source = df.get("before_onset_anticoagulants", empty)
    out["before_onset_warfarin"] = anticoagulant_source.map(lambda value: _key(value) == "01" if not _is_missing(value) else None)
    out["before_onset_other_anticoagulant"] = anticoagulant_source.map(lambda value: _key(value) == "98" if not _is_missing(value) else None)
    out["before_onset_doak"] = anticoagulant_source.map(lambda value: _key(value) == "06" if not _is_missing(value) else None)
    out["before_onset_any_anticoagulant"] = out.apply(lambda row: _disjunction(row, ["before_onset_warfarin", "before_onset_other_anticoagulant", "before_onset_doak"]), axis=1)

    out["no_thrombolysis_reason"] = df.get("no_thrombolysis_reason", empty).map(lambda value: _map_value(value, NO_THROMBOLYSIS_REASON_MAP))
    out.loc[df.get("no_ivt_reason_time_window", empty).map(_key) == "1", "no_thrombolysis_reason"] = "2"
    out.loc[df.get("no_ivt_reason_mild_deficit", empty).map(_key) == "1", "no_thrombolysis_reason"] = "3"
    out["no_thrombectomy_reason"] = df.get("no_thrombectomy_reason", empty).map(lambda value: _map_value(value, NO_THROMBECTOMY_REASON_MAP))
    out.loc[df.get("no_mt_reason_time_window", empty).map(_key) == "1", "no_thrombectomy_reason"] = "2"
    out.loc[df.get("no_mt_reason_mild_deficit", empty).map(_key) == "1", "no_thrombectomy_reason"] = "3"
    out.loc[df.get("no_mt_reason_premorbidity", empty).map(_key) == "1", "no_thrombectomy_reason"] = "5"

    imaging_type_source = df.get("imaging_type", empty).map(_key)
    ct_angio = df.get("ct_angio", empty).map(_key)
    ct_perfusion = df.get("ct_perfusion", empty).map(_key)
    out["imaging_type"] = None
    out.loc[(ct_perfusion == "1") & (imaging_type_source == "1"), "imaging_type"] = "3"
    out.loc[(ct_perfusion == "1") & (imaging_type_source == "3"), "imaging_type"] = "6"
    out.loc[(ct_angio == "1") & (imaging_type_source == "1"), "imaging_type"] = "2"
    out.loc[(ct_angio == "1") & (imaging_type_source == "3"), "imaging_type"] = "5"
    out.loc[(imaging_type_source == "1") & out["imaging_type"].isna(), "imaging_type"] = "1"
    out.loc[(imaging_type_source == "3") & out["imaging_type"].isna(), "imaging_type"] = "4"
    out["imaging_done"] = out["imaging_type"].map(lambda value: "1" if not _is_missing(value) else None)

    bleeding_source = df.get("bleeding_reasons", empty).map(_key)
    out["bleeding_reason_aneurysm"] = bleeding_source.map(lambda value: True if value == "2" else (False if value else None))
    out["bleeding_reason_malformation"] = bleeding_source.map(lambda value: True if value in {"3", "5"} else (False if value else None))
    out["bleeding_reason_other"] = bleeding_source.map(lambda value: True if value in {"1", "4", "6", "8"} else (False if value else None))

    etiology_source = df.get("etiology", empty).map(_key)
    out["stroke_etiology_cardioembolism"] = etiology_source.map(lambda value: True if value == "1" else (False if value else None))
    out["stroke_etiology_la_atherosclerosis"] = etiology_source.map(lambda value: True if value == "2" else (False if value else None))
    out["stroke_etiology_lacunar"] = etiology_source.map(lambda value: True if value == "3" else (False if value else None))
    out["stroke_etiology_cryptogenic_stroke"] = etiology_source.map(lambda value: True if value == "4" else (False if value else None))
    out["stroke_etiology_other"] = etiology_source.map(lambda value: True if value == "5" else (False if value else None))
    if "risk_atrial_fibrillation" in out:
        out.loc[out["risk_atrial_fibrillation"] == True, "atrial_fibrillation_or_flutter"] = "1"

    for column in ("hospital_timestamp", "imaging_timestamp", "bolus_timestamp", "puncture_timestamp", "reperfusion_timestamp", "discharge_date"):
        if column in df:
            out[column] = df[column].map(_format_datetime)
    out["onset_timestamp"] = [
        _combine_date_time(date_value, time_value)
        for date_value, time_value in zip(df.get("onset_date", empty), df.get("onset_time", empty))
    ]
    out["door_to_needle"] = [_minute_difference(bolus, hospital) for bolus, hospital in zip(out.get("bolus_timestamp", empty), out.get("hospital_timestamp", empty))]
    out["door_to_groin"] = [_minute_difference(puncture, hospital) for puncture, hospital in zip(out.get("puncture_timestamp", empty), out.get("hospital_timestamp", empty))]
    out.loc[df.get("mtici_score", empty).map(_key) == "000", "reperfusion_timestamp"] = None

    for column in ("discharge_mrs", "three_m_mrs"):
        if column in df:
            out[column] = df[column].map(_last_mrs_digit)
    out["post_acute_care"] = [
        None if _parse_datetime(discharge) is None or _parse_datetime(hospital) is None
        else (_parse_datetime(discharge) - _parse_datetime(hospital)).total_seconds() > 24 * 3600
        for discharge, hospital in zip(out.get("discharge_date", empty), out.get("hospital_timestamp", empty))
    ]

    for column in INTEGER_COLUMNS:
        if column in out:
            out[column] = pd.to_numeric(out[column], errors="coerce").astype("Int64")
    for column in OUTPUT_COLUMNS:
        if column not in out:
            out[column] = None

    out = out[OUTPUT_COLUMNS].where(pd.notna(out), None)
    report = {
        "rows": len(out),
        "columns": len(out.columns),
        "renamedColumns": renamed,
        "sourceFormat": "sk_registry",
    }
    return out, report


def normalize_sk_registry_csv(input_path: Path, output_path: Path) -> dict[str, Any]:
    df = pd.read_csv(Path(input_path), sep=";", encoding="utf-8")
    normalized, report = normalize_sk_registry_dataframe(df)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output_path, index=False, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize original Slovak registry CSV to the internal FHIR contract")
    parser.add_argument("--input", "-i", required=True, help="Path to source CSV")
    parser.add_argument("--output", "-o", required=True, help="Path to normalized CSV")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    report = normalize_sk_registry_csv(Path(args.input), Path(args.output))
    logger.info("Normalized %s rows from %s", report["rows"], report["sourceFormat"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
