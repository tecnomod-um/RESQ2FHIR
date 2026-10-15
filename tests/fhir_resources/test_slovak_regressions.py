import unittest
from unittest.mock import Mock, patch

import pandas as pd

from scripts.normalization.sk_registry import normalize_sk_registry_dataframe
from scripts.data_modeling import _add_thrombolysis_location


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
