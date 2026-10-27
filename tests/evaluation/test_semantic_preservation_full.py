import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.enum_models import (
    AdmissionPathway,
    ImagingType,
    NoThrombectomyReason,
    NoThrombolysisReason,
    PerforationProcedures,
    RiskFactor,
    ThrombectomyComplications,
)
from scripts.normalization.sk_registry import OUTPUT_COLUMNS
from scripts.evaluation.semantic_preservation_full import (
    _check,
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
    def _bundle_with_all_extra_representations(self):
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
                        "resourceType": "Encounter",
                        "meta": {"profile": [
                            "http://qualityregistry.org/StructureDefinition/stroke-encounter-profile"
                        ]},
                        "admission": {
                            "admitSource": concept(AdmissionPathway.INHOSPITAL_STROKE)
                        },
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
                        "resourceType": "Condition",
                        "meta": {"profile": [
                            "http://qualityregistry.org/StructureDefinition/stroke-risk-factor-condition-profile"
                        ]},
                        "code": concept(RiskFactor.Smoker),
                        "clinicalStatus": {
                            "coding": [{"code": "active"}]
                        },
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

    def test_all_ten_previously_excluded_fields_have_comparators(self):
        bundle = self._bundle_with_all_extra_representations()
        checks = {
            "provider": "Example Hospital",
            "provider_id": "12345",
            "carotid_arteries_imaging": True,
            "imaging_done": "1",
            "inhospital_stroke": True,
            "mt_complications_perforation": True,
            "no_thrombolysis_reason": "1",
            "no_thrombectomy_reason": "1",
            "onset_timestamp": "2026-01-15T10:30:00+01:00",
            "risk_smoker_last_10_years": True,
        }

        for field, value in checks.items():
            with self.subTest(field=field):
                self.assertIs(_check(field, value, bundle), True)

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

    def test_missing_reversible_representation_is_counted_as_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "normalized.csv"
            pd.DataFrame([{
                "case": "case-1",
                "inhospital_stroke": True,
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
                        }
                    },
                ],
            }
            (bundle_dir / "case-1.json").write_text(
                json.dumps(bundle), encoding="utf-8"
            )

            report = evaluate_semantic_preservation(csv_path, bundle_dir)

            self.assertEqual(report["unsupportedFields"], [])
            self.assertEqual(report["comparableSourceValues"], 3)
            self.assertEqual(report["matchedValues"], 1)
            self.assertEqual(report["mismatchedValues"], 2)
            self.assertEqual(
                report["byField"]["inhospital_stroke"]["mismatched"], 1
            )
            self.assertEqual(
                report["byField"]["risk_smoker_last_10_years"]["mismatched"], 1
            )


if __name__ == "__main__":
    unittest.main()
