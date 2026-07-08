"""Shared modeling context for one RESQ+ stroke case.

The context stores the FHIR resources created while transforming one source
record. It is shared by the transaction Bundle and, in a later step, by the
Hospital Discharge Report document Bundle.

This module does not classify resources into document sections and does not
construct a Composition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fhir.resources.bundle import BundleEntry

from scripts.enum_models import DischargeSection
from scripts.utils import TransformError


@dataclass
class StrokeCaseResource:
    """One FHIR resource registered during case transformation."""

    full_url: str
    resource: Any
    sections: set[DischargeSection] = field(default_factory=set)

    @property
    def resource_type(self) -> str:
        """Return the FHIR resource type."""

        return self.resource.get_resource_type()


@dataclass
class StrokeCaseContext:
    """FHIR modeling state associated with one RESQ+ case."""

    case_id: str
    raw: dict[str, Any]

    transaction_entries: list[BundleEntry] = field(default_factory=list)
    resources_by_full_url: dict[str, StrokeCaseResource] = field(
        default_factory=dict
    )

    patient_ref: str | None = None
    encounter_ref: str | None = None
    organization_ref: str | None = None

    def index_transaction_entries(self) -> None:
        """Rebuild the resource index from the transaction entries.

        This method allows the current modeling implementation to continue
        appending BundleEntry objects directly to transaction_entries.

        Once every insertion uses StrokeCaseContext.add_resource(), this
        reindexing step will no longer be necessary.
        """

        self.resources_by_full_url.clear()

        for entry in self.transaction_entries:
            self.register_entry(entry)

    def register_entry(self, entry: BundleEntry) -> StrokeCaseResource:
        """Register an already-created BundleEntry in the case index."""

        if entry.fullUrl is None:
            raise TransformError(
                "Cannot register a FHIR resource without BundleEntry.fullUrl."
            )

        if entry.resource is None:
            raise TransformError(
                f"Bundle entry {entry.fullUrl} does not contain a resource."
            )

        full_url = str(entry.fullUrl)

        if full_url in self.resources_by_full_url:
            raise TransformError(
                f"Duplicate BundleEntry.fullUrl in stroke case: {full_url}"
            )

        record = StrokeCaseResource(
            full_url=full_url,
            resource=entry.resource,
        )

        self.resources_by_full_url[full_url] = record
        return record

    def get_resource(
        self,
        reference: str,
    ) -> StrokeCaseResource | None:
        """Resolve a local fullUrl reference inside the case."""

        return self.resources_by_full_url.get(reference)

    def require_resource(
        self,
        reference: str,
    ) -> StrokeCaseResource:
        """Resolve a local reference or fail with a clear error."""

        record = self.get_resource(reference)

        if record is None:
            raise TransformError(
                f"FHIR resource not found in stroke case: {reference}"
            )

        return record

    @property
    def resources(self) -> tuple[StrokeCaseResource, ...]:
        """Return registered resources in transaction-entry order."""

        records: list[StrokeCaseResource] = []

        for entry in self.transaction_entries:
            if entry.fullUrl is None:
                continue

            record = self.resources_by_full_url.get(str(entry.fullUrl))

            if record is not None:
                records.append(record)

        return tuple(records)