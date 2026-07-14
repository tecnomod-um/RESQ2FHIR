"""Xt-EHR EHDSDischargeReport policy for the RESQ FHIR R5 document."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scripts.enum_models import DischargeSection

LOINC = "http://loinc.org"
SNOMED_CT = "http://snomed.info/sct"
EHDS_DISCHARGE_REPORT = "http://www.xt-ehr.eu/fhir/models/StructureDefinition/EHDSDischargeReport"


class DocumentSection(str, Enum):
    ALERTS = "alerts"
    ALLERGIES_INTOLERANCES = "allergies-intolerances"
    ENCOUNTER_INFORMATION = "encounter-information"
    ADMISSION_EVALUATION = "admission-evaluation"
    PATIENT_HISTORY = "patient-history"
    COURSE_OF_ENCOUNTER = "course-of-encounter"
    DIAGNOSTIC_SUMMARY = "diagnostic-summary"
    SIGNIFICANT_PROCEDURES = "significant-procedures"
    MEDICAL_DEVICES = "medical-devices"
    PHARMACOTHERAPY = "pharmacotherapy"
    SIGNIFICANT_RESULTS = "significant-results"
    DISCHARGE_DETAILS = "discharge-details"
    VITAL_SIGNS = "vital-signs"
    ANTHROPOMETRY = "anthropometry"
    PHYSICAL_EXAMINATION = "physical-examination"
    FUNCTIONAL_STATUS = "functional-status"
    MEDICATION_SUMMARY = "medication-summary"
    PLAN_OF_CARE = "plan-of-care"
    CLINICAL_SYNTHESIS = "clinical-synthesis"


@dataclass(frozen=True)
class DocumentSectionDefinition:
    title: str
    order: int
    system: str
    code: str
    display: str
    required: bool
    ehds_path: str
    parent: DocumentSection | None = None
    source_sections: tuple[DischargeSection, ...] = ()
    include_encounter: bool = False
    empty_reason: str = "unavailable"
    empty_reason_display: str = "Unavailable"


def _definition(
    title: str,
    order: int,
    system: str,
    code: str,
    display: str,
    required: bool,
    ehds_path: str,
    parent: DocumentSection | None = None,
    source_sections: tuple[DischargeSection, ...] = (),
    include_encounter: bool = False,
    empty_reason: str = "unavailable",
    empty_reason_display: str = "Unavailable",
) -> DocumentSectionDefinition:
    return DocumentSectionDefinition(
        title, order, system, code, display, required, ehds_path, parent,
        source_sections, include_encounter, empty_reason, empty_reason_display,
    )


D = DocumentSection
DOCUMENT_SECTION_DEFINITIONS = {
    D.ALERTS: _definition("Medical Alerts", 10, LOINC, "75310-3", "Health concerns document", True, "body.alerts", empty_reason="notasked", empty_reason_display="Not Asked"),
    D.ALLERGIES_INTOLERANCES: _definition("Allergies and Intolerances", 20, LOINC, "48765-2", "Allergies and adverse reactions document", True, "body.alerts", empty_reason="notasked", empty_reason_display="Not Asked"),
    D.ENCOUNTER_INFORMATION: _definition("Encounter Information", 30, LOINC, "46240-8", "History of hospitalization and outpatient visits", True, "body.encounterInformation", include_encounter=True),
    D.ADMISSION_EVALUATION: _definition("Admission Evaluation", 40, LOINC, "67851-6", "Admission evaluation note", False, "body.admissionEvaluation", source_sections=(DischargeSection.ADMISSION_EVALUATION,)),
    D.PATIENT_HISTORY: _definition("Relevant Patient History", 50, LOINC, "11329-0", "History of general health narrative", False, "body.patientHistory", source_sections=(DischargeSection.PATIENT_HISTORY, DischargeSection.PROBLEM_LIST)),
    D.COURSE_OF_ENCOUNTER: _definition("Course of Encounter", 60, LOINC, "8648-8", "Hospital course note", True, "body.courseOfEncounter"),
    D.DIAGNOSTIC_SUMMARY: _definition("Diagnostic Summary", 10, LOINC, "11535-2", "Hospital discharge diagnosis note", True, "body.courseOfEncounter.diagnosticSummary", D.COURSE_OF_ENCOUNTER, (DischargeSection.DIAGNOSTIC_SUMMARY,)),
    D.SIGNIFICANT_PROCEDURES: _definition("Significant Procedures", 20, LOINC, "10185-7", "Hospital discharge procedure note", True, "body.courseOfEncounter.procedures", D.COURSE_OF_ENCOUNTER, (DischargeSection.SIGNIFICANT_PROCEDURES,)),
    D.MEDICAL_DEVICES: _definition("Medical Devices and Implants", 30, SNOMED_CT, "1184586001", "Medical device document section", True, "body.courseOfEncounter.medicalDevicesAndImplants", D.COURSE_OF_ENCOUNTER, empty_reason="notasked", empty_reason_display="Not Asked"),
    D.PHARMACOTHERAPY: _definition("Pharmacotherapy During Encounter", 40, LOINC, "87232-5", "Medication administration brief", False, "body.courseOfEncounter.pharmacotherapy", D.COURSE_OF_ENCOUNTER, (DischargeSection.PHARMACOTHERAPY,)),
    D.SIGNIFICANT_RESULTS: _definition("Significant Test Results", 50, LOINC, "30954-2", "Relevant diagnostic tests and laboratory data note", True, "body.courseOfEncounter.testResults[x]", D.COURSE_OF_ENCOUNTER, (DischargeSection.SIGNIFICANT_RESULTS,)),
    D.DISCHARGE_DETAILS: _definition("Discharge Details", 70, LOINC, "8650-4", "Hospital discharge disposition note", True, "body.dischargeDetails", source_sections=(DischargeSection.DISCHARGE_DETAILS,), include_encounter=True),
    D.VITAL_SIGNS: _definition("Vital Signs at Discharge", 10, LOINC, "8716-3", "Vital signs note", True, "body.dischargeDetails.objectiveFindings", D.DISCHARGE_DETAILS, (DischargeSection.VITAL_SIGNS,)),
    D.ANTHROPOMETRY: _definition("Anthropometric Measurements", 20, SNOMED_CT, "248326004", "Anthropometric measure", True, "body.dischargeDetails.objectiveFindings", D.DISCHARGE_DETAILS, empty_reason="notasked", empty_reason_display="Not Asked"),
    D.PHYSICAL_EXAMINATION: _definition("Physical Examination at Discharge", 30, LOINC, "29545-1", "Physical findings", True, "body.dischargeDetails.objectiveFindings", D.DISCHARGE_DETAILS, empty_reason="notasked", empty_reason_display="Not Asked"),
    D.FUNCTIONAL_STATUS: _definition("Functional Status at Discharge", 40, LOINC, "47420-5", "Functional status assessment note", True, "body.dischargeDetails.functionalStatus[x]", D.DISCHARGE_DETAILS, (DischargeSection.FUNCTIONAL_STATUS,)),
    D.MEDICATION_SUMMARY: _definition("Medication Summary at Discharge", 80, LOINC, "75311-1", "Discharge medications note", True, "body.medicationSummary", source_sections=(DischargeSection.DISCHARGE_MEDICATIONS,)),
    D.PLAN_OF_CARE: _definition("Plan of Care and Follow-up", 90, LOINC, "18776-5", "Plan of care note", True, "body.carePlan", source_sections=(DischargeSection.PLAN_OF_CARE,)),
    D.CLINICAL_SYNTHESIS: _definition("Clinical Synthesis", 100, SNOMED_CT, "866144008", "Encounter note", False, "body.clinicalSynthesis", source_sections=(DischargeSection.HOSPITAL_COURSE,)),
}

ROOT_SECTION_ORDER = tuple(
    section for section, definition in sorted(
        DOCUMENT_SECTION_DEFINITIONS.items(), key=lambda item: item[1].order
    ) if definition.parent is None
)


def child_sections(parent: DocumentSection) -> tuple[DocumentSection, ...]:
    return tuple(
        section for section, definition in sorted(
            DOCUMENT_SECTION_DEFINITIONS.items(), key=lambda item: item[1].order
        ) if definition.parent == parent
    )


def _fields(value: str) -> tuple[str, ...]:
    return tuple(value.split())


# Exact source list from "Case summary variables"; bleeding_reasons is expanded
# to the eight concrete SHM fields described in the data catalogue.
CASE_SUMMARY_SOURCE_FIELDS = _fields("""stroke_type
imaging_done
imaging_type
occlusion_found
occlusion_left_mca_m1
occlusion_left_mca_m2
occlusion_left_mca_m3
occlusion_left_aca
occlusion_left_pca_p1
occlusion_left_pca_p2
occlusion_left_cae
occlusion_left_cai
occlusion_right_mca_m1
occlusion_right_mca_m2
occlusion_right_mca_m3
occlusion_right_aca
occlusion_right_pca_p1
occlusion_right_pca_p2
occlusion_right_cae
occlusion_right_cai
occlusion_ba
occlusion_va
tia_clinical_symptoms
tia_symptoms_duration
thrombolysis
stroke_mimics_diagnosis
infratentorial_hemorrhage
intraventricular_hemorrhage
bleeding_volume
bleeding_reason_hypertension
bleeding_reason_aneurysm
bleeding_reason_malformation
bleeding_reason_anticoagulant
bleeding_reason_angiopathy
bleeding_reason_brain_tumor
bleeding_reason_cvt
bleeding_reason_other
anticoagulant_reversal
ich_score
ich_treatment_hematoma_evacuation
ich_treatment_ventricular_drainage
ich_treatment_craniectomy
bleeding_source_found
hunt_hess_score
sah_treatment_coiling
sah_treatment_clipping
sah_treatment_drainage
sah_treatment_craniectomy
nimodipine
nimodipine_timing
cvt_treatment_anticoagulation
cvt_treatment_thrombectomy
cvt_treatment_thrombolysis
cvt_treatment_neurosurgery
sex
age
risk_atrial_fibrillation
risk_hypertension
risk_diabetes
risk_hyperlipidemia
risk_congestive_heart_failure
risk_smoker_last_10_years
risk_previous_ischemic_stroke
risk_previous_hemorrhagic_stroke
risk_coronary_artery_disease_or_myocardial_infarction
risk_vte
risk_hiv
risk_covid
onset_date
wakeup_stroke
aspects_score
nihss_score
prestroke_mrs
hospitalized_in
ivt_drug
ivt_drug_dose
door_to_needle
no_thrombolysis_reason
thrombectomy
door_to_groin
mtici_score
no_thrombectomy_reason
door_to_door
post_recanalization_imaging
post_treatment_brain_infarct
post_treatment_remote_bleeding
post_treatment_hemorrhagic_transformation
hemorrhagic_transformation_type
atrial_fibrillation_or_flutter
physiotherapy
occup_therapy
speech_therapy
post_stroke_pneumonia
post_stroke_dvt
post_stroke_pulmonary_embolism
post_stroke_urinary_infection
post_stroke_pressure_sores
post_stroke_drip_site_sepsis
post_stroke_recurrence_or_extension
post_stroke_falling
stroke_etiology_cardioembolism
stroke_etiology_la_atherosclerosis
carotid_stenosis_level
stroke_etiology_lacunar
stroke_etiology_other
stroke_etiology_cryptogenic_stroke
discharge_destination
discharge_date
discharge_systolic_pressure
discharge_glucose
before_onset_asa
before_onset_cilostazol
before_onset_clopidogrel
before_onset_ticagrelor
before_onset_ticlopidine
before_onset_prasugrel
before_onset_dipyridamole
before_onset_warfarin
before_onset_heparin
before_onset_dabigatran
before_onset_rivaroxaban
before_onset_apixaban
before_onset_edoxaban
before_onset_antihypertensives
before_onset_statin
before_onset_antidiabetics
discharge_asa
discharge_cilostazol
discharge_clopidogrel
discharge_ticagrelor
discharge_ticlopidine
discharge_prasugrel
discharge_dipyridamole
discharge_warfarin
discharge_heparin
discharge_dabigatran
discharge_rivaroxaban
discharge_apixaban
discharge_edoxaban
discharge_antihypertensives
discharge_statin
discharge_antidiabetics
discharge_nihss_score
discharge_mrs
stroke_management_appointment""")

HEADER_SOURCE_FIELDS = _fields("""sex
age""")
SOURCE_FIELDS_BY_DOCUMENT_SECTION = {
    D.ADMISSION_EVALUATION: _fields("""onset_date
