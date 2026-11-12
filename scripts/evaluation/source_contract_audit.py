"""Aggregate checks for selected Slovak source -> normalized RES-Q mappings.

This module intentionally does NOT certify source clinical semantics or the
normalized -> FHIR transformation. It must be combined with the existing FHIR
semantic-preservation evaluator and independent clinical adjudication.
No row-level identifiers, source values or clinical values are serialized.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


TICI_TO_RESQ = {"000": "1", "010": "2", "02a": "3", "02b": "4", "030": "6"}
THROMBOLYSIS_TO_BOOL = {"1": True, "2": False, "3": False}
THROMBECTOMY_TO_BOOL = {"1": True, "2": False, "3": False, "9": False}


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    return "" if value.lower() in {"nan", "none", "<na>"} else value


def _datetime_equal(source_value: object, normalized_value: object) -> bool:
    source = pd.to_datetime(_text(source_value), errors="coerce")
    normalized = pd.to_datetime(_text(normalized_value), errors="coerce")
    return not pd.isna(source) and not pd.isna(normalized) and source == normalized


def _same_numeric(source_value: object, normalized_value: object) -> bool:
    source = pd.to_numeric(_text(source_value), errors="coerce")
    normalized = pd.to_numeric(_text(normalized_value), errors="coerce")
    return not pd.isna(source) and not pd.isna(normalized) and source == normalized


def audit_source_to_contract(
    source_csv: Path,
    normalized_csv: Path,
) -> dict:
    """Run independent source-to-contract assertions on the row-aligned CSVs.

    Correctness of the clinical *interpretation* of mRS timing, puncture
    timing or TICI/mTICI scale equivalence requires external confirmation.
    """
    source = pd.read_csv(source_csv, sep=";", dtype=str, keep_default_na=False)
    normalized = pd.read_csv(normalized_csv, dtype=str, keep_default_na=False)
    if len(source) != len(normalized):
        raise ValueError("Source and normalized CSV must contain the same rows")
    if len(source) and not len(normalized):
        raise ValueError("Normalized CSV is empty")

    per_rule = defaultdict(Counter)
    flags = Counter()

    def record(rule: str, correct: bool) -> None:
        per_rule[rule]["checked"] += 1
        per_rule[rule]["matched" if correct else "mismatched"] += 1

    for i in range(len(source)):
        s = source.iloc[i]
        n = normalized.iloc[i]

        if {"OA_TIA", "OA_ISCHEMICKA_CMP"} <= set(source.columns):
            # Registry-level intentionally combined event history. Only
            # unambiguous 1=yes, 2=no and blank cases are compared; NCZI
            # code 3 meanings need independent source-codebook review.
            codes = [_text(s[field]) for field in ("OA_TIA", "OA_ISCHEMICKA_CMP")]
            if all(code in {"", "1", "2"} for code in codes):
                if "1" in codes:
                    expected = "true"
                elif all(code == "2" for code in codes):
                    expected = "false"
                else:
                    expected = ""
                record(
                    "tia_or_ischemic_stroke_combined_resq_indicator",
                    _text(n.get("risk_previous_ischemic_stroke")).lower() == expected,
                )
            else:
                flags["tia_stroke_source_codes_require_review"] += 1

        if "STAV_M_RANKIN_2" in source.columns:
            raw = _text(s["STAV_M_RANKIN_2"])
            if raw:
                record(
                    "mrs_numeric_copy_not_timing_adjudication",
                    _same_numeric(raw, n.get("prestroke_mrs")),
                )
                flags["mrs_timepoint_requires_source_confirmation"] += 1

        if "DATUM_ENDO_V" in source.columns:
            raw = _text(s["DATUM_ENDO_V"])
            if raw:
                record(
                    "endovascular_timestamp_copy_not_puncture_adjudication",
                    _datetime_equal(raw, n.get("puncture_timestamp")),
                )
                flags["endo_event_definition_requires_confirmation"] += 1

        if "TICI" in source.columns:
            raw = _text(s["TICI"])
            if raw:
                if raw in TICI_TO_RESQ:
                    record("tici_grade_recode_not_scale_equivalence",
                           _text(n.get("mtici_score")) == TICI_TO_RESQ[raw])
                    flags["tici_to_mtici_grade_definition_requires_review"] += 1
                elif raw == "090":
                    # A source unknown code is not an mTICI grade.
                    record("tici_unknown_is_not_assigned_a_grade",
                           not _text(n.get("mtici_score")))
                else:
                    flags["tici_unmapped_source_code"] += 1

        if "CT_MR_VYSETRENIE" in source.columns:
            imaging_source = _text(s["CT_MR_VYSETRENIE"])
            # The 2024 source explicitly distinguishes local / elsewhere /
            # no study. Audit status independently of selected modality.
            done_map = {"1": "1", "2": "3", "3": "1",
                        "4": "3", "5": "2"}
            type_map = {"1": "1", "2": "1", "3": "4", "4": "4"}
            if imaging_source in done_map:
                record("brain_imaging_location_or_absence_status",
                       _text(n.get("imaging_done")) == done_map[imaging_source])
                if imaging_source in {"2", "4"}:
                    record("external_imaging_modality",
                           _text(n.get("imaging_type")) == type_map[imaging_source])
                if imaging_source == "5":
                    record("no_imaging_does_not_invent_modality",
                           not _text(n.get("imaging_type")))
            elif imaging_source:
                flags["imaging_unmapped_source_code"] += 1

        if "ENDO_VYKON" in source.columns:
            mt_source = _text(s["ENDO_VYKON"])
            if mt_source in THROMBECTOMY_TO_BOOL:
                actual = _text(n.get("thrombectomy")).lower()
                expected = str(THROMBECTOMY_TO_BOOL[mt_source]).lower()
                record("mt_reporting_hospital_boolean", actual == expected)
                if mt_source in {"2", "3"}:
                    expected_reason = "1" if mt_source == "2" else "8"
                    record(
                        "mt_external_or_planned_reason",
                        _text(n.get("no_thrombectomy_reason")) == expected_reason,
                    )
                if mt_source == "2":
                    flags["mt_external_procedure_and_time_not_checked_in_fhir"] += 1
                if mt_source == "3":
                    flags["mt_transfer_planned_not_equivalent_to_completed"] += 1
            elif mt_source:
                flags["mt_unmapped_source_code"] += 1

        if "NL_TROMBOLYZA" in source.columns:
            raw = _text(s["NL_TROMBOLYZA"])
            if raw in THROMBOLYSIS_TO_BOOL:
                boolean_value = _text(n.get("thrombolysis")).lower()
                expected = str(THROMBOLYSIS_TO_BOOL[raw]).lower()
                record("ivt_reporting_hospital_boolean", boolean_value == expected)
                if raw == "2":
                    record("ivt_elsewhere_reason",
                           _text(n.get("no_thrombolysis_reason")) == "1")
                    record("ivt_elsewhere_no_local_door_to_needle",
                           not _text(n.get("door_to_needle")))
                    if ("NL_DATUM_TROMBOLYZA" in source.columns
                            and _text(s["NL_DATUM_TROMBOLYZA"])):
                        record(
                            "ivt_elsewhere_timestamp_source_to_contract",
                            _datetime_equal(
                                s["NL_DATUM_TROMBOLYZA"],
                                n.get("bolus_timestamp"),
                            ),
                        )
                        flags["ivt_elsewhere_bolus_time_not_checked_in_fhir"] += 1
                if raw == "3":
                    record("ivt_not_administered_has_no_local_door_to_needle",
                           not _text(n.get("door_to_needle")))
                if raw != "3" and any(
                    _text(s.get(code)) == "1"
                    for code in ("DNTL_MIMO_CAS", "DNTL_DEFICIT")
                ):
                    flags["ivt_conflicting_source_flags"] += 1
            elif raw:
                flags["ivt_unmapped_source_code"] += 1

    checked = sum(counter["checked"] for counter in per_rule.values())
    mismatched = sum(counter["mismatched"] for counter in per_rule.values())
    return {
        "scope": "Selected original Slovak source to normalized RES-Q contract checks only",
        "patientLevelValuesIncluded": False,
        "sourceRows": len(source),
        "checkedAssertions": checked,
        "matchedAssertions": checked - mismatched,
        "mismatchedAssertions": mismatched,
        "byRule": {name: {
            "checked": counts["checked"],
            "matched": counts["matched"],
            "mismatched": counts["mismatched"],
        } for name, counts in sorted(per_rule.items())},
        "reviewFlags": dict(sorted(flags.items())),
        "notYetClinicallyAdjudicated": [
            "STAV_M_RANKIN_2: prestroke vs admission mRS timepoint",
            "DATUM_ENDO_V: arterial puncture vs procedure start",
            "2024 TICI 02a (<2/3) and 02b (slow distal filling) differ "
            "from target mTICI 2a (<1/2) and 2b (>1/2) definitions",
            "CT/MR at another institution is represented by a reporting-hospital not-done Procedure, not the historical completed remote event",
            "ENDO_VYKON=2 external MT time/grade are not checked downstream",
            "NL_TROMBOLYZA=2: source external treatment time is not checked "
            "by the normalized-contract-to-FHIR semantic evaluator",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate audit of selected Slovak source-to-contract rules"
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--normalized", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit_source_to_contract(args.source, args.normalized)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"Source-to-contract audit: {result['matchedAssertions']}/"
        f"{result['checkedAssertions']} assertions matched "
        f"({result['mismatchedAssertions']} mismatches)."
    )
    return 1 if result["mismatchedAssertions"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
