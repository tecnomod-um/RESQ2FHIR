import json
import tempfile
import unittest
from pathlib import Path

from scripts.evaluation.resource_counts import summarize_resource_counts


class ResourceCountTests(unittest.TestCase):
    def test_counts_transaction_and_document_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transaction = {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [
                    {"resource": {"resourceType": "Patient"}},
                    {"resource": {"resourceType": "Observation"}},
                    {"resource": {"resourceType": "Observation"}},
                ],
            }
            document = {
                "resourceType": "Bundle",
                "type": "document",
                "entry": [
                    {"resource": {"resourceType": "Composition"}},
                    {"resource": {"resourceType": "Patient"}},
                ],
            }
            tx_path = root / "sk-1.transaction.json"
            doc_path = root / "sk-1.document.json"
            tx_path.write_text(json.dumps(transaction), encoding="utf-8")
            doc_path.write_text(json.dumps(document), encoding="utf-8")

            report = summarize_resource_counts([tx_path, doc_path])

            self.assertEqual(report["bundleCounts"]["transaction"], 1)
            self.assertEqual(report["bundleCounts"]["document"], 1)
            self.assertEqual(report["transaction"]["resources"], 3)
            self.assertEqual(report["transaction"]["byResourceType"]["Observation"], 2)
            self.assertEqual(report["transaction"]["meanResourcesPerBundle"], 3.0)


if __name__ == "__main__":
    unittest.main()
