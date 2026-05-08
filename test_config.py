"""
Test configuration and utilities for RESQ2FHIR.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_sample_row() -> Dict[str, Any]:
    """Load a sample data row for testing."""
    return {
        "case_id": "test-case-001",
        "hospital_name": "Demo Hospital",
        "sex": "male",
        "age": 75,
        "arrival_mode_id": "ems-home",
        "admission_department": "neurology",
        "first_contact_place": "emergency",
        "hospitalized_in": "same hospital",
        "systolic_pressure": 145,
        "diastolic_pressure": 85,
        "glucose": 110,
        "cholesterol": 220,
        "nihss_score": 8,
        "stroke_type": "ischemic",
    }


def validate_bundle_json(bundle_path: Path) -> bool:
    """Basic validation of a generated bundle JSON file."""
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
        
        # Check basic structure
        assert bundle.get("resourceType") == "Bundle", "Not a Bundle"
        assert bundle.get("type") == "transaction", "Not a transaction Bundle"
        assert "entry" in bundle, "No entries in Bundle"
        assert len(bundle["entry"]) > 0, "Empty Bundle"
        
        # Check for Patient, Encounter, Organization
        resource_types = {e["resource"]["resourceType"] for e in bundle["entry"]}
        assert "Patient" in resource_types, "No Patient resource"
        assert "Encounter" in resource_types, "No Encounter resource"
        assert "Organization" in resource_types, "No Organization resource"
        
        return True
    except (json.JSONDecodeError, KeyError, AssertionError) as e:
        print(f"Bundle validation failed: {e}")
        return False
