"""
Procedure resource builders for FHIR transformation.
"""


from decimal import Decimal

from fhir.resources.procedure import Procedure, ProcedurePerformer
from fhir.resources.reference import Reference
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.range import Range
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.extension import Extension
from fhir.resources.period import Period
from fhir.resources.meta import Meta
from scripts.enum_models import (
    AssessmentContext, CarotidEndarterectomyTiming, IchTreatment, ImagingDone, ImagingType, NoThrombectomyReason, NoThrombolysisReason, PostAcuteCare, PostNeurosurgeryImaging, PostRecanalizationImaging, PostStrokeProcedures, ProcedureNotDoneReason, SwallowingScreeningDone,SwallowingScreeningType,
    SwallowingScreeningTiming, PerforationProcedures, ThrombectomyComplications, VteProcedures
)
from scripts.utils import parse_datetime


def build_imaging_procedure(patient_ref: str, encounter_ref: str, diagnostic_report_ref: str | None, imaging_done: ImagingDone | None, imaging_type: ImagingType | None, post_acute_care: bool, imaging_timestamp: str | None) -> Procedure:
    """
    Build a FHIR Procedure resource for imaging.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        diagnostic_report_ref: Reference to the DiagnosticReport resource
        imaging_done: ID of the imaging done status
        imaging_type: ID of the imaging type
        post_acute_care: ID of the post-acute care status
        imaging_timestamp: Timestamp of the imaging procedure
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource

    Returns:
        Procedure resource for imaging
    """
    procedure_final = Procedure(
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        status="completed"
    )
    if diagnostic_report_ref:
        procedure_final.report = [Reference(reference=diagnostic_report_ref)]
    
    if imaging_done is not None:
        status_reason = None

        if imaging_done == ImagingDone.YES:
            procedure_final.status = "completed"
        
        if imaging_done == ImagingDone.NO:
                status_reason = ProcedureNotDoneReason.UNKNOWN
                procedure_final.status = "not-done"
        elif imaging_done == ImagingDone.ELSEWHERE:
                status_reason = ProcedureNotDoneReason.DONE_ELSEWHERE
            
        if status_reason is not None:
            status_reason_coding = Coding(
                    system=status_reason.system,
                    code=status_reason.code,
                    display=status_reason.display
                )
            status_reason_code = CodeableConcept(coding=[status_reason_coding])
            procedure_final.statusReason = status_reason_code
            
        if imaging_type is not None:
            imaging_code = CodeableConcept(coding=[imaging_type.to_coding()])
            procedure_final.code = imaging_code
        
        category_coding = Coding(
            system="http://terminology.hl7.org/CodeSystem/observation-category",
            code="imaging",
            display="Imaging"
        )
        category_code = CodeableConcept(coding=[category_coding])
        procedure_final.category = [category_code]
        
        if post_acute_care :
            post_acute_care_code = CodeableConcept(coding=[PostAcuteCare.TRUE.to_coding()])
        else:
            post_acute_care_code = CodeableConcept(coding=[PostAcuteCare.FALSE.to_coding()])

        extension_list = [Extension(
            url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
            valueCodeableConcept=post_acute_care_code
        )]
        
        procedure_final.extension = extension_list
        
        if imaging_timestamp is not None:   
            imaging_timestamp_parsed = parse_datetime(imaging_timestamp)
            procedure_final.occurrenceDateTime = imaging_timestamp_parsed
    
    return procedure_final


def build_carotid_imaging_procedure(patient_ref: str, encounter_ref: str, diagnostic_report_ref: str, carotid_arteries_imaging_done: bool) -> Procedure:
    """
    Build a FHIR Procedure resource for carotid imaging.
    
    Args:
        raw: Raw procedure data dictionary
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        diagnostic_report_ref: Reference to the DiagnosticReport resource
        done_value: Boolean indicating if procedure was performed
        
    Returns:
        Procedure resource for carotid imaging
    """
    procedure = Procedure(status="completed", 
                          subject=Reference(reference=patient_ref),
                          encounter=Reference(reference=encounter_ref),
                          meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-carotid-imaging-procedure-profile"])
                          )


    code_carotid = CodeableConcept(coding=[ImagingType.CAROTID.to_coding()])
        
    extension_list = [Extension(
        url="http://tecnomod-um.org/StructureDefinition/post-acute-care-required-ext",
        valueBoolean=True
    )]
    
    if carotid_arteries_imaging_done is True:
        status_value = "completed"
        procedure.report = [Reference(reference=diagnostic_report_ref)]

    elif not carotid_arteries_imaging_done is False:
        status_value = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        procedure.statusReason = code_status_reason
    else:
        status_value = "unknown"

    procedure.status = status_value
    procedure.extension = extension_list
    procedure.code = code_carotid

    return procedure


