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
        self.assertEqual({}, report["reviewFlags"])
        self.assertIn("acceptedMappingConventions", report)
        self.assertNotIn("notYetClinicallyAdjudicated", report)
        self.assertEqual(1, report["byRule"]["mrs_source_to_resq_numeric_value"]["matched"])
        self.assertEqual(1, report["byRule"]["endovascular_source_to_resq_timestamp"]["matched"])
        self.assertEqual(1, report["byRule"]["tici_source_to_resq_grade_code"]["matched"])
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

    def test_mt_external_planned_and_not_done_are_checked(self):
        source = pd.DataFrame([
            {"KKD_TYP_SPEC": "5", "ENDO_VYKON": value}
            for value in ("1", "2", "3", "9")
        ])
        report = self._run(source)
        self.assertEqual(0, report["mismatchedAssertions"])
        self.assertEqual(
            4, report["byRule"]["mt_reporting_hospital_boolean"]["matched"]
        )
        self.assertEqual(
            2, report["byRule"]["mt_external_or_planned_reason"]["matched"]
        )
        self.assertEqual({}, report["reviewFlags"])
        self.assertEqual(4, report["byRule"]["mt_reporting_hospital_boolean"]["matched"])

    def test_audits_explicit_external_and_no_imaging_status(self):
        source = pd.DataFrame([
            {"CT_MR_VYSETRENIE": "2"},
            {"CT_MR_VYSETRENIE": "4"},
            {"CT_MR_VYSETRENIE": "5"},
        ])
        report = self._run(source)
        self.assertEqual(
            3, report["byRule"]["brain_imaging_location_or_absence_status"]["matched"]
        )
        self.assertEqual(
            2, report["byRule"]["external_imaging_modality"]["matched"]
        )
        self.assertEqual(
            1, report["byRule"]["no_imaging_does_not_invent_modality"]["matched"]
        )

    def test_prior_tia_and_ischemic_stroke_are_audited_as_one_indicator(self):
        source = pd.DataFrame([
            {"OA_TIA": "1", "OA_ISCHEMICKA_CMP": "2"},
            {"OA_TIA": "2", "OA_ISCHEMICKA_CMP": "1"},
            {"OA_TIA": "1", "OA_ISCHEMICKA_CMP": "1"},
            {"OA_TIA": "2", "OA_ISCHEMICKA_CMP": "2"},
            {"OA_TIA": "", "OA_ISCHEMICKA_CMP": "2"},
            {"OA_TIA": "", "OA_ISCHEMICKA_CMP": ""},
        ])
        report = self._run(source)
        self.assertEqual(6, report["byRule"][
            "tia_or_ischemic_stroke_combined_resq_indicator"
        ]["matched"])
        self.assertEqual(0, report["mismatchedAssertions"])

    def test_prior_tia_aggregation_corruption_is_detected(self):
        source = pd.DataFrame([{"OA_TIA": "1", "OA_ISCHEMICKA_CMP": "2"}])
        def corrupt(normalized):
            normalized.loc[0, "risk_previous_ischemic_stroke"] = False
        report = self._run(source, mutate=corrupt)
        self.assertEqual(1, report["byRule"][
            "tia_or_ischemic_stroke_combined_resq_indicator"
        ]["mismatched"])

    def test_unknown_tici_is_not_forced_to_grade_three(self):
        source = pd.DataFrame([{"KKD_TYP_SPEC": "5", "TICI": "090"}])
        report = self._run(source)
        self.assertEqual(0, report["mismatchedAssertions"])
        self.assertEqual(
            1, report["byRule"]["tici_unknown_is_not_assigned_a_grade"]["matched"]
        )


if __name__ == "__main__":
    unittest.main()
