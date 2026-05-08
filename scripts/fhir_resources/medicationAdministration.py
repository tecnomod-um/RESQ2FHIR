


from decimal import Decimal
from fhir.resources.reference import Reference
from fhir.resources.medicationadministration import MedicationAdministration, MedicationAdministrationDosage
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.quantity import Quantity
from fhir.resources.extension import Extension
from fhir.resources.meta import Meta

from scripts.enum_models import DischargeMedication, InsulinOnHyperglycemiaTiming, Medications, Nimodipinetiming, NoAnticoagulantReason, NotMedicationReason, ParacetamolOnFeverTiming, PostAcuteCare, UnitofMeasurement
from scripts.utils import parse_datetime

def build_ivt_medicationAdministration(ivt_drug_dose,ivt_drug, patient_ref, encounter_ref):
    """
    Build a FHIR MedicationAdministration resource for IVT administration.
    
    Args:
        ivt_drug: The drug administered 
        ivt_drug_dose: The dose administered (string)
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        MedicationAdministration resource
    """

    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref))
    
    medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[Medications.by_id(ivt_drug).to_coding()]))

    dosage = MedicationAdministrationDosage(dose=Quantity(value=Decimal(ivt_drug_dose), unit=UnitofMeasurement.MG.display, system=UnitofMeasurement.MG.system, code=UnitofMeasurement.MG.code))
    medicationAdministration.dosage = dosage

    return medicationAdministration

def build_medicationAdministration(patient_ref: str, encounter_ref: str, medication: Medications, medication_timestamp: str | None = None, condition_ref: str | None = None, procedure_ref: str | None = None, observation_ref: str | None = None, dose: int | None = None, medication_post_acute: bool | None = None, medication_range_timing: ParacetamolOnFeverTiming | None = None, no_medication_reason: NotMedicationReason | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource.
    
    Args:
        medication: The medication administered
        medication_timestamp: The timestamp of the medication administration
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource
        observation_ref: Reference to the Observation resource
        condition_ref: Reference to the Condition resource
        dose: The dose administered (integer)
        no_medication_reason: The reason for no medication administration, if applicable
    Returns:
        MedicationAdministration resource 
    """
    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        occurenceDateTime = parse_datetime(medication_timestamp)
        )
    
    medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[medication.to_coding()]))
    reason_list = []
    if condition_ref is not None:
        reason_list.append(CodeableReference(reference=Reference(reference=condition_ref)))
        medicationAdministration.reason = reason_list
    if observation_ref is not None:
        reason_list.append(CodeableReference(reference=Reference(reference=observation_ref)))
        medicationAdministration.reason = reason_list
    if procedure_ref is not None:
        medicationAdministration.partOf = [Reference(reference=procedure_ref)]
    if dose is not None:
        medicationAdministration.dosage = MedicationAdministrationDosage(dose=Quantity(value=Decimal(dose), unit=UnitofMeasurement.MG.display, system=UnitofMeasurement.MG.system, code=UnitofMeasurement.MG.code))
    extension_list = []
    if medication_post_acute is not None:
        if medication_post_acute is True or medication_post_acute is PostAcuteCare.TRUE:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/required-post-acute-care-ext",
                valueBoolean=True
            ))
        elif medication_post_acute is False or medication_post_acute is PostAcuteCare.FALSE:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/required-post-acute-care-ext",
                valueBoolean=False
            ))
        elif medication_post_acute is None:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/required-post-acute-care-ext",
                valueBoolean=False
            ))

    # if medication_timestamp is not None:
    #     medicationAdministration.occurenceDateTime = parse_datetime(medication_timestamp)

    if medication_range_timing is not None:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/assessment-timing-ext",
            valueCode=medication_range_timing
        ))

    if no_medication_reason is not None:
        medicationAdministration.status = "not-done"
        medicationAdministration.statusReason = [CodeableConcept(coding=[no_medication_reason.to_coding()])]
    
    if len(extension_list) > 0:
        medicationAdministration.extension = extension_list  

    return medicationAdministration


def build_medicationAdministration_paracetamol_on_fever(patient_ref:str, encounter_ref:str, fever_ref:str, medication_range_timing: ParacetamolOnFeverTiming | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for paracetamol administration on fever.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        fever_ref: Reference to the fever Observation resource
    Returns:
        MedicationAdministration resource for paracetamol administration on fever
    """
    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/paracetamol-on-fever-medicationAdministration-profile"])
        )
    
    medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[Medications.PARACETAMOL.to_coding()]))
    medicationAdministration.reason = [CodeableReference(reference=Reference(reference=fever_ref))]
    extension_list = []

    if medication_range_timing is not None:
        extension_list.append(Extension(url = "http://tecnomod-um.org/StructureDefinition/assessment-timing-ext", valueCodeableConcept=CodeableConcept(coding=[medication_range_timing.to_coding()])))
        medicationAdministration.extension = extension_list

    # Add extension to link to the fever observation
    return medicationAdministration


