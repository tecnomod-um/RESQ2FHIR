"""Regression tests for original Slovak source -> normalized contract audit."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from scripts.evaluation.source_contract_audit import audit_source_to_contract
from scripts.normalization.sk_registry import normalize_sk_registry_dataframe


class SourceContractAuditTests(unittest.TestCase):
    def _run(self, source: pd.DataFrame, mutate=None) -> dict:
        normalized, _ = normalize_sk_registry_dataframe(source)
        if mutate is not None:
            mutate(normalized)
        with TemporaryDirectory() as directory:
            source_file = Path(directory) / "source.csv"
            normalized_file = Path(directory) / "normalized.csv"
            source.to_csv(source_file, sep=";", index=False)
            normalized.to_csv(normalized_file, index=False)
            return audit_source_to_contract(source_file, normalized_file)

    def test_checks_four_critical_source_mappings_without_patient_values(self):
        source = pd.DataFrame([{
            "KKD_TYP_SPEC": "5",
            "STAV_M_RANKIN_2": "2",
            "DATUM_ENDO_V": "05/21/2026 12:45",
            "TICI": "02b",
            "NL_TROMBOLYZA": "2",
            "NL_DATUM_TROMBOLYZA": "05/21/2026 12:40",
            "DATUM_LEKAR": "05/21/2026 13:10",
        }])
        report = self._run(source)
        self.assertEqual(0, report["mismatchedAssertions"])
        self.assertEqual(report["checkedAssertions"], report["matchedAssertions"])
        self.assertGreaterEqual(report["checkedAssertions"], 6)
        self.assertEqual(
            1, report["reviewFlags"]["ivt_elsewhere_bolus_time_not_checked_in_fhir"]
        )
        self.assertFalse(report["patientLevelValuesIncluded"])
        self.assertNotIn("05/21/2026", str(report))

    def test_catches_lost_external_treatment_reason(self):
        source = pd.DataFrame([{
            "KKD_TYP_SPEC": "5",
            "NL_TROMBOLYZA": "2",
        }])
        def corrupt(normalized):
            normalized.loc[0, "no_thrombolysis_reason"] = None

        report = self._run(source, mutate=corrupt)
        self.assertEqual(1, report["byRule"]["ivt_elsewhere_reason"]["mismatched"])
        self.assertGreaterEqual(report["mismatchedAssertions"], 1)

    def test_unknown_tici_is_not_forced_to_grade_three(self):
        source = pd.DataFrame([{"KKD_TYP_SPEC": "5", "TICI": "090"}])
        report = self._run(source)
        self.assertEqual(0, report["mismatchedAssertions"])
        self.assertEqual(
            1, report["byRule"]["tici_unknown_is_not_assigned_a_grade"]["matched"]
        )


if __name__ == "__main__":
    unittest.main()
