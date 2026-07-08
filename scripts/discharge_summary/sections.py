"""Section catalogue for the RESQ+ Stroke Hospital Discharge Report.

The catalogue follows the European Hospital Discharge Report structure.
Standard clinical-document sections use LOINC codes.

This module defines document policy only. It does not construct FHIR
resources, render narratives or build the document Bundle.
"""

from __future__ import annotations

from dataclasses import dataclass

from scripts.enum_models import DischargeSection


LOINC = "http://loinc.org"


@dataclass(frozen=True)
class SectionDefinition:
    """Metadata and constraints for one Composition section."""

    title: str
    order: int
    code: str
    display: str
    required: bool
    entry_types: frozenset[str]

    @property
    def system(self) -> str:
        return LOINC


SECTION_DEFINITIONS: dict[DischargeSection, SectionDefinition] = {
    DischargeSection.ADMISSION_EVALUATION: SectionDefinition(
        title="Admission Evaluation",
        order=10,
        code="67851-6",
        display="Admission evaluation note",
        required=False,
        entry_types=frozenset({
            "Condition",
            "Observation",
            "Location",
        }),
    ),
    DischargeSection.PATIENT_HISTORY: SectionDefinition(
        title="Relevant Patient History",
        order=20,
        code="11329-0",
        display="History of general health Narrative",
        required=False,
        entry_types=frozenset({
            "MedicationStatement",
        }),
    ),
    DischargeSection.PROBLEM_LIST: SectionDefinition(
        title="Relevant Problems and Risk Factors",
        order=30,
        code="11450-4",
        display="Problem list - Reported",
        required=False,
        entry_types=frozenset({
            "Condition",
        }),
    ),
    DischargeSection.HOSPITAL_COURSE: SectionDefinition(
        title="Hospital Course",
        order=40,
        code="8648-8",
        display="Hospital course note",
        required=True,
        entry_types=frozenset({
            "Condition",
            "Observation",
            "Procedure",
            "MedicationAdministration",
            "DiagnosticReport",
        }),
    ),
    DischargeSection.DIAGNOSTIC_SUMMARY: SectionDefinition(
        title="Diagnostic Summary",
        order=50,
        code="11535-2",
        display="Hospital discharge diagnosis Narrative",
        required=False,
        entry_types=frozenset({
            "Condition",
            "Observation",
        }),
    ),
    DischargeSection.SIGNIFICANT_PROCEDURES: SectionDefinition(
        title="Significant Procedures",
        order=60,
        code="10185-7",
        display="Hospital discharge procedures",
        required=False,
        entry_types=frozenset({
            "Procedure",
        }),
    ),
    DischargeSection.PHARMACOTHERAPY: SectionDefinition(
        title="Pharmacotherapy During Hospitalisation",
        order=70,
        code="87232-5",
        display="Medication administration brief",
        required=False,
        entry_types=frozenset({
            "MedicationAdministration",
            "MedicationStatement",
        }),
    ),
    DischargeSection.SIGNIFICANT_RESULTS: SectionDefinition(
        title="Significant Results",
        order=80,
        code="30954-2",
        display="Relevant diagnostic tests/laboratory data Narrative",
        required=False,
        entry_types=frozenset({
            "Observation",
            "DiagnosticReport",
        }),
    ),
    DischargeSection.VITAL_SIGNS: SectionDefinition(
        title="Vital Signs at Discharge",
        order=90,
        code="8716-3",
        display="Vital signs note",
        required=False,
        entry_types=frozenset({
            "Observation",
        }),
    ),
    DischargeSection.FUNCTIONAL_STATUS: SectionDefinition(
        title="Functional Status at Discharge",
        order=100,
        code="47420-5",
        display="Functional status assessment note",
        required=False,
        entry_types=frozenset({
            "Observation",
            "Condition",
            "QuestionnaireResponse",
        }),
    ),
    DischargeSection.DISCHARGE_DETAILS: SectionDefinition(
        title="Discharge Details",
        order=110,
        code="8650-4",
        display="Hospital discharge disposition note",
        required=False,
        entry_types=frozenset({
            "Encounter",
        }),
    ),
    DischargeSection.DISCHARGE_MEDICATIONS: SectionDefinition(
        title="Discharge Medications",
        order=120,
        code="75311-1",
        display="Discharge medications Narrative",
        required=False,
        entry_types=frozenset({
            "MedicationRequest",
            "MedicationStatement",
        }),
    ),
    DischargeSection.PLAN_OF_CARE: SectionDefinition(
        title="Plan of Care and Follow-up",
        order=130,
        code="18776-5",
        display="Plan of care note",
        required=False,
        entry_types=frozenset({
            "Appointment",
            "CarePlan",
            "ServiceRequest",
        }),
    ),
}


