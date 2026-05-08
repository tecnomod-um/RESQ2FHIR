#!/bin/bash
# RESQ2FHIR Quick Start Examples
# Copy and run these commands from the project root

echo "================================"
echo "RESQ2FHIR - Quick Start Examples"
echo "================================"
echo ""

# Example 1: Install dependencies
echo "[1] Installing dependencies..."
echo "    pip install -r requirements.txt"
echo ""

# Example 2: Run converter on sample data
echo "[2] Convert CSV to FHIR Bundles (Converter only)..."
echo "    python scripts/transform.py --input data/data-extended.csv --outdir ./bundles --verbose"
echo ""
echo "    Output: JSON files in ./bundles/"
echo "    One file per patient (named by case_id)"
echo ""

# Example 3: Run integration test
echo "[3] Run integration tests..."
echo "    python test_converter.py --verbose"
echo ""

# Example 4: Start API server
echo "[4] Start FastAPI server..."
echo "    # Terminal 1: Start the server"
echo "    uvicorn scripts.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "    # Terminal 2: Upload CSV and process"
echo "    curl -X POST http://localhost:8000/jobs/csv \\"
echo "      -F 'file=@data/data-extended.csv' \\"
echo "      -F 'parallelism=6'"
echo ""

# Example 5: Run with Docker
echo "[5] Run with Docker Compose..."
echo "    # Make sure Docker and Docker Compose are installed"
echo "    docker-compose up"
echo ""
echo "    # Services available:"
echo "    # - API: http://localhost:8000"
echo "    # - Validator: http://localhost:8085"
echo "    # - HAPI FHIR: http://localhost:8080"
echo ""

# Example 6: Configuration
echo "[6] Configuration..."
echo "    # Copy example config"
echo "    cp .env.example .env"
echo "    # Edit .env to customize:"
echo "    vim .env"
echo ""
echo "    Key variables:"
echo "    - CONVERTER_CMD: (MANDATORY) How to run the converter"
echo "    - VALIDATOR_BASE_URL: FHIR Validator service URL"
echo "    - HAPI_BASE_URL: HAPI FHIR Server URL (optional)"
echo ""

# Example 7: Check generated bundles
echo "[7] Inspect generated bundles..."
echo "    # List generated files"
echo "    ls -lh bundles/"
echo ""
echo "    # View one bundle"
echo "    cat bundles/*.json | python -m json.tool | head -50"
echo ""

# Example 8: Validate bundles manually
echo "[8] Validate bundles against FHIR profiles..."
echo "    curl -X POST http://localhost:8085/api/validate/bundle \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d @bundles/case_id.json"
echo ""

# Example 9: Troubleshooting
echo "[9] Troubleshooting..."
echo ""
echo "    Issue: CONVERTER_CMD not set"
echo "    Fix: Set CONVERTER_CMD env var or in .env file"
echo ""
echo "    Issue: Module not found: 'scripts'"
echo "    Fix: Run from project root and ensure PYTHONPATH is correct"
echo "    export PYTHONPATH=\$PYTHONPATH:\$(pwd)"
echo ""
echo "    Issue: CSV parsing errors"
echo "    Fix: Check that CSV uses UTF-8 encoding and valid column names"
echo ""

echo ""
echo "================================"
echo "More information:"
echo "- README.md - Full documentation"
echo "- DATA_TRANSFORMATION.md - CSV field mappings"
echo "- CONTRIBUTING.md - How to extend the project"
echo "- .env.local - Example environment configuration"
echo "================================"
