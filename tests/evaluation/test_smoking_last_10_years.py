import unittest

from scripts.evaluation.semantic_preservation_full import NON_REVERSIBLE_FIELDS, _check
from scripts.fhir_resources.condition import build_risk_factor_condition_profile
from scripts.helpers import get_risk_factors
from scripts.local_risk_factors import SMOKING_LAST_10_YEARS


class SmokingLast10YearsTests(unittest.TestCase):
    @staticmethod
    def _has_smoking_concept(concepts):
        # Helpers currently return RiskFactor enum members, whereas the
        # historical fixture is a LocalRiskFactorConcept dataclass. Compare
        # code-system identities, not unrelated Python object types.
        return any(
            concept.system == SMOKING_LAST_10_YEARS.system
            and concept.code == SMOKING_LAST_10_YEARS.code
            for concept in concepts
        )

    def test_helper_maps_true_to_active_and_false_to_inactive(self):
        active, inactive, _, _ = get_risk_factors({"risk_smoker_last_10_years": True})
        self.assertTrue(self._has_smoking_concept(active))
        self.assertFalse(self._has_smoking_concept(inactive))

        active, inactive, _, _ = get_risk_factors({"risk_smoker_last_10_years": False})
        self.assertFalse(self._has_smoking_concept(active))
        self.assertTrue(self._has_smoking_concept(inactive))

    def test_existing_risk_factor_builder_serializes_local_code(self):
        conditions = build_risk_factor_condition_profile(
            risk_factors=[("Active", [SMOKING_LAST_10_YEARS])],
            patient_ref="urn:uuid:patient",
            encounter_ref="urn:uuid:encounter",
        )
        self.assertEqual(len(conditions), 1)
        condition = conditions[0]
        coding = condition.code.coding[0]
        self.assertEqual(coding.system, SMOKING_LAST_10_YEARS.system)
        self.assertEqual(coding.code, SMOKING_LAST_10_YEARS.code)
        self.assertEqual(condition.clinicalStatus.coding[0].code, "active")

    @staticmethod
    def _bundle(status: str) -> dict:
        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Condition",
                        "meta": {
                            "profile": [
                                "http://qualityregistry.org/StructureDefinition/stroke-risk-factor-condition-profile"
                            ]
                        },
                        "code": {
                            "coding": [
                                {
                                    "system": SMOKING_LAST_10_YEARS.system,
                                    "code": SMOKING_LAST_10_YEARS.code,
                                    "display": SMOKING_LAST_10_YEARS.display,
                                }
                            ]
                        },
                        "clinicalStatus": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                    "code": status,
                                }
                            ]
                        },
                    }
                }
            ],
        }

    def test_evaluator_reads_true_from_active_condition(self):
        self.assertIs(
            _check("risk_smoker_last_10_years", True, self._bundle("active")),
            True,
        )

    def test_evaluator_reads_false_from_inactive_condition(self):
        self.assertIs(
            _check("risk_smoker_last_10_years", False, self._bundle("inactive")),
            True,
        )

    def test_status_mismatch_is_detected(self):
        self.assertIs(
            _check("risk_smoker_last_10_years", True, self._bundle("inactive")),
            False,
        )

    def test_tia_history_is_flagged_until_distinct_fhir_encoding_exists(self):
        self.assertEqual(NON_REVERSIBLE_FIELDS, {"risk_tia"})


if __name__ == "__main__":
    unittest.main()
