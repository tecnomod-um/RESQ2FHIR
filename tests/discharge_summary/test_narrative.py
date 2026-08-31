from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.coding import Coding
from fhir.resources.condition import Condition
from fhir.resources.extension import Extension
from fhir.resources.medication import Medication
from fhir.resources.medicationadministration import MedicationAdministration
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.observation import Observation
from fhir.resources.organization import Organization
from fhir.resources.patient import Patient
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference

from scripts.discharge_summary.document import build_discharge_composition
from scripts.discharge_summary.narrative import medication_administration_summary
from scripts.enum_models import DischargeSection
from scripts.modeling_context import StrokeCaseContext


def _concept(system, code, display):
    return CodeableConcept(
        coding=[Coding(system=system, code=code, display=display)]
    )


def _section_by_title(sections, title):
    return next(section for section in sections if section.title == title)


def _context():
    context = StrokeCaseContext(
        case_id="case-narrative",
        raw={},
        patient_ref="urn:uuid:patient",
        encounter_ref=None,
        organization_ref="urn:uuid:organization",
    )
    patient = Patient(
        id="patient",
        extension=[
            Extension(
                url="http://tecnomod-um.org/StructureDefinition/gender-snomed-ext",
                valueCodeableConcept=_concept(
                    "http://snomed.info/sct",
                    "248152002",
                    "Female (finding)",
                ),
            )
        ],
    )
    context.add_resource(patient, full_url=context.patient_ref)
    context.add_resource(
        Organization(id="organization"),
        full_url=context.organization_ref,
    )
    return context


def _add_age_and_scores(context):
    context.add_resource(
        Observation(
            status="final",
            code=_concept(
                "http://snomed.info/sct",
                "445518008",
                "Age at onset of clinical finding (observable entity)",
            ),
            valueInteger=84,
        ),
        sections=(DischargeSection.ADMISSION_EVALUATION,),
    )
    context.add_resource(
        Observation(
            status="final",
            code=_concept(
                "http://snomed.info/sct",
                "450743008",
                "National Institutes of Health stroke scale score (observable entity)",
            ),
            valueInteger=20,
            extension=[
                Extension(
                    url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
                    valueCodeableConcept=_concept(
                        "http://tecnomod-um.org/CodeSystem/assessment-context-cs",
                        "admission",
                        "Admission",
                    ),
                )
            ],
        ),
        sections=(DischargeSection.ADMISSION_EVALUATION,),
    )
    context.add_resource(
        Observation(
            status="final",
            code=_concept(
                "http://snomed.info/sct",
                "450743008",
                "National Institutes of Health stroke scale score (observable entity)",
            ),
            valueInteger=12,
            extension=[
                Extension(
                    url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
                    valueCodeableConcept=_concept(
                        "http://tecnomod-um.org/CodeSystem/assessment-context-cs",
                        "discharge",
                        "Discharge",
                    ),
                )
            ],
        ),
        sections=(DischargeSection.FUNCTIONAL_STATUS,),
    )
    context.add_resource(
        Observation(
            status="final",
            code=_concept(
                "http://snomed.info/sct",
                "1255866005",
                "Modified Rankin Scale score (observable entity)",
            ),
            valueCodeableConcept=_concept(
                "http://tecnomod-um.org/CodeSystem/mrs-score-cs",
                "1",
                "No significant disability despite symptoms",
            ),
            extension=[
                Extension(
                    url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
                    valueCodeableConcept=_concept(
                        "http://tecnomod-um.org/CodeSystem/assessment-context-cs",
                        "discharge",
                        "Discharge",
                    ),
                )
            ],
        ),
        sections=(DischargeSection.FUNCTIONAL_STATUS,),
    )


def _add_clinical_content(context):
    context.add_resource(
        Condition(
            clinicalStatus=_concept(
                "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "active",
                "Active",
            ),
            code=_concept(
                "http://snomed.info/sct",
                "422504002",
                "Ischemic stroke (disorder)",
            ),
        ),
        sections=(DischargeSection.DIAGNOSTIC_SUMMARY,),
    )
    for code, display in (
        ("66590003", "Alcohol dependence (disorder)"),
        ("73430006", "Sleep apnea (disorder)"),
    ):
        context.add_resource(
            Condition(
                clinicalStatus=_concept(
                    "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "active",
                    "Active",
                ),
                code=_concept("http://snomed.info/sct", code, display),
            ),
            sections=(DischargeSection.PROBLEM_LIST,),
        )

    medication_ref = "urn:uuid:tenectase"
    context.add_resource(
        Medication(
            code=_concept(
                "http://tecnomod-um.org/CodeSystem/tenecteplase-brand-cs",
                "tenectase",
                "Tenectase (Gennova Biopharmaceuticals)",
            ),
            ingredient=[
                {
                    "item": {
                        "concept": _concept(
                            "http://snomed.info/sct",
                            "127967007",
                            "Product containing tenecteplase (medicinal product)",
                        )
                    },
                    "isActive": True,
                }
            ],
        ),
        full_url=medication_ref,
    )
    administration = MedicationAdministration(
        status="completed",
        medication=CodeableReference(
            reference=Reference(reference=medication_ref)
        ),
        dosage={
            "dose": Quantity(
                value=57,
                unit="milligram",
                system="https://ucum.org/ucum",
                code="mg",
            )
        },
    )
    context.add_resource(
        administration,
        sections=(DischargeSection.PHARMACOTHERAPY,),
    )

    context.add_resource(
        MedicationRequest(
            status="active",
            intent="order",
            medication=CodeableReference(
                concept=_concept(
                    "http://snomed.info/sct",
                    "442031002",
                    "Rivaroxaban (substance)",
                )
            ),
            subject=Reference(reference=context.patient_ref),
        ),
        sections=(DischargeSection.DISCHARGE_MEDICATIONS,),
    )
    return administration


def test_medication_administration_narrative_resolves_local_medication():
    context = _context()
    administration = _add_clinical_content(context)

    summary = medication_administration_summary(administration, context)

    assert "Tenectase" in summary
    assert "tenecteplase" in summary
    assert "57 milligram" in summary
    assert "urn:uuid" not in summary


def test_patient_history_keeps_alcohol_and_sleep_apnea():
    context = _context()
    _add_clinical_content(context)

    composition = build_discharge_composition(context)
    history = _section_by_title(
        composition.section,
        "Relevant Patient History",
    )

    assert "alcohol dependence" in history.text.div.lower()
    assert "sleep apnea" in history.text.div.lower()


def test_clinical_synthesis_is_narrative_only_and_uses_discharge_data():
    context = _context()
    _add_age_and_scores(context)
    _add_clinical_content(context)

    composition = build_discharge_composition(context)
    synthesis = _section_by_title(composition.section, "Clinical Synthesis")
    text = synthesis.text.div.lower()

    assert not getattr(synthesis, "entry", None)
    assert "84-year-old female" in text
    assert "ischemic stroke" in text
    assert "admission nihss score of 20" in text
    assert "alcohol dependence" in text
    assert "sleep apnea" in text
    assert "tenectase" in text
    assert "tenecteplase" in text
    assert "57 milligram" in text
    assert "at discharge, the nihss score was 12" in text
    assert "modified rankin scale score was 1" in text
    assert "rivaroxaban" in text
    assert "urn:uuid" not in text
