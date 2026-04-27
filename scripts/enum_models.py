from enum import Enum, unique
import json
from typing import TypeVar, overload
from fhir.resources.coding import Coding

TConceptEnum = TypeVar("TConceptEnum", bound="ConceptEnum")

class ConceptEnum(Enum):
    """
    Base generic for enums whose values are dicts
    with the keys 'code', 'display', and 'system'.
    Provides .code, .display, .system, and .to_coding().
    """
    id: str
    code: str
    display: str
    system: str

    def __new__(cls, id: str, value: dict):
        obj = object.__new__(cls)
        obj._value_ = value      # <-- aquí vive el dict
        obj.id = id
        obj.code    = value["code"]
        obj.display = value["display"]
        obj.system  = value["system"]
        
        return obj
    @overload
    @classmethod
    def by_id(cls: type[TConceptEnum], id_str: None) -> None:
        ...

    @overload
    @classmethod
    def by_id(cls: type[TConceptEnum], id_str: str) -> TConceptEnum:
        ...

    @classmethod
    def by_id(cls: type[TConceptEnum], id_str: str | None) -> TConceptEnum | None:
        """Returns the Enum member whose .id == id_str."""
        if id_str is None:
            return None
        for m in cls:
            if m.id == id_str:
                return m
        raise KeyError(f"{cls.__name__}: id not found -> {id_str}")
    
    @classmethod
    def dict_by_id(cls, id_str) -> dict:
        """Returns the dict (not serialized) associated with the id."""
        if id_str is None:
            return dict()
        else:
            return cls.by_id(id_str).value
    
    @classmethod
    def json_by_id(cls, id_str: str) -> str:
        """Returns the JSON (string) associated with the id."""
        return json.dumps(cls.dict_by_id(id_str), ensure_ascii=False)

    def to_coding(self) -> Coding:
        """Build and return a fhir.resources.Coding."""
        coding = Coding(
        system = self.system,
        code = self.code,
        display = self.display)
        return coding

class Sex(ConceptEnum):
    MALE   = ("Male", {"code" : "248153007", "display": "Male (finding)", "system": "http://snomed.info/sct"})
    FEMALE = ("Female", {"code" : "248152002", "display": "Female (finding)", "system": "http://snomed.info/sct"})
    OTHER  = ("Other", {"code" : "32570681000036106", "display": "Indeterminate sex (finding)", "system": "http://snomed.info/sct"})

class YesNoAnswers(ConceptEnum):
    YES = ("Yes", {"code": "yes", "display": "Yes", "system": "http://snomed.info/sct"})
    NO = ("No", {"code": "no", "display": "No", "system": "http://snomed.info/sct"})
    NOT_REQUIRED = ("Not Required", {"code": "not-required", "display": "Not Required", "system": "http://tecnomod-um.org/CodeSystem/yes-no-not-required-cs"})

class ThreeMonthContactMode(ConceptEnum):
    CLINIC = ("Clinic", {"code": "visit-clinic", "display": "Visit to Clinic", "system": "http://tecnomod-um.org/CodeSystem/three-month-contact-mode-cs"})
    NOT_CONTACTED = ("Not Contacted", {"code": "not-contacted", "display": "Not Contacted", "system": "http://tecnomod-um.org/CodeSystem/three-month-contact-mode-cs"})
    WEB_APP = ("Web App", {"code": "706690007", "display": "Web-based application software (physical object)", "system": "http://snomed.info/sct"})
    TELEMEDICINE = ("Telemedicine", {"code": "466583009", "display": "Video conferencing telemedicine system (physical object)", "system": "http://snomed.info/sct"})
    NO_RESPONSE = ("No Response", {"code": "no-response", "display": "No Response", "system": "http://tecnomod-um.org/CodeSystem/three-month-contact-mode-cs"})
    

class ArrivalMode(ConceptEnum):
    EMS_GP = ("Emergency Medical Services from GP", {"code": "ems-gp", "display": "EMS from GP", "system": "http://tecnomod-um.org/CodeSystem/stroke-arrival-mode-cs"})
    PRIVATE_TRANSPORTATION_HOME = ("Private Transportation Home", {"code": "priv-transport-home", "display": "Private Transportation from Home/Scene", "system": "http://tecnomod-um.org/CodeSystem/stroke-arrival-mode-cs"})
    PRIVATE_TRANSPORTATION_GP = ("Private Transportation GP", {"code": "priv-transport-gp", "display": "Private Transportation from GP", "system": "http://tecnomod-um.org/CodeSystem/stroke-arrival-mode-cs"})
    STROKE_CENTER = ("Stroke Center", {"code": "stroke-center", "display": "Stroke Center", "system": "http://tecnomod-um.org/CodeSystem/stroke-arrival-mode-cs"})
    EMS_HOME = ("Emergency Medical Services from Home", {"code": "ems-home", "display": "EMS from Home", "system": "http://tecnomod-um.org/CodeSystem/stroke-arrival-mode-cs"})
    ANOTHER_HOSPITAL = ("Another Hospital", {"code": "another-hosp", "display": "Another Hospital", "system": "http://tecnomod-um.org/CodeSystem/stroke-arrival-mode-cs"})

class Locations(ConceptEnum):
    EMERGENCY= ("Emergency", {"code": "ER", "display": "Emergency room", "system": "http://tecnomod-um.org/CodeSystem/first-contact-place-cs"})
    OUTPATIENT = ("Outpatient", {"code": "OF", "display": "Outpatient facility", "system": "http://tecnomod-um.org/CodeSystem/first-contact-place-cs"})
    RADIOLOGY = ("Radiology", {"code": "HRAD", "display": "radiology unit", "system": "http://tecnomod-um.org/CodeSystem/first-contact-place-cs"})
    NEUROLOGY = ("Neurology", {"code": "NCCS", "display": "Neurology critical care and stroke unit", "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode"})
    ICU = ("Critical Care ICU", {"code": "ICU", "display": "Intensive Care Unit", "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode"})
    NEUROSURGERY = ("Neurosurgery", {"code": "NS", "display": "Neurosurgery unit", "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode"})
    INTERNAL_MEDICINE = ("Internal Medicine", {"code": "GIM", "display": "General internal medicine clinic", "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode"})
    OTHER = ("Other", {"code": "other", "display": "Other Department", "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode"})    

class FirstHospital(ConceptEnum):
    TRUE = ("True", {"code": "true", "display": "True", "system": "http://tecnomod-um.org/StructureDefinition/first-hospital-ext"})
    FALSE = ("False", {"code": "false", "display": "False", "system": "http://tecnomod-um.org/StructureDefinition/first-hospital-ext"})


class HospitalizedIn(ConceptEnum):
    ICU_STROKE_UNIT = ("ICU Stroke Unit", {"code": "icu-stroke", "display": "ICU / Stroke Unit", "system": "http://tecnomod-um.org/CodeSystem/initial-care-intensity-cs"})
    STANDARD = ("Standard", {"code": "standard", "display": "Standard Bed", "system": "http://tecnomod-um.org/CodeSystem/initial-care-intensity-cs"})
    MONITORED = ("Monitored", {"code": "monitored", "display": "Monitored Bed", "system": "http://tecnomod-um.org/CodeSystem/initial-care-intensity-cs"})

class ImagingDone(ConceptEnum):
    YES = ("Yes", {"code": "yes", "display": "Yes", "system": ""})
    NO = ("No", {"code": "no", "display": "No", "system": ""})
    ELSEWHERE = ("Elsewhere", {"code": "elsewhere", "display": "Elsewhere", "system": ""})


class InHospital(ConceptEnum):
    FALSE = ("False", {"code": "false", "display": "False", "system": "http://hl7.org/fhir/in-hospital"})
    TRUE = ("True", {"code": "true", "display": "True", "system": "http://hl7.org/fhir/in-hospital"})
    NONE = ("None", {"code": "none", "display": "None", "system": "http://hl7.org/fhir/in-hospital"})

class ImagingType(ConceptEnum):
    MR_MRA_PERFUSION = ("MR MRA Perfusion", {"code": "mr-dwi-flair-mra-perfusion", "display": "MR DWI-FLAIR, MRA, and Perfusion", "system": "http://tecnomod-um.org/CodeSystem/brain-imaging-type-cs"})
    CT_CTA_PERFUSION = ("CT CTA Perfusion", {"code": "ct-cta-perfusion", "display": "CT-CTA and Perfusion", "system": "http://tecnomod-um.org/CodeSystem/brain-imaging-type-cs"})
    CT_CTA = ("CT CTA", {"code": "ct-cta", "display": "Computed Tomography (CT) and CT Angiography (CTA)", "system": "http://tecnomod-um.org/CodeSystem/brain-imaging-type-cs"})
    MR_MRA = ("MR MRA", {"code": "mr-dwi-flair-mra", "display": "MR MRA", "system": "http://tecnomod-um.org/CodeSystem/brain-imaging-type-cs"})
    CT = ("CT", {"code": "396205005", "display": "Computed tomography of brain without radiopaque contrast (procedure)", "system": "http://snomed.info/sct"})
    MR = ("MR", {"code": "mr-dwi-flair", "display": "MR", "system": "http://tecnomod-um.org/CodeSystem/brain-imaging-type-cs"})
    CAROTID = ("Carotid", {"code": "58920005", "display": "Angiography of carotid artery (procedure)", "system": "http://snomed.info/sct"})

