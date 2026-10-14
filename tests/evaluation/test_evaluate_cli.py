import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.enum_models import FunctionalScore


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


class EvaluationCliTests(unittest.TestCase):
    def test_cli_generates_aggregate_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "normalized.csv"
            bundle_dir = root / "bundles"
            output_path = root / "evaluation.json"
            bundle_dir.mkdir()

            pd.DataFrame([
                {"case": "sk-cli-1", "age": 72}
            ]).to_csv(csv_path, index=False)

            transaction_bundle = {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Patient",
                            "identifier": [{"value": "sk-cli-1"}],
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "status": "final",
                            "code": {"coding": [coding_dict(FunctionalScore.AGE)]},
                            "valueInteger": 72,
                        }
                    },
                ],
            }
            document_bundle = {
                "resourceType": "Bundle",
                "type": "document",
                "entry": [
                    {"resource": {"resourceType": "Composition"}},
                    {"resource": {"resourceType": "Patient"}},
                ],
            }

            (bundle_dir / "sk-cli-1.json").write_text(
                json.dumps(transaction_bundle), encoding="utf-8"
            )
            (bundle_dir / "sk-cli-1.document.json").write_text(
                json.dumps(document_bundle), encoding="utf-8"
            )

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.evaluation.evaluate",
                    "--csv",
                    str(csv_path),
                    "--bundles",
                    str(bundle_dir),
                    "--out",
                    str(output_path),
                ],
                check=True,
            )

            self.assertTrue(output_path.exists())
            report = json.loads(output_path.read_text(encoding="utf-8"))

            semantic = report["semanticPreservation"]
            self.assertEqual(semantic["comparableSourceValues"], 2)
            self.assertEqual(semantic["matchedValues"], 2)
            self.assertEqual(semantic["mismatchedValues"], 0)
            self.assertEqual(semantic["preservationRate"], 1.0)

            counts = report["resourceCounts"]
            self.assertEqual(counts["bundleCounts"]["transaction"], 1)
            self.assertEqual(counts["bundleCounts"]["document"], 1)
            self.assertEqual(counts["transaction"]["resources"], 2)
            self.assertEqual(counts["transaction"]["byResourceType"]["Patient"], 1)
            self.assertEqual(counts["transaction"]["byResourceType"]["Observation"], 1)


if __name__ == "__main__":
    unittest.main()
