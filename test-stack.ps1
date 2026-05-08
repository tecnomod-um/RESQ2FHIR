#!/usr/bin/env pwsh

# Test RESQ2FHIR Stack - FHIR R5 + Snowstorm
# This script validates that all services are running and responsive

Write-Host "`n=== RESQ2FHIR Stack Validation ===" -ForegroundColor Cyan
Write-Host "Testing all services with FHIR R5 Bundle and SNOMED validation`n" -ForegroundColor Gray

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url"
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method $Method -ContentType "application/json" -ErrorAction Stop
        if ($Body) {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -Body $Body -ContentType "application/json" -ErrorAction Stop
        }
        Write-Host "  Status: $($response.StatusCode) ✅" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "  Status: $($_.Exception.Response.StatusCode) ⚠️" -ForegroundColor Yellow
        Write-Host "  Error: $($_.Exception.Message)"
        return $null
    }
}

# 1. Test Snowstorm (SNOMED CT terminology server)
Write-Host "`n[1/5] Snowstorm Terminology Server" -ForegroundColor Cyan
Test-Endpoint -Name "Snowstorm Health" -Url "http://localhost:8081/fhir/metadata"

# 2. Test HAPI FHIR Server
Write-Host "`n[2/5] HAPI FHIR R5 Server" -ForegroundColor Cyan
Test-Endpoint -Name "HAPI FHIR Metadata" -Url "http://localhost:8082/fhir/metadata"

# 3. Test Validator Service - Health
Write-Host "`n[3/5] FHIR R5 Validator Service" -ForegroundColor Cyan
Test-Endpoint -Name "Validator Health" -Url "http://localhost:8085/actuator/health"

# 4. Test Validator - Validate Bundle
Write-Host "`n[4/5] Validator - FHIR Bundle Validation" -ForegroundColor Cyan
$bundleJson = Get-Content -Path "./test-bundle-r5.json" -Raw -ErrorAction SilentlyContinue

if ($bundleJson) {
    $validationResponse = Test-Endpoint -Name "Validate FHIR Bundle" `
        -Url "http://localhost:8085/api/validate/bundle" `
        -Method "POST" `
        -Body $bundleJson
    
    if ($validationResponse) {
        Write-Host "  Response Preview:"
        $responseContent = $validationResponse.Content | ConvertFrom-Json
        Write-Host "    Issues: $($responseContent.issue.count)" -ForegroundColor Cyan
        $responseContent.issue | ForEach-Object {
            $color = if ($_.severity -eq 'error') { 'Red' } else { 'Gray' }
            Write-Host "      - [$($_.severity)] $($_.code): $($_.details.text)" -ForegroundColor $color
        }
    }
} else {
    Write-Host "  ⚠️  test-bundle-r5.json not found in current directory" -ForegroundColor Yellow
}

# 5. Test ResQ2FHIR API
Write-Host "`n[5/5] ResQ2FHIR API Service" -ForegroundColor Cyan
Test-Endpoint -Name "API Health" -Url "http://localhost:8000/docs"

# Summary
Write-Host "`n=== Service Summary ===" -ForegroundColor Cyan
Write-Host "Endpoint Mapping:" -ForegroundColor Gray
Write-Host "  API:        http://localhost:8000" -ForegroundColor Gray
Write-Host "  Validator:  http://localhost:8085/api/validate/bundle" -ForegroundColor Gray  
Write-Host "  HAPI FHIR:  http://localhost:8082/fhir" -ForegroundColor Gray
Write-Host "  Snowstorm:  http://localhost:8081/fhir" -ForegroundColor Gray
Write-Host ""
