"""
Observation resource builders for FHIR transformation.
"""

from decimal import Decimal

from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.reference import Reference
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.range import Range
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.extension import Extension
from scripts.enum_models import (
    AnaliticsCodes, AtrialFibrillationOrFlutter, BodySites, CarotidStenosisLevel, GCSScore, GlasgowComaScale, HemorrhagicTransformationType, INRmode, Laterality, ManagementAppointment, NotMedicationReason, ObservationMethods, ProcedureNotDoneReason, TiaClinicalSymptoms, ThreeMonthContactMode, VitalSigns, MRsScore,
    AssessmentContext, FunctionalScore, MTiciScore, SpecificFinding, UnitofMeasurement, TimingMetricCodes, TiaSymptomDuration
)
from fhir.resources.meta import Meta 
from scripts.utils import TransformError, parse_datetime


def build_observation_vital_signs(systolic_pressure: int | None, diastolic_pressure: int | None, patient_ref: str, encounter_ref: str, timing: AssessmentContext | None) -> Observation:
    """
    Build a FHIR Observation resource for vital signs (blood pressure).
    
    Args:
        systolic_pressure: Systolic blood pressure value
        diastolic_pressure: Diastolic blood pressure value
        raw: Raw observation data dictionary
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        
    Returns:
        Observation resource for vital signs
    """
    observation = Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/vital-sign-observation-profile"]),
        code=CodeableConcept(coding=[VitalSigns.TAKE_VS.to_coding()]),
    )

    component_list = []

    if systolic_pressure is not None:
        component_systolic = ObservationComponent(
            code= CodeableConcept(coding=[VitalSigns.SYSTOLIC.to_coding()]),
            valueQuantity= Quantity(
                value=Decimal(str(systolic_pressure)),
                unit=UnitofMeasurement.MMGM.display,
                system=UnitofMeasurement.MMGM.system,
                code=UnitofMeasurement.MMGM.code
            )
        )  
        component_list.append(component_systolic)

    if diastolic_pressure is not None:
        component_diastolic = ObservationComponent(
            code=CodeableConcept(coding=[VitalSigns.DIASTOLIC.to_coding()]),
            valueQuantity= Quantity(
                value=Decimal(str(diastolic_pressure)),
                unit=UnitofMeasurement.MMGM.display,
                system=UnitofMeasurement.MMGM.system,
            code=UnitofMeasurement.MMGM.code
            )
        )
        component_list.append(component_diastolic)

    if component_list is not []:
        observation.component = component_list

    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="vital-signs",
        display="Vital Signs"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]

    if timing is not None:
        assessment_value = timing.to_coding()
        assessment_code = CodeableConcept(coding=[assessment_value])
        extension = Extension(
                url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
                valueCodeableConcept=assessment_code
            )
        extension_list = [extension]
        observation.extension = extension_list

    return observation
    



def build_observation_mrs(patient_ref: str, encounter_ref: str, mrs_score: MRsScore | None, prestroke: bool | None = False , discharge: bool | None = False , threem: bool | None = False) -> Observation:
    """
    Build a FHIR Observation resource for mRS (modified Rankin Scale) score.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        mrs_score: The mRS score value coded as MRsScore enum
        prestroke: If True, use prestroke_mrs value
        discharge: If True, use discharge_mrs value
        threem: If True, use three_m_mrs value
        
    Returns:
        Observation resource for mRS score
    """
    if prestroke is True:
        assessment_value = AssessmentContext.PRESTROKE.to_coding()
    elif discharge is True:
        assessment_value = AssessmentContext.DISCHARGE.to_coding()
    elif threem is True:
        assessment_value = AssessmentContext.THREE_MONTHS.to_coding()

    assessment_code = CodeableConcept(coding=[assessment_value])
    extensions = Extension(
        url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
        valueCodeableConcept=assessment_code
    )
    
    coding_mrs = FunctionalScore.MRS.to_coding()
    code_mrs = CodeableConcept(coding=[coding_mrs])
    
    coding_category = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    code_category = CodeableConcept(coding=[coding_category])

    if mrs_score is not None:
        code_value_mrs = CodeableConcept(coding=[mrs_score.to_coding()])
    
    return Observation(
        status="final",
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"]),
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=code_mrs,
        valueCodeableConcept=code_value_mrs,
        category=[code_category],
        extension=[extensions],
    )


def build_observation_nihss(patient_ref: str, encounter_ref: str, value_nihss: int | None, admission_nihss: bool | None = False, discharge_nihss: bool | None = False) -> Observation:
    """
    Build a FHIR Observation resource for NIHSS (National Institutes of Health Stroke Scale) score.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        value_nihss: The NIHSS score value
        admission_nihss: If True, use nihss_score value (admission)
        discharge_nihss: If True, use discharge_nihss_score value
        
    Returns:
        Observation resource for NIHSS score
    """
    if admission_nihss is True:
        assesment_value = AssessmentContext.ADMISSION.to_coding()

    elif discharge_nihss is True:
        assesment_value = AssessmentContext.DISCHARGE.to_coding()
    else:
        raise TransformError("NIHSS observation requires admission or discharge context.")
    
    extensions = Extension(
        url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[assesment_value])
    )
 
    code_nihss = CodeableConcept(coding=[FunctionalScore.NIHSS.to_coding()])
    
    coding_category = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    code_category = CodeableConcept(coding=[coding_category])


    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"]),
        code=code_nihss,
        valueInteger=value_nihss,
        category=[code_category],
        extension=[extensions],
    )


