
from scripts.enum_models import PractitionerRoles
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.practitionerrole import PractitionerRole

def build_practitioner(practitioner_type: PractitionerRoles) -> PractitionerRole:
    """
    Build a FHIR Practitioner resource.
    
    Args:
        practitioner_type: The type of practitioner (e.g., doctor, nurse)
    Returns:
        Practitioner resource
    """
    practitionerRole = PractitionerRole()
    practitionerRole.code = [CodeableConcept(coding=[practitioner_type.to_coding()])]
    return practitionerRole