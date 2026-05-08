# RESQ2FHIR - Stroke Data to FHIR Resources API

Transform preprocessed stroke patient data (CSV) into HL7 FHIR-compliant JSON bundles through an orchestrated API.

## Overview

This project implements a **CSV-to-FHIR conversion pipeline** tailored for stroke (RESQ) registries:

1. **CSV Input**: Preprocessed stroke patient data with clinical observations
2. **Converter**: `scripts/transform.py` transforms each row into a complete FHIR Bundle
3. **API Layer**: FastAPI orchestrates validation and optional persistence to HAPI FHIR Server
4. **Validation**: FHIR bundles are validated against profiles via validator-api

## Architecture

```
┌─────────────────────┐
│   User/Client       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  FastAPI (main.py)                  │
│  POST /jobs/csv                     │
└──────────────┬──────────────────────┘
               │
               ├─► Save CSV upload
               │
               ├─► Run converter (transform.py)
               │   ├─ Read CSV
               │   ├─ Transform rows → FHIR Bundles
               │   └─ Write *.json files
               │
               ├─► Validate Bundles (validator-api)
               │
               ├─► [Optional] Persist to HAPI
               │
               └─► Return summary report
```

## Project Structure

```
RESQ2FHIR/
├── data/
│   ├── data-extended.csv           # Input data (preprocessed stroke records)
│   └── mappings.csv                 # Field→FHIR mappings reference
├── scripts/
│   ├── transform.py                 # CSV → FHIR Bundles converter
│   ├── main.py                      # FastAPI application
│   ├── data_modeling.py             # FHIR transformation orchestrator
│   ├── enum_models.py               # SNOMED/FHIR concept enums
│   ├── helpers.py                   # Domain-specific helpers
│   ├── utils.py                     # Shared utilities
│   └── fhir_resources/              # FHIR resource builders
│       ├── patient.py
│       ├── encounter.py
│       ├── condition.py
│       ├── observation.py
│       ├── procedure.py
│       ├── medication*.py
│       └── ...
├── requirements.txt                 # Python dependencies
├── .env.example                     # Configuration template
└── README.md                        # This file
```

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

1. **Clone/Extract the repository**
   ```bash
   cd RESQ2FHIR
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Usage

### Option 1: Direct Converter (CLI)

Transform a CSV file to FHIR Bundles without the API:

```bash
python scripts/transform.py --input data/data-extended.csv --outdir ./bundles --verbose
```

**Output**: JSON files in `./bundles/` (one per patient, named by case_id)

### Option 2: REST API

Start the FastAPI server and use the `/jobs/csv` endpoint:

```bash
# Start the server
uvicorn scripts.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, upload a CSV
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@data/data-extended.csv" \
  -F "parallelism=6" \
  -F "persistToHapi=false"
```

**Response**:
```json
{
  "jobId": "20240101-120000-a1b2c3d4",
  "input": {
    "filename": "data-extended.csv",
    "rows": 150
  },
  "totals": {
    "bundles": 150,
    "errors": 0,
    "warnings": 5
  },
  "bySeverity": {
    "fatal": 0,
    "error": 0,
    "warning": 5,
    "information": 120
  },
  "bundles": [
    {
      "bundle": "case_uuid_1.json",
      "issues": { "fatal": 0, "error": 0, "warning": 0, "information": 2 }
    }
  ],
  "hapiUpload": {
    "attempted": 150,
    "uploaded": 150,
    "failures": []
  }
}
```

## Configuration

### Environment Variables (`.env`)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `WORKDIR` | Work directory for job files | No | `/app/workdir` |
| `CONVERTER_CMD` | Converter execution command | **YES** | (empty) |
| `VALIDATOR_BASE_URL` | FHIR validator API URL | No | `http://localhost:8085` |
| `VALIDATOR_PATH` | Validator endpoint path | No | `/api/validate/bundle` |
| `HAPI_BASE_URL` | HAPI FHIR Server URL | No | (empty) |
| `HAPI_BEARER` | Bearer token for HAPI | No | (empty) |
| `JOB_TAG_SYSTEM` | Job identifier system | No | `https://resq_fhir/job` |

### CONVERTER_CMD

This is **mandatory** for the API to function. It defines how the converter is invoked:

```bash
# Example for local Python
CONVERTER_CMD=python scripts/transform.py --input {in} --outdir {out}

# Example with Spark (for large datasets)
CONVERTER_CMD=spark-submit --master local[*] scripts/transform.py --input {in} --outdir {out}

# Windows example
CONVERTER_CMD=python C:\path\to\scripts\transform.py --input {in} --outdir {out}
```

