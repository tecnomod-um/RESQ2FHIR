"""FHIR projection tests for NCZI imaging location/absence and partial dates."""
import unittest
from scripts.enum_models import ImagingDone, ImagingType, StrokeType
from scripts.fhir_resources.procedure import build_imaging_procedure
from scripts.fhir_resources.condition import build_stroke_diagnosis_condition_profile
from scripts.evaluation.semantic_preservation_full import _check


class Slovak2024FhirProjectionTests(unittest.TestCase):
    def imaging(self, done, modality=None):
        procedure = build_imaging_procedure(
            patient_ref="urn:uuid:p", encounter_ref="urn:uuid:e",
            diagnostic_report_ref=None, imaging_done=done,
            imaging_type=modality, post_acute_care=False,
            imaging_timestamp=None,
        )
        return procedure

    def bundle(self, resource):
        return {"resourceType": "Bundle", "type": "transaction",
                "entry": [{"resource": resource.model_dump(mode="json", by_alias=True, exclude_none=True)}]}

    def test_external_ct_is_not_local_completed_event(self):
        procedure = self.imaging(ImagingDone.ELSEWHERE, ImagingType.CT)
        self.assertEqual("not-done", procedure.status)
        self.assertEqual("1", ImagingType.CT.id)
        self.assertIsNotNone(procedure.statusReason)
        bundle = self.bundle(procedure)
        self.assertTrue(_check("imaging_done", "3", bundle))
        self.assertTrue(_check("imaging_type", "1", bundle))
        self.assertFalse(_check("imaging_done", "2", bundle))

    def test_external_mr_is_distinct_from_local_mr(self):
        procedure = self.imaging(ImagingDone.ELSEWHERE, ImagingType.MR)
        bundle = self.bundle(procedure)
        self.assertTrue(_check("imaging_done", "3", bundle))
        self.assertTrue(_check("imaging_type", "4", bundle))

    def test_explicit_no_ct_mr_is_not_unknown_or_external(self):
        procedure = self.imaging(ImagingDone.NO, None)
        bundle = self.bundle(procedure)
        self.assertEqual("not-done", procedure.status)
        self.assertEqual("brain-imaging-unspecified", procedure.code.coding[0].code)
        self.assertTrue(_check("imaging_done", "2", bundle))
        self.assertFalse(_check("imaging_done", "3", bundle))
        self.assertFalse(_check("imaging_done", "1", bundle))

    def test_local_ct_is_completed(self):
        bundle = self.bundle(self.imaging(ImagingDone.YES, ImagingType.CT))
        self.assertTrue(_check("imaging_done", "1", bundle))
        self.assertFalse(_check("imaging_done", "2", bundle))

    def diagnosis(self, onset_timestamp):
        return build_stroke_diagnosis_condition_profile(
            patient_ref="urn:uuid:p", encounter_ref="urn:uuid:e",
            stroke_type=StrokeType.ISCHEMIC, stroke_type_mimics=None,
            stroke_etiology_known=False, stroke_etiology=None,
            bleeding_reason_found=False, bleeding_reasons=[],
            wakeup_stroke=False, sleep_timestamp=None,
            onset_timestamp=onset_timestamp, obs_symptoms_tia_ref=None,
            ich_infratentorial=False, ich_supratentorial=False,
            intraventricular_hemorrhage=False,
            subarachnoid_hemorrhage=False,
        )

    def test_partial_onset_date_roundtrip_without_clock(self):
        condition = self.diagnosis("2026-05-21")
        bundle = self.bundle(condition)
        self.assertEqual("2026-05-21", bundle["entry"][0]["resource"]["onsetDateTime"])
        self.assertTrue(_check("onset_timestamp", "2026-05-21", bundle))

    def test_partial_onset_date_rejects_fabricated_midnight(self):
        condition = self.diagnosis("2026-05-21")
        bundle = self.bundle(condition)
        bundle["entry"][0]["resource"]["onsetDateTime"] = "2026-05-21T00:00:00+02:00"
        self.assertFalse(_check("onset_timestamp", "2026-05-21", bundle))


if __name__ == "__main__":
    unittest.main()
