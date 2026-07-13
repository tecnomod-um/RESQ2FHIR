package com.example.validator.validation;

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.context.support.ConceptValidationOptions;
import ca.uhn.fhir.context.support.IValidationSupport.CodeValidationIssue;
import ca.uhn.fhir.context.support.IValidationSupport.CodeValidationIssueCode;
import ca.uhn.fhir.context.support.IValidationSupport.CodeValidationIssueCoding;
import ca.uhn.fhir.context.support.IValidationSupport.CodeValidationResult;
import ca.uhn.fhir.context.support.IValidationSupport.IssueSeverity;
import ca.uhn.fhir.context.support.IValidationSupport.LookupCodeResult;
import ca.uhn.fhir.context.support.LookupCodeRequest;
import ca.uhn.fhir.context.support.ValidationSupportContext;
import ca.uhn.fhir.rest.client.api.IGenericClient;

import jakarta.annotation.Nonnull;

import org.hl7.fhir.common.hapi.validation.support.BaseValidationSupport;
import org.hl7.fhir.instance.model.api.IBaseResource;
import org.hl7.fhir.r5.model.BooleanType;
import org.hl7.fhir.r5.model.CodeSystem;
import org.hl7.fhir.r5.model.Parameters;
import org.hl7.fhir.r5.model.StringType;
import org.hl7.fhir.r5.model.UriType;
import org.hl7.fhir.r5.model.ValueSet;
import org.springframework.util.StringUtils;
import org.hl7.fhir.r5.model.Enumerations;
/**
 * R5 validation support dedicated exclusively to LOINC.
 *
 * It calls the local HAPI terminology server using R5 Parameters resources,
 * avoiding RemoteTerminologyServiceValidationSupport.lookupCode(), which only
 * supports DSTU3 and R4.
 */
public class LoincHapiValidationSupport extends BaseValidationSupport {

    public static final String LOINC_SYSTEM = "http://loinc.org";

    private final String baseUrl;

    public LoincHapiValidationSupport(FhirContext r5Context, String baseUrl) {
        super(r5Context);

        if (!StringUtils.hasText(baseUrl)) {
            throw new IllegalArgumentException(
                "LOINC terminology server base URL must not be empty"
            );
        }

        this.baseUrl = baseUrl.replaceAll("/+$", "");
    }

    @Override
    public String getName() {
        return "R5 LOINC HAPI validation support";
    }

    @Override
    public boolean isCodeSystemSupported(
        ValidationSupportContext context,
        String system
    ) {
        return LOINC_SYSTEM.equals(system);
    }

    /*
     * The chain asks this before calling validateCode when a ValueSet URL is
     * present. We accept the request but validate it only when its coding uses
     * LOINC. Returning null for non-LOINC systems lets the chain continue.
     */
    @Override
    public boolean isValueSetSupported(
        ValidationSupportContext context,
        String valueSetUrl
    ) {
        /*
        * Los ValueSet del IG se validan mediante NpmPackageValidationSupport
        * e InMemoryTerminologyServerValidationSupport.
        *
        * Este módulo solo valida códigos pertenecientes al CodeSystem LOINC.
        */
        return false;
    }

    @Override
    public IBaseResource fetchCodeSystem(String system) {
        if (!LOINC_SYSTEM.equals(system)) {
            return null;
        }

    return new CodeSystem()
        .setUrl(LOINC_SYSTEM)
        .setName("LOINC")
        .setStatus(Enumerations.PublicationStatus.ACTIVE)
        .setContent(Enumerations.CodeSystemContentMode.NOTPRESENT);
    }

    @Override
    public CodeValidationResult validateCode(
        ValidationSupportContext context,
        ConceptValidationOptions options,
        String system,
        String code,
        String display,
        String valueSetUrl
    ) {
        if (!LOINC_SYSTEM.equals(system)
            || !StringUtils.hasText(code)
            || StringUtils.hasText(valueSetUrl)) {
            return null;
        }

        Parameters input = new Parameters();

        input.addParameter()
            .setName("url")
            .setValue(new UriType(system));

        input.addParameter()
            .setName("code")
            .setValue(new org.hl7.fhir.r5.model.CodeType(code));

        if (StringUtils.hasText(display)) {
            input.addParameter()
                .setName("display")
                .setValue(new StringType(display));
        }

        return executeValidateCode(
            "CodeSystem",
            input,
            code,
            null
        );
    }

    // @Override
    // public CodeValidationResult validateCodeInValueSet(
    //     ValidationSupportContext context,
    //     ConceptValidationOptions options,
    //     String system,
    //     String code,
    //     String display,
    //     @Nonnull IBaseResource valueSet
    // ) {
    //     if (!LOINC_SYSTEM.equals(system)
    //         || !StringUtils.hasText(code)
    //         || !(valueSet instanceof ValueSet r5ValueSet)) {
    //         return null;
    //     }

    //     Parameters input = new Parameters();

    //     input.addParameter()
    //         .setName("valueSet")
    //         .setResource(r5ValueSet);

    //     input.addParameter()
    //         .setName("system")
    //         .setValue(new UriType(system));

    //     input.addParameter()
    //         .setName("code")
    //         .setValue(new org.hl7.fhir.r5.model.CodeType(code));