def build_observation_mtici_score(mtici_score: MTiciScore, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for mTICI (modified Thrombolysis In Cerebral Infarction) score.
    
    Args:
        mtici_score: The mTICI score
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        
    Returns:
        Observation resource for mTICI score
    """
    specific_finding_coding = SpecificFinding.MTICI.to_coding()
    code_mtici = CodeableConcept(coding=[specific_finding_coding])

    coding_category = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="procedure",
        display="Procedure"
    )
    code_category = CodeableConcept(coding=[coding_category])

    code_value_mtici = CodeableConcept(coding=[mtici_score.to_coding()])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"]),
        code=code_mtici,
        valueCodeableConcept=code_value_mtici,
        category=[code_category],
        encounter=Reference(reference=encounter_ref)
    )


def build_observation_blood_volume(patient_ref: str, encounter_ref: str, bleeding_volume: int , post_acute_care: bool |None = None) -> Observation:
    """
    Build a FHIR Observation resource for bleeding volume in hemorrhagic stroke.
    
    Args:
        bleeding_volume: Volume of bleeding in milliliters
        post_acute_care: Whether the observation is for post-acute care
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        
    Returns:
        Observation resource for bleeding volume
    """
    observation = Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"]),
        code=CodeableConcept(coding=[SpecificFinding.BLOOD_VOLUME.to_coding()])
    )
    coding_category = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    code_category = CodeableConcept(coding=[coding_category])
    observation.category = [code_category]
    extension_list = []
    if post_acute_care is not None:
        acute_extension = Extension(
                url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
                valueBoolean=post_acute_care
            )
        
        extension_list.append(acute_extension)


    value_quantity = Quantity(
            value=Decimal(bleeding_volume),
            unit=UnitofMeasurement.ML.display,
            system=UnitofMeasurement.ML.system,
            code=UnitofMeasurement.ML.code
        )
    observation.valueQuantity = value_quantity

    observation.extension = extension_list
    return observation

def build_observation_carotid_stenosis(patient_ref: str, encounter_ref: str, carotid_stenosis_level: CarotidStenosisLevel | None,  carotid_stenosis: bool | None = False) -> Observation:
    """
    Build a FHIR Observation resource for carotid stenosis.
    
    Args:
        carotid_stenosis: Whether carotid stenosis is present
        carotid_stenosis_level: Level of carotid stenosis (e.g., "50-69%", "70-99%")
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for carotid stenosis
    """
    obs =  Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"]),
        encounter=Reference(reference=encounter_ref),
        code = CodeableConcept(coding=[SpecificFinding.CAROTID_STENOSIS.to_coding()])
    )


    coding_category = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    obs.category = [CodeableConcept(coding=[coding_category])]


    if carotid_stenosis is False:
        obs.valueBoolean = False
    elif carotid_stenosis is True:
        if carotid_stenosis_level is not None:
            obs.valueCodeableConcept = CodeableConcept(
                coding=[carotid_stenosis_level.to_coding()]
            )
        else:
            obs.valueBoolean = True

    return obs


  
def build_observation_occluded_artery(patient_ref: str, encounter_ref: str, body_structure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for a specific occluded artery.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        body_site: The specific body site (artery) that is occluded, coded as BodySites enum
    Returns:
        Observation resource for the occluded artery
    """
    specific_finding_coding = SpecificFinding.ARTERY_OCCLUSION.to_coding()
    code_occluded_artery = CodeableConcept(coding=[specific_finding_coding])

    coding_category = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    code_category = CodeableConcept(coding=[coding_category])

    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"]),
        code=code_occluded_artery,
        category=[code_category],
        valueBoolean=True,
        encounter=Reference(reference=encounter_ref),
        bodyStructure=Reference(reference=body_structure_ref)
    )