SECTION_ORDER: tuple[DischargeSection, ...] = tuple(
    sorted(
        SECTION_DEFINITIONS,
        key=lambda section: SECTION_DEFINITIONS[section].order,
    )
)

OCCLUSION_FIELDS = (
    "occlusion_left_mca_m1",
    "occlusion_left_mca_m2",
    "occlusion_left_mca_m3",
    "occlusion_left_aca",
    "occlusion_left_pca_p1",
    "occlusion_left_pca_p2",
    "occlusion_left_cae",
    "occlusion_left_cai",
    "occlusion_right_mca_m1",
    "occlusion_right_mca_m2",
    "occlusion_right_mca_m3",
    "occlusion_right_aca",
    "occlusion_right_pca_p1",
    "occlusion_right_pca_p2",
    "occlusion_right_cae",
    "occlusion_right_cai",
    "occlusion_ba",
    "occlusion_va",
)


BLEEDING_REASON_FIELDS = (
    "bleeding_reason_hypertension",
    "bleeding_reason_aneurysm",
    "bleeding_reason_malformation",
    "bleeding_reason_anticoagulant",
    "bleeding_reason_angiopathy",
    "bleeding_reason_brain_tumor",
    "bleeding_reason_cvt",
    "bleeding_reason_other",
)


RISK_FACTOR_FIELDS = (
    "risk_atrial_fibrillation",
    "risk_hypertension",
    "risk_diabetes",
    "risk_hyperlipidemia",
    "risk_congestive_heart_failure",
    "risk_smoker_last_10_years",
    "risk_previous_ischemic_stroke",
    "risk_previous_hemorrhagic_stroke",
    "risk_coronary_artery_disease_or_myocardial_infarction",
    "risk_vte",
    "risk_hiv",
    "risk_covid",
)


PRIOR_MEDICATION_FIELDS = (
    "before_onset_asa",
    "before_onset_cilostazol",
    "before_onset_clopidogrel",
    "before_onset_ticagrelor",
    "before_onset_ticlopidine",
    "before_onset_prasugrel",
    "before_onset_dipyridamole",
    "before_onset_warfarin",
    "before_onset_heparin",
    "before_onset_dabigatran",
    "before_onset_rivaroxaban",
    "before_onset_apixaban",
    "before_onset_edoxaban",
    "before_onset_antihypertensives",
    "before_onset_statin",
    "before_onset_antidiabetics",
)


DISCHARGE_MEDICATION_FIELDS = (
    "discharge_asa",
    "discharge_cilostazol",
    "discharge_clopidogrel",
    "discharge_ticagrelor",
    "discharge_ticlopidine",
    "discharge_prasugrel",
    "discharge_dipyridamole",
    "discharge_warfarin",
    "discharge_heparin",
    "discharge_dabigatran",
    "discharge_rivaroxaban",
    "discharge_apixaban",
    "discharge_edoxaban",
    "discharge_antihypertensives",
    "discharge_statin",
    "discharge_antidiabetics",
)


ETIOLOGY_FIELDS = (
    "stroke_etiology_cardioembolism",
    "atrial_fibrillation_or_flutter",
    "stroke_etiology_la_atherosclerosis",
    "carotid_stenosis_level",
    "stroke_etiology_lacunar",
    "stroke_etiology_other",
    "stroke_etiology_cryptogenic_stroke",
)


