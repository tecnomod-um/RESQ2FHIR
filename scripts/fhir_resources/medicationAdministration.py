


from datetime import timedelta
from decimal import Decimal
from fhir.resources.reference import Reference
from fhir.resources.medicationadministration import MedicationAdministration, MedicationAdministrationDosage
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.quantity import Quantity
from fhir.resources.extension import Extension
from fhir.resources.meta import Meta
from fhir.resources.coding import Coding
from fhir.resources.timing import Timing
from fhir.resources.period import Period
from scripts.enum_models import AnticoagulantReversal, InsulinOnHyperglycemiaTiming, IvtDrug, Medications, Nimodipinetiming, NoAnticoagulantReversalReason, NotMedicationReason, ParacetamolOnFeverTiming, PostAcuteCare, UnitofMeasurement
from scripts.utils import parse_datetime


def _coerce_relative_timing(relative_timing):
    if relative_timing is not None and not hasattr(relative_timing, "to_coding"):
        for enum_cls in (ParacetamolOnFeverTiming, InsulinOnHyperglycemiaTiming, Nimodipinetiming):
            try:
                return enum_cls.by_id(str(relative_timing))
            except Exception:
                continue
    return relative_timing


def _relative_occurrence_timing(relative_timing) -> Timing:
    relative_timing = _coerce_relative_timing(relative_timing)
    if relative_timing is not None:
        return Timing(code=CodeableConcept(coding=[relative_timing.to_coding()]))

    return Timing(code=CodeableConcept(coding=[Coding(
        system="http://terminology.hl7.org/CodeSystem/data-absent-reason",
        code="unknown",
        display="Unknown"
    )]))



def build_medicationAdministration(patient_ref: str, encounter_ref: str, medication: Medications | IvtDrug | str, medication_timestamp: str | None = None, condition_ref: str | None = None, procedure_ref: str | None = None, observation_ref: str | None = None, dose: int | None = None, medication_post_acute: bool | None = None, medication_range_timing: ParacetamolOnFeverTiming | None = None, no_medication_reason: NotMedicationReason | None = None, reference_time: str | None = None) -> MedicationAdministration:
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

    if isinstance(medication,Medications):
        med = CodeableReference(concept=CodeableConcept(coding=[medication.to_coding()]))
    elif isinstance(medication,IvtDrug):
        med = CodeableReference(concept=CodeableConcept(coding=[medication.to_coding()]))
    elif medication:
        med = CodeableReference(reference=Reference(reference=medication))
    
    if medication_timestamp is None and reference_time is not None:
        ref_timestamp = parse_datetime(reference_time)
        if ref_timestamp is not None:
            timestamp_offsetted = ref_timestamp + timedelta(hours=24)
            if medication_range_timing == Nimodipinetiming.WITHIN_24_HOURS:
                period = Period(start=ref_timestamp, end=timestamp_offsetted)
            else:
                period = Period(start=timestamp_offsetted)
            medicationAdministration = MedicationAdministration(
                status="completed",
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                occurencePeriod=period,
                medication=med
                )


    if medication_timestamp is not None:
        medicationAdministration = MedicationAdministration(
            status="completed",
            subject=Reference(reference=patient_ref),
            encounter=Reference(reference=encounter_ref),
            occurenceDateTime = parse_datetime(medication_timestamp),
            medication=med
            )
    


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


    if medication_range_timing is not None:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/assessment-timing-ext",
            valueCodeableConcept=medication_range_timing
        ))

    if no_medication_reason is not None:
        medicationAdministration.status = "not-done"
        medicationAdministration.statusReason = [CodeableConcept(coding=[no_medication_reason.to_coding()])]
    
    if len(extension_list) > 0:
        medicationAdministration.extension = extension_list  

    return medicationAdministration


