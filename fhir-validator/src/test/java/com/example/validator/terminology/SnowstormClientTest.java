package com.example.validator.terminology;

import com.example.validator.terminology.SnowstormClient.ValidationStatus;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;

class SnowstormClientTest {

  private HttpServer server;

  @AfterEach
  void stopServer() {
    if (server != null) {
      server.stop(0);
    }
  }

  @Test
  void retriesTemporaryFailureAndCachesValidResult() throws Exception {
    AtomicInteger calls = new AtomicInteger();
    server = startServer(exchange -> {
      int call = calls.incrementAndGet();
      if (call == 1) {
        respond(exchange, 503, "service unavailable");
      } else {
        respond(exchange, 200, parametersResult(true));
      }
    });

    SnowstormClient client = clientForServer(3);

    assertEquals(ValidationStatus.VALID, client.validateSnomedCode("450743008"));
    assertEquals(2, calls.get());

    assertEquals(ValidationStatus.VALID, client.validateSnomedCode("450743008"));
    assertEquals(2, calls.get(), "VALID result should be served from cache");
  }

  @Test
  void explicitFalseIsInvalidAndCached() throws Exception {
    AtomicInteger calls = new AtomicInteger();
    server = startServer(exchange -> {
      calls.incrementAndGet();
      respond(exchange, 200, parametersResult(false));
    });

    SnowstormClient client = clientForServer(3);

    assertEquals(ValidationStatus.INVALID, client.validateSnomedCode("999999999"));
    assertEquals(ValidationStatus.INVALID, client.validateSnomedCode("999999999"));
    assertEquals(1, calls.get(), "Definitive INVALID result should be cached");
  }

  @Test
  void unavailableIsNotMisclassifiedAsInvalidOrCached() throws Exception {
    AtomicInteger calls = new AtomicInteger();
    server = startServer(exchange -> {
      calls.incrementAndGet();
      respond(exchange, 503, "service unavailable");
    });

    SnowstormClient client = clientForServer(3);

    assertEquals(ValidationStatus.UNAVAILABLE, client.validateSnomedCode("372756006"));
    assertEquals(3, calls.get());

    assertEquals(ValidationStatus.UNAVAILABLE, client.validateSnomedCode("372756006"));
    assertEquals(6, calls.get(), "UNAVAILABLE results must not be cached");
  }

  private SnowstormClient clientForServer(int attempts) {
    String base = "http://localhost:" + server.getAddress().getPort() + "/fhir";
    return new SnowstormClient(base, attempts, Duration.ofSeconds(2));
  }

  private HttpServer startServer(ExchangeHandler handler) throws IOException {
    HttpServer httpServer = HttpServer.create(new InetSocketAddress(0), 0);
    httpServer.createContext("/fhir/CodeSystem/$validate-code", exchange -> handler.handle(exchange));
    httpServer.start();
    return httpServer;
  }

  private static String parametersResult(boolean value) {
    return "{\"resourceType\":\"Parameters\",\"parameter\":[{\"name\":\"result\",\"valueBoolean\":" + value + "}]}";
  }

  private static void respond(HttpExchange exchange, int status, String body) throws IOException {
    byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
    exchange.getResponseHeaders().add("Content-Type", "application/fhir+json");
    exchange.sendResponseHeaders(status, bytes.length);
    exchange.getResponseBody().write(bytes);
    exchange.close();
  }

  @FunctionalInterface
  private interface ExchangeHandler {
    void handle(HttpExchange exchange) throws IOException;
  }
}
