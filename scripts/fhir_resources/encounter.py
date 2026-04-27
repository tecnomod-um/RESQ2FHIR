"""
Encounter resource builder for FHIR transformation.
"""

from fhir.resources.encounter import Encounter, EncounterAdmission
from fhir.resources.reference import Reference
from fhir.resources.coding import Coding
from fhir.resources.fhirtypes import MetaType 
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.extension import Extension
from fhir.resources.period import Period
from scripts.enum_models import ArrivalMode, DischargeDestination, DischargeFacilityDepartment, Locations
from scripts.fhir_resources.location import build_location, build_hospitalized_location
from scripts.helpers import get_encounter_class
from utils import parse_datetime


def build_stroke_encounter_profile(
    patient_ref: str,
    arrival_mode: ArrivalMode | None, 
    discharge_destination: DischargeDestination | None = None,
    discharge_facility_department: DischargeFacilityDepartment | None = None,
    discharge_facility_type: DischargeFacilityDepartment | None = None,
    admission_department: Locations | None = None,
    first_contact_place: Locations | None = None,
    inhospital_stroke: bool | None = None,
    hospitalized_in: Locations | None = None,
    hospital_timestamp: str | None = None,
    discharge_date: str | None = None,
    first_hospital: bool = False,
    post_acute_care: bool = False,
    ems_prenotification: bool = False,
) -> Encounter:    
    """
    Build a FHIR Encounter resource for stroke care.
    
    Args:
        patient_ref: Reference to the Patient resource
        arrival_mode: The mode of arrival for the patient (e.g., ambulance, walk-in)
        discharge_destination: The destination of the patient after discharge (e.g., home, rehabilitation facility)
        discharge_facility_department: The department of the facility where the patient was discharged to (e.g., neurology, general medicine)
        discharge_facility_type: The type of facility where the patient was discharged to (e.g., hospital, nursing home)
        admission_department: The department of the hospital where the patient was admitted (e.g., emergency department, neurology)
        first_contact_place: The place of first contact for the patient (e.g., pre-hospital, emergency department)
        inhospital_stroke: Boolean indicating if stroke occurred in-hospital
        hospitalized_in: The hospital where the patient was hospitalized
        hospital_timestamp: Timestamp of hospital admission
        discharge_date: Date of discharge from hospital
        first_hospital: Boolean indicating if this is the first hospital the patient was admitted to for this stroke event
        post_acute_care: Boolean indicating if post-acute care is required for the patient after discharge
        ems_prenotification: Boolean indicating if EMS prenotification was done for the patient before arrival at the hospital
        
    Returns:
        Encounter resource for stroke care 
    """
    encounter = Encounter(status="completed", subject=Reference(reference=patient_ref))
    encounter.meta = MetaType(profile=["http://tecnomod-um.org/StructureDefinition/stroke-encounter-profile"])

    # Obtain discharge destination and arrival mode
    
    
    # Build admission section based on available data
    if discharge_destination is not None and arrival_mode is not None:
        encounter.admission = EncounterAdmission(admitSource=CodeableConcept(coding=[arrival_mode.to_coding()]), dischargeDisposition=CodeableConcept(coding=[discharge_destination.to_coding()]))
    elif arrival_mode is None and discharge_destination is not None:
        encounter.admission = EncounterAdmission(dischargeDisposition=CodeableConcept(coding=[discharge_destination.to_coding()]))
    elif discharge_destination is None and arrival_mode is not None:
        encounter.admission = EncounterAdmission(admitSource=CodeableConcept(coding=[arrival_mode.to_coding()]))

    # Create extensions for hospitalized_in, first_hospital, discharge_facility_department and post_acute_care
    extension_list = []
    location_list = []
    # Set the class of the encounter to inpatient
    if first_contact_place is not None:
        first_location = build_location(first_contact_place)
        location_list.append(first_location)

        encounter_class_code, encounter_class_display = get_encounter_class(first_contact_place)
        if not encounter_class_code is "OTH":
            coding_class = Coding(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code=encounter_class_code,
                display=encounter_class_display
            )
        code_class = CodeableConcept(coding=[coding_class])
        encounter.class_fhir = [code_class]
        
    if hospitalized_in is not None:
        if admission_department is not None:
            # Create hospitalized_in extension
            hosp_loc = build_hospitalized_location(hospitalized_in, admission_department)
            location_list.append(hosp_loc)

    if first_hospital:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/first-hospital-ext",
            valueBoolean=True
        ))
    else:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/first-hospital-ext",
            valueBoolean=False
        ))

    if discharge_facility_department is not None:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/discharge-department-service-ext",
            valueCodeableConcept=CodeableConcept(coding=[discharge_facility_department.to_coding()])
        ))
    elif discharge_facility_type is not None:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/discharge-department-service-ext",
            valueCodeableConcept=CodeableConcept(coding=[discharge_facility_type.to_coding()])
        ))


    if post_acute_care:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/required-post-acute-care-ext",
            valueBoolean=True
        ))
    else:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/required-post-acute-care-ext",
            valueBoolean=False
        ))

    if ems_prenotification:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/ems-prenotification-ext",
                valueBoolean=True
            ))
    else:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/ems-prenotification-ext",
                valueBoolean=False
            ))

    encounter.extension = extension_list

    encounterPeriod = Period()
    if inhospital_stroke is not None :
        if hospital_timestamp is not None:
            encounterPeriod.start = parse_datetime(hospital_timestamp)

    if discharge_date is not None:
        encounterPeriod.end = parse_datetime(discharge_date)


    return encounter
