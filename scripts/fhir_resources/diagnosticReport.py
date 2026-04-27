

from scripts.enum_models import ConceptEnum, ImagingType, PerforationProcedures, SpecificFinding
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.reference import Reference
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.observation import Observation


def build_imaging_diagnostic_report(patient_ref: str, encounter_ref: str, imaging_type: ImagingType, perfusion_deficit_ref: str | None = None, imaging_results_ref: list[str] | None = None) -> DiagnosticReport:
    """
    Build a FHIR DiagnosticReport resource for imaging results.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        perfusion_deficit_ref: Reference to the Observation resource for perfusion deficit
        imaging_type: The type of imaging performed (e.g., CT, MRI)
        imaging_results_ref: References to the Observation resources for imaging results
    Returns:
        DiagnosticReport resource for imaging results
    """

    diagnostic_report = DiagnosticReport(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=CodeableConcept(coding=[imaging_type.to_coding()])
    )
    result_list = []
    if perfusion_deficit_ref is not None:
        result_list.append(Reference(reference=perfusion_deficit_ref))
    if imaging_results_ref is not None:
        result_list.extend([Reference(reference=result) for result in imaging_results_ref])

    diagnostic_report.result = result_list
    return diagnostic_report

def build_mechanical_thrombectomy_diagnostic_report(patient_ref: str, encounter_ref: str, thrombectomy_procedure_ref: str, mtici_score_ref: str) -> DiagnosticReport:
    """
    Build a FHIR DiagnosticReport resource for mechanical thrombectomy results.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        thrombectomy_procedure_ref: Reference to the Procedure resource for mechanical thrombectomy
        mtici_score_ref: Reference to the Observation resource for mTICI score
    Returns:
        DiagnosticReport resource for mechanical thrombectomy results
    """

    diagnostic_report = DiagnosticReport(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=CodeableConcept(coding=[PerforationProcedures.THROMBECTOMY.to_coding()]),
        result=[Reference(reference=mtici_score_ref)]
    )
    
    return diagnostic_report


def build_carotid_arteries_imaging_diagnostic_report(patient_ref: str, encounter_ref: str, observation_ref: str) -> DiagnosticReport:
    """
    Build a FHIR DiagnosticReport resource for carotid arteries imaging results.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        observation_ref: Reference to the Observation resource
    Returns:
        DiagnosticReport resource for carotid arteries imaging results
    """
    diagnostic_report = DiagnosticReport(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=CodeableConcept(coding=[ImagingType.CAROTID.to_coding()]),
        result=[Reference(reference=observation_ref)]
    )
    
    
    return diagnostic_report


def build_ct_mr_after_ivt_diagnostic_report(patient_ref: str, encounter_ref: str, ct_mr_after_ivt_results: ConceptEnum) -> DiagnosticReport:
    """
    Build a FHIR DiagnosticReport resource for CT/MR after IVT results.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        ct_mr_after_ivt_results: CT/MR after IVT result as ConceptEnum
    Returns:
        DiagnosticReport resource for CT/MR after IVT results
    """
    diagnostic_report = DiagnosticReport(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=CodeableConcept(coding=[ImagingType.CT.to_coding()])
    )
    
    if ct_mr_after_ivt_results is not None:
        diagnostic_report.conclusionCode = [CodeableConcept(coding=[ct_mr_after_ivt_results.to_coding()])]
    
    return diagnostic_report

def build_follow_up_ct_mr_diagnostic_report(patient_ref: str, encounter_ref: str, bleeding_volume_follow_up_ref: str, imaging_performed: ConceptEnum, hydrocephalus: bool) -> DiagnosticReport:
    """
    Build a FHIR DiagnosticReport resource for follow-up CT/MR results.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        bleeding_volume_follow_up_ref: Reference to the Observation resource for bleeding volume follow-up
        imaging_performed: The type of imaging performed for follow-up (e.g., CT, MRI)
        hydrocephalus: Boolean indicating presence of hydrocephalus in follow-up imaging
    Returns:
        DiagnosticReport resource for follow-up CT/MR results
    """
    diagnostic_report = DiagnosticReport(
        status="final",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        code=CodeableConcept(coding=[imaging_performed.to_coding()]),
        result=[Reference(reference=bleeding_volume_follow_up_ref)]
    )
    
    if hydrocephalus is not None:
        hydrocephalus_code = CodeableConcept(coding=[SpecificFinding.HYDROCEPHALUS.to_coding()])
        diagnostic_report.conclusionCode = [hydrocephalus_code]
    
    return diagnostic_report