def build_endarterectomy_procedure(patient_ref: str, encounter_ref: str, diagnostic_report_ref: str, carotid_endarterectomy: bool | None, carotid_endarterectomy_timing: CarotidEndarterectomyTiming | None) -> Procedure:
    """
    Build a FHIR Procedure resource for carotid endarterectomy.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        diagnostic_report_ref: Reference to the DiagnosticReport resource
        carotid_endarterectomy: Whether carotid endarterectomy was performed
        carotid_endarterectomy_timing: Timing of the carotid endarterectomy procedure
    Returns:
        Procedure resource for carotid endarterectomy
    """
    procedure = Procedure(
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        status="completed",
        meta=Meta(profile = ["http://tecnomod-um.org/StructureDefinition/stroke-carotid-endarterectomy-procedure-profile"]),
        report = [Reference(reference=diagnostic_report_ref)])
    
    code_endarterectomy = CodeableConcept(coding=[PerforationProcedures.ENDARTERECTOMY.to_coding()])
    
    
    extension_list = [Extension(
        url="http://tecnomod-um.org/StructureDefinition/post-acute-care-required-ext",
        valueBoolean=True
    )]
    
    if carotid_endarterectomy is True:
        status_value = "completed"

        if carotid_endarterectomy_timing is not None:
            if carotid_endarterectomy_timing == CarotidEndarterectomyTiming.IN_24_HOURS:
                procedure.occurrenceRange = Range(high=Quantity(value=Decimal(24), unit="h", system="http://unitsofmeasure.org", code="h", comparator="<="))
            elif carotid_endarterectomy_timing == CarotidEndarterectomyTiming.HOURS_TO_WEEKS:
                procedure.occurrenceRange = Range(low=Quantity(value=Decimal(24), unit="h", system="http://unitsofmeasure.org", code="h", comparator=">"), high=Quantity(value=Decimal(2), unit="wk", system="http://unitsofmeasure.org", code="wk", comparator="<="))
            elif carotid_endarterectomy_timing == CarotidEndarterectomyTiming.AFTER_WEEKS:
                procedure.occurrenceRange = Range(low=Quantity(value=Decimal(2), unit="wk", system="http://unitsofmeasure.org", code="wk", comparator=">"))

    elif not carotid_endarterectomy is False:
        status_value = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        procedure.statusReason = code_status_reason
    else:
        status_value = "unknown"

    procedure.status = status_value
    procedure.extension = extension_list
    procedure.code = code_endarterectomy

    return procedure

def build_swallowing_screening_procedure(patient_ref: str, encounter_ref: str, practitioner_role_ref: str | None, swallowing_screening_done: SwallowingScreeningDone | None = None, swallowing_screening_type: SwallowingScreeningType | None = None, swallowing_screening_timing: SwallowingScreeningTiming | None = None) -> Procedure:
    """
    Build a FHIR Procedure resource for swallowing screening.
    
    Args:
        raw: Raw procedure data dictionary
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        practitioner_role_ref: Reference to the PractitionerRole resource
        swallowing_screening_done: Whether the swallowing screening was performed
        swallowing_screening_type: The type of swallowing screening performed
        swallowing_screening_timing: The timing of the swallowing screening performed
        
    Returns:
        Procedure resource for swallowing screening
    """
    procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    procedure.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-swallow-procedure-profile"])
    
    if swallowing_screening_done is SwallowingScreeningDone.YES:
        if swallowing_screening_type is not None:
        #     swallowing_type_coding = SwallowingScreeningType.OTHER.to_coding()
        # else:
            swallowing_type_coding = swallowing_screening_type.to_coding()
            procedure.code = CodeableConcept(coding=[swallowing_type_coding])

        if practitioner_role_ref is not None:
            procedure.performer = [ProcedurePerformer(actor=Reference(reference=practitioner_role_ref))]
        procedure.status = "completed"
    elif swallowing_screening_done is SwallowingScreeningDone.NO:
        procedure.status = "not-done"
        status_reason_code = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        procedure.statusReason = status_reason_code
    elif swallowing_screening_done is SwallowingScreeningDone.NOT_APPLICABLE:
        procedure.status = "not-done"
        status_reason_code = CodeableConcept(coding=[ProcedureNotDoneReason.NOT_APPLICABLE.to_coding()])
        procedure.statusReason = status_reason_code
        return procedure
     
    else:
        procedure.status = "unknown"
        return procedure
    
    extension_list = []
    if swallowing_screening_timing is not None:
         swallowing_screening_timing_coding = swallowing_screening_timing.to_coding()
         timing_ext = Extension(
            url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
            valueCodeableConcept=CodeableConcept(coding=[swallowing_screening_timing_coding])
         )
         extension_list.append(timing_ext)
        
    extension_list.append(Extension(
        url="http://tecnomod-um.org/StructureDefinition/post-acute-care-required-ext",
        valueBoolean=True
    ))
    
    if len(extension_list) > 0:
        procedure.extension = extension_list


    return procedure



