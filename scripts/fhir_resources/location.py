
from fhir.resources.location import Location
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.meta import Meta
from scripts.enum_models import AdmissionDepartment, HospitalizedIn, Locations
from fhir.resources.extension import Extension


def build_location(location: Locations) -> Location:
    """
    Build a FHIR Location resource from raw data.
    
    Args:
        contact_place: FirstContactPlace enum member
        
    Returns:
        Location resource
    """
    loc = Location()
    location_coding = location.to_coding()
    loc.type = [CodeableConcept(coding=[location_coding])]
     
    return loc

def build_hospitalized_location(hospitalized_in: HospitalizedIn, admission_department: AdmissionDepartment) -> Location:
    """
    Build a FHIR Location resource from raw data.
    
    Args:
        hospitalized_in: HospitalizedIn enum member
        admission_department: AdmissionDepartment enum member
        
    Returns:
        Location resource
    """
    loc = Location()
    coding_hospitalized_in = Coding(
            system=hospitalized_in.system,
            code=hospitalized_in.code,
            display=hospitalized_in.display
        )
    extensionCode = CodeableConcept(coding=[coding_hospitalized_in])
    loc.meta = Meta(profile=["http://tecnomod-um.org/StructureDefinition/hospitalized-location-profile"])

    coding_admission_department = Coding(
            system=admission_department.system,
            code=admission_department.code,
            display=admission_department.display
        )
    admission_department_code = CodeableConcept(coding=[coding_admission_department])
   
    loc.type = [admission_department_code]
    extension_list = []        
    # Create extension url 
    extension_list.append(Extension(
                url="http://tecnomod-um.org/StructureDefinition/initial-care-intensity-ext",
                valueCodeableConcept=extensionCode
            ))
    loc.extension = extension_list
    return loc