wakeup_stroke
aspects_score
nihss_score
prestroke_mrs
hospitalized_in
tia_clinical_symptoms
tia_symptoms_duration"""),
    D.PATIENT_HISTORY: _fields("""risk_atrial_fibrillation
risk_hypertension
risk_diabetes
risk_hyperlipidemia
risk_congestive_heart_failure
risk_smoker_last_10_years
risk_previous_ischemic_stroke
risk_previous_hemorrhagic_stroke
risk_coronary_artery_disease_or_myocardial_infarction
risk_vte
risk_hiv
risk_covid
before_onset_asa
before_onset_cilostazol
before_onset_clopidogrel
before_onset_ticagrelor
before_onset_ticlopidine
before_onset_prasugrel
before_onset_dipyridamole
before_onset_warfarin
before_onset_heparin
before_onset_dabigatran
before_onset_rivaroxaban
before_onset_apixaban
before_onset_edoxaban
before_onset_antihypertensives
before_onset_statin
before_onset_antidiabetics"""),
    D.DIAGNOSTIC_SUMMARY: _fields("""stroke_type
stroke_mimics_diagnosis
bleeding_reason_hypertension
bleeding_reason_aneurysm
bleeding_reason_malformation
bleeding_reason_anticoagulant
bleeding_reason_angiopathy
bleeding_reason_brain_tumor
bleeding_reason_cvt
bleeding_reason_other
stroke_etiology_cardioembolism
atrial_fibrillation_or_flutter
stroke_etiology_la_atherosclerosis
carotid_stenosis_level
stroke_etiology_lacunar
stroke_etiology_other
stroke_etiology_cryptogenic_stroke
post_stroke_pneumonia
post_stroke_dvt
post_stroke_pulmonary_embolism
post_stroke_urinary_infection
post_stroke_pressure_sores
post_stroke_drip_site_sepsis
post_stroke_recurrence_or_extension
post_stroke_falling"""),
    D.SIGNIFICANT_PROCEDURES: _fields("""thrombolysis
