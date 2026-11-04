# Transformation evaluation

This repository includes an aggregate evaluation layer for the Slovak registry use case.
It is designed for technical/scientific evaluation without exporting patient-level values.

## What is measured

### 1. Resource counts

`scripts.evaluation.resource_counts` reports:

- Bundle counts separated into `transaction`, `document`, and other types.
- Total FHIR resources by Bundle type.
- Counts by `resourceType`.
- Mean resources per transaction Bundle.

Transaction and document Bundles are deliberately separated because document Bundles may repeat references/resources and would otherwise inflate the resource counts reported for the source-to-FHIR transformation.

### 2. Semantic preservation

`scripts.evaluation.semantic_preservation` compares populated values in the normalized CSV with the corresponding serialized FHIR representation.

The comparison is deterministic and field-specific. It checks the expected resource/profile, FHIR element, code, extension, assessment context, status, or timestamp instead of searching for the same literal value anywhere in the Bundle.

Supported checks currently cover core demographics, encounter information, stroke diagnosis, NIHSS/mRS, blood pressure, imaging, thrombolysis, thrombectomy, mTICI, atrial fibrillation/flutter, swallowing screening, timing metrics, major risk factors, prior medications, discharge medications, selected stroke etiologies, and selected hemorrhagic causes.

The report contains only aggregate counts:

```json
{
  "comparableSourceValues": 100,
  "matchedValues": 99,
  "mismatchedValues": 1,
  "preservationRate": 0.99,
  "byField": {
    "age": {
      "comparable": 10,
      "matched": 10,
      "mismatched": 0,
      "preservationRate": 1.0
    }
  }
}
```

No source or target patient values are written to the report.

A source value is included in the denominator only when:

1. the source value is populated;
2. a deterministic field-specific comparator has been implemented; and
3. the target semantics are explicitly representable in the current FHIR model.

Positive-only concepts (for example, individual stroke-etiology flags represented as one selected coded extension) are compared only when the source flag is `true`. This avoids treating absence of a code as an explicit representation of `false` when the FHIR model does not encode that distinction.

## Run the evaluation

After normalization and conversion:

```bash
python -m scripts.evaluation.evaluate \
  --csv workdir/jobs/<job_id>/normalized/normalized.csv \
  --bundles workdir/jobs/<job_id>/bundles \
  --out workdir/jobs/<job_id>/evaluation.json
```

The report contains two top-level sections:

- `resourceCounts`
- `semanticPreservation`


## 3. Slovak source-to-contract technical checks (RQ1/M2)

The **separate** `scripts.evaluation.source_contract_audit` verifies selected
original Slovak field values against the normalized contract, rather than only
checking normalized values against FHIR. It covers the numeric mRS copy,
endovascular timestamp copy, TICI grade recoding and the reporting-hospital
thrombolysis status/elsewhere reason. It flags externally administered bolus
timestamps whose original value is not evaluated in FHIR.

Run (with the **same row order** and the 2024 source schema):

```bash
python -m scripts.evaluation.source_contract_audit \
  --source <slovak_source.csv> \
  --normalized <normalized.csv> \
  --out <source_contract_audit.json>
```

This report is aggregate-only; it never serializes patient-level values. It is
**not a clinical adjudication**: correctness of the original mRS timepoint, the
puncture-time interpretation and the TICI/mTICI conceptual correspondence still
requires independent source/expert review. See
[`SOURCE_SEMANTIC_ADJUDICATION.md`](SOURCE_SEMANTIC_ADJUDICATION.md) and the
unfilled [expert audit template](source_to_fhir_expert_audit_template.csv).

**Important current limitation:** `NL_TROMBOLYZA=2` indicates that treatment
was performed at another hospital. The existing RES-Q contract records local
non-administration plus coded `DONE_ELSEWHERE` and preserves the source bolus
timestamp in the normalized CSV. The current FHIR builder does not serialize
this external bolus timestamp. Therefore the combined pipeline does **not**
yet demonstrate complete source-to-FHIR preservation for that specific event.
Do not update previous evaluation totals without a versioned rerun.

## Scientific interpretation

FHIR profile validation and semantic preservation are separate outcomes.

- **Conformance** answers whether the generated resources satisfy FHIR R5, the RES-Q Implementation Guide, and terminology constraints.
- **Semantic preservation** answers whether comparable source values are represented in the expected FHIR structures with the expected meaning.

A Bundle may be syntactically/profile-valid while still encoding an incorrect value or concept, so both dimensions should be reported independently.

## Tests

The evaluation layer uses synthetic fixtures only.

```bash
python -m unittest discover -s tests/evaluation -p 'test_*.py'
```

The tests verify that transaction/document resource counts are separated and that the semantic evaluator can both confirm a correct transformation and detect an intentionally introduced value mismatch.
