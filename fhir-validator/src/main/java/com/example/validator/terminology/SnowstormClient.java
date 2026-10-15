package com.example.validator.terminology;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/**
 * Small HTTP client for validating SNOMED CT codes against Snowstorm.
 *
 * <p>The client distinguishes a definitive terminology answer from a technical
 * failure. A code is INVALID only when Snowstorm successfully returns an
 * explicit FHIR $validate-code result=false. Network failures, timeouts,
 * malformed responses and non-2xx HTTP responses are UNAVAILABLE instead of
 * being misclassified as invalid clinical codes.</p>
 *
 * <p>Successful VALID/INVALID results are cached for the lifetime of the
 * application so repeated codings do not generate thousands of identical
 * terminology requests during large registry validation jobs.</p>
 */
@Component
public class SnowstormClient {

  public enum ValidationStatus {
    VALID,
    INVALID,
    UNAVAILABLE
  }

  private static final Logger log = LoggerFactory.getLogger(SnowstormClient.class);
  private static final ObjectMapper JSON = new ObjectMapper();
  private static final Duration DEFAULT_TIMEOUT = Duration.ofSeconds(5);
  private static final int DEFAULT_MAX_ATTEMPTS = 3;

  @Value("${app.fhir.snowstorm.baseUrl:http://snowstorm:8080/fhir}")
  private String base;

  @Value("${app.fhir.snowstorm.branch:MAIN}")
  private String branch;

  private final HttpClient http;
  private final int maxAttempts;
  private final Duration requestTimeout;
  private final ConcurrentMap<String, ValidationStatus> validationCache = new ConcurrentHashMap<>();

  public SnowstormClient() {
    this(
        HttpClient.newBuilder().connectTimeout(DEFAULT_TIMEOUT).build(),
        DEFAULT_MAX_ATTEMPTS,
        DEFAULT_TIMEOUT
    );
  }

  SnowstormClient(HttpClient http, int maxAttempts, Duration requestTimeout) {
    this.http = http;
    this.maxAttempts = Math.max(1, maxAttempts);
    this.requestTimeout = requestTimeout;
  }

  SnowstormClient(String base, int maxAttempts, Duration requestTimeout) {
    this(
        HttpClient.newBuilder().connectTimeout(requestTimeout).build(),
        maxAttempts,
        requestTimeout
    );
    this.base = base;
  }

  /**
   * Validate one SNOMED CT code using Snowstorm's FHIR $validate-code operation.
   *
   * @return VALID when Snowstorm explicitly returns result=true, INVALID when
   *         it explicitly returns result=false, or UNAVAILABLE when a reliable
   *         terminology answer cannot be obtained after retries.
   */
  public ValidationStatus validateSnomedCode(String code) {
    ValidationStatus cached = validationCache.get(code);
    if (cached != null) {
      return cached;
    }

    ValidationStatus result = ValidationStatus.UNAVAILABLE;
    for (int attempt = 1; attempt <= maxAttempts; attempt++) {
      result = validateSnomedCodeOnce(code);
      if (result != ValidationStatus.UNAVAILABLE) {
        validationCache.putIfAbsent(code, result);
        return result;
      }
      if (attempt < maxAttempts) {
        log.debug("Retrying Snowstorm validation for {} (attempt {}/{})", code, attempt + 1, maxAttempts);
      }
    }

    log.warn("Snowstorm validation unavailable for {} after {} attempts", code, maxAttempts);
    return result;
  }

  private ValidationStatus validateSnomedCodeOnce(String code) {
    try {
      String fhirBase = base.replaceAll("/+$", "");
      if (!fhirBase.endsWith("/fhir")) {
        fhirBase = fhirBase + "/fhir";
      }
      String endpoint = fhirBase + "/CodeSystem/$validate-code";

      String body = """
        {
          "resourceType":"Parameters",
          "parameter":[
            {"name":"url","valueUri":"http://snomed.info/sct"},
            {"name":"code","valueCode":"%s"}
          ]
        }
      """.formatted(code);

      HttpRequest req = HttpRequest.newBuilder()
          .uri(URI.create(endpoint))
          .timeout(requestTimeout)
          .header("Content-Type", "application/fhir+json")
          .header("Accept", "application/fhir+json")
          .POST(HttpRequest.BodyPublishers.ofString(body))
          .build();

      log.debug("Snowstorm $validate-code -> {}", endpoint);
      HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
      log.debug("Snowstorm $validate-code status={} body={}", resp.statusCode(), resp.body());

      if (resp.statusCode() / 100 != 2) {
        log.warn("Snowstorm returned HTTP {} while validating {}", resp.statusCode(), code);
        return ValidationStatus.UNAVAILABLE;
      }

      JsonNode response = JSON.readTree(resp.body());
      for (JsonNode parameter : response.path("parameter")) {
        if ("result".equals(parameter.path("name").asText()) && parameter.has("valueBoolean")) {
          return parameter.path("valueBoolean").asBoolean()
              ? ValidationStatus.VALID
              : ValidationStatus.INVALID;
        }
      }

      log.warn("Snowstorm returned no explicit result parameter while validating {}", code);
      return ValidationStatus.UNAVAILABLE;
    } catch (Exception e) {
      log.warn("Snowstorm $validate-code failed for {}: {}", code, e.toString());
      return ValidationStatus.UNAVAILABLE;
    }
  }

  /**
   * Alternate existence check using Snowstorm's native browser API.
   */
  public boolean conceptExistsNative(String code) {
    try {
      String rootBase = base.replaceAll("/+$", "");
      if (rootBase.endsWith("/fhir")) {
        rootBase = rootBase.substring(0, rootBase.length() - "/fhir".length());
      }
      String url = rootBase + "/browser/" + branch + "/concepts/" + code;

      HttpRequest req = HttpRequest.newBuilder()
          .uri(URI.create(url))
          .timeout(requestTimeout)
          .GET()
          .build();

      log.debug("Snowstorm native check -> {}", url);
      HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());

      return resp.statusCode() == 200 && resp.body().contains("\"active\":true");
    } catch (Exception e) {
      log.warn("Snowstorm native check failed for {}: {}", code, e.toString());
      return false;
    }
  }
}
