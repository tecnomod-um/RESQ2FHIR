
from fhir.resources.appointment import Appointment, AppointmentParticipant
from fhir.resources.reference import Reference
from fhir.resources.codeableconcept import CodeableConcept

from scripts.enum_models import ConceptEnum, Locations, AppointmentSituation

def build_follow_up_appointment(patient_ref: str, management_appointment: AppointmentSituation | None) -> Appointment:

    appointment = Appointment(status="proposed")
    
    if management_appointment == AppointmentSituation.SCHEDULED: 
        appointment.status = "booked"
    elif management_appointment == AppointmentSituation.NOT_RECOMMENDED:
        appointment.status = "cancelled"
    
    appointment.participant = [AppointmentParticipant(actor = Reference(reference=patient_ref))]
    appointment.specialty = [CodeableConcept(coding=[Locations.NEUROLOGY.to_coding()])]
    return appointment

