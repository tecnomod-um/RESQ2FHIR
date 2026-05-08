RESQ2FHIR - SETUP & DEPLOYMENT GUIDE
====================================

This file contains step-by-step instructions for setting up and deploying the RESQ2FHIR system.

## PREREQUISITES

- Python 3.9+
- pip (Python package manager)
- (Optional) Docker & Docker Compose for containerized deployment
- (Optional) FHIR Validator API service
- (Optional) HAPI FHIR Server for data persistence

## INSTALLATION (Local Development)

### Step 1: Clone/Extract the Repository
```bash
cd RESQ2FHIR
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create venv
python -m venv venv

# Activate venv
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy configuration template
cp .env.example .env

# Edit .env (MANDATORY: set CONVERTER_CMD)
# For Unix/Linux/Mac:
nano .env
# For Windows:
notepad .env
```

**Key Configuration Variables:**
- `CONVERTER_CMD` (MANDATORY): How to run the converter
  ```
  CONVERTER_CMD=python scripts/transform.py --input {in} --outdir {out}
  ```
- `VALIDATOR_BASE_URL` (Optional): FHIR Validator service
- `HAPI_BASE_URL` (Optional): HAPI FHIR Server
- `WORKDIR` (Optional): Working directory for job files

### Step 5: Verify Installation
```bash
# Run setup demo (tests installation and converter)
python setup_demo.py

# Or run integration tests
python test_converter.py --verbose
```

## USAGE

### Method 1: CLI Converter Only
Convert CSV to FHIR Bundles without API:

```bash
python scripts/transform.py \
  --input data/data-extended.csv \
  --outdir ./bundles \
  --verbose
```

**Output:**
- JSON files in `./bundles/`
- One file per patient (named by case_id)
- Each file is a FHIR Bundle (transaction type)

### Method 2: FastAPI Server
Start the full API with validation:

```bash
# Terminal 1: Start API server
export PYTHONPATH="$PYTHONPATH:$(pwd)"
uvicorn scripts.main:app --host 0.0.0.0 --port 8000 --reload
```

**Available Endpoints:**

- `GET /health` - Health check
- `POST /jobs/csv` - Upload CSV and process
  - Parameters:
    - `file` (required): CSV file
    - `profile` (optional): FHIR profile to validate against
    - `parallelism` (optional, 1-16): Validation concurrency
    - `persistToHapi` (optional): Save to HAPI if no errors

**Example Request:**
```bash
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@data/data-extended.csv" \
  -F "parallelism=6"
```

### Method 3: Docker Deployment
Deploy complete stack with Docker Compose:

```bash
# Start all services (API, Validator, HAPI)
docker-compose up

# Services will be available at:
# - API: http://localhost:8000
# - Validator: http://localhost:8085
# - HAPI FHIR: http://localhost:8080
```

**First Time Setup:**
```bash
docker-compose up --build  # Build Docker images
```

**Cleanup:**
```bash
docker-compose down         # Stop all services
docker-compose down -v      # Also remove volumes
```

## TESTING

### Unit/Integration Tests
```bash
# Run all tests
python test_converter.py

# Verbose mode
python test_converter.py --verbose

# Specific test
python -m pytest test_converter.py::test_csv_load -v
```

### Manual Testing
```bash
# Test with small sample
head -11 data/data-extended.csv > test_sample.csv

python scripts/transform.py \
  --input test_sample.csv \
  --outdir ./test_output \
  --verbose

# Inspect output
ls -la test_output/
cat test_output/*.json | python -m json.tool | head -100
```

### Validate Generated Bundles
If you have a FHIR Validator running:

```bash
# Manual validation via curl
curl -X POST http://localhost:8085/api/validate/bundle \
  -H "Content-Type: application/json" \
  -d @bundles/case_id.json
```

## TROUBLESHOOTING

### 1. CONVERTER_CMD not configured
**Error:** `RuntimeError: CONVERTER_CMD is not set`

**Solution:**
- Set environment variable: `export CONVERTER_CMD="python scripts/transform.py --input {in} --outdir {out}"`
- OR configure in `.env` file

### 2. Module import errors
**Error:** `ModuleNotFoundError: No module named 'scripts'`

**Solution:**
- Ensure you're running from project root
- Set PYTHONPATH: `export PYTHONPATH="$PYTHONPATH:$(pwd)"`

### 3. CSV encoding issues
**Error:** `UnicodeDecodeError: 'utf-8' codec can't decode`

**Solution:**
- Ensure CSV is saved with UTF-8 encoding
- Try: `iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv`

