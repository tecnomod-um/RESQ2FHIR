"""
Main module for FHIR transformation.
Orchestrates the construction of FHIR resources from raw stroke data.
"""

from curses import raw

from fhir.resources.bundle import Bundle, BundleEntryRequest
import pandas as pd

import scripts
from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryRequest
from scripts.enum_models import AdmissionDepartment, AdmissionPathway, AssessmentContext, AtrialFibrillationOrFlutter, BleedingReason, CarotidStenosisLevel, DischargeDestination, DischargeFacilityDepartment, FirstContactPlace, HospitalizedIn, ImagingDone, ImagingType, InsulinOnHyperglycemiaTiming, Locations, MRsScore, MTiciScore, ManagementAppointment, Medications, MimicsDiagnosis, NoThrombectomyReason, NoThrombolysisReason, NotMedicationReason, PostAcuteCare, PostNeurosurgeryImaging, PostRecanalizationImaging, ProcedureNotDoneReason, Sex, StrokeEtiology, StrokeType, ThreeMonthContactMode
from scripts.fhir_resources.appointment import build_follow_up_appointment
from scripts.fhir_resources.bodyStructure import build_bodyStructure
from scripts.fhir_resources.diagnosticReport import build_carotid_arteries_imaging_diagnostic_report, build_ct_mr_after_ivt_diagnostic_report, build_imaging_diagnostic_report, build_mechanical_thrombectomy_diagnostic_report
from scripts.fhir_resources.location import build_hospitalized_location, build_location
from scripts.fhir_resources.medicationAdministration import build_insulin_on_hyperglycemia, build_medicationAdministration, build_medicationAdministration_nimopidine, build_medicationAdministration_paracetamol_on_fever
from scripts.fhir_resources.organization import build_organization
from scripts.fhir_resources.patient import build_Patient
from scripts.fhir_resources.encounter import build_stroke_encounter_profile
from scripts.fhir_resources.condition import build_post_stroke_conditions, build_stroke_diagnosis_condition_profile, build_risk_factor_condition_profile
from scripts.fhir_resources.observation import build_CHA2S2_VASc_observation, build_abcd2_score_observation, build_door_to_anticoagulant_reversal_observation, build_door_to_discharge_observation, build_door_to_door_observation, build_door_to_reperfusion_observation, build_door_to_sys_bp_lt140_observation, build_groin_to_reperfusion_observation, build_highest_systolic_pressure_after24h_observation, build_observation_aspect_score, build_observation_blood_volume, build_observation_carotid_stenosis, build_observation_cholesterol, build_observation_fever, build_observation_finding_post_ivt_mt, build_observation_ge10, build_observation_glasgow_coma_scale, build_observation_glucose, build_observation_highest_hyperglycemia_value, build_observation_hunt_hess_score, build_observation_hyperglycemia_measurement_checks, build_observation_inr, build_observation_occluded_artery, build_observation_old_infarcts_brainstem, build_observation_patient_ventilated, build_observation_perfusion, build_observation_temp_checks, build_observation_three_month_contact_mode, build_observation_vital_signs, build_observation_mrs, build_observation_nihss, build_observation_mtici_score, build_observation_age, build_onset_to_door_observation, build_systolic_pressure_lt140_observation, build_thrive_score_observation, build_tia_clinical_symptomps_observation, build_timing_d2g_le120_observation, build_timing_d2g_le90_observation, build_timing_d2g_observation, build_timing_d2n_le45_observation, build_timing_d2n_le60_observation, build_timing_d2n_observation, build_timing_discharge_to_three_months_contact_observation, build_timing_door_to_ich_evacuation_observation, build_timing_door_to_ich_evacuation_observation, build_timing_door_to_imaging_observation, build_timing_door_to_iv_antihypertensive_observation, build_observation_Af_or_F
from scripts.fhir_resources.practitionerRole import build_practitioner
from scripts.fhir_resources.procedure import build_carotid_imaging_procedure, build_craniectomy_procedure, build_cvt_treatment_procedure, build_endarterectomy_procedure, build_ich_treatment_procedure, build_imaging_procedure, build_occupational_therapy_procedure, build_physioterapy_procedure, build_post_neurosurgery_imaging_procedure, build_post_recanalization_imaging_procedure, build_sah_treatment_procedure, build_speech_therapy_procedure, build_thrombolysis_procedure, build_thrombectomy_procedure, build_swallowing_screening_procedure, build_vte_procedure
from scripts.fhir_resources.medicationStatement import build_before_onset_medicationStatement_profile
from scripts.fhir_resources.medicationRequest import build_on_discharge_medicationRequest_profile
from scripts.helpers import get_before_onset_medications, get_occlusions_list, get_on_discharge_medications, get_risk_factors
from scripts.helpers import get_risk_factors
from utils import get_uuid, safe_get, safe_get_bool, ensure_dependency







def transform_to_fhir(file_id: str, raw: dict) -> Bundle:
    """
    Transform raw stroke data into a FHIR Bundle transaction.
    
    Orchestrates the construction of all FHIR resources from raw data:
    - Organization, Patient, Encounter (core resources)
    - Conditions (stroke diagnosis, risk factors)
    - Observations (vital signs, functional scores, etc.)
    - Procedures (imaging, interventions, screening)
    - Medications (before-onset, discharge)

    

    Args:
        file_id: Unique patient file identifier
        raw: Raw patient/stroke data dictionary
        
    Returns:
        FHIR Bundle with transaction entries
        
    Raises:
        TransformError: If required data is missing or invalid
    """
    patient_ref = get_uuid()
    encounter_ref = get_uuid()
    medicationAdministration_reversal_ref = get_uuid()
    observation_vital_signs_ref = ""
    procedure_imaging_ref = ""
    procedure_ich_treatment_ref = ""
    medicationAdministration_iv_antihypertensive_ref = ""
########################## 0. Admission Data ##########################

    ########################## 0.1. Organization ##########################
    hospital_name = safe_get(raw, "provider", required=True)
    organization = build_organization(str(hospital_name))
    entries = [BundleEntry(fullUrl=get_uuid(), resource=organization, request=BundleEntryRequest(method="POST", url="Organization"))] # Initialize entries list with Organization resource built from hospital_name in raw data, field required

    ########################## 0.2. Patient ##########################
    sex = safe_get(raw, "sex", required=True) # Obtain sex from raw data, field not required
    patient = build_Patient(patient_id=file_id, patient_sex=Sex.by_id(sex)) # Build Patient resource using file_id and sex
    entries.append(BundleEntry(fullUrl=patient_ref, resource=patient, request=BundleEntryRequest(method="POST", url="Patient"))) # Add Patient resource to entries with reference patient_ref

    age = build_observation_age(patient_ref=patient_ref, encounter_ref=encounter_ref, age=safe_get(raw, "age", required=True)) # Build Observation resource for age using patient_ref, encounter_ref and age from raw data, field required
    entries.append(BundleEntry(fullUrl=get_uuid(), resource=age, request=BundleEntryRequest(method="POST", url="Observation")))

    ########################## 0.3. Encounter ##########################
    first_contact_place = safe_get(raw, "first_contact_place", required=False)
    first_location_ref = ""
    if first_contact_place is not None:
        first_location = build_location(FirstContactPlace.by_id(first_contact_place)) # Build Location resource for first contact place using first_contact_place from raw data, field not required
        first_location_ref = get_uuid()
        entries.append(BundleEntry(fullUrl=first_location_ref, resource=first_location, request=BundleEntryRequest(method="POST", url="Location")))
    hospitalized_in = safe_get(raw, "hospitalized_in", required=True)

    hosp_loc_ref = ""
    if hospitalized_in is not None:
        admission_department = safe_get(raw, "admission_department", required=False)
        if admission_department is not None:
            # Create hospitalized_in extension
            hosp_loc = build_hospitalized_location(HospitalizedIn.by_id(hospitalized_in), AdmissionDepartment.by_id(admission_department))
            hosp_loc_ref = get_uuid()
            entries.append(BundleEntry(fullUrl=hosp_loc_ref, resource=hosp_loc, request=BundleEntryRequest(method="POST", url="Location")))


    encounter = build_stroke_encounter_profile(patient_ref=patient_ref, # Build Encounter resource using patient_ref and other relevant data from raw
                                                arrival_mode=AdmissionPathway.by_id(safe_get(raw, "arrival_mode_id", required=False)), # Obtain arrival mode from raw data and convert to ArrivalMode enum, field not required
                                                discharge_destination=DischargeDestination.by_id(safe_get(raw, "discharge_destination", required=False)), # Obtain discharge destination from raw data and convert to DischargeDestination enum, field not required
                                                discharge_facility_department=DischargeFacilityDepartment.by_id(safe_get(raw, "discharge_facility_department", required=False)), # Obtain discharge facility department from raw data and convert to DischargeFacilityDepartment enum, field not required
                                                discharge_facility_type=DischargeDestination.by_id(safe_get(raw, "discharge_facility_type", required=False)), # Obtain discharge facility type from raw data and convert to DischargeDestination enum, field not required
                                                first_contact_place=FirstContactPlace.by_id(first_contact_place), # Obtain first contact place from raw data and convert to Locations enum, field not required
                                                first_location_ref = first_location_ref,
                                                hospitalized_location_ref= hosp_loc_ref,
                                                inhospital_stroke=safe_get_bool(raw, "inhospital_stroke", required=False, default=False), # Obtain inhospital stroke boolean from raw data, field not required, default to False
                                                hospital_timestamp=safe_get(raw, "hospital_timestamp", required=False), # Obtain hospital timestamp from raw data, field not required
                                                discharge_date=safe_get(raw, "discharge_date", required=False), # Obtain discharge date from raw data, field not required
                                                first_hospital=safe_get_bool(raw, "first_hospital", required=False, default=False), # Obtain first hospital boolean from raw data, field not required, default to False
                                                post_acute_care=safe_get_bool(raw, "post_acute_care", required=False, default=False), # Obtain post-acute care boolean from raw data, field not required, default to False
                                                ems_prenotification=safe_get_bool(raw, "ems_prenotification", required=False, default=False)) # Obtain EMS prenotification boolean from raw data, field not required, default to False
    
    entries.append(BundleEntry(fullUrl=encounter_ref, resource=encounter, request=BundleEntryRequest(method="POST", url="Encounter")))

########################### End Admission Data Form ########################################################################

