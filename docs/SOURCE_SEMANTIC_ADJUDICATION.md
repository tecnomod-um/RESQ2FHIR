# Slovak source-to-RES-Q semantic adjudication (RQ1 / M2)

**Status:** Technical checks implemented; clinical adjudication and independent expert review **not yet performed**.

**Reference implementation:** `scripts/normalization/sk_registry.py`; independent aggregate audit: `scripts/evaluation/source_contract_audit.py`. These source-to-contract assertions complement but do not replace `scripts/evaluation/semantic_preservation_full.py`, which evaluates **normalized contract → serialized transaction FHIR**.

## SHM/RES-Q destination data-catalogue cross-check (user-supplied export; revision unverified)

An SHM `InpatientCase` and choice-model data-catalogue excerpt was supplied for review. It **documents destination-contract field meanings**, not the semantic definitions of the original 2024 Slovak source columns. Source-to-contract equivalence still needs original-source evidence.

| SHM field | Destination data-catalogue wording | Implication |
| --- | --- | --- |
| `prestroke_mrs` | “Value of modified Rankin Scale (mRS) prior of the stroke onset” | RES-Q target means **before stroke**, unequivocally; does **not** prove `STAV_M_RANKIN_2` has this 2024 source meaning. |
| `puncture_timestamp` | “date and time (or best estimate) of groin puncture in mechanical thrombectomy procedure” | RES-Q target means **actual groin puncture**; does **not** prove `DATUM_ENDO_V` is the same event. |
| `door_to_groin` | Reporting hospital first-door → groin puncture | This derived interval is sensitive to the ambiguous event interpretation. |
| `no_thrombolysis_reason` / reason ID 1 | “done elsewhere” | Confirms the **destination code** used to represent local non-performance; no evidence it serializes an external completed event. |
| `bolus_timestamp` | Date and time of IVT treatment | Destination contract has the field; remote IVT time remains unrepresented in the current generated local `Procedure`. |
| `door_to_needle` | First door of reporting hospital → application of IVT drug | Excluding external IVT from local D2N is justified by the destination definition. |

### **Critical data-catalogue discrepancy: mTICI 2A/2B descriptions**

The supplied SHM `MTiciScoreModel` rows state:

- ID 3, `2A`: “partial reperfusion > 50 % territory”
- ID 4, `2B`: “partial reperfusion <= 50 % territory”

These are **reversed relative to standard mTICI definitions** (2a <50%; 2b ≥50%) and relative to the actual `scripts/enum_models.py` `MTiciScore.TWO_A` / `TWO_B` displays (less-than-half versus more-than-half). See the American Heart Association's TICI grade abstraction definition: https://www.heart.org/-/media/Files/Professional/Quality-Improvement/Get-With-the-Guidelines/Get-With-The-Guidelines-Stroke/Workshops-and-Webinars/Get-With-The-Guidelines-Stroke-Mechanical-Endovascular-Reperfusion-Therapy-SLIDES-ucm_494077.pdf

**Do not swap the 2a/2b target codes or source mappings based solely on the supplied catalogue.** Obtain catalogue maintainer confirmation and correct the **catalogue metadata** if these are transposed descriptions. Otherwise, review the deployed code system and current clinical data separately. Do not call the clinical relation equivalent until adjudicated. The supplied excerpt provides no source-repository SHA, edition or timestamp; record provenance before treating it as controlled metadata.

## Authoritative original-source evidence — NCZI 2024 (reviewed)

**Source catalogue supplied by the user:** https://www.nczisk.sk/Documents/nzr/2024/doc_ZR_NEUR_CMP.html . The HTML could not be reliably fetched by the automated reader (legacy page encoding); the **official 2024 printable form and methodological instructions** were independently available and supply the actual clinical text below:

- 2024 form: https://www.nczisk.sk/Documents/nzr/2024/hlasenie_cievna_mozgova_prihoda.pdf
- 2024 methodological instructions: https://www.nczisk.sk/Documents/nzr/2024/MP_ZR_NEUR_CMP.pdf
- 2026 change notice **for version contrast only**: https://www.nczisk.sk/Documents/nzr/2026/zmena_ZR_NEUR_CMP.pdf

**Finding 1 — `STAV_M_RANKIN_2` is not demonstrably prestroke in 2024.** The 2024 form places “mRankin skóre (0–6)” under **“STAV PRI PRIJATÍ” (status on admission)**, next to admission NIHSS and blood pressure, with **no explicit “pre-stroke” qualifier**. The 2024 instructions likewise describe Module 04 as status at admission. The destination `prestroke_mrs` explicitly requires status **before stroke onset**. Further, the 2026 change notice retires `STAV_M_RANKIN_2` (end of 2025) and introduces **`M_RANKIN_PRED`** (from 2026), whose label explicitly means mRS *before* stroke. This reinforces the ambiguity but does not prove how clinicians operationally assessed the 2024 field. **Classification: unadjudicated; cannot be asserted equivalent.** If 2024 source means admission assessment, current FHIR `PRESTROKE` context is wrong.

