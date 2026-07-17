from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.encounter import Encounter
from fhir.resources.observation import Observation
from fhir.resources.organization import Organization
from fhir.resources.patient import Patient

from scripts.discharge_summary.document import (
    build_discharge_composition,
    build_discharge_document_bundle,
)
from scripts.discharge_summary.ehds_model import TIMING_METRIC_SYSTEM
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
        "Hospital Course",
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
            "Hospital Course",
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


def test_generated_xhtml_has_language_attributes_recursively():
    composition = build_discharge_composition(_minimal_context())

    narratives = [composition.text]

    def collect(sections):
        for section in sections or ():
            narratives.append(section.text)
            collect(section.section)

    collect(composition.section)

    for narrative in narratives:
        assert 'lang="en"' in narrative.div
        assert 'xml:lang="en"' in narrative.div


def test_hospital_course_title_matches_fixed_profile_value():
    composition = build_discharge_composition(_minimal_context())
    course = _section_by_title(composition.section, "Hospital Course")

    assert course.title == "Hospital Course"


def test_treatment_timing_observation_is_selected_by_code():
    context = _minimal_context()
    timing_ref = context.add_resource(
        Observation(
            status="final",
            code=CodeableConcept(
                coding=[
                    Coding(
                        system=TIMING_METRIC_SYSTEM,
                        code="D2N",
                        display="Door to Needle",
                    )
                ]
            ),
            valueInteger=42,
        )
    )

    composition = build_discharge_composition(context)
    course = _section_by_title(
        composition.section,
        "Hospital Course",
    )
    timings = _section_by_title(course.section, "Treatment Timings")

    assert [entry.reference for entry in timings.entry] == [timing_ref]
    assert "Door to Needle" in timings.text.div
    assert "42" in timings.text.div


def test_non_case_summary_timing_metric_is_not_selected():
    context = _minimal_context()
    context.add_resource(
        Observation(
            status="final",
            code=CodeableConcept(
                coding=[
                    Coding(
                        system=TIMING_METRIC_SYSTEM,
                        code="D2N<=45",
                        display="Door to Needle <= 45 Minutes",
                    )
                ]
            ),
            valueBoolean=True,
        )
    )

    composition = build_discharge_composition(context)
    course = _section_by_title(
        composition.section,
        "Hospital Course",
    )

    assert all(
        section.title != "Treatment Timings"
        for section in course.section
    )


def test_document_bundle_contains_selected_timing_observation():
    context = _minimal_context()
    timing_ref = context.add_resource(
        Observation(
            status="final",
            code=CodeableConcept(
                coding=[
                    Coding(
                        system=TIMING_METRIC_SYSTEM,
                        code="D2G",
                        display="Door to Groin",
                    )
                ]
            ),
            valueInteger=78,
        )
    )

    bundle = build_discharge_document_bundle(context)
    full_urls = {str(entry.fullUrl) for entry in bundle.entry}

    assert timing_ref in full_urls
    assert bundle.entry[0].resource.get_resource_type() == "Composition"
