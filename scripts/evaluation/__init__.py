"""Evaluation utilities for RESQ2FHIR transformations."""

from .resource_counts import summarize_resource_counts
from .semantic_preservation_full import evaluate_semantic_preservation


def evaluate_job(*args, **kwargs):
    """Lazily import the combined evaluator to keep ``python -m`` warning-free."""
    from .evaluate import evaluate_job as _evaluate_job

    return _evaluate_job(*args, **kwargs)


__all__ = [
    "evaluate_job",
    "summarize_resource_counts",
    "evaluate_semantic_preservation",
]
