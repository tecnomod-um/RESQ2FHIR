"""Regression tests for historical Slovak 2024 development incidents.

These tests use synthetic single-row inputs and do not assert clinical
equivalence for mRS or the original TICI scale.
"""
import unittest

import pandas as pd

from scripts.enum_models import AdherenceCodes, AssessmentContext, Medications, RiskFactor
from scripts.helpers import (
    get_before_onset_medications,
    get_on_discharge_medications,
    get_risk_factors,
)
from scripts.fhir_resources.condition import build_risk_factor_condition_profile
from scripts.fhir_resources.medicationRequest import build_on_discharge_medicationRequest_profile
from scripts.fhir_resources.medicationStatement import build_before_onset_medicationStatement_profile
from scripts.fhir_resources.observation import build_observation_vital_signs
from scripts.fhir_resources.discharge_medication_status import (
    STATUS_CODE_SYSTEM,
    build_any_discharge_medication_answer,
    build_discharge_medication_answers_2024,
)
from scripts.evaluation.semantic_preservation import _check
from scripts.normalization.sk_registry import normalize_sk_registry_dataframe


PATIENT = "urn:uuid:test-patient"
ENCOUNTER = "urn:uuid:test-encounter"


def bundle(resource):
    return {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [{"resource": resource.model_dump(by_alias=True, exclude_none=True)}],
    }


def med_code(resource):
    return resource.medication.concept.coding[0].code


