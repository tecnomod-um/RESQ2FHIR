"""Controlled semantic mutations for normalized contract -> FHIR read-back.

Not a FHIR validator sensitivity experiment: these tests measure ONLY whether
the deterministic semantic evaluator notices altered but plausible fields.
"""
import copy
import unittest
from scripts.enum_models import (
    FunctionalScore, AssessmentContext, PerforationProcedures,
    NoThrombolysisReason,
)
from scripts.evaluation.semantic_preservation_full import _check


def concept(member):
    return {"coding": [{"system": member.system, "code": member.code}]}


def valid_fixture():
    return {"resourceType": "Bundle", "type": "transaction", "entry": [
        {"resource": {
            "resourceType": "Observation", "status": "final",
            "code": concept(FunctionalScore.AGE), "valueInteger": 72,
        }},
        {"resource": {
            "resourceType": "Observation", "status": "final",
            "code": concept(FunctionalScore.NIHSS), "valueInteger": 7,
            "extension": [{
                "url": "http://qualityregistry.org/StructureDefinition/observation-timing-context-ext",
                "valueCodeableConcept": concept(AssessmentContext.ADMISSION),
            }],
        }},
        {"resource": {
            "resourceType": "Procedure", "status": "not-done",
            "code": concept(PerforationProcedures.THROMBOLYSIS),
            "statusReason": concept(NoThrombolysisReason.DONE_ELSEWHERE),
        }},
    ]}


class ControlledSemanticMutations(unittest.TestCase):
    def test_unmodified_fixture_passes_all_three_comparators(self):
        bundle = valid_fixture()
        for field, value in (("age", 72), ("nihss_score", 7),
                             ("no_thrombolysis_reason", "1")):
            with self.subTest(field=field):
                self.assertIs(True, _check(field, value, bundle))

    def test_changed_valid_age_is_detected(self):
        bundle = copy.deepcopy(valid_fixture())
        bundle["entry"][0]["resource"]["valueInteger"] = 71
        self.assertIs(False, _check("age", 72, bundle))

    def test_changed_nihss_value_is_detected(self):
        bundle = copy.deepcopy(valid_fixture())
        bundle["entry"][1]["resource"]["valueInteger"] = 8
        self.assertIs(False, _check("nihss_score", 7, bundle))

    def test_changed_nihss_assessment_context_is_detected(self):
        bundle = copy.deepcopy(valid_fixture())
        bundle["entry"][1]["resource"]["extension"][0]["valueCodeableConcept"] = concept(AssessmentContext.DISCHARGE)
        self.assertIs(False, _check("nihss_score", 7, bundle))

    def test_changed_external_thrombolysis_reason_is_detected(self):
        bundle = copy.deepcopy(valid_fixture())
        bundle["entry"][2]["resource"]["statusReason"] = concept(NoThrombolysisReason.TIME_WINDOW)
        self.assertIs(False, _check("no_thrombolysis_reason", "1", bundle))

    def test_missing_external_thrombolysis_reason_is_detected(self):
        bundle = copy.deepcopy(valid_fixture())
        del bundle["entry"][2]["resource"]["statusReason"]
        self.assertIs(False, _check("no_thrombolysis_reason", "1", bundle))


if __name__ == "__main__":
    unittest.main()
