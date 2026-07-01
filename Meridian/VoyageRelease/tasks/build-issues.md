# VoyageRelease Build Issues

## Open Items for User

1. **Placeholder Review Tasks (3 items)** — Awaiting dedicated review apps. The case is structurally complete and validates, but these tasks have empty `data:{}` and will be no-ops at runtime until bound:
   - `DOCUMENT_REVIEW` / `tDocRev001` — needs DocumentReviewApp
   - `PARTY_REVIEW` / `tParRev001` — needs PartyReviewApp
   - `PORT_REVIEW` / `tPortRev001` — needs PortReviewApp

   The only review app currently registered in the solution is `EscalationApp` (ResourceId: `c917ee4e-f070-41ef-94e5-91ade0b24b2b`), but its action schema is not exposed via `uip maestro case tasks describe`. To bind the placeholders, either:
   - Create the three named apps in the solution and re-run the task wiring, OR
   - Reuse EscalationApp once it's promoted to a case-management action app (so it appears in `action-apps-index.json`).

   Each placeholder must end with these outputs to drive the conditional routing:
   - `reviewDecision` (string: `"APPROVE"` or `"REJECT"`)
   - `reviewComment` (string)

2. **PartyValidationAgent agent wiring required** — The agent must call **Get Asset** at the start of each run to fetch `list_type` from Orchestrator. The caseplan.json `list_type` input stays empty — the agent sources the value externally.
   - **Asset name:** `VoyageRelease.PartyValidation.ListType`
   - **Asset key:** `b0cc50ab-cdd9-40a2-8df9-9c22878e7c7f`
   - **Type:** Text
   - **Folder:** `19901aa0-a2af-4d48-851e-de9ae597df07`
   - **Current value:** `"OFAC"` (restricted)
   - **Runtime control:** Orchestrator → Assets → edit `VoyageRelease.PartyValidation.ListType` → save. Next case run picks up the new value. No code change required.

## Resolved Issues

- Duplicate PASS condition on `DOCUMENT_VERIFICATION` exit — removed (`Condition_lKMlAq` deduplicated).
- Missing `reviewDecision` / `reviewComment` variables — added to `variables.inputOutputs[]`.
- `releaseOutcome` type mismatch — trigger response schema changed from `integer` to `string` to match task outputs.
- `approvedOverride` unused field — removed from trigger response schema (the override case is already captured via the `RELEASED_WITH_OVERRIDE` value of `releaseOutcome`).

## Structural Validation

- 9 stages present (5 primary + 4 secondary)
- 6 resolved tasks with full I/O schemas
- 3 placeholder tasks (action-type, awaiting app binding)
- All conditional routing wired (PASS/FAIL/REVIEW on primary stages; APPROVE/REJECT on review stages)
- Re-entry conditions present on Document Intake, Party Validation, Port Readiness
- SLA: 24h at case level
- Case exit rules: `required-stages-completed` + `selected-stage-completed(REJECTED)`
- CLI validation: `cases get` → `Success` / `CaseRetrieved`
