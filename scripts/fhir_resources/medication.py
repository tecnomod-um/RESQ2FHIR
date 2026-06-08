from fhir.resources.medication import Medication, MedicationIngredient
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.meta import Meta

from scripts.enum_models import Medications, TenecteplaseBrand



def build_tenecteplase_brand_medication(tenecteplase_brand: TenecteplaseBrand ) -> Medication:
    """
    Build a FHIR Medication resource for tenecteplase brand.
    
    Args:
        tenecteplase_brand: The brand of tenecteplase (e.g., Metalyse, TNKase)
    Returns:
        Medication resource for tenecteplase brand
    """

    medication = Medication()
    medication.code = CodeableConcept(coding=[tenecteplase_brand.to_coding()])
    medication.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/tenecteplase-brand-medication-profile"])

    ingredient = MedicationIngredient(isActive=True, item= CodeableReference(concept=CodeableConcept(coding=[Medications.TENECTEPLASE.to_coding()])))
    medication.ingredient = [ingredient]

    return medication