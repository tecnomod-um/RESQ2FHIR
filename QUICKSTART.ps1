# RESQ2FHIR Quick Start Examples (Windows PowerShell)
# Copy and run these commands from the project root

Write-Host "================================" -ForegroundColor Cyan
Write-Host "RESQ2FHIR - Quick Start Examples" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Example 1: Install dependencies
Write-Host "[1] Installing dependencies..." -ForegroundColor Yellow
Write-Host "    pip install -r requirements.txt" -ForegroundColor Gray
Write-Host ""

# Example 2: Run converter on sample data
Write-Host "[2] Convert CSV to FHIR Bundles (Converter only)..." -ForegroundColor Yellow
Write-Host "    python scripts/transform.py --input data/data-extended.csv --outdir ./bundles --verbose" -ForegroundColor Gray
Write-Host ""
Write-Host "    Output: JSON files in ./bundles/" -ForegroundColor Gray
Write-Host "    One file per patient (named by case_id)" -ForegroundColor Gray
Write-Host ""

# Example 3: Run integration test
Write-Host "[3] Run integration tests..." -ForegroundColor Yellow
Write-Host "    python test_converter.py --verbose" -ForegroundColor Gray
Write-Host ""

# Example 4: Start API server
Write-Host "[4] Start FastAPI server..." -ForegroundColor Yellow
Write-Host "    # Terminal 1: Start the server" -ForegroundColor Gray
Write-Host "    uvicorn scripts.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "    # Terminal 2: Upload CSV and process" -ForegroundColor Gray
Write-Host "    `$params = @{" -ForegroundColor Gray
Write-Host "        Uri = 'http://localhost:8000/jobs/csv'" -ForegroundColor Gray
Write-Host "        Method = 'POST'" -ForegroundColor Gray
Write-Host "        Form = @{" -ForegroundColor Gray
Write-Host "            file = Get-Item 'data/data-extended.csv'" -ForegroundColor Gray
Write-Host "        }" -ForegroundColor Gray
Write-Host "    }" -ForegroundColor Gray
Write-Host "    Invoke-WebRequest @params" -ForegroundColor Gray
Write-Host ""

# Example 5: Run with Docker
Write-Host "[5] Run with Docker Compose..." -ForegroundColor Yellow
Write-Host "    # Make sure Docker and Docker Compose are installed" -ForegroundColor Gray
Write-Host "    docker-compose up" -ForegroundColor Gray
Write-Host ""
Write-Host "    # Services available:" -ForegroundColor Gray
Write-Host "    # - API: http://localhost:8000" -ForegroundColor Gray
Write-Host "    # - Validator: http://localhost:8085" -ForegroundColor Gray
Write-Host "    # - HAPI FHIR: http://localhost:8080" -ForegroundColor Gray
Write-Host ""

# Example 6: Configuration
Write-Host "[6] Configuration..." -ForegroundColor Yellow
Write-Host "    # Copy example config" -ForegroundColor Gray
Write-Host "    Copy-Item .env.example .env" -ForegroundColor Gray
Write-Host "    # Edit .env to customize:" -ForegroundColor Gray
Write-Host "    notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "    Key variables:" -ForegroundColor Gray
Write-Host "    - CONVERTER_CMD: (MANDATORY) How to run the converter" -ForegroundColor Gray
Write-Host "    - VALIDATOR_BASE_URL: FHIR Validator service URL" -ForegroundColor Gray
Write-Host "    - HAPI_BASE_URL: HAPI FHIR Server URL (optional)" -ForegroundColor Gray
Write-Host ""

# Example 7: Check generated bundles
Write-Host "[7] Inspect generated bundles..." -ForegroundColor Yellow
Write-Host "    # List generated files" -ForegroundColor Gray
Write-Host "    Get-ChildItem bundles/ -Filter '*.json'" -ForegroundColor Gray
Write-Host ""
Write-Host "    # View one bundle" -ForegroundColor Gray
Write-Host "    Get-Content bundles/*.json | python -m json.tool | Select-Object -First 50" -ForegroundColor Gray
Write-Host ""

# Example 8: Validate bundles manually
Write-Host "[8] Validate bundles against FHIR profiles..." -ForegroundColor Yellow
Write-Host "    `$bundle = Get-Content bundles/case_id.json" -ForegroundColor Gray
Write-Host "    Invoke-WebRequest -Uri 'http://localhost:8085/api/validate/bundle' `" -ForegroundColor Gray
Write-Host "      -Method Post `" -ForegroundColor Gray
Write-Host "      -ContentType 'application/json' `" -ForegroundColor Gray
Write-Host "      -Body `$bundle" -ForegroundColor Gray
Write-Host ""

# Example 9: Troubleshooting
Write-Host "[9] Troubleshooting..." -ForegroundColor Yellow
Write-Host ""
Write-Host "    Issue: CONVERTER_CMD not set" -ForegroundColor Red
Write-Host "    Fix: Set CONVERTER_CMD env var or in .env file" -ForegroundColor Green
Write-Host ""
Write-Host "    Issue: Module not found: 'scripts'" -ForegroundColor Red
Write-Host "    Fix: Run from project root and ensure PYTHONPATH is correct" -ForegroundColor Green
Write-Host "    `$env:PYTHONPATH += ';' + (Get-Location)" -ForegroundColor Gray
Write-Host ""
Write-Host "    Issue: CSV parsing errors" -ForegroundColor Red
Write-Host "    Fix: Check that CSV uses UTF-8 encoding and valid column names" -ForegroundColor Green
Write-Host ""

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "More information:" -ForegroundColor Cyan
Write-Host "- README.md - Full documentation" -ForegroundColor Gray
Write-Host "- DATA_TRANSFORMATION.md - CSV field mappings" -ForegroundColor Gray
Write-Host "- CONTRIBUTING.md - How to extend the project" -ForegroundColor Gray
Write-Host "- .env.local - Example environment configuration" -ForegroundColor Gray
Write-Host "================================" -ForegroundColor Cyan