no_thrombolysis_reason
thrombectomy
no_thrombectomy_reason
ich_treatment_hematoma_evacuation
ich_treatment_ventricular_drainage
ich_treatment_craniectomy
sah_treatment_coiling
sah_treatment_clipping
sah_treatment_drainage
sah_treatment_craniectomy
cvt_treatment_thrombectomy
cvt_treatment_thrombolysis
cvt_treatment_neurosurgery
door_to_needle
door_to_groin
door_to_door"""),
    D.PHARMACOTHERAPY: _fields("""ivt_drug
ivt_drug_dose
anticoagulant_reversal
nimodipine
nimodipine_timing
cvt_treatment_anticoagulation"""),
    D.SIGNIFICANT_RESULTS: _fields("""imaging_done
imaging_type
occlusion_found
occlusion_left_mca_m1
occlusion_left_mca_m2
occlusion_left_mca_m3
occlusion_left_aca
occlusion_left_pca_p1
occlusion_left_pca_p2
occlusion_left_cae
occlusion_left_cai
occlusion_right_mca_m1
occlusion_right_mca_m2
occlusion_right_mca_m3
occlusion_right_aca
occlusion_right_pca_p1
occlusion_right_pca_p2
occlusion_right_cae
occlusion_right_cai
occlusion_ba
occlusion_va
infratentorial_hemorrhage
intraventricular_hemorrhage
bleeding_volume
bleeding_source_found
ich_score
hunt_hess_score
mtici_score
post_recanalization_imaging
post_treatment_brain_infarct
post_treatment_remote_bleeding
post_treatment_hemorrhagic_transformation
hemorrhagic_transformation_type
carotid_stenosis_level
discharge_glucose"""),
    D.PLAN_OF_CARE: _fields("""physiotherapy
