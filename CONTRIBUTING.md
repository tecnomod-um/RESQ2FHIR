# Contributing to RESQ2FHIR

Thank you for your interest in contributing! This guide will help you understand how to extend and improve the RESQ2FHIR converter.

## Project Structure Review

### Core Components

1. **`scripts/transform.py`** - Main converter entry point
   - Reads CSV, iterates rows, generates FHIR bundles
   - Handles logging and error reporting
   - **Extend this if**: Adding new batch processing features

2. **`scripts/data_modeling.py`** - FHIR transformation orchestrator
   - Calls individual FHIR resource builders
   - Constructs complete bundles with all resources
   - **Extend this if**: Adding new resource types to the bundle

3. **`scripts/enum_models.py`** - SNOMED/FHIR concept enums
   - Defines coding systems, ValueSets, and code mappings
   - Uses ConceptEnum base class for structured codes
   - **Extend this if**: Adding new clinical codes or ValueSets

4. **`scripts/helpers.py`** - Domain-specific transformation helpers
   - Functions for extracting and grouping related fields
   - **Extend this if**: Adding complex multi-field transformations

5. **`scripts/utils.py`** - Shared utilities
   - Type validation, date parsing, error handling
   - **Extend this if**: Adding new common utilities

6. **`scripts/fhir_resources/`** - Individual FHIR resource builders
   - One module per FHIR resource type (patient.py, encounter.py, etc.)
   - **Extend this if**: Enhancing individual resource generation

## Common Extension Scenarios

### 1. Adding a New Clinical Observation

**Scenario**: You want to capture a new vital sign or lab value.

**Steps**:

1. Add the CSV field to your input data
2. Add a builder function in `scripts/fhir_resources/observation.py`:
   ```python
   def build_observation_my_measurement(
       patient_ref: str,
       encounter_ref: str,
       value: float,
       unit: str = "unit/L"
   ) -> Observation:
       """Build Observation for my measurement."""
       obs = Observation()
       obs.id = str(get_uuid())
       obs.status = "final"
       obs.code = CodeableConcept(coding=[Coding(
           system="http://snomed.info/sct",
           code="XXXX",  # SNOMED code
           display="My Measurement"
       )])
       obs.subject = Reference(reference=patient_ref)
       obs.encounter = Reference(reference=encounter_ref)
       obs.value_quantity = Quantity(value=value, unit=unit)
       return obs
   ```

3. Import and call in `data_modeling.py`:
   ```python
   from scripts.fhir_resources.observation import build_observation_my_measurement
   
   # In transform_to_fhir():
   if value := safe_get(raw, "my_measurement_field"):
       obs = build_observation_my_measurement(
           patient_ref=patient_ref,
           encounter_ref=encounter_ref,
           value=float(value)
       )
       entries.append(BundleEntry(...))
   ```

### 2. Adding a New FHIR Resource Type

**Scenario**: You want to add Medication, CarePlan, or another resource type.

**Steps**:

1. Create `scripts/fhir_resources/new_resource.py`:
   ```python
   """New resource builder for FHIR transformation."""
   from fhir.resources.new_resource import NewResource
   from utils import get_uuid
   
   def build_new_resource(patient_ref: str, ...) -> NewResource:
       """Build FHIR NewResource from raw data."""
       resource = NewResource()
       resource.id = str(get_uuid())
       resource.subject = Reference(reference=patient_ref)
       # ... populate fields ...
       return resource
   ```

2. Add enum codes if needed to `scripts/enum_models.py`

3. Import and use in `data_modeling.py`:
   ```python
   from scripts.fhir_resources.new_resource import build_new_resource
   
   # In transform_to_fhir():
   new_res = build_new_resource(patient_ref, ...)
   entries.append(BundleEntry(
       fullUrl=get_uuid(),
       resource=new_res,
       request=BundleEntryRequest(method="POST", url="NewResource")
   ))
   ```

### 3. Adding a New Value Set

**Scenario**: You need to map new categorical values.

**Steps**:

1. Define enum in `scripts/enum_models.py`:
   ```python
   class MyNewValueSet(ConceptEnum):
       OPTION_A = ("OptA", {
           "code": "code-a",
           "display": "Option A",
           "system": "http://tecnomod-um.org/CodeSystem/my-vs"
       })
       OPTION_B = ("OptB", {
           "code": "code-b",
           "display": "Option B",
           "system": "http://tecnomod-um.org/CodeSystem/my-vs"
       })
   ```

2. Use in transformation:
   ```python
   from scripts.enum_models import MyNewValueSet
   
   value = MyNewValueSet.by_id(safe_get(raw, "field_name"))
   if value:
       # Use value.code, value.display, value.system
   ```

### 4. Adding a Helper Function

**Scenario**: You need to extract and transform complex multi-field data.

**Steps**:

1. Add to `scripts/helpers.py`:
   ```python
   def get_my_complex_data(raw: dict) -> tuple:
       """Extract and categorize complex data."""
       list_a = []
       list_b = []
       for field_name, field_value in raw.items():
           if field_name.startswith("prefix_") and field_value is True:
               list_a.append(...)
           elif field_name.startswith("other_") and field_value is True:
               list_b.append(...)
       return list_a, list_b
   ```

