"""
Domain-specific helper functions for stroke data extraction.
"""

import pandas as pd
from scripts.enum_models import (
    BodySites, FirstContactPlace, Laterality, StrokeEtiology, Medications, BleedingReason, RiskFactor
)


def get_encounter_class(first_contact_place: FirstContactPlace):
    """Determine encounter class based on first contact place."""
    if first_contact_place == FirstContactPlace.EMERGENCY:
        return "IMP", "inpatient encounter"  # Inpatient encounter
    elif first_contact_place == FirstContactPlace.OUTPATIENT or first_contact_place == FirstContactPlace.RADIOLOGY:
        return "AMB", "ambulatory"  # Ambulatory encounter
    elif first_contact_place == FirstContactPlace.OTHER:
        return "OTH", "other"  # Other encounter
    else:
        raise ValueError(f"Unknown first contact place: {first_contact_place.id}")



def get_stroke_etiology(raw: dict):
    """Extract stroke etiology from raw data. Returns None if no etiology applies."""
    mapping = {
        "stroke_etiology_cardioembolism": StrokeEtiology.CARDIOEMBOLYSM,
        "stroke_etiology_la_atherosclerosis": StrokeEtiology.ATHEROSCLEROSIS,
        "stroke_etiology_lacunar": StrokeEtiology.LACUNAR,
        "stroke_etiology_cryptogenic_stroke": StrokeEtiology.CRYPTOGENIC_STROKE,
        "stroke_etiology_other": StrokeEtiology.OTHER,
        "stroke_etiology_dissection": StrokeEtiology.DISSECTION,
        "stroke_etiology_migrainous_stroke": StrokeEtiology.MIGRAINOUS_STROKE,
        "stroke_etiology_moyamoya": StrokeEtiology.MOYAMOYA,
        "stroke_etiology_sickle_cell_anemia": StrokeEtiology.SICKLE_CELL_ANEMIA,
        "stroke_etiology_undetermined": StrokeEtiology.UNDETERMINED
    }
    for key, etiology in mapping.items():
        value = raw.get(key)
        if value is True:
            return etiology
    return None


def get_before_onset_medications(raw: dict):
    """Extract medications taken before stroke onset, categorized by status."""
    medications_taken = []
    medications_not_taken = []
    medications_unknown = []

    mapping = {
        "before_onset_antidiabetics": Medications.ANTIDIABETIC,
        "before_onset_antihypertensives": Medications.ANTIHYPERTENSIVE,
        "before_onset_any_anticoagulant": Medications.ANTICOAGULANT,
        "before_onset_any_antiplatelet": Medications.ANTIPLATELET,
        "before_onset_apixaban": Medications.APIXABAN,
        "before_onset_asa": Medications.ASA,
        "before_onset_cilostazol": Medications.CILOSTOLAZOL,
        "before_onset_clopidogrel": Medications.CLOPIDOGREL,
        "before_onset_contraception": Medications.CONTRACEPTION,
        "before_onset_dabigatran": Medications.DABIGATRAN,
        "before_onset_dipyridamole": Medications.DIPYRIDAMOLE,
        "before_onset_edoxaban": Medications.EDOXABAN,
        "before_onset_heparin": Medications.HEPARIN,
        "before_onset_other_anticoagulant": Medications.OTHER_ANTICOAGULANT,
        "before_onset_other_antiplatelet": Medications.OTHER_ANTIPLATELET,
        "before_onset_other": Medications.OTHER_MEDICATION,
        "before_onset_plasugrel": Medications.PLASUGREL,
        "before_onset_rivaroxaban": Medications.RIVAROXABAN,
        "before_onset_statin": Medications.STATIN,
        "before_onset_ticagrelor": Medications.TICAGRELOR,
        "before_onset_ticlopidine": Medications.TICLOPIDINE,
        "before_onset_warfarin": Medications.WARFARIN
    }

    for key, med in mapping.items():
        value = raw.get(key)
        if value is True:
            medications_taken.append(med)
        elif value is False:
            medications_not_taken.append(med)
        elif pd.isna(value):
            medications_unknown.append(med)

    return medications_taken, medications_not_taken, medications_unknown


def get_on_discharge_medications(raw: dict):
    """Extract medications prescribed at discharge."""
    medications_prescribed = []

    mapping = {
        "discharge_antidiabetics": Medications.ANTIDIABETIC,
        "discharge_antihypertensives": Medications.ANTIHYPERTENSIVE,
        "discharge_any_anticoagulant": Medications.ANTICOAGULANT,
        "discharge_any_antiplatelet": Medications.ANTIPLATELET,
        "discharge_other_antiplatelet": Medications.OTHER_ANTIPLATELET,
        "discharge_heparin": Medications.HEPARIN,
        "discharge_asa": Medications.ASA,
        "discharge_clopidogrel": Medications.CLOPIDOGREL,
        "discharge_contraception": Medications.CONTRACEPTION,
        "discharge_other": Medications.OTHER_MEDICATION,
        "discharge_statin": Medications.STATIN,
        "discharge_warfarin": Medications.WARFARIN,
        #"discharge_any_antithrombotics": Medications.ANTITHROMBOTIC,
        #"discharge_any_medication": Medications.ANY_MEDICATION,
        "discharge_apixaban": Medications.APIXABAN,
        "discharge_cilostazol": Medications.CILOSTOLAZOL,
        "discharge_dabigatran": Medications.DABIGATRAN,
        "discharge_dipyridamole": Medications.DIPYRIDAMOLE,
        "discharge_edoxaban": Medications.EDOXABAN,
        "discharge_other_anticoagulant": Medications.OTHER_ANTICOAGULANT,
        "discharge_plasugrel": Medications.PLASUGREL,
        "discharge_rivaroxaban": Medications.RIVAROXABAN,
        "discharge_ticagrelor": Medications.TICAGRELOR,
        
    }

    for key, med in mapping.items():
        value = raw.get(key)
        if value is True:
            medications_prescribed.append(med)

    return medications_prescribed


