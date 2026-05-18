"""
MedicationStatement resource builder for FHIR transformation.
Represents medications taken before stroke onset.
"""

from fhir.resources.medicationstatement import MedicationStatement, MedicationStatementAdherence
from fhir.resources.reference import Reference
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from scripts.enum_models import AdherenceCodes
from fhir.resources.meta import Meta


def build_before_onset_medicationStatement_profile(medications_list: list, patient_ref: str, encounter_ref: str):
    """
    Build FHIR MedicationStatement resources for medications taken before stroke onset.
    
    Creates separate MedicationStatement entries for each medication, grouped by adherence status:
    - Taking: Medications the patient was taking
    - Not Taking: Medications explicitly not taken
    - Unknown: Medications with unknown status
    
    Args:
        medications_list: List of medication data dictionaries containing medication information and adherence status
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        
    Returns:
        List of MedicationStatement resources
        
    Profile: http://tecnomod-um.org/StructureDefinition/prior-medication-statement-profile
    """

    final_medication_lists = []

    for status_key, meds in medications_list:
        # Get adherence code for the status
        adherence_code = AdherenceCodes.by_id(status_key)
        adherence_coding = Coding(
            system=adherence_code.system,
            code=adherence_code.code,
            display=adherence_code.display
        )
        adherence_codeable = CodeableConcept(coding=[adherence_coding])

        # Create a MedicationStatement for each medication in this status group
        for bom in meds:
            coding_bom = Coding(
                system=bom.system,
                code=bom.code,
                display=bom.display
            )
            code_bom = CodeableConcept(coding=[coding_bom])
            code_med_bom = CodeableReference(concept=code_bom)

            medication_statement = MedicationStatement(
                status="recorded",
                subject=Reference(reference=patient_ref),
                medication=code_med_bom,
                encounter=Reference(reference=encounter_ref),
                adherence=MedicationStatementAdherence(code=adherence_codeable),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/prior-medication-statement-profile"])
            )
            final_medication_lists.append(medication_statement)
    
    return final_medication_lists
