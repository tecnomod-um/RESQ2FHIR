"""Guard FHIR R5 NIHSS numeric values and Encounter actualPeriod."""
import unittest

from scripts.fhir_resources.observation import build_observation_nihss
from scripts.fhir_resources.encounter import build_stroke_encounter_profile


class SlovakFhirBuilderContextRegressions(unittest.TestCase):
    def test_nihss_numeric_value_and_assessment_context(self):
        for score in (0, 7, 42):
            for context_flag, context_code in (
                ("admission_nihss", "admission"),
                ("discharge_nihss", "discharge"),
            ):
                with self.subTest(score=score, context=context_flag):
                    obs = build_observation_nihss(
                        patient_ref="urn:uuid:p",
                        encounter_ref="urn:uuid:e",
                        value_nihss=score,
                        **{context_flag: True},
                    )
                    self.assertEqual(score, obs.valueInteger)
                    self.assertEqual(
                        context_code,
                        obs.extension[0].valueCodeableConcept.coding[0].code,
                    )

    def test_inhospital_encounter_period_r5(self):
        encounter = build_stroke_encounter_profile(
            patient_ref="urn:uuid:p",
            arrival_mode=None,
            inhospital_stroke=True,
            hospital_timestamp="2026-05-21 12:10:00",
            discharge_date="2026-05-23 12:10:00",
        )
        self.assertIsNotNone(encounter.actualPeriod)
        self.assertIsNotNone(encounter.actualPeriod.start)
        self.assertIsNotNone(encounter.actualPeriod.end)


if __name__ == "__main__":
    unittest.main()
