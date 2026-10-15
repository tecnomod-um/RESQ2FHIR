import unittest

from scripts.enum_models import BleedingReason, StrokeEtiology, StrokeType
from scripts.fhir_resources.condition import build_stroke_diagnosis_condition_profile


ISCHEMIC_ETIOLOGY_URL = (
    "http://qualityregistry.org/StructureDefinition/ischemic-stroke-etiology-ext"
)
BLEEDING_REASON_URL = (
    "http://qualityregistry.org/StructureDefinition/hemorrhagic-stroke-bleeding-reason-ext"
)


class StrokeDiagnosisConditionTests(unittest.TestCase):
    def _build(
        self,
        *,
        stroke_type,
        stroke_etiology_known=False,
        stroke_etiology=None,
        bleeding_reason_found=False,
        bleeding_reasons=None,
        obs_symptoms_tia_ref=None,
    ):
        return build_stroke_diagnosis_condition_profile(
            patient_ref="urn:uuid:patient",
            encounter_ref="urn:uuid:encounter",
            stroke_type=stroke_type,
            stroke_type_mimics=None,
            stroke_etiology_known=stroke_etiology_known,
            stroke_etiology=stroke_etiology,
            bleeding_reason_found=bleeding_reason_found,
            bleeding_reasons=bleeding_reasons or [],
            wakeup_stroke=False,
            sleep_timestamp=None,
            onset_timestamp=None,
            obs_symptoms_tia_ref=obs_symptoms_tia_ref,
            ich_infratentorial=False,
            ich_supratentorial=False,
            intraventricular_hemorrhage=False,
            subarachnoid_hemorrhage=False,
        )

    @staticmethod
    def _extension_urls(condition):
        return [extension.url for extension in (condition.extension or [])]

    def test_tia_does_not_serialize_ischemic_etiology(self):
        """Regression for ischemic-etiology-only-for-ischemic-stroke."""
        condition = self._build(
            stroke_type=StrokeType.TRANSIENT_ISCHEMIC,
            stroke_etiology_known=True,
            stroke_etiology=StrokeEtiology.CARDIOEMBOLYSM,
        )

        self.assertNotIn(ISCHEMIC_ETIOLOGY_URL, self._extension_urls(condition))

    def test_ischemic_stroke_serializes_etiology_once(self):
        condition = self._build(
            stroke_type=StrokeType.ISCHEMIC,
            stroke_etiology_known=True,
            stroke_etiology=StrokeEtiology.CARDIOEMBOLYSM,
        )

        self.assertEqual(
            self._extension_urls(condition).count(ISCHEMIC_ETIOLOGY_URL),
            1,
        )

    def test_hemorrhagic_stroke_serializes_bleeding_reason_once(self):
        condition = self._build(
            stroke_type=StrokeType.INTRACEREBRAL_HEMORRHAGE,
            bleeding_reason_found=True,
            bleeding_reasons=[BleedingReason.ANEURYSM],
        )

        self.assertEqual(
            self._extension_urls(condition).count(BLEEDING_REASON_URL),
            1,
        )

    def test_tia_references_symptom_observation_when_available(self):
        symptom_ref = "urn:uuid:tia-symptoms"
        condition = self._build(
            stroke_type=StrokeType.TRANSIENT_ISCHEMIC,
            obs_symptoms_tia_ref=symptom_ref,
        )

        self.assertTrue(condition.evidence)
        self.assertEqual(condition.evidence[0].reference.reference, symptom_ref)


if __name__ == "__main__":
    unittest.main()
