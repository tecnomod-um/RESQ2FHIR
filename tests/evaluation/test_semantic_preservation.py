import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.enum_models import FunctionalScore, Sex, StrokeType
from scripts.evaluation.semantic_preservation import evaluate_semantic_preservation


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


class SemanticPreservationTests(unittest.TestCase):
    def _write_fixture(self, root: Path, age_in_bundle: int = 72):
        csv_path = root / "normalized.csv"
        pd.DataFrame([
            {
                "case": "sk-1",
                "sex": "1",
                "age": 72,
                "stroke_type": "1",
                "wakeup_stroke": True,
            }
        ]).to_csv(csv_path, index=False)

        bundle_dir = root / "bundles"
        bundle_dir.mkdir()
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "identifier": [{"value": "sk-1"}],
                        "extension": [{
                            "url": "http://qualityregistry.org/StructureDefinition/gender-snomed-ext",
                            "valueCodeableConcept": {"coding": [coding_dict(Sex.by_id("1"))]},
                        }],
                    }
                },
                {
                    "resource": {
                        "resourceType": "Observation",
                        "status": "final",
                        "code": {"coding": [coding_dict(FunctionalScore.AGE)]},
                        "valueInteger": age_in_bundle,
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "meta": {"profile": [
                            "http://qualityregistry.org/StructureDefinition/stroke-diagnosis-condition-profile"
                        ]},
                        "code": {"coding": [coding_dict(StrokeType.by_id("1"))]},
                        "extension": [{
                            "url": "http://qualityregistry.org/StructureDefinition/wakeup-stroke-ext",
                            "valueBoolean": True,
                        }],
                    }
                },
            ],
        }
        (bundle_dir / "sk-1.json").write_text(json.dumps(bundle), encoding="utf-8")
        return csv_path, bundle_dir

    def test_reports_complete_match_for_supported_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path, bundle_dir = self._write_fixture(Path(tmp))
            report = evaluate_semantic_preservation(csv_path, bundle_dir)

            self.assertEqual(report["comparableSourceValues"], 5)
            self.assertEqual(report["matchedValues"], 5)
            self.assertEqual(report["mismatchedValues"], 0)
            self.assertEqual(report["preservationRate"], 1.0)

    def test_detects_value_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path, bundle_dir = self._write_fixture(Path(tmp), age_in_bundle=71)
            report = evaluate_semantic_preservation(csv_path, bundle_dir)

            self.assertEqual(report["byField"]["age"]["mismatched"], 1)
            self.assertLess(report["preservationRate"], 1.0)


if __name__ == "__main__":
    unittest.main()