def build_thrombolysis_procedure(patient_ref: str, encounter_ref: str, condition_ref: str, location_ref: str | None = None, thrombolysis: bool | None = None, post_acute_care: bool = False, no_thrombolysis_reason_id: NoThrombolysisReason | None = None, bolus_timestamp:str|None = None) -> Procedure:
    """
    Build a FHIR Procedure resource for thrombolysis.
    
    Args:
        thrombolysis: Whether thrombolysis was performed
        post_acute_care: Whether post-acute care was provided
        no_thrombolysis_reason_id: ID of the reason for not performing thrombolysis
        bolus_timestamp: Timestamp of the bolus event
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
    Returns:
        Procedure resource for thrombolysis
    """
    procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason=[CodeableReference(reference=Reference(reference=condition_ref))]
    )
    procedure.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-mechanical-procedure-profile"])
    
    thrombolysis_coding = PerforationProcedures.THROMBOLYSIS.to_coding()
    procedure.code = CodeableConcept(coding=[thrombolysis_coding])
    
    extension_list = []
    if post_acute_care is True:
        post_acute_care_coding = PostAcuteCare.TRUE.to_coding()
    else:
        post_acute_care_coding = PostAcuteCare.FALSE.to_coding()
        code_post_acute = CodeableConcept(coding=[post_acute_care_coding])
        extension_list.append(Extension(
            url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
            valueCodeableConcept=code_post_acute
        ))
    
    if len(extension_list) > 0:
        procedure.extension = extension_list
    if location_ref is not None:
        procedure.location = Reference(reference=location_ref)
    if thrombolysis is None and no_thrombolysis_reason_id is None:
        procedure.status = "unknown"
        return procedure
    elif thrombolysis is None or thrombolysis is False:
        if no_thrombolysis_reason_id is not None:
            code_reason = CodeableConcept(coding=[no_thrombolysis_reason_id.to_coding()])
            procedure.status = "not-done"
            procedure.statusReason = code_reason
            return procedure
        else:
            code_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
            procedure.status = "not-done"
            procedure.statusReason = code_reason
            return procedure
    else:
        if bolus_timestamp is not None:
            bolus_timestamp_dt = parse_datetime(bolus_timestamp)
            procedure.occurrencePeriod = Period(start=bolus_timestamp_dt)
        return procedure