class StrokeType(ConceptEnum):
    INTRACEREBRAL_HEMORRHAGE = ("Intracerebral Hemorrhage", {"code": "274100004", "display": "Cerebral hemorrhage (disorder)", "system": "http://snomed.info/sct"})
    SUBARACHNOID_HEMORRHAGE  = ("Subarachnoid Hemorrhage", {"code": "21454007", "display": "Subarachnoid intracranial hemorrhage (disorder)", "system": "http://snomed.info/sct"})
    ISCHEMIC                = ("Ischemic", {"code": "422504002", "display": "Ischemic stroke (disorder)", "system": "http://snomed.info/sct"})
    TRANSIENT_ISCHEMIC      = ("Transient Ischemic", {"code": "266257000", "display": "Transient ischemic attack (disorder)", "system": "http://snomed.info/sct"})
    CEREBRAL_VENOUS_THROMBOSIS = ("Cerebral Venous Thrombosis", {"code": "95455008", "display": "Thrombosis of cerebral veins (disorder)", "system": "http://snomed.info/sct"})
    STROKE_MIMICS = ("Stroke Mimics", {"code": "230690007", "display": "Cerebrovascular accident (disorder)", "system": "http://snomed.info/sct"})
    INTRAVENTRICULAR_HEMORRAGE = ("Intraventricular Hemorrhage", {"code": "274110009", "display": "Intraventricular hemorrhage (disorder)", "system": "http://snomed.info/sct"})
    UNDETERMINED            = ("Undetermined", {"code": "373068000", "display": "Undetermined (qualifier value)", "system": "http://snomed.info/sct"})

class StrokeEtiology(ConceptEnum):
    CARDIOEMBOLYSM = ("Cardioembolism", {"code": "413758000", "display": "Cardioembolic stroke (disorder)", "system": "http://snomed.info/sct"})
    ATHEROSCLEROSIS = ("Atherosclerosis", {"code": "atherosclerosis", "display": "Stroke Etiology Atherosclerosis", "system": "http://tecnomod-um.org/CodeSystem/stroke-etiology-cs"})
    LACUNAR = ("Lacunar", {"code": "230698000", "display": "Lacunar infarction (disorder)", "system": "http://snomed.info/sct"})
    CRYPTOGENIC_STROKE = ("Cryptogenic Stroke", {"code": "16891111000119104", "display": "Cryptogenic stroke (disorder)", "system": "http://snomed.info/sct"})
    OTHER= ("Other", {"code": "other", "display": "Stroke Etiology Other", "system": "http://tecnomod-um.org/CodeSystem/stroke-etiology-cs"})
    DISSECTION = ("Dissection", {"code": "122459003", "display": "Dissection of artery (disorder)", "system": "http://snomed.info/sct"})
    MIGRAINOUS_STROKE = ("Migrainous Stroke", {"code": "1263550001", "display": "Infarction of brain due to migraine (disorder)", "system": "http://snomed.info/sct"})
    MOYAMOYA = ("Moyamoya", {"code": "69116000", "display": "Moyamoya disease (disorder)", "system": "http://snomed.info/sct"})
    SICKLE_CELL_ANEMIA = ("Sickle Cell Anemia", {"code": "127040003", "display": "Sickle cell-hemoglobin SS disease (disorder)", "system": "http://snomed.info/sct"})
    UNDETERMINED = ("Undetermined", {"code": "373068000", "display": "Undetermined (qualifier value)", "system": "http://snomed.info/sct"})

class DiagnosisStrokes(ConceptEnum):
    MIGRAINE = ("Migraine", {"code": "37796009", "display": "Migraine (disorder)", "system": "http://snomed.info/sct"})
    SEIZURE = ("Seizure", {"code": "128613002", "display": " Seizure disorder (disorder)", "system": "http://snomed.info/sct"})
    DELIRIUM = ("Delirium", {"code": "2776000", "display": "Delirium (disorder)", "system": "http://snomed.info/sct"})
    ELECTROLYTE_IMBALANCE = ("Electrolyte Imbalance", {"code": "105593004", "display": "Electrolyte imbalance (disorder)", "system": "http://snomed.info/sct"})
    FUNCTIONAL_DISORDER = ("Functional Disorder", {"code": "386585008", "display": "Functional disorder (disorder)", "system": "http://snomed.info/sct"})

class BleedingReason(ConceptEnum):
    ANEURYSM = ("Aneurysm", {"code": "128609009", "display": "Intracranial aneurysm (disorder)", "system": "http://snomed.info/sct"})
    MALFORMATION = ("Malformation", {"code": "703221003", "display": "Congenital intracranial vascular malformation (disorder)", "system": "http://snomed.info/sct"})
    ANGIOPATHY = ("Angiopathy", {"code": "27550009", "display": "Disorder of blood vessel (disorder)", "system": "http://snomed.info/sct"})
    ANTICOAGULANT = ("Anticoagulant-therapy", {"code":"182764009", "display": "Anticoagulant therapy (procedure)", "system": "http://snomed.info/sct"})
    BRAINTUMOR = ("Brain Tumor", {"code": "126952004", "display": "Neoplasm of brain (disorder)", "system": "http://snomed.info/sct"})
    CVT = ("Cerebral Venous Thrombosis", {"code": "95455008", "display": "Thrombosis of cerebral veins (disorder)", "system": "http://snomed.info/sct"})
    HYPERTENSION = ("Hypertension", {"code": "38341003", "display": "Hypertensive disorder, systemic arterial (disorder)", "system": "http://snomed.info/sct"})
    AVM = ("AVM", {"code": "24551003", "display": "Arteriovenous malformation (morphologic abnormality)", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "other", "display": "Bleeding Reason Other", "system": "http://tecnomod-um.org/CodeSystem/hemorrhagic-stroke-bleeding-reason-cs"})
    UNDETERMINED = ("Undetermined", {"code": "373068000", "display": "Undetermined (qualifier value)", "system": "http://snomed.info/sct"})

class AtrialFibrillationOrFlutter(ConceptEnum):
    KNOWN_AF = ("Known AF", {"code": "410515003", "display": "Known present (qualifier value)", "system": "http://snomed.info/sct"})
    NO_AF = ("No AF", {"code": "410516002", "display": "Known absent (qualifier value)", "system": "http://snomed.info/sct"})
    NOT_SCREENED = ("Not Screened", {"code": "261665006", "display": "Unknown (qualifier value)", "system": "http://snomed.info/sct"})
    DETECTED = ("Detected", {"code": "410515003", "display": "Known present (qualifier value)", "system": "http://snomed.info/sct"})

