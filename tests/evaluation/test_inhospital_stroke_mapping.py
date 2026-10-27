import unittest

from scripts.fhir_resources.encounter import build_stroke_encounter_profile
from scripts.utils import parse_datetime


class InHospitalStrokeEncounterMappingTests(unittest.TestCase):
    def test_true_uses_hospital_timestamp_as_encounter_start(self):
        hospital_timestamp = "2026-01-15 10:30:00"
        encounter = build_stroke_encounter_profile(
            patient_ref="urn:uuid:patient",
            arrival_mode=None,
            inhospital_stroke=True,
            hospital_timestamp=hospital_timestamp,
        )

        self.assertIsNotNone(encounter.actualPeriod)
        self.assertEqual(
            encounter.actualPeriod.start,
            parse_datetime(hospital_timestamp),
        )

    def test_false_does_not_use_hospital_timestamp_as_encounter_start(self):
        encounter = build_stroke_encounter_profile(
            patient_ref="urn:uuid:patient",
            arrival_mode=None,
            inhospital_stroke=False,
            hospital_timestamp="2026-01-15 10:30:00",
        )

        self.assertIsNotNone(encounter.actualPeriod)
        self.assertIsNone(encounter.actualPeriod.start)

    def test_none_does_not_use_hospital_timestamp_as_encounter_start(self):
        encounter = build_stroke_encounter_profile(
            patient_ref="urn:uuid:patient",
            arrival_mode=None,
            inhospital_stroke=None,
            hospital_timestamp="2026-01-15 10:30:00",
        )

        self.assertIsNotNone(encounter.actualPeriod)
        self.assertIsNone(encounter.actualPeriod.start)


if __name__ == "__main__":
    unittest.main()