def build_thrombectomy_procedure(thrombectomy: bool, post_acute_care: bool, patient_ref: str, encounter_ref: str, condition_ref: str, no_thrombectomy_reason_id : NoThrombectomyReason | None = None, reperfusion_timestamp = None, puncture_timestamp = None, mt_complications_perforation: bool = False, mt_complications_dissection: bool = False, mt_complications_hematoma: bool = False, mt_complications_embolism: bool = False, mt_complications_other: bool = False, transfer_timestamp: str | None = None) -> Procedure:
    """
    Build a FHIR Procedure resource for thrombectomy.
    
    Args:
        thrombectomy: Whether the thrombectomy procedure was performed
        post_acute_care: Whether the patient received post-acute care
        no_thrombectomy_reason_id: ID of the reason why thrombectomy was not performed
        reperfusion_timestamp: Timestamp of the reperfusion event
        puncture_timestamp: Timestamp of the puncture event
        mt_complications_perforation: Whether the patient experienced perforation complications
        mt_complications_dissection: Whether the patient experienced dissection complications
        mt_complications_hematoma: Whether the patient experienced hematoma complications
        mt_complications_embolism: Whether the patient experienced embolism complications
        mt_complications_other: Whether the patient experienced other complications
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        transfer_timestamp: Timestamp of the transfer if was done elsewhere
    Returns:
        Procedure resource for thrombectomy
    """

    procedure = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    procedure.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-mechanical-procedure-profile"])
    
    
    code_thrombectomy = CodeableConcept(coding=[PerforationProcedures.THROMBECTOMY.to_coding()])
    procedure.code = code_thrombectomy

    extension_list = []

    extension_list.append(Extension(
        url="http://tecnomod-um.org/StructureDefinition/post-acute-care-required-ext",
        valueBoolean = post_acute_care
    ))
    
    if len(extension_list) > 0:
        procedure.extension = extension_list

    if thrombectomy is False or thrombectomy is None :
        if no_thrombectomy_reason_id is True or no_thrombectomy_reason_id is None:
            no_thrombectomy_reason_coding = ProcedureNotDoneReason.UNKNOWN.to_coding()
        else:
            no_thrombectomy_reason_coding = no_thrombectomy_reason_id.to_coding()
            procedure.status = "not-done"
            if no_thrombectomy_reason_coding == NoThrombectomyReason.TRANSFERRED_ELSEWHERE_IVT:
                if transfer_timestamp is not None:
                    procedure.occurrenceDateTime = parse_datetime(transfer_timestamp)
                procedure.status = "on-hold"

        code_reason = CodeableConcept(coding=[no_thrombectomy_reason_coding])
        procedure.statusReason = code_reason
        return procedure
    
    if thrombectomy is True:
        procedure.status = "completed"
        if puncture_timestamp is not None and reperfusion_timestamp is not None:
            puncture_timestamp_dt = parse_datetime(puncture_timestamp)
            reperfusion_timestamp_dt = parse_datetime(reperfusion_timestamp)
            procedure.occurrencePeriod = Period(start=puncture_timestamp_dt, end=reperfusion_timestamp_dt)

        if  mt_complications_perforation is True:
            perforation_coding = ThrombectomyComplications.PERFORATION.to_coding()
            code_perforation = CodeableConcept(coding=[perforation_coding])
            code_ref_perforation = CodeableReference(concept=code_perforation, reference=Reference(reference=condition_ref))
            procedure.complication = [code_ref_perforation]
        elif mt_complications_dissection is True:
            dissection_coding = ThrombectomyComplications.DISSECTION.to_coding()
            code_dissection = CodeableConcept(coding=[dissection_coding])
            code_ref_dissection = CodeableReference(concept=code_dissection, reference=Reference(reference=condition_ref))
            procedure.complication = [code_ref_dissection]
        elif mt_complications_hematoma is True:
            hematoma_coding = ThrombectomyComplications.HEMATOMA.to_coding()
            code_hematoma = CodeableConcept(coding=[hematoma_coding])
            code_ref_hematoma = CodeableReference(concept=code_hematoma, reference=Reference(reference=condition_ref))
            procedure.complication = [code_ref_hematoma]
        elif mt_complications_embolism is True:
            embolism_coding = ThrombectomyComplications.EMBOLISM.to_coding()
            code_embolism = CodeableConcept(coding=[embolism_coding])
            code_ref_embolism = CodeableReference(concept=code_embolism, reference=Reference(reference=condition_ref))
            procedure.complication = [code_ref_embolism]
        elif mt_complications_other is True:
            other_coding = ThrombectomyComplications.OTHER.to_coding()
            code_other = CodeableConcept(coding=[other_coding])
            code_ref_other = CodeableReference(concept=code_other, reference=Reference(reference=condition_ref))
            procedure.complication = [code_ref_other]
  
    return procedure


def build_ivt_procedure(ivt_antidote_given:bool, ivt_application_dep_ref: str, antidote_ref: str, patient_ref: str, encounter_ref: str) -> Procedure:
    """
    Build a FHIR Procedure resource for IVT administration.
    
    Args:
        ivt_antidote_given: Whether an antidote was given for IVT
        ivt_application_dep_ref: Reference to the department where IVT was administered
        antidote_ref: Reference to the MedicationAdministration resource
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
    Returns:
        Procedure resource for IVT administration
    """

    procedure= Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref))
    
    procedure.code = CodeableConcept(coding=[PerforationProcedures.ANTIDOTE.to_coding()])

    if ivt_antidote_given is True:
        procedure.status = "completed"
    else: 
        procedure.status = "not-done"
    
    procedure.location = Reference(reference=ivt_application_dep_ref)
    procedure.partOf = [Reference(reference=antidote_ref)]

    return procedure