class Medications(ConceptEnum):
    ANTIDIABETIC = ("Antidiabetic", {"code": "antidiabetic", "display": "Any Antidiabetic", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})    
    ANTIHYPERTENSIVE = ("Antihypertensive", {"code": "372586001", "display": "Hypotensive agent (substance)", "system": "http://snomed.info/sct"})
    ANTICOAGULANT = ("Anticoagulant", {"code": "372862008", "display": "Anticoagulant (substance)", "system": "http://snomed.info/sct"})
    ANTIPLATELET = ("Antiplatelet", {"code": "antiplatelet", "display": "Any Antiplatelet", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})
    APIXABAN = ("Apixaban", {"code": "698090000", "display": "Apixaban (substance)", "system": "http://snomed.info/sct"})
    ASA = ("ASA", {"code": "387458008", "display": "Aspirin (substance)", "system": "http://snomed.info/sct"})
    CILOSTOLAZOL = ("Cilostazol", {"code": "116087001", "display": "Cilostazol (substance)", "system": "http://snomed.info/sct"})
    CLOPIDOGREL = ("Clopidogrel", {"code": "386952008", "display": "Clopidogrel (substance)", "system": "http://snomed.info/sct"})    
    CONTRACEPTION = ("Contraception", {"code": "312263009", "display": "Sex hormone (substance)", "system": "http://snomed.info/sct"})
    DABIGATRAN = ("Dabigatran", {"code": "698871007", "display": "Dabigatran (substance)", "system": "http://snomed.info/sct"})
    DIPYRIDAMOLE = ("Dipyridamole", {"code": "387371005", "display": "Dipyridamole (substance)", "system": "http://snomed.info/sct"})
    EDOXABAN = ("Edoxaban", {"code": "712778008", "display": "Edoxaban (substance)", "system": "http://snomed.info/sct"})
    HEPARIN = ("Heparin", {"code": "372877000", "display": "Heparin (substance)", "system": "http://snomed.info/sct"})
    OTHER_ANTICOAGULANT = ("Other Anticoagulant", {"code": "other-anticoagulant", "display": "Other Anticoagulant", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})
    OTHER_ANTIPLATELET = ("Other Antiplatelet", {"code": "other-antiplatelet", "display": "Other Antiplatelet", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})
    OTHER = ("Other", {"code": "other", "display": "Other Medication", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})
    PLASUGREL = ("Plasugrel", {"code": "443129001", "display": "Prasugrel (substance)", "system": "http://snomed.info/sct"})
    RIVAROXABAN = ("Rivaroxaban", {"code": "442031002", "display": "Rivaroxaban (substance)", "system": "http://snomed.info/sct"})
    STATIN = ("Statin", {"code": "387371005", "display": "Substance with 3-hydroxy-3-methylglutaryl-coenzyme A reductase inhibitor mechanism of action (substance)", "system": "http://snomed.info/sct"})
    TICAGRELOR = ("Ticagrelor", {"code": "698805004", "display": "Ticagrelor (substance)", "system": "http://snomed.info/sct"})
    TICLOPIDINE = ("Ticlopidine", {"code": "386950000", "display": "Ticlopidine (substance)", "system": "http://snomed.info/sct"})
    WARFARIN = ("Warfarin", {"code": "372756006", "display": "Warfarin (substance)", "system": "http://snomed.info/sct"})
    ALTEPLASE = ("Alteplase", {"code": "387152000", "display": "Alteplase (substance)", "system": "http://snomed.info/sct"})
    TENECTEPLASE = ("Tenecteplase", {"code": "387066007", "display": "Tenecteplase (substance)", "system": "http://snomed.info/sct"})
    STREPTOKINASE = ("Streptokinase", {"code": "395889004", "display": "Streptokinase (substance)", "system": "http://snomed.info/sct"})
    ANDEXANET = ("Andexanet", {"code": "783678000", "display": "Andexanet alfa (substance)", "system": "http://snomed.info/sct"})
    IDARUCIZUMAB = ("Idarucizumab", {"code": "716017002", "display": "Idarucizumab (substance)", "system": "http://snomed.info/sct"})
    FRESH_FROZEN_PLASMA = ("Fresh Frozen Plasma", {"code": "346447007", "display": "Fresh frozen plasma (substance)", "system": "http://snomed.info/sct"})
    PROTHROMBIN = ("Prothombin", {"code": "7348004", "display": "Coagulation factor II (substance)", "system": "http://snomed.info/sct"})
    PROTAMINE = ("Protamine", {"code": "64520006", "display": "Protamine sulfate (substance)", "system": "http://snomed.info/sct"})
    TRANEXAMIC_ACID = ("Tranexamic Acid", {"code": "386960009", "display": "Tranexamic acid (substance)", "system": "http://snomed.info/sct"})
    AMINOCAPROIC_ACID = ("Aminocaproic Acid", {"code": "59882007", "display": "Aminocaproic acid (substance)", "system": "http://snomed.info/sct"})
    CIRAPARANTAG = ("Ciraparantag", {"code": "Ciraparantag", "display": "Ciraparantag", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})
    VITAMIN_K = ("Vitamin K", {"code": "Vitamin-K", "display": "Vitamin K", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})
    PARACETAMOL = ("Paracetamol", {"code": "387517004", "display": "Paracetamol (substance)", "system": "http://snomed.info/sct"})
    ANTICOAGULANT_REVERSAL = ("Anticoagulant Reversal", {"code": "419927001", "display": "Anticoagulant antagonist (substance)", "system": "http://snomed.info/sct"})
    INSULIN = ("Insulin", {"code":"67866001", "display": "Insulin (substance)", "system": "http://snomed.info/sct"})
    NIMODIPINE = ("Nimodipine", {"code": "387502003", "display": "Nimodipine (substance)", "system": "http://snomed.info/sct"})
    NONE_MEDICATION = ("None", {"code": "none-medication", "display": "No Medication", "system": "http://tecnomod-um.org/CodeSystem/medication-cs"})
    
class QualifierValue(ConceptEnum):
    MILD = ("Mild", {"code": "255604002", "display": "Mild (qualifier value)", "system": "http://snomed.info/sct"})
    MODERATE = ("Moderate", {"code": "1255665007", "display": "Moderate (qualifier value)", "system": "http://snomed.info/sct"})
    SEVERE = ("Severe", {"code": "24484000", "display": "Severe (qualifier value)", "system": "http://snomed.info/sct"})
    OCCLUSSION = ("Occlusion", {"code": "257885003", "display": "Occlusion - action (qualifier value)", "system": "http://snomed.info/sct"})

class VteProcedures(ConceptEnum):
    VTE_INTERVENTION = ("Thromboembolism intervention", {"code": "vte-proc", "display": "Thromboembolism intervention", "system": "http://tecnomod-um.org/CodeSystem/vte-procedures-cs"})
    STOCKINGS =("Stockings", {"code": "225420001", "display": "Application of antithromboembolic stockings (procedure)", "system": "http://snomed.info/sct"})
    IPC = ("Intermittent Pneumatic Compression", {"code": "443448006", "display": "Application of intermittent pneumatic compression device (procedure)", "system": "http://snomed.info/sct"})
    VFP = ("Venous Foot Pump", {"code": "442410008", "display": "Application of venous foot pump (procedure)", "system": "http://snomed.info/sct"})
    XA_INHIBITOR = ("Xa Inhibitor", {"code": "787927008", "display": "Administration of prophylactic coagulation factor Xa inhibitor (procedure)", "system": "http://snomed.info/sct"})
    VTE_WARFARIN = ("VTE Warfarin", {"code": "699041005", "display": "Administration of prophylactic warfarin (procedure)", "system": "http://snomed.info/sct"})
    UFH = ("Unfractionated Heparin", {"code": "392129008", "display": "Administration of prophylactic low dose heparin (procedure)", "system": "http://snomed.info/sct"})
    LMWH = ("Low Molecular Weight Heparin", {"code": "443464003", "display": "Low molecular weight heparin therapy (procedure)", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "421728001", "display": "Administration of prophylactic anticoagulant (procedure)", "system": "http://snomed.info/sct"})

class ObservationMethods(ConceptEnum):
    LAB = ("Laboratory", {"code": "15220000", "display": "Laboratory test (procedure)", "system": "http://snomed.info/sct"})
    POINTOFCARE=("Point of Care", {"code": "405262001", "display": "Point of care (qualifier value)", "system": "http://snomed.info/sct"})
    VENTILATED = ("Ventilated", {"code": "40617009", "display": "Artificial ventilation (regime/therapy)", "system": "http://snomed.info/sct"})
    
