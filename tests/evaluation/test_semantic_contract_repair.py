import unittest

from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.condition import Condition
from fhir.resources.meta import Meta
from fhir.resources.reference import Reference

from scripts.enum_models import (
    ImagingType,
    NoThrombectomyReason,
    NoThrombolysisReason,
    PerforationProcedures,
)
from scripts.fhir_resources.procedure import build_thrombolysis_procedure
from scripts.modeling_context import StrokeCaseContext


STROKE_PROFILE = (
    "http://qualityregistry.org/StructureDefinition/stroke-diagnosis-condition-profile"
)


def concept_has(concept, member):
    if concept is None:
        return False
    return any(
        coding.system == member.system and coding.code == member.code
        for coding in (concept.coding or [])
    )


def find_procedure(context, member):
    for record in context.resources:
        resource = record.resource
        if resource.get_resource_type() != "Procedure":
            continue
        if concept_has(resource.code, member):
            return resource
    return None


class SemanticContractRepairTests(unittest.TestCase):
    def make_context(self, raw):
        context = StrokeCaseContext(
            case_id="case-1",
            raw=raw,
            patient_ref="urn:uuid:patient",
            encounter_ref="urn:uuid:encounter",
        )
        condition = Condition(
            subject=Reference(reference=context.patient_ref),
            clinicalStatus=CodeableConcept(coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                code="active",
            )]),
            meta=Meta(profile=[STROKE_PROFILE]),
        )
        context.add_resource(condition, full_url="urn:uuid:condition")
        return context

    def test_no_thrombolysis_reason_repairs_existing_not_done_procedure(self):
        context = self.make_context({
            "stroke_type": "1",
            "thrombolysis": False,
            "no_thrombolysis_reason": "2",
        })
        procedure = build_thrombolysis_procedure(
            patient_ref=context.patient_ref,
            encounter_ref=context.encounter_ref,
            condition_ref="urn:uuid:condition",
            thrombolysis=False,
            no_thrombolysis_reason_id=None,
        )
        context.add_resource(procedure)

        context.index_transaction_entries()

        repaired = find_procedure(context, PerforationProcedures.THROMBOLYSIS)
        self.assertIsNotNone(repaired)
        self.assertEqual(repaired.status, "not-done")
        self.assertTrue(
            concept_has(repaired.statusReason, NoThrombolysisReason.TIME_WINDOW)
        )

    def test_reason_creates_not_done_thrombectomy_when_boolean_is_missing(self):
        context = self.make_context({
            "stroke_type": "1",
            "thrombectomy": None,
            "no_thrombectomy_reason": "3",
        })

        context.index_transaction_entries()

        repaired = find_procedure(context, PerforationProcedures.THROMBECTOMY)
        self.assertIsNotNone(repaired)
        self.assertEqual(repaired.status, "not-done")
        self.assertTrue(
            concept_has(repaired.statusReason, NoThrombectomyReason.MILD_DEFICIT)
        )

    def test_carotid_imaging_is_generated_without_post_acute_care(self):
        context = self.make_context({
            "carotid_arteries_imaging": True,
            "post_acute_care": False,
            "carotid_stenosis": False,
        })

        context.index_transaction_entries()

        procedure = find_procedure(context, ImagingType.CAROTID)
        self.assertIsNotNone(procedure)
        self.assertEqual(procedure.status, "completed")

        resource_types = [record.resource_type for record in context.resources]
        self.assertIn("Observation", resource_types)
        self.assertIn("DiagnosticReport", resource_types)

    def test_repairs_are_idempotent(self):
        context = self.make_context({
            "no_thrombolysis_reason": "1",
            "no_thrombectomy_reason": "1",
            "carotid_arteries_imaging": True,
            "post_acute_care": False,
        })

        context.index_transaction_entries()
        first_count = len(context.transaction_entries)
        context.index_transaction_entries()
        second_count = len(context.transaction_entries)

        self.assertEqual(first_count, second_count)


if __name__ == "__main__":
    unittest.main()
