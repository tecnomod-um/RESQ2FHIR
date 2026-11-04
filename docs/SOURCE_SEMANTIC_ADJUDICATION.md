# Slovak source-to-RES-Q semantic adjudication (RQ1 / M2)

**Status:** Technical checks implemented; clinical adjudication and independent expert review **not yet performed**.

**Reference implementation:** `scripts/normalization/sk_registry.py`; independent aggregate audit: `scripts/evaluation/source_contract_audit.py`. These source-to-contract assertions complement but do not replace `scripts/evaluation/semantic_preservation_full.py`, which evaluates **normalized contract → serialized transaction FHIR**.

## Source evidence and version boundary

Use the **2024** `ZR_NEUR_CMP` form/code list, not later forms as a substitute for the evaluated export. Consult the Slovak registry clinical/metadata custodian when the form or code list does not define a clinical time point or a procedural event unambiguously.

- NCZI 2024 stroke form: https://www.nczisk.sk/Documents/nzr/2024/hlasenie_cievna_mozgova_prihoda.pdf
- NCZI registry metadata (cross-check only; definitions may change between form years): https://nczisk.sk/Documents/nzr/2025/doc_ZR_NEUR_CMP.html
- FHIR R5 `Procedure.statusReason`: https://hl7.org/fhir/R5/procedure-definitions.html#Procedure.statusReason

The 2024 form distinguishes thrombolysis administered at the reporting hospital (1), at another hospital (2), and not administered (3). The time of administration is requested for both 1 and 2.

## Adjudication matrix

| Original source | Current adapter and output | Technical evidence | Clinical question / adjudication status |
| --- | --- | --- | --- |
| `STAV_M_RANKIN_2` | `prestroke_mrs`, then mRS Observation with `PRESTROKE` assessment context | Grade is copied as a number and checked downstream against the **assumed** context | **OPEN.** Is the 2024 assessment explicitly *before index stroke* or *on hospital admission*? Do not claim exact equivalence without source-custodian confirmation. |
| `DATUM_ENDO_V` | `puncture_timestamp`; also derives `door_to_groin` | The original form uses start of thrombectomy / “groin time”; technical timestamps are preserved | **OPEN.** Does “groin time” operationally mean arterial puncture, not e.g. arrival in angiography suite or endovascular procedure start? If not, change timing semantics and derived measure. |
| `TICI` | `mtici_score` | See grade-level table below | **OPEN for clinical equivalence.** Numeric grade preservation is not proof that original TICI and mTICI thresholds are identical. |
| `NL_TROMBOLYZA=2` | `thrombolysis=False` (not performed **here**) + `no_thrombolysis_reason=1` (`DONE_ELSEWHERE`) | Current RES-Q target contract can encode local `not-done` with `statusReason=done-elsewhere`. Correction and regression tests are on this PR branch. | **PARTIAL.** This is a reporting-centre representation, *not* a claim that the patient was untreated. The source bolus timestamp is kept in the normalized contract but the current FHIR builder does **not** serialize it for external treatment. A richer external-event representation requires separate IG/clinical decision. |

### TICI mapping (implementation-level, not formal equivalence)

| 2024 source code | Reported TICI grade | RES-Q enum ID | RES-Q mTICI grade | Assessment |
| --- | --- | --- | --- | --- |
| `000` | 0 | `1` | 0 | Grade label maintained; scale equivalence unconfirmed |
| `010` | 1 | `2` | 1 | Same |
| `02a` | 2a | `3` | 2a | TICI/mTICI grade-definition review needed |
| `02b` | 2b | `4` | 2b | TICI/mTICI grade-definition review needed |
| `030` | 3 | `6` | 3 | Grade label maintained; scale equivalence unconfirmed |
| `090` | Unknown | no mapped grade | no mapped grade | Correctly do not invent a grade |
| none | — | `5` | 2c | Target-specific grade absent in evaluated source code list |

The recoding neither creates a source 2c grade nor demonstrates that source 2b implies the same reperfusion threshold as mTICI 2b. Record any loss of clinical granularity after source-custodian review.

### Thrombolysis performed elsewhere: scope and limitations

