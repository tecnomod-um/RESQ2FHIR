"""
Utility functions for FHIR transformation.
Contains shared helper functions used across multiple modules.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
import pandas as pd


class TransformError(ValueError):
    """Raised when input data is invalid or inconsistent for FHIR transformation."""
    pass


def safe_get(raw: dict, key: str, *, required: bool = False, ctx: str = ""):
    """Get a value from raw with an optional requirement and nice error if missing."""
    if key in raw and raw[key] is not None:
        return raw[key]
    if required:
        where = f" while {ctx}" if ctx else ""
        raise TransformError(f"Missing required field '{key}'{where}.")
    return None


def safe_get_bool(
    raw: dict,
    key: str,
    *,
    required: bool = False,
    default: bool = False,
    ctx: str = "",
) -> bool:
    """Get a boolean value from raw, accepting common string and numeric forms."""
    value = safe_get(raw, key, required=required, ctx=ctx)
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes", "y", "t"):
            return True
        if normalized in ("false", "0", "no", "n", "f"):
            return False

    raise TransformError(f"Invalid boolean value '{value}' for field '{key}'.")


def by_id_or_error(enum_cls, value, *, field: str, ctx: str = ""):
    """Call Enum.by_id with clear error messages."""
    try:
        return enum_cls.by_id(str(value))
    except Exception as e:
        where = f" while {ctx}" if ctx else ""
        raise TransformError(
            f"Invalid value '{value}' for field '{field}'{where}. "
            f"Expected a valid identifier for {enum_cls.__name__}. Underlying error: {e}"
        )


def ensure_dependency(condition: bool, *, need: str, because: str):
    """Validate that a prerequisite condition is met."""
    if not condition:
        raise TransformError(
            f"Prerequisite missing: {need} is required because {because}."
        )


def safe_isna(x) -> bool:
    """Check if a value is NaN or None."""
    try:
        import pandas as _pd
        return bool(_pd.isna(x))
    except Exception:
        return x is None


def parse_datetime(raw: str, *, tz: str = "Europe/Bratislava") -> datetime:
    """Parse datetime with informative error."""
    if raw is None or str(raw).strip() == "":
        raise TransformError("Datetime value is empty.")
    raw = str(raw).strip()
    tried = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
    last_err = None
    for fmt in tried:
        try:
            dt = datetime.strptime(raw, fmt)
            # If only date, assume midnight
            if fmt == "%Y-%m-%d":
                dt = datetime.combine(dt.date(), datetime.min.time())
                dt = dt.replace(tzinfo=ZoneInfo(tz))
            return dt.astimezone(ZoneInfo("UTC"))
        except Exception as e:
            last_err = e
    raise TransformError(
        f"Invalid datetime '{raw}'. Expected one of formats {tried}. Underlying error: {last_err}"
    )


def get_uuid() -> str:
    """Generate a UUID in FHIR format."""
    return f"urn:uuid:{uuid.uuid4()}"


def get_patient_id() -> str:
    """Generate a patient ID."""
    return f"{uuid.uuid4()}"
