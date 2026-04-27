

from scripts.enum_models import ConceptEnum
from fhir.resources.communication import Communication, CommunicationPayload
from fhir.resources.reference import Reference

def build_three_m_contact(patient_ref: str, encounter_ref: str, contact_date: None, contact_mode: None) -> Communication:

    if contact_mode is None or contact_mode == ContactModes.NO_CONTACT:
        communication = Communication(status="not-done")
        return communication
    else:
        communication = Communication(status="completed")
        communication.medium = [contact_mode.to_coding()]
        communication.subject = Reference(reference=patient_ref)
        communication.encounter = Reference(reference=encounter_ref)
        if contact_date is not None:
            communication.sent = contact_date
        
        return communication