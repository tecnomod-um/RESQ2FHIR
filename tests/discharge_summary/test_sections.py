from scripts.discharge_summary.sections import (
    LOINC,
    REGISTRY_ONLY_FIELDS,
    SECTION_DEFINITIONS,
    SECTION_ORDER,
    SECTION_SOURCE_FIELDS,
)
from scripts.enum_models import DischargeSection


def test_all_sections_have_definitions():
    assert set(SECTION_DEFINITIONS) == set(DischargeSection)


def test_all_sections_use_loinc():
    assert all(
        definition.system == LOINC
        for definition in SECTION_DEFINITIONS.values()
    )


def test_section_codes_are_unique():
    codes = [
        definition.code
        for definition in SECTION_DEFINITIONS.values()
    ]

    assert len(codes) == len(set(codes))


def test_section_order_is_unique():
    orders = [
        definition.order
        for definition in SECTION_DEFINITIONS.values()
    ]

    assert len(orders) == len(set(orders))


def test_section_order_contains_every_section():
    assert set(SECTION_ORDER) == set(DischargeSection)


def test_every_section_has_source_field_declaration():
    assert set(SECTION_SOURCE_FIELDS) == set(DischargeSection)


def test_quality_metrics_are_not_document_fields():
    document_fields = {
        field
        for fields in SECTION_SOURCE_FIELDS.values()
        for field in fields
    }

    assert document_fields.isdisjoint(REGISTRY_ONLY_FIELDS)


def test_bleeding_reasons_belong_to_diagnostic_summary():
    fields = SECTION_SOURCE_FIELDS[
        DischargeSection.DIAGNOSTIC_SUMMARY
    ]

    assert "bleeding_reason_hypertension" in fields
    assert "bleeding_reason_aneurysm" in fields
    assert "bleeding_reason_malformation" in fields
    assert "bleeding_reason_anticoagulant" in fields
    assert "bleeding_reason_angiopathy" in fields
    assert "bleeding_reason_brain_tumor" in fields
    assert "bleeding_reason_cvt" in fields
    assert "bleeding_reason_other" in fields