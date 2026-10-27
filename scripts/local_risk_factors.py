"""Locally governed RES-Q risk-factor concepts not represented precisely in SNOMED CT."""

from __future__ import annotations

from dataclasses import dataclass

from fhir.resources.coding import Coding


STROKE_RISK_FACTOR_CODE_SYSTEM = (
    "http://qualityregistry.org/CodeSystem/risk-factor-cs"
)


@dataclass(frozen=True)
class LocalRiskFactorConcept:
    """Small concept wrapper compatible with the existing risk-factor builders."""

    id: str
    code: str
    display: str
    system: str = STROKE_RISK_FACTOR_CODE_SYSTEM

    def to_coding(self) -> Coding:
        return Coding(system=self.system, code=self.code, display=self.display)


SMOKING_LAST_10_YEARS = LocalRiskFactorConcept(
    id="SmokingLast10Years",
    code="smoking-last-10-years",
    display="Smoking within the last 10 years",
)
