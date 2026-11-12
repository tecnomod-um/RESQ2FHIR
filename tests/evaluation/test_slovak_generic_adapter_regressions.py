"""Generic Slovak/RES-Q adapter: synthetic regression boundaries."""
import unittest
import pandas as pd
from scripts.normalization.slovak import normalize_slovak_dataframe

class GenericSlovakAdapterRegressions(unittest.TestCase):
    def row(self, **values):
        out, _ = normalize_slovak_dataframe(pd.DataFrame([values]))
        return out.iloc[0]

    def test_enum_labels_resolve_to_contract_ids(self):
        row = self.row(sex="male", stroke_type="ischemic",
                       arrival_mode="EMS from home/scene")
        self.assertEqual("1", row["sex"])
        self.assertEqual("1", row["stroke_type"])
        self.assertEqual("1", row["arrival_mode_id"])

    def test_text_boolean_on_non_enum_field(self):
        row = self.row(wakeup_stroke="sí", risk_hypertension="no")
        self.assertEqual(True, row["wakeup_stroke"])
        self.assertEqual(False, row["risk_hypertension"])

    def test_quarter_only_timestamp_is_unknown(self):
        self.assertIsNone(self.row(discharge_date="2024 Q2")["discharge_date"])

    def test_column_alias(self):
        self.assertEqual("case-1", self.row(case_id="case-1")["case"])

    def test_fixed_categorical_numeric_string_must_not_be_boolean(self):
        # Enum identifiers must be resolved before boolean strings.
        row = self.row(sex="1", stroke_type="2", arrival_mode="1")
        self.assertEqual("1", row["sex"])
        self.assertEqual("2", row["stroke_type"])
        self.assertEqual("1", row["arrival_mode_id"])

if __name__ == "__main__":
    unittest.main()