def get_bleeding_reason(raw: dict):
    """Extract bleeding reason from raw data. Returns None if none applies."""
    mapping = {
        "bleeding_reason_aneurysm": BleedingReason.ANEURYSM,
        "bleeding_reason_malformation": BleedingReason.MALFORMATION,
        "bleeding_reason_other": BleedingReason.OTHER,
        "bleeding_reason_anticoagulant": BleedingReason.ANTICOAGULANT,
        "bleeding_reason_brain_tumor": BleedingReason.BRAINTUMOR,
        "bleeding_reason_cvt": BleedingReason.CVT,
        "bleeding_reason_hypertension": BleedingReason.HYPERTENSION,
        "bleeding_reason_avm": BleedingReason.AVM,
        "bleeding_reason_angiopathy": BleedingReason.ANGIOPATHY
    }

    reason_list = []
    for key, reason in mapping.items():
        if raw.get(key) is True:
            reason_list.append(reason)
    return reason_list



def get_risk_factors(raw: dict):
    """
    Extract risk factors from raw data, categorized by clinical status.
    Returns: (active, inactive, unknown, remission) tuples of RiskFactor enums
    """
    risk_factor_active = []
    risk_factor_inactive = []
    risk_factor_unknown = []
    risk_factor_remission = []
    
    mapping = {
        "risk_hypertension": RiskFactor.Hypertension,
        "risk_diabetes": RiskFactor.Diabetes,
        "risk_hyperlipidemia": RiskFactor.Hyperlipidemia,
        "risk_previous_stroke": RiskFactor.PreviousStroke,
        "risk_previous_ischemic_stroke": RiskFactor.PreviousIschemicStroke,
        "risk_previous_hemorrhagic_stroke": RiskFactor.PreviousHemorrhagicStroke,
        "risk_atrial_fibrillation": RiskFactor.AtrialFibrillation,
        "risk_coronary_artery_disease_or_myocardial_infarction": RiskFactor.CoronaryArteryDisease,
        "risk_congestive_heart_failure": RiskFactor.CongestiveHeartFailure,
        "risk_covid": RiskFactor.COVID,
        "risk_hiv": RiskFactor.HIV,
        "risk_vte": RiskFactor.VTE,
        "risk_alcohol_overuse": RiskFactor.ALCOHOL,
        "risk_sleep_apnea": RiskFactor.SLEEP_APNEA,
    }

    for key, med in mapping.items():
        value = raw.get(key)
        if value is True:
            if med.id == "PreviousIschemicStroke" or med.id == "PreviousHemorrhagicStroke" or med.id == "PreviousStroke":
                risk_factor_remission.append(med)
            else:
                risk_factor_active.append(med)
        elif value is False:
            risk_factor_inactive.append(med)
        elif pd.isna(value):
            risk_factor_unknown.append(med)

    return risk_factor_active, risk_factor_inactive, risk_factor_unknown, risk_factor_remission


def get_occlusions_list(raw: dict):
    """
    Extract list of occluded arteries from raw data.
    Returns: List of BodySites enums for occluded arteries
    """
    occlusions = []
    mapping = {
        "occlusion_left_mca_m1": (BodySites.MCA_M1,Laterality.LEFT),
        "occlusion_right_mca_m1": (BodySites.MCA_M1,Laterality.RIGHT),
        "occlusion_left_mca_m2": (BodySites.MCA_M2,Laterality.LEFT),
        "occlusion_right_mca_m2": (BodySites.MCA_M2,Laterality.RIGHT),
        "occlusion_left_mca_m3": (BodySites.MCA_M3,Laterality.LEFT),
        "occlusion_right_mca_m3": (BodySites.MCA_M3,Laterality.RIGHT),
        "occlusion_left_aca": (BodySites.ACA, Laterality.LEFT),
        "occlusion_right_aca": (BodySites.ACA, Laterality.RIGHT),
        "occlusion_left_cai": (BodySites.CAI, Laterality.LEFT),
        "occlusion_right_cai": (BodySites.CAI, Laterality.RIGHT),
        "occlusion_left_pca_p1": (BodySites.PCA_P1, Laterality.LEFT),
        "occlusion_right_pca_p1": (BodySites.PCA_P1, Laterality.RIGHT),
        "occlusion_left_pca_p2": (BodySites.PCA_P2, Laterality.LEFT),
        "occlusion_right_pca_p2": (BodySites.PCA_P2, Laterality.RIGHT),
        "occlusion_left_cae": (BodySites.CAE, Laterality.LEFT),
        "occlusion_right_cae": (BodySites.CAE, Laterality.RIGHT),
    }
    for key, body_site in mapping.items():
        if raw.get(key) is True:
            occlusions.append(body_site)
    return occlusions