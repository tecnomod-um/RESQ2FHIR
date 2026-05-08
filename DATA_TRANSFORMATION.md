# RESQ2FHIR - Data Transformation Guide

## Overview

This document explains how RESQ stroke registry CSV data is transformed into FHIR resources.

## Data Flow

```
CSV Row (Patient Record)
    ↓
Parse & Validate Fields
    ↓
Create Core Resources:
  - Organization (Hospital)
  - Patient (Demographics)
  - Encounter (Admission/Stay)
    ↓
Create Clinical Resources:
  - Conditions (Stroke diagnosis, Risk factors)
  - Observations (Vital signs, Scores, Measurements)
  - Procedures (Imaging, Interventions, Screening)
  - Medications (Before-onset, At discharge)
    ↓
Bundle Resources (Transaction)
    ↓
JSON Output File
```

## CSV Column Categories

### 1. Patient Demographics
```
- case_id              (string) → Patient.id
- sex                  (male/female/other) → Patient.extension[gender]
- age                  (integer) → Observation (AdmissionAge)
```

### 2. Admission Data
```
- hospital_name        (string) → Organization.name
- provider             (string) → Encounter.serviceProvider
- provider_id          (string) → Organization.id
- arrival_mode         (enum) → Encounter.extension[arrivalMode]
- admission_department (enum) → Encounter.location[0].location.reference
- first_contact_place  (enum) → Encounter.extension[firstContactPlace]
- hospitalized_in      (enum) → Encounter.type[0]
```

### 3. Vital Signs & Baseline
```
- systolic_pressure    (integer) → Observation (Blood Pressure - systolic)
- diastolic_pressure   (integer) → Observation (Blood Pressure - diastolic)
- glucose              (integer) → Observation (Glucose Level)
- cholesterol          (integer) → Observation (Total Cholesterol)
```

### 4. Stroke Severity Scores
```
- nihss_score          (integer) → Observation (NIHSS)
- mrs_score            (integer) → Observation (Modified Rankin Scale)
- aspects_score        (integer) → Observation (ASPECTS)
- gcs_score            (integer) → Observation (Glasgow Coma Scale)
- abcd2_score          (integer) → Observation (ABCD2)
- cha2ds2_vasc_score   (integer) → Observation (CHA2DS2-VASc)
- hunt_hess_score      (integer) → Observation (Hunt & Hess)
- ich_score            (integer) → Observation (ICH Score)
- mtici_score          (string) → Observation (mTICI)
- thrive_score         (integer) → Observation (THRIVE)
```

### 5. Stroke Type & Diagnosis
```
- stroke_type          (ischemic/hemorrhagic/tia/sah) → Condition.code
- stroke_etiology_*    (boolean flags) → Condition (multiple)
  - stroke_etiology_cardioembolism
  - stroke_etiology_la_atherosclerosis
  - stroke_etiology_lacunar
  - stroke_etiology_cryptogenic_stroke
  - stroke_etiology_other
```

### 6. Risk Factors (Boolean Conditions)
```
- risk_atrial_fibrillation
- risk_diabetes
- risk_hypertension
- risk_coronary_artery_disease_or_myocardial_infarction
- risk_hyperlipidemia
- risk_smoker
- risk_previous_stroke
- risk_previous_hemorrhagic_stroke
- risk_previous_ischemic_stroke
- risk_vte
- risk_hiv
- risk_covid
- risk_congestive_heart_failure
- risk_other
```

### 7. Pre-Stroke Medications (Boolean Flags)
```
- before_onset_antihypertensives    → MedicationStatement (Taking)
- before_onset_antidiabetics
- before_onset_any_antiplatelet
- before_onset_asa                  → MedicationStatement (specific medication)
- before_onset_clopidogrel
- before_onset_ticlopidine
- before_onset_any_anticoagulant
- before_onset_warfarin
- before_onset_dabigatran
- before_onset_apixaban
- before_onset_edoxaban
- before_onset_rivaroxaban
- before_onset_heparin
- before_onset_statin
```

