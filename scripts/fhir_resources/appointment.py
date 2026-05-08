
from fhir.resources.appointment import Appointment, AppointmentParticipant
from fhir.resources.reference import Reference
from fhir.resources.codeableconcept import CodeableConcept

from scripts.enum_models import Locations, ManagementAppointment

def build_follow_up_appointment(patient_ref: str, management_appointment: ManagementAppointment) -> Appointment:

    appointment = Appointment(status="proposed", participant=[AppointmentParticipant(actor=Reference(reference=patient_ref), status="tentative")])
    if management_appointment == ManagementAppointment.SCHEDULED: 
        appointment.status = "booked"
        appointment.participant[0].status = "accepted"
    elif management_appointment == ManagementAppointment.NOT_RECOMMENDED:
        appointment.status = "cancelled"
        appointment.participant[0].status = "declined"
    
    appointment.specialty = [CodeableConcept(coding=[Locations.NEUROLOGY.to_coding()])]
    return appointment