2. Use in `data_modeling.py`:
   ```python
   from scripts.helpers import get_my_complex_data
   
   a_list, b_list = get_my_complex_data(raw)
   for item in a_list:
       # Process item
   ```

## Testing Your Changes

### Unit Testing Pattern

```python
# test_my_changes.py
import pytest
from scripts.utils import safe_get, TransformError
from scripts.fhir_resources.observation import build_observation_my_measurement

def test_build_observation_my_measurement():
    obs = build_observation_my_measurement(
        patient_ref="urn:uuid:123",
        encounter_ref="urn:uuid:456",
        value=42.5
    )
    assert obs.status == "final"
    assert obs.value_quantity.value == 42.5
    assert obs.subject.reference == "urn:uuid:123"

def test_safe_get_with_missing_field():
    raw = {"field1": "value1"}
    result = safe_get(raw, "missing_field", required=False)
    assert result is None

def test_safe_get_with_required_field_missing():
    raw = {"field1": "value1"}
    with pytest.raises(TransformError):
        safe_get(raw, "missing_field", required=True)
```

### Integration Testing

Test with a small CSV sample:

```bash
# Create test CSV with 10 rows
head -11 data/data-extended.csv > test_sample.csv

# Run converter
python scripts/transform.py --input test_sample.csv --outdir ./test_output --verbose

# Inspect output
ls -la test_output/
cat test_output/*.json | python -m json.tool
```

## Code Style Guidelines

### Python
- Follow PEP 8
- Type hints for function signatures
- Docstrings for all public functions
- Use descriptive variable names

```python
def build_observation_glucose(
    patient_ref: str,
    encounter_ref: str,
    glucose: float,
    timing: str = "admission"
) -> Observation:
    """
    Build FHIR Observation for glucose measurement.
    
    Args:
        patient_ref: Reference to Patient resource
        encounter_ref: Reference to Encounter resource
        glucose: Blood glucose value (mg/dL)
        timing: Assessment context (admission/discharge/etc)
        
    Returns:
        Observation resource
        
    Raises:
        TransformError: If glucose value is invalid
    """
```

### FHIR Resources
- Always set `.id` with `get_uuid()` or patient id
- Use `Reference` objects, not raw strings
- Set `.status` to appropriate value
- Use SNOMED CT codes where possible
- Include `coding` (structured) + `text` (human-readable)

## Common Pitfalls

### ❌ Don't: Hardcode UUIDs
```python
obs.id = "12345"  # ❌ Not unique!
```

### ✅ Do: Use get_uuid()
```python
from utils import get_uuid
obs.id = str(get_uuid())  # ✅ Unique per resource
```

### ❌ Don't: Ignore None values
```python
value = raw["field"]  # Crashes if field is missing
```

### ✅ Do: Use safe_get
```python
from utils import safe_get
value = safe_get(raw, "field", required=False)
if value:
    # Process value
```

### ❌ Don't: Mix string references
```python
encounter_ref = "Encounter/abc123"  # ❌ Inconsistent with UUID format
```

### ✅ Do: Use URN format
```python
encounter_ref = "urn:uuid:abc123"  # ✅ Consistent
# Or when creating references:
Reference(reference="urn:uuid:abc123")
```

## Documentation

When adding new features:
- Update README.md with usage examples
- Update DATA_TRANSFORMATION.md with field mappings
- Add docstrings to functions
- Include example inputs/outputs

## Submitting Changes

1. **Fork/Branch**: Create a feature branch
2. **Test**: Run your changes against sample data
3. **Document**: Update relevant docs
4. **Review**: Check for consistency with existing code
5. **Submit**: Create a pull request with description

## Performance Optimization

For large datasets (>100k rows):

### 1. Use Vectorized Operations
```python
# ❌ Slow: Loop over each row
for idx, row in df.iterrows():
    process(row)

# ✅ Faster: Vectorized operations
df.apply(lambda row: process(row), axis=1)
```

### 2. Consider Spark
```bash
# Use Spark for very large datasets
spark-submit --master local[*] scripts/transform.py --input large.csv --outdir output
```

### 3. Batch JSON Writing
```python
# Write in chunks, not individual files
with open(output_file, 'w') as f:
    for bundle in bundles:
        f.write(json.dumps(bundle) + "\n")  # JSONL format
```

## Support & Questions

- Check existing code patterns first
- Review DATA_TRANSFORMATION.md for field mappings
- Look at enum_models.py for available codes
- Ask in issues/discussions

## Resources

- [FHIR R4 Specification](https://www.hl7.org/fhir/R4/)
- [SNOMED CT Browser](https://browser.ihtsdotools.org/)
- [fhir.resources Library](https://github.com/nazrulworld/fhir.resources)
- [HL7 Terminology](http://terminology.hl7.org/)

---

Thank you for contributing to RESQ2FHIR!
