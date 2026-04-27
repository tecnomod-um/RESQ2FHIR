"""
Patient resource builder for FHIR transformation.
"""

from fhir.resources.patient import Patient
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.extension import Extension
from enum_models import Sex
from utils import  TransformError


def build_Patient(patient_id: str, patient_sex= None) -> Patient:
    """
    Build a FHIR Patient resource from raw data.
    
    Args:
        patient_id: Unique patient identifier
        patient_sex: Patient's sex
        
    Returns:
        Patient resource
    """
    patient = Patient()
    patient.id = str(patient_id)
    extension_list = []

    # Gender (optional)
    if patient_sex is not None:
        try:
            if patient_sex == Sex.MALE:
                sex = Sex.MALE.to_coding()
            elif patient_sex == Sex.FEMALE:
                sex = Sex.FEMALE.to_coding()
            elif patient_sex == Sex.OTHER:
                sex = Sex.OTHER.to_coding()
            else:
                raise ValueError(f"Invalid 'sex' value '{patient_sex}'. Expected 'MALE' or 'FEMALE' or 'OTHER'.")
  
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/gender-snomed-ext",
                valueCodeableConcept=CodeableConcept(coding=[sex])
            ))
        except Exception as e:
            raise TransformError(
                f"Invalid 'sex' value '{patient_sex}'. Expected a valid Sex. Underlying error: {e}"
            )
    
    if extension_list:
        patient.extension = extension_list
    
    return patient