### 4. Missing required fields
**Error:** `TransformError: Missing required field 'hospitalized_in'`

**Solution:**
- Check that CSV contains all required columns
- See DATA_TRANSFORMATION.md for field mappings

### 5. API connection errors
**Error:** `Connection refused to validator`

**Solution:**
- Ensure VALIDATOR_BASE_URL is correct
- Verify validator service is running: `curl http://localhost:8085/health`
- Set `SKIP_VALIDATION=true` temporarily to test converter only

### 6. Docker issues
**Error:** `docker: command not found`

**Solution:**
- Install Docker: https://docs.docker.com/install/
- Add your user to docker group: `sudo usermod -aG docker $USER`

## CONFIGURATION DETAILS

### Environment Variables

```bash
# Core
WORKDIR=/tmp/resq2fhir/workdir
CONVERTER_CMD=python scripts/transform.py --input {in} --outdir {out}

# FHIR Validator
VALIDATOR_BASE_URL=http://localhost:8085
VALIDATOR_PATH=/api/validate/bundle

# HAPI FHIR (Optional)
HAPI_BASE_URL=http://localhost:8080/fhir
HAPI_BEARER=

# Metadata
JOB_TAG_SYSTEM=https://resq_fhir/job
```

### Docker Environment
In `docker-compose.yml`, services are configured to:
1. API server listens on port 8000
2. Validator listens on port 8085
3. HAPI FHIR listens on port 8080

To customize ports, edit `docker-compose.yml`:
```yaml
services:
  api:
    ports:
      - "8000:8000"  # Change first number for custom port
```

## MONITORING

### Check Job Status
Jobs are stored in `WORKDIR/jobs/{job_id}/`:

```bash
# List jobs
ls -la workdir/jobs/

# Check job summary
cat workdir/jobs/{job_id}/job.json | python -m json.tool

# View converter logs
tail -f workdir/jobs/{job_id}/_converter.stdout.log
tail -f workdir/jobs/{job_id}/_converter.stderr.log

# View validation outcomes
ls workdir/jobs/{job_id}/outcomes/
cat workdir/jobs/{job_id}/outcomes/*.oo.json | python -m json.tool
```

## PERFORMANCE OPTIMIZATION

### For Large CSV Files (>100k rows)

1. **Use Spark:**
   ```bash
   CONVERTER_CMD="spark-submit --master local[*] scripts/transform.py --input {in} --outdir {out}"
   ```

2. **Increase Validation Parallelism:**
   ```bash
   # In API call
   curl -X POST http://localhost:8000/jobs/csv \
     -F "file=@large_file.csv" \
     -F "parallelism=16"  # Increase from default 6
   ```

3. **Skip Validation if Not Needed:**
   ```bash
   SKIP_VALIDATION=true python scripts/transform.py --input data.csv --outdir ./out
   ```

## SCALING CONSIDERATIONS

### Single Machine
- Recommended: <1M rows
- Memory: 4+ GB
- CPU: 4+ cores

### Distributed (Spark)
- For: >1M rows
- Requires: Spark cluster
- Update CONVERTER_CMD to use spark-submit

### Cloud Deployment
- Containerize with provided Dockerfile
- Deploy to: Kubernetes, AWS ECS, Azure Container Instances, etc.

## SECURITY NOTES

1. **Never commit `.env` file** with real credentials
2. **Use `.env.example`** as template
3. **Secure HAPI_BEARER token** in production
4. **Run validator/HAPI on internal network** only in production
5. **Enable HTTPS** when exposing API publicly
6. **Use authentication/authorization** in production (not included)

## NEXT STEPS

1. **Read documentation:**
   - `README.md` - Full feature overview
   - `DATA_TRANSFORMATION.md` - CSV field mappings
   - `CONTRIBUTING.md` - How to extend

2. **Explore examples:**
   - Run `setup_demo.py`
   - Check `QUICKSTART.sh` or `QUICKSTART.ps1`

3. **Customize for your data:**
   - Review your CSV structure
   - Check field mappings in DATA_TRANSFORMATION.md
   - Add custom FHIR resource builders if needed

4. **Set up production deployment:**
   - Configure Docker deployment
   - Set up monitoring/logging
   - Implement authentication

## SUPPORT

- Check README.md for common questions
- Review error messages in converter logs
- Check validation outcomes in `{job_id}/outcomes/` 
- See CONTRIBUTING.md for extending the system

## VERSION INFO

- RESQ2FHIR: 1.0.0
- FHIR Standard: R4 (4.0.1)
- Python: 3.9+
- Last Updated: 2024

---

For issues or questions, refer to the documentation files or create an issue in the repository.