### 8. Clinical Procedures & Treatments
```
- imaging_done         (boolean) → Procedure (Imaging)
- imaging_type         (MR/CT/...) → Procedure.code
- carotid_arteries_imaging (boolean)
- carotid_endarterectomy (boolean)
- cvt_treatment_*      (boolean flags)
  - cvt_treatment_anticoagulation
  - cvt_treatment_thrombectomy
  - cvt_treatment_thrombolysis
- thrombectomy         (boolean) → Procedure (MT)
- thrombolysis         (boolean) → Procedure (IVT)
- craniectomy          (boolean)
- ich_treatment_*      (various)
- sah_treatment_*      (various)
```

### 9. Hemodynamic & Monitoring Data
```
- day_1_fever_checks   (integer) → Observation
- day_1_hyperglycemia_checks
- day_2_fever_checks
- day_2_hyperglycemia_checks
- day_3_fever_checks
- day_3_hyperglycemia_checks
- patient_ventilated   (boolean)
- fever_diagnosed      (boolean)
- hyperglycemia_diagnosed (boolean)
```

### 10. Timing & Door-to-Treatment
```
- door_to_needle       (integer minutes) → Observation
- door_to_groin        (integer minutes) → Observation
- door_to_reperfusion  (integer minutes) → Observation
- door_to_discharge    (integer minutes) → Observation
- onset_to_door        (integer minutes) → Observation
- groin_to_reperfusion (integer minutes) → Observation
```

### 11. Post-Stroke Complications
```
- post_stroke_pneumonia
- post_stroke_dvt
- post_stroke_pulmonary_embolism
- post_stroke_urinary_infection
- post_stroke_pressure_sores
- post_stroke_recurrence_or_extension
- post_stroke_hemorrhagic_transformation
- post_stroke_remote_bleeding
- post_stroke_drip_site_sepsis
```

### 12. Discharge Data
```
- discharge_date       (date) → Encounter.period.end
- discharge_destination (enum) → Encounter.hospitalization.dischargeDisposition
- discharge_mrs        (integer) → Observation (mRS at discharge)
- discharge_nihss_score (integer) → Observation (NIHSS at discharge)
- discharge_facility_type (enum)
- discharge_facility_department (enum)
```

### 13. Discharge Medications
```
- discharge_asa        (boolean) → MedicationRequest
- discharge_clopidogrel
- discharge_ticagrelor
- discharge_statin
- discharge_any_anticoagulant
- discharge_any_antiplatelet
- discharge_warfarin
- discharge_apixaban
- etc.
```

### 14. Rehabilitation & Follow-up
```
- physiotherapy        (boolean) → Procedure
- occupational_therapy (boolean) → Procedure
- speech_therapy       (boolean) → Procedure
- swallowing_screening_done (boolean) → Procedure
- stroke_management_appointment (boolean)
- three_m_mode_contact (enum) → Observation
- three_m_mrs          (integer) → Observation (mRS at 3 months)
```

## FHIR Resource Mapping

### Organization
```
CSV Fields          FHIR Resource
hospital_name     → Organization.name
provider_id       → Organization.id
provider          → Organization.alias
```

### Patient
```
case_id           → Patient.id
sex               → Patient.extension[gender]
age               → Observation (derived from DOB or as age value)
```

### Encounter
```
hospital_timestamp → Encounter.period.start
discharge_date    → Encounter.period.end
admission_dept    → Encounter.location[0].location
arrival_mode      → Encounter.extension[arrivalMode]
inhospital_stroke → Encounter.extension[inHospitalStroke]
```

### Condition (Stroke Diagnosis)
```
stroke_type       → Condition.code (ischemic/hemorrhagic/tia/sah)
stroke_etiology_* → Condition (one per active etiology)
```

### Condition (Risk Factors)
```
risk_*            → Condition.code (one per risk factor)
                  → Condition.clinicalStatus (active/remission/inactive)
```

### Observation (Vital Signs)
```
systolic_pressure → Observation (SNOMED: 72313002)
diastolic_pressure → Observation (SNOMED: 1091811000000102)
```

