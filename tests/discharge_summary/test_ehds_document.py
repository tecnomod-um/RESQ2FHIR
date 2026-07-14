from fhir.resources.encounter import Encounter
from fhir.resources.observation import Observation
from fhir.resources.organization import Organization
from fhir.resources.patient import Patient

from scripts.discharge_summary.document import build_discharge_composition
from scripts.enum_models import DischargeSection
from scripts.modeling_context import StrokeCaseContext


def _section_by_title(sections, title):
    return next(section for section in sections if section.title == title)


def _minimal_context():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
        patient_ref="urn:uuid:patient",
        encounter_ref="urn:uuid:encounter",
        organization_ref="urn:uuid:organization",
    )
    context.add_resource(
        Patient(id="patient"),
        full_url=context.patient_ref,
    )
    context.add_resource(
        Encounter(status="completed"),
        full_url=context.encounter_ref,
    )
    context.add_resource(
        Organization(id="organization"),
        full_url=context.organization_ref,
    )
    return context


def test_composition_uses_ehds_hierarchy():
    context = _minimal_context()
    context.add_resource(
        Observation(status="final"),
        sections=(DischargeSection.SIGNIFICANT_RESULTS,),
    )

    composition = build_discharge_composition(context)
    course = _section_by_title(
        composition.section,
        "Course of Encounter",
    )
    discharge = _section_by_title(
        composition.section,
        "Discharge Details",
    )

    assert [section.title for section in course.section] == [
        "Diagnostic Summary",
        "Significant Procedures",
        "Medical Devices and Implants",
        "Significant Test Results",
    ]
    assert [section.title for section in discharge.section] == [
        "Vital Signs at Discharge",
        "Anthropometric Measurements",
        "Physical Examination at Discharge",
        "Functional Status at Discharge",
    ]


def test_missing_core_information_is_explicitly_represented():
    composition = build_discharge_composition(_minimal_context())

    allergies = _section_by_title(
        composition.section,
        "Allergies and Intolerances",
    )
    devices = _section_by_title(
        _section_by_title(
            composition.section,
            "Course of Encounter",
        ).section,
        "Medical Devices and Implants",
    )

    assert allergies.emptyReason.coding[0].code == "notasked"
    assert devices.emptyReason.coding[0].code == "notasked"


def test_encounter_is_present_in_encounter_and_discharge_sections():
    composition = build_discharge_composition(_minimal_context())

    encounter_information = _section_by_title(
        composition.section,
        "Encounter Information",
    )
    discharge_details = _section_by_title(
        composition.section,
        "Discharge Details",
    )

    expected = "urn:uuid:encounter"
    assert encounter_information.entry[0].reference == expected
    assert discharge_details.entry[0].reference == expected