POST_STROKE_COMPLICATION_FIELDS = (
    "post_stroke_pneumonia",
    "post_stroke_dvt",
    "post_stroke_pulmonary_embolism",
    "post_stroke_urinary_infection",
    "post_stroke_pressure_sores",
    "post_stroke_drip_site_sepsis",
    "post_stroke_recurrence_or_extension",
    "post_stroke_falling",
)


POST_ACUTE_REHABILITATION_FIELDS = (
    "physiotherapy",
    "occup_therapy",
    "speech_therapy",
)

SECTION_SOURCE_FIELDS: dict[
    DischargeSection,
    tuple[str, ...],
] = {
    DischargeSection.ADMISSION_EVALUATION: (
        "age",
        "stroke_type",
        "onset_date",
        "wakeup_stroke",
        "tia_clinical_symptoms",
        "tia_symptoms_duration",
        "aspects_score",
        "nihss_score",
        "prestroke_mrs",
        "hospitalized_in",
    ),

    DischargeSection.PATIENT_HISTORY: (
        PRIOR_MEDICATION_FIELDS
    ),

    DischargeSection.PROBLEM_LIST: (
        RISK_FACTOR_FIELDS
    ),

    DischargeSection.HOSPITAL_COURSE: (
        "stroke_type",
        "thrombolysis",
        "thrombectomy",
        "discharge_nihss_score",
        "discharge_mrs",
    ) + POST_STROKE_COMPLICATION_FIELDS,

    DischargeSection.DIAGNOSTIC_SUMMARY: (
        "stroke_type",
        "stroke_mimics_diagnosis",
    ) + ETIOLOGY_FIELDS + BLEEDING_REASON_FIELDS + POST_STROKE_COMPLICATION_FIELDS,

    DischargeSection.SIGNIFICANT_PROCEDURES: (
        "thrombolysis",
        "no_thrombolysis_reason",
        "thrombectomy",
        "no_thrombectomy_reason",
        "ich_treatment_hematoma_evacuation",
        "ich_treatment_ventricular_drainage",
        "ich_treatment_craniectomy",
        "sah_treatment_coiling",
        "sah_treatment_clipping",
        "sah_treatment_drainage",
        "sah_treatment_craniectomy",
        "cvt_treatment_thrombectomy",
        "cvt_treatment_thrombolysis",
        "cvt_treatment_neurosurgery",
    ),

    DischargeSection.PHARMACOTHERAPY: (
        "ivt_drug",
        "ivt_drug_dose",
        "anticoagulant_reversal",
        "nimodipine",
        "nimodipine_timing",
        "cvt_treatment_anticoagulation",
    ),

    DischargeSection.SIGNIFICANT_RESULTS: (
        "imaging_done",
        "imaging_type",
        "occlusion_found",
        "bleeding_volume",
        "bleeding_source_found",
        "ich_score",
        "hunt_hess_score",
        "post_recanalization_imaging",
        "post_treatment_brain_infarct",
        "post_treatment_remote_bleeding",
        "post_treatment_hemorrhagic_transformation",
        "hemorrhagic_transformation_type",
        "carotid_stenosis_level",
        "infratentorial_hemorrhage",
        "intraventricular_hemorrhage",
        "mtici_score",
        "discharge_glucose",
    ) + OCCLUSION_FIELDS,

    DischargeSection.VITAL_SIGNS: (
        "discharge_systolic_pressure",
    ),

    DischargeSection.FUNCTIONAL_STATUS: (
        "discharge_nihss_score",
        "discharge_mrs",
    ),

    DischargeSection.DISCHARGE_DETAILS: (
        "discharge_date",
        "discharge_destination",
    ),

    DischargeSection.DISCHARGE_MEDICATIONS: (
        DISCHARGE_MEDICATION_FIELDS
    ),

    DischargeSection.PLAN_OF_CARE: (
        "stroke_management_appointment",
    ) + POST_ACUTE_REHABILITATION_FIELDS,
}

HEADER_SOURCE_FIELDS = (
    "sex",
    "discharge_date",
)