def build_vte_procedure(patient_ref: str, encounter_ref: str, thromboembolism_procedure: bool | None = False, vte_gcs: bool| None = False, vte_ipc: bool | None = False, vte_lmwh: bool | None = False, vte_other: bool | None = False, vte_ufh: bool | None = False, vte_vfp : bool | None = False, vte_warfarin : bool | None = False, vte_xa_inhibitor: bool | None = False ) -> list[Procedure]:
    """
    Build FHIR Procedure resources for VTE prophylaxis.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        thromboembolism_procedure: Whether a thromboembolism intervention was performed
        vte_gcs: Whether graduated compression stockings were used
        vte_ipc: Whether intermittent pneumatic compression was used
        vte_lmwh: Whether low molecular weight heparin was used
        vte_other: Whether other VTE prophylaxis was used
        vte_ufh: Whether unfractionated heparin was used
        vte_vfp: Whether vena cava filter placement was performed
        vte_warfarin: Whether warfarin was used
        vte_xa_inhibitor: Whether a factor Xa inhibitor was used
    Returns:
        List of Procedure resources for VTE prophylaxis: vte_gcs_procedure, vte_ipc_procedure, vte_lmwh_procedure, vte_other_procedure, vte_ufh_procedure, vte_vfp_procedure, vte_warfarin_procedure, vte_xa_inhibitor_procedure
    """

    if thromboembolism_procedure is False : 
        return [
            Procedure(
                status="not-done",
                code=CodeableConcept(coding=[VteProcedures.VTE_INTERVENTION.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            )]
    else:
        procedure_list = []
        if vte_gcs is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.STOCKINGS.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
        if vte_ipc is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.IPC.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
        if vte_lmwh is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.LMWH.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
        if vte_other is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.OTHER.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
        if vte_ufh is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.UFH.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
        if vte_vfp is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.VFP.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
        if vte_warfarin is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.VTE_WARFARIN.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
        if vte_xa_inhibitor is True:
            procedure_list.append(Procedure(
                status="completed",
                code=CodeableConcept(coding=[VteProcedures.XA_INHIBITOR.to_coding()]),
                subject=Reference(reference=patient_ref),
                encounter=Reference(reference=encounter_ref),
                meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-vte-procedure-profile"]),
            ))
    return procedure_list


def build_ich_treatment_procedure( patient_ref: str, encounter_ref: str, condition_ref: str, ich_treatment_any: bool | None = False, ich_treatment_craniectomy: bool | None= False, ich_treatment_stereotactic_aspiration: bool | None = False, ich_treatment_ventricular_drainage: bool | None = False, ich_treatment_hematoma_evacuation: bool | None = False, ich_treatment_open_craniectomy: bool | None = False, ich_treatment_min_invasive: bool | None = False, ich_treatment_evacuation_timestamp: str | None = None, no_ich_treatment_reason: ProcedureNotDoneReason | None = None) -> list[tuple[bool, Procedure]]:
    """
    Build a FHIR Procedure resources for ICH treatment.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        ich_treatment_craniectomy: Whether a craniectomy was performed
        ich_treatment_stereotactic_aspiration: Whether stereotactic aspiration was performed
        ich_treatment_ventricular_drainage: Whether ventricular drainage was performed
        ich_treatment_hematoma_evacuation: Whether hematoma evacuation was performed
        ich_treatment_open_craniectomy: Whether open craniectomy was performed
        ich_treatment_min_invasive: Whether minimally invasive procedure was performed
        ich_treatment_evacuation_timestamp: Timestamp of the ICH evacuation procedure
        no_ich_treatment_reason: Reason for not performing ICH treatment
    Returns:
        Procedure resources for ICH treatments in the following order: procedure_craniectomy, procedure_stereotactic_aspiration, procedure_ventricular_drainage, procedure_hematoma_evacuation, procedure_open_craniectomy, procedure_min_invasive
    """
    procedure_craniectomy = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code=CodeableConcept(coding=[IchTreatment.CRANIECTOMY.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    procedure_hematoma_evacuation = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code=CodeableConcept(coding=[IchTreatment.HEMATOMA_EVACUATION.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    procedure_open_craniectomy = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code=CodeableConcept(coding=[IchTreatment.OPEN_CRANIECTOMY.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    
    procedure_stereotactic_aspiration = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code=CodeableConcept(coding=[IchTreatment.STEREOTACTIC_ASPIRATION.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )
    
    procedure_ventricular_drainage = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code=CodeableConcept(coding=[IchTreatment.VENTRICULAR_DRAINAGE.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    procedure_min_invasive = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code=CodeableConcept(coding=[IchTreatment.MIN_INVASIVE.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )
    

    if ich_treatment_any is False :
        for proc in [procedure_craniectomy, procedure_stereotactic_aspiration, procedure_ventricular_drainage, procedure_hematoma_evacuation, procedure_open_craniectomy]:
            if no_ich_treatment_reason is not None:
                proc.statusReason = CodeableConcept(coding=[no_ich_treatment_reason.to_coding()])
            else:
                proc.statusReason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        return [(False, procedure_craniectomy), (False, procedure_stereotactic_aspiration), (False, procedure_ventricular_drainage), (False, procedure_hematoma_evacuation), (False, procedure_open_craniectomy)]
    

    procedures = [
        (ich_treatment_craniectomy, procedure_craniectomy),
        (ich_treatment_stereotactic_aspiration, procedure_stereotactic_aspiration),
        (ich_treatment_ventricular_drainage, procedure_ventricular_drainage),
        (ich_treatment_hematoma_evacuation, procedure_hematoma_evacuation),
        (ich_treatment_open_craniectomy, procedure_open_craniectomy),
        (ich_treatment_min_invasive, procedure_min_invasive),
    ]
    for done, procedure in procedures:
        if done is True:
            procedure.status = "completed"
            if ich_treatment_evacuation_timestamp is not None:
                procedure.occurrenceDateTime = parse_datetime(ich_treatment_evacuation_timestamp)

    
    return [(False, procedure_craniectomy), (False, procedure_stereotactic_aspiration), (False, procedure_ventricular_drainage), (True, procedure_hematoma_evacuation), (False, procedure_open_craniectomy), (False, procedure_min_invasive)]


def build_sah_treatment_procedure(patient_ref: str, encounter_ref: str, condition_ref: str, sah_treatment_any: bool = False, sah_treatment_clipping: bool | None = False, sah_treatment_coiling: bool | None = False, sah_treatment_craniectomy: bool | None = False, sah_treatment_drainage: bool | None = False, sah_treatment_other: bool | None = False) -> list[Procedure]:
    """
    Build FHIR Procedure resources for SAH treatment.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        sah_treatment_any: Whether any SAH treatment was performed
        sah_treatment_clipping: Whether clipping treatment was performed
        sah_treatment_coiling: Whether coiling treatment was performed
        sah_treatment_craniectomy: Whether craniectomy treatment was performed
        sah_treatment_drainage: Whether drainage treatment was performed
        sah_treatment_other: Whether other treatment was performed

    Returns:
        Procedure resources for SAH treatments: sah_treatment_clipping_procedure, sah_treatment_coiling_procedure, sah_treatment_craniectomy_procedure, sah_treatment_drainage_procedure, sah_treatment_other_procedure
    """

    procedure_clipping = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code = CodeableConcept(coding=[IchTreatment.CLIPPING.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )
    procedure_coiling = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code = CodeableConcept(coding=[IchTreatment.COILING.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )
    procedure_craniectomy = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code = CodeableConcept(coding=[IchTreatment.CRANIECTOMY.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )
    procedure_drainage = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code = CodeableConcept(coding=[IchTreatment.VENTRICULAR_DRAINAGE.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )
    procedure_other = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code = CodeableConcept(coding=[IchTreatment.OTHER.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    
    if sah_treatment_any is False:
        for proc in [procedure_clipping, procedure_coiling, procedure_craniectomy, procedure_drainage, procedure_other]:
            proc.status = "not-done"
            proc.statusReason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        return [procedure_clipping, procedure_coiling, procedure_craniectomy, procedure_drainage, procedure_other]
    else:
        if sah_treatment_clipping is True:
            procedure_clipping.status = "completed"
        if sah_treatment_coiling is True:
            procedure_coiling.status = "completed"
        if sah_treatment_craniectomy is True:
            procedure_craniectomy.status = "completed"
        if sah_treatment_drainage is True:
            procedure_drainage.status = "completed"
        if sah_treatment_other is True:
            procedure_other.status = "completed"
    
    return [procedure_clipping, procedure_coiling, procedure_craniectomy, procedure_drainage, procedure_other]


def build_cvt_treatment_procedure(patient_ref: str, encounter_ref: str, condition_ref: str, cvt_treatment_any: bool = False, cvt_treatment_neurosurgery: bool | None = False, cvt_treatment_thrombectomy: bool | None = False, cvt_treatment_thrombolysis: bool | None = False, cvt_treatment_anticoagulation: bool | None = False) -> list[Procedure]:
    """
    Build FHIR Procedure resources for CVT treatment.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        cvt_treatment_any: Whether any CVT treatment was performed
        cvt_treatment_neurosurgery: Whether neurosurgery was performed
        cvt_treatment_thrombectomy: Whether thrombectomy was performed
        cvt_treatment_thrombolysis: Whether thrombolysis was performed
        cvt_treatment_anticoagulation: Whether anticoagulation was performed
    Returns:
        Procedure resources for CVT treatments: cvt_treatment_neurosurgery_procedure, cvt_treatment_thrombectomy_procedure, cvt_treatment_thrombolysis_procedure, cvt_treatment_anticoagulation_procedure
    """ 

    procedure_neurosurgery = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code= CodeableConcept(coding=[IchTreatment.CRANIECTOMY.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    procedure_thrombectomy = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code= CodeableConcept(coding=[PerforationProcedures.THROMBECTOMY.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    procedure_thrombolysis = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code= CodeableConcept(coding=[PerforationProcedures.THROMBOLYSIS.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"])
    )

    procedure_anticoagulation = Procedure(
        status="not-done",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason = [CodeableReference(reference=Reference(reference=condition_ref))],
        code= CodeableConcept(coding=[IchTreatment.ANTICOAGULATION.to_coding()]),
        meta=Meta(profile=["http://tecnomod-um.org/StructureDefinition/stroke-treatment-procedure-profile"]),
        partOf=[Reference(reference=condition_ref)]
    )

    
    if cvt_treatment_any is False:
        for proc in [procedure_neurosurgery, procedure_thrombectomy, procedure_thrombolysis, procedure_anticoagulation]:
            proc.status = "not-done"
            proc.statusReason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])

        return [procedure_neurosurgery, procedure_thrombectomy, procedure_thrombolysis, procedure_anticoagulation]
            
    else:   
        if cvt_treatment_neurosurgery is True:
            procedure_neurosurgery.status = "completed"
        if cvt_treatment_thrombectomy is True:
            procedure_thrombectomy.status = "completed"
        if cvt_treatment_thrombolysis is True:
            procedure_thrombolysis.status = "completed"
        if cvt_treatment_anticoagulation is True:
            procedure_anticoagulation.status = "completed"
        
    return [procedure_neurosurgery, procedure_thrombectomy, procedure_thrombolysis, procedure_anticoagulation]



def build_craniectomy_procedure(patient_ref: str, encounter_ref: str, condition_ref: str | None, craniectomy_performed: bool) -> Procedure:
    """
    Build a FHIR Procedure resource for craniectomy.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        craniectomy_performed: Whether craniectomy was performed
        craniectomy_timing: Timing of the craniectomy procedure
        post_acute_care: Whether post-acute care was provided
    Returns:
        Procedure resource for craniectomy
    """
    procedure = Procedure(
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason=[CodeableReference(reference=Reference(reference=condition_ref))],
        status="completed"
    )
    
    code_craniectomy = CodeableConcept(coding=[IchTreatment.CRANIECTOMY.to_coding()])
    procedure.code = code_craniectomy
    
    if craniectomy_performed is False:
        procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        procedure.statusReason = code_status_reason

    return procedure

def build_post_neurosurgery_imaging_procedure(patient_ref: str, encounter_ref: str, condition_ref: str | None, post_neurosurgery_imaging_done: PostNeurosurgeryImaging) -> Procedure:
    """
    Build a FHIR Procedure resource for post-neurosurgery imaging.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        post_neurosurgery_imaging_done: Whether post-neurosurgery imaging was done
    Returns:
        Procedure resource for post-neurosurgery imaging
    """
    procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason=[CodeableReference(reference=Reference(reference=condition_ref))]
    )
    procedure.code = CodeableConcept(coding=[post_neurosurgery_imaging_done.to_coding()])
    if post_neurosurgery_imaging_done is False:
        procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        procedure.statusReason = code_status_reason

    return procedure

def build_post_recanalization_imaging_procedure(patient_ref: str, encounter_ref: str, condition_ref: str | None, post_recanalization_imaging_done: PostRecanalizationImaging) -> Procedure:
    """
    Build a FHIR Procedure resource for post-recanalization imaging.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        post_recanalization_imaging_done: Whether post-recanalization imaging was done
    Returns:
        Procedure resource for post-recanalization imaging
    """
    procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason=[CodeableReference(reference=Reference(reference=condition_ref))]
    )
    procedure.code = CodeableConcept(coding=[post_recanalization_imaging_done.to_coding()])
    if post_recanalization_imaging_done is False:
        procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        procedure.statusReason = code_status_reason

    return procedure

def build_physioterapy_procedure(patient_ref: str, encounter_ref: str, physiotherapy: str) -> Procedure:
    """
    Build a FHIR Procedure resource for physiotherapy.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        physiotherapy: Whether physiotherapy was performed
    Returns:
        Procedure resource for physiotherapy
    """
    physiotherapy_procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    physiotherapy_procedure.code = CodeableConcept(coding=[PostStrokeProcedures.PHYSIOTHERAPY.to_coding()])
    if physiotherapy == "no":
        physiotherapy_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        physiotherapy_procedure.statusReason = code_status_reason
    elif physiotherapy == "not required":
        physiotherapy_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.NOT_REQUIRED.to_coding()])
        physiotherapy_procedure.statusReason = code_status_reason

    physiotherapy_procedure.extension = [Extension(
        url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.POST_STROKE.to_coding()])
    )]

    return physiotherapy_procedure

def build_occupational_therapy_procedure(patient_ref: str, encounter_ref: str, occupational_therapy: str) -> Procedure:
    """
    Build a FHIR Procedure resource for occupational therapy.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        occupational_therapy: Whether occupational therapy was performed
    Returns:
        Procedure resource for occupational therapy
    """
    occupational_therapy_procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    occupational_therapy_procedure.code = CodeableConcept(coding=[PostStrokeProcedures.OCCUPATIONAL_THERAPY.to_coding()])

    if occupational_therapy == "no":
        occupational_therapy_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        occupational_therapy_procedure.statusReason = code_status_reason
    elif occupational_therapy == "not required":
        occupational_therapy_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.NOT_REQUIRED.to_coding()])
        occupational_therapy_procedure.statusReason = code_status_reason
    
    occupational_therapy_procedure.extension = [Extension(
        url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.POST_STROKE.to_coding()])
    )]
    

    return occupational_therapy_procedure

def build_speech_therapy_procedure(patient_ref: str, encounter_ref: str, speech_therapy: str) -> Procedure:
    """
    Build a FHIR Procedure resource for speech therapy.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        speech_therapy: Whether speech therapy was performed
    Returns:
        Procedure resource for speech therapy
    """
    speech_therapy_procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    speech_therapy_procedure.code = CodeableConcept(coding=[PostStrokeProcedures.SPEECH_THERAPY.to_coding()])
    if speech_therapy == "no":
        speech_therapy_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        speech_therapy_procedure.statusReason = code_status_reason
    elif speech_therapy == "not required":
        speech_therapy_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.NOT_REQUIRED.to_coding()])
        speech_therapy_procedure.statusReason = code_status_reason

    speech_therapy_procedure.extension = [Extension(
        url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.POST_STROKE.to_coding()])
    )]

    return speech_therapy_procedure

def build_smoking_cessation_procedure(patient_ref: str, encounter_ref: str, smoking_cessation: bool) -> Procedure:
    """
    Build a FHIR Procedure resource for smoking cessation counseling.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        smoking_cessation: Whether smoking cessation counseling was provided
    Returns:
        Procedure resource for smoking cessation counseling
    """
    smoking_cessation_procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref)
    )
    smoking_cessation_procedure.code = CodeableConcept(coding=[PostStrokeProcedures.SMOKING_CESSATION.to_coding()])
    if smoking_cessation is False:
        smoking_cessation_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        smoking_cessation_procedure.statusReason = code_status_reason

    smoking_cessation_procedure.extension = [Extension(
        url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.POST_STROKE.to_coding()])
    )]

    return smoking_cessation_procedure


def build_hydrocephalus_shunt_procedure(patient_ref: str, encounter_ref: str, condition_ref: str, hydrocephalus_shunt: bool) -> Procedure:
    """
    Build a FHIR Procedure resource for hydrocephalus shunt placement.
    
    Args:
        patient_ref: Reference to the Patient resource
        encounter_ref: Reference to the Encounter resource
        condition_ref: Reference to the Condition resource
        hydrocephalus_shunt: Whether a hydrocephalus shunt was placed
    Returns:
        Procedure resource for hydrocephalus shunt placement
    """
    hydrocephalus_shunt_procedure = Procedure(
        status="completed",
        subject=Reference(reference=patient_ref),
        encounter=Reference(reference=encounter_ref),
        reason=[CodeableReference(reference=Reference(reference=condition_ref))]
    )
    hydrocephalus_shunt_procedure.code = CodeableConcept(coding=[PostStrokeProcedures.VENTRICULOPERITONEAL_SHUNT.to_coding()])
    if hydrocephalus_shunt is False:
        hydrocephalus_shunt_procedure.status = "not-done"
        code_status_reason = CodeableConcept(coding=[ProcedureNotDoneReason.UNKNOWN.to_coding()])
        hydrocephalus_shunt_procedure.statusReason = code_status_reason

    hydrocephalus_shunt_procedure.extension = [Extension(
        url="http://tecnomod-um.org/StructureDefinition/procedure-timing-context-ext",
        valueCodeableConcept=CodeableConcept(coding=[AssessmentContext.POST_STROKE.to_coding()])
    )]

    return hydrocephalus_shunt_procedure
