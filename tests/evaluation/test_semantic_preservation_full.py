import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.enum_models import (
    ImagingType,
    NoThrombectomyReason,
    NoThrombolysisReason,
    PerforationProcedures,
    ThrombectomyComplications,
)
from scripts.normalization.sk_registry import OUTPUT_COLUMNS
from scripts.evaluation.semantic_preservation_full import (
    _check,
    _is_applicable,
    evaluate_semantic_preservation,
)


def coding_dict(member):
    coding = member.to_coding()
    if hasattr(coding, "model_dump"):
        return coding.model_dump(by_alias=True, exclude_none=True)
    if hasattr(coding, "dict"):
        return coding.dict(by_alias=True, exclude_none=True)
    return {
        "system": coding.system,
        "code": coding.code,
        "display": coding.display,
    }


def concept(member):
    return {"coding": [coding_dict(member)]}


class FullSemanticPreservationTests(unittest.TestCase):
    def _bundle_with_reversible_extra_representations(self):
        imaging_member = ImagingType.by_id("1")
        self.assertIsNotNone(imaging_member)

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Organization",
                        "name": "Example-Hospital",
                        "identifier": [{
                            "system": "https://stroke.qualityregistry.org",
                            "value": "12345",
                        }],
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "meta": {"profile": [
                            "http://qualityregistry.org/StructureDefinition/stroke-diagnosis-condition-profile"
                        ]},
                        "onsetDateTime": "2026-01-15T10:30:00+01:00",
                    }
                },
                {
                    "resource": {
                        "resourceType": "Procedure",
                        "meta": {"profile": [
                            "http://qualityregistry.org/StructureDefinition/stroke-carotid-imaging-procedure-profile"
                        ]},
                        "code": concept(ImagingType.CAROTID),
                        "status": "completed",
                    }
                },
                {
                    "resource": {
                        "resourceType": "Procedure",
                        "code": concept(imaging_member),
                        "status": "completed",
                    }
                },
                {
                    "resource": {
                        "resourceType": "Procedure",
                        "code": concept(PerforationProcedures.THROMBOLYSIS),
                        "status": "not-done",
                        "statusReason": concept(NoThrombolysisReason.by_id("1")),
                    }
                },
                {
                    "resource": {
                        "resourceType": "Procedure",
                        "code": concept(PerforationProcedures.THROMBECTOMY),
                        "status": "completed",
                        "statusReason": concept(NoThrombectomyReason.by_id("1")),
                        "complication": [{
                            "concept": concept(ThrombectomyComplications.PERFORATION)
                        }],
                    }
                },
            ],
        }

    @staticmethod
    def _bundle_with_encounter_start(start=None):
        encounter = {
            "resourceType": "Encounter",
            "meta": {"profile": [
                "http://qualityregistry.org/StructureDefinition/stroke-encounter-profile"
            ]},
        }
        if start is not None:
            encounter["actualPeriod"] = {"start": start}
        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [{"resource": encounter}],
        }

    def test_eight_serialized_extra_fields_have_readback_comparators(self):
        bundle = self._bundle_with_reversible_extra_representations()
        checks = {
            "provider": "Example Hospital",
            "provider_id": "12345",
            "carotid_arteries_imaging": True,
            "imaging_done": "1",
            "mt_complications_perforation": True,
            "no_thrombolysis_reason": "1",
            "no_thrombectomy_reason": "1",
            "onset_timestamp": "2026-01-15T10:30:00+01:00",
        }

        for field, value in checks.items():
            with self.subTest(field=field):
                self.assertIs(_check(field, value, bundle), True)

    def test_inhospital_stroke_is_checked_through_encounter_start(self):
        hospital_timestamp = "2026-01-15T10:30:00+01:00"
        matching_bundle = self._bundle_with_encounter_start(hospital_timestamp)
        wrong_bundle = self._bundle_with_encounter_start("2026-01-15T11:00:00+01:00")
        no_start_bundle = self._bundle_with_encounter_start()
        row = {"hospital_timestamp": hospital_timestamp}

        self.assertIs(
            _check("inhospital_stroke", True, matching_bundle, row=row),
            True,
        )
        self.assertIs(
            _check("inhospital_stroke", True, wrong_bundle, row=row),
            False,
        )
        self.assertIs(
            _check("inhospital_stroke", False, matching_bundle, row=row),
            False,
        )
        self.assertIs(
            _check("inhospital_stroke", False, no_start_bundle, row=row),
            True,
        )

    def test_hospital_timestamp_is_only_applicable_to_inhospital_stroke(self):
        self.assertTrue(_is_applicable(
            "hospital_timestamp",
            pd.Series({"inhospital_stroke": True}),
        ))
        self.assertFalse(_is_applicable(
            "hospital_timestamp",
            pd.Series({"inhospital_stroke": False}),
        ))
        self.assertFalse(_is_applicable(
            "hospital_timestamp",
            pd.Series({"inhospital_stroke": None}),
        ))

    def test_only_smoking_field_remains_non_reversible(self):
        bundle = self._bundle_with_reversible_extra_representations()
        self.assertIs(_check("risk_smoker_last_10_years", True, bundle), False)

    def test_complete_normalized_contract_is_classified_as_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = {column: None for column in OUTPUT_COLUMNS}
            row["case"] = "case-1"
            csv_path = root / "normalized.csv"
            pd.DataFrame([row], columns=OUTPUT_COLUMNS).to_csv(csv_path, index=False)

            bundle_dir = root / "bundles"
            bundle_dir.mkdir()
            bundle = {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [{
                    "resource": {
                        "resourceType": "Patient",
                        "identifier": [{"value": "case-1"}],
                    }
                }],
            }
            (bundle_dir / "case-1.json").write_text(
                json.dumps(bundle), encoding="utf-8"
            )

            report = evaluate_semantic_preservation(csv_path, bundle_dir)

            self.assertEqual(report["normalizedFieldCount"], len(OUTPUT_COLUMNS))
            self.assertEqual(report["supportedFieldCount"], len(OUTPUT_COLUMNS))
            self.assertEqual(report["unsupportedFieldCount"], 0)
            self.assertEqual(report["unsupportedFields"], [])
            self.assertEqual(report["fieldCoverageRate"], 1.0)
            self.assertEqual(
                report["nonReversibleFields"],
                ["risk_smoker_last_10_years"],
            )

    def test_inhospital_rule_and_smoking_failure_are_counted_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "normalized.csv"
            pd.DataFrame([{
                "case": "case-1",
                "inhospital_stroke": True,
                "hospital_timestamp": "2026-01-15T10:30:00+01:00",
                "risk_smoker_last_10_years": True,
            }]).to_csv(csv_path, index=False)

            bundle_dir = root / "bundles"
            bundle_dir.mkdir()
            bundle = {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Patient",
                            "identifier": [{"value": "case-1"}],
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "Encounter",
                            "meta": {"profile": [
                                "http://qualityregistry.org/StructureDefinition/stroke-encounter-profile"
                            ]},
                            "actualPeriod": {
                                "start": "2026-01-15T10:30:00+01:00"
                            },
                        }
                    },
                ],
            }
            (bundle_dir / "case-1.json").write_text(
                json.dumps(bundle), encoding="utf-8"
            )

            report = evaluate_semantic_preservation(csv_path, bundle_dir)

            self.assertEqual(report["unsupportedFields"], [])
            self.assertEqual(report["comparableSourceValues"], 4)
            self.assertEqual(report["matchedValues"], 3)
            self.assertEqual(report["mismatchedValues"], 1)
            self.assertEqual(
                report["byField"]["inhospital_stroke"]["matched"], 1
            )
            self.assertEqual(
                report["byField"]["hospital_timestamp"]["matched"], 1
            )
            self.assertEqual(
                report["byField"]["risk_smoker_last_10_years"]["mismatched"], 1
            )


if __name__ == "__main__":
    unittest.main()
