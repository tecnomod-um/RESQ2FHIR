"""
Condition resource builders for FHIR transformation.
"""

from fhir.resources.condition import Condition
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.meta import Meta 
from fhir.resources.reference import Reference
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.extension import Extension
from scripts.enum_models import BleedingReason, BodySites, MimicsDiagnosis, PostStrokeComplications, RiskFactor, SpecificFinding, StrokeEtiology, StrokeEtiology, StrokeType, ClinicalStatusCodes
from scripts.utils import parse_datetime


def build_stroke_diagnosis_condition_profile(patient_ref: str, encounter_ref: str, stroke_type: StrokeType | None, stroke_type_mimics: MimicsDiagnosis | None, stroke_etiology_known: bool, stroke_etiology: StrokeEtiology | None , bleeding_reason_found: bool, bleeding_reason: BleedingReason | None, wakeup_stroke: bool, sleep_timestamp: str | None, onset_timestamp: str | None, obs_symptoms_tia_ref: str | None, ich_infratentorial: bool, ich_supratentorial: bool, intraventricular_hemorrhage: bool, subarachnoid_hemorrhage: bool) -> Condition:
    """
    Build a FHIR Condition resource for stroke diagnosis.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        stroke_type: ConceptEnum representing the type of stroke (Ischemic, Hemorrhagic, TIA, Stroke Mimic)
        stroke_type_mimics: ConceptEnum representing the type of stroke mimic
        stroke_etiology_known: Boolean indicating if stroke etiology is known
        stroke_etiology: ConceptEnum representing the etiology of ischemic stroke (if known)
        bleeding_reason_found: Boolean indicating if bleeding reason for hemorrhagic stroke is found
        bleeding_reason: ConceptEnum representing the bleeding reason for hemorrhagic stroke (if found)
        wakeup_stroke: Boolean indicating if it's a wake-up stroke
        sleep_timestamp: Timestamp of when the patient went to sleep (for wake-up strokes)
        onset_timestamp: Timestamp of symptom onset (for non-wake-up strokes)
        obs_symptoms_tia_ref: Reference to observed symptoms for TIA (optional, can be used for extensions)
        
    Returns:
        Condition resource with stroke diagnosis profile
    """
    condition = Condition(
        subject=Reference(reference=patient_ref),
        clinicalStatus=CodeableConcept(),
        encounter=Reference(reference=encounter_ref),
    )

    # code (Stroke type)
    if stroke_type is not None:
        condition.code = CodeableConcept(coding=[stroke_type.to_coding()])
    
    if stroke_type == StrokeType.STROKE_MIMICS and stroke_type_mimics is not None:
        condition.code = CodeableConcept(coding=[stroke_type_mimics.to_coding()])

    if stroke_type == StrokeType.TRANSIENT_ISCHEMIC: 
        if obs_symptoms_tia_ref is not None:
            condition.evidence = [CodeableReference(reference=Reference(reference=obs_symptoms_tia_ref))]


    if stroke_type == StrokeType.INTRACEREBRAL_HEMORRHAGE:
        bodysites = []
        if ich_infratentorial is True:
            bodysites.append(CodeableConcept(coding=[BodySites.INFRATENTORIAL.to_coding()]))
        if ich_supratentorial is True:
            bodysites.append(CodeableConcept(coding=[BodySites.SUPRATENTORIAL.to_coding()]))
        if intraventricular_hemorrhage is True:
            bodysites.append(CodeableConcept(coding=[BodySites.INTRAVENTRICULAR.to_coding()]))
        if subarachnoid_hemorrhage is True:
            bodysites.append(CodeableConcept(coding=[BodySites.SUBARACHNOID.to_coding()]))
        condition.bodySite = bodysites
    
    # statuses
    condition.clinicalStatus = CodeableConcept(coding=[Coding(
        system="http://terminology.hl7.org/CodeSystem/condition-clinical",
        code="active",
        display="Active"
    )])

    if stroke_type == StrokeType.UNDETERMINED:
        condition.verificationStatus = CodeableConcept(coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
            code="unknown",
            display="Unknown"
        )])
    else:
        condition.verificationStatus = CodeableConcept(coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
            code="confirmed",
            display="Confirmed"
        )])

    # Profile + optional extensions
    condition.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-diagnosis-condition-profile"])
    extension_list = []

    
    

    # if not safe_isna(raw.get("stroke_etiology_known")) and raw.get("stroke_etiology_known"):
    #     etiology = get_stroke_etiology(raw)
    if stroke_etiology_known is True:
        if stroke_etiology is not None:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/ischemic-stroke-etiology-ext",
                valueCodeableConcept=CodeableConcept(coding=[stroke_etiology.to_coding()])
            ))
    else:
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/ischemic-stroke-etiology-known-ext",
            valueCodeableConcept=CodeableConcept(coding=[StrokeEtiology.UNDETERMINED.to_coding()])
        ))
    
    if bleeding_reason_found is True:
        if bleeding_reason is not None:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/hemorrhagic-stroke-bleeding-reason-ext",
                valueCodeableConcept=CodeableConcept(coding=[bleeding_reason.to_coding()])
            ))
        else:
            extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/hemorrhagic-stroke-bleeding-reason-found-ext",
                valueCodeableConcept=CodeableConcept(coding=[BleedingReason.UNDETERMINED.to_coding()])
            ))


    
    if wakeup_stroke is True:
            if sleep_timestamp is not None: 
                condition.onsetDateTime = parse_datetime(sleep_timestamp)
    else:
            if onset_timestamp is not None:
                condition.onsetDateTime = parse_datetime(onset_timestamp)

    extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/wakeup-stroke-ext",
            valueBoolean=wakeup_stroke
        ))

    if extension_list:
        condition.extension = extension_list

    return condition


