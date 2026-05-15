package com.example.validator.validation;

import ca.uhn.fhir.fhirpath.IFhirPath;
import ca.uhn.fhir.validation.IValidationContext;
import ca.uhn.fhir.validation.IValidatorModule;
import ca.uhn.fhir.validation.ResultSeverityEnum;
import ca.uhn.fhir.validation.SingleValidationMessage;
import ca.uhn.fhir.context.FhirContext;
import com.example.validator.terminology.SnowstormClient;
import org.hl7.fhir.instance.model.api.IBase;
import org.hl7.fhir.instance.model.api.IBaseResource;
import org.hl7.fhir.r5.model.Coding;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Validator module that checks SNOMED CT codings found in any R5 resource
 * by calling Snowstorm's terminology endpoints.
 *
 * How it works:
 * - Uses FHIRPath to collect all Coding elements whose system is SNOMED CT.
 * - For each code, calls Snowstorm's FHIR API (via $validate-code operation).
 * - If validation fails, adds an error to the validation result.
 *
 * Notes:
 * - This module operates independently of the built-in HAPI terminology validators.
 * - It expects a FhirContext configured for R5.
 * - SNOMED code validation is version-agnostic (system + code pairs work across FHIR versions).
 */
@Component
public class SnomedSnowstormValidator implements IValidatorModule {

  private static final Logger log = LoggerFactory.getLogger(SnomedSnowstormValidator.class);

  /** SNOMED CT canonical system URI */
  private static final String SNOMED_SYSTEM = "http://snomed.info/sct";

  private final FhirContext ctx;
  private final SnowstormClient snow;

  /**
   * @param r5Ctx FHIR R5 context (used for FHIRPath evaluation over R5 resources)
   * @param snow  Tiny HTTP client that talks to Snowstorm
   */
  public SnomedSnowstormValidator(FhirContext r5Ctx, SnowstormClient snow) {
    this.ctx = r5Ctx;
    this.snow = snow;
  }

  /**
   * Entry point invoked by HAPI's validation pipeline.
   * We scan the resource for any SNOMED codings and validate them using Snowstorm.
   */
  @Override
  public void validateResource(IValidationContext<IBaseResource> context) {
    IBaseResource resource = context.getResource();
    IFhirPath fhirPath = ctx.newFhirPath();

    // Collect all Coding elements with system == SNOMED (R5 expression).
    // descendants().ofType(Coding) -> all Coding nodes anywhere in the resource
    // where(system = 'http://snomed.info/sct') -> only SNOMED CT codings
    List<IBase> codings = fhirPath.evaluate(
        resource,
        "descendants().ofType(Coding).where(system = '" + SNOMED_SYSTEM + "')",
        IBase.class
    );

    for (IBase baseCoding : codings) {
      Coding coding = (Coding) baseCoding;
      String code = coding.getCode();
      if (code == null || code.isBlank()) {
        // Ignore empty codes
        continue;
      }

      // Validate the code with Snowstorm (FHIR $validate-code).
      // Alternative (commented) shows how to use the native browser API instead.
      boolean ok = snow.validateSnomedCode(code);
      // boolean ok = snow.conceptExistsNative(code);

      if (!ok) {
        // Build a validation message and attach it to the context.
        SingleValidationMessage msg = new SingleValidationMessage();
        msg.setSeverity(ResultSeverityEnum.ERROR);
        msg.setMessage("SNOMED: code " + code + " is not valid (Snowstorm).");
        // Optional: include a pointer to the specific element
        msg.setLocationString("Coding(" + SNOMED_SYSTEM + "|" + code + ")");
        context.addValidationMessage(msg);
        log.info("Invalid SNOMED detected: {}", code);
      } else {
        log.debug("Valid SNOMED: {}", code);
      }
    }
  }
}
