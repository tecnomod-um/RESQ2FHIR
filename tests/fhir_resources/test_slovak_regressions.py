import unittest
from unittest.mock import Mock, patch

import pandas as pd

from scripts.normalization.sk_registry import normalize_sk_registry_dataframe
from scripts.data_modeling import _add_thrombolysis_location
from scripts.enum_models import NoThrombolysisReason
from scripts.fhir_resources.procedure import build_thrombolysis_procedure


class SlovakRegressionTests(unittest.TestCase):
    def test_non_ischemic_cases_do_not_export_ischemic_etiology(self):
        source = pd.DataFrame([
            {"KKD_TYP_SPEC": "4", "ETIO_ISCH_CMP": "1"},  # TIA
            {"KKD_TYP_SPEC": "5", "ETIO_ISCH_CMP": "1"},  # ischemic stroke
        ])

        normalized, _ = normalize_sk_registry_dataframe(source)

        etiology_fields = [
            "stroke_etiology_cardioembolism",
            "stroke_etiology_la_atherosclerosis",
            "stroke_etiology_lacunar",
            "stroke_etiology_cryptogenic_stroke",
            "stroke_etiology_other",
        ]

        self.assertEqual("3", normalized.loc[0, "stroke_type"])
        self.assertTrue(all(normalized.loc[0, field] is None for field in etiology_fields))

        self.assertEqual("1", normalized.loc[1, "stroke_type"])
        self.assertEqual(True, normalized.loc[1, "stroke_etiology_cardioembolism"])
        self.assertEqual(False, normalized.loc[1, "stroke_etiology_la_atherosclerosis"])

    def test_thrombolysis_at_reporting_hospital_elsewhere_and_not_given(self):
        source = pd.DataFrame([
            {
                "KKD_TYP_SPEC": "5",  # Ischemic
                "NL_TROMBOLYZA": "1",
                "DATUM_LEKAR": "05/21/2026 12:10",
                "NL_DATUM_TROMBOLYZA": "05/21/2026 12:40",
            },
            {
                "KKD_TYP_SPEC": "5",
                "NL_TROMBOLYZA": "2",  # Administered in another hospital
                "DATUM_LEKAR": "05/21/2026 13:10",
                "NL_DATUM_TROMBOLYZA": "05/21/2026 12:40",
            },
            {"KKD_TYP_SPEC": "5", "NL_TROMBOLYZA": "3"},  # Not given
        ])

        normalized, _ = normalize_sk_registry_dataframe(source)

        self.assertEqual([True, False, False], normalized["thrombolysis"].tolist())
        self.assertTrue(pd.isna(normalized.loc[0, "no_thrombolysis_reason"]))
        self.assertEqual("1", normalized.loc[1, "no_thrombolysis_reason"])
        self.assertTrue(pd.isna(normalized.loc[2, "no_thrombolysis_reason"]))
        self.assertEqual(30, normalized.loc[0, "door_to_needle"])
        self.assertTrue(pd.isna(normalized.loc[1, "door_to_needle"]))
        self.assertEqual(
            "2026-05-21 12:40:00", normalized.loc[1, "bolus_timestamp"]
        )

    def test_elsewhere_dominates_conflicting_no_ivt_flags_and_warns(self):
        source = pd.DataFrame([{
            "KKD_TYP_SPEC": "5",
            "NL_TROMBOLYZA": "2",
            "DNTL_MIMO_CAS": "1",
        }])

        with self.assertLogs("scripts.normalization.sk_registry", level="WARNING"):
            normalized, _ = normalize_sk_registry_dataframe(source)

        self.assertEqual("1", normalized.loc[0, "no_thrombolysis_reason"])

    def test_elsewhere_reason_is_serializable_in_current_resq_profile(self):
        procedure = build_thrombolysis_procedure(
            patient_ref="urn:uuid:patient",
            encounter_ref="urn:uuid:encounter",
            condition_ref="urn:uuid:condition",
            thrombolysis=False,
            no_thrombolysis_reason_id=NoThrombolysisReason.DONE_ELSEWHERE,
        )

        self.assertEqual("not-done", procedure.status)
        self.assertEqual(
            NoThrombolysisReason.DONE_ELSEWHERE.code,
            procedure.statusReason.coding[0].code,
        )

    def test_2024_thrombectomy_here_elsewhere_planned_and_not_done(self):
        # 2024 ZR_NEUR_CMP form: 1 local; 2 elsewhere; 3 planned transfer; 9 no MT.
        source = pd.DataFrame([
            {"KKD_TYP_SPEC": "5", "ENDO_VYKON": source_code}
            for source_code in ("1", "2", "3", "9")
        ])
        normalized, _ = normalize_sk_registry_dataframe(source)
        self.assertEqual(
            [True, False, False, False], normalized["thrombectomy"].tolist()
        )
        self.assertEqual("1", normalized.loc[1, "no_thrombectomy_reason"])
        self.assertEqual("8", normalized.loc[2, "no_thrombectomy_reason"])
        self.assertTrue(pd.isna(normalized.loc[0, "no_thrombectomy_reason"]))
        self.assertTrue(pd.isna(normalized.loc[3, "no_thrombectomy_reason"]))

    def test_planned_mt_transfer_overrides_conflicting_no_mt_reason(self):
        source = pd.DataFrame([{
            "KKD_TYP_SPEC": "5", "ENDO_VYKON": "3", "NMT_MIMO_CAS": "1",
        }])
        with self.assertLogs("scripts.normalization.sk_registry", level="WARNING"):
            normalized, _ = normalize_sk_registry_dataframe(source)
        self.assertEqual(False, normalized.loc[0, "thrombectomy"])
        self.assertEqual("8", normalized.loc[0, "no_thrombectomy_reason"])

    def test_missing_ivt_department_does_not_create_location_reference(self):
        context = Mock()

        location_ref = _add_thrombolysis_location(context, None)

        self.assertIsNone(location_ref)
        context.add_resource.assert_not_called()

    @patch("scripts.data_modeling.build_location")
    @patch("scripts.data_modeling.get_uuid", return_value="urn:uuid:ivt-location")
    def test_ivt_department_creates_matching_location_reference(self, _get_uuid, build_location):
        context = Mock()
        location = object()
        build_location.return_value = location

        location_ref = _add_thrombolysis_location(context, "1")

        self.assertEqual("urn:uuid:ivt-location", location_ref)
        context.add_resource.assert_called_once_with(
            location,
            full_url="urn:uuid:ivt-location",
        )


if __name__ == "__main__":
    unittest.main()