def build_risk_factor_condition_profile(risk_factors: list, patient_ref: str, encounter_ref: str):
    """
    Build FHIR Condition resources for stroke risk factors.
    
    Args:
        risk_factors: List of risk factors grouped by clinical status (active, inactive, unknown, remission), where each item is a tuple of (clinical_status, list_of_risk_factors)
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        List of Condition resources representing risk factors by clinical status
    """
    final_rf_list = []
    for status_key, rf in risk_factors:
        # Build condition core attributes
        clinicalStatus_coding = ClinicalStatusCodes.by_id(status_key).to_coding()
        code_status = CodeableConcept(coding=[clinicalStatus_coding])
        
        for r in rf:
            code_rf = CodeableConcept(coding=[r.to_coding()])
            
            condition = Condition(
                subject=Reference(reference=patient_ref),
                code=code_rf,
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-risk-factor-condition-profile"]),
                clinicalStatus=code_status,
                encounter=Reference(reference=encounter_ref),
            )
            
            if r.id == RiskFactor.AtrialFibrillation.id:
                condition.verificationStatus = CodeableConcept(coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    code="differential",
                    display="Differential"
                )])
            
            final_rf_list.append(condition)
        
    return final_rf_list



# def build_stroke_mimics_condition(patient_ref:str, encounter_ref:str, stroke_mimic_type: DiagnosisStrokes) -> Condition:
#     """
#     Build a FHIR Condition resource for stroke mimic diagnosis.
    
#     Args:
#         patient_ref: Reference to the Patient resource
#         encounter_ref: Reference to the Encounter resource
#         stroke_mimic_type: ConceptEnum representing the type of stroke mimic (Delirium, Seizure, Functional Disorder, Imbalance, Other)
#     Returns:
#         Condition resource with stroke mimic diagnosis
#     """

#     mimic_condition = Condition(
#         subject=Reference(reference=patient_ref),
#         clinicalStatus=CodeableConcept(coding=[Coding(
#             system="http://terminology.hl7.org/CodeSystem/condition-clinical",
#             code="active",
#             display="Active"
#         )]),
#         verificationStatus=CodeableConcept(coding=[Coding(
#             system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
#             code="confirmed",
#             display="Confirmed"
#         )]),
#         encounter=Reference(reference=encounter_ref),
#         code = CodeableConcept(coding=[stroke_mimic_type.to_coding()])
#     )

#     return mimic_condition


# def build_hyperglycemia_condition(patient_ref:str, encounter_ref:str, hyperglycemia: bool) -> Condition:
#     """
#     Build a FHIR Condition resource for hyperglycemia status.
    
