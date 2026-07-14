from scripts.discharge_summary.ehds_model import (
    CASE_SUMMARY_SOURCE_FIELDS,
    DOCUMENT_SECTION_DEFINITIONS,
    ROOT_SECTION_ORDER,
    DocumentSection,
    child_sections,
    mapped_source_fields,
    unmapped_case_summary_fields,
)


def test_all_case_summary_variables_are_mapped():
    assert unmapped_case_summary_fields() == ()
    assert set(CASE_SUMMARY_SOURCE_FIELDS).issubset(mapped_source_fields())


def test_ehds_root_section_order_is_deterministic():
    assert ROOT_SECTION_ORDER == (
        DocumentSection.ALERTS,
        DocumentSection.ALLERGIES_INTOLERANCES,
        DocumentSection.ENCOUNTER_INFORMATION,
        DocumentSection.ADMISSION_EVALUATION,
        DocumentSection.PATIENT_HISTORY,
        DocumentSection.COURSE_OF_ENCOUNTER,
        DocumentSection.DISCHARGE_DETAILS,
        DocumentSection.MEDICATION_SUMMARY,
        DocumentSection.PLAN_OF_CARE,
        DocumentSection.CLINICAL_SYNTHESIS,
    )


def test_course_of_encounter_children_follow_ehds_model():
    assert child_sections(DocumentSection.COURSE_OF_ENCOUNTER) == (
        DocumentSection.DIAGNOSTIC_SUMMARY,
        DocumentSection.SIGNIFICANT_PROCEDURES,
        DocumentSection.MEDICAL_DEVICES,
        DocumentSection.PHARMACOTHERAPY,
        DocumentSection.SIGNIFICANT_RESULTS,
    )


def test_discharge_details_children_follow_ehds_model():
    assert child_sections(DocumentSection.DISCHARGE_DETAILS) == (
        DocumentSection.VITAL_SIGNS,
        DocumentSection.ANTHROPOMETRY,
        DocumentSection.PHYSICAL_EXAMINATION,
        DocumentSection.FUNCTIONAL_STATUS,
    )


def test_every_child_section_has_a_defined_parent():
    for definition in DOCUMENT_SECTION_DEFINITIONS.values():
        if definition.parent is not None:
            assert definition.parent in DOCUMENT_SECTION_DEFINITIONS


def test_document_section_codes_are_unique_by_system():
    codes = [
        (definition.system, definition.code)
        for definition in DOCUMENT_SECTION_DEFINITIONS.values()
    ]
    assert len(codes) == len(set(codes))