def build_no_anticoagulant_reversal_medicationAdministration(patient_ref:str, encounter_ref:str, no_anticoagulant_reversal_reason:NoAnticoagulantReason) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for no anticoagulant reversal administration.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        no_anticoagulant_reversal_reason: The reason for no anticoagulant reversal administration
    Returns:

        MedicationAdministration resource for no anticoagulant reversal administration
    """
    medicationAdministration = MedicationAdministration(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref))
    
    medicationAdministration.statusReason = [CodeableConcept(coding=[no_anticoagulant_reversal_reason.to_coding()])]
    medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[Medications.ANTICOAGULANT_REVERSAL.to_coding()]))
    return medicationAdministration


def build_insulin_on_hyperglycemia(patient_ref:str, encounter_ref:str, observation_ref:str, insulin_timing: InsulinOnHyperglycemiaTiming) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for insulin administration on hyperglycemia.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        observation_ref: Reference to the hyperglycemia observation resource
        insulin_timing: The timing of the insulin administration  (within 1 hour or after 1 hour)
    Returns:
        MedicationAdministration resource for insulin administration on hyperglycemia
    """
    
    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=observation_ref))],
        meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/insulin-on-hyperglycemia-medicationAdministration-profile"])
        )
    
    medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[Medications.INSULIN.to_coding()]))

    extension_list = []
    if insulin_timing is not None:
        extension_list.append(Extension(url = "http://tecnomod-um-org/StructureDefinition/assessment-timing-ext", valueCodeableConcept=CodeableConcept(coding=[insulin_timing.to_coding()])))
        medicationAdministration.extension = extension_list

    return medicationAdministration


def build_no_anticoagulant_discharge_medicationAdministration(patient_ref:str, encounter_ref:str, no_anticoagulant_discharge_reason:NoAnticoagulantReason) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for no anticoagulant discharge administration.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        no_anticoagulant_discharge_reason: The reason for no anticoagulant discharge administration
    Returns:
        MedicationAdministration resource for no anticoagulant discharge administration
    """
    medicationAdministration = MedicationAdministration(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref))
    
    medicationAdministration.statusReason = [CodeableConcept(coding=[no_anticoagulant_discharge_reason.to_coding()])]
    medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[DischargeMedication.ANTICOAGULANT.to_coding()]))
    return medicationAdministration

def build_medicationAdministration_nimopidine(patient_ref:str, encounter_ref:str, condition_ref: str | None = None, procedure_ref:str | None = None, medication_range_timing: Nimodipinetiming | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for nimodipine administration.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource, if applicable
        procedure_ref: Reference to the Procedure resource, if applicable
        medication_range_timing: The timing information for the nimodipine administration, if applicable
    Returns:
        MedicationAdministration resource for nimodipine administration
    """
    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/nimodipine-medicationAdministration-profile"])
        )
    
    medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[Medications.NIMODIPINE.to_coding()]))



    reason_list = []
    if condition_ref is not None:
        reason_list.append(CodeableReference(reference=Reference(reference=condition_ref)))
        medicationAdministration.reason = reason_list
    if procedure_ref is not None:
        medicationAdministration.partOf = [Reference(reference=procedure_ref)]


    extension_list = []
    if medication_range_timing is not None:
        extension_list.append(Extension(url = "http://tecnomod-um-org/StructureDefinition/assessment-timing-ext", valueCodeableConcept=CodeableConcept(coding=[medication_range_timing.to_coding()])))
        medicationAdministration.extension = extension_list
    return medicationAdministration