class HistoricalIncidents2024Tests(unittest.TestCase):
    def test_anticoagulant_code_01_and_1_are_equivalent_in_2024(self):
        for source in ("01", "1", 1, 1.0):
            with self.subTest(source=source):
                normalized, _ = normalize_sk_registry_dataframe(
                    pd.DataFrame([{"OA_ANTIKOAGULANCIA": source}])
                )
                self.assertEqual(normalized.loc[0, "before_onset_warfarin"], True)
                self.assertEqual(normalized.loc[0, "before_onset_doak"], False)
                self.assertEqual(normalized.loc[0, "before_onset_any_anticoagulant"], True)

    def test_anticoagulant_code_06_and_6_preserve_doac(self):
        for source in ("06", "6", 6, 6.0):
            with self.subTest(source=source):
                normalized, _ = normalize_sk_registry_dataframe(
                    pd.DataFrame([{"OA_ANTIKOAGULANCIA": source}])
                )
                self.assertEqual(normalized.loc[0, "before_onset_doak"], True)
                self.assertEqual(normalized.loc[0, "before_onset_warfarin"], False)
                self.assertEqual(normalized.loc[0, "before_onset_any_anticoagulant"], True)
                taking, _, _ = get_before_onset_medications(
                    normalized.iloc[0].to_dict()
                )
                self.assertIn(Medications.DOAC, taking)
                self.assertNotIn(Medications.ANTICOAGULANT, taking)

    def test_prior_doac_is_serialized_as_specific_medication_statement(self):
        norm, _ = normalize_sk_registry_dataframe(
            pd.DataFrame([{"OA_ANTIKOAGULANCIA": "06"}])
        )
        taken, _, _ = get_before_onset_medications(norm.iloc[0].to_dict())
        statements = build_before_onset_medicationStatement_profile(
            [("Taking", taken)], PATIENT, ENCOUNTER
        )
        doac = next(m for m in statements if med_code(m) == Medications.DOAC.code)
        self.assertEqual(
            "taking", doac.adherence.code.coding[0].code
        )
        self.assertTrue(_check("before_onset_doak", True, bundle(doac)))
        self.assertTrue(_check(
            "before_onset_any_anticoagulant", True, bundle(doac)
        ))

    def test_doac_and_antidepressant_discharge_do_not_collapse_to_other(self):
        source = pd.DataFrame([{
            "UKON_DOAK": "1",
            "UKON_ANTIDEPRESIVA": "1",
            "UKON_NOOTROPIKA": "2",
        }])
        normalized, _ = normalize_sk_registry_dataframe(source)
        row = normalized.iloc[0].to_dict()
        self.assertEqual(row["discharge_doak"], True)
        self.assertEqual(row["discharge_antidepressants"], True)
        self.assertEqual(row["discharge_other"], False)
        self.assertEqual(row["discharge_any_anticoagulant"], True)
        meds = get_on_discharge_medications(row)
        self.assertIn(Medications.DOAC, meds)
        self.assertIn(Medications.ANTIDEPRESSANT, meds)
        self.assertNotIn(Medications.ANTICOAGULANT, meds)
        self.assertNotIn(Medications.OTHER_MEDICATION, meds)
        requests = build_on_discharge_medicationRequest_profile(
            on_discharge_meds=meds, patient_ref=PATIENT, encounter_ref=ENCOUNTER
        )
        codes = {med_code(m) for m in requests}
        self.assertIn(Medications.DOAC.code, codes)
        self.assertIn(Medications.ANTIDEPRESSANT.code, codes)
        self.assertNotIn(Medications.OTHER_MEDICATION.code, codes)
        for field, code in (
            ("discharge_doak", Medications.DOAC.code),
            ("discharge_antidepressants", Medications.ANTIDEPRESSANT.code),
        ):
            matching = next(m for m in requests if med_code(m) == code)
            self.assertTrue(_check(field, True, bundle(matching)))
        doac_request = next(m for m in requests if med_code(m) == Medications.DOAC.code)
        self.assertTrue(_check(
            "discharge_any_anticoagulant", True, bundle(doac_request)
        ))

    def test_missing_doac_does_not_fabricate_prior_statement(self):
        prior, _, _ = get_before_onset_medications({"before_onset_doak": None})
        self.assertNotIn(Medications.DOAC, prior)
        meds = get_on_discharge_medications({
            "discharge_doak": None,
            "discharge_antidepressants": False,
        })
        self.assertNotIn(Medications.DOAC, meds)
        self.assertNotIn(Medications.ANTIDEPRESSANT, meds)

    def test_risk_smoker_contract_true_false_unknown_are_distinct(self):
        for value, group, expected_status in (
            (True, 0, "active"),
            (False, 1, "inactive"),
            (None, 2, "unknown"),
        ):
            with self.subTest(value=value):
                groups = get_risk_factors({"risk_smoker": value})
                self.assertIn(RiskFactor.Smoker, groups[group])
                status = ("Active", "Inactive", "Unknown")[group]
                conditions = build_risk_factor_condition_profile(
                    [(status, [RiskFactor.Smoker])], PATIENT, ENCOUNTER
                )
                self.assertEqual(
                    expected_status, conditions[0].clinicalStatus.coding[0].code
                )
                if value is not None:
                    self.assertTrue(_check(
                        "risk_smoker", value, bundle(conditions[0])
                    ))

    def test_explicit_contract_smoking_true_false_stays_typed(self):
        source = pd.DataFrame([
            {"risk_smoker": True},
            {"risk_smoker": False},
        ])
        normalized, _ = normalize_sk_registry_dataframe(source)
        self.assertEqual(True, normalized.loc[0, "risk_smoker"])
        self.assertEqual(False, normalized.loc[1, "risk_smoker"])

    def test_slovak_2024_source_not_assumed_to_mean_current_smoking(self):
        normalized, _ = normalize_sk_registry_dataframe(
            pd.DataFrame([{"OA_FAJCENIE": "3"}])
        )
        self.assertEqual(normalized.loc[0, "risk_smoker_last_10_years"], True)
        self.assertIsNone(normalized.loc[0, "risk_smoker"])

    def test_med_statement_true_false_unknown_keep_different_adherence(self):
        for value, group, status in (
            (True, 0, "taking"),
            (False, 1, "not-taking"),
            (None, 2, "unknown"),
        ):
            with self.subTest(value=value):
                groups = get_before_onset_medications({"before_onset_asa": value})
                self.assertIn(Medications.ASA, groups[group])
                statements = build_before_onset_medicationStatement_profile(
                    [(("Taking", "Not Taking", "Unknown")[group],
                      [Medications.ASA])], PATIENT, ENCOUNTER
                )
                self.assertEqual(
                    status, statements[0].adherence.code.coding[0].code
                )
                if value is not None:
                    self.assertTrue(_check(
                        "before_onset_asa", value, bundle(statements[0])
                    ))

    def test_discharge_false_or_missing_does_not_create_positive_order(self):
        for value in (False, None):
            with self.subTest(value=value):
                meds = get_on_discharge_medications({"discharge_asa": value})
                self.assertNotIn(Medications.ASA, meds)
                self.assertEqual([], build_on_discharge_medicationRequest_profile(
                    on_discharge_meds=meds, patient_ref=PATIENT, encounter_ref=ENCOUNTER
                ))

    def test_single_systolic_or_diastolic_component_is_valid(self):
        for systolic, diastolic, target in (
            (120, None, "271649006"),
            (None, 80, "271650006"),
        ):
            with self.subTest(systolic=systolic, diastolic=diastolic):
                observation = build_observation_vital_signs(
                    systolic_pressure=systolic,
                    diastolic_pressure=diastolic,
                    patient_ref=PATIENT,
                    encounter_ref=ENCOUNTER,
                    timing=AssessmentContext.ADMISSION,
                )
                self.assertEqual(1, len(observation.component))
                self.assertEqual(
                    target, observation.component[0].code.coding[0].code
                )


    def test_discharge_asa_three_distinct_fhir_states(self):
        # All three source answers are intentionally different in the bundle.
        for source, expected in (("1", True), ("2", False), (None, None)):
            with self.subTest(source=source):
                norm, _ = normalize_sk_registry_dataframe(
                    pd.DataFrame([{"UKON_ASA": source}])
                )
                row = norm.iloc[0].to_dict()
                self.assertEqual(expected, row["discharge_asa"])
                orders = build_on_discharge_medicationRequest_profile(
                    on_discharge_meds=get_on_discharge_medications(row),
                    patient_ref=PATIENT,
                    encounter_ref=ENCOUNTER,
                )
                answers = build_discharge_medication_answers_2024(
                    raw=row, patient_ref=PATIENT, encounter_ref=ENCOUNTER
                )
                fhir_bundle = {
                    "resourceType": "Bundle",
                    "type": "transaction",
                    "entry": [
                        {"resource": resource.model_dump(
                            by_alias=True, exclude_none=True
                        )}
                        for resource in orders + answers
                    ],
                }
                self.assertTrue(_check(
                    "discharge_asa", expected, fhir_bundle
                ))
                asa_orders = [
                    med for med in orders if med_code(med) == Medications.ASA.code
                ]
                asa_answers = [
                    obs for obs in answers
                    if obs.component[0].valueCodeableConcept.coding[0].code
                    == Medications.ASA.code
                ]
                if expected is True:
                    self.assertEqual(1, len(asa_orders))
                    self.assertEqual([], asa_answers)
                elif expected is False:
                    self.assertEqual([], asa_orders)
                    self.assertEqual(1, len(asa_answers))
                    self.assertIs(asa_answers[0].valueBoolean, False)
                    self.assertIsNone(asa_answers[0].dataAbsentReason)
                else:
                    self.assertEqual([], asa_orders)
                    self.assertEqual(1, len(asa_answers))
                    self.assertIsNone(asa_answers[0].valueBoolean)
                    self.assertEqual(
                        "unknown",
                        asa_answers[0].dataAbsentReason.coding[0].code,
                    )

    def test_unknown_not_accepted_as_explicit_no_or_yes(self):
        no = build_discharge_medication_answers_2024(
            raw={"discharge_asa": False},
            patient_ref=PATIENT, encounter_ref=ENCOUNTER,
        )
        unknown = build_discharge_medication_answers_2024(
            raw={"discharge_asa": None},
            patient_ref=PATIENT, encounter_ref=ENCOUNTER,
        )
        self.assertEqual(1, len(no))
        self.assertEqual(1, len(unknown))
        self.assertFalse(_check("discharge_asa", None, bundle(no[0])))
        self.assertFalse(_check("discharge_asa", False, bundle(unknown[0])))
        self.assertFalse(_check("discharge_asa", True, bundle(no[0])))
        self.assertFalse(_check("discharge_asa", True, bundle(unknown[0])))

    def test_unprovided_contract_field_makes_no_unsupported_assertion(self):
        self.assertEqual([], build_discharge_medication_answers_2024(
            raw={}, patient_ref=PATIENT, encounter_ref=ENCOUNTER,
        ))
        self.assertFalse(_check("discharge_asa", False, {
            "resourceType": "Bundle", "type": "transaction", "entry": [],
        }))

    def test_discharge_no_medication_is_not_fabricated_as_active_order(self):
        obs = build_any_discharge_medication_answer(
            answer=False, patient_ref=PATIENT, encounter_ref=ENCOUNTER
        )
        self.assertIs(obs.valueBoolean, False)
        self.assertEqual(
            "any-medication-prescribed-at-discharge",
            obs.code.coding[0].code,
        )

    def test_all_eight_original_2024_discharge_classes_are_supported(self):
        # Every source-specific class can represent known NO and UNKNOWN.
        source = {
            "discharge_asa": False,
            "discharge_clopidogrel": False,
            "discharge_warfarin": False,
            "discharge_heparin": False,
            "discharge_doak": False,
            "discharge_statin": False,
            "discharge_other": False,
            "discharge_antidepressants": False,
        }
        answers = build_discharge_medication_answers_2024(
            raw=source, patient_ref=PATIENT, encounter_ref=ENCOUNTER
        )
        self.assertEqual(8, len(answers))
        expected_status_code = "medication-prescribed-at-discharge"
        for obs in answers:
            self.assertEqual(STATUS_CODE_SYSTEM, obs.code.coding[0].system)
            self.assertEqual(expected_status_code, obs.code.coding[0].code)
            self.assertIs(obs.valueBoolean, False)
            self.assertIsNone(obs.dataAbsentReason)


if __name__ == "__main__":
    unittest.main()