############################# 1. Baseline Data ##########################################
    ################## 1.1. Risk factor Conditions #######################
    risk_factor_active, risk_factor_inactive, risk_factor_unknown, risk_factor_remission = get_risk_factors(raw) ## Obtain risk factors grouped by clinical status using helper function, passing raw data
    risk_grouped = [
        ("Active", risk_factor_active),
        ("Inactive", risk_factor_inactive),
        ("Unknown", risk_factor_unknown),
        ("Remission", risk_factor_remission)
    ] # Group risk factors by clinical status in a list of tuples, where each tuple contains the clinical status and the corresponding list of risk factors
    for condition in build_risk_factor_condition_profile(risk_factors=risk_grouped, patient_ref=patient_ref, encounter_ref=encounter_ref): # Build Condition resources for risk factors using the grouped risk factors and other relevant data from raw
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=condition, request=BundleEntryRequest(method="POST", url="Condition")))

    #################### 1.2. Before-onset medications (MedicationStatement) #######################
    med_taken, med_not_taken, med_unknown = get_before_onset_medications(raw)
    med_grouped = [
        ("Taking", med_taken),
        ("Not Taking", med_not_taken),
        ("Unknown", med_unknown)
    ]
    
    for med_statement in build_before_onset_medicationStatement_profile(med_grouped, patient_ref, encounter_ref):
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=med_statement, request=BundleEntryRequest(method="POST", url="MedicationStatement")))

    #################### 1.3. Glucose observation ########################
    glucose_value = safe_get(raw, "glucose", required=True) # Check if glucose level is present in raw data, not required
    if glucose_value is not None:
        observation_glucose = build_observation_glucose(patient_ref = patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        glucose=glucose_value,
                                                        timing=AssessmentContext.ADMISSION) # Build Observation resource for glucose level using patient_ref, encounter_ref and glucose_value

        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_glucose, request=BundleEntryRequest(method="POST", url="Observation")))

    #################### 1.4. Cholesterol observation ########################
    cholesterol_value = safe_get(raw, "cholesterol", required=True) # Check if cholesterol level is present in raw data, not required
    if cholesterol_value is not None:
        observation_cholesterol = build_observation_cholesterol(patient_ref = patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                cholesterol=cholesterol_value) # Build Observation resource for cholesterol level using patient_ref, encounter_ref and cholesterol_value
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_cholesterol, request=BundleEntryRequest(method="POST", url="Observation")))

    #################### 1.5. Vital signs observation ########################
    systolic_pressure = safe_get(raw, "systolic_pressure", required=True) # Check if systolic pressure is present in raw data, not required
    diastolic_pressure = safe_get(raw, "diastolic_pressure", required=True) # Check if diastolic pressure is present in raw data, not required

    if systolic_pressure is not None and diastolic_pressure is not None:
        observation_vital_signs_ref = get_uuid()
        observation_vital_signs = build_observation_vital_signs(patient_ref=patient_ref, # Build Observation resource for vital signs using patient_ref, encounter_ref, systolic_pressure and diastolic_pressure
                                                                encounter_ref=encounter_ref,
                                                                systolic_pressure=systolic_pressure,
                                                                diastolic_pressure=diastolic_pressure,
                                                                timing=AssessmentContext.ADMISSION)
        entries.append(BundleEntry(fullUrl=observation_vital_signs_ref, resource=observation_vital_signs, request=BundleEntryRequest(method="POST", url="Observation")))


    nihss_score = safe_get(raw, "nihss_score", required=True) # Check if NIHSS score is present in raw data, not required
    ################### 1.6. NIHSS score #############################
    nihss_pre = build_observation_nihss(patient_ref= patient_ref, 
                                        encounter_ref= encounter_ref, 
                                        value_nihss=nihss_score,
                                        admission_nihss=True, 
                                        discharge_nihss=False) # Build Observation resource for NIHSS score at admission using patient_ref, encounter_ref and nihss_score from raw data, field not required
    entries.append(BundleEntry(fullUrl=get_uuid(), resource=nihss_pre, request=BundleEntryRequest(method="POST", url="Observation")))

    ################### 1.7. mRS score #############################
    prestroke_mrs = safe_get(raw, "prestroke_mrs", required=False) # Check if prestroke mRS score is present in raw data, not required
    if prestroke_mrs is not None:
        mrs_admission = build_observation_mrs(patient_ref= patient_ref, 
                                              encounter_ref= encounter_ref, 
                                              mrs_score=MRsScore.by_id(prestroke_mrs), 
                                              prestroke=True, 
                                              discharge=False, 
                                              threem=False) # Build Observation resource for mRS score at admission using patient_ref, encounter_ref and mrs_score from raw data, field not required
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=mrs_admission, request=BundleEntryRequest(method="POST", url="Observation")))

    ################### 1.8. Glasgow Coma Scale score #############################
    gcs_score = safe_get(raw, "gcs_score", required=False) # Check if Glasgow Coma Scale score is present in raw data, not required
    if gcs_score is not None:
        observation_gcs = build_observation_glasgow_coma_scale(patient_ref= patient_ref, 
                                                               encounter_ref= encounter_ref, 
                                                               gcs_score= gcs_score) # Build Observation resource for Glasgow Coma Scale score using patient_ref, encounter_ref and gcs_score
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_gcs, request=BundleEntryRequest(method="POST", url="Observation")))
    
    ################## 1.9. INR Observation #############################
    inr_mode = safe_get(raw, "inr_mode", required=False) # Check if INR model is present in raw data, not required
    if inr_mode is not None:
        inr_value = safe_get(raw, "inr_value", required=False) # If INR model is present, check if inr_value is present in raw data, required if inr_mode is present
        if inr_value is not None:
            observation_inr = build_observation_inr(patient_ref=patient_ref, 
                                                    encounter_ref=encounter_ref, 
                                                    inr_mode=inr_mode, 
                                                    inr_value=inr_value) # Build Observation resource for INR using patient_ref, encounter_ref and inr_mode from raw data, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_inr, request=BundleEntryRequest(method="POST", url="Observation")))
#######################################End Baseline Data Form########################################################################

