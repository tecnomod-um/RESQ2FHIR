from fhir.resources.bundle import (
    BundleEntry,
    BundleEntryRequest,
)
from fhir.resources.patient import Patient

from scripts.data_modeling import build_stroke_case_context, transform_to_fhir
from scripts.data_modeling import transform_to_fhir
from scripts.modeling_context import StrokeCaseContext


def test_context_indexes_transaction_entries():
    patient = Patient(
        id="patient-1",
    )

    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    context.transaction_entries.append(
        BundleEntry(
            fullUrl="urn:uuid:patient-1",
            resource=patient,
            request=BundleEntryRequest(
                method="POST",
                url="Patient",
            ),
        )
    )

    context.index_transaction_entries()

    record = context.get_resource(
        "urn:uuid:patient-1"
    )

    assert record is not None
    assert record.resource is patient
    assert record.resource_type == "Patient"
    assert record.sections == set()


from scripts.modeling_context import StrokeCaseContext
from scripts.utils import TransformError


def test_context_fails_when_required_resource_is_missing():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    with pytest.raises(
        TransformError,
        match="FHIR resource not found",
    ):
        context.require_resource(
            "urn:uuid:missing"
        )

def test_context_rejects_duplicate_full_urls():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    for patient_id in ("patient-1", "patient-2"):
        context.transaction_entries.append(
            BundleEntry(
                fullUrl="urn:uuid:duplicated",
                resource=Patient(id=patient_id),
                request=BundleEntryRequest(
                    method="POST",
                    url="Patient",
                ),
            )
        )

    with pytest.raises(
        TransformError,
        match="Duplicate BundleEntry.fullUrl",
    ):
        context.index_transaction_entries()

def test_context_rejects_duplicate_full_urls():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    for patient_id in ("patient-1", "patient-2"):
        context.transaction_entries.append(
            BundleEntry(
                fullUrl="urn:uuid:duplicated",
                resource=Patient(id=patient_id),
                request=BundleEntryRequest(
                    method="POST",
                    url="Patient",
                ),
            )
        )

    with pytest.raises(
        TransformError,
        match="Duplicate BundleEntry.fullUrl",
    ):
        context.index_transaction_entries()
        
from fhir.resources.observation import Observation

from scripts.enum_models import DischargeSection
from scripts.modeling_context import StrokeCaseContext


def test_add_resource_registers_transaction_entry_and_section():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    observation = Observation(
        status="final",
    )

    full_url = context.add_resource(
        observation,
        sections=(
            DischargeSection.ADMISSION_EVALUATION,
        ),
    )

    assert len(context.transaction_entries) == 1
    assert context.transaction_entries[0].fullUrl == full_url
    assert context.transaction_entries[0].request.method == "POST"
    assert context.transaction_entries[0].request.url == "Observation"

    record = context.require_resource(full_url)

    assert record.resource is observation
    assert record.sections == {
        DischargeSection.ADMISSION_EVALUATION
    }

def test_reindex_preserves_document_sections():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    full_url = context.add_resource(
        Observation(status="final"),
        sections=(
            DischargeSection.ADMISSION_EVALUATION,
        ),
    )

    context.index_transaction_entries()

    assert context.require_resource(full_url).sections == {
        DischargeSection.ADMISSION_EVALUATION
    }

import pytest

from fhir.resources.patient import Patient

from scripts.utils import TransformError


def test_add_resource_rejects_invalid_section_resource_type():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    with pytest.raises(
        TransformError,
        match="Patient cannot be added",
    ):
        context.add_resource(
            Patient(),
            sections=(
                DischargeSection.DIAGNOSTIC_SUMMARY,
            ),
        )

def test_resources_for_section_preserves_modeling_order():
    context = StrokeCaseContext(
        case_id="case-1",
        raw={},
    )

    first_ref = context.add_resource(
        Observation(status="final"),
        sections=(
            DischargeSection.ADMISSION_EVALUATION,
        ),
    )

    context.add_resource(
        Observation(status="final"),
        sections=(
            DischargeSection.SIGNIFICANT_RESULTS,
        ),
    )

    third_ref = context.add_resource(
        Observation(status="final"),
        sections=(
            DischargeSection.ADMISSION_EVALUATION,
        ),
    )

    records = context.resources_for_section(
        DischargeSection.ADMISSION_EVALUATION
    )

    assert [
        record.full_url
        for record in records
    ] == [
        first_ref,
        third_ref,
    ]