### Observation (Lab Values)
```
glucose           → Observation (SNOMED: 2345-7 or equivalent)
cholesterol       → Observation (SNOMED: 2093-3 or equivalent)
```

### Observation (Functional Scores)
```
nihss_score       → Observation (SNOMED: 445949006)
mrs_score         → Observation (mRS - custom ValueSet)
aspects_score     → Observation (ASPECTS - custom ValueSet)
gcs_score         → Observation (SNOMED: 248241002)
```

### Observation (Timing)
```
door_to_needle    → Observation (Time from door to thrombolysis)
door_to_groin     → Observation (Time from door to MT groin access)
door_to_reperfusion → Observation (Time to reperfusion)
```

### Procedure
```
imaging_done      → Procedure (Imaging - CT/MR)
thrombectomy      → Procedure (Mechanical Thrombectomy)
thrombolysis      → Procedure (IV Thrombolysis)
craniectomy       → Procedure (Craniectomy)
carotid_imaging   → Procedure (Carotid Imaging)
```

### MedicationStatement (Before Onset)
```
before_onset_*    → MedicationStatement
                  → status: "taken" / "not-taken" / "unknown"
```

### MedicationRequest (Discharge)
```
discharge_*       → MedicationRequest
                  → intent: "plan"
                  → status: "active"
```

## Code Systems

### SNOMED CT
Used for most clinical codes (procedures, conditions, observations)

### Custom ValueSets
- Stroke types (Ischemic, Hemorrhagic, TIA, SAH)
- Stroke etiology
- Discharge destinations
- Functional outcomes (mRS, NIHSS ranges)

### HL7 V3
- Administrative gender codes
- Encounter types/classes
- Participation types

## Validation Rules

### Required Fields (for valid Bundle)
- `case_id` - Patient identifier
- `hospital_name` - Organization
- `sex` - Patient demographics
- `hospitalized_in` - Encounter type
- `stroke_type` - Diagnosis

### Dependent Fields
- If `stroke_type=ischemic` → one `stroke_etiology_*` should be true
- If `thrombectomy=true` → `imaging_done` should be true
- If `thrombolysis=true` → `door_to_needle` timing should be present

### Data Type Validations
- Dates: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
- Integers: Valid numeric ranges
- Booleans: VERDADERO/FALSO (Spanish), true/false (English), 0/1
- Enums: Valid enum values only

## Example Transformation

**CSV Row:**
```
case_id,hospital_name,sex,age,stroke_type,nihss_score,systolic_pressure,diastolic_pressure
abc123,Hospital A,male,65,ischemic,8,145,85
```

**FHIR Bundle Output:**
```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "resource": {
        "resourceType": "Organization",
        "id": "hospital-a",
        "name": "Hospital A"
      },
      "request": { "method": "POST", "url": "Organization" }
    },
    {
      "resource": {
        "resourceType": "Patient",
        "id": "abc123",
        "gender": "male",
        "extension": [...]
      },
      "request": { "method": "POST", "url": "Patient" }
    },
    {
      "resource": {
        "resourceType": "Encounter",
        "subject": { "reference": "urn:uuid:..." },
        "serviceProvider": { "reference": "urn:uuid:..." },
        ...
      },
      "request": { "method": "POST", "url": "Encounter" }
    },
    {
      "resource": {
        "resourceType": "Condition",
        "code": {
          "coding": [{"system": "http://snomed.info/sct", "code": "...", "display": "Ischemic stroke"}]
        },
        ...
      },
      "request": { "method": "POST", "url": "Condition" }
    },
    ...observations, procedures, medications...
  ]
}
```

## Troubleshooting Data Issues

### Missing required field error
Check that the CSV contains all required columns and values are not empty.

### Boolean value parsing error
Ensure boolean values are in recognized format: VERDADERO/FALSO, true/false, yes/no, 0/1, Y/N.

### Enum value not found
Check that enum values match exactly (case-sensitive where applicable).

### Date parsing error
Ensure dates are in supported formats: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, or YYYY-MM-DDThh:MM:SS.

---

For more information, see README.md and data/mappings.csv.