####################################### 2. Imaging, diagnosis and treatment ########################################################

    ###################################### 2.1 Brain imaging ######################################
    imaging_type = safe_get(raw, "imaging_type", required=False)
    if imaging_type is not None:
        ############################### 2.1.1 Old infarcts seen in brain imaging (Observation) ######################################
        observation_list_old_infarcts = build_observation_old_infarcts_brainstem(patient_ref=patient_ref,
                                                                                 encounter_ref=encounter_ref,
                                                                                    old_infarcts_any=safe_get_bool(raw, "old_infarcts_any", required=False, default=False),
                                                                                    old_infarcts_brainstem=safe_get_bool(raw, "old_infarcts_brainstem", required=False, default=False),
                                                                                    old_infarcts_cortical=safe_get_bool(raw, "old_infarcts_cortical", required=False, default=False),
                                                                                    old_infarcts_subcortical=safe_get_bool(raw, "old_infarcts_subcortical", required=False, default=False))
        observation_list_old_infarcts_ids = []
        for obs in observation_list_old_infarcts:
            obs_id = get_uuid()
            observation_list_old_infarcts_ids.append(obs_id)
            entries.append(BundleEntry(fullUrl=obs_id, resource=obs, request=BundleEntryRequest(method="POST", url="Observation")))
        ############################ 2.1.2 Perfusion deficit seen in brain imaging (Observation) ######################################
        observation_perfusion_deficit = build_observation_perfusion(patient_ref=patient_ref,
                                                                    encounter_ref=encounter_ref,
                                                                    perfusion_found=safe_get_bool(raw, "perfusion_found", required=False, default=False),
                                                                    perfusion_anterior=safe_get_bool(raw, "perfusion_anterior", required=False, default=False),
                                                                    perfusion_posterior=safe_get_bool(raw, "perfusion_posterior", required=False, default=False),
                                                                    perfusion_carotid=safe_get_bool(raw, "perfusion_carotid", required=False, default=False),
                                                                    perfusion_volume=safe_get(raw, "perfusion_volume", required=False),
                                                                    hypoperfusion_volume=safe_get(raw, "hypoperfusion_volume", required=False)) # Build Observation resource for perfusion deficit using patient_ref, encounter_ref and perfusion-related data from raw data, field not required
        obs_id_perfusion = get_uuid()
        entries.append(BundleEntry(fullUrl=obs_id_perfusion, resource=observation_perfusion_deficit, request=BundleEntryRequest(method="POST", url="Observation")))

        ############################# 2.1.3 DiagnosticReport generated from brain imaging results ######################################
        diagnostic_report_imaging_id = get_uuid()
        diagnostic_report_imaging = build_imaging_diagnostic_report(patient_ref = patient_ref,
                                                                    encounter_ref= encounter_ref,
                                                                    perfusion_deficit_ref = obs_id_perfusion, # Placeholder for perfusion deficit observation reference, can be used for extensions if needed
                                                                    imaging_type = ImagingType.by_id(imaging_type), # Obtain imaging type from raw data and convert to ImagingType enum, field not required
                                                                    imaging_results_ref = observation_list_old_infarcts_ids) # Placeholder for imaging results, can be used for extensions if needed
    
        entries.append(BundleEntry(fullUrl=diagnostic_report_imaging_id, resource=diagnostic_report_imaging, request=BundleEntryRequest(method="POST", url="DiagnosticReport")))
    
        ############################ 2.1.4 Imaging Procedure (Procedure) ######################################
        imaging_timestamp = safe_get(raw, "imaging_timestamp", required=True) # Check if imaging timestamp is present in raw data, not required
        procedure_imaging_ref = get_uuid()
        proc_img = build_imaging_procedure(patient_ref = patient_ref, 
                                           encounter_ref = encounter_ref,
                                           diagnostic_report_ref= diagnostic_report_imaging_id,
                                           imaging_done= ImagingDone.by_id(safe_get(raw, "imaging_done", required=False)), # Build Procedure resource for brain imaging using patient_ref, encounter_ref and imaging_type from raw data, field not required
                                           imaging_type = ImagingType.by_id(imaging_type),
                                           post_acute_care=False,
                                           imaging_timestamp= imaging_timestamp) # Build Procedure resource for brain imaging using patient_ref, encounter_ref and imaging_type from raw data, field not required
                                                                         
        entries.append(BundleEntry(fullUrl=procedure_imaging_ref, resource=proc_img, request=BundleEntryRequest(method="POST", url="Procedure")))

    ########################## 2.2 Stroke Type ###########################
    condition_stroke_ref = None
    stroke_type = safe_get(raw, "stroke_type", required=True) # Check if stroke_type is present in raw data, not required
    if stroke_type is not None:
        ############################ 2.2.1 Clinical symptoms of TIA (Observation) ######################################
        obs_clinical_symptoms_ref_id = None
        if stroke_type == StrokeType.TRANSIENT_ISCHEMIC:
            tia_symptoms = safe_get(raw, "tia_symptoms", required=True) # If stroke type is TIA, check if tia_symptoms is present in raw data, required if stroke_type is TIA
            if tia_symptoms is not None:
                obs_clinical_symptoms_ref = build_tia_clinical_symptomps_observation(patient_ref=patient_ref, # Build Observation resource for TIA clinical symptoms using patient_ref, encounter_ref and tia_symptoms from raw data, field not required
                                                                                encounter_ref=encounter_ref,
                                                                                tia_symptom=tia_symptoms,
                                                                                tia_duration=safe_get(raw, "tia_symptoms_duration", required=False)) 
            
                obs_clinical_symptoms_ref_id = get_uuid()
                entries.append(BundleEntry(fullUrl=obs_clinical_symptoms_ref_id, resource=obs_clinical_symptoms_ref, request=BundleEntryRequest(method="POST", url="Observation"))  )
        condition_stroke_ref = get_uuid()
        condition_stroke = build_stroke_diagnosis_condition_profile(patient_ref = patient_ref, # Build Condition resource for stroke diagnosis using patient_ref and other relevant data from raw
                                                                    encounter_ref = encounter_ref,
                                                                    stroke_type = StrokeType.by_id(safe_get(raw, "stroke_type", required=True)), # Obtain stroke type from raw data and convert to ConceptEnum, field not required
                                                                    stroke_type_mimics=MimicsDiagnosis.by_id(safe_get(raw, "stroke_mimics_diagnosis", required=False)), # Obtain stroke type mimics from raw data and convert to ConceptEnum, field not required
                                                                    stroke_etiology=StrokeEtiology.by_id(safe_get(raw, "stroke_etiology", required=False)), # Obtain stroke etiology from raw data and convert to ConceptEnum, field not required
                                                                    bleeding_reason=BleedingReason.by_id(safe_get(raw, "bleeding_reason", required=False)), # Obtain bleeding reason from raw data and convert to ConceptEnum, field not required
                                                                    bleeding_reason_found=safe_get_bool(raw, "bleeding_reason_found", required=False), # Obtain bleeding reason found from raw data and convert to ConceptEnum, field not required
                                                                    stroke_etiology_known=safe_get_bool(raw, "stroke_etiology_known", required=False, default=False), # Obtain stroke etiology known boolean from raw data, field not required, default to False
                                                                    ich_infratentorial=safe_get_bool(raw, "ich_infratentorial", required=False, default=False), # Obtain intracerebral hemorrhage infratentorial boolean from raw data, field not required, default to False
                                                                    ich_supratentorial=safe_get_bool(raw, "ich_supratentorial", required=False, default=False), # Obtain intracerebral hemorrhage supratentorial boolean from raw data, field not required, default to False
                                                                    intraventricular_hemorrhage=safe_get_bool(raw, "intraventricular_hemorrhage", required=False, default=False), # Obtain intraventricular hemorrhage boolean from raw data, field not required, default to False
                                                                    subarachnoid_hemorrhage=safe_get_bool(raw, "subarachnoid_hemorrhage", required=False, default=False), # Obtain subarachnoid hemorrhage boolean from raw data, field not required, default to False
                                                                    wakeup_stroke = safe_get_bool(raw, "wakeup_stroke", required=False, default=False), # Obtain wake-up stroke boolean from raw data, field not required, default to False
                                                                    sleep_timestamp = safe_get(raw, "sleep_timestamp", required=False), # Obtain sleep timestamp from raw data, field not required
                                                                    onset_timestamp = safe_get(raw, "onset_timestamp", required=False), # Obtain onset timestamp from raw data, field not required
                                                                    obs_symptoms_tia_ref = obs_clinical_symptoms_ref_id, # Placeholder for observed symptoms reference, can be used for extensions if needed
                                                                    ) # Placeholder for observed symptoms description, can be used for extensions if needed
        entries.append(BundleEntry(fullUrl=condition_stroke_ref, resource=condition_stroke, request=BundleEntryRequest(method="POST", url="Condition")))
        ########################### 2.2.2 Ischemic stroke type (Condition) ######################################

        if stroke_type == StrokeType.ISCHEMIC:
            
            ensure_dependency(condition_stroke_ref is not None,
                              need="Stroke Condition",
                              because="Stroke Type=Ischemic requires a Condition to reference")
        ########################### 2.2.2.1 ASPECTS score (Observation) ######################################
            aspect_score_value = safe_get(raw, "aspect_score", required=False) # Check if ASPECTS score is present in raw data, not required
            if aspect_score_value is not None:
                observation_aspect_score = build_observation_aspect_score(patient_ref=patient_ref, 
                                                                      encounter_ref=encounter_ref, 
                                                                      aspect_score=aspect_score_value
                                                                      ) # Build Observation resource for ASPECTS score using patient_ref, encounter_ref and aspect_score from raw data, field not required
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_aspect_score, request=BundleEntryRequest(method="POST", url="Observation")))

        ########################### 2.2.2.2 Thrombolysis (Procedure) ######################################
            
            thrombolysis_done = safe_get_bool(raw, "thrombolysis", required=True) # Check if thrombolysis done boolean is present in raw data, not required
            procedure_thrombolysis_ref = get_uuid()
            thrombolysis_location_ref = None
            bolus_timestamp = None

            if thrombolysis_done is True:
                bolus_timestamp = safe_get(raw, "bolus_timestamp", required=True) # Check if bolus timestamp is present in raw data, not required
                thrombolysis_location_value = safe_get(raw, "ivt_application_department", required=True) # Check if thrombolysis location is present in raw data, not required
                thrombolysis_location_ref = get_uuid()

                if thrombolysis_location_value is not None:
                    thrombolysis_location = build_location(Locations.by_id(thrombolysis_location_value)) # Build Location resource for thrombolysis location
                    entries.append(BundleEntry(fullUrl=thrombolysis_location_ref, resource=thrombolysis_location, request=BundleEntryRequest(method="POST", url="Location")))
                
                medication_thrombolysis = safe_get(raw, "ivt_drug", required=True) # Check if thrombolysis medication is present in raw data, not required
                ivt_drug_dose = safe_get(raw, "ivt_drug_dose", required=True) # Check if thrombolysis medication dose is present in raw data, not required

        ############################ 2.2.2.3 Thombolysis administration (MedicationAdministration) ######################################
                
                if medication_thrombolysis is not None and ivt_drug_dose is not None:
                    medicationAdministration_thrombolysis_ref = get_uuid()
                    medicationAdministration_thrombolysis = build_medicationAdministration(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                condition_ref=condition_stroke_ref,
                                                                                procedure_ref=procedure_thrombolysis_ref,
                                                                                medication= Medications.by_id(medication_thrombolysis), # Obtain thrombolysis medication from raw data and convert to Medications enum, field not required
                                                                                medication_timestamp=bolus_timestamp,
                                                                                dose = int(ivt_drug_dose))    # Convert dose to integer and pass to build_medicationAdministration
                    entries.append(BundleEntry(fullUrl=medicationAdministration_thrombolysis_ref, resource=medicationAdministration_thrombolysis, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))

        ############################ 2.2.2.4 Thombolysis administration reversal (MedicationAdministration) ######################################

                medicationAdministration_reversal = safe_get(raw, "ivt_antidote_given", required = False) # Check if thrombolysis reversal medication administration is present in raw data, not required

                if medicationAdministration_reversal is not None:
                    anticoagulant_reversal_timestamp = safe_get(raw, "anticoagulant_reversal_timestamp", required=False) # Check if thrombolysis reversal medication administration timestamp is present in raw data, not required
                    if anticoagulant_reversal_timestamp is None:
                        medicationAdministration_thrombolysis_reversal = build_medicationAdministration(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                condition_ref=condition_stroke_ref,
                                                                                procedure_ref=procedure_thrombolysis_ref,
                                                                                medication= Medications.ANTICOAGULANT_REVERSAL, # Use a specific medication for thrombolysis reversal, can be extended to use different medications if needed
                                                                                medication_timestamp=anticoagulant_reversal_timestamp,
                                                                                dose = None)    # Dose is not applicable for reversal medication, pass None
                        entries.append(BundleEntry(fullUrl=medicationAdministration_reversal_ref, resource=medicationAdministration_thrombolysis_reversal, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))
            else:
                no_thrombolysis_reason_id = safe_get(raw, "no_thrombolysis_reason", required=True) # Check if no thrombolysis reason is present in raw data, not required
            
            procedure_thrombolysis = build_thrombolysis_procedure(patient_ref=patient_ref,
                                                                    encounter_ref=encounter_ref,
                                                                    condition_ref=condition_stroke_ref,
                                                                    location_ref = thrombolysis_location_ref,
                                                                    thrombolysis=thrombolysis_done,
                                                                    post_acute_care=False,
                                                                    no_thrombolysis_reason_id=NoThrombolysisReason.by_id(no_thrombolysis_reason_id) if no_thrombolysis_reason_id else None,
                                                                    bolus_timestamp=bolus_timestamp) # Build Procedure resource for thrombolysis using patient_ref, encounter_ref and stroke diagnosis reference, field not required         
            entries.append(BundleEntry(fullUrl=procedure_thrombolysis_ref, resource=procedure_thrombolysis, request=BundleEntryRequest(method="POST", url="Procedure")))
        
        ######################## 2.2.2.5 Mechanical thrombectomy (Procedure) ######################################

        thrombectomy_done = safe_get_bool(raw, "thrombectomy", required=False) # Check if mechanical thrombectomy done boolean is present in raw data, not required
        procedure_thrombectomy_ref = get_uuid()

        if thrombectomy_done is not None and thrombectomy_done is False:
            no_thrombectomy_reason_id = safe_get(raw, "no_thrombectomy_reason", required=False) # Check if no mechanical thrombectomy reason is present in raw data, not required
            procedure_thrombectomy = build_thrombectomy_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                condition_ref=condition_stroke_ref,
                                                                thrombectomy=thrombectomy_done,
                                                                post_acute_care=False,
                                                                no_thrombectomy_reason_id=NoThrombectomyReason.by_id(no_thrombectomy_reason_id)) # Build Procedure resource for mechanical thrombectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
            entries.append(BundleEntry(fullUrl=procedure_thrombectomy_ref, resource=procedure_thrombectomy, request=BundleEntryRequest(method="POST", url="Procedure")))
        elif thrombectomy_done is not None and thrombectomy_done is True:
            groin_puncture_timestamp = safe_get(raw, "puncture_timestamp", required=True) # Check if groin puncture timestamp is present in raw data, not required
            
            mtici_score = safe_get(raw, "mtici_score", required=False) # Check if mTICI score is present in raw data, not required
            if mtici_score is not None:
                observation_mtici = build_observation_mtici_score(patient_ref=patient_ref,
                                                            encounter_ref=encounter_ref,
                                                            mtici_score=MTiciScore.by_id(mtici_score)) # Build Observation resource for mTICI score using patient_ref, encounter_ref and mtici_score from raw data, field not required
                observation_mtici_ref = get_uuid()
                entries.append(BundleEntry(fullUrl=observation_mtici_ref, resource=observation_mtici, request=BundleEntryRequest(method="POST", url="Observation")))

            reperfusion_timestamp = safe_get(raw, "reperfusion_timestamp", required=False) # Check if reperfusion timestamp is present in raw data, not required
            procedure_thrombectomy = build_thrombectomy_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                condition_ref=condition_stroke_ref,
                                                                thrombectomy=thrombectomy_done,
                                                                puncture_timestamp=groin_puncture_timestamp,
                                                                reperfusion_timestamp=reperfusion_timestamp,
                                                                mt_complications_dissection= safe_get_bool(raw,"mt_complications_dissection", required=False), # Build Procedure resource for mechanical thrombectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                mt_complications_embolism=safe_get_bool(raw,"mt_complications_embolism", required=False), # Build Procedure resource for mechanical thrombectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                mt_complications_hematoma=safe_get_bool(raw,"mt_complications_hematoma", required=False), # Build Procedure resource for mechanical thrombectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                mt_complications_other=safe_get_bool(raw,"mt_complications_other", required=False), # Build Procedure resource for mechanical thrombectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                mt_complications_perforation=safe_get_bool(raw,"mt_complications_perforation", required=False), # Build Procedure resource for mechanical thrombectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                post_acute_care=False) # Build Procedure resource for mechanical thrombectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
            entries.append(BundleEntry(fullUrl=procedure_thrombectomy_ref, resource=procedure_thrombectomy, request=BundleEntryRequest(method="POST", url="Procedure")))

            diagnostic_report_thrombectomy = build_mechanical_thrombectomy_diagnostic_report(patient_ref=patient_ref,
                                                                                        encounter_ref=encounter_ref,
                                                                                        thrombectomy_procedure_ref=procedure_thrombectomy_ref,
                                                                                        mtici_score_ref=observation_mtici_ref) # Build DiagnosticReport resource for mechanical thrombectomy using patient_ref, encounter_ref and references to thrombectomy procedure and mTICI score, field not required
            diagnostic_report_thrombectomy_ref = get_uuid()
            entries.append(BundleEntry(fullUrl=diagnostic_report_thrombectomy_ref, resource=diagnostic_report_thrombectomy, request=BundleEntryRequest(method="POST", url="DiagnosticReport")))
        
        ####################### 2.2.4 Arterial occlusion (Observation + DiagnosticReport) ######################################
            
        occlusion_found = safe_get_bool(raw, "occlusion_found", required=False) # Check if arterial occlusion found boolean is present in raw data, not required
        observation_ref_list = []
        if occlusion_found is not None and occlusion_found is True:
            bodystructures_list = get_occlusions_list(raw)
            
            for bodystructure in bodystructures_list:
                bodystructure_ref= get_uuid()
                bodystructure = build_bodyStructure(patient_ref=patient_ref,
                                                    structure=bodystructure[0], # Get occluded artery structure from bodystructure tuple, field not required
                                                     laterality=bodystructure[1]) # Build BodyStructure resource for arterial occlusion using patient_ref, encounter_ref and bodystructure from raw data, field not required
                observation_occlusion = build_observation_occluded_artery(patient_ref=patient_ref,
                                                                    encounter_ref=encounter_ref,
                                                                    body_structure_ref=bodystructure_ref) # Build Observation resource for arterial occlusion using patient_ref, encounter_ref and bodystructure from raw data, field not required
                observation_ref= get_uuid()
                observation_ref_list.append(observation_ref)
                entries.append(BundleEntry(fullUrl=bodystructure_ref, resource=bodystructure, request=BundleEntryRequest(method="POST", url="BodyStructure")))
                entries.append(BundleEntry(fullUrl=observation_ref, resource=observation_occlusion, request=BundleEntryRequest(method="POST", url="Observation")))
            
        ############################# 2.1.3 DiagnosticReport generated from brain imaging results ######################################
        diagnostic_report_imaging_id = get_uuid()
        if imaging_type is not None:
            diagnostic_report_imaging = build_imaging_diagnostic_report(patient_ref = patient_ref,
                                                                        encounter_ref= encounter_ref,
                                                                        imaging_type = ImagingType.by_id(imaging_type), # Obtain imaging type from raw data and convert to ImagingType enum, field not required
                                                                        imaging_results_ref = observation_ref_list) # Placeholder for imaging results, can be used for extensions if needed
        
            entries.append(BundleEntry(fullUrl=diagnostic_report_imaging_id, resource=diagnostic_report_imaging, request=BundleEntryRequest(method="POST", url="DiagnosticReport")))

        
        ############################ 2.2.3 Intracerebral hemorrhage (Condition) ######################################

        if stroke_type == StrokeType.INTRACEREBRAL_HEMORRHAGE:
            bleeding_volume = safe_get(raw, "bleeding_volume", required=True) # Check if intracerebral hemorrhage volume is present in raw data, required if stroke type is intracerebral hemorrhage
            if bleeding_volume is not None:
                observation_bleeding_volume = build_observation_blood_volume(patient_ref=patient_ref, 
                                                                            encounter_ref=encounter_ref, 
                                                                            bleeding_volume=bleeding_volume,
                                                                            post_acute_care=False) # Build Observation resource for intracerebral hemorrhage bleeding volume using patient_ref, encounter_ref and bleeding_volume from raw data, field required if stroke type is intracerebral hemorrhage
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_bleeding_volume, request=BundleEntryRequest(method="POST", url="Observation")))

                anticoagulant_reversal = safe_get(raw, "anticoagulant_reversal", required = False) # Check if thrombolysis reversal medication administration is present in raw data, not required
                
                if anticoagulant_reversal is not None:
                    anticoagulant_reversal_timestamp = safe_get(raw, "anticoagulant_reversal_timestamp", required=False) # Check if thrombolysis reversal medication administration timestamp is present in raw data, not required
                    if anticoagulant_reversal_timestamp is not None:
                        medicationAdministration_anticoagulant_reversal = build_medicationAdministration(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                condition_ref=condition_stroke_ref,
                                                                                procedure_ref=None, # No procedure reference for anticoagulant reversal in intracerebral hemorrhage, can be extended to reference a specific procedure if needed
                                                                                medication= Medications.ANTICOAGULANT_REVERSAL, # Use a specific medication for thrombolysis reversal, can be extended to use different medications if needed
                                                                                dose = None, # Dose is not applicable for reversal medication, pass None
                                                                                medication_timestamp=anticoagulant_reversal_timestamp) # Pass anticoagulant reversal timestamp to build_medicationAdministration
                        entries.append(BundleEntry(fullUrl=get_uuid(), resource=medicationAdministration_anticoagulant_reversal, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))

                    no_anticoagulant_reversal_reason = safe_get(raw, "no_anticoagulant_reversal_reason", required=False) # Check if no anticoagulant reversal reason is present in raw data, not required
                    if no_anticoagulant_reversal_reason is not None:
                        medicationAdministration_anticoagulant_reversal_no_reason = build_medicationAdministration(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                condition_ref=condition_stroke_ref,
                                                                                procedure_ref=None, # No procedure reference for anticoagulant reversal in intracerebral hemorrhage, can be extended to reference a specific procedure if needed
                                                                                medication= Medications.ANTICOAGULANT_REVERSAL, # Use a specific medication for thrombolysis reversal, can be extended to use different medications if needed
                                                                                dose = None, # Dose is not applicable for reversal medication, pass None
                                                                                no_medication_reason=NotMedicationReason.by_id(no_anticoagulant_reversal_reason)) # Pass no anticoagulant reversal reason to build_medicationAdministration

                        entries.append(BundleEntry(fullUrl=get_uuid(), resource=medicationAdministration_anticoagulant_reversal_no_reason, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))


            ich_treatment_any = safe_get_bool(raw, "ich_treatment_any", required=True) # Check if any treatment for intracerebral hemorrhage was given, not required
            if ich_treatment_any is not None:
                ich_treatment_evacuation_timestamp = safe_get(raw, "ich_treatment_evacuation_timestamp", required=True) # Check if intracerebral hemorrhage evacuation treatment timestamp is present in raw data, not required
                if ich_treatment_evacuation_timestamp is not None:
                    procedure_ich_treatment_ref = get_uuid()
                    procedure_ich_treatment = build_ich_treatment_procedure(patient_ref=patient_ref,
                                                                        encounter_ref=encounter_ref,
                                                                        condition_ref=condition_stroke_ref,
                                                                        ich_treatment_any=ich_treatment_any,
                                                                        ich_treatment_craniectomy=safe_get_bool(raw, "ich_treatment_craniectomy", required=False), # Build Procedure resource for intracerebral hemorrhage treatment using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                        ich_treatment_hematoma_evacuation=safe_get_bool(raw, "ich_treatment_hematoma_evacuation", required=False), # Build Procedure resource for intracerebral hemorrhage treatment using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                        ich_treatment_stereotactic_aspiration=safe_get_bool(raw, "ich_treatment_stereotactic_aspiration", required=False), # Build Procedure resource for intracerebral hemorrhage treatment using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                        ich_treatment_open_craniectomy=safe_get_bool(raw, "ich_treatment_open_craniectomy", required=False),
                                                                        ich_treatment_ventricular_drainage=safe_get_bool(raw, "ich_treatment_ventricular_drainage", required=False),
                                                                        ich_treatment_evacuation_timestamp=ich_treatment_evacuation_timestamp,
                                                                        no_ich_treatment_reason= ProcedureNotDoneReason.by_id(safe_get(raw, "no_ich_treatment_reason", required=False))) # Build Procedure resource for intracerebral hemorrhage treatment using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                for proc in procedure_ich_treatment:
                    entries.append(BundleEntry(fullUrl=procedure_ich_treatment_ref, resource=proc, request=BundleEntryRequest(method="POST", url="Procedure")))
        ########################### 2.2.4 Subarachnoid hemorrhage (Condition) ######################################
        if stroke_type == StrokeType.SUBARACHNOID_HEMORRHAGE:
            hunt_hess_score = safe_get(raw, "hunt_hess_score", required=True) # Check if Hunt and Hess score is present in raw data, required if stroke type is subarachnoid hemorrhage
            
            if hunt_hess_score is not None:
                observation_hunt_hess_score = build_observation_hunt_hess_score(patient_ref=patient_ref, 
                                                                            encounter_ref=encounter_ref, 
                                                                            hunt_hess_score=int(hunt_hess_score)) # Build Observation resource for Hunt and Hess score using patient_ref, encounter_ref and hunt_hess_score from raw data, field required if stroke type is subarachnoid hemorrhage
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_hunt_hess_score, request=BundleEntryRequest(method="POST", url="Observation")))
            
            sah_treatment_any = safe_get_bool(raw, "sah_treatment_any", required=True) # Check if any treatment for subarachnoid hemorrhage was given, not required
            if sah_treatment_any: # Check if any treatment for subarachnoid hemorrhage was given, not required
                procedure_sah_treatment = build_sah_treatment_procedure(patient_ref=patient_ref,
                                                                        encounter_ref=encounter_ref,
                                                                        condition_ref=condition_stroke_ref,
                                                                        sah_treatment_any=sah_treatment_any,
                                                                        sah_treatment_clipping=safe_get_bool(raw, "sah_treatment_clipping", required=False), # Build Procedure resource for subarachnoid hemorrhage treatment using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                        sah_treatment_coiling=safe_get_bool(raw, "sah_treatment_coiling", required=False),
                                                                        sah_treatment_craniectomy=safe_get_bool(raw, "sah_treatment_craniectomy", required=False),
                                                                        sah_treatment_drainage=safe_get_bool(raw, "sah_treatment_drainage", required=False),
                                                                        sah_treatment_other=safe_get_bool(raw, "sah_treatment_other", required=False)) # Build Procedure resource for subarachnoid hemorrhage treatment using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                for proc in procedure_sah_treatment:
                    entries.append(BundleEntry(fullUrl=get_uuid(), resource=proc, request=BundleEntryRequest(method="POST", url="Procedure")))

            nimodipine_administration = safe_get_bool(raw, "nimodipine", required= True) # Check if nimodipine administration is present in raw data, not required
            nimodipine_administration_timing = safe_get(raw, "nimodipine_timing", required=True) # Check if nimodipine administration timestamp is present in raw data, not required
            if nimodipine_administration is not None and nimodipine_administration_timing is not None:
                medicationAdministration_nimodipine = build_medicationAdministration_nimopidine(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                condition_ref=condition_stroke_ref,
                                                                                procedure_ref=None, # No procedure reference for nimodipine administration, can be extended to reference a specific procedure if needed
                                                                                medication_range_timing=PostAcuteCare.by_id(nimodipine_administration_timing)) # Pass nimodipine administration timestamp to build_medicationAdministration
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=medicationAdministration_nimodipine, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))
        ############################ 2.2.5 Cerebral venous thrombosis (Condition) ######################################
        if stroke_type == StrokeType.CEREBRAL_VENOUS_THROMBOSIS:
            cvt_treatment_any = safe_get_bool(raw, "cvt_treatment_any", required=True) # Check if any treatment for cerebral venous thrombosis was given, not required
            if cvt_treatment_any:
                procedure_cvt_treatment = build_cvt_treatment_procedure(patient_ref=patient_ref,
                                                                        encounter_ref=encounter_ref,
                                                                        condition_ref=condition_stroke_ref,
                                                                        cvt_treatment_any=cvt_treatment_any,
                                                                        cvt_treatment_anticoagulation=safe_get_bool(raw, "cvt_treatment_anticoagulation", required=False), # Build Procedure resource for cerebral venous thrombosis treatment using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                                                                        cvt_treatment_thrombolysis=safe_get_bool(raw, "cvt_treatment_thrombolysis", required=False),
                                                                        cvt_treatment_neurosurgery=safe_get_bool(raw, "cvt_treatment_neurosurgery", required=False),
                                                                        cvt_treatment_thrombectomy=safe_get_bool(raw, "cvt_treatment_thrombectomy", required=False),
                )
                for proc in procedure_cvt_treatment:
                    entries.append(BundleEntry(fullUrl=get_uuid(), resource=proc, request=BundleEntryRequest(method="POST", url="Procedure")))

        ############################# 2.2.6 Stroke Mimics (Condition) ######################################
        procedure_thrombolysis_ref = get_uuid()
        if stroke_type == StrokeType.STROKE_MIMICS:
        ########################### 2.2.6.1 Thrombolysis (Procedure) ######################################
            thrombolysis_done = safe_get_bool(raw, "thrombolysis", required=True) # Check if thrombolysis done boolean is present in raw data, not required
            thrombolysis_location_ref = None
            bolus_timestamp = None
            no_thrombolysis_reason_id = None

            if thrombolysis_done is True:
                bolus_timestamp = safe_get(raw, "bolus_timestamp", required=True) # Check if bolus timestamp is present in raw data, not required
                thrombolysis_location_value = safe_get(raw, "ivt_application_department", required=True) # Check if thrombolysis location is present in raw data, not required
                thrombolysis_location_ref = get_uuid()

                if thrombolysis_location_value is not None:
                    thrombolysis_location = build_location(Locations.by_id(thrombolysis_location_value)) # Build Location resource for thrombolysis location
                    entries.append(BundleEntry(fullUrl=thrombolysis_location_ref, resource=thrombolysis_location, request=BundleEntryRequest(method="POST", url="Location")))

                medication_thrombolysis = safe_get(raw, "ivt_drug", required=True) # Check if thrombolysis medication is present in raw data, not required
                ivt_drug_dose = safe_get(raw, "ivt_drug_dose", required=True) # Check if thrombolysis medication dose is present in raw data, not required

        ############################ 2.2.6.2 Thombolysis administration (MedicationAdministration) ######################################
                
                if medication_thrombolysis is not None and ivt_drug_dose is not None:
                    if bolus_timestamp is not None:
                        medicationAdministration_thrombolysis = build_medicationAdministration(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                condition_ref=condition_stroke_ref,
                                                                                procedure_ref=procedure_thrombolysis_ref,
                                                                                medication= Medications.by_id(medication_thrombolysis), # Obtain thrombolysis medication from raw data and convert to Medications enum, field not required
                                                                                dose = int(ivt_drug_dose),
                                                                                medication_timestamp=bolus_timestamp)    # Convert dose to integer and pass to build_medicationAdministration
                        entries.append(BundleEntry(fullUrl=get_uuid(), resource=medicationAdministration_thrombolysis, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))

        ############################ 2.2.6.3 Thombolysis administration reversal (MedicationAdministration) ######################################

                medicationAdministration_reversal = safe_get(raw, "ivt_antidote_given", required = False) # Check if thrombolysis reversal medication administration is present in raw data, not required
                
                if medicationAdministration_reversal is not None:
                    medicationAdministration_thrombolysis_reversal = build_medicationAdministration(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                condition_ref=condition_stroke_ref,
                                                                                procedure_ref=procedure_thrombolysis_ref,
                                                                                medication= Medications.ANTICOAGULANT_REVERSAL, # Use a specific medication for thrombolysis reversal, can be extended to use different medications if needed
                                                                                dose = None)    # Dose is not applicable for reversal medication, pass None
                    entries.append(BundleEntry(fullUrl=get_uuid(), resource=medicationAdministration_thrombolysis_reversal, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))
            else:
                no_thrombolysis_reason_id = safe_get(raw, "no_thrombolysis_reason", required=False) # Check if no thrombolysis reason is present in raw data, not required
            
            procedure_thrombolysis = build_thrombolysis_procedure(patient_ref=patient_ref,
                                                                    encounter_ref=encounter_ref,
                                                                    condition_ref=condition_stroke_ref,
                                                                    location_ref = thrombolysis_location_ref,
                                                                    thrombolysis=thrombolysis_done,
                                                                    post_acute_care=False,
                                                                    no_thrombolysis_reason_id=NoThrombolysisReason.by_id(no_thrombolysis_reason_id) if no_thrombolysis_reason_id else None,
                                                                    bolus_timestamp=bolus_timestamp) # Build Procedure resource for thrombolysis using patient_ref, encounter_ref and stroke diagnosis reference, field not required         
            entries.append(BundleEntry(fullUrl=procedure_thrombolysis_ref, resource=procedure_thrombolysis, request=BundleEntryRequest(method="POST", url="Procedure")))
        
