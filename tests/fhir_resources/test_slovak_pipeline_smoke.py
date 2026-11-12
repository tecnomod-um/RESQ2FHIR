"""Synthetic original-NCZI → normalized contract → real FHIR generator smoke tests.

Checks the actual converter, not only the isolated resource builder. These are
not profile validation or clinical-equivalence assertions.
"""
import unittest

import pandas as pd

from scripts.normalization.sk_registry import normalize_sk_registry_dataframe
from scripts.transform import transform_row_to_bundles, bundle_to_json_dict, row_to_dict
from scripts.evaluation.semantic_preservation_full import _check


class SlovakMappingPipelineSmokeTests(unittest.TestCase):
    def generate(self, **overrides):
        src = {
            "ICO": "12345678", "NAZOV": "Synthetic Stroke Hospital",
            "PACVEK": "72", "PACPOHLAVIE": "1",
            "KKD_TYP_SPEC": "5", "TRANSPORT_SPE": "1",
            "CT_MR_VYSETRENIE": "1",
            "NL_TROMBOLYZA": "3", "ENDO_VYKON": "9",
        }
        src.update(overrides)
        normalized, _ = normalize_sk_registry_dataframe(pd.DataFrame([src]))
        row = normalized.iloc[0]
        raw = row_to_dict(row)
        self.assertEqual("1", raw["sex"])
        self.assertEqual("1", raw["stroke_type"])
        bundles = transform_row_to_bundles(row, 1, bundle_mode="transaction")
        self.assertIsNotNone(bundles, "Synthetic source row failed FHIR conversion")
        serialized = bundle_to_json_dict(bundles["transaction"])
        return row, serialized

    def test_no_imaging_goes_through_actual_converter(self):
        row, bundle = self.generate(CT_MR_VYSETRENIE="5")
        self.assertEqual("2", row["imaging_done"])
        self.assertTrue(_check("imaging_done", "2", bundle))
        self.assertFalse(_check("imaging_done", "3", bundle))

    def test_external_ct_retains_external_not_local_semantics(self):
        row, bundle = self.generate(CT_MR_VYSETRENIE="2")
        self.assertEqual("3", row["imaging_done"])
        self.assertTrue(_check("imaging_done", "3", bundle))
        self.assertTrue(_check("imaging_type", "1", bundle))

    def test_combined_ct_imaging_uses_perfusion_category(self):
        row, bundle = self.generate(
            CT_MR_VYSETRENIE="1", CT_ANGIO="1", CT_PERFUZNE="1",
        )
        self.assertEqual("3", row["imaging_type"])
        self.assertTrue(_check("imaging_type", "3", bundle))


if __name__ == "__main__":
    unittest.main()