**Finding 2 — `DATUM_ENDO_V` records start of thrombectomy, explicitly labelled “groin time”.** The 2024 form and instructions specify “Dátum a čas zahájenia trombektómie (\"groin time\")”, then reperfusion time. It is operationally close to a groin-puncture timestamp, but the source wording does not explicitly say *arterial puncture*; obtain clinical confirmation before declaring exact equivalence to the RES-Q destination field.

**Finding 3 — original TICI categories **are not semantically identical** to the mTICI target grades.** The 2024 source explicitly describes `02a` as incomplete distal filling of **<2/3 of the arterial territory**, versus RES-Q `mTICI 2a` as **<1/2**. It describes `02b` qualitatively as partial perfusion with slow filling of distal branches, whereas RES-Q `mTICI 2b` uses **>1/2**. Consequently, grade-label recoding `02a→2a` and `02b→2b` preserves textual labels **but not guaranteed clinical thresholds**. This is an **observed definition mismatch, not merely an untested possibility**. The 2026 change notice newly adds source `TICI=02c` and labels the updated variable “mTICI score after recanalization”; do **not** retrospectively apply 2026 rules to 2024.

**Finding 4 — source treatment and external context are explicit.** 2024 `NL_TROMBOLYZA`: `1` IVT in reporting hospital, `2` IVT at another hospital, `3` not administered; administration timestamp required for `1` and `2`. 2024 `ENDO_VYKON` (thrombectomy): `1` performed in reporting hospital, `2` performed elsewhere, `3` transferred for planned thrombectomy elsewhere, `9` not performed. This PR now retains the latter distinctions through `thrombectomy` (local flag) and `no_thrombectomy_reason` (done elsewhere / transferred elsewhere). **This still does not serialize a completed external MT event, external puncture/reperfusion time or TICI grade into FHIR** when the local flag is false.

**Additional source-to-contract issue uncovered:** `CT_MR_VYSETRENIE` explicitly permits `1` CT here, `2` CT elsewhere, `3` MR here, `4` MR elsewhere, `5` no CT/MR. The current adapter only derives the target `imaging_type` for `1`/`3` and leaves `imaging_done` null for `2`/`4`/`5`, losing an external location or explicit no-imaging assertion. This needs a **separate modeling fix and test suite** before comprehensive source-to-FHIR preservation can be claimed. The source-to-contract audit flags these cases.

## Source evidence and version boundary

Use the **2024** `ZR_NEUR_CMP` form/code list, not later forms as a substitute for the evaluated export. Consult the Slovak registry clinical/metadata custodian when the form or code list does not define a clinical time point or a procedural event unambiguously.

- NCZI 2024 stroke form: https://www.nczisk.sk/Documents/nzr/2024/hlasenie_cievna_mozgova_prihoda.pdf
- NCZI registry metadata (cross-check only; definitions may change between form years): https://nczisk.sk/Documents/nzr/2025/doc_ZR_NEUR_CMP.html
- FHIR R5 `Procedure.statusReason`: https://hl7.org/fhir/R5/procedure-definitions.html#Procedure.statusReason

The 2024 form distinguishes thrombolysis administered at the reporting hospital (1), at another hospital (2), and not administered (3). The time of administration is requested for both 1 and 2.

## Adjudication matrix

| Original source | Current adapter and output | Technical evidence | Clinical question / adjudication status |
| --- | --- | --- | --- |
| `STAV_M_RANKIN_2` | `prestroke_mrs`, then Observation with `PRESTROKE` context | 2024 form places mRS under admission-status module without explicit prestroke qualifier; 2026 replaces it with explicit `M_RANKIN_PRED` | **SOURCE–TARGET MISMATCH RISK.** Do not classify as equivalent without 2024 source-owner confirmation. |
| `DATUM_ENDO_V` | `puncture_timestamp`; derives `door_to_groin` | The 2024 source explicitly says start of thrombectomy (“groin time”), while RES-Q demands groin puncture | **STRONG PROXY; NOT FORMALLY CONFIRMED.** Verify that this specific start event equals arterial puncture. |
| `TICI` | `mtici_score` | Source 2a is <2/3 of territory; destination 2a is <1/2. Source 2b is qualitative; destination 2b >1/2. | **DEFINITION MISMATCH CONFIRMED.** Code-label preserving mapping is **not exact semantic equivalence** for grades 2a/2b. |
| `NL_TROMBOLYZA=2` | `thrombolysis=False` (not performed **here**) + `no_thrombolysis_reason=1` (`DONE_ELSEWHERE`) | 2024 source code 2 explicitly denotes IVT elsewhere; correction retains reporting-hospital semantics | **PARTIAL.** The external completed event and timestamp are still absent from FHIR; not proof of whole-patient non-treatment. |\n| `ENDO_VYKON=2/3/9` | `thrombectomy=False` locally plus reason `1` for performed elsewhere or `8` for transferred/planned; code 9 means not done | 2024 source explicitly distinguishes local/external/planned/not performed; covered by new tests | **PARTIAL.** External completed event, clinical grade and timestamp are not fully represented in FHIR. |\n| `CT_MR_VYSETRENIE=2/4/5` | Current normalization loses external CT/MR and explicit no imaging | 2024 form explicitly lists these three source categories | **OPEN CODE DEFECT.** Separate modeling and regression tests needed. |

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