##################################### 3. Post-acute care data #####################################

    post_acute_care = safe_get_bool(raw, "post_acute_care", required=True) # Check if post-acute care boolean is present in raw data, not required  
    if post_acute_care is not None and post_acute_care:
        ############################ 3.1 Post-acute, patient ventilated (Observation) ######################################
        patient_ventilated = safe_get_bool(raw, "patient_ventilated", required=False, default=False) # Check if patient ventilated boolean is present in raw data, not required
        observation_ventilated = build_observation_patient_ventilated(patient_ref=patient_ref, 
                                                                      encounter_ref=encounter_ref, 
                                                                      ventilated=patient_ventilated)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_ventilated, request=BundleEntryRequest(method="POST", url="Observation")))

        recanalization_done = safe_get_bool(raw,"cvt_treatment_thrombolysis", required=False) or safe_get_bool(raw, "cvt_treatment_thrombectomy", required=False) # Check if recanalization treatment for cerebral venous thrombosis boolean is present in raw data, not required
        procedure_post_imaging_ref = get_uuid()
        neurosurgery_done = safe_get_bool(raw, "cvt_treatment_neurosurgery", required=False) # Check if neurosurgery for cerebral venous thrombosis treatment boolean is present in raw data, not required
        if neurosurgery_done is True: # If neurosurgery for cerebral venous thrombosis treatment was done, check if post-neurosurgery imaging type is present in raw data and build Procedure resource for post-neurosurgery imaging
            post_imaging_type = PostNeurosurgeryImaging.by_id(safe_get(raw, "post_neurosurgery_imaging", required=False)) # Check if post-neurosurgery imaging type is present in raw data, not required
            if post_imaging_type is not None: # If neurosurgery for cerebral venous thrombosis treatment was done, build Procedure resource for neurosurgery
                procedure_imaging_neurosurgery = build_post_neurosurgery_imaging_procedure(patient_ref=patient_ref,
                                                                            encounter_ref=encounter_ref,
                                                                            condition_ref=condition_stroke_ref,
                                                                            post_neurosurgery_imaging_done=post_imaging_type)
                entries.append(BundleEntry(fullUrl=procedure_post_imaging_ref, resource=procedure_imaging_neurosurgery, request=BundleEntryRequest(method="POST", url="Procedure")))

            elif recanalization_done:
                post_imaging_type = PostRecanalizationImaging.by_id(safe_get(raw, "post_recanalization_imaging", required=False)) # Check if post-recanalization imaging type is present in raw data, not required
                if post_imaging_type is not None: # If post-recanalization imaging type is present in raw data, build Procedure resource for post-recanalization imaging
                    procedure_imaging_neurosurgery = build_post_recanalization_imaging_procedure(patient_ref=patient_ref,
                                                                            encounter_ref=encounter_ref,
                                                                            condition_ref=condition_stroke_ref,
                                                                            post_recanalization_imaging_done=post_imaging_type) # Build Procedure resource for post-recanalization imaging using patient_ref, encounter_ref and stroke diagnosis reference, with post_recanalization_imaging_done set to False since neurosurgery was not done but recanalization was done, field not required
                    entries.append(BundleEntry(fullUrl=procedure_post_imaging_ref, resource=procedure_imaging_neurosurgery, request=BundleEntryRequest(method="POST", url="Procedure")))
            
            post_imaging_type = PostRecanalizationImaging.by_id(safe_get(raw, "post_recanalization_imaging", required=False)) # Check if post-recanalization imaging type is present in raw data, not required
            post_treatment_findings = safe_get_bool(raw, "post_treatment_findings_any", required=False)
            if post_treatment_findings is not None: 
                if post_treatment_findings is True:
                    obs_ref_list = []
                    observation_finding_post_ivt_mt = build_observation_finding_post_ivt_mt(patient_ref=patient_ref,
                                                                                   encounter_ref=encounter_ref,
                                                                                   post_treatment_findings_any=safe_get_bool(raw, "post_treatment_findings_any", required=False), # Check if any post-treatment findings boolean is present in raw data, not required
                                                                                   post_treatment_brain_infarct=safe_get_bool(raw, "post_treatment_brain_infarct", required=False), # Check if post-treatment brain infarct boolean is present in raw data, not required
                                                                                   post_treatment_remote_bleeding=safe_get_bool(raw, "post_treatment_remote_bleeding", required=False), # Check if post-treatment remote bleeding boolean is present in raw data, not required
                                                                                   post_treatment_hemorrhagic_transformation=safe_get_bool(raw, "post_treatment_hemorrhagic_transformation", required=False), # Check if post-treatment hemorrhagic transformation boolean is present in raw data, not required
                                                                                   hemorrhagic_transformation_type=safe_get(raw, "hemorrhagic_transformation_type", required=False), # Check if hemorrhagic transformation type is present in raw data, not required
            )
                    for obs in observation_finding_post_ivt_mt:
                        obs_ref = get_uuid()
                        obs_ref_list.append(obs_ref)
                        entries.append(BundleEntry(fullUrl=obs_ref, resource=obs, request=BundleEntryRequest(method="POST", url="Observation")))
            if post_imaging_type is not None:
                diagnostic_report_post_neurosurgery = build_ct_mr_after_ivt_diagnostic_report(patient_ref=patient_ref,
                                                                                        encounter_ref=encounter_ref,
                                                                                        observation_ref=[obs_ref_list],
                                                                                        imaging_type=post_imaging_type) # Build DiagnosticReport resource for post-neurosurgery imaging using patient_ref, encounter_ref and post-neurosurgery imaging type from raw data, field not required
            
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=diagnostic_report_post_neurosurgery, request=BundleEntryRequest(method="POST", url="DiagnosticReport")))

        # if recanalization_done: # If recanalization treatment for cerebral venous thrombosis was done, build Procedure resource for recanalization
        #     procedure_imaging_recanalization = build_cvt_recanalization_procedure(patient_ref=patient_ref,
        #                                                                 encounter_ref=encounter_ref,
        #                                                                 condition_ref=condition_stroke_ref,
        #                                                                 cvt_recanalization_done=recanalization_done)
        #     entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_imaging_recanalization, request=BundleEntryRequest(method="POST", url="Procedure")))

        ############################ 3.2 Post-acute, craniectomy (Procedure) ######################################

        craniectomy_done = safe_get_bool(raw, "craniectomy", required=False, default=False) # Check if craniectomy done boolean is present in raw data, not required
        if craniectomy_done:
            procedure_craniectomy = build_craniectomy_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                condition_ref=condition_stroke_ref,
                                                                craniectomy_performed=craniectomy_done) 
            # Build Procedure resource for craniectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required                    )
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_craniectomy, request=BundleEntryRequest(method="POST", url="Procedure")))
        ############################ 3.3 Post-acute, atrial fibrillation/flutter (Observation) ######################################
        atrial_fibrillation_or_flutter = safe_get(raw, "atrial_fibrillation_or_flutter", required=False) # Check if atrial fibrillation or flutter boolean is present in raw data, not required 
        if atrial_fibrillation_or_flutter is not None:
            observation_af_or_f =build_observation_Af_or_F(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        atrial_fibrillation_or_flutter=AtrialFibrillationOrFlutter.by_id(str(atrial_fibrillation_or_flutter))) # Build Observation resource for atrial fibrillation or flutter using patient_ref, encounter_ref and atrial fibrillation or flutter boolean from raw data, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_af_or_f, request=BundleEntryRequest(method="POST", url="Observation")))
        ############################ 3.4 Carotid artery imaging (Procedure) ######################################
        carotid_arteries_imaging = safe_get_bool(raw, "carotid_arteries_imaging", required=False, default=False) # Check if carotid artery imaging boolean is present in raw data, not required
        if carotid_arteries_imaging:
            carotid_stenosis = safe_get_bool(raw, "carotid_stenosis", required=False, default=False)  # Check if carotid stenosis percentage is present in raw data, not required
            carotid_stenosis_level = safe_get(raw, "carotid_stenosis_level", required=False) # Check if carotid stenosis level is present in raw data, not required
            
            carotid_stenosis_observation_ref = get_uuid()
            carotid_stenosis_observation = build_observation_carotid_stenosis(patient_ref=patient_ref,
                                                                            encounter_ref=encounter_ref,
                                                                            carotid_stenosis=carotid_stenosis,
                                                                            carotid_stenosis_level=CarotidStenosisLevel.by_id(carotid_stenosis_level)) # Build Observation resource for carotid stenosis using patient_ref, encounter_ref and carotid stenosis percentage and level from raw data, field not required
            entries.append(BundleEntry(fullUrl=carotid_stenosis_observation_ref, resource=carotid_stenosis_observation, request=BundleEntryRequest(method="POST", url="Observation")))
            diagnostic_report_carotid_ref = get_uuid()
            diagnostic_report_carotid = build_carotid_arteries_imaging_diagnostic_report(patient_ref=patient_ref,
                                                                                        encounter_ref=encounter_ref,
                                                                                        observation_ref=carotid_stenosis_observation_ref
                                                                                        ) # Build DiagnosticReport resource for carotid artery imaging using patient_ref, encounter_ref and carotid artery imaging boolean from raw data, field not required
            entries.append(BundleEntry(fullUrl=diagnostic_report_carotid_ref, resource=diagnostic_report_carotid, request=BundleEntryRequest(method="POST", url="DiagnosticReport")))

            procedure_carotid = build_carotid_imaging_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                diagnostic_report_ref=diagnostic_report_carotid_ref,
                                                                carotid_arteries_imaging_done=carotid_arteries_imaging) # Build Procedure resource for carotid artery imaging using patient_ref, encounter_ref and carotid artery imaging boolean from raw data, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_carotid, request=BundleEntryRequest(method="POST", url="Procedure")))

            carotid_endardectomy_done = safe_get_bool(raw, "carotid_endardectomy", required=False, default=False) # Check if carotid endardectomy boolean is present in raw data, not required
            if carotid_endardectomy_done is not None:
                carotid_endarterectomy_timing = safe_get(raw, "carotid_endardectomy_timing", required=False) # Check if carotid endardectomy timing is present in raw data, not required
                
                procedure_carotid_endardectomy = build_endarterectomy_procedure(patient_ref=patient_ref,
                                                                                encounter_ref=encounter_ref,
                                                                                diagnostic_report_ref=diagnostic_report_carotid_ref,
                                                                                carotid_endarterectomy=carotid_endardectomy_done,
                                                                                carotid_endarterectomy_timing=carotid_endarterectomy_timing) # Build Procedure resource for carotid endardectomy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_carotid_endardectomy, request=BundleEntryRequest(method="POST", url="Procedure")))
            ############################ 3.5 Post Stroke Complications (Condition) ######################################
            highest_sys_bp_post_24h = safe_get(raw, "highest_systolic_pressure_after24h", required=False)
            if highest_sys_bp_post_24h is not None:
                observation_hbp = build_highest_systolic_pressure_after24h_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                highest_systolic_pressure_after24h=highest_sys_bp_post_24h)
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_hbp, request=BundleEntryRequest(method="POST", url="Observation")))
            
            post_stroke_any = safe_get_bool(raw, "post_stroke_any", required=False) # Check if any post-treatment findings are present in raw data, not required
            if post_stroke_any:
                condition_list = build_post_stroke_conditions(patient_ref=patient_ref,
                                                            encounter_ref=encounter_ref,
                                                            post_stroke_any=post_stroke_any,
                                                            post_stroke_dvt=safe_get_bool(raw, "post_stroke_dvt", required=False), # Build Condition resources for post-stroke complications using patient_ref, encounter_ref and post-stroke complication booleans from raw data, field not required
                                                            post_stroke_pneumonia=safe_get_bool(raw, "post_stroke_pneumonia", required=False),
                                                            post_stroke_falling=safe_get_bool(raw, "post_stroke_falling", required=False),
                                                            post_stroke_pressure_sores=safe_get_bool(raw, "post_stroke_pressure_sores", required=False),
                                                            post_stroke_pulmonary_embolism=safe_get_bool(raw, "post_stroke_pulmonary_embolism", required=False),
                                                            post_stroke_urinary_infection=safe_get_bool(raw, "post_stroke_urinary_infection", required=False),
                                                            post_stroke_recurrence=safe_get_bool(raw, "post_stroke_recurrence_or_extension", required=False),
                                                            post_stroke_sepsis=safe_get_bool(raw, "post_stroke_drip_site_sepsis", required=False),
                                                            post_stroke_other=safe_get_bool(raw, "post_stroke_other", required=False))
                for condition in condition_list:
                    entries.append(BundleEntry(fullUrl=get_uuid(), resource=condition, request=BundleEntryRequest(method="POST", url="Condition")))
            ############################# 3.6 Thromboembolism intervention (Procedure) ######################################
            thromboembolism_done = safe_get_bool(raw, "thromboembolism_any", required=True) # Check if any thromboembolism intervention was done, not required
            if thromboembolism_done is not None:
                procedure_thromboembolism = build_vte_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                thromboembolism_procedure=thromboembolism_done,
                                                                vte_gcs=safe_get_bool(raw, "vte_gcs", required=False), # Build Procedure resource for thromboembolism intervention using patient_ref, encounter_ref and thromboembolism intervention booleans from raw data, field not required
                                                                vte_ipc=safe_get_bool(raw, "vte_ipc", required=False),
                                                                vte_lmwh=safe_get_bool(raw, "vte_lmwh", required=False),
                                                                vte_other=safe_get_bool(raw, "vte_other", required=False),
                                                                vte_ufh=safe_get_bool(raw, "vte_ufh", required=False),
                                                                vte_vfp=safe_get_bool(raw, "vte_vfp", required=False),
                                                                vte_warfarin=safe_get_bool(raw, "vte_warfarin", required=False),
                                                                vte_xa_inhibitor=safe_get_bool(raw, "vte_xa_inhibitor", required=False))
                
                for proc in procedure_thromboembolism:
                    entries.append(BundleEntry(fullUrl=get_uuid(), resource=proc, request=BundleEntryRequest(method="POST", url="Procedure")))
        ############################# 3.7 Fever observation (Observation) ######################################
        fever_measurement_observation = build_observation_temp_checks(patient_ref=patient_ref,
                                                          encounter_ref=encounter_ref,
                                                          day_1_fever=safe_get(raw, "day_1_fever_checks", required=False), # Build Observation resource for fever using patient_ref, encounter_ref and temperature check values from raw data, field not required
                                                          day_2_fever=safe_get(raw, "day_2_fever_checks", required=False),
                                                          day_3_fever=safe_get(raw, "day_3_fever_checks", required=False))
        obs_ref_list = []
        for obs in fever_measurement_observation:
            obs_ref = get_uuid()
            obs_ref_list.append(obs_ref)
            entries.append(BundleEntry(fullUrl=obs_ref, resource=obs, request=BundleEntryRequest(method="POST", url="Observation")))
        fever_observation_ref = get_uuid()        
        fever_observation = build_observation_fever(patient_ref=patient_ref,
                                                encounter_ref=encounter_ref,
                                                observation_measurement_ref= obs_ref_list,
                                                fever=safe_get_bool(raw, "fever_diagnosed", required=False)
                                                ) # Build Observation resource for fever using patient_ref, encounter_ref and references to temperature check observations, field not required
        entries.append(BundleEntry(fullUrl=fever_observation_ref, resource=fever_observation, request=BundleEntryRequest(method="POST", url="Observation")))

        
        paracetamol_on_fever = safe_get(raw, "paracetamol_on_fever", required=False) # Check if paracetamol administration for fever boolean is present in raw data, not required
        if paracetamol_on_fever is not None:
            paracetamol_on_fever_timing = safe_get(raw, "paracetamol_on_fever_timing", required=False) # Check if paracetamol administration for fever timing is present in raw data, not required
            if paracetamol_on_fever_timing is not None:
                medicationAdministration_paracetamol = build_medicationAdministration_paracetamol_on_fever(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                fever_ref=fever_observation_ref, # Reference to the fever observation
                                                                medication_range_timing=paracetamol_on_fever_timing) # Pass paracetamol administration timestamp to build_medicationAdministration
                entries.append(BundleEntry(fullUrl=get_uuid(), resource=medicationAdministration_paracetamol, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))
        
        ########################## 3.8 Hyperglycemia observation (Observation) ######################################
        hyperglycemia_measurement_observation = build_observation_hyperglycemia_measurement_checks(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                day_1_hyperglycemia=safe_get(raw, "day_1_hyperglycemia_checks", required=False), # Build Observation resource for hyperglycemia using patient_ref, encounter_ref and glucose check values from raw data, field not required
                                                                day_2_hyperglycemia=safe_get(raw, "day_2_hyperglycemia_checks", required=False),
                                                                day_3_hyperglycemia=safe_get(raw, "day_3_hyperglycemia_checks", required=False))
        obs_ref_list = []
        for obs in hyperglycemia_measurement_observation:
            obs_ref = get_uuid()
            obs_ref_list.append(obs_ref)
            entries.append(BundleEntry(fullUrl=obs_ref, resource=obs, request=BundleEntryRequest(method="POST", url="Observation")))
        
        highest_hyperglycemia_observation_ref = get_uuid()
        highest_hyperglycemia_observation = build_observation_highest_hyperglycemia_value(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        observation_measurement_ref= obs_ref_list,
                                                        highest_hyperglycemia_value=safe_get(raw, "highest_glucose_within48h", required=False)
                                                        ) # Build Observation resource for hyperglycemia using patient_ref, encounter_ref and references to glucose check observations, field not required
        
        entries.append(BundleEntry(fullUrl=highest_hyperglycemia_observation_ref, resource=highest_hyperglycemia_observation, request=BundleEntryRequest(method="POST", url="Observation")))

        glucose_ge10 = safe_get_bool(raw, "glucose_ge10", required=False) # Check if hyperglycemia diagnosed boolean is present in raw data, not required 
        if glucose_ge10 is not None:
            obs_ge10 = build_observation_ge10(patient_ref=patient_ref,
                                            encounter_ref=encounter_ref,
                                            ge10=glucose_ge10)
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=obs_ge10, request=BundleEntryRequest(method="POST", url="Observation")))

        insulin_bool = safe_get_bool(raw, "insulin_on_hyperglycemia", required=False) # Check if insulin administration for hyperglycemia boolean is present in raw data, not required
        if insulin_bool is not None:
            medicationAdministration_insulin_timing = safe_get(raw, "insulin_on_hyperglycemia_timing", required=False) # Check if insulin administration for hyperglycemia timing is present in raw data, not required
            insulin_on_hyperglycemia_medicationAdministration = build_insulin_on_hyperglycemia(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                observation_ref=highest_hyperglycemia_observation_ref, # Reference to the highest hyperglycemia observation
                                                                insulin_timing=InsulinOnHyperglycemiaTiming.by_id(medicationAdministration_insulin_timing)) # Pass insulin administration timestamp to build_medicationAdministration
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=insulin_on_hyperglycemia_medicationAdministration, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))

        ############################# 3.9 Swallowing screening test (Procedure) ######################################
        swallowing_screening_done = safe_get_bool(raw, "swallowing_screening_done", required=False) # Check if swallowing screening test done boolean is present in raw data, not required
        if swallowing_screening_done is not None:
            practitioner_role_ref = get_uuid()
            swallowing_screening_performer = safe_get(raw, "swallowing_screening_performer", required=True) # Check if swallowing screening test performer is present in raw data, not required
            if swallowing_screening_performer is not None:  
                performer = build_practitioner(swallowing_screening_performer) # Build PractitionerRole resource for swallowing screening test performer
                entries.append(BundleEntry(fullUrl=practitioner_role_ref, resource=performer, request=BundleEntryRequest(method="POST", url="Practitioner")))

            swallowing_screening_timing = safe_get(raw, "swallowing_screening_done_timing", required=True) # Check if swallowing screening test timing is present in raw data, not required
            swallowing_screening_type = safe_get(raw, "swallowing_screening_type", required=False) # Check if swallowing screening test type is present in raw data, not required

            procedure_swallowing_screening = build_swallowing_screening_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                practitioner_role_ref=practitioner_role_ref,
                                                                swallowing_screening_done=swallowing_screening_done,
                                                                swallowing_screening_type=swallowing_screening_type,
                                                                swallowing_screening_timing=swallowing_screening_timing) # Build Procedure resource for swallowing screening test using patient_ref, encounter_ref and stroke diagnosis reference, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_swallowing_screening, request=BundleEntryRequest(method="POST", url="Procedure")))

        ######################### 3.10 Rehabilitation/Occupational therapy/Speech therapy (Procedure) ######################################
        physiotherapy_done = safe_get(raw, "physiotherapy", required=False) # Check if physiotherapy done boolean is present in raw data, not required     
        if physiotherapy_done is not None:
            procedure_physiotherapy = build_physioterapy_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                physiotherapy=physiotherapy_done) # Build Procedure resource for physiotherapy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_physiotherapy, request=BundleEntryRequest(method="POST", url="Procedure")))
        occupational_therapy_done = safe_get(raw, "occupational_therapy", required=False) # Check if occupational therapy done boolean is present in raw data, not required
        if occupational_therapy_done is not None:
            procedure_occupational_therapy = build_occupational_therapy_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                occupational_therapy=occupational_therapy_done) # Build Procedure resource for occupational therapy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_occupational_therapy, request=BundleEntryRequest(method="POST", url="Procedure")))
        speech_therapy_done = safe_get(raw, "speech_therapy", required=False) # Check if speech therapy done boolean is present in raw data, not required
        if speech_therapy_done is not None:
            procedure_speech_therapy = build_speech_therapy_procedure(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                speech_therapy=speech_therapy_done) # Build Procedure resource for speech therapy using patient_ref, encounter_ref and stroke diagnosis reference, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=procedure_speech_therapy, request=BundleEntryRequest(method="POST", url="Procedure")))

