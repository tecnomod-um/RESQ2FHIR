# 2024 Slovak → RES-Q: executable mapping verification matrix

**Evidence status:** Technical baseline using synthetic cases; **not** clinical adjudication, independent held-out evaluation, or full source-to-FHIR preservation proof. Source catalogue and unresolved expert questions are described in [SOURCE_SEMANTIC_ADJUDICATION.md](SOURCE_SEMANTIC_ADJUDICATION.md).

## What is tested

The 2024 NCZI source adapter (`scripts/normalization/sk_registry.py`) and the generic labelled-CSV adapter (`scripts/normalization/slovak.py`) are **alternative normalization entry points**, not evidence of two sequential normalization stages.

- All **71 configured source columns** exercised individually and **45 syntactic combinations** (5 source imaging statuses × 3 CTA states × 3 perfusion states); these are execution/smoke tests, not proof of correct source semantics.
- Every code in **13 explicit original-source mapping tables**: **48 code-to-target entries**.
- Every code `1`, `2`, `3` and missing for **24 directly mapped Boolean source columns**: **96 individual source-state trials**. This confirms *implementation*; the semantic definition of `3` must still be independently checked per NCZI field.
- Three IVT administration states and four local/external/planned/none mechanical thrombectomy states, including corresponding RES-Q reason codes.
- Prior anticoagulant code variants, eight discharge-medication flags, aggregate medication indicators, five ischemic-etiology categories and seven hemorrhage-cause codes.
- Six local imaging combinations; timestamps, local versus external door-to-needle, mRS parsing, treatment reason precedence and invalid source codes.
- The generic adapter's labelled enums and repaired numeric-ID handling.
- Downstream FHIR R5 regression tests for NIHSS admission/discharge context and `Encounter.actualPeriod`.
- Six controlled tests of semantic read-back (three original comparator checks; mutations of age, NIHSS value, NIHSS assessment context, and external IVT reason) without making unmeasured FHIR validation sensitivity claims.

The source mapping defines **71 CSV input aliases** and **81 normalized output fields**. The source `OA_TIA` and `OA_ISCHEMICKA_CMP` intentionally populate one RES-Q `risk_previous_ischemic_stroke` indicator by three-valued OR. They are distinct source diagnoses, but their aggregation is a **registry-contract modeling decision**, not a claim of clinical or SNOMED equivalence. This code inventory must not be equated with the **70 clinically agreed variables** reported in the paper; they require a separate reconciliation against Supplementary Table S1.

## Remediation results and boundaries

The eight formerly expected failures have been converted to executable, ordinary assertions. On this branch:

| ID | Implemented | Interpretation |
|---|---|---|
| G01 | CT + CTA + perfusion selects target composite CT/CTA/perfusion code | Preserves combination at available target category granularity |
| G02 | MR + MRA + perfusion selects target composite MR/MRA/perfusion code | Preserves combination at available target category granularity |
| G03 | Source CT/MR elsewhere maps to `imaging_done=3`, retaining CT/MR subtype | FHIR Procedure records **not performed at reporting hospital** with `DONE_ELSEWHERE`; historical completed remote event/performer is **not** fully encoded |
| G04 | Explicit no CT/MR maps to `imaging_done=2`, without inventing CT or MR | Emits not-done generic brain imaging Procedure, using local `brain-imaging-unspecified` code **pending IG terminology approval** |
| G05 | Derived OR uses three-valued semantics | Known true / known all-false / otherwise unknown |
| G06 | Date-only source onset remains `YYYY-MM-DD` | FHIR R5 `Condition.onsetDateTime` preserves partial precision; read-back rejects fabricated midnight |
| G07 | TIA and prior ischemic stroke source flags intentionally combined for RES-Q | `risk_previous_ischemic_stroke = OR3(OA_TIA, OA_ISCHEMICKA_CMP)` with no extra `risk_tia` output column. Original input columns remain in the source CSV; this is **intentional many-to-one aggregation**, not lossless recovery of which diagnosis occurred. The existing FHIR risk-factor code represents TIA specifically and remains subject to terminology review. |
| G08 | Enum IDs are processed before generic Boolean coercion | String IDs remain categorical values, including at normalized CSV converter input |

The technical tests above are **not** a claim that all 70 clinically selected source variables are clinically equivalent to their RES-Q representations. In particular, unresolved clinical/IG questions include `STAV_M_RANKIN_2` timepoint, `DATUM_ENDO_V` groin-time interpretation, 2024 TICI versus mTICI 2a/2b definitions, `RA_CMP` family history versus personal stroke history, and external IVT/MT completed procedures and timestamps. The generic local brain-imaging code must be reviewed against the current IG/ValueSets before claiming profile validation.

**Baseline reference:** The current default-branch implementation already correctly retains NIHSS numeric values and `Encounter.actualPeriod`; the regression tests guard those existing behaviors. Historical paper metrics must not be modified without a versioned repeat.

## Execution

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests/evaluation -p 'test_*.py' -v
python -m unittest tests.fhir_resources.test_slovak_regressions tests.fhir_resources.test_slovak_observation_context tests.fhir_resources.test_slovak_imaging_and_time tests.fhir_resources.test_slovak_pipeline_smoke -v
```

For actual end-to-end confirmation, run a version-frozen synthetic NCZI source CSV through `sk_registry`, `transform.py`, the `source_contract_audit`, `evaluate`, and the IG validator. The pipeline has not been revalidated here against the complete IG. Test methods and subtests are not source-level clinical-accuracy denominators. All fixtures are synthetic, with no patient-identifying data.

## Scientific reporting protocol

For claims in BMC, freeze and report the exact adapter SHA, converter SHA, RES-Q IG package/version, terminology server/code-system releases, generated cases/seed, test runner version and CI run ID. Run the same fixtures through the **complete** chain (original source → contract → transaction/document FHIR → validation and semantic read-back), then audit source→target mappings by independent experts. Keep conformance rates, contract-value read-back, source-level preservation and clinically adjudicated equivalence as **separate endpoints**. Never replace prior 60,366/60,366 or 4,131/4,131 figures without a versioned rerun and new denominators.

**Limits:** These tests systematically enumerate the supported individual source codebooks but **do not exhaustively enumerate all cross-variable combinations** or evaluate the destination RES-Q Registry ingestion.