#     Args:
#         patient_ref: Reference to the Patient resource
#         encounter_ref: Reference to the Encounter resource
#         hyperglycemia: Boolean indicating presence of hyperglycemia
#     Returns:
#         Condition resource with hyperglycemia status
#     """
#     hyperglycemia_condition = Condition(
#         subject=Reference(reference=patient_ref),
#         encounter=Reference(reference=encounter_ref),
#         code = CodeableConcept(coding=[AnaliticsCodes.HYPERGLYCEMIA.to_coding()])
#     )

#     if hyperglycemia is True:
#         hyperglycemia_condition.clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()])
#     else:
#         hyperglycemia_condition.clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.INACTIVE.to_coding()])

#     return hyperglycemia_condition


def build_post_stroke_conditions(patient_ref:str, encounter_ref:str, post_stroke_any:bool, post_stroke_sepsis:bool, post_stroke_dvt:bool, post_stroke_falling:bool, post_stroke_other:bool, post_stroke_pressure_sores: bool, post_stroke_recurrence: bool, post_stroke_urinary_infection: bool, post_stroke_pneumonia: bool, post_stroke_pulmonary_embolism: bool) -> list[Condition]:
    """
    Build a FHIR Condition resource for post-stroke complications.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        post_stroke_any: Boolean indicating presence of any post-stroke complication
        post_stroke_sepsis: Boolean indicating presence of post-stroke sepsis
        post_stroke_dvt: Boolean indicating presence of post-stroke deep vein thrombosis
        post_stroke_falling: Boolean indicating presence of post-stroke falling
        post_stroke_other: Boolean indicating presence of other post-stroke complications
        post_stroke_pressure_sores: Boolean indicating presence of post-stroke pressure sores
        post_stroke_recurrence: Boolean indicating presence of post-stroke recurrence
        post_stroke_urinary_infection: Boolean indicating presence of post-stroke urinary infection
        post_stroke_pneumonia: Boolean indicating presence of post-stroke pneumonia
        post_stroke_pulmonary_embolism: Boolean indicating presence of post-stroke pulmonary embolism
    Returns:
        Condition resource with post-stroke complications status
    """
    condition_list = []
    if post_stroke_any is True:  
        if post_stroke_sepsis is True:
            sepsis_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.SEPSIS.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(sepsis_condition)
        if post_stroke_dvt is True:
            dvt_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.DVT.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(dvt_condition)

        if post_stroke_falling is True:
            falling_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.FALLING.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(falling_condition)
        if post_stroke_other is True:
            other_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.OTHER.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(other_condition)
        if post_stroke_pressure_sores is True:
            sores_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.SORES.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(sores_condition)
        if post_stroke_recurrence is True:
            recurrence_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.RECURRENT.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(recurrence_condition)
        if post_stroke_urinary_infection is True:
            urinary_infection_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.URINARY_INFECTION.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(urinary_infection_condition)

        if post_stroke_pneumonia is True:
            pneumonia_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.PNEUMONIA.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(pneumonia_condition)

        if post_stroke_pulmonary_embolism is True:
            pulmonary_embolism_condition = Condition(
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                code = CodeableConcept(coding=[PostStrokeComplications.PULMONARY_EMBOLISM.to_coding()]),
                clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()]),
                meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/post-stroke-complication-condition-profile"])
            )
            condition_list.append(pulmonary_embolism_condition)

    return condition_list
        

    
def build_hydrocephalus_condition(patient_ref:str, encounter_ref:str, hydrocephalus: bool) -> Condition:
    """
    Build a FHIR Condition resource for hydrocephalus status.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        hydrocephalus: Boolean indicating presence of hydrocephalus
    Returns:
        Condition resource with hydrocephalus status
    """
    hydrocephalus_condition = Condition(
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code = CodeableConcept(coding=[SpecificFinding.HYDROCEPHALUS.to_coding()])
    )

    if hydrocephalus is True:
        hydrocephalus_condition.clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.ACTIVE.to_coding()])
    else:
        hydrocephalus_condition.clinicalStatus = CodeableConcept(coding=[ClinicalStatusCodes.INACTIVE.to_coding()])

    return hydrocephalus_condition

    
    