################################# End Post-acute care data #####################################

################################# 4.Discharge Data ############################################### 

    ############################### 4.1 MRS and NIHSS at discharge (Observation) ######################################
    mrs_at_discharge = safe_get(raw, "discharge_mrs", required=False) # Check if mRS at discharge value is present in raw data, not required
    if mrs_at_discharge is not None:
        mrs_observation = build_observation_mrs(patient_ref =patient_ref,
                                                encounter_ref=encounter_ref,
                                                mrs_score=MRsScore.by_id(mrs_at_discharge),
                                                discharge=True) # Build Observation resource for mRS at discharge using patient_ref, encounter_ref and mRS at discharge value from raw data, field not required
            

        entries.append(BundleEntry(fullUrl=get_uuid(), resource=mrs_observation, request=BundleEntryRequest(method="POST", url="Observation")))

    nihss_at_discharge = safe_get(raw, "discharge_nihss_score", required=False) # Check if NIHSS at discharge value is present in raw data, not required
    if nihss_at_discharge is not None:
        nihss_observation = build_observation_nihss(patient_ref=patient_ref,
                                                encounter_ref=encounter_ref,
                                                value_nihss=nihss_at_discharge,
                                                discharge_nihss=True) # Build Observation resource for NIHSS at discharge using patient_ref, encounter_ref and NIHSS at discharge value from raw data, field not required
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=nihss_observation, request=BundleEntryRequest(method="POST", url="Observation")))

    ################################ 4.2 Treatment at discharge (MedicationRequest) ######################################
    
    discharge_any_med = safe_get_bool(raw, "discharge_any_medication", required=False) # Check if any medication at discharge boolean is present in raw data, not required
    if discharge_any_med is not None:
        if discharge_any_med:
            meds = get_on_discharge_medications(raw) # Obtain list of medications prescribed at discharge from raw data, can be empty if no medications prescribed at discharge
        else:
            meds = [Medications.NONE_MEDICATION]

        for med_request in build_on_discharge_medicationRequest_profile(patient_ref = patient_ref,
                                                                        encounter_ref=encounter_ref,
                                                                        on_discharge_meds=meds): # Build MedicationRequest resources for medications prescribed at discharge using patient_ref, encounter_ref and list of medications prescribed at discharge from raw data, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=med_request, request=BundleEntryRequest(method="POST", url="MedicationRequest")))

    ################################## 4.3 Follow-up appointment (Appointment) ######################################
    stroke_management_appointment = safe_get(raw, "stroke_management_appointment", required=False) # Check if follow-up appointment boolean is present in raw data, not required
    if stroke_management_appointment is not None:
        stroke_appointment = build_follow_up_appointment(patient_ref=patient_ref,
                                                        management_appointment= ManagementAppointment.by_id(stroke_management_appointment)) # Build Appointment resource for follow-up appointment using patient_ref, encounter_ref and follow-up appointment boolean from raw data, field not required
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=stroke_appointment, request=BundleEntryRequest(method="POST", url="Appointment")))
    

    ################################# 4.4 Discharge Systolic Blood Pressure (Observation) ######################################
    discharge_systolic_bp = safe_get(raw, "discharge_systolic_pressure", required=False) # Check if discharge systolic blood pressure value is present in raw data, not required
    if discharge_systolic_bp is not None:
        discharge_systolic_bp_observation = build_observation_vital_signs(patient_ref=patient_ref,
                                                                                    encounter_ref=encounter_ref,
                                                                                    systolic_pressure=discharge_systolic_bp,
                                                                                    diastolic_pressure=None,
                                                                                    timing=AssessmentContext.DISCHARGE_OR_7_DAYS) # Build Observation resource for discharge systolic blood pressure using patient_ref, encounter_ref and discharge systolic blood pressure value from raw data, field not required
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=discharge_systolic_bp_observation, request=BundleEntryRequest(method="POST", url="Observation")))

    discharge_glucose = safe_get(raw, "discharge_glucose", required=False) # Check if discharge glucose value is present in raw data, not required
    if discharge_glucose is not None:
        discharge_glucose_observation = build_observation_glucose(patient_ref=patient_ref,
                                                                    encounter_ref=encounter_ref,
                                                                    glucose=discharge_glucose,
                                                                    timing=AssessmentContext.DISCHARGE_OR_7_DAYS) # Build Observation resource for discharge glucose using patient_ref, encounter_ref and discharge glucose value from raw data, field not required
        
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=discharge_glucose_observation, request=BundleEntryRequest(method="POST", url="Observation")))