Placeholders:
- `{in}` → Input CSV file path
- `{out}` → Output directory for bundles

## API Endpoints

### Health Check
```bash
GET /health
```

### Create Job from CSV
```bash
POST /jobs/csv
Content-Type: multipart/form-data

Parameters:
  - file (required): CSV file
  - profile (optional): FHIR profile URL to validate against
  - parallelism (optional, 1-16, default=6): Validation concurrency
  - persistToHapi (optional, default=false): Upload to HAPI if no errors
  - persistOnlyIfNoErrors (optional, default=true): Only persist error-free bundles
```

## Data Mapping

The converter uses `data/mappings.csv` to map CSV fields to FHIR concepts:

- **Observable fields** → FHIR Observations
- **Condition fields** → FHIR Conditions
- **Procedure fields** → FHIR Procedures
- **Medication fields** → FHIR MedicationStatements/Requests

Example mapping:
```
field_id,pattern_type,source_procedure,observable,finding,ontology_mapping
age,ObservationResultStatement,http://snomed.info/id/32485007,http://snomed.info/id/424144002,,AdmissionAge,Integer
sex,ClinicalSituationStatement,http://snomed.info/id/32485007,,http://snomed.info/id/184100006,AdmissionGender,Categorical
```

## Output Format

Each generated bundle is a FHIR `Bundle` with `type=transaction`:

```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "fullUrl": "urn:uuid:...",
      "resource": {
        "resourceType": "Organization",
        "id": "...",
        ...
      },
      "request": {
        "method": "POST",
        "url": "Organization"
      }
    },
    {
      "fullUrl": "urn:uuid:...",
      "resource": {
        "resourceType": "Patient",
        ...
      },
      "request": {
        "method": "POST",
        "url": "Patient"
      }
    },
    ...
  ]
}
```

## Troubleshooting

### Converter not found
```
Error: Converter exited with code 127
```
**Solution**: Check that `CONVERTER_CMD` is correctly set in `.env` and the script path is absolute.

### Missing required field
```
TransformError: Missing required field 'hospitalized_in'
```
**Solution**: Ensure your CSV contains all required columns. Check `data_modeling.py` for field requirements.

### Validation failures
Check the generated `{job_id}/outcomes/*.oo.json` files for `OperationOutcome` details.

### Import errors
```
ModuleNotFoundError: No module named 'scripts'
```
**Solution**: Run the API from the project root:
```bash
cd RESQ2FHIR
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python scripts/transform.py --input data/data-extended.csv --outdir ./bundles
```

## Development

### Adding a New FHIR Resource Type

1. Create `scripts/fhir_resources/new_resource.py`:
   ```python
   from fhir.resources.new_resource import NewResource
   
   def build_new_resource(patient_ref: str, ...) -> NewResource:
       """Build FHIR NewResource from raw data."""
       resource = NewResource()
       # Populate fields
       return resource
   ```

2. Import and use in `data_modeling.py`:
   ```python
   from scripts.fhir_resources.new_resource import build_new_resource
   
   # In transform_to_fhir():
   new_res = build_new_resource(patient_ref, ...)
   entries.append(BundleEntry(...))
   ```

### Testing

```bash
# Test converter alone
python scripts/transform.py --input data/data-extended.csv --outdir ./test_output --verbose

# Test API with curl
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@data/data-extended.csv"

# Check job results
ls -la workdir/jobs/{job_id}/
cat workdir/jobs/{job_id}/job.json
```

## FHIR Standards Compliance

This implementation targets:
- **FHIR R4** (4.0.1)
- **SNOMED CT** for clinical coding
- **HL7v3** coded value systems (where applicable)
- Custom ValueSets for stroke-specific concepts

## References

- [FHIR R4 Specification](https://www.hl7.org/fhir/R4/)
- [SNOMED CT Browser](https://browser.ihtsdotools.org/)
- [SK2FHIR Reference Implementation](https://github.com/tecnomod-um/SK2FHIR)
- RESQ Stroke Registry Schema

## License

See LICENSE file

## Support

For issues or questions:
1. Check this README and troubleshooting section
2. Review converter logs in `{job_id}/_converter.std*.log`
3. Check validation outcomes in `{job_id}/outcomes/*.oo.json`

---

**Last Updated**: 2024  
**Version**: 1.0.0
