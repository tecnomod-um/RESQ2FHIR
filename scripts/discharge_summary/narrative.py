"""Deterministic XHTML narrative generation for the RESQ discharge document."""

from __future__ import annotations

import html
import re
from collections.abc import Callable, Iterable
from typing import Any

from fhir.resources.composition import CompositionSection
from fhir.resources.narrative import Narrative

from scripts.discharge_summary.ehds_model import