################################### End of discharge data #####################################

################################### 5. Follow-up data ######################################

    ########################### 5.1 Three-month follow-up contact mode (Observation) ######################################
    
    three_m_mode_contact = safe_get(raw, "three_m_mode_contact", required=False) # Check if 3-month follow-up contact mode is present in raw data, not required
    if three_m_mode_contact is not None:
        three_m_mode_contact_observation = build_observation_three_month_contact_mode(patient_ref=patient_ref,
                                                                    encounter_ref=encounter_ref,
                                                                    three_month_contact_mode=ThreeMonthContactMode.by_id(three_m_mode_contact) # Build Observation resource for 3-month follow-up contact mode using patient_ref, encounter_ref and 3-month follow-up contact mode value from raw data, field not required
                                                                    )
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=three_m_mode_contact_observation, request=BundleEntryRequest(method="POST", url="Observation")))

    ########################## 5.2 Three-month mRS (Observation) ######################################
        three_m_mrs = safe_get(raw, "three_m_mrs", required=False) # Check if 3-month mRS value is present in raw data, not required
        if three_m_mrs is not None:
            three_m_mrs_observation = build_observation_mrs(patient_ref=patient_ref,
                                                            encounter_ref=encounter_ref,
                                                            mrs_score=MRsScore.by_id(three_m_mrs),
                                                            threem=True) # Build Observation resource for 3-month mRS using patient_ref, encounter_ref and 3-month mRS value from raw data, field not required
            entries.append(BundleEntry(fullUrl=get_uuid(), resource=three_m_mrs_observation, request=BundleEntryRequest(method="POST", url="Observation")))