- Source `1` → locally performed `thrombolysis=True`; local `door_to_needle` may be derived when timestamps exist.
- Source `2` → `thrombolysis=False` for **this reporting hospital**, plus `no_thrombolysis_reason=1` (`DONE_ELSEWHERE`). The current FHIR builder emits a locally `not-done` `Procedure` with an explicit `statusReason` indicating the event was performed elsewhere. This is a *local non-performance* statement. It is **not** a completed external treatment event and should not be construed as global absence of treatment.
- Source `3` → no trombolysis administered; retain true non-administration reason if known.
- For source `2`, do **not** calculate a reporting-hospital `door_to_needle` metric from the remote bolus timestamp.
- The remote `NL_DATUM_TROMBOLYZA` is **retained in `bolus_timestamp`** in the normalized contract, but is **not currently represented on the emitted FHIR `Procedure`**. This field is deliberately excluded by the existing normalized→FHIR comparator when `thrombolysis=False`. Therefore **do not claim complete source-to-FHIR preservation of external IVT timestamps**.
- Where source fields conflict (e.g. elsewhere plus no-treatment reason), the normalizer logs a warning and prioritizes the explicit elsewhere code. These cases require human review.

**Design question for the IG maintainers:** Is a second `Procedure.status=completed` representing the historical remote thrombolysis event appropriate, and what evidence for remote performer/organization and the event time is available? Resolve before implementing an external event or its provenance; do not misuse `statusReason` on `completed` as if it were a performer/location.

## Run reproducible aggregate source-to-contract checks

```bash
python -m scripts.normalization.sk_registry \
  --input <2024_slovak_registry_export.csv> \
  --output <normalized.csv>

python -m scripts.evaluation.source_contract_audit \
  --source <2024_slovak_registry_export.csv> \
  --normalized <normalized.csv> \
  --out <source_contract_audit.json>

python -m scripts.evaluation.evaluate \
  --csv <normalized.csv> \
  --bundles <transaction_bundle_directory> \
  --out <fhir_evaluation.json>
```

The first source-to-contract report performs technical assertions about selected codes/values and outputs only aggregate counts and scenario flags, not source values. The separate FHIR evaluation covers the normalized contract-to-transaction-Bundle stage. The two reports cannot establish the **clinical validity** of source variable interpretations.

If using synthetic cases, explicitly record the generator version, seed, input case-selection method, and version SHA of converter/evaluator. The previously published development-run numbers are **not** automatically updated by this PR.

## Expert audit protocol (not yet executed)

Select a **reasoned sample of at least 15 synthetic source→contract→FHIR transformations** and stratify across direct, coded, conditional, temporal, and the four contested mappings. Use `docs/source_to_fhir_expert_audit_template.csv` as an **unfilled review template**, not as evidence that review happened.

1. Freeze the source schema/code-list edition, converter commit, IG package and evaluator revisions before selecting cases.
2. Select 3 direct, 3 coded, 3 conditional, 3 temporal and 3 ambiguity-focused transformations, including at least one `NL_TROMBOLYZA=2`, one `TICI=02b`, one mRS time-point question and one `DATUM_ENDO_V` case. A case can contain several mappings; record the selection logic without clinical identifiers.
3. The independent clinician/terminologist reviews actual *synthetic* source value, normalized field/value, generated FHIR resource, code/system/profile/assessment context and temporal interpretation. Record **correct**, **incorrect**, or **needs clarification** for each chain. Reviewer/date and rationale must be explicit.
4. Resolve disagreements by documented consensus with the Slovak source owner; version changes and re-run both stages and generation-side FHIR/IG validation.
5. Report actual numbers reviewed, disagreements and unresolved mappings in the manuscript. Do not report success or inter-rater agreement without observed data.

## ConceptMap relationship counts: deferred until adjudication

Only apply FHIR R5 `ConceptMap.relationship` to clinically meaningful **coded source-value ↔ target-concept pairs**. Possible values include `equivalent`, `source-is-narrower-than-target`, `source-is-broader-than-target`, `related-to`, and `not-related-to`.

- **Unit of analysis:** distinct adjudicated source-code→target-code pairs, not the 70 input variable names and not FHIR resource instances.
- Distinguish exact equivalence from same-number-but-different-clinical-scale mapping (TICI→mTICI).
- Separately document temporal and procedural-context mappings which are not necessarily `ConceptMap` entries.
- Until the clinical questions above are resolved, do not publish aggregate relationship counts or mark all source variables equivalent.

### Formal outstanding confirmations

- [ ] Slovak clinician/data steward: intended 2024 time point of `STAV_M_RANKIN_2`.
- [ ] Slovak procedural expert: `DATUM_ENDO_V` = arterial puncture vs procedure-start timestamp.
- [ ] Neurointerventional/terminology expert: TICI↔mTICI grade-level relation and any information loss.
- [ ] FHIR IG owner: modeling of **completed external thrombolysis** with real bolus time/performer.
- [ ] Independent expert(s): execute and sign off the 15-item sample review.
- [ ] After fixes: rerun versioned synthetic development and held-out evaluations, including source→contract and contract→FHIR stages, before changing paper claims.