class ProcedureNotDoneReason(ConceptEnum):
    DONE_ELSEWHERE = ("Done Elsewhere", {"code": "done-elsewhere", "display": "Performed Elsewhere", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    TRANSFERRED_ELSEWHERE = ("Transferred Elsewhere", {"code": "transfer", "display": "Transferred to Another Facility", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    TIME_WINDOW = ("Time Window", {"code": "time-window", "display": "Outside Therapeutic Window", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    MILD_DEFICIT = ("Mild Deficit", {"code": "mild-deficit", "display": "Mild Deficit", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    DISABILITY = ("Disability", {"code": "disability", "display": "Disability", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})  
    COST = ("Cost", {"code": "cost", "display": "Cost / No Insurance", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    NOT_AVAILABLE = ("Not Available", {"code": "unavailable", "display": "Not Available", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    OTHER = ("other", {"code": "other", "display": "Other Reason", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    NO_LARGE_VESSEL = ("No Large Vessel", {"code": "no-lvo", "display": "No Large Vessel Occlusion (LVO)", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    CONSENT = ("Consent", {"code": "consent", "display": "Consent Not Obtained", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    TECHNICALLY_NOT_POSSIBLE = ("Technically Not Possible", {"code": "technically-not-possible", "display": "Technically Not Possible", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    NO_ANGIOGRAPHY = ("No Angiography", {"code": "no-angiography", "display": "Angiography Not Performed", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    ONLY_MT = ("Only MT", {"code": "only-mt", "display": "Only Mechanical Thrombectomy Considered", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    NO_LVO = ("No LVO", {"code": "no-lvo", "display": "No Large Vessel Occlusion (LVO)", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    CONTRAINDICATION = ("contraindication", {"code": "contraindication", "display": "Contraindication Present", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    PATIENT_REFUSAL = ("Patient Refusal", {"code": "patient-refusal", "display": "Patient/Family Refusal", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    UNKNOWN = ("Unknown", {"code": "unknown", "display": "Unknown Reason", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    NOT_DONE = ("Not Done", {"code": "385660001", "display": "Not done (qualifier value)", "system": "http://snomed.info/sct"})
    POOR_PROGNOSIS = ("Poor Prognosis", {"code": "170969009", "display": "Prognosis bad (finding)", "system": "http://snomed.info/sct"})
    SPECIALIST_NOT_AVAILABLE = ("no specialist", {"code": "specialist-unavailable", "display": "Specialist Not Available", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    SIZE_OF_HEMATOMA = ("size contraindication", {"code": "size-hematoma", "display": "Size of Hematoma", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    LOCATION_OF_HEMATOMA = ("Location of Hematoma", {"code": "location-hematoma", "display": "Location of Hematoma", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    NEUROSURGERY_NOT_AVAILABLE = ("Neurosurgery Not Available", {"code": "neurosurgery-unavailable", "display": "Neurosurgery Not Available", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})
    NOT_REQUIRED = ("Not Required", {"code": "not-required", "display": "Not Required", "system": "http://tecnomod-um.org/CodeSystem/stroke-proc-not-done-reason-cs"})

class PostStrokeProcedures(ConceptEnum):
    PHYSIOTHERAPY = ("Physiotherapy", {"code": "722138006", "display": "Physiotherapy (qualifier value)", "system": "http://snomed.info/sct"})
    OCCUPATIONAL_THERAPY = ("Occupational Therapy", {"code": "84478008", "display": " Occupational therapy (regime/therapy)", "system": "http://snomed.info/sct"})
    SPEECH_THERAPY = ("Speech Therapy", {"code": "5154007", "display": "Speech therapy (regime/therapy)", "system": "http://snomed.info/sct"})
    SMOKING_CESSATION = ("Smoking Cessation", {"code": "225323000", "display": "Smoking cessation education (procedure)", "system": "http://snomed.info/sct"})
    VENTRICULOPERITONEAL_SHUNT = ("Ventriculoperitoneal Shunt", {"code": "47020004", "display": "Ventriculoperitoneal shunt (procedure)", "system": "http://snomed.info/sct"})


class PostStrokeComplications(ConceptEnum):
    PNEUMONIA = ("Pneumonia", {"code": "233604007", "display": "Pneumonia (disorder)", "system": "http://snomed.info/sct"})
    SEPSIS = ("Sepsis", {"code": "91302008", "display": "Sepsis (disorder)", "system": "http://snomed.info/sct"})
    DVT = ("DVT", {"code": "128053003", "display": "Deep venous thrombosis (disorder)", "system": "http://snomed.info/sct"})
    FALLING = ("Falling", {"code": "398117008", "display": "Falling injury (disorder)", "system": "http://snomed.info/sct"})
    SORES = ("Sores", {"code": "Sores", "display": "Sores", "system": "http://tecnomod-um.org/CodeSystem/stroke-post-stroke-complication-cs"})
    PULMONARY_EMBOLISM = ("Pulmonary Embolism", {"code": "59282003", "display": "Pulmonary embolism (disorder)", "system": "http://snomed.info/sct"})
    RECURRENT = ("Recurrence of Problem", {"code": "161917009", "display": "Recurrence of problem (finding)", "system": "http://snomed.info/sct"})
    URINARY_INFECTION = ("Urinary Infection", {"code": "68566005", "display": "Urinary tract infectious disease (disorder)", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "other", "display": "Other Post-Stroke Complication", "system": "http://tecnomod-um.org/CodeSystem/stroke-post-stroke-complication-cs"})


class SwallowingScreeningDone(ConceptEnum):
    YES = ("Yes", {"code": "385658003", "display": "Done (qualifier value)", "system": "http://snomed.info/sct"})
    NO = ("No", {"code": "385660001", "display": "Not done (qualifier value)", "system": "http://snomed.info/sct"})
    NOT_APPLICABLE = ("Not Applicable", {"code": "385432009", "display": "Not applicable (qualifier value)", "system": "http://snomed.info/sct"})

class PractitionerRoles(ConceptEnum):
    NURSE = ("Nurse", {"code": "nurse", "display": "Nurse", "system": "http://terminology.hl7.org/CodeSystem/practitioner-role"})
    PHYSICIAN = ("Physician", {"code": "physician", "display": "Physician", "system": "http://terminology.hl7.org/CodeSystem/practitioner-role"})
    SPEECH_THERAPIST = ("Speech Therapist", {"code": "159026005", "display": "	Speech and language therapist", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "223366009", "display": "Healthcare professional (occupation)", "system": "http://snomed.info/sct"})

class SwallowingScreeningTiming(ConceptEnum):
    WITHIN_24_HOURS = ("Within 24 Hours", {"code": "post-acute", "display": "Acute Phase (<24h)", "system": "http://tecnomod-um.org/CodeSystem/procedure-timing-context-cs"})
    AFTER_24_HOURS = ("After 24 Hours", {"code": "281381003", "display": "More than 24 hours after admission (qualifier value)", "system": "http://snomed.info/sct"})
    WITHIN_4_HOURS = ("Within 4 Hours", {"code": "T4H", "display": "Within 4 Hours", "system": "http://tecnomod-um.org/CodeSystem/swallow-screen-time-cs"})

class SwallowingScreeningType(ConceptEnum):
    GUSS = ("GUSS", {"code": "1290000005", "display": "Assessment using Gugging Swallowing Screen (procedure)", "system": "http://snomed.info/sct"})
    WATER_TEST = ("Water Test", {"code": "63913004", "display": "Tonography with water provocation (procedure)", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "other", "display": "Other Swallow Procedure", "system": "http://tecnomod-um.org/CodeSystem/swallow-procedures-cs"})
    ASSIST = ("Assist", {"code": "assist", "display": "ASSIST", "system": "http://tecnomod-um.org/CodeSystem/swallow-procedures-cs"})
    VST = ("VST", {"code": "v-vst", "display": "V-VST", "system": "http://tecnomod-um.org/CodeSystem/swallow-procedures-cs"})
    UNKNOWN = ("UNKNOWN", {"code": "261665006", "display": "Unknown (qualifier value)", "system": "http://snomed.info/sct"})

class DischargeDestination(ConceptEnum):
    HOME = ("Home", {"code": "306689006", "display": "Discharge to home (procedure)", "system": "http://snomed.info/sct"})
    ANOTHER_HOSPITAL = ("Another Hospital", {"code": "19712007", "display": "Patient transfer, to another health care facility (procedure)", "system": "http://snomed.info/sct"})
    SAME_HOSPITAL = ("Same Hospital", {"code": "37729005", "display": "Patient transfer, in-hospital (procedure)", "system": "http://snomed.info/sct"})
    SOCIAL_CARE = ("Social Care", {"code": "306694006", "display": "Discharge to nursing home (procedure)", "system": "http://snomed.info/sct"})
    DEAD = ("Dead", {"code": "dead", "display": "Patient Deceased", "system": "http://tecnomod-um.org/CodeSystem/stroke-discharge-destination-cs"})
    PRIMARY_STROKE = ("Primary Stroke Center", {"code": "45131006", "display": "Primary care hospital (environment)", "system": "http://snomed.info/sct"})
    COMPREHENSIVE_STROKE = ("Comprehensive Stroke Center", {"code": "comprehensive-stroke-center", "display": "Comprehensive Stroke Center", "system": "http://tecnomod-um.org/CodeSystem/stroke-discharge-destination-cs"})

class DischargeFacilityDepartment(ConceptEnum):
    ACUTE_REHABILITATION = ("Acute Rehabilitation", {"code": "acute", "display": "Acute Rehabilitation", "system": "http://tecnomod-um.org/CodeSystem/discharge-dept-cs"})
    POSTCARE_BED = ("Postcare Bed", {"code": "post-care", "display": "Post Care Bed", "system": "http://tecnomod-um.org/CodeSystem/discharge-dept-cs"})
    NEUROLOGY = ("Neurology", {"code": "neurology", "display": "Neurology", "system": "http://tecnomod-um.org/CodeSystem/discharge-dept-cs"})
    ANOTHER_DEPARTMENT = ("Another Department", {"code": "another-department", "display": "Another Department", "system": "http://tecnomod-um.org/CodeSystem/discharge-dept-cs"})


class MTiciScore(ConceptEnum):
    ZERO   = ("Zero", {"code": "0", "display": "Grade 0: No perfusion", "system": "http://tecnomod-um.org/CodeSystem/mtici-score-cs"})
    ONE    = ("One", {"code": "1", "display": "Grade 1: Antegrade reperfusion past the initial occlusion, but limited distal branch filling with little or slow distal reperfusion", "system": "http://tecnomod-um.org/CodeSystem/mtici-score-cs"})
    TWO_A  = ("Two A", {"code": "2a", "display": "Grade 2a: Antegrade reperfusion of less than half of the occluded target artery previously ischemic territory", "system": "http://tecnomod-um.org/CodeSystem/mtici-score-cs"})
    TWO_B  = ("Two B", {"code": "2b", "display": "Grade 2b: Antegrade reperfusion of more than half of the previously occluded target artery ischemic territory", "system": "http://tecnomod-um.org/CodeSystem/mtici-score-cs"})
    TWO_C  = ("Two C", {"code": "2c", "display": "Grade 2c: Near complete perfusion except for slow flow or distal emboli in a few distal cortical vessels", "system": "http://tecnomod-um.org/CodeSystem/mtici-score-cs"})
    THREE  = ("Three", {"code": "3", "display": "Grade 3: Complete antegrade reperfusion of the previously occluded target artery ischemic territory, with absence of visualized occlusion in all distal branches", "system": "http://tecnomod-um.org/CodeSystem/mtici-score-cs"})



class Laterality(ConceptEnum):
    LEFT = ("Left", {"code": "7771000", "display": "Left (qualifier value)", "system": "http://snomed.info/sct"})
    RIGHT = ("Right", {"code": "24028007", "display": "Right (qualifier value)", "system": "http://snomed.info/sct"})
    BILATERAL = ("Bilateral", {"code": "51440002", "display": "Bilateral", "system": "http://snomed.info/sct"})
    DISTAL = ("Distal", {"code": "46053002", "display": "Distal", "system": "http://snomed.info/sct"})
    DORSAL = ("Dorsal", {"code": "255554000", "display": "Dorsal", "system": "http://snomed.info/sct"})
    PLANTAR = ("Plantar", {"code": "264147007", "display": "Plantar", "system": "http://snomed.info/sct"})
    UPPER = ("Upper", {"code": "261183002", "display": "Upper", "system": "http://snomed.info/sct"})
    LOWER = ("Lower", {"code": "261122009", "display": "Lower", "system": "http://snomed.info/sct"})
    MEDIAL = ("Medial", {"code": "255561001", "display": "Medial", "system": "http://snomed.info/sct"})
    LATERAL = ("Lateral", {"code": "49370004", "display": "Lateral", "system": "http://snomed.info/sct"})
    SUPERIOR = ("Superior", {"code": "264217000", "display": "Superior", "system": "http://snomed.info/sct"})
    INFERIOR = ("Inferior", {"code": "261089000", "display": "Inferior", "system": "http://snomed.info/sct"})
    POSTERIOR = ("Posterior", {"code": "255551008", "display": "Posterior", "system": "http://snomed.info/sct"})
    BELOW = ("Below", {"code": "351726001", "display": "Below", "system": "http://snomed.info/sct"})
    ABOVE = ("Above", {"code": "352730000", "display": "Above", "system": "http://snomed.info/sct"})


class BodySites(ConceptEnum):  
    ANTERIOR = ("Anterior", {"code": "60176003", "display": "Structure of anterior cerebral artery (body structure)", "system": "http://snomed.info/sct"})
    CAROTID = ("Carotid", {"code": "86117002", "display": "Internal carotid artery structure (body structure)", "system": "http://snomed.info/sct"})
    ACA = ("ACA", {"code": "60176003", "display": "Structure of anterior cerebral artery (body structure)", "system": "http://snomed.info/sct"})
    BA = ("BA", {"code": "59011009", "display": "Structure of basilar artery (body structure)", "system": "http://snomed.info/sct"})
    CAE = ("CAE", {"code": "69105007", "display": "Carotid artery structure (body structure)", "system": "http://snomed.info/sct"})
    CAI = ("CAI", {"code": "86117002", "display": "Internal carotid artery structure (body structure)", "system": "http://snomed.info/sct"})
    VA = ("VA", {"code": "85234005", "display": "Structure of vertebral artery (body structure)", "system": "http://snomed.info/sct"})
    MCA_M1 = ("MCA M1", {"code": "414722000", "display": "Structure of middle cerebral artery M1 segment (body structure)", "system": "http://snomed.info/sct"})
    MCA_M2 = ("MCA M2", {"code": "414723005", "display": "Structure of middle cerebral artery M2 segment (body structure)", "system": "http://snomed.info/sct"})
    MCA_M3 = ("MCA M3", {"code": "414724004", "display": "Structure of middle cerebral artery M3 segment (body structure)", "system": "http://snomed.info/sct"})
    PCA_P1 = ("PCA P1", {"code": "415144009", "display": "Structure of posterior cerebral artery P1 segment (body structure)", "system": "http://snomed.info/sct"})
    PCA_P2 = ("PCA P2", {"code": "415145005", "display": "Structure of posterior cerebral artery P2 segment (body structure)", "system": "http://snomed.info/sct"})
    BRAIN_STEM = ("Brain Stem", {"code": "119238007", "display": "Brain stem part (body structure)", "system": "http://snomed.info/sct"})
    CORTICAL = ("Cortical", {"code": "87791003", "display": "Cortex of bone structure (body structure)", "system": "http://snomed.info/sct"})
    SUBCORTICAL = ("Subcortical", {"code": "81737006", "display": "Structure of lacunar ligament (body structure)", "system": "http://snomed.info/sct"})
    INFRATENTORIAL = ("Infratentorial", {"code": "21031007", "display": " Infratentorial brain structure (body structure)", "system": "http://snomed.info/sct"})
    SUPRATENTORIAL = ("Supratentorial", {"code": "222036002", "display": " Supratentorial brain structure (body structure)", "system": "http://snomed.info/sct"})
    SUBARACHNOID = ("Subarachnoid", {"code": "35951006", "display": " Subarachnoid space structure (body structure)", "system": "http://snomed.info/sct"})
    INTRAVENTRICULAR = ("Intraventricular", {"code": "180955002", "display": "Structure of intraventricular meninges of brain (body structure)", "system": "http://snomed.info/sct"})


    

class RiskFactor(ConceptEnum):
    AtrialFibrillation = ("AtrialFibrillation", {"code": "49436004", "display": "Atrial fibrillation (disorder)", "system": "http://snomed.info/sct"})
    CongestiveHeartFailure = ("CongestiveHeartFailure", {"code": "84114007", "display": "Heart failure (disorder)", "system": "http://snomed.info/sct"})
    CoronaryArteryDisease = ("CoronaryArteryDisease", {"code": "53741008", "display": "Coronary arteriosclerosis (disorder)", "system": "http://snomed.info/sct"})
    COVID = ("Covid", {"code": "840539006", "display": "Disease caused by severe acute respiratory syndrome coronavirus 2 (disorder)", "system": "http://snomed.info/sct"})
    Diabetes = ("Diabetes", {"code": "73211009", "display": "Diabetes mellitus (disorder)", "system": "http://snomed.info/sct"})
    HIV = ("HIV", {"code": "165816005", "display": "Human immunodeficiency virus detected (finding)", "system": "http://snomed.info/sct"})
    Hyperlipidemia = ("Hyperlipidemia", {"code": "55822004", "display": "Hyperlipidemia (disorder)", "system": "http://snomed.info/sct"})    
    Hypertension = ("Hypertension", {"code": "38341003", "display": "Hypertensive disorder, systemic arterial (disorder)", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "other", "display": "Other", "system": "http://tecnomod-um.org/CodeSystem/risk-factor-cs"})    
    PreviousHemorrhagicStroke = ("PreviousHemorrhagicStroke", {"code": "230706003", "display": "Hemorrhagic cerebral infarction (disorder)", "system": "http://snomed.info/sct"})
    PreviousIschemicStroke = ("PreviousIschemicStroke", {"code": "266257000", "display": "Transient ischemic attack (disorder)", "system": "http://snomed.info/sct"})
    PreviousStroke = ("PreviousStroke", {"code": "230690007", "display": "Cerebrovascular accident (disorder)", "system": "http://snomed.info/sct"})
    Smoker = ("Smoker", {"code": "77176002", "display": "Smoker (finding)", "system": "http://snomed.info/sct"})
    Non_Smoker = ("Non-Smoker", {"code": "8392000 ", "display": "Non-smoker (finding)", "system": "http://snomed.info/sct"})
    Ex_Smoker = ("Ex-Smoker", {"code": "8517006", "display": "Ex-smoker (finding)", "system": "http://snomed.info/sct"})
    VTE = ("VTE", {"code": "429098002", "display": "Thromboembolism of vein (disorder)", "system": "http://snomed.info/sct"})



    
class Bool(ConceptEnum):
    TRUE = ("True", {"code": "true", "display": "True", "system": "http://hl7.org/fhir/bool"})
    FALSE = ("False", {"code": "false", "display": "False", "system": "http://hl7.org/fhir/bool"})

class DischargeMedication(ConceptEnum):
    ANTIPLATELET = ("Antiplatelet", {"code": "antiplatelet", "display": "Any Antiplatelet", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    ANTICOAGULANT = ("Anticoagulant", {"code": "anticoagulant", "display": "Any Anticoagulant", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    ASPIRIN = ("Aspirin", {"code": "asa", "display": "Aspirin", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    HEPARIN = ("Heparin", {"code": "heparin", "display": "Heparin", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    WARFARIN = ("Warfarin", {"code": "warfarin", "display": "Warfarin", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    STATIN = ("Statin", {"code": "statin", "display": "Statin", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    ANTIDIABETIC = ("Antidiabetic", {"code": "antidiabetics", "display": "Antidiabetics", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    ANTIHYPERTENSIVE = ("Antihypertensive", {"code": "antihypertensive", "display": "Antihypertensive", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    OTHER_ANTIPLATELET = ("Other Antiplatelet", {"code": "other-antiplatelet", "display": "Other Antiplatelet", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    CLOPIDOGREL = ("Clopidogrel", {"code": "clopidogrel", "display": "Clopidogrel", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    CONTRACEPTION = ("Contraception", {"code": "contraception", "display": "Contraception", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})
    OTHER = ("Other", {"code": "other", "display": "Other", "system": "http://tecnomod-um.org/CodeSystem/discharge-medication-cs"})


class VitalSigns(ConceptEnum):
    SYSTOLIC = ("Systolic", {"code": "271649006", "display": "Systolic blood pressure (observable entity)", "system": "http://snomed.info/sct"})
    DIASTOLIC = ("Diastolic", {"code": "271650006", "display": "Diastolic blood pressure (observable entity)", "system": "http://snomed.info/sct"})
    TAKE_VS = ("Take VS", {"code": "61746007", "display": "Taking patient vital signs (procedure)", "system": "http://snomed.info/sct"})
    SYS_BP_LT140 = ("SysBP<140", {"code": "sys-bp-lt-140", "display": "Systolic Blood Pressure < 140 mmHg", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})


class MRsScore(ConceptEnum):
    ZERO   = ("0", {"code": "0", "display": "No symptoms at all", "system": "http://tecnomod-um.org/CodeSystem/mrs-score-cs"})
    ONE    = ("1", {"code": "1", "display": "No significant disability despite symptoms; able to carry out all usual duties and activities", "system": "http://tecnomod-um.org/CodeSystem/mrs-score-cs"})
    TWO    = ("2", {"code": "2", "display": "Slight disability; unable to carry out all previous activities, but able to look after own affairs without assistance", "system": "http://tecnomod-um.org/CodeSystem/mrs-score-cs"})
    THREE  = ("3", {"code": "3", "display": "Moderate disability; requiring some help, but able to walk without assistance", "system": "http://tecnomod-um.org/CodeSystem/mrs-score-cs"})
    FOUR   = ("4", {"code": "4", "display": "Moderately severe disability; unable to walk without assistance and unable to attend to own bodily needs without assistance", "system": "http://tecnomod-um.org/CodeSystem/mrs-score-cs"})
    FIVE   = ("5", {"code": "5", "display": "Severe disability; bedridden, incontinent and requiring constant nursing care and attention", "system": "http://tecnomod-um.org/CodeSystem/mrs-score-cs"})
    SIX    = ("6", {"code": "6", "display": "Dead", "system": "http://tecnomod-um.org/CodeSystem/mrs-score-cs"})

class FunctionalScore(ConceptEnum):
    MRS = ("MRS", {"code": "1255866005", "display": "Modified Rankin Scale score (observable entity)", "system": "http://snomed.info/sct"})
    NIHSS = ("NIHSS", {"code": "450743008", "display": "National Institutes of Health stroke scale score (observable entity)", "system": "http://snomed.info/sct"})
    ASPECT = ("ASPECT", {"code": "1290002002", "display": "Alberta Stroke Program Early CT score (assessment scale)", "system": "http://snomed.info/sct"})
    ICH_SCORE = ("ICH", {"code": "ICH-score", "display": "Intracerebral Hemorrhage Score", "system": "http://tecnomod-um.org/CodeSystem/functional-score-cs"})
    HUNT_HESS = ("Hunt-Hess", {"code": "hunt-hess", "display": "Hunt and Hess Score", "system": "http://tecnomod-um.org/CodeSystem/functional-score-cs"})
    ABCD2 = ("ABCD2", {"code": "774086001", "display": "Age, Blood pressure, Clinical features, Duration, Diabetes 2 score (observable entity)","system": "http://snomed.info/sct"})
    CHA2S2_VASc = ("CHA2DS2-VASc", {"code": "713678009", "display": "Congestive heart failure, hypertension, age 2, diabetes mellitus, stroke 2, vascular disease, age, sex category stroke risk score (observable entity)", "system": "http://snomed.info/sct"})
    THRIVE = ("THRIVE", {"code": "thrive", "display": "Totaled Health Risks in Vascular Events Score", "system": "http://tecnomod-um.org/CodeSystem/functional-score-cs"})
    AGE = ("Age", {"code": "445518008", "display": "Age at onset of clinical finding (observable entity)", "system": "http://snomed.info/sct"})
    
class AppointmentSituation(ConceptEnum):
    SCHEDULED = ("Scheduled", {"code": "Scheduled", "display": "Scheduled", "system": ""})
    NOT_RECOMMENDED = ("Not Recommended", {"code": "not-recommended", "display": "Not Recommended", "system": ""})

class AssessmentContext(ConceptEnum):
    PRESTROKE = ("Prestroke", {"code": "pre-stroke", "display": "Pre-stroke", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    DISCHARGE = ("Discharge", {"code": "discharge", "display": "Discharge", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    THREE_MONTHS = ("Three Months", {"code": "3-month", "display": "3 Month Follow-up", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    ADMISSION = ("Admission", {"code": "admission", "display": "Admission", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    HOURS_72 = ("72 Hours", {"code": "72-hours", "display": "72 Hours After Admission", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    FIRST_48_HOURS = ("First 48 Hours", {"code": "first-48-hours", "display": "First 48 Hours After Admission", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    POST_STROKE = ("Post-Stroke", {"code": "post-stroke", "display": "Post-Stroke", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    DURING_LAST_10_YEARS = ("During Last 10 Years", {"code": "last-10-years", "display": "During Last 10 Years", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})
    DISCHARGE_OR_7_DAYS = ("Discharge or 7 Days", {"code": "discharge-or-7-days", "display": "Discharge or 7 Days After Admission", "system": "http://tecnomod-um.org/CodeSystem/assessment-context-cs"})

class SpecificFinding(ConceptEnum):
    MTICI = ("MTICI", {"code": "mTICI", "display": "mTICI", "system": "http://tecnomod-um.org/CodeSystem/mtici-code-cs"})
    PERFUSION = ("Perfusion", {"code": "371863001", "display": "Perfusion finding (finding)", "system": "http://snomed.info/sct"}) 
    BILATERAL_STENOSIS = ("Bilateral-Stenosis", {"code": "787044009", "display": "Stenosis of bilateral carotid arteries (disorder)", "system": "http://snomed.info/sct"})
    PERFUSION_VOLUME = ("Perfusion Volume", {"code": "perf-volume", "display": "Perfusion Volume", "system": "http://tecnomod-um.org/CodeSystem/perfusion-volume-cs"})
    HYPOPERFUSION_VOLUME = ("Hypoperfusion Volume", {"code": "hypo-volume", "display": "Hypoperfusion Volume", "system": "http://tecnomod-um.org/CodeSystem/perfusion-volume-cs"})
    BLOOD_VOLUME = ("Blood Volume", {"code": "16086006", "display": "Blood volume (observable entity)", "system": "http://snomed.info/sct"})
    CAROTID_STENOSIS = ("Carotid Stenosis", {"code": "64586002", "display": "Stenosis of carotid artery (disorder)", "system": "http://snomed.info/sct"})
    HYDROCEPHALUS = ("Hydrocephalus", {"code": "230745008", "display": "Hydrocephalus (disorder)", "system": "http://snomed.info/sct"})
    OLD_INFARCT = ("Old Infarct", {"code": "old-infarct", "display": "Old Infarct", "system": "http://tecnomod-um.org/CodeSystem/old-infarct-cs"})
    ARTERY_OCCLUSION = ("Artery Occlusion", {"code": "2929001", "display": "Occlusion of artery (disorder)", "system": "http://snomed.info/sct"})
    INTRACRANIAL_HEMORRHAGE = ("Intracranial Hemorrhage", {"code": "1386000", "display": " Intracranial hemorrhage (disorder)", "system": "http://snomed.info/sct"})
    BRAIN_INFARCT = ("Brain Infarct", {"code": "230690007", "display": "Cerebrovascular accident (disorder)", "system": "http://snomed.info/sct"})
    HEMORRHAGIC_TRANSFORMATION = ("Hemorrhagic Transformation", {"code": "230706003", "display": " Hemorrhagic cerebral infarction (disorder)", "system": "http://snomed.info/sct"}) 

class IchTreatment(ConceptEnum):
    CRANIECTOMY = ("Craniectomy", {"code": "1288015005", "display": "Decompressive craniectomy (procedure)", "system": "http://snomed.info/sct"})
    HEMATOMA_EVACUATION = ("Hematoma Evacuation", {"code": "10458001", "display": "Evacuation of intracerebral hematoma (procedure)", "system": "http://snomed.info/sct"})
    REMOVAL_OF_THROMBUS = ("Removal of Thrombus", {"code": "43810009", "display": "Removal of thrombus (procedure)", "system": "http://snomed.info/sct"})
    OPEN_CRANIECTOMY = ("Open Craniectomy", {"code": "36910002", "display": "Excision of bone of cranium (procedure)", "system": "http://snomed.info/sct"})
    STEREOTACTIC_ASPIRATION = ("Stereotactic Aspiration", {"code": "77337009", "display": "Stereotactic biopsy by aspiration of intracranial lesion (procedure)", "system": "http://snomed.info/sct"})
    VENTRICULAR_DRAINAGE = ("Ventricular Drainage", {"code": "230869001", "display": "External drainage procedure from ventricle of brain (procedure)", "system": "http://snomed.info/sct"})
    CLIPPING = ("Clipping", {"code": "21147007", "display": "Closure by clip (procedure)", "system": "http://snomed.info/sct"})
    COILING = ("Coiling", {"code": "1230010003", "display": "Percutaneous transluminal procedure on blood vessel (procedure)", "system": "http://snomed.info/sct"})
    ANTICOAGULATION = ("Anticoagulation", {"code": "182764009", "display": "Anticoagulant therapy (procedure)", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "other", "display": "Other Treatment", "system": "http://tecnomod-um.org/CodeSystem/ich-treatment-cs"})


class StrokeCircumstance(ConceptEnum):
    WAKE_UP = ("Wake Up", {"code": "wake-up", "display": "Wake Up Stroke", "system": "http://tecnomod-um.org/CodeSystem/stroke-circumstance-codes-cs"})
    IN_HOSPITAL = ("In Hospital", {"code": "in-hospital", "display": "In Hospital Stroke", "system": "http://tecnomod-um.org/CodeSystem/stroke-circumstance-codes-cs"})

class PostAcuteCare(ConceptEnum):
    TRUE = ("True", {"code": "post-acute", "display": "Acute Phase (<24h)", "system": "http://tecnomod-um.org/CodeSystem/procedure-timing-context-cs"})
    FALSE = ("False", {"code": "281381003", "display": "More than 24 hours after admission (qualifier value)", "system": "http://snomed.info/sct"})
    NONE = ("None", {"code": "unknown", "display": "Unknown/Not Applicable", "system": "http://tecnomod-um.org/CodeSystem/procedure-timing-context-cs"})

class PerforationProcedures(ConceptEnum):
    THROMBOLYSIS = ("Thrombolysis", {"code": "472191000119101", "display": "Thrombolysis of cerebral artery by intravenous infusion (procedure)", "system": "http://snomed.info/sct"})
    THROMBECTOMY = ("Thrombectomy", {"code": "397046001", "display": "Thrombectomy of artery (procedure)", "system": "http://snomed.info/sct"})
    ANTIDOTE = ("Antidote", {"code": "67329000", "display": "Administration of antidote (procedure)", "system": "http://snomed.info/sct"})
    ENDARTERECTOMY = ("Endarterectomy", {"code": "66951008", "display": "Carotid endarterectomy (procedure)", "system": "http://snomed.info/sct"})

class TimingMetricCodes(ConceptEnum):
    DOOR_TO_GROIN = ("Door2Groin", {"code": "D2G", "display": "Door to Groin", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_GROIN_LE90 = ("Door2GroinLe90", {"code": "D2G<=90", "display": "Door to Groin <= 90 Minutes", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_GROIN_LE120 = ("Door2GroinLe120", {"code": "D2G<=120", "display": "Door to Groin <= 120 Minutes", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_DOOR = ("Door2Door", {"code": "D2D", "display": "Door to Door", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_DISCHARGE = ("Door2Discharge", {"code": "D2D", "display": "Door to Discharge", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_NEEDLE = ("Door2Needle", {"code": "D2N", "display": "Door to Needle", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_NEEDLE_LE45 = ("Door2NeedleLe45", {"code": "D2N<=45", "display": "Door to Needle <= 45 Minutes", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_NEEDLE_LE60 = ("Door2NeedleLe60", {"code": "D2N<=60", "display": "Door to Needle <= 60 Minutes", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_ICH_EVACUATION = ("Door2ICHEvacuation", {"code": "D2ICH-Evac", "display": "Door to ICH Evacuation", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_IMAGING = ("Door2Imaging", {"code": "D2I", "display": "Door to Imaging", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_IV_ANTIHYPERTENSIVE = ("Door2IVAntihypertensive", {"code": "D2IV-Antihypertensive", "display": "Door to IV Antihypertensive", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_SYS_BP_LT140 = ("Door2SysBP<140", {"code": "D2SysBP<140", "display": "Door to Systolic Blood Pressure < 140 mmHg", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_REPERFUSION = ("Door2Reperfusion", {"code": "D2R", "display": "Door to Reperfusion", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    ONSET_TO_DOOR = ("Onset2Door", {"code": "O2D", "display": "Onset to Door", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    HIGHEST_SYS_BP_AFTER24H = ("HighestSysBPAfter24Hours", {"code": "highest-sys-bp-after-24-hours", "display": "Highest Systolic Blood Pressure After 24 Hours", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    GROIN_TO_REPERFUSION = ("Groin2Reperfusion", {"code": "G2R", "display": "Groin to Reperfusion", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    FEVER_DAY_1 = ("FeverDay1", {"code": "temperature-checks-day-1", "display": "Temperature Checks Day 1", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    FEVER_DAY_2 = ("FeverDay2", {"code": "temperature-checks-day-2", "display": "Temperature Checks Day 2", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    FEVER_DAY_3 = ("FeverDay3", {"code": "temperature-checks-day-3", "display": "Temperature Checks Day 3", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    HYPERGLYCEMIA_DAY_1 = ("HyperglycemiaDay1", {"code": "hyperglycemia-day-1", "display": "Hyperglycemia Checks Day 1", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    HYPERGLYCEMIA_DAY_2 = ("HyperglycemiaDay2", {"code": "hyperglycemia-day-2", "display": "Hyperglycemia Checks Day 2", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    HYPERGLYCEMIA_DAY_3 = ("HyperglycemiaDay3", {"code": "hyperglycemia-day-3", "display": "Hyperglycemia Checks Day 3", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"}) 
    DISCHARGE_TO_THREE_MONTHS_CONTACT = ("DischargeTo3MonthContact", {"code": "discharge-to-3-month-contact", "display": "Discharge to 3 Month Contact", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DISCHARGE_OR_7DAYS = ("DischargeOr7Days", {"code": "discharge-or-7-days", "display": "At Discharge or at 7 Days", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    DOOR_TO_ANTICOAGULANT_REVERSAL = ("DoorToAnticoagulantReversal", {"code": "D2AnticoagulantReversal", "display": "Door to Anticoagulant Reversal", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})
    IV_ANTIHYPERTENSIVE_TO_SYS_BP_LT140 = ("IVAntihypertensiveToSysBP<140", {"code": "IV-Antihypertensive-to-SysBP<140", "display": "IV Antihypertensive to Systolic Blood Pressure < 140 mmHg", "system": "http://tecnomod-um.org/CodeSystem/timing-metric-codes-cs"})

class Symptomps(ConceptEnum):
    UNILATERAL_WEAKNESS = ("Weakness", {"code": "26544005", "display": "Muscle weakness (finding)", "system": "http://snomed.info/sct"})
    SPEECH_DISTURBANCE = ("Speech Disturbance", {"code": "29164008", "display": " Disturbance in speech (finding)", "system": "http://snomed.info/sct"})
    OTHER_SYMPTOM = ("Other Symptom", {"code": "other-symptom", "display": "Other Symptom", "system": "http://tecnomod-um.org/CodeSystem/symptoms-cs"})

class ThrombectomyComplications(ConceptEnum):
    PERFORATION = ("Perforation", {"code": "307312008", "display": "Perforation of artery (disorder)", "system": "http://snomed.info/sct"})
    DISSECTION = ("Dissection", {"code": "710864009", "display": "Dissection of artery (disorder)", "system": "http://snomed.info/sct"})
    HEMATOMA = ("Hematoma", {"code": "385494008", "display": "Hematoma (disorder)", "system": "http://snomed.info/sct"})
    EMBOLISM = ("Embolism", {"code": "414086009", "display": "Embolism (disorder)", "system": "http://snomed.info/sct"})
    OTHER = ("Other", {"code": "other", "display": "Other Complication", "system": "http://tecnomod-um.org/CodeSystem/thrombectomy-complications-cs"})

class UnitofMeasurement(ConceptEnum):
    MINUTE = ("Minute", {"code": "min", "display": "minute", "system": "https://ucum.org/ucum"})
    MMGM = ("mmHg", {"code": "mm[Hg]", "display": "millimeter Mercury column", "system": "https://ucum.org/ucum"})
    MMOL_L = ("mmol/L", {"code": "mmol/L", "display": "millimole per liter", "system": "https://ucum.org/ucum"})
    ML = ("mL", {"code": "mL", "display": "milliliter", "system": "https://ucum.org/ucum"})
    MG = ("mg", {"code": "mg", "display": "milligram", "system": "https://ucum.org/ucum"})
    DAY = ("Day", {"code": "d", "display": "day", "system": "https://ucum.org/ucum"})

class AdherenceCodes(ConceptEnum):
    TAKING = ("Taking", {"code":"taking", "display": "Taking", "system": "http://hl7.org/fhir/CodeSystem/medication-statement-adherence"})
    NOT_TAKING = ("Not Taking", {"code":"not-taking", "display": "Not Taking", "system": "http://hl7.org/fhir/CodeSystem/medication-statement-adherence"})
    UNKNOWN = ("Unknown", {"code": "unknown", "display": "Unknown", "system": "http://hl7.org/fhir/CodeSystem/medication-statement-adherence"})

class ClinicalStatusCodes(ConceptEnum):
    ACTIVE = ("Active", {"code":"active", "display": "Active", "system": "http://terminology.hl7.org/CodeSystem/condition-clinical"})
    INACTIVE = ("Inactive", {"code":"inactive", "display": "Inactive", "system": "http://terminology.hl7.org/CodeSystem/condition-clinical"})
    REMISSION = ("Remission", {"code":"remission", "display": "Remission", "system": "http://terminology.hl7.org/CodeSystem/condition-clinical"})
    UNKNOWN = ("Unknown", {"code": "unknown", "display": "Unknown", "system": "http://terminology.hl7.org/CodeSystem/condition-clinical"})

class AnaliticsCodes(ConceptEnum):
    GLUCOSE = ("Glucose", {"code": "33747003", "display": "Glucose measurement, blood (procedure)", "system": "http://snomed.info/sct"})
    CHOLESTEROL = ("Cholesterol", {"code": "372361000119104", "display": "Low density lipoprotein cholesterol by direct assay (observable entity)", "system": "http://snomed.info/sct"})
    INR = ("INR", {"code": "165581004", "display": "International normalized ratio (observable entity)", "system": "http://snomed.info/sct"})
    FEVER = ("Fever", {"code": "386661006", "display": "Fever (finding)", "system": "http://snomed.info/sct"})
    HYPERGLYCEMIA = ("Hyperglycemia", {"code": "80394007", "display": "Hyperglycemia (disorder)", "system": "http://snomed.info/sct"})
    GE10 = ("GE10", {"code": "ge10", "display": "Glucose > 10 mmol/L", "system": "http://tecnomod-um.org/CodeSystem/analytics-codes-cs"})
    HIGHEST_HYPERGLYCEMIA_VALUE = ("Highest Hyperglycemia Value", {"code": "highest-hyperglycemia-value", "display": "Highest Hyperglycemia Value", "system": "http://tecnomod-um.org/CodeSystem/analytics-codes-cs"})  

class GlasgowComaScale(ConceptEnum):
    GCS_3 = ("3", {"code": "26394007", "display": "Glasgow coma scale, 3 (finding)", "system": "http://snomed.info/sct"})
    GCS_4 = ("4", {"code": "112110007", "display": "Glasgow coma scale, 4 (finding)", "system": "http://snomed.info/sct"})
    GCS_5 = ("5", {"code": "74957005", "display": "Glasgow coma scale, 5 (finding)", "system": "http://snomed.info/sct"})
    GCS_6 = ("6", {"code": "80072008", "display": "Glasgow coma scale, 6 (finding)", "system": "http://snomed.info/sct"})
    GCS_7 = ("7", {"code": "18136007", "display": "Glasgow coma scale, 7 (finding)", "system": "http://snomed.info/sct"})
    GCS_8 = ("8", {"code": "32856008", "display": "Glasgow coma scale, 8 (finding)", "system": "http://snomed.info/sct"})
    GCS_9 = ("9", {"code": "5999000", "display": "Glasgow coma scale, 9 (finding)", "system": "http://snomed.info/sct"})
    GCS_10 = ("10", {"code": "1184008", "display": "Glasgow coma scale, 10 (finding)", "system": "http://snomed.info/sct"})
    GCS_11 = ("11", {"code": "61102007", "display": "Glasgow coma scale, 11 (finding)", "system": "http://snomed.info/sct"})
    GCS_12 = ("12", {"code": "91234001", "display": "Glasgow coma scale, 12 (finding)", "system": "http://snomed.info/sct"})
    GCS_13 = ("13", {"code": "54185009", "display": "Glasgow coma scale, 13 (finding)", "system": "http://snomed.info/sct"})
    GCS_14 = ("14", {"code": "26734006", "display": "Glasgow coma scale, 14 (finding)", "system": "http://snomed.info/sct"})
    GCS_15 = ("15", {"code": "70040003", "display": "Glasgow coma scale, 15 (finding)", "system": "http://snomed.info/sct"})
    GCS = ("GCS", {"code": "248241002", "display": "Glasgow coma scale (observable entity)", "system": "http://snomed.info/sct"})

class NotMedicationReason(ConceptEnum):
    ALLERGY = ("Allergy", {"code": "609328004", "display": "Allergy disposition (finding)", "system": "http://snomed.info/sct"})
    MENTAL_STATUS = ("Mental Status", {"code": "36456004", "display": "Mental state finding (finding)", "system": "http://snomed.info/sct"})
    REFUSED = ("Refused", {"code": "443390004", "display": "Declined (qualifier value)", "system": "http://snomed.info/sct"})
    FALL_RISK = ("Fall Risk", {"code": "129839007", "display": "At increased risk for falls (finding)", "system": "http://snomed.info/sct"})
    BLEEDING = ("Bleeding", {"code": "131148009", "display": "Bleeding (finding)", "system": "http://snomed.info/sct"})
    SIDE_EFFECT = ("Side Effect", {"code": "401207004", "display": "Medication side effects present (finding)", "system": "http://snomed.info/sct"})
    PLANNED = ("Planned", {"code": "397943006", "display": "Planned (qualifier value)", "system": "http://snomed.info/sct"})
    TERMINAL_ILLNESS = ("Terminal Illness", {"code": "300936002", "display": "Terminal illness (finding)", "system": "http://snomed.info/sct"})
    CONSENT = ("Consent", {"code": "Not-Consent", "display": "Patient or family did not consent ", "system": "http://tecnomod-um.org/CodeSystem/not-medication-reason-cs"})
    COST = ("Cost", {"code": "Cost of drug", "display": "Cost of drug", "system": "http://tecnomod-um.org/CodeSystem/not-medication-reason-cs"})
    NOT_AVAILABLE = ("Not Available", {"code": "Not-Available", "display": "Medication not available", "system": "http://tecnomod-um.org/CodeSystem/not-medication-reason-cs"})
    NOT_LICENSED = ("Not Licensed", {"code": "Not-Licensed", "display": "Medication not licensed", "system": "http://tecnomod-um.org/CodeSystem/not-medication-reason-cs"})
    NOT_CRITERIA = ("Not Criteria", {"code": "Not-Criteria", "display": "Patient does not meet criteria for medication", "system": "http://tecnomod-um.org/CodeSystem/not-medication-reason-cs"})
    FORGOT = ("Forgot", {"code": "Forgot", "display": "Patient forgot to take medication", "system": "http://tecnomod-um.org/CodeSystem/not-medication-reason-cs"})


