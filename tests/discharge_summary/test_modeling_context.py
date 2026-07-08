from fhir.resources.bundle import (
    BundleEntry,
    BundleEntryRequest,
)
from fhir.resources.patient import Patient

from scripts.data_modeling import build_stroke_case_context, transform_to_fhir
from scripts.data_modeling import transform_to_fhir
from scripts.modeling_context import StrokeCaseContext
import pytest


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
        
