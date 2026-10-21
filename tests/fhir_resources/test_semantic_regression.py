import unittest

from scripts.fhir_resources.procedure import (
    build_thrombectomy_procedure,
    build_swallowing_screening_procedure,
)
from scripts.enum_models import (
    SwallowingScreeningDone,
)


class SemanticRegressionTests(unittest.TestCase):

    def test_thrombectomy_preserves_puncture_without_reperfusion(self):
        procedure = build_thrombectomy_procedure(
            thrombectomy=True,
            post_acute_care=False,
            patient_ref="urn:uuid:patient",
            encounter_ref="urn:uuid:encounter",
            condition_ref="urn:uuid:condition",
            puncture_timestamp="2026-01-01 10:00:00",
            reperfusion_timestamp=None,
        )

        self.assertEqual("completed", procedure.status)
        self.assertIsNotNone(procedure.occurrencePeriod)
        self.assertIsNotNone(procedure.occurrencePeriod.start)
        self.assertIsNone(procedure.occurrencePeriod.end)


if __name__ == "__main__":
    unittest.main()