package com.example.validator.validation;

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.fhirpath.IFhirPath;
import ca.uhn.fhir.validation.IValidationContext;
import ca.uhn.fhir.validation.IValidatorModule;
import ca.uhn.fhir.validation.ResultSeverityEnum;
import ca.uhn.fhir.validation.SingleValidationMessage;
import com.example.validator.terminology.SnowstormClient;
import com.example.validator.terminology.SnowstormClient.ValidationStatus;
import org.hl7.fhir.instance.model.api.IBase;
import org.hl7.fhir.instance.model.api.IBaseResource;
import org.hl7.fhir.r5.model.Coding;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Validator module that checks SNOMED CT codings found in R5 resources through Snowstorm.
 */
@Component
public class SnomedSnowstormValidator implements IValidatorModule {

  private static final Logger log = LoggerFactory.getLogger(SnomedSnowstormValidator.class);
  private static final String SNOMED_SYSTEM = "http://snomed.info/sct";

  private final FhirContext ctx;
  private final SnowstormClient snow;

  public SnomedSnowstormValidator(FhirContext r5Ctx, SnowstormClient snow) {
    this.ctx = r5Ctx;
    this.snow = snow;
  }

  @Override
  public void validateResource(IValidationContext<IBaseResource> context) {
    IBaseResource resource = context.getResource();
    IFhirPath fhirPath = ctx.newFhirPath();

    List<IBase> codings = fhirPath.evaluate(
        resource,
        "descendants().ofType(Coding).where(system = '" + SNOMED_SYSTEM + "')",
        IBase.class
    );

    for (IBase baseCoding : codings) {
      Coding coding = (Coding) baseCoding;
      String code = coding.getCode();
      if (code == null || code.isBlank()) {
        continue;
      }

      ValidationStatus status = snow.validateSnomedCode(code);

      if (status == ValidationStatus.INVALID) {
        SingleValidationMessage msg = new SingleValidationMessage();
        msg.setSeverity(ResultSeverityEnum.ERROR);
        msg.setMessage("SNOMED: code " + code + " is not valid (Snowstorm returned result=false).");
        msg.setLocationString("Coding(" + SNOMED_SYSTEM + "|" + code + ")");
        context.addValidationMessage(msg);
        log.info("Invalid SNOMED detected: {}", code);
      } else if (status == ValidationStatus.UNAVAILABLE) {
        SingleValidationMessage msg = new SingleValidationMessage();
        msg.setSeverity(ResultSeverityEnum.WARNING);
        msg.setMessage("SNOMED terminology validation unavailable for code " + code + " after retries; code validity was not determined.");
        msg.setLocationString("Coding(" + SNOMED_SYSTEM + "|" + code + ")");
        context.addValidationMessage(msg);
        log.warn("SNOMED validation unavailable for {}", code);
      } else {
        log.debug("Valid SNOMED: {}", code);
      }
    }
  }
}
