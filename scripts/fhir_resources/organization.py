"""
Organization resource builder for FHIR transformation.
"""

from fhir.resources.organization import Organization
from fhir.resources.identifier import Identifier
from scripts.provider_map import mapping as provider_mapping


def get_org_id(hospital_name: str):
    """
    Map hospital name to organization ID using provider mapping.
    
    Args:
        hospital_name: Name of the hospital
        
    Returns:
        Organization ID from provider mapping
        
    Raises:
        ValueError: If hospital name not found in mapping
    """
    if hospital_name is None or hospital_name.strip() == "":
        raise ValueError("Hospital name is required to map to organization ID")
    
    normalized_name = hospital_name.strip().replace(" ", "-")
    if normalized_name not in [key.strip().replace(" ", "-") for key in provider_mapping.keys()]:
        raise ValueError(f"Hospital name '{hospital_name}' not found in provider mapping")
    
    for key in provider_mapping.keys():
        if normalized_name == key.strip().replace(" ", "-"):
            return provider_mapping[key]


def build_organization(hospital_name: str, provider_id: str | int | None = None) -> Organization:
    """
    Build a FHIR Organization resource from raw data.
    
    Args:
        hospital_name: Name of the hospital
        provider_id: Source registry organization identifier, when available
        
    Returns:
        Organization resource
    """
    org = Organization()
    org.active = True

    mapped_org_id = provider_id if provider_id not in (None, "") else get_org_id(hospital_name.strip().replace(" ", "-"))

    valueConceptOrg = Identifier(
        system="https://stroke.qualityregistry.org",
        value=str(mapped_org_id)
    )

    org.identifier = [valueConceptOrg]
    org.name = hospital_name.strip().replace(" ", "-")
    
    return org