################################# 6. Timing specific metrics (KPis) ######################################

    door_to_needle_time = safe_get(raw, "door_to_needle", required=False)
    if door_to_needle_time is not None:
        observation_d2n = build_timing_d2n_observation(patient_ref=patient_ref,
                                    encounter_ref=encounter_ref,
                                    procedure_ref=procedure_thrombolysis_ref,
                                    door_to_needle_time=door_to_needle_time) # Build Observation resource for door-to-needle time using patient_ref, encounter_ref and door-to-needle time value from raw data, field not required
    
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2n, request=BundleEntryRequest(method="POST", url="Observation")))

    door_to_needle_le45 = safe_get_bool(raw, "door_to_needle_le45", required=False)
    if door_to_needle_le45 is not None:
        observation_d2n_le45 = build_timing_d2n_le45_observation(patient_ref=patient_ref,
                                    encounter_ref=encounter_ref,
                                    procedure_ref=procedure_thrombolysis_ref,
                                    door_to_needle_le45=door_to_needle_le45) # Build Observation resource for door-to-needle time <= 45 minutes using patient_ref, encounter_ref and door-to-needle time <= 45 minutes boolean from raw data, field not required
    
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2n_le45, request=BundleEntryRequest(method="POST", url="Observation")))
    
    door_to_needle_le60 = safe_get_bool(raw, "door_to_needle_le60", required=False)
    if door_to_needle_le60 is not None:
        observation_d2n_le60 = build_timing_d2n_le60_observation(patient_ref=patient_ref,
                                    encounter_ref=encounter_ref,
                                    procedure_ref=procedure_thrombolysis_ref,
                                    door_to_needle_le60=door_to_needle_le60) # Build Observation resource for door-to-needle time <= 60 minutes using patient_ref, encounter_ref and door-to-needle time <= 60 minutes boolean from raw data, field not required
    
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2n_le60, request=BundleEntryRequest(method="POST", url="Observation")))
    door_to_anticoagulant_reversal = safe_get(raw, "door_to_anticoagulant_reversal", required=False)
    if door_to_anticoagulant_reversal is not None:
        observation_d2ar = build_door_to_anticoagulant_reversal_observation(patient_ref=patient_ref,
                                                                            encounter_ref=encounter_ref,
                                                                            medicationAdministration_ref=medicationAdministration_reversal_ref,
                                                                            door_to_anticoagulant_reversal_time=door_to_anticoagulant_reversal)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2ar, request=BundleEntryRequest(method="POST", url="Observation")))

    door_to_discharge = safe_get(raw, "door_to_discharge", required=False)
    if door_to_discharge is not None:
        observation_d2d = build_door_to_discharge_observation(patient_ref=patient_ref,
                                                            encounter_ref=encounter_ref,
                                                            door_to_discharge_time=door_to_discharge)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2d, request=BundleEntryRequest(method="POST", url="Observation")))

    door_to_door = safe_get(raw, "door_to_door", required=False)
    if door_to_door is not None:
        observation_d2d = build_door_to_door_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        procedure_ref = procedure_thrombectomy_ref,
                                                        door_to_door_time=door_to_door)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2d, request=BundleEntryRequest(method="POST", url="Observation")))
    
    door_to_groin = safe_get(raw, "door_to_groin", required=False)
    if door_to_groin is not None:
        observation_d2g = build_timing_d2g_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        procedure_ref = procedure_thrombectomy_ref,
                                                        door_to_groin_time=door_to_groin)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2g, request=BundleEntryRequest(method="POST", url="Observation")))
    
    door_to_groin_le90 = safe_get_bool(raw, "door_to_groin_le90", required=False)
    if door_to_groin_le90 is not None:
        observation_d2g_le90 = build_timing_d2g_le90_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        procedure_ref = procedure_thrombectomy_ref,
                                                        door_to_groin_le90=door_to_groin_le90)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2g_le90, request=BundleEntryRequest(method="POST", url="Observation")))
    door_to_groin_le120 = safe_get_bool(raw, "door_to_groin_le120", required=False)
    if door_to_groin_le120 is not None:
        observation_d2g_le120 = build_timing_d2g_le120_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        procedure_ref = procedure_thrombectomy_ref,
                                                        door_to_groin_le120=door_to_groin_le120)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2g_le120, request=BundleEntryRequest(method="POST", url="Observation")))

    door_to_ich_evacuation = safe_get(raw, "door_to_ich_evacuation", required=False)
    if door_to_ich_evacuation is not None and procedure_ich_treatment_ref:
        observation_d2e = build_timing_door_to_ich_evacuation_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                procedure_ref = procedure_ich_treatment_ref,
                                                                door_to_ich_evacuation_time=door_to_ich_evacuation)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2e, request=BundleEntryRequest(method="POST", url="Observation")))

    door_to_imaging = safe_get(raw, "door_to_imaging", required=False)
    if door_to_imaging is not None and procedure_imaging_ref:
        observation_d2i = build_timing_door_to_imaging_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                procedure_ref = procedure_imaging_ref,
                                                                door_to_imaging_time=door_to_imaging)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2i, request=BundleEntryRequest(method="POST", url="Observation")))


    iv_antihypertensive = safe_get(raw, "iv_antihypertensive", required=False)
    if iv_antihypertensive is not None:
        iv_antihypertensive_timing = safe_get(raw, "iv_antihypertensive_timing", required=False)
        if iv_antihypertensive_timing is not None:
            medicationAdministration_iv_antihypertensive = build_medicationAdministration(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                condition_ref=None, # No condition reference for IV antihypertensive administration, can be extended to reference a specific condition if needed
                                                                procedure_ref=None, # No procedure reference for IV antihypertensive administration, can be extended to reference a specific procedure if needed
                                                                observation_ref= observation_vital_signs_ref or None, # No observation reference for IV antihypertensive administration, can be extended to reference a specific observation if needed
                                                                medication= Medications.ANTIHYPERTENSIVE, # Use a specific medication for IV antihypertensive, can be extended to use different medications if needed
                                                                dose = None, # Dose is not provided for IV antihypertensive in raw data, pass None
                                                                medication_timestamp=iv_antihypertensive_timing) # Pass IV antihypertensive administration timestamp to build_medicationAdministration
            medicationAdministration_iv_antihypertensive_ref = get_uuid()
            entries.append(BundleEntry(fullUrl=medicationAdministration_iv_antihypertensive_ref, resource=medicationAdministration_iv_antihypertensive, request=BundleEntryRequest(method="POST", url="MedicationAdministration")))
    door_to_iv_antihypertensive = safe_get(raw, "door_to_iv_antihypertensive", required=False)
    if door_to_iv_antihypertensive is not None and medicationAdministration_iv_antihypertensive_ref:
        observation_d2iv = build_timing_door_to_iv_antihypertensive_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                medicationAdministration_ref=medicationAdministration_iv_antihypertensive_ref,
                                                                door_to_iv_antihypertensive_time=door_to_iv_antihypertensive)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2iv, request=BundleEntryRequest(method="POST", url="Observation")))
    door_to_reperfusion = safe_get(raw, "door_to_reperfusion", required=False)
    if door_to_reperfusion is not None:
        observation_d2r = build_door_to_reperfusion_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                procedure_ref = procedure_thrombectomy_ref, # This can be extended to reference either thrombolysis or thrombectomy procedure based on which reperfusion treatment was done
                                                                door_to_reperfusion_time=door_to_reperfusion)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2r, request=BundleEntryRequest(method="POST", url="Observation")))
    door_to_sys_bp_lt140 = safe_get(raw, "door_to_sys_bp_lt140", required=False)
    if door_to_sys_bp_lt140 is not None:
        observation_d2bp = build_door_to_sys_bp_lt140_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                door_to_sys_bp_lt140_time=door_to_sys_bp_lt140)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_d2bp, request=BundleEntryRequest(method="POST", url="Observation")))
        
    onset_to_door = safe_get(raw, "onset_to_door", required=False)
    if onset_to_door is not None:
        observation_o2d = build_onset_to_door_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        onset_to_door_time=onset_to_door)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_o2d, request=BundleEntryRequest(method="POST", url="Observation")))

    abcd_score = safe_get(raw, "abcd2_score", required=False)
    if abcd_score is not None:
        observation_abcd = build_abcd2_score_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        abcd2_score=abcd_score)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_abcd, request=BundleEntryRequest(method="POST", url="Observation")))

    cha2ds2_vasc_score = safe_get(raw, "chads2_vasc_score", required=False)
    if cha2ds2_vasc_score is not None:
        observation_cha2ds2 = build_CHA2S2_VASc_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        cha2s2_vasc_score=cha2ds2_vasc_score)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_cha2ds2, request=BundleEntryRequest(method="POST", url="Observation")))

    thrive_score = safe_get(raw, "thrive_score", required=False)
    if thrive_score is not None:
        observation_thrive = build_thrive_score_observation(patient_ref=patient_ref,
                                                        encounter_ref=encounter_ref,
                                                        thrive_score=thrive_score)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_thrive, request=BundleEntryRequest(method="POST", url="Observation")))
    
    systolic_pressure_lt140 = safe_get_bool(raw, "systolic_pressure_lt140", required=False)
    if systolic_pressure_lt140 is not None:
        systolic_pressure_lt140_timestamp = safe_get(raw, "systolic_pressure_lt140_timestamp", required=False)
        observation_sys_bp_lt140 = build_systolic_pressure_lt140_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                systolic_pressure_lt140=systolic_pressure_lt140,
                                                                systolic_pressure_lt140_timestamp=systolic_pressure_lt140_timestamp)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_sys_bp_lt140, request=BundleEntryRequest(method="POST", url="Observation")))

    discharge_to_three_month_contact = safe_get(raw, "discharge_to_three_month_contact", required=False)
    if discharge_to_three_month_contact is not None:
        observation_discharge_to_three_month_contact = build_timing_discharge_to_three_months_contact_observation(patient_ref=patient_ref,
                                                                                               encounter_ref=encounter_ref,
                                                                                               discharge_to_three_months_contact=discharge_to_three_month_contact)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_discharge_to_three_month_contact, request=BundleEntryRequest(method="POST", url="Observation")))

    groin_to_reperfusion = safe_get(raw, "groin_to_reperfusion", required=False)
    if groin_to_reperfusion is not None:
        observation_g2r = build_groin_to_reperfusion_observation(patient_ref=patient_ref,
                                                                encounter_ref=encounter_ref,
                                                                procedure_ref = procedure_thrombectomy_ref, # This can be extended to reference either thrombolysis or thrombectomy procedure based on which reperfusion treatment was done
                                                                groin_to_reperfusion_time=groin_to_reperfusion)
        entries.append(BundleEntry(fullUrl=get_uuid(), resource=observation_g2r, request=BundleEntryRequest(method="POST", url="Observation")))

    # Create and return the transaction Bundle
    bundle_final = Bundle(type="transaction")
    bundle_final.entry = entries
    return bundle_final


