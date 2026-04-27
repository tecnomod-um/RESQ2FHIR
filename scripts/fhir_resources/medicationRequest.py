"""
MedicationRequest resource builder for FHIR transformation.
Represents medications prescribed at discharge.
"""

from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.reference import Reference
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.fhirtypes import MetaType


def build_on_discharge_medicationRequest_profile(on_discharge_meds: list, patient_ref: str, encounter_ref: str):
    """
    Build FHIR MedicationRequest resources for medications prescribed at discharge.
    
    Creates MedicationRequest entries for all medications to be continued or started at discharge.
    All requests are marked as 'active' with intent 'order' and location 'community'.
    
    Args:
        on_discharge_meds: List of medications prescribed at discharge
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        
    Returns:
        List of MedicationRequest resources
        
    Profile: http://tecnomod-um.org/StructureDefinition/discharge-medication-request-profile
    Status: active
    Intent: order
    Category: Community
    """
    #get_on_discharge_medications(raw)
    final_medication_lists = []
    
    # Category coding for community setting
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/medicationrequest-admin-location",
        code="community",
        display="Community"
    )
    category_code = CodeableConcept(coding=[category_coding])

    # Create a MedicationRequest for each discharge medication
    for odm in on_discharge_meds:
        coding_bom = Coding(
            system=odm.system,
            code=odm.code,
            display=odm.display
        )
        code_bom = CodeableConcept(coding=[coding_bom])
        code_med_bom = CodeableReference(concept=code_bom)

        medication_request = MedicationRequest(
            status="active",
            intent="order",
            category=[category_code],
            subject=Reference(reference=patient_ref),
            encounter=Reference(reference=encounter_ref),
            medication=code_med_bom,
            meta=MetaType(profile =["http://tecnomod-um.org/StructureDefinition/discharge-medication-request-profile"])
        )
        final_medication_lists.append(medication_request)
    
    return final_medication_lists
