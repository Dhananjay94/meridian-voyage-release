# SDD — VoyageRelease

**Case Definition Blueprint** — maritime voyage-release compliance. A new case orchestrates document understanding, party screening, port readiness, and human-in-the-loop review on every new voyage record, culminating in a release decision.

## Table of Contents

1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Triggers, Exit Conditions, Variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: Document Intake](#stage-1-document-intake) — 1 task
   - [Stage 2: Document Verification](#stage-2-document-verification) — 1 task
   - [Stage 3: Party Validation](#stage-3-party-validation) — 1 task
   - [Stage 4: Port Readiness](#stage-4-port-readiness) — 1 task
   - [Stage 5: Released](#stage-5-released) — 1 task
   - [Exception Stage: Party Review](#exception-stage-party-review) — 1 task
   - [Exception Stage: Port Review](#exception-stage-port-review) — 1 task
   - [Exception Stage: Document Review](#exception-stage-document-review) — 1 task
   - [Exception Stage: Rejected](#exception-stage-rejected) — 1 task
3. [Personas & App Views](#section-3-personas--app-views) — 2 Personas, Case App view
4. [Integrations](#section-4-integrations) — IS Connectors, API Workflows, Agents, Processes & RPA

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | VoyageRelease |
| Case Description | Reviews and approves the release of a maritime voyage. Verifies the five shipping documents, screens shipper / consignee / vessel operator against denied-party lists, confirms destination port readiness, and routes flagged items through human review before issuing a release outcome. |
| Case Identifier | Type: `constant`. Prefix: `VOY` |
| Priority | Choiceset: Low, Medium, High, Critical — Default: Medium |
| Case-Level SLA | 24 h |
| SLA Type | time-based |
| Case App | Enabled |
| Task-output passing | Direct |
| Case Identifier source | `=metadata.ExternalId` |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | 75% of SLA duration | Notify: `UserGroup:Maritime Compliance Reviewers` |
| Breached | 100% of SLA duration | Notify: `UserGroup:Operations Leadership` |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Intsvc.EventTrigger | UiPath Data Fabric | Record created on object `MeridianCase` |

> The user opted to reuse the existing `MeridianCase` Data Fabric entity rather than mint a new `VoyageRelease` entity (the entity already carries the five shipping-document file fields plus the scalar voyage fields). The trigger is the same `Record Created` activity the existing MeridianCase project uses, on the same Data Fabric connection.

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| `required-stages-completed` | — | Case exited | Yes | Complete Rule 1 |

### Case Exit Conditions (alternate disposition)

| WHEN | IF | Marks Case Complete | Exit Type | Display Name |
|------|-----|---------------------|-----------|--------------|
| `selected-stage-completed("Rejected")` | — | No | `exit-only` | Exit Rule 1 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| caseId | Variable | string | T02 | response.caseId | | External case id supplied by the trigger record. |
| vesselName | Variable | string | T02 | response.voyage | | Vessel name carried in the trigger payload's `voyage` field. |
| voyageNumber | Variable | string | T02 | response.externalKey | | Voyage number carried in the trigger payload's `externalKey` field. |
| destinationPortCode | Variable | string | T02 | response.parties | | Destination port code; reuses the existing `parties` slot on the MeridianCase entity. |
| shipper | Variable | string | T02 | response.parties | | Shipper name; carried alongside the other party identifiers in `parties`. |
| consignee | Variable | string | T02 | response.parties | | Consignee name; carried alongside the other party identifiers in `parties`. |
| vesselOperator | Variable | string | T02 | response.parties | | Vessel operator name; carried alongside the other party identifiers in `parties`. |
| bolDocument | Variable | file | T02 | response.bolDocument | | Bill of Lading attachment from the trigger record. |
| cargoManifestDocument | Variable | file | T02 | response.cargoManifestDocument | | Cargo manifest attachment from the trigger record. |
| certificateOfOriginDocument | Variable | file | T02 | response.certificateOfOriginDocument | | Certificate of Origin attachment from the trigger record. |
| insuranceCertificateDocument | Variable | file | T02 | response.insuranceCertificateDocument | | Insurance certificate attachment from the trigger record. |
| qualityCertificateDocument | Variable | file | T02 | response.qualityCertificateDocument | | Quality certificate attachment from the trigger record. |
| docResult | Variable | string | | | | Document Verification outcome — `PASS`, `FAIL`, or `REVIEW`. Read by Document Verification exits and by Document Review entry. |
| docComment | Variable | string | | | | One-sentence rationale produced by VerificationAgent; surfaced in the closure summary. |
| flaggedDocument | Variable | string | | | | When `docResult == "REVIEW"`, the key of the document the reviewer must re-upload. |
| partyResult | Variable | string | | | | Party Validation outcome — `PASS`, `FAIL`, or `REVIEW`. Read by Party Validation exits and by Party Review entry. |
| partyComment | Variable | string | | | | One-sentence rationale produced by PartyValidationAgent; surfaced in the closure summary. |
| partyScore | Variable | number | | | | Worst denied-party score (0.0–1.0); 0.0 when CLEAR. Surfaced in the closure summary. |
| portResult | Variable | string | | | | Port Readiness outcome — `PASS`, `FAIL`, or `REVIEW`. Read by Port Readiness exits and by Port Review entry. |
| portComment | Variable | string | | | | One-sentence rationale produced by PortLookupTool; surfaced in the closure summary. |
| reviewDecision | Variable | string | | | | Reviewer decision on the active review lane — `APPROVE` or `REJECT`. Read by the originating stage's re-evaluation and by the Document Review continuation rule. |
| reviewComment | Variable | string | | | | Reviewer's comment; surfaced in the closure summary. |
| reviewOriginStage | Variable | string | | | | Tag written by whichever review lane fires so the closure summary can reference which validation produced the override. |
| partyOverride | Variable | boolean | | | false | Set to `true` only by Party Review APPROVE. Gates Party Validation's completion (PASS-or-approved) and suppresses its REVIEW divert on re-entry. Lane-specific so an approval in one lane never bypasses another lane's REVIEW. |
| portOverride | Variable | boolean | | | false | Set to `true` only by Port Review APPROVE. Gates Port Readiness's completion and suppresses its REVIEW divert on re-entry. |
| approvedOverride | Variable | boolean | | | false | Set to `true` whenever ANY review lane returns `APPROVE` (Party / Port / Document Review). Read only by ReleaseCoordinatorAgent at Released to decide `RELEASED` vs `RELEASED_WITH_OVERRIDE`. NOT used for gating — see `partyOverride` / `portOverride` for that. |
| closureSummary | Variable | string | | | | Human-readable case summary written by ReleaseCoordinatorAgent in Released or Rejected. |
| releaseOutcome | Out | string | | | | Final outcome — `RELEASED`, `RELEASED_WITH_OVERRIDE`, or `REJECTED`. Written only once per case (see business rules below). |

> **Business rule — write-once outcome:** `releaseOutcome` is written exactly once. Released sets `RELEASED` (or `RELEASED_WITH_OVERRIDE` when `approvedOverride === true`); Rejected sets `REJECTED`. Once Rejected fires, no later stage writes the variable.
>
> **Business rule — REJECT signaling:** A reviewer's `REJECT` does NOT flow through `return-to-origin`. Each review lane routes `REJECT` directly to Rejected via `exit-only`. `APPROVE` is the only signal that returns to the originating stage (Party Review, Port Review) or re-enters Document Intake (Document Review).
>
> **Business rule — clear on re-entry:** When Document Review's `APPROVE` re-enters Document Intake, the Run DUExtraction task's Outputs clear `reviewDecision`, `reviewComment`, and `flaggedDocument` (via `=`-assignments) so the next review lane starts clean. The override flags (`approvedOverride`, `partyOverride`, `portOverride`) are NEVER cleared — they persist for the lifetime of the case.
>
> **Business rule — three override flags, three jobs:** Two per-lane booleans (`partyOverride`, `portOverride`) gate their originating stage on re-entry. One global boolean (`approvedOverride`) is the input ReleaseCoordinatorAgent reads at Released. All three are set `true` by their respective review's `APPROVE` button via `=`-assignment outputs.

---

## Section 2: Stages & Tasks

The case has five primary stages on the happy path (Document Intake → Document Verification → Party Validation → Port Readiness → Released) and four exception stages (Party Review, Port Review, Document Review, Rejected). Routing between stages is condition-driven — there are no edges. Each primary stage that branches on a `PASS / FAIL / REVIEW` signal carries a gated completion exit (continues forward when the result is `PASS`) plus two gated divert exits (`Marks Stage Complete: No` — one to Rejected on `FAIL`, one to the matching review lane on `REVIEW`).

The three review lanes use **per-lane override flags** so that an approval in one lane never bypasses another lane's gates:

- **Party Review** sets `partyOverride = true` on `APPROVE`. Party Validation completes when `partyResult === "PASS" OR partyOverride === true`. Its REVIEW divert is gated by `partyOverride !== true` to prevent re-entry loops.
- **Port Review** mirrors the pattern with `portOverride`.
- **Document Review** does NOT set a per-lane gate (it forward-routes to Document Intake — DUExtraction re-runs and emits a fresh `docResult`).

All three lanes additionally set `approvedOverride = true` on `APPROVE` — this is the single signal ReleaseCoordinatorAgent reads at Released to choose between `RELEASED` and `RELEASED_WITH_OVERRIDE`.

`REJECT` on any review lane bypasses `return-to-origin` and routes directly to Rejected via `exit-only` — no override flag is written. Document Review's `APPROVE` re-enters Document Intake (not its origin Document Verification) so DUExtraction re-runs on the corrected file; Party Review and Port Review use `return-to-origin` on `APPROVE` so the originating stage's `Run Only Once: Yes` task is skipped and the completion gate re-evaluates with the lane override.

---

### Stage 1: Document Intake

**Type:** Stage
**Description:** Runs the DUExtraction RPA workflow against the trigger record's five document attachments and emits a single `documentPacket` payload for downstream verification. Re-entered when Document Review approves a corrected document — DUExtraction's Outputs clear `reviewDecision`, `reviewComment`, and `flaggedDocument` on every run so the next review lane starts clean. Override flags (`approvedOverride`, `partyOverride`, `portOverride`) are deliberately NOT cleared — they must persist for the lifetime of the case.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `case-entered` | — | No | Entry Rule 1 |
| `selected-stage-exited("Document Review")` | `=js:(vars.reviewDecision === "APPROVE")` | Yes | Entry Rule 2 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | `exit-only` | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Run DUExtraction | rpa | Yes | No | system | — |

##### Task 1.1: Run DUExtraction

**Type:** rpa
**Description:** Runs the `DUExtraction` RPA workflow against the case record. The workflow reads the five document attachments by `caseId`, runs document understanding, and writes a single `documentPacket` JSON string covering BoL, manifest, certificate of origin, insurance certificate, and quality certificate. Its Outputs also clear the per-review-lane scratch variables on completion (`=`-assignments) so each new Document Intake activation starts with a clean review slate. The override flags are intentionally NOT cleared — they're sticky for the lifetime of the case.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Resolved Resource:** DUExtraction
**Folder Path:** `<UNRESOLVED>` _(project is in this solution; bound by solution-project name + folder at deploy time)_
**Resource Identity:** `<UNRESOLVED>` _(not yet deployed; bindings resolve at solution pack time)_
**Binding Sub-Type:** —
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| documentpacket | -> documentPacket |
| — | reviewDecision = "" |
| — | reviewComment = "" |
| — | flaggedDocument = "" |

---

### Stage 2: Document Verification

**Type:** Stage
**Description:** Runs VerificationAgent against the extracted `documentPacket`. The agent emits `docResult` (`PASS` / `FAIL` / `REVIEW`), a one-sentence `docComment`, and (when `REVIEW`) the `flaggedDocument` key the reviewer must re-upload. Completion gates on `PASS`; `FAIL` diverts to Rejected; `REVIEW` diverts to Document Review.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Document Intake")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:(vars.docResult === "PASS")` | `exit-only` | Yes | Complete Rule 1 |
| `selected-tasks-completed("Run VerificationAgent")` | `=js:(vars.docResult === "FAIL")` | `exit-only` _(`exitToStageId` → Rejected)_ | No | Exit Rule 1 |
| `selected-tasks-completed("Run VerificationAgent")` | `=js:(vars.docResult === "REVIEW")` | `exit-only` _(`exitToStageId` → Document Review)_ | No | Exit Rule 2 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Run VerificationAgent | agent | Yes | No | system | — |

##### Task 2.1: Run VerificationAgent

**Type:** agent
**Description:** Runs the `VerificationAgent` against the extracted document packet. The agent inspects the five document objects, runs cross-document consistency checks, and emits `docResult` plus a deciding rationale.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Resolved Resource:** VerificationAgent
**Folder Path:** `dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian`
**Resource Identity:** `965ac3e9-96b8-4d6c-a777-c6ec630618a3` (agent)
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| documentPacket | string | `=vars.documentPacket` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| docResult | -> docResult |
| docComment | -> docComment |
| flaggedDocument | -> flaggedDocument |

---

### Stage 3: Party Validation

**Type:** Stage
**Description:** Runs PartyValidationAgent to screen shipper, consignee, and vessel operator against denied-party lists. Emits `partyResult` (`PASS` / `FAIL` / `REVIEW`), a one-sentence `partyComment`, and a 0.0–1.0 `partyScore`. Completion gates on `PASS` OR an approved override from Party Review.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Document Verification")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:(vars.partyResult === "PASS" || vars.partyOverride === true)` | `exit-only` | Yes | Complete Rule 1 |
| `selected-tasks-completed("Run PartyValidationAgent")` | `=js:(vars.partyResult === "FAIL")` | `exit-only` _(`exitToStageId` → Rejected)_ | No | Exit Rule 1 |
| `selected-tasks-completed("Run PartyValidationAgent")` | `=js:(vars.partyResult === "REVIEW" && vars.partyOverride !== true)` | `exit-only` _(`exitToStageId` → Party Review)_ | No | Exit Rule 2 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Run PartyValidationAgent | agent | Yes | Yes | system | — |

##### Task 3.1: Run PartyValidationAgent

**Type:** agent
**Description:** Runs the `PartyValidationAgent` to screen the three named parties. `Run Only Once: Yes` so the agent is skipped on re-entry from Party Review — the stage completion gate then re-evaluates with `partyOverride` (set `true` by the lane's APPROVE button).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** PartyValidationAgent
**Folder Path:** `dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian`
**Resource Identity:** `de933600-26f3-45fb-8274-e75865599c4d` (agent)
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| shipper | string | `=vars.shipper` |
| consignee | string | `=vars.consignee` |
| vessel_operator | string | `=vars.vesselOperator` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| partyResult | -> partyResult |
| partyComment | -> partyComment |
| partyScore | -> partyScore |

---

### Stage 4: Port Readiness

**Type:** Stage
**Description:** Runs the `PortLookupTool` API workflow to confirm the destination port is open for the voyage. Emits `portResult` (`PASS` / `FAIL` / `REVIEW`) and a one-sentence `portComment`. Completion gates on `portResult == "PASS"` OR `portOverride === true` (Port Review approved). The REVIEW divert is suppressed when `portOverride === true` to prevent a re-entry loop.

> **Port result semantics.** `PASS` = port is open / cleared for this voyage. `FAIL` = port is explicitly denied (sanctions, embargo, closed). `REVIEW` = port not found in the lookup table or status indeterminate / low-confidence. The Port Review lane is reachable only on `REVIEW`; if the deployed PortLookupTool ends up emitting only `PASS` / `FAIL` (no `REVIEW`), the Port Review lane will be unreachable — a known acceptable state.

**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Party Validation")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:(vars.portResult === "PASS" || vars.portOverride === true)` | `exit-only` | Yes | Complete Rule 1 |
| `selected-tasks-completed("Run PortLookupTool")` | `=js:(vars.portResult === "FAIL")` | `exit-only` _(`exitToStageId` → Rejected)_ | No | Exit Rule 1 |
| `selected-tasks-completed("Run PortLookupTool")` | `=js:(vars.portResult === "REVIEW" && vars.portOverride !== true)` | `exit-only` _(`exitToStageId` → Port Review)_ | No | Exit Rule 2 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Run PortLookupTool | api-workflow | Yes | Yes | system | — |

##### Task 4.1: Run PortLookupTool

**Type:** api-workflow
**Description:** Calls the `PortLookupTool` API workflow to look up the destination port's operational status. `Run Only Once: Yes` so re-entry from Port Review skips the call and the stage's completion gate re-evaluates with `portOverride` (set `true` by the Port Review APPROVE button).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** PortLookupTool
**Folder Path:** `<UNRESOLVED>` _(project is in this solution; bound by solution-project name + folder at deploy time)_
**Resource Identity:** `<UNRESOLVED>` _(not yet deployed; bindings resolve at solution pack time)_
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| destinationPortCode | string | `=vars.destinationPortCode` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| portResult | -> portResult |
| portComment | -> portComment |

---

### Stage 5: Released

**Type:** Stage
**Description:** Terminal happy-path stage. Runs `ReleaseCoordinatorAgent` to compose a one-sentence `closureSummary` from the verification, party, and port comments, then writes `releaseOutcome` — `RELEASED_WITH_OVERRIDE` when any review approved the case, otherwise `RELEASED`.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Port Readiness")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | `exit-only` | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Write closure summary | agent | Yes | Yes | system | — |

##### Task 5.1: Write closure summary

**Type:** agent
**Description:** Runs `ReleaseCoordinatorAgent` to assemble `closureSummary` from the case's accumulated comments and writes the appropriate `releaseOutcome` value.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** ReleaseCoordinatorAgent
**Folder Path:** `dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian`
**Resource Identity:** `05a27308-2df8-49b0-89ce-cb2e15fbc20f` (agent)
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| docComment | string | `=vars.docComment` |
| partyComment | string | `=vars.partyComment` |
| portComment | string | `=vars.portComment` |
| reviewComment | string | `=vars.reviewComment` |
| approvedOverride | boolean | `=vars.approvedOverride` |
| outcomeContext | string | "released" |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| closureSummary | -> closureSummary |
| — | releaseOutcome = `=js:(vars.approvedOverride === true ? "RELEASED_WITH_OVERRIDE" : "RELEASED")` |

---

### Exception Stage: Party Review

**Type:** ExceptionStage
**Description:** Human review lane that fires when `partyResult == "REVIEW"`. A maritime compliance reviewer inspects the party-screening evidence and decides `APPROVE` (case continues forward past Party Validation) or `REJECT` (case routes to Rejected). On `APPROVE`, the lane writes `approvedOverride = true` and returns to Party Validation; PartyValidationAgent is skipped on re-entry (Run Only Once: Yes) and the stage's completion gate re-evaluates with the override.
**Required for Case Completion:** No
**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-exited("Party Validation")` | `=js:(vars.partyResult === "REVIEW")` | Yes | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:(vars.reviewDecision === "APPROVE")` | `return-to-origin` | Yes | Complete Rule 1 |
| `selected-tasks-completed("Party reviewer decision")` | `=js:(vars.reviewDecision === "REJECT")` | `exit-only` _(`exitToStageId` → Rejected)_ | No | Exit Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Party reviewer decision | action | Yes | No | Maritime Compliance Reviewer | — |

##### Task PR.1: Party reviewer decision

**Type:** action
**Description:** Human task using `PartyReviewApp` (not yet deployed — Phase 1 will surface as a high-severity review item). The reviewer sees shipper / consignee / vessel operator and the party screening rationale, then picks `APPROVE` or `REJECT` with a free-text `reviewComment`.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**HITL Implementation:** Action App: `PartyReviewApp` _(placeholder — app not yet deployed)_
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`
**actionType:** `PartyReview`
**Recipient:** `Role:Maritime Compliance Reviewer`
**Priority:** High · **Task Title:** Review denied-party screening for this voyage · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| caseId | String | `=metadata.ExternalId` | Yes |
| shipper | String | `=vars.shipper` | Yes |
| consignee | String | `=vars.consignee` | Yes |
| vesselOperator | String | `=vars.vesselOperator` | Yes |
| partyResult | String | `=vars.partyResult` | Yes |
| partyComment | String | `=vars.partyComment` | Yes |
| partyScore | Number | `=vars.partyScore` | No |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> reviewDecision |
| reviewComment | -> reviewComment |
| — | reviewOriginStage = "Party Validation" |
| — | partyOverride = `=js:(vars.reviewDecision === "APPROVE")` |
| — | approvedOverride = `=js:(vars.reviewDecision === "APPROVE")` |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | reviewDecision = "APPROVE" | Approves the override. Lane's `=` outputs set both `partyOverride = true` (gates Party Validation's completion re-evaluation) and `approvedOverride = true` (read by ReleaseCoordinatorAgent at Released). Case returns to Party Validation via `return-to-origin`. |
| Reject | reviewDecision = "REJECT" | Rejects the override; case routes to Rejected via `exit-only`. No override flag is set. |

---

### Exception Stage: Port Review

**Type:** ExceptionStage
**Description:** Human review lane that fires when `portResult == "REVIEW"`. A maritime compliance reviewer inspects the port-readiness evidence and decides `APPROVE` (case continues forward past Port Readiness) or `REJECT` (case routes to Rejected). On `APPROVE`, the lane writes `approvedOverride = true` and returns to Port Readiness; PortLookupTool is skipped on re-entry and the stage's completion gate re-evaluates with the override.
**Required for Case Completion:** No
**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-exited("Port Readiness")` | `=js:(vars.portResult === "REVIEW")` | Yes | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:(vars.reviewDecision === "APPROVE")` | `return-to-origin` | Yes | Complete Rule 1 |
| `selected-tasks-completed("Port reviewer decision")` | `=js:(vars.reviewDecision === "REJECT")` | `exit-only` _(`exitToStageId` → Rejected)_ | No | Exit Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Port reviewer decision | action | Yes | No | Maritime Compliance Reviewer | — |

##### Task PoR.1: Port reviewer decision

**Type:** action
**Description:** Human task using `PortReviewApp` (not yet deployed — Phase 1 will surface as a high-severity review item). The reviewer sees the destination port code and the lookup rationale, then picks `APPROVE` or `REJECT` with a free-text `reviewComment`.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**HITL Implementation:** Action App: `PortReviewApp` _(placeholder — app not yet deployed)_
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`
**actionType:** `PortReview`
**Recipient:** `Role:Maritime Compliance Reviewer`
**Priority:** High · **Task Title:** Review port readiness for this voyage · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| caseId | String | `=metadata.ExternalId` | Yes |
| destinationPortCode | String | `=vars.destinationPortCode` | Yes |
| portResult | String | `=vars.portResult` | Yes |
| portComment | String | `=vars.portComment` | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> reviewDecision |
| reviewComment | -> reviewComment |
| — | reviewOriginStage = "Port Readiness" |
| — | portOverride = `=js:(vars.reviewDecision === "APPROVE")` |
| — | approvedOverride = `=js:(vars.reviewDecision === "APPROVE")` |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | reviewDecision = "APPROVE" | Approves the override. Lane's `=` outputs set both `portOverride = true` (gates Port Readiness's completion re-evaluation) and `approvedOverride = true` (read by ReleaseCoordinatorAgent at Released). Case returns to Port Readiness via `return-to-origin`. |
| Reject | reviewDecision = "REJECT" | Rejects the override; case routes to Rejected via `exit-only`. No override flag is set. |

---

### Exception Stage: Document Review

**Type:** ExceptionStage
**Description:** Human review lane that fires when `docResult == "REVIEW"`. The reviewer re-uploads the corrected document named in `flaggedDocument` and picks `APPROVE` or `REJECT`. `APPROVE` re-enters Document Intake so DUExtraction re-runs on the corrected file; `REJECT` routes to Rejected. This lane does NOT return to its origin Document Verification — its `APPROVE` exit is a forward route to Document Intake.
**Required for Case Completion:** No
**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-exited("Document Verification")` | `=js:(vars.docResult === "REVIEW")` | Yes | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `selected-tasks-completed("Document reviewer decision")` | `=js:(vars.reviewDecision === "APPROVE")` | `exit-only` _(`exitToStageId` → Document Intake)_ | No | Exit Rule 1 |
| `selected-tasks-completed("Document reviewer decision")` | `=js:(vars.reviewDecision === "REJECT")` | `exit-only` _(`exitToStageId` → Rejected)_ | No | Exit Rule 2 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Document reviewer decision | action | Yes | No | Maritime Compliance Reviewer | — |

##### Task DR.1: Document reviewer decision

**Type:** action
**Description:** Human task using `DocumentReviewApp` (not yet deployed — Phase 1 will surface as a high-severity review item). The reviewer sees the originally-flagged document key and the agent's rationale, uploads a corrected file, and picks `APPROVE` or `REJECT` with a free-text `reviewComment`.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**HITL Implementation:** Action App: `DocumentReviewApp` _(placeholder — app not yet deployed)_
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`
**actionType:** `DocumentReview`
**Recipient:** `Role:Maritime Compliance Reviewer`
**Priority:** High · **Task Title:** Re-upload the flagged document · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| caseId | String | `=metadata.ExternalId` | Yes |
| flaggedDocument | String | `=vars.flaggedDocument` | Yes |
| docComment | String | `=vars.docComment` | Yes |
| bolDocument | file | `=vars.bolDocument` | No |
| cargoManifestDocument | file | `=vars.cargoManifestDocument` | No |
| certificateOfOriginDocument | file | `=vars.certificateOfOriginDocument` | No |
| insuranceCertificateDocument | file | `=vars.insuranceCertificateDocument` | No |
| qualityCertificateDocument | file | `=vars.qualityCertificateDocument` | No |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> reviewDecision |
| reviewComment | -> reviewComment |
| bolDocument | -> bolDocument |
| cargoManifestDocument | -> cargoManifestDocument |
| certificateOfOriginDocument | -> certificateOfOriginDocument |
| insuranceCertificateDocument | -> insuranceCertificateDocument |
| qualityCertificateDocument | -> qualityCertificateDocument |
| — | reviewOriginStage = "Document Verification" |
| — | approvedOverride = `=js:(vars.reviewDecision === "APPROVE")` |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | reviewDecision = "APPROVE" | Approves the corrected document. The deployed app emits the re-uploaded file into whichever of the five document slots matched `flaggedDocument`; the other four fields emit null (and their `->` extracts no-op). Case re-enters Document Intake via `exit-only` forward-route so DUExtraction runs again on the corrected packet. Sets `approvedOverride = true` so the eventual Released stage marks `RELEASED_WITH_OVERRIDE`. |
| Reject | reviewDecision = "REJECT" | Rejects the document; case routes to Rejected via `exit-only`. No override flag is set. |

> **Note:** the deployed `DocumentReviewApp` must expose five `file` output fields (`bolDocument`, `cargoManifestDocument`, `certificateOfOriginDocument`, `insuranceCertificateDocument`, `qualityCertificateDocument`) and route the reviewer's re-uploaded file into whichever one matches `flaggedDocument` (set by VerificationAgent in Stage 2). The other four file fields emit null on each run. This is a high-severity placeholder review item — the app must be deployed and wired to this exact 5-slot output schema before the case can publish.

---

### Exception Stage: Rejected

**Type:** ExceptionStage
**Description:** Terminal exception lane. Entered from any primary or review stage that produces a `FAIL` / `REJECT` signal. Runs `ReleaseCoordinatorAgent` once to compose a closure summary, writes `releaseOutcome = "REJECTED"`, and exits the case via the §1.4a case-exit on `selected-stage-completed("Rejected")`.
**Required for Case Completion:** No
**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-exited("Document Verification")` | `=js:(vars.docResult === "FAIL")` | Yes | Entry Rule 1 |
| `selected-stage-exited("Party Validation")` | `=js:(vars.partyResult === "FAIL")` | Yes | Entry Rule 2 |
| `selected-stage-exited("Port Readiness")` | `=js:(vars.portResult === "FAIL")` | Yes | Entry Rule 3 |
| `selected-stage-exited("Party Review")` | `=js:(vars.reviewDecision === "REJECT")` | Yes | Entry Rule 4 |
| `selected-stage-exited("Port Review")` | `=js:(vars.reviewDecision === "REJECT")` | Yes | Entry Rule 5 |
| `selected-stage-exited("Document Review")` | `=js:(vars.reviewDecision === "REJECT")` | Yes | Entry Rule 6 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | `exit-only` | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Write rejection summary | agent | Yes | Yes | system | — |

##### Task R.1: Write rejection summary

**Type:** agent
**Description:** Runs `ReleaseCoordinatorAgent` to compose `closureSummary` for the rejected case and writes `releaseOutcome = "REJECTED"`.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** ReleaseCoordinatorAgent
**Folder Path:** `dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian`
**Resource Identity:** `05a27308-2df8-49b0-89ce-cb2e15fbc20f` (agent)
**Binding Sub-Type:** Agent
**Dispatch / Operation:** `outcomeContext = "rejected"`

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| docComment | string | `=vars.docComment` |
| partyComment | string | `=vars.partyComment` |
| portComment | string | `=vars.portComment` |
| reviewComment | string | `=vars.reviewComment` |
| reviewOriginStage | string | `=vars.reviewOriginStage` |
| outcomeContext | string | "rejected" |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| closureSummary | -> closureSummary |
| — | releaseOutcome = "REJECTED" |

---

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| Maritime Compliance Reviewer | Party Review, Port Review, Document Review | View, Act, Reassign | Reviews flagged voyages — decides on denied-party hits, port-readiness ambiguities, and document re-uploads. |
| Operations Lead | All | View, Act, Reassign | Receives SLA breach escalations and oversees case throughput across all stages. |

### Case App Views

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| Case App | Case list | Maritime Compliance Reviewer, Operations Lead | List active VoyageRelease cases and their current stage. | Columns: caseId, vesselName, voyageNumber, current stage, partyResult, portResult, docResult, SLA status. Filters: by stage, by reviewer. |
| Case App | Case detail | Maritime Compliance Reviewer, Operations Lead | Inspect the full case state and decision audit. | Sections: voyage parties, five document attachments, agent rationales (docComment / partyComment / portComment), active review tasks, releaseOutcome on close. |

---

## Section 4: Integrations

### Integration Service Connectors

| Connector | Connector Key | System | Connection (ID) | Auth Method | Operations Used | Used By Tasks |
|-----------|---------------|--------|-----------------|-------------|-----------------|---------------|
| UiPath Data Fabric | `uipath-uipath-dataservice` | UiPath Data Fabric (tenant data store) | Default tenant connection (`340a34eb-b132-42ae-9efc-95c151a40b54`) | Bearer (tenant default) | Record Created (trigger) | Trigger T02 |

#### UiPath Data Fabric

**Operations:**

| Operation | Activity Type ID | Method | Input Fields | Output Fields |
|-----------|------------------|--------|-------------|---------------|
| Record Created | `af2a53ad-5d90-3d4e-bf3c-55b6d91595cd` | EVENT | objectName=`MeridianCase`; operation=`CREATED` | Full record payload — caseId, voyage, parties, externalKey, five file fields, status enums |

### API Workflows

| Workflow | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|----------|--------|------------------------|------------------|---------------|
| PortLookupTool | `<UNRESOLVED — solution-bound>` | `<UNRESOLVED — solution-bound>` | destinationPortCode → portResult, portComment | Task 4.1: Run PortLookupTool |

> Project lives at `/solution/PortLookupTool/` in this solution. Identity binds at solution pack time.

### Agents

| Agent | Folder | Resource ID (+version) | Inputs → Outputs (or shared contract) | Used By Tasks |
|-------|--------|------------------------|----------------------------------------|---------------|
| VerificationAgent | `dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian` | `965ac3e9-96b8-4d6c-a777-c6ec630618a3` (1.0.0-debug) | documentPacket → docResult, docComment, flaggedDocument | Task 2.1 |
| PartyValidationAgent | `dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian` | `de933600-26f3-45fb-8274-e75865599c4d` (1.0.0-debug) | shipper, consignee, vessel_operator → partyResult, partyComment, partyScore | Task 3.1 |
| ReleaseCoordinatorAgent | `dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian` | `05a27308-2df8-49b0-89ce-cb2e15fbc20f` (1.0.0-debug) | caseId, comments, outcomeContext → closureSummary | Tasks 5.1, R.1 |

### Processes & RPA

| Resource | Type | Folder | Resource ID (+version) | Used By Tasks |
|----------|------|--------|------------------------|---------------|
| DUExtraction | rpa | `<UNRESOLVED — solution-bound>` | `<UNRESOLVED — solution-bound>` | Task 1.2 |

> Project lives at `/solution/DUExtraction/`. Identity binds at solution pack time.

### Action Apps (placeholders)

| App | Recipient | Used By Tasks |
|-----|-----------|---------------|
| PartyReviewApp | Role:Maritime Compliance Reviewer | Task PR.1 |
| PortReviewApp | Role:Maritime Compliance Reviewer | Task PoR.1 |
| DocumentReviewApp | Role:Maritime Compliance Reviewer | Task DR.1 |

> None of the three action apps are deployed. Phase 1 will surface each as a high-severity review item. The case plan will author each action task with `<UNRESOLVED>` action-app id and Phase 2 will emit Rule-8 placeholders that you (or another skill) wire to deployed apps later.
