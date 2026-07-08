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

from collections.abc import Iterable
from typing import Any

from fhir.resources.bundle import BundleEntry, BundleEntryRequest

from scripts.discharge_summary.sections import SECTION_DEFINITIONS
from scripts.enum_models import DischargeSection
from scripts.utils import TransformError, get_uuid


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


    def _validate_sections(self,resource: Any,sections: Iterable[DischargeSection],) -> set[DischargeSection]:
        """Validate that a resource type is permitted in every assigned section."""

        resource_type = resource.get_resource_type()
        normalized_sections = set(sections)

        for section in normalized_sections:
            definition = SECTION_DEFINITIONS.get(section)

            if definition is None:
                raise TransformError(
                    f"Unknown discharge-summary section: {section}"
                )

            if resource_type not in definition.entry_types:
                allowed = ", ".join(
                    sorted(definition.entry_types)
                )

                raise TransformError(
                    f"FHIR resource type {resource_type} cannot be added to "
                    f"section '{definition.title}'. "
                    f"Allowed resource types: {allowed}."
                )

        return normalized_sections
    
    def index_transaction_entries(self) -> None:
        """Rebuild the resource index without losing section assignments.

        Resources added through add_resource() are already indexed and may already
        contain discharge-summary section assignments. Legacy resources still
        appended directly to transaction_entries are indexed here with no section.
        """

        preserved_sections = {
            full_url: set(record.sections)
            for full_url, record in self.resources_by_full_url.items()
        }

        self.resources_by_full_url.clear()

        for entry in self.transaction_entries:
            if entry.fullUrl is None:
                raise TransformError(
                    "Cannot index a FHIR resource without BundleEntry.fullUrl."
                )

            full_url = str(entry.fullUrl)

            self.register_entry(
                entry,
                sections=preserved_sections.get(
                    full_url,
                    (),
                ),
            )

    def register_entry(self, entry: BundleEntry, sections: Iterable[DischargeSection] = ()) -> StrokeCaseResource:
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

        validated_sections = self._validate_sections(
            entry.resource,
            sections,
        )

        record = StrokeCaseResource(
            full_url=full_url,
            resource=entry.resource,
            sections=validated_sections,
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

    def add_resource(
        self,
        resource: Any,
        *,
        full_url: str | None = None,
        sections: Iterable[DischargeSection] = (),
    ) -> str:
        """Add and register one resource in the transaction Bundle.

        The returned fullUrl can be used immediately by subsequent resources.
        Document sections are optional because some resources are document-header
        resources or transitive dependencies rather than direct section entries.
        """

        if resource is None:
            raise TransformError(
                "Cannot add an empty FHIR resource to the stroke case."
            )

        full_url = full_url or get_uuid()
        resource_type = resource.get_resource_type()

        if full_url in self.resources_by_full_url:
            raise TransformError(
                f"Duplicate BundleEntry.fullUrl in stroke case: {full_url}"
            )

        if any(
            entry.fullUrl is not None
            and str(entry.fullUrl) == full_url
            for entry in self.transaction_entries
        ):
            raise TransformError(
                f"Duplicate BundleEntry.fullUrl in stroke case: {full_url}"
            )

        validated_sections = self._validate_sections(
            resource,
            sections,
        )

        entry = BundleEntry(
            fullUrl=full_url,
            resource=resource,
            request=BundleEntryRequest(
                method="POST",
                url=resource_type,
            ),
        )

        self.transaction_entries.append(entry)

        self.resources_by_full_url[full_url] = StrokeCaseResource(
            full_url=full_url,
            resource=resource,
            sections=validated_sections,
        )

        return full_url
    
    def resources_for_section(
        self,
        section: DischargeSection,
    ) -> tuple[StrokeCaseResource, ...]:
        """Return section resources in transaction-entry order."""

        return tuple(
            record
            for record in self.resources
            if section in record.sections
        )
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