    //     if (StringUtils.hasText(display)) {
    //         input.addParameter()
    //             .setName("display")
    //             .setValue(new StringType(display));
    //     }

    //     return executeValidateCode(
    //         "ValueSet",
    //         input,
    //         code,
    //         r5ValueSet.getUrl()
    //     );
    // }

    @Override
    public LookupCodeResult lookupCode(
        ValidationSupportContext context,
        @Nonnull LookupCodeRequest request
    ) {
        String system = request.getSystem();
        String code = request.getCode();

        if (!LOINC_SYSTEM.equals(system) || !StringUtils.hasText(code)) {
            return null;
        }

        Parameters input = new Parameters();

        input.addParameter()
            .setName("system")
            .setValue(new UriType(system));

        input.addParameter()
            .setName("code")
            .setValue(new org.hl7.fhir.r5.model.CodeType(code));

        if (StringUtils.hasText(request.getDisplayLanguage())) {
            input.addParameter()
                .setName("displayLanguage")
                .setValue(
                    new org.hl7.fhir.r5.model.CodeType(
                        request.getDisplayLanguage()
                    )
                );
        }

        for (String property : request.getPropertyNames()) {
            input.addParameter()
                .setName("property")
                .setValue(new org.hl7.fhir.r5.model.CodeType(property));
        }

        try {
            Parameters output = (Parameters) client()
                .operation()
                .onType(CodeSystem.class)
                .named("$lookup")
                .withParameters(input)
                .execute();

            LookupCodeResult result = new LookupCodeResult()
                .setFound(true)
                .setSearchedForSystem(system)
                .setSearchedForCode(code);

            result.setCodeSystemDisplayName(
                stringParameter(output, "name")
            );
            result.setCodeSystemVersion(
                stringParameter(output, "version")
            );
            result.setCodeDisplay(
                stringParameter(output, "display")
            );

            Boolean abstractValue = booleanParameter(output, "abstract");
            result.setCodeIsAbstract(
                abstractValue != null && abstractValue
            );

            return result;

        } catch (RuntimeException exception) {
            return LookupCodeResult
                .notFound(system, code)
                .setErrorMessage(
                    "LOINC lookup failed: " + exception.getMessage()
                );
        }
    }

    private CodeValidationResult executeValidateCode(
        String resourceType,
        Parameters input,
        String code,
        String valueSetUrl
    ) {
        try {
            Parameters output;

            if ("ValueSet".equals(resourceType)) {
                output = (Parameters) client()
                    .operation()
                    .onType(ValueSet.class)
                    .named("$validate-code")
                    .withParameters(input)
                    .execute();
            } else {
                output = (Parameters) client()
                    .operation()
                    .onType(CodeSystem.class)
                    .named("$validate-code")
                    .withParameters(input)
                    .execute();
            }

            Boolean valid = booleanParameter(output, "result");
            String display = stringParameter(output, "display");
            String message = stringParameter(output, "message");

            CodeValidationResult result = new CodeValidationResult()
                .setDisplay(display)
                .setSourceDetails(baseUrl);

            if (Boolean.TRUE.equals(valid)) {
                result.setCode(code);
                return result;
            }

            String diagnostics = StringUtils.hasText(message)
                ? message
                : "LOINC code is not valid"
                    + (StringUtils.hasText(valueSetUrl)
                        ? " in ValueSet " + valueSetUrl
                        : "");

            result
                .setSeverity(IssueSeverity.ERROR)
                .setMessage(diagnostics)
                .addIssue(
                    new CodeValidationIssue(
                        diagnostics,
                        IssueSeverity.ERROR,
                        CodeValidationIssueCode.CODE_INVALID,
                        CodeValidationIssueCoding.INVALID_CODE
                    )
                );

            return result;

        } catch (RuntimeException exception) {
            String diagnostics =
                "LOINC terminology server request failed: "
                    + exception.getMessage();

            return new CodeValidationResult()
                .setSeverity(IssueSeverity.ERROR)
                .setMessage(diagnostics)
                .setSourceDetails(baseUrl)
                .addIssue(
                    new CodeValidationIssue(
                        diagnostics,
                        IssueSeverity.ERROR,
                        CodeValidationIssueCode.INVALID,
                        CodeValidationIssueCoding.INVALID_CODE
                    )
                );
        }
    }

    private IGenericClient client() {
        return myCtx.newRestfulGenericClient(baseUrl);
    }

    private static String stringParameter(
        Parameters parameters,
        String name
    ) {
        return parameters.getParameter().stream()
            .filter(parameter -> name.equals(parameter.getName()))
            .map(Parameters.ParametersParameterComponent::getValue)
            .filter(value -> value != null)
            .map(value -> value.primitiveValue())
            .findFirst()
            .orElse(null);
    }

    private static Boolean booleanParameter(
        Parameters parameters,
        String name
    ) {
        return parameters.getParameter().stream()
            .filter(parameter -> name.equals(parameter.getName()))
            .map(Parameters.ParametersParameterComponent::getValue)
            .filter(BooleanType.class::isInstance)
            .map(BooleanType.class::cast)
            .map(BooleanType::booleanValue)
            .findFirst()
            .orElse(null);
    }
}