def build_medicationAdministration_paracetamol_on_fever(patient_ref:str, encounter_ref:str, fever_ref:str, reference_time : str , medication_range_timing: ParacetamolOnFeverTiming | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for paracetamol administration on fever.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        fever_ref: Reference to the fever Observation resource
    Returns:
        MedicationAdministration resource for paracetamol administration on fever
    """

    
    ref_timestamp = parse_datetime(reference_time)
    if ref_timestamp is not None:
        timestamp_offsetted = ref_timestamp + timedelta(hours=1)
        if medication_range_timing == ParacetamolOnFeverTiming.WITHIN_1_HOURS:
            period = Period(start=ref_timestamp, end=timestamp_offsetted)
        else:
            period = Period(start=timestamp_offsetted)
    
    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/paracetamol-on-fever-medication-administration-profile"]),
        medication = CodeableReference(concept=CodeableConcept(coding=[Medications.PARACETAMOL.to_coding()])),
        occurencePeriod=period
        )
    medicationAdministration.reason = [CodeableReference(reference=Reference(reference=fever_ref))]
    extension_list = []

    if medication_range_timing is not None:
        extension_list.append(Extension(url = "http://tecnomod-um.org/StructureDefinition/assessment-timing-ext", valueCodeableConcept=CodeableConcept(coding=[medication_range_timing.to_coding()])))
        medicationAdministration.extension = extension_list

    # Add extension to link to the fever observation
    return medicationAdministration


def build_insulin_on_hyperglycemia(patient_ref:str, encounter_ref:str, observation_ref:str, initial_reference_time: str, insulin_timing: InsulinOnHyperglycemiaTiming, final_reference_time: str | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for insulin administration on hyperglycemia.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        observation_ref: Reference to the hyperglycemia observation resource
        initial_reference_time: The initial reference time for the insulin administration
        final_reference_time: The final reference time for the insulin administration
        insulin_timing: The timing of the insulin administration  (within 1 hour or after 1 hour)
    Returns:
        MedicationAdministration resource for insulin administration on hyperglycemia
    """
    if initial_reference_time is not None:
        initial_timestamp = parse_datetime(initial_reference_time)
        timestamp_offsetted = initial_timestamp + timedelta(hours=1)
        if insulin_timing == InsulinOnHyperglycemiaTiming.WITHIN_1_HOUR:
            period = Period(start=initial_timestamp, end=timestamp_offsetted)
        elif insulin_timing == InsulinOnHyperglycemiaTiming.AFTER_1_HOUR:
            if final_reference_time is not None:
                final_ref_timestamp = parse_datetime(final_reference_time)
                period = Period(start=timestamp_offsetted, end=final_ref_timestamp)
        else:
            period = Period(start=timestamp_offsetted)

    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=observation_ref))],
        meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/insulin-on-hyperglycemia-medication-administration-profile"]),
        medication = CodeableReference(concept=CodeableConcept(coding=[Medications.INSULIN.to_coding()])),
        occurencePeriod=period,
        )
    

    extension_list = []
    if insulin_timing is not None:
        extension_list.append(Extension(url = "http://tecnomod-um.org/StructureDefinition/assessment-timing-ext", valueCodeableConcept=CodeableConcept(coding=[insulin_timing.to_coding()])))
        medicationAdministration.extension = extension_list

    return medicationAdministration


def build_medicationAdministration_nimopidine(patient_ref:str, encounter_ref:str, initial_reference_time: str | None = None, final_reference_time: str | None = None, condition_ref: str | None = None, procedure_ref:str | None = None, medication_range_timing: Nimodipinetiming | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for nimodipine administration.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource, if applicable
        procedure_ref: Reference to the Procedure resource, if applicable
        initial_reference_time: The initial reference time for the nimodipine administration
        final_reference_time: The final reference time for the nimodipine administration
        medication_range_timing: The timing information for the nimodipine administration, if applicable
    Returns:
        MedicationAdministration resource for nimodipine administration
    """

    
    if initial_reference_time is not None:
        initial_ref_timestamp = parse_datetime(initial_reference_time)
        timestamp_offsetted = initial_ref_timestamp + timedelta(hours=24)
        if medication_range_timing == Nimodipinetiming.WITHIN_24_HOURS:
            period = Period(start=initial_ref_timestamp, end=timestamp_offsetted)
        if medication_range_timing == Nimodipinetiming.AFTER_24_HOURS:
            if final_reference_time is not None:
                final_ref_timestamp = parse_datetime(final_reference_time)
                period = Period(start=timestamp_offsetted, end=final_ref_timestamp)
        elif final_reference_time is not None:
            final_ref_timestamp = parse_datetime(final_reference_time)
            period = Period(start=timestamp_offsetted, end=final_ref_timestamp)
        else:
            period = Period(start=timestamp_offsetted)

    medicationAdministration = MedicationAdministration(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/nimodipine-medication-administration-profile"]),
        medication=CodeableReference(concept=CodeableConcept(coding=[Medications.NIMODIPINE.to_coding()])),
        occurencePeriod=period
        )


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


def build_medicationAdministration_anticoagulantReversal(patient_ref:str, encounter_ref:str, condition_ref: str | None, medication: AnticoagulantReversal, medication_timestamp:str | None = None, initial_reference_time: str | None = None, final_reference_time: str | None = None,no_medication_reason: NoAnticoagulantReversalReason | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for anticoagulant reversal medication administration.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        medication: The anticoagulant reversal medication administered
        medication_timestamp: The timestamp of the medication administration
        no_medication_reason: The reason for no medication administration, if applicable
    Returns:
        MedicationAdministration resource for anticoagulant reversal medication administration
    """

    occurrence = {}
    if medication_timestamp is not None:
        occurrence["occurenceDateTime"] = parse_datetime(medication_timestamp)
    elif initial_reference_time is not None:
        start = parse_datetime(initial_reference_time)
        end = parse_datetime(final_reference_time) if final_reference_time is not None else None
        occurrence["occurencePeriod"] = Period(start=start, end=end)
    else:
        raise ValueError("Anticoagulant reversal requires a medication timestamp or reference period.")

    medicationAdministration = MedicationAdministration(
        status="completed",
        meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/anticoagulant-reversal-medication-administration-profile"]),
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        medication=CodeableReference(concept=CodeableConcept(coding=[medication.to_coding()])),
        **occurrence,
        )
    
    reason_list = []
    if condition_ref is not None:
        reason_list.append(CodeableReference(reference=Reference(reference=condition_ref)))
        medicationAdministration.reason = reason_list

    if no_medication_reason is not None:
        medicationAdministration.status = "not-done"
        medicationAdministration.statusReason = [CodeableConcept(coding=[no_medication_reason.to_coding()])]
        medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[Medications.ANTICOAGULANT_REVERSAL.to_coding()]))

    return medicationAdministration


def build_medicationAdministration_anticoagulantReversal(patient_ref:str, encounter_ref:str, condition_ref: str | None, medication: AnticoagulantReversal, medication_timestamp:str | None = None, initial_reference_time: str | None = None, final_reference_time: str | None = None,no_medication_reason: NoAnticoagulantReversalReason | None = None) -> MedicationAdministration:
    """
    Build a FHIR MedicationAdministration resource for anticoagulant reversal medication administration.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        medication: The anticoagulant reversal medication administered
        medication_timestamp: The timestamp of the medication administration
        no_medication_reason: The reason for no medication administration, if applicable
    Returns:
        MedicationAdministration resource for anticoagulant reversal medication administration
    """



    medicationAdministration = MedicationAdministration(
        status="completed",
        meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/anticoagulant-reversal-medication-administration-profile"]),
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        medication=CodeableReference(concept=CodeableConcept(coding=[medication.to_coding()]))
        )
    
    reason_list = []
    if condition_ref is not None:
        reason_list.append(CodeableReference(reference=Reference(reference=condition_ref)))
        medicationAdministration.reason = reason_list

    if medication_timestamp is not None:
        medication_timestamp_parsed = parse_datetime(medication_timestamp)
        medicationAdministration.occurenceDateTime = medication_timestamp_parsed
    else:
        if initial_reference_time is not None:
            initial_ref_timestamp = parse_datetime(initial_reference_time)
            if final_reference_time is not None:
                final_ref_timestamp = parse_datetime(final_reference_time)
                period = Period(start=initial_ref_timestamp, end=final_ref_timestamp)
            else:
                period = Period(start=initial_ref_timestamp)
            medicationAdministration.occurencePeriod = period


    if no_medication_reason is not None:
        medicationAdministration.status = "not-done"
        medicationAdministration.statusReason = [CodeableConcept(coding=[no_medication_reason.to_coding()])]
        medicationAdministration.medication = CodeableReference(concept=CodeableConcept(coding=[Medications.ANTICOAGULANT_REVERSAL.to_coding()]))

    return medicationAdministration