"""
Patient resource builder for FHIR transformation.
"""

from fhir.resources.patient import Patient
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.identifier import Identifier
from fhir.resources.extension import Extension
from scripts.enum_models import Sex
from scripts.utils import TransformError


def build_Patient(patient_id: str, patient_sex: Sex | None) -> Patient:
    """
    Build a FHIR Patient resource from raw data.
    
    Args:
        patient_id: Unique patient identifier
        patient_sex: Patient's sex
        
    Returns:
        Patient resource
    """
    patient = Patient()
    patient.identifier = [Identifier(value=str(patient_id))]
    extension_list = []

    # Gender (optional)
    if patient_sex is not None:
        try:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/gender-snomed-ext",
                valueCodeableConcept=CodeableConcept(coding=[patient_sex.to_coding()])
            ))
        except Exception as e:
            raise TransformError(
                f"Invalid 'sex' value '{patient_sex}'. Expected a valid Sex. Underlying error: {e}"
            )
    
    if extension_list:
        patient.extension = extension_list
    
    return patient
