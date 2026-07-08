


from fhir.resources.bodystructure import BodyStructure, BodyStructureIncludedStructure
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference

from scripts.enum_models import BodySites, Laterality



def build_bodyStructure(patient_ref: str, laterality: Laterality, structure: BodySites ) -> BodyStructure:
    """
    Build a FHIR BodyStructure resource for a specific anatomical structure.
    
    Args:
        patient_ref: Reference to the Patient resource
        laterality: Laterality of the structure (e.g., left, right)
        structure: Anatomical structure (e.g., carotid artery, brain)
    Returns:
        BodyStructure resource for the specified anatomical structure
    """
    included_structure = None
    if laterality is not None and structure is not None:
        included_structure = BodyStructureIncludedStructure(
            laterality = CodeableConcept(coding=[laterality.to_coding()]),
            structure = CodeableConcept(coding=[structure.to_coding()])
        )
    if structure is not None and laterality is None:
        included_structure = BodyStructureIncludedStructure(
            structure = CodeableConcept(coding=[structure.to_coding()])
        )
        
    return BodyStructure(
        patient=Reference(reference=patient_ref),
        includedStructure=[included_structure],
    )