def build_observation_Af_or_F(patient_ref: str, encounter_ref: str, atrial_fibrillation_or_flutter: AtrialFibrillationOrFlutter, hospital_timestamp:str |None = None) -> Observation:
    """
    Build a FHIR Observation resource for Atrial Fibrillation/Flutter.
    
    Args:
        raw: Raw observation data dictionary
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        atrial_fibrillation_or_flutter: Atrial Fibrillation or Flutter value (ConceptEnum)
        hospital_timestamp: Timestamp of the hospital visit
        
    Returns:
        Observation resource for AF/Flutter
    """
 

    observation = Observation(
        code=CodeableConcept(coding=[SpecificFinding.ATRIAL_FIBRILLATION_FLUTTER.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"])

    category = CodeableConcept(coding=[Coding(
        code="laboratory",
        display="Laboratory",
        system="http://terminology.hl7.org/CodeSystem/observation-category"
    )])

    observation.valueCodeableConcept = CodeableConcept(coding=[atrial_fibrillation_or_flutter.to_coding()])
    observation.category = [category]

    if hospital_timestamp is not None:
        observation.effectiveDateTime = parse_datetime(str(hospital_timestamp))
    
    return observation


# def build_observation_smoking(raw: dict, patient_ref: str, encounter_ref: str) -> Observation:
#     """
#     Build a FHIR Observation resource for smoking status.
    
#     Args:
#         raw: Raw observation data dictionary
#         patient_ref: Reference to the Patient resource
#         encounter_ref: Reference to the Encounter resource
        
#     Returns:
#         Observation resource for smoking status
#     """

#     if not safe_isna(raw.get("risk_smoker")):
#         risk_smoker = raw.get("risk_smoker")
#         if risk_smoker is True:
#             smoker_status = RiskFactor.Smoker
#         elif risk_smoker is False:
#             if not safe_isna(raw.get("risk_smoker_last_10_years")):
#                 risk_smoker_10_years = raw.get("risk_smoker_last_10_years")
#                 if risk_smoker_10_years is True:
#                     smoker_status = RiskFactor.Ex_Smoker
#             else:
#                     smoker_status = RiskFactor.Non_Smoker
#         smoker_coding = Coding(
#             code=smoker_status.code,
#             system=smoker_status.system,
#             display=smoker_status.display
#         )

#         code_smoker = CodeableConcept(coding=[smoker_coding])
    
#     return Observation(
#         status="final",
#         subject=Reference(reference=patient_ref),
#         meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/base-stroke-observation"]),
#         code=code_smoker,
#         encounter=Reference(reference=encounter_ref),
#     )


# def build_stroke_circumstance_observation(patient_ref: str, encounter_ref: str, condition_ref: str, wake_up: bool = False, in_hosp: bool = False) -> Observation:
#     """
#     Build a FHIR Observation resource for stroke circumstance (wake-up stroke or in-hospital stroke).
    
#     Args:
#         patient_ref: Reference to the Patient resource
#         encounter_ref: Reference to the Encounter resource
#         condition_ref: Reference to the Condition resource
#         wake_up: If True, marks as wake-up stroke
#         in_hosp: If True, marks as in-hospital stroke
        
#     Returns:
#         Observation resource for stroke circumstance
#     """
#     if wake_up:
#         circumstance = StrokeCircumstance.WAKE_UP
#     elif in_hosp:
#         circumstance = StrokeCircumstance.IN_HOSPITAL
    
#     circumstance_coding = Coding(
#         code=circumstance.code,
#         system=circumstance.system,
#         display=circumstance.display
#     )
#     code_circumstance = CodeableConcept(coding=[circumstance_coding])
    
#     return Observation(
#         status="final",
#         subject=Reference(reference=patient_ref),
#         meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-circumstance-observation-profile"]),
#         code=code_circumstance,
#         encounter=Reference(reference=encounter_ref),
#     )

def build_no_anticoagulant_discharge_medication(patient_ref:str, encounter_ref:str, no_anticoagulant_discharge_reason:NotMedicationReason) -> Observation:
    """
    Build a FHIR Observation resource for no anticoagulant discharge.
     
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        no_anticoagulant_discharge_reason: The reason for no anticoagulant discharge 
    Returns:
        Observation resource for no anticoagulant discharge 
    """
    observation = Observation(
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/no-anticoagulant-discharge-reason-observation-profile"]),
        code=CodeableConcept(coding=[ObservationMethods.NO_ANTICOAGULATION.to_coding()]),
        valueCodeableConcept=CodeableConcept(coding=[no_anticoagulant_discharge_reason.to_coding()]),
        status="final"
    )
    return observation
                  
def build_observation_age(age: int | None, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for patient age.
    
    Args:
        age: Patient age at stroke onset
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        
    Returns:
        Observation resource for age
    """
    obs = Observation(
        code=CodeableConcept(coding=[(FunctionalScore.AGE.to_coding())]),
        status="final",
        valueInteger=int(age) if age is not None else None
    )
    obs.subject = Reference(reference=patient_ref)
    obs.encounter = Reference(reference=encounter_ref)

    return obs


def build_timing_d2n_observation(door_to_needle_time: int, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-needle time.
    
    Args:
        door_to_needle_time: Time from hospital arrival to thrombolysis administration in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombolysis administration
    Returns:
        Observation resource for door-to-needle time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_NEEDLE.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_needle_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=procedure_ref)]
    )

def build_timing_d2n_le45_observation(door_to_needle_le45: bool, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-needle time ≤ 45 minutes.
    
    Args:
        door_to_needle_le45: Whether door-to-needle time is less than or equal to 45 minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombolysis administration
    Returns:
        Observation resource for door-to-needle time ≤ 45 minutes
    """
    timing_obj = TimingMetricCodes.DOOR_TO_NEEDLE_LE45.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueBoolean=door_to_needle_le45,
        partOf=[Reference(reference=procedure_ref)]
    )

def build_timing_d2n_le60_observation(door_to_needle_le60: bool, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-needle time ≤ 60 minutes.
    
    Args:
        door_to_needle_le60: Whether door-to-needle time is less than or equal to 60 minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombolysis administration
    Returns:
        Observation resource for door-to-needle time ≤ 60 minutes
    """
    timing_obj = TimingMetricCodes.DOOR_TO_NEEDLE_LE60.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueBoolean=door_to_needle_le60,
        partOf=[Reference(reference=procedure_ref)]
    )

def build_timing_door_to_ich_evacuation_observation(door_to_ich_evacuation_time: int, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-ICH evacuation time.
    
    Args:
        door_to_ich_evacuation_time: Time from hospital arrival to ICH evacuation in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for ICH evacuation
    Returns:
        Observation resource for door-to-ICH evacuation time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_ICH_EVACUATION.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_ich_evacuation_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=procedure_ref)]
    )


def build_timing_door_to_imaging_observation(door_to_imaging_time: int, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-imaging time.
    
    Args:
        door_to_imaging_time: Time from hospital arrival to brain imaging in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for brain imaging
    Returns:
        Observation resource for door-to-imaging time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_IMAGING.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_imaging_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=procedure_ref)]
    )

def build_timing_door_to_iv_antihypertensive_observation(door_to_iv_antihypertensive_time: int, patient_ref: str, encounter_ref: str, medicationAdministration_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-IV antihypertensive time.
    
    Args:
        door_to_iv_antihypertensive_time: Time from hospital arrival to IV antihypertensive administration in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        medicationAdministration_ref: Reference to the MedicationAdministration resource for IV antihypertensive administration
    Returns:
        Observation resource for door-to-IV antihypertensive time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_IV_ANTIHYPERTENSIVE.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_iv_antihypertensive_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=medicationAdministration_ref)]
    )

def build_door_to_reperfusion_observation(door_to_reperfusion_time: int, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-reperfusion time.
    
    Args:
        door_to_reperfusion_time: Time from hospital arrival to reperfusion (thrombolysis or thrombectomy) in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for reperfusion
    Returns:
        Observation resource for door-to-reperfusion time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_REPERFUSION.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_reperfusion_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=procedure_ref)]
    )

def build_door_to_sys_bp_lt140_observation(door_to_sys_bp_lt140_time: int, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-systolic blood pressure < 140 mmHg time.
    
    Args:
        door_to_sys_bp_lt140_time: Time from hospital arrival to reduce the systolic blood pressure < 140 mmHg in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for door-to-systolic blood pressure < 140 mmHg time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_SYS_BP_LT140.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_sys_bp_lt140_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
    )

def build_onset_to_door_observation(onset_to_door_time: int, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for onset-to-door time.
    
    Args:
        onset_to_door_time: Time from stroke symptom onset to hospital arrival in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for onset-to-door time
    """
    timing_obj = TimingMetricCodes.ONSET_TO_DOOR.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(onset_to_door_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        )
    )

def build_highest_systolic_pressure_after24h_observation(highest_systolic_pressure_after24h: int, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for highest systolic blood pressure after 24 hours.
    
    Args:
        highest_systolic_pressure_after24h: Highest systolic blood pressure after 24 hours in mmHg
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for highest systolic blood pressure after 24 hours
    """
    timing_obj = VitalSigns.SYSTOLIC.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    extension = Extension(
        url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.POST_ACUTE.to_coding()])
    )
    extension_list = [extension]
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(highest_systolic_pressure_after24h),
            unit=UnitofMeasurement.MMGM.display,
            system=UnitofMeasurement.MMGM.system,
            code=UnitofMeasurement.MMGM.code
        ),
        extension=extension_list
    )

def build_systolic_pressure_lt140_observation(patient_ref: str, encounter_ref: str, systolic_pressure_lt140:bool, systolic_pressure_lt140_timestamp = None) -> Observation:
    """
    Build a FHIR Observation resource for systolic blood pressure < 140 mmHg.
    
    Args:
        systolic_pressure_lt140: Whether systolic blood pressure is < 140 mmHg
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for systolic blood pressure < 140 mmHg
    """
    timing_obj = VitalSigns.SYS_BP_LT140.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueBoolean=systolic_pressure_lt140,
        effectiveDateTime=parse_datetime(str(systolic_pressure_lt140_timestamp)) if systolic_pressure_lt140_timestamp is not None else None
    )

def build_timing_d2g_observation(door_to_groin_time: int, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-groin time.
    
    Args:
        door_to_groin_time: Time from hospital arrival to groin puncture in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombectomy
    Returns:
        Observation resource for door-to-groin time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_GROIN.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_groin_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=procedure_ref)]
    )

def build_timing_d2g_le90_observation(door_to_groin_le90: bool, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-groin time ≤ 90 minutes.
    
    Args:
        door_to_groin_le90: Whether door-to-groin time is less than or equal to 90 minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombectomy
    Returns:
        Observation resource for door-to-groin time ≤ 90 minutes
    """
    timing_obj = TimingMetricCodes.DOOR_TO_GROIN_LE90.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueBoolean=door_to_groin_le90,
        partOf=[Reference(reference=procedure_ref)]
    )

def build_door_to_anticoagulant_reversal_observation(door_to_anticoagulant_reversal_time: int, patient_ref: str, encounter_ref: str, medicationAdministration_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-anticoagulant reversal time.
    
    Args:
        door_to_anticoagulant_reversal_time: Time from hospital arrival to anticoagulant reversal in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        medicationAdministration_ref: Reference to the MedicationAdministration resource
    Returns:
        Observation resource for door-to-anticoagulant reversal time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_ANTICOAGULANT_REVERSAL.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity=Quantity(
            value=Decimal(door_to_anticoagulant_reversal_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=medicationAdministration_ref)]
    )

def build_timing_d2g_le120_observation(door_to_groin_le120: bool, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-groin time ≤ 120 minutes.
    
    Args:
        door_to_groin_le120: Whether door-to-groin time is less than or equal to 120 minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombectomy
    Returns:
        Observation resource for door-to-groin time ≤ 120 minutes
    """
    timing_obj = TimingMetricCodes.DOOR_TO_GROIN_LE120.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueBoolean=door_to_groin_le120,
        partOf=[Reference(reference=procedure_ref)]
    )

def build_observation_three_month_contact_mode(three_month_contact_mode: ThreeMonthContactMode, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for 3 months contact mode.
    
    Args:
        three_month_contact_mode: Mode of contact at 3 months (e.g., in-person, phone, telehealth)
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for 3 months contact mode
    """
    contact_mode_coding = three_month_contact_mode.to_coding()
    code_contact_mode = CodeableConcept(coding=[contact_mode_coding])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/three-month-contact-mode-observation-profile"]),
        code=code_contact_mode,
    )

def build_timing_discharge_to_three_months_contact_observation(discharge_to_three_months_contact: int, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for discharge to 3 months contact time.
    
    Args:
        discharge_to_three_months_contact: Time from hospital discharge to 3 months contact in days
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for discharge to 3 months contact time
    """

    timing_obj = TimingMetricCodes.DISCHARGE_TO_THREE_MONTHS_CONTACT.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(discharge_to_three_months_contact),
            unit=UnitofMeasurement.DAY.display,
            system=UnitofMeasurement.DAY.system,
            code=UnitofMeasurement.DAY.code
        )
    )

def build_door_to_discharge_observation(door_to_discharge_time: int, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-discharge time.
    
    Args:
        door_to_discharge_time: Time from hospital arrival to discharge in days
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for door-to-discharge time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_DISCHARGE.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_discharge_time),
            unit=UnitofMeasurement.DAY.display,
            system=UnitofMeasurement.DAY.system,
            code=UnitofMeasurement.DAY.code
        )
    )

def build_door_to_door_observation(door_to_door_time: int, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for door-to-door time.
    
    Args:
        door_to_door_time: Time from hospital arrival to door-to-door in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombectomy
    Returns:
        Observation resource for door-to-door time
    """
    timing_obj = TimingMetricCodes.DOOR_TO_DOOR.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(door_to_door_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=procedure_ref)]
    )

def build_groin_to_reperfusion_observation(groin_to_reperfusion_time: int, patient_ref: str, encounter_ref: str, procedure_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for groin-to-reperfusion time.
    
    Args:
        groin_to_reperfusion_time: Time from groin puncture to reperfusion in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        procedure_ref: Reference to the Procedure resource for thrombectomy
    Returns:
        Observation resource for groin-to-reperfusion time
    """
    timing_obj = TimingMetricCodes.GROIN_TO_REPERFUSION.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])
    
    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity= Quantity(
            value=Decimal(groin_to_reperfusion_time),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=procedure_ref)]
    )



def build_observation_glucose(glucose: float | None, patient_ref: str, encounter_ref: str, timing: AssessmentContext | None = None) -> Observation:

    """
    Build a FHIR Observation resource for blood glucose level.
    
    Args:
        glucose: Blood glucose level
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    """
    
    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/analytics-observation-profile"])
    glucose_coding = AnaliticsCodes.GLUCOSE.to_coding()
    code_glucose = CodeableConcept(coding=[glucose_coding])
    observation.code = code_glucose
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]
    observation.valueQuantity = Quantity(
        value=Decimal(str(glucose)),
        unit=UnitofMeasurement.MMOL_L.display,
        system=UnitofMeasurement.MMOL_L.system,
        code=UnitofMeasurement.MMOL_L.code
    )

    extension_list = []
    ext = Extension(
        url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[timing.to_coding()]) if timing is not None else None
    )
    extension_list.append(ext)
    observation.extension = extension_list
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation


def build_iv_antihypertensive_to_sys_bp_lt140_observation(iv_antihypertensive_to_sys_bp_lt140_time: int, patient_ref: str, encounter_ref: str, medicationAdministration_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for IV antihypertensive to systolic blood pressure < 140 mmHg time.
    
    Args:
        iv_antihypertensive_to_sys_bp_lt140_time: Time from IV antihypertensive administration to reduce the systolic blood pressure < 140 mmHg in minutes
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        medicationAdministration_ref: Reference to the MedicationAdministration resource for IV antihypertensive administration
    Returns:
        Observation resource for IV antihypertensive to systolic blood pressure < 140 mmHg time
    """

    timing_obj = TimingMetricCodes.IV_ANTIHYPERTENSIVE_TO_SYS_BP_LT140.to_coding()
    code_timing = CodeableConcept(coding=[timing_obj])

    return Observation(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/timing-metric-observation-profile"]),
        code=code_timing,
        valueQuantity=Quantity(
            value=Decimal(str(iv_antihypertensive_to_sys_bp_lt140_time)),
            unit=UnitofMeasurement.MINUTE.display,
            system=UnitofMeasurement.MINUTE.system,
            code=UnitofMeasurement.MINUTE.code
        ),
        partOf=[Reference(reference=medicationAdministration_ref)]
    )

def build_observation_cholesterol(cholesterol: float, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for cholesterol level.
    
    Args:
        cholesterol: Cholesterol level
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    """
    
    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/analytics-observation-profile"])
    cholesterol_coding = AnaliticsCodes.CHOLESTEROL.to_coding()
    code_cholesterol = CodeableConcept(coding=[cholesterol_coding])
    observation.code = code_cholesterol
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]
    observation.valueQuantity = Quantity(
        value=Decimal(str(cholesterol)),
        unit=UnitofMeasurement.MMOL_L.display,
        system=UnitofMeasurement.MMOL_L.system,
        code=UnitofMeasurement.MMOL_L.code
    )

    extension_list = []
    ext = Extension(
        url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.ADMISSION.to_coding()])
    )
    extension_list.append(ext)
    observation.extension = extension_list
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation

def build_observation_glasgow_coma_scale_score(patient_ref: str, encounter_ref: str,gcs_score: int) -> Observation:
    """
    Build a FHIR Observation resource for Glasgow Coma Scale score.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        gcs_score: Glasgow Coma Scale score
    Returns:
        Observation resource for Glasgow Coma Scale score
    """
    observation = Observation(
        code=CodeableConcept(),
        status="final")
    

    gcs_coding = GlasgowComaScale.GCScore.to_coding()
    code_gcs = CodeableConcept(coding=[gcs_coding])
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/glasgow-coma-score-observation-profile"])
    observation.code = code_gcs
    observation.category = [category_code]
    observation.valueInteger = gcs_score
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation

def build_observation_glasgow_coma_scale_level(patient_ref: str, encounter_ref: str, gcs_obs_ref: str, gcs_level: GCSScore) -> Observation:
    """
    Build a FHIR Observation resource for Glasgow Coma Scale level.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        gcs_obs_ref: Reference to the Glasgow Coma Scale score observation
        gcs_level: Glasgow Coma Scale level (e.g., mild, moderate, severe)
    Returns:
        Observation resource for Glasgow Coma Scale level
    """
    observation = Observation(
        code=CodeableConcept(),
        status="final")
    

    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/glasgow-coma-scale-observation-profile"])
    observation.code = CodeableConcept(coding=[GlasgowComaScale.GCS.to_coding()])
    observation.category = [category_code]
    observation.valueCodeableConcept = CodeableConcept(coding=[gcs_level.to_coding()])
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)
    observation.derivedFrom = [Reference(reference=gcs_obs_ref)]

    return observation

def build_observation_inr(patient_ref: str, encounter_ref: str, inr_value: int | None, inr_mode: str | None) -> Observation:
    """
    Build a FHIR Observation resource for INR (International Normalized Ratio) value.
    
    Args:
        inr_value: INR value
        inr_mode: Mode of INR measurement (e.g., "point_of_care", "lab")
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for INR value
    """

    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )
    inr_coding = AnaliticsCodes.INR.to_coding()
    code_inr = CodeableConcept(coding=[inr_coding])
    observation.code = code_inr
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]
    

    extension_list = []
    timing_ext = Extension(
            url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext",
            valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.ADMISSION.to_coding()])
        )
    extension_list.append(timing_ext)

    if inr_mode is not None:
        if inr_mode == "not done" or inr_mode == "":
            observation.dataAbsentReason = CodeableConcept(coding=[ProcedureNotDoneReason.NOT_DONE.to_coding()])
        else:

            observation.valueInteger = inr_value
            observation.method = CodeableConcept(coding=[INRmode.by_id(inr_mode).to_coding()])

    observation.extension = extension_list
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation


def build_observation_perfusion(perfusion_found:bool, patient_ref: str, encounter_ref: str, perfusion_anterior : bool | None, perfusion_posterior : bool | None, perfusion_carotid: bool | None = None, perfusion_volume: int | None = None, hypoperfusion_volume: int | None = None) -> Observation:
    """
    Build a FHIR Observation resource for perfusion imaging finding.
    
    Args:
        perfusion_found: Boolean indicating if perfusion abnormality was found
        perfusion_anterior: Boolean indicating if anterior perfusion abnormality was found
        perfusion_posterior: Boolean indicating if posterior perfusion abnormality was found
        perfusion_carotid: Boolean indicating if carotid perfusion abnormality was found
        perfusion_volume: Volume of perfusion abnormality in mL
        hypoperfusion_volume: Volume of hypoperfusion in mL
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for perfusion imaging finding
    """
    observation = Observation(
        status="final",
        code = CodeableConcept(coding=[SpecificFinding.PERFUSION.to_coding()]),
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="procedure",
        display="Procedure"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]

    if perfusion_anterior:
        observation.bodySite = CodeableConcept(coding=[BodySites.ANTERIOR.to_coding()])
    elif perfusion_posterior:
        observation.bodySite = CodeableConcept(coding=[Laterality.POSTERIOR.to_coding()])
    elif perfusion_carotid:
        observation.bodySite = CodeableConcept(coding=[BodySites.CAROTID.to_coding()])

    observation.valueBoolean = perfusion_found

    observation.component = []

    observation_core_volume = ObservationComponent(
        code=CodeableConcept(coding=[SpecificFinding.PERFUSION_VOLUME.to_coding()]),
        valueQuantity=Quantity(value=Decimal(perfusion_volume) if perfusion_volume is not None else None, unit=UnitofMeasurement.ML.display, system=UnitofMeasurement.ML.system, code=UnitofMeasurement.ML.code)
    )
    observation.component.append(observation_core_volume)

    observation_hypoperfusion_volume = ObservationComponent(
        code=CodeableConcept(coding=[SpecificFinding.HYPOPERFUSION_VOLUME.to_coding()]),
        valueQuantity=Quantity(value=Decimal(hypoperfusion_volume) if hypoperfusion_volume is not None else None, unit=UnitofMeasurement.ML.display, system=UnitofMeasurement.ML.system, code=UnitofMeasurement.ML.code)
    )
    observation.component.append(observation_hypoperfusion_volume)

    return observation           


def build_observation_old_infarcts_brainstem(patient_ref: str, encounter_ref: str, old_infarcts_any: bool, old_infarcts_brainstem: bool, old_infarcts_cortical: bool, old_infarcts_subcortical: bool) -> list[Observation]:
    """
    Build a FHIR Observation resource for presence of old infarcts on imaging.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        old_infarcts_any: Boolean indicating presence of any old infarcts
        old_infarcts_brainstem: Boolean indicating presence of old infarct brainstem
        old_infarcts_cortical: Boolean indicating presence of old infarct cortical
        old_infarcts_subcortical: Boolean indicating presence of old infarct subcortical

    Returns:
        Observation resource for old infarcts brainstem
    """
    observation_brainstem = Observation(
        status="final",
        code = CodeableConcept(coding=[SpecificFinding.OLD_INFARCT.to_coding()]),
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        bodySite=CodeableConcept(coding=[BodySites.BRAIN_STEM.to_coding()]),
        valueBoolean=old_infarcts_brainstem
    )

    observation_cortical = Observation(
        status="final",
        code = CodeableConcept(coding=[SpecificFinding.OLD_INFARCT.to_coding()]),
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        bodySite=CodeableConcept(coding=[BodySites.CORTICAL.to_coding()]),
        valueBoolean=old_infarcts_cortical
    )

    observation_subcortical = Observation(
        status="final",
        code = CodeableConcept(coding=[SpecificFinding.OLD_INFARCT.to_coding()]),
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        bodySite=CodeableConcept(coding=[BodySites.SUBCORTICAL.to_coding()]),
        valueBoolean=old_infarcts_subcortical
    )

    return [observation_brainstem, observation_cortical, observation_subcortical]
    

def build_observation_aspect_score(patient_ref: str, encounter_ref: str, aspect_score: int) -> Observation:
    """
    Build a FHIR Observation resource for ASPECTS (Alberta Stroke Program Early CT Score).
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        aspect_score: ASPECTS score

    Returns:
        Observation resource for ASPECTS score
    """
    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )
    aspect_coding = FunctionalScore.ASPECT.to_coding()
    code_aspect = CodeableConcept(coding=[aspect_coding])
    observation.code = code_aspect
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]
    observation.valueInteger = aspect_score
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"])
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation


def build_observation_ich_score (ich_score: int, patient_ref: str, encounter_ref: str) -> Observation:
    """
    Build a FHIR Observation resource for ICH (Intracerebral Hemorrhage) score.
    
    Args:
        ich_score: ICH score
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Observation resource for ICH score
    """
    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )
    ich_coding = FunctionalScore.ICH_SCORE.to_coding()
    code_ich = CodeableConcept(coding=[ich_coding])
    observation.code = code_ich
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]
    observation.valueInteger = ich_score
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"])
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation

def build_observation_hunt_hess_score(patient_ref: str, encounter_ref: str,hunt_hess_score: int) -> Observation:
    """
    Build a FHIR Observation resource for Hunt and Hess score.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        hunt_hess_score: Hunt and Hess score
    Returns:
        Observation resource for Hunt and Hess score
    """
    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )
    hunt_hess_coding = FunctionalScore.HUNT_HESS.to_coding()
    code_hunt_hess = CodeableConcept(coding=[hunt_hess_coding])
    observation.code = code_hunt_hess
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]
    observation.valueInteger = hunt_hess_score
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"])
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation


def build_tia_clinical_symptomps_observation(patient_ref: str, encounter_ref: str, tia_symptom: TiaClinicalSymptoms, tia_duration: TiaSymptomDuration | None) -> Observation:
    """
    Build a FHIR Observation resource for TIA (Transient Ischemic Attack) clinical symptoms.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        symptoms: List of clinical symptoms observed in TIA
        tia_duration: Duration of the TIA episode
    Returns:
        Observation resource for TIA clinical symptoms
    """

    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )

    code_tia_symptom = CodeableConcept(coding=[tia_symptom.to_coding()])
    observation.code = code_tia_symptom
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]

    if tia_duration == TiaSymptomDuration.LT_10_MINUTES:
        observation.valueQuantity = Quantity(value=Decimal(10),comparator="<", unit=UnitofMeasurement.MINUTE.display, system=UnitofMeasurement.MINUTE.system, code=UnitofMeasurement.MINUTE.code)
    elif tia_duration == TiaSymptomDuration.BETWEEN_10_AND_60_MINUTES:
        observation.valueRange = Range(low=Quantity(value=Decimal(10), unit=UnitofMeasurement.MINUTE.display, system=UnitofMeasurement.MINUTE.system, code=UnitofMeasurement.MINUTE.code), high=Quantity(value=Decimal(59), unit=UnitofMeasurement.MINUTE.display, system=UnitofMeasurement.MINUTE.system, code=UnitofMeasurement.MINUTE.code))
    elif tia_duration == TiaSymptomDuration.GT_60_MINUTES:
        observation.valueQuantity = Quantity(value=Decimal(60),comparator=">=", unit=UnitofMeasurement.MINUTE.display, system=UnitofMeasurement.MINUTE.system, code=UnitofMeasurement.MINUTE.code)

    #observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/tia-clinical-symptoms-observation-profile"])
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)

    return observation


def build_observation_patient_ventilated(patient_ref: str, encounter_ref: str, ventilated: bool = False) -> Observation:
    """
    Build a FHIR Observation resource for patient ventilation status.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        ventilated: Boolean indicating if the patient was ventilated
    Returns:
        Observation resource for patient ventilation status
    """ 
    observation = Observation(
        code=CodeableConcept(),
        status="final"
    )

    ventilation_coding = ObservationMethods.VENTILATED.to_coding()
    code_ventilation = CodeableConcept(coding=[ventilation_coding])
    observation.code = code_ventilation
    category_coding = Coding(
        system="http://terminology.hl7.org/CodeSystem/observation-category",
        code="exam",
        display="Exam"
    )
    category_code = CodeableConcept(coding=[category_coding])
    observation.category = [category_code]

    observation.valueBoolean = ventilated

    #observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/patient-ventilated-observation-profile"])
    observation.subject = Reference(reference=patient_ref)
    observation.encounter = Reference(reference=encounter_ref)
    extension_list = []
    extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/required-post-acute-care-ext",
                valueBoolean=True
            ))


    return observation


def build_observation_finding_post_ivt_mt(patient_ref: str, encounter_ref: str,post_treatment_findings_any: bool, post_treatment_brain_infarct: bool, post_treatment_remote_bleeding: bool, post_treatment_hemorrhagic_transformation:bool, hemorrhagic_transformation_type : HemorrhagicTransformationType | None = None) -> list[Observation]:
    """
    Build FHIR Observation resources for findings after IVT/MT treatment.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        post_treatment_findings_any: Boolean indicating if any post-treatment finding was observed
        post_treatment_brain_infarct: Boolean indicating if post-treatment brain infarct was observed
        post_treatment_remote_bleeding: Boolean indicating if post-treatment remote bleeding was observed
        hemorrhagic_transformation_type: Type of hemorrhagic transformation observed (if any)
    Returns:
        Tuple of Observation resources for post-treatment findings
    """

    observation_brain_infarct = Observation(
        code=CodeableConcept(coding=[SpecificFinding.BRAIN_INFARCT.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"])
    )

    observation_remote_bleeding = Observation(
        code=CodeableConcept(coding=[SpecificFinding.INTRACRANIAL_HEMORRHAGE.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"])
    )

    observation_hemorrhagic_transformation = Observation(
        code=CodeableConcept(coding=[SpecificFinding.HEMORRHAGIC_TRANSFORMATION.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/specific-finding-observation-profile"])
    )


    if post_treatment_findings_any is False:
        observation_brain_infarct.valueBoolean = False
        observation_remote_bleeding.valueBoolean = False
        observation_hemorrhagic_transformation.valueBoolean = False
    else:
        observation_brain_infarct.valueBoolean = post_treatment_brain_infarct
        observation_remote_bleeding.valueBoolean = post_treatment_remote_bleeding
        observation_hemorrhagic_transformation.valueBoolean = post_treatment_hemorrhagic_transformation
        if post_treatment_hemorrhagic_transformation:
            if hemorrhagic_transformation_type is not None:
                observation_hemorrhagic_transformation.valueCodeableConcept = CodeableConcept(
                    coding=[hemorrhagic_transformation_type.to_coding()]
                )
            else:
                observation_hemorrhagic_transformation.valueBoolean = True
        else:
            observation_hemorrhagic_transformation.valueBoolean = False
    return [observation_brain_infarct, observation_remote_bleeding, observation_hemorrhagic_transformation]


def build_observation_temp_checks(patient_ref: str, encounter_ref: str, day_1_fever: int | None, day_2_fever: int | None, day_3_fever: int | None) -> list[Observation]:
    """
    Build FHIR Observation resources for daily temperature checks.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        day_1_fever: Temperature measurements on day 1
        day_2_fever: Temperature measurements on day 2
        day_3_fever: Temperature measurements on day 3
    Returns:
        List of Observation resources for daily temperature checks
    """
    observations = []
    if day_1_fever is not None:
        observation_day_1 = Observation(
            code=CodeableConcept(coding=[TimingMetricCodes.FEVER_DAY_1.to_coding()]),
            status="final",
            valueInteger=day_1_fever,
            subject=Reference(reference=patient_ref),
            encounter=Reference(reference=encounter_ref)
        )
        observations.append(observation_day_1)
    if day_2_fever is not None:
        observation_day_2 = build_observation_temp_checks_day_2(patient_ref, encounter_ref, day_2_fever)
        observations.append(observation_day_2)
    if day_3_fever is not None:
        observation_day_3 = build_observation_temp_checks_day_3(patient_ref, encounter_ref, day_3_fever)
        observations.append(observation_day_3)
    

    return observations

def build_observation_temp_checks_day_2(patient_ref: str, encounter_ref: str, day_2_fever: int) -> Observation:
    """
    Build FHIR Observation resources for daily temperature checks.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        day_2_fever: Temperature measurements on day 2
    Returns:
        Observation resource for daily temperature checks
    """

    observation = Observation(
        code=CodeableConcept(coding=[TimingMetricCodes.FEVER_DAY_2.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueInteger = day_2_fever


    return observation

def build_observation_temp_checks_day_3(patient_ref: str, encounter_ref: str, day_3_fever: int) -> Observation:
    """
    Build FHIR Observation resources for daily temperature checks.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        day_3_fever: Temperature measurements on day 3
    Returns:
        Observation resource for daily temperature checks
    """

    observation = Observation(
        code=CodeableConcept(coding=[TimingMetricCodes.FEVER_DAY_3.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueInteger = day_3_fever


    return observation


def build_observation_fever(patient_ref: str, encounter_ref: str, observation_measurement_ref: list[str] | None , fever: bool) -> Observation:
    """
    Build a FHIR Observation resource for presence of fever.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        fever: Boolean indicating presence of fever
    Returns:
        Observation resource for presence of fever
    """

    observation = Observation(
        code=CodeableConcept(coding=[AnaliticsCodes.FEVER.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        hasMember=[Reference(reference=ref) for ref in observation_measurement_ref] if observation_measurement_ref is not None else None,
        valueBoolean=fever
    )

    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/fever-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    observation.extension = [Extension(url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext", valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.HOURS_72.to_coding()]))]
    
    
    return observation


def build_observation_hyperglycemia_measurement_checks(patient_ref: str, encounter_ref: str, day_1_hyperglycemia: int | None , day_2_hyperglycemia: int | None , day_3_hyperglycemia: int| None ) -> list[Observation]:
    """
    Build a FHIR Observation resource for presence of hyperglycemia.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        day_1_hyperglycemia: Hyperglycemia measurements on day 1
        day_2_hyperglycemia: Hyperglycemia measurements on day 2
        day_3_hyperglycemia: Hyperglycemia measurements on day 3
    Returns:
        List of Observation resources for presence of hyperglycemia
    """

    observations = []
    if day_1_hyperglycemia is not None:
        observation_day_1_hyperglycemia = Observation(
            code=CodeableConcept(coding=[TimingMetricCodes.HYPERGLYCEMIA_DAY_1.to_coding()]),
            status="final",
            subject=Reference(reference=patient_ref),
            encounter=Reference(reference=encounter_ref),
            meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/hyperglycemia-observation-profile"]),
            category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]

        )
        observation_day_1_hyperglycemia.valueInteger = day_1_hyperglycemia
        observations.append(observation_day_1_hyperglycemia)

    if day_2_hyperglycemia is not None:
        observation_day_2_hyperglycemia = build_observation_hyperglycemia_day_2(patient_ref, encounter_ref, day_2_hyperglycemia)
        observations.append(observation_day_2_hyperglycemia)
    if day_3_hyperglycemia is not None:
        observation_day_3_hyperglycemia = build_observation_hyperglycemia_day_3(patient_ref, encounter_ref, day_3_hyperglycemia)
        observations.append(observation_day_3_hyperglycemia)

    return observations

def build_observation_hyperglycemia_day_2(patient_ref: str, encounter_ref: str, day_2_hyperglycemia: int) -> Observation:
    """
    Build a FHIR Observation resource for presence of hyperglycemia.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        day_2_hyperglycemia: Hyperglycemia measurements on day 2
    Returns:
        Observation resource for presence of hyperglycemia
    """
    observation = Observation(
        code=CodeableConcept(coding=[TimingMetricCodes.HYPERGLYCEMIA_DAY_2.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueInteger = day_2_hyperglycemia

    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/hyperglycemia-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    return observation

def build_observation_hyperglycemia_day_3(patient_ref: str, encounter_ref: str, day_3_hyperglycemia: int) -> Observation:
    """
    Build a FHIR Observation resource for presence of hyperglycemia.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        day_3_hyperglycemia: Hyperglycemia measurements on day 3
    Returns:
        Observation resource for presence of hyperglycemia
    """
    observation = Observation(
        code=CodeableConcept(coding=[TimingMetricCodes.HYPERGLYCEMIA_DAY_3.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueInteger = day_3_hyperglycemia

    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/hyperglycemia-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    return observation


def build_observation_ge10(patient_ref: str, encounter_ref: str, ge10: bool) -> Observation:
    """
    Build a FHIR Observation resource for presence of glucose >= 10 mmol/L.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        ge10: Boolean indicating presence of glucose >= 10 mmol/L
    Returns:
        Observation resource for presence of glucose >= 10 mmol/L
    """
    observation = Observation(
        code=CodeableConcept(coding=[AnaliticsCodes.GE10.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueBoolean = ge10

    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/glucose-ge10-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    return observation

def build_observation_highest_hyperglycemia_value(patient_ref: str, encounter_ref: str, observation_measurement_ref: list[str] | None, highest_hyperglycemia_value: int ) -> Observation:
    """
    Build a FHIR Observation resource for highest hyperglycemia value.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        highest_hyperglycemia_value: Highest hyperglycemia value recorded during hospitalization
    Returns:
        Observation resource for highest hyperglycemia value
    """
    observation = Observation(
        code=CodeableConcept(coding=[AnaliticsCodes.HIGHEST_HYPERGLYCEMIA_VALUE.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        hasMember=[Reference(reference=ref) for ref in observation_measurement_ref] if observation_measurement_ref is not None else None
    )
    observation.valueQuantity = Quantity(value=Decimal(highest_hyperglycemia_value) , unit=UnitofMeasurement.MMOL_L.display, system=UnitofMeasurement.MMOL_L.system, code=UnitofMeasurement.MMOL_L.code) 

    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/highest-hyperglycemia-value-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    observation.extension = [Extension(url="http://tecnomod-um.org/StructureDefinition/observation-timing-context-ext", valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.FIRST_48_HOURS.to_coding()]))]
    return observation


def build_abcd2_score_observation(patient_ref: str, encounter_ref: str, abcd2_score: int) -> Observation:
    """
    Build a FHIR Observation resource for ABCD2 score.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        abcd2_score: ABCD2 score

    Returns:
        Observation resource for ABCD2 score
    """
    observation = Observation(
        code=CodeableConcept(coding=[FunctionalScore.ABCD2.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueInteger = abcd2_score
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    return observation

def build_CHA2S2_VASc_observation(patient_ref: str, encounter_ref: str, cha2s2_vasc_score: int) -> Observation:
    """
    Build a FHIR Observation resource for CHA2DS2-VASc score.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        cha2s2_vasc_score: CHA2DS2-VASc score
    Returns:
        Observation resource for CHA2DS2-VASc score
    """
    observation = Observation(
        code=CodeableConcept(coding=[FunctionalScore.CHA2S2_VASc.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueInteger = cha2s2_vasc_score
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    return observation

def build_thrive_score_observation(patient_ref: str, encounter_ref: str, thrive_score: int) -> Observation:
    """
    Build a FHIR Observation resource for THRIVE score.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        thrive_score: THRIVE score
    Returns:
        Observation resource for THRIVE score
    """
    observation = Observation(
        code=CodeableConcept(coding=[FunctionalScore.THRIVE.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    observation.valueInteger = thrive_score
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/functional-score-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    return observation

def build_appointment_observation(patient_ref: str, encounter_ref: str, appointment_management: ManagementAppointment) -> Observation:
    """
    Build a FHIR Observation resource for appointment date.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        appointment_management: ManagementAppointment resource
    Returns:
        Observation resource for appointment meeting recommendations
    """

    observation = Observation(
        code=CodeableConcept(coding=[ManagementAppointment.APPOINTMENT.to_coding()]),
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        valueCodeableConcept=CodeableConcept(coding=[appointment_management.to_coding()])
    )
    observation.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/appointment-management-observation-profile"])
    observation.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
    return observation