occup_therapy
speech_therapy
stroke_management_appointment"""),
    D.DISCHARGE_DETAILS: _fields("""discharge_destination
discharge_date"""),
    D.VITAL_SIGNS: _fields("""discharge_systolic_pressure"""),
    D.FUNCTIONAL_STATUS: _fields("""discharge_nihss_score
discharge_mrs"""),
    D.MEDICATION_SUMMARY: _fields("""discharge_asa
discharge_cilostazol
discharge_clopidogrel
discharge_ticagrelor
discharge_ticlopidine
discharge_prasugrel
discharge_dipyridamole
discharge_warfarin
discharge_heparin
discharge_dabigatran
discharge_rivaroxaban
discharge_apixaban
discharge_edoxaban
discharge_antihypertensives
discharge_statin
discharge_antidiabetics"""),
}


def mapped_source_fields() -> frozenset[str]:
    mapped = set(HEADER_SOURCE_FIELDS)
    for fields in SOURCE_FIELDS_BY_DOCUMENT_SECTION.values():
        mapped.update(fields)
    return frozenset(mapped)


def unmapped_case_summary_fields() -> tuple[str, ...]:
    mapped = mapped_source_fields()
    return tuple(field for field in CASE_SUMMARY_SOURCE_FIELDS if field not in mapped)
