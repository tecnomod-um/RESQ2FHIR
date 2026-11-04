# Slovak 2024 historical-incident closure checks

**Source/version boundary:** NCZI `ZR_NEUR_CMP` 2024 only. These checks are about the historical integration incidents recorded with Slovak developers, not the separate unresolved source mRS or TICI clinical-equivalence questions. All regression cases are synthetic. No patient data or new manuscript metrics have been produced.

## Implemented in this branch (pending merge)

| Area | Previous failure mode | Current change and verification | Status |
| --- | --- | --- | --- |
| Anticoagulant source codes | The same `OA_ANTIKOAGULANCIA` categorical code may arrive as `01`/`1` or `06`/`6`, especially when parsed numerically. | Canonicalize **this field only**, retaining `01`/1 as warfarin and `06`/6 as DOAC; preserve original TICI mapping unchanged. Synthetic tests include string, integer and floating-point representations. | Code correction and tests prepared |
| DOAC before stroke | A derived `before_onset_doak` flag existed but was absent from the emitted normalized contract. | Export that flag, represent a **DOAC class** as a `MedicationStatement`, and check positive FHIR round-trip. Suppress duplicate generic anticoagulant statement when a specific DOAC class is recorded. | Code correction and tests prepared; terminology IG dependency below |
| DOAC at discharge | `discharge_doak` contributed to aggregate anticoagulation but was discarded from normalized contract. | Preserve the specific class through `discharge_doak`, serialize an explicit medication category `MedicationRequest`, and avoid a duplicate generic anticoagulant order. | Code correction and tests prepared; terminology IG dependency below |
| Antidepressant at discharge | `UKON_ANTIDEPRESIVA` was merged into `discharge_other`, losing the category. | Export `discharge_antidepressants` and represent with SNOMED CT **372720008 Antidepressant (substance)**, retaining `discharge_other` solely for the original other/nootropic group. | Code correction and tests prepared; IG ValueSet dependency below |
| Blood pressure with one component | The transaction builder required **both** systolic and diastolic components. | Permit either known component; the existing Observation builder supports independent components, and the version supplied for the FHIR IG defines `component 0..*` with no two-component minimum. | Code correction and regression prepared |
| `FALSE` vs `UNKNOWN` | Positive/negative/unknown values could be conflated. | Tests cover tri-state `get_risk_factors` → `Condition.clinicalStatus` and `get_before_onset_medications` → `MedicationStatement.adherence.code`; negative/missing discharge flags must not generate a **positive** `MedicationRequest`. | Existing policy checked in synthetic test; clinical policy is **not** inferred from code alone |
| `risk_smoker` | SHM model includes `risk_smoker`, but 2024 NCZI source adapter only exports `risk_smoker_last_10_years`. | Explicit optional SHM-contract `risk_smoker` is passed to existing `Condition` builder and evaluated. Tests cover true/false/unknown. **Do not invent `risk_smoker` from NCZI `OA_FAJCENIE`**: the 2024-specific adapter does not have independently adjudicated current-smoker semantics. | Contract support implemented; 2024-source equivalence **not established** |

## Terminology / IG action required before end-to-end sign-off

- DOAC is represented as a **locally defined class**, `http://qualityregistry.org/CodeSystem/medication-cs#doac`. This code must be added to the authoritative RES-Q IG `MedicationCS` and its bound `MedicationVS`, then checked with terminology validation and the built IG package. **Do not call this a published code until that change is merged.**
- Antidepressant uses established SNOMED CT **372720008**. The IG `MedicationVS` must permit this concept for a fully conformant `MedicationRequest`; check against the actual published ValueSet.
- A broad `discharge_any_anticoagulant` / `before_onset_any_anticoagulant` asserted by a specific DOAC medication is evaluated by recognizing the subtype representation, rather than requiring an artificial second medication order.
- If the registry requires first-class **individual DOAC substances** rather than the aggregate DOAC class, that is *not derivable* from the 2024 categorical `UKON_DOAK` / `OA_ANTIKOAGULANCIA=06` alone.

## Remaining semantic adjudication of explicit negative versus unknown

The synthetic tests establish that the **normalized contract** can carry separate `True`, `False` and `None` values, and that `Condition` and `MedicationStatement` map those to distinct serialized statuses. They **do not establish that all of these statuses are clinically correct**: `Condition.clinicalStatus=inactive` for a risk factor that was *never present* may be over-specific.

Moreover, an explicitly negative discharge medication (`False`) and an unknown discharge medication (`None`) currently **both generate no positive `MedicationRequest`**. This does not preserve the negative/unknown distinction in FHIR. Source-contract values remain distinct, but full source→FHIR parity requires an IG data-model decision. See [issue #26](https://github.com/tecnomod-um/RESQ2FHIR/issues/26).

The proposed new DOAC and antidepressant medication codes require terminology/IG alignment and full profile validation before any end-to-end closure; see [issue #25](https://github.com/tecnomod-um/RESQ2FHIR/issues/25).

## Scientific limits

Passing unit/CI tests provides **regression evidence for the specified synthetic cases**, not proof of all historical production incidents being resolved in clinical data. Re-run the whole NCZI 2024→RES-Q normalized contract→FHIR Bundle→IG validator pipeline on an independently selected dataset before publishing quantitative claims. See `docs/SOURCE_SEMANTIC_ADJUDICATION.md` for the separate unresolved mRS/TICI original-source questions. The TICI problem caused by Spark's variable type inference is **historically closed by developer confirmation** and is intentionally **not** modified by this PR.
