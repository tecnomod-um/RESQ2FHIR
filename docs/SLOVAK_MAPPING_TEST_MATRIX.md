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
- The generic adapter's labelled enums and known numeric-ID coercion defect.
- Downstream FHIR R5 regression tests for NIHSS admission/discharge context and `Encounter.actualPeriod`.
- Six controlled tests of semantic read-back (three original comparator checks; mutations of age, NIHSS value, NIHSS assessment context, and external IVT reason) without making unmeasured FHIR validation sensitivity claims.

The source mapping defines **71 CSV input aliases** and **81 normalized output fields**. This code inventory must not be equated with the **70 clinically agreed variables** reported in the paper; they require a separate reconciliation against Supplementary Table S1.

## Expected failures and acceptance criteria

`unittest.expectedFailure` marks the following currently unresolved behavior. **An expected failure does not count as a successful mapping**; convert each to a normal passing test only after fixing and documenting its semantics.

| ID | Known gap | Acceptance criterion |
|---|---|---|
| G01 | CT + CTA + perfusion overwritten to CT + CTA | Preserve all provided imaging modalities |
| G02 | MR + MRA + perfusion overwritten to MR + MRA | Preserve all provided imaging modalities |
| G03 | CT/MR performed elsewhere not represented | Preserve explicit external imaging location/status |
| G04 | Explicit no imaging becomes unknown | Explicit no-imaging state retained |
| G05 | Missing inputs can yield false aggregate flags | Agree three-valued semantics; unknown ≠ negative |
| G06 | Onset date with unknown time becomes midnight | Preserve time precision/unknown time |
| G07 | TIA history and ischemic stroke history conflated | Retain separate source distinctions or document deliberate generalization |
| G08 | Generic numeric enum string `'1'` becomes `True` | Field-aware enum before Boolean coercion |

Additional *clinical* open items are **not test failures**: `STAV_M_RANKIN_2` timepoint, `DATUM_ENDO_V` groin-time meaning, the threshold mismatch between 2024 TICI and RES-Q mTICI 2a/2b, historical external IVT/MT events, family-history interpretation of `RA_CMP`, and multi-flag no-treatment reasons. These need source-owner/clinician decisions, not assertions based only on code.

**Important correction to previous off-repository review:** The current `main` FHIR builder already retains NIHSS numerical values and assigns `Encounter.actualPeriod`. New tests guard these **resolved** cases. Do not report them as current defects.

## Execution

```bash
pip install -r requirements.txt
python -m unittest discover -s tests/evaluation -p 'test_*.py' -v
python -m unittest tests.fhir_resources.test_slovak_regressions tests.fhir_resources.test_slovak_observation_context -v
```

The evaluation GitHub Actions workflow is updated to include these modules on a PR. No patient-level values are placed in fixtures or output.

An initial **local** check against user-uploaded adapter copies produced 21 source-specific test methods (14 passed, 7 expected failures) and 5 generic-adapter methods (4 passed, 1 expected failure). The generic local check substituted a minimal FHIR `Coding` import stub; full FHIR validation was **not** run locally. The GitHub CI result on the repository's own code is the authoritative execution. `unittest` method counts exclude additional `subTest` trials and must not be used as clinical accuracy denominators.

## Scientific reporting protocol

For claims in BMC, freeze and report the exact adapter SHA, converter SHA, RES-Q IG package/version, terminology server/code-system releases, generated cases/seed, test runner version and CI run ID. Run the same fixtures through the **complete** chain (original source → contract → transaction/document FHIR → validation and semantic read-back), then audit source→target mappings by independent experts. Keep conformance rates, contract-value read-back, source-level preservation and clinically adjudicated equivalence as **separate endpoints**. Never replace prior 60,366/60,366 or 4,131/4,131 figures without a versioned rerun and new denominators.

**Limits:** These tests systematically enumerate the supported individual source codebooks but **do not exhaustively enumerate all cross-variable combinations** or evaluate the destination RES-Q Registry ingestion.
