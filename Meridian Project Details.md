# Meridian — Voyage Release Control System


## 1. Business Problem

Meridian governs whether a voyage may be released, held, or revalidated as operational evidence changes after work has already started.

Today, when one release-critical fact changes, teams often re-run the full release packet because prior conclusions are stored as flat outcomes, not as evidence-linked, independently re-checkable assumptions.

Meridian fixes this by giving each release check:

```text
- its own stage
- its own owner
- its own re-entry rule
- its own auditable assumption record
```

So when one fact changes, only the affected stage reactivates, only the responsible team is notified, and the case history shows exactly what changed and why.

---

## 2. Case Model

### Case name

```text
Voyage Release Case
```

### Example case ID

```text
VOY-2026-0417
```

### Case goal

```text
Decide whether voyage VOY-2026-0417 can be released, held, overridden, or cancelled.
```

### Final outcomes

```text
RELEASED
RELEASED_WITH_OVERRIDE
ON_HOLD_UNRESOLVED
CANCELLED
```

---

## 3. Case Personas

| Persona | Responsibility |
|---|---|
| Voyage Coordinator | Owns and tracks the case end-to-end. Opens the case, monitors progress, and coordinates across teams. |
| Documentation Analyst | Owns document intake, BOL extraction, manifest consistency, and certificate completeness. |
| Trade Compliance Analyst | Owns party validation outcomes and reviews possible party matches. |
| Port Operations Analyst | Owns destination port readiness and port-status rechecks. |
| Release Manager | Owns the final release decision, hold decision, override decision, and cost/delay acceptance. |
| Compliance Manager | Escalation persona for confirmed risk, SLA breach, or unresolved compliance hold. |
| Port Operations Lead | Escalation persona for Port Readiness SLA breaches. Sits above Port Operations Analyst, the same way Compliance Manager sits above Trade Compliance Analyst. |

### Persona-to-stage visibility

| Stage | Primary persona |
|---|---|
| Document Intake | Documentation Analyst |
| Document Verification | Documentation Analyst |
| Party Validation | Trade Compliance Analyst |
| Port Readiness | Port Operations Analyst |
| Monitoring | Voyage Coordinator |
| Human Review | Depends on issue type |
| On Hold | Release Manager |
| Closure | Release Manager |
| Port Readiness (SLA breach only) | Port Operations Lead — escalation, not normal-path owner |

### Adoption story

The Port Operations Analyst does not need to monitor every voyage release case. They only receive work when the port-readiness stage is active or re-entered due to a port-related event.

That is the enterprise value:

```text
The right team sees the case only when the case needs their expertise.
```

---

## 4. Case Entity

The case entity is the persistent record that every stage reads and writes.

The Assumption Ledger lives inside the case entity.

### Example case entity

```json
{
  "caseId": "VOY-2026-0417",
  "externalKey": "VOY-2026-0417",
  "caseStatus": "MONITORING",
  "caseOwner": {
    "persona": "Voyage Coordinator",
    "team": "Release Operations"
  },
  "voyage": {
    "vesselName": "MV Helios Star",
    "originPortCode": "GRPIR",
    "destinationPortCode": "AEJEA",
    "destinationPortName": "Jebel Ali"
  },
  "parties": {
    "shipper": "Aegean Bulk Traders SA",
    "consignee": "Gulf Industrial Supplies LLC",
    "vesselOperator": "Helios Marine Operations"
  },
  "assumptions": [
    {
      "assumptionId": "ASM-DOC",
      "checkType": "document_completeness",
      "ownerStage": "Document Verification",
      "status": "VALID",
      "evidenceRef": "BOL_CLEAN.pdf#extract_2026-06-18T09:12Z",
      "dependsOn": [
        "document_fields",
        "certificate_list"
      ],
      "invalidationTriggers": [
        "document_amended",
        "certificate_requirement_changed"
      ],
      "version": 1,
      "supersededBy": null
    },
    {
      "assumptionId": "ASM-PARTY",
      "checkType": "party_validation",
      "ownerStage": "Party Validation",
      "status": "VALID",
      "evidenceRef": "party_validation_list_v2026.06.18.csv",
      "dependsOn": [
        "party_names",
        "party_validation_list_version"
      ],
      "invalidationTriggers": [
        "party_name_changed",
        "party_validation_list_updated"
      ],
      "version": 1,
      "supersededBy": null
    },
    {
      "assumptionId": "ASM-PORT",
      "checkType": "port_readiness",
      "ownerStage": "Port Readiness",
      "status": "VALID",
      "evidenceRef": "port_status_lookup_2026-06-18T09:20Z",
      "dependsOn": [
        "port_status",
        "destination_port"
      ],
      "invalidationTriggers": [
        "port_status_change",
        "destination_port_changed"
      ],
      "version": 1,
      "supersededBy": null
    }
  ],
  "openTasks": [],
  "approvedOverride": null,
  "releaseOutcome": null,
  "closureRecord": null
}
```

When an override is approved, `approvedOverride` is populated like this — it is never
implied, only ever set explicitly by a Release Manager action:

```json
"approvedOverride": {
  "overrideId": "OVR-PORT-001",
  "approvedBy": "Release Manager",
  "approvedAt": "2026-06-19T05:10:00Z",
  "overriddenCheckType": "port_readiness",
  "reason": "Port restriction waived for priority medical equipment shipment",
  "acceptedRisk": "Berth delay risk accepted by Release Manager"
}
```

---

### Assumption status lifecycle

Every assumption in the ledger moves through the same four states. This is separate from the case-stage lifecycle — it describes what happens to one ledger entry, not the whole case.

```text
VALID
  ↓ (owning stage re-enters)
SUPERSEDED            ← the old version, kept for audit history, never deleted
  +
PENDING_RECHECK        ← a new version is created the instant re-entry starts
  ↓ (owning stage completes its re-run)
VALID   (re-check passed)
  or
INVALID (re-check failed — stage hands case to Human Review or On Hold)
```

Rules:

```text
- Only one assumption per checkType is ever VALID or PENDING_RECHECK at a time.
- SUPERSEDED versions are append-only history — version numbers increment, nothing is overwritten.
- Normal Closure may only enter when every checkType's latest version is VALID.
- Override Closure may enter with exactly one INVALID assumption, only if that checkType
  is explicitly covered by approvedOverride (see §8.8, path B).
- Unresolved Closure may enter with INVALID assumptions only when the Release Manager
  approves ON_HOLD_UNRESOLVED after the business window (see §8.7, §8.8 path C).
- PENDING_RECHECK always blocks every Closure path, with no exception — a recheck must
  either finish (becoming VALID/INVALID) or be explicitly abandoned with a recorded
  reason before Closure can be entered.
- The Ledger Diff Agent is what flips VALID → SUPERSEDED + creates the PENDING_RECHECK
  version, at the moment a stage re-enters — not at the moment it completes.
```

---

## 5. Primary Case Stages

Primary stages are the normal case work areas.

```text
Document Intake
Document Verification
Party Validation
Port Readiness
Monitoring
Closure
```

The three readiness stages run independently after intake:

```text
Document Verification
Party Validation
Port Readiness
```

Each readiness stage owns one assumption:

```text
Document Verification → ASM-DOC
Party Validation → ASM-PARTY
Port Readiness → ASM-PORT
```

---

## 6. Exception Case Stages

Exception stages are activated only when needed.

```text
Human Review
On Hold
Cancelled
```

### Interrupting behavior

| Stage | Interrupting? | Reason |
|---|---:|---|
| Human Review | No | A possible party match or missing document should not stop unrelated checks from continuing. |
| On Hold | Yes | Confirmed risk or port restriction blocks release. |
| Cancelled | Yes | Voyage withdrawn means the case exits. |

---

## 7. Stage Definitions

---

## 7.1 Document Intake

### Owner persona

```text
Documentation Analyst
```

### Invokes

```text
UiPath IDP
Document Packet Builder
```

### Entry rule

```text
WHEN case is created
```

### Re-entry rule

```text
WHEN document_amended event arrives
```

On re-entry, Document Intake re-runs IDP extraction against the new document version and
rebuilds the document packet. It does not skip straight to Document Verification — amended
fields must be re-extracted before they can be re-checked. Once the packet is rebuilt,
Document Intake raises `document_packet_updated` — that is the event downstream stages
actually listen for, not the raw `document_amended` event, which avoids a race where
Document Verification could re-enter before the new packet exists.

### Completion rule

Complete when:

```text
- BOL extracted
- voyage_id exists
- vessel_name exists
- consignee_name exists
- destination_port_code exists
- document_packet created
```

### Handover

On success, activate these stages:

```text
Document Verification
Party Validation
Port Readiness
```

On low confidence or missing mandatory extraction fields:

```text
Human Review
```

On amended BOL for an existing case:

```text
Document Intake re-entry (re-extraction)
→ on completion, Document Intake raises document_packet_updated
→ Document Verification re-enters on document_packet_updated
→ Port Readiness re-entry also fires if destination_port_code changed in the new extraction
→ Party Validation re-entry also fires if shipper_name, consignee_name, or vessel_operator
  changed in the new extraction (Document Intake raises party_name_changed in this case)
```

---

## 7.2 Document Verification

### Owner persona

```text
Documentation Analyst
```

### Invokes

```text
Verification Agent
```

### Entry rule

```text
WHEN Document Intake completes
```

### Re-entry rule

```text
WHEN document_packet_updated event arrives
OR certificate_requirement_changed event arrives
```

`document_packet_updated` is raised by Document Intake only after re-extraction completes
and the packet is rebuilt — Document Verification does not listen to raw `document_amended`
directly, so it can never run against a stale or not-yet-rebuilt packet.

### Completion rule

Complete when the Verification Agent creates or updates the latest document assumption.

### Output assumption

```json
{
  "assumptionId": "ASM-DOC",
  "checkType": "document_completeness",
  "ownerStage": "Document Verification",
  "status": "VALID",
  "dependsOn": [
    "document_fields",
    "certificate_list"
  ]
}
```

### Handover rules

```text
IF status = VALID
THEN stage completes, ASM-DOC becomes VALID

IF status = FAILED
THEN ASM-DOC becomes INVALID, route to Human Review

IF issue is blocking and cannot be resolved
THEN On Hold
```

---

## 7.3 Party Validation

### Owner persona

```text
Trade Compliance Analyst
```

### Invokes

```text
Party Validation Agent
```

### Entry rule

```text
WHEN Document Intake completes
```

### Re-entry rule

```text
WHEN party_name_changed event arrives
OR party_validation_list_updated event arrives
```

### Completion rule

Complete when Party Validation Agent returns one of:

```text
CLEAR
POSSIBLE_MATCH
CONFIRMED_MATCH
```

### Handover rules

```text
CLEAR
→ stage completes with ASM-PARTY VALID

POSSIBLE_MATCH
→ Human Review
(ASM-PARTY stays PENDING_RECHECK until Human Review submits a decision)

CONFIRMED_MATCH
→ ASM-PARTY becomes INVALID
→ On Hold
```

### Thresholds

```text
score < 0.30
→ CLEAR

0.30 <= score < 0.75
→ POSSIBLE_MATCH

score >= 0.75
→ CONFIRMED_MATCH
```

---

## 7.4 Port Readiness

### Owner persona

```text
Port Operations Analyst
```

### Invokes

```text
RPA Port Status Tool
```

### Entry rule

```text
WHEN Document Intake completes
```

### Re-entry rule

```text
WHEN port_status_change event arrives
IF event.portCode == voyage.destinationPortCode
```

Also re-enter when:

```text
WHEN destination_port_changed event arrives
```

### Completion rule

Complete when the RPA Port Status Tool returns the latest readiness result.

### Handover rules

```text
OPEN
→ stage completes with ASM-PORT VALID

RESTRICTED
→ ASM-PORT becomes INVALID
→ On Hold

CLOSED
→ ASM-PORT becomes INVALID
→ On Hold
```

---

## 7.5 Monitoring

### Owner persona

```text
Voyage Coordinator
```

### Invokes

```text
Wait for Connector Event
Port status listener
Party list update listener
Amended document listener
```

### Entry rule

```text
WHEN Document Verification, Party Validation, and Port Readiness are complete
AND latest ASM-DOC status = VALID
AND latest ASM-PARTY status = VALID
AND latest ASM-PORT status = VALID
```

### Completion rule

Monitoring does not complete normally.

It exits when:

```text
- event arrives
- release decision is ready
- voyage is withdrawn
```

### Event routing

```text
port_status_change
→ Port Readiness re-enters

party_validation_list_updated
→ Party Validation re-enters

document_amended
→ Document Intake re-enters (re-extraction)
→ document_packet_updated event raised on completion
→ Document Verification re-enters on document_packet_updated
→ Port Readiness re-enters if destination_port_code changed in the new extraction
→ Party Validation re-enters if shipper_name, consignee_name, or vessel_operator changed

destination_port_changed
→ Port Readiness re-enters

planned_release_ready
→ Closure
```

---

## 7.6 Human Review

### Owner persona

Depends on issue type.

| Issue | Owner persona |
|---|---|
| Missing document | Documentation Analyst |
| Possible party match | Trade Compliance Analyst |
| Port override request | Port Operations Analyst / Release Manager |
| SLA breach | Compliance Manager |
| Unmapped event | Voyage Coordinator |

### Invokes

```text
Human task
Release Coordinator summary
```

### Entry rules

```text
WHEN Document Verification returns FAILED
OR Party Validation returns POSSIBLE_MATCH
OR IDP confidence is below threshold
OR event cannot be mapped
OR SLA breach requires escalation
```

### Completion rule

Complete when human decision is submitted.

### Allowed decisions

```text
CLEAR
HOLD
REQUEST_MORE_INFO
CANCEL
OVERRIDE_RELEASE
```

### Handover rules

```text
CLEAR
→ return to relevant readiness stage or Monitoring

REQUEST_MORE_INFO
→ Document Intake

HOLD
→ On Hold

CANCEL
→ Cancelled

OVERRIDE_RELEASE
→ the human reviewer who owns this Human Review instance (Documentation Analyst,
  Trade Compliance Analyst, or Port Operations Analyst — see §8.6's issue-type table)
  may only request an override; they cannot approve one
→ Release Manager must separately approve and populate approvedOverride on the case entity
  (only valid for document_completeness or port_readiness checkTypes — a CONFIRMED_MATCH
  party result is never reachable from Human Review, since it routes straight to On Hold)
→ Closure (path B — RELEASED_WITH_OVERRIDE)
```

---

## 7.7 On Hold

### Owner persona

```text
Release Manager
```

### Escalation persona

```text
Compliance Manager
```

### Invokes

```text
Release Coordinator Agent
Wait for Connector Event — port status listener (scoped to this stage)
Wait for Connector Event — compliance clearance listener (scoped to this stage)
Optional human override task
```

### Why On Hold needs its own listeners

On Hold is `interrupting = true`, which means it takes over the case and Monitoring's
listeners are not active while On Hold owns it. The resolving event (port reopens, or
compliance clears the match) has to be heard by a listener that belongs to On Hold itself,
not assumed to still be running underneath it from Monitoring.

### Re-entry / resolution rules

```text
WHEN port_status_change event arrives IF event.status == "OPEN"
→ exit On Hold, Port Readiness re-enters

WHEN compliance_clearance event arrives IF Compliance Manager has cleared ASM-PARTY
→ exit On Hold, Party Validation re-enters
```

### Entry rules

```text
WHEN Party Validation returns CONFIRMED_MATCH
OR Port Readiness returns RESTRICTED
OR Port Readiness returns CLOSED
OR human reviewer chooses HOLD
```

### Completion rule

Complete when:

```text
- blocking condition is resolved
OR override is approved
OR voyage is cancelled
OR Release Manager closes the case unresolved (see below)
```

### Business window for unresolved closure

```text
WHEN On Hold has been active for more than 48 hours
AND the blocking condition is still unresolved
THEN Release Manager may close the case as ON_HOLD_UNRESOLVED instead of waiting further
```

This is a Release Manager decision, never automatic — the 48-hour mark only makes the
option available and triggers an SLA notification (see §13); it does not force closure.

### Handover rules

```text
Port reopens
→ Port Readiness re-enters

Compliance clears hold
→ Party Validation re-enters
→ ASM-PARTY becomes VALID on completion
→ Monitoring, or Closure if release decision is otherwise ready
  (never Closure directly — Closure requires ASM-PARTY's latest version to already be VALID)

Override approved
→ Release Manager populates approvedOverride on the case entity
→ Closure (path B — RELEASED_WITH_OVERRIDE)

Release Manager closes unresolved beyond business window
→ unresolved reason recorded on the case entity
→ Closure (path C — ON_HOLD_UNRESOLVED)

Voyage withdrawn
→ Cancelled
```

---

## 7.8 Closure

### Owner persona

```text
Release Manager
```

### Invokes

```text
Release Coordinator Agent
Cost Impact Tool
Closure Record Writer
```

### Entry rule

Closure may enter via one of three paths:

```text
A) Normal release (releaseOutcome = RELEASED)
- latest ASM-DOC status = VALID
- latest ASM-PARTY status = VALID
- latest ASM-PORT status = VALID
- no assumption is PENDING_RECHECK
- no open Human Review task exists
- no active On Hold stage exists

B) Override release (releaseOutcome = RELEASED_WITH_OVERRIDE)
- approvedOverride exists and is populated by a Release Manager action
- the checkType named in approvedOverride.overriddenCheckType is the only one
  whose latest assumption is INVALID — every other checkType's latest assumption is VALID
- no assumption is PENDING_RECHECK
- no open Human Review task exists
- no active On Hold stage exists

C) Unresolved closure (releaseOutcome = ON_HOLD_UNRESOLVED)
- case has been in On Hold beyond the allowed business window
- Release Manager has explicitly approved closing without release
- unresolved reason is recorded on the case entity
- no assumption is PENDING_RECHECK (rechecks, if any, must finish or be abandoned
  with reason before this path is taken)
```

A `CONFIRMED_MATCH` party result can never be overridden through path B — only
`port_readiness` or `document_completeness` checkTypes are eligible for
`approvedOverride`, since a confirmed sanctions/denied-party match is a hard stop by
design, not a risk a Release Manager can accept on the case's behalf.

### Completion rule

Complete when:

```text
- releaseOutcome is set
- final ledger version is stored
- cost impact is calculated
- closure record is written
- Release Manager approves
```

### Closure record

```json
{
  "caseId": "VOY-2026-0417",
  "finalStatus": "RELEASED",
  "closedAt": "2026-06-19T05:30:00Z",
  "finalLedgerVersion": 4,
  "finalAssumptions": [
    {
      "assumptionId": "ASM-DOC",
      "checkType": "document_completeness",
      "status": "VALID"
    },
    {
      "assumptionId": "ASM-PARTY",
      "checkType": "party_validation",
      "status": "VALID"
    },
    {
      "assumptionId": "ASM-PORT-r3",
      "checkType": "port_readiness",
      "status": "VALID"
    }
  ],
  "costImpact": {
    "actualCostOfDelayUsd": 3791.67,
    "estimatedFullRerunCostUsd": 10500.0,
    "selectiveRecheckSavingsUsd": 6708.33,
    "selectiveRecheckSavingsHours": 5.75
  },
  "closedBy": "ReleaseCoordinatorAgent"
}
```

### Closure record — override variant

```json
{
  "caseId": "VOY-2026-0417",
  "finalStatus": "RELEASED_WITH_OVERRIDE",
  "closedAt": "2026-06-19T05:30:00Z",
  "finalLedgerVersion": 4,
  "finalAssumptions": [
    { "assumptionId": "ASM-DOC", "checkType": "document_completeness", "status": "VALID" },
    { "assumptionId": "ASM-PARTY", "checkType": "party_validation", "status": "VALID" },
    { "assumptionId": "ASM-PORT-r3", "checkType": "port_readiness", "status": "INVALID" }
  ],
  "approvedOverride": {
    "overrideId": "OVR-PORT-001",
    "approvedBy": "Release Manager",
    "approvedAt": "2026-06-19T05:10:00Z",
    "overriddenCheckType": "port_readiness",
    "reason": "Port restriction waived for priority medical equipment shipment",
    "acceptedRisk": "Berth delay risk accepted by Release Manager"
  },
  "costImpact": {
    "actualCostOfDelayUsd": 3791.67,
    "estimatedFullRerunCostUsd": 10500.0,
    "selectiveRecheckSavingsUsd": 6708.33,
    "selectiveRecheckSavingsHours": 5.75
  },
  "closedBy": "ReleaseCoordinatorAgent"
}
```

---

## 7.9 Cancelled

### Owner persona

```text
Voyage Coordinator
```

### Invokes

```text
Closure Record Writer (cancellation variant)
```

### Entry rules

```text
WHEN Voyage.status changes IF Voyage.status == "Withdrawn"
OR human reviewer chooses CANCEL in Human Review
OR Release Manager chooses CANCEL while On Hold
```

### Interrupting

```text
true — takes over the case immediately, same as On Hold.
```

### Completion rule

Complete when:

```text
- releaseOutcome is set to CANCELLED
- final ledger version is stored as-is (no further rechecks run)
- closure record is written with finalStatus = CANCELLED
```

### Closure record (cancellation variant)

```json
{
  "caseId": "VOY-2026-0417",
  "finalStatus": "CANCELLED",
  "closedAt": "2026-06-19T05:30:00Z",
  "cancelledFromStage": "On Hold",
  "cancellationReason": "Voyage withdrawn by shipper",
  "finalLedgerVersion": 3,
  "closedBy": "VoyageCoordinator"
}
```

Cancelled is a terminal stage — no stage re-enters after Cancelled, and the case completes
immediately once the closure record is written.

---

## 8. Full Handover Map

```text
CASE_CREATED
→ Document Intake

Document Intake
→ Document Verification
→ Party Validation
→ Port Readiness

Document Verification
→ Human Review if failed
→ complete if valid

Party Validation
→ Human Review if possible match
→ On Hold if confirmed match
→ complete if clear

Port Readiness
→ On Hold if restricted or closed
→ complete if open

All three readiness stages complete and valid
→ Monitoring

Monitoring receives port_status_change
→ Port Readiness re-enters

Monitoring receives party_validation_list_updated
→ Party Validation re-enters

Monitoring receives document_amended
→ Document Intake re-enters for re-extraction
→ Document Intake raises document_packet_updated on completion
→ Document Verification re-enters on document_packet_updated
→ Port Readiness re-enters if destination_port_code changed in the new extraction
→ Party Validation re-enters if shipper_name, consignee_name, or vessel_operator changed

Monitoring receives destination_port_changed
→ Port Readiness re-enters

Human Review
→ relevant readiness stage / Monitoring / On Hold / Closure / Cancelled

On Hold
→ relevant readiness stage / Human Review / Closure / Cancelled

Closure
→ Case complete
```

---

## 9. Event-to-Re-entry Rules

| Event | Affected source | Re-entered stage | Reason |
|---|---|---|---|
| `port_status_change` | `port_status` | Port Readiness | ASM-PORT depends on port status. |
| `destination_port_changed` | `destination_port` | Port Readiness | Destination affects which port must be checked. |
| `party_name_changed` | `party_names` | Party Validation | Party names affect party validation. |
| `party_validation_list_updated` | `party_validation_list_version` | Party Validation | The validation evidence source changed. |
| `document_amended` | `document_fields` | Document Intake (re-extraction) → raises `document_packet_updated` → Document Verification | A new document version must be re-extracted before its fields can be re-checked; Document Verification never listens to the raw event directly. |
| `certificate_requirement_changed` | `certificate_list` | Document Verification | Required certificate rules changed. |

---

## 10. Coded Agents

With native stage re-entry handling the primary routing, Meridian uses coded agents only where code is genuinely justified.

---

## 10.1 Party Validation Agent

### Type

```text
Coded Agent — Python SDK
```

### Purpose

Validate shipper, consignee, and vessel operator against a controlled party validation list using deterministic fuzzy matching.

### Why coded

```text
- threshold-based classification
- deterministic matching
- unit-testable logic
- auditable scoring
- operational consequences for false positives and false negatives
```

### Outputs

```text
CLEAR
POSSIBLE_MATCH
CONFIRMED_MATCH
```

---

## 10.2 Ledger Diff Agent

### Type

```text
Coded Agent — Python SDK
```

### Purpose

Create auditable ledger versioning and before/after diffs whenever a stage re-enters or completes after re-entry.

### What it does

```text
1. Reads previous assumption version.
2. On stage re-entry: marks the old VALID assumption as SUPERSEDED, creates a new
   version with status PENDING_RECHECK.
3. On stage completion after re-entry: updates that new version to VALID or INVALID
   based on the latest stage output.
4. Produces before/after diff.
5. Writes audit-friendly summary to case history.
```

### What it does not do

```text
It does not decide which stage re-enters.
Native Maestro Case re-entry rules do that.
```

### Example diff output

```json
{
  "caseId": "VOY-2026-0417",
  "eventId": "EVT-PORT-001",
  "stage": "Port Readiness",
  "changedAssumption": "ASM-PORT",
  "before": {
    "assumptionId": "ASM-PORT",
    "status": "VALID",
    "evidenceRef": "port_status_lookup_2026-06-18T09:20Z"
  },
  "after": {
    "assumptionId": "ASM-PORT-r2",
    "status": "INVALID",
    "evidenceRef": "port_status_lookup_2026-06-19T02:46Z"
  },
  "summary": "Port Readiness was re-entered because AEJEA changed from OPEN to RESTRICTED. Document Verification and Party Validation were not re-entered."
}
```

---

## 11. Low-Code Agents and Tools

## 11.1 Verification Agent

### Type

```text
Low-code Agent Builder agent
```

### Purpose

Check document completeness, BOL/manifest consistency, certificate completeness, and basic release-readiness fields.

### Owns assumption

```text
ASM-DOC
```

---

## 11.2 Release Coordinator Agent

### Type

```text
Low-code Agent Builder agent
```

### Purpose

Summarize final release status, open tasks, assumption history, hold reason, and closure recommendation.

### Important boundary

It does not calculate cost itself.

It calls:

```text
Cost Impact Tool
```

---

## 11.3 RPA Port Status Tool

### Type

```text
UiPath RPA workflow exposed as tool / connector
```

### Purpose

Read destination port status and return readiness result.

### Owns assumption

```text
ASM-PORT
```

---

## 11.4 Cost Impact Tool

### Type

```text
Deterministic API workflow / Execute Connector task
```

### Purpose

Calculate delay cost and avoided full-rerun cost.

### Input

```json
{
  "caseId": "VOY-2026-0417",
  "holdDurationHours": 3.25,
  "fullRerunDurationHours": 9.0,
  "dailyCharterRateUsd": 28000
}
```

### Output

```json
{
  "caseId": "VOY-2026-0417",
  "actualCostOfDelayUsd": 3791.67,
  "estimatedFullRerunCostUsd": 10500.0,
  "selectiveRecheckSavingsUsd": 6708.33,
  "selectiveRecheckSavingsHours": 5.75,
  "computedBy": "cost_impact_tool"
}
```

---

## 12. SLAs and Escalation

| Level | SLA | Escalation |
|---|---|---|
| Case | Resolve within 24 hours of case open | Notify Voyage Coordinator at risk, Release Manager on breach. |
| Human Review | Complete within 4 business hours | Reassign to Compliance Manager on breach. |
| On Hold | Review every 8 hours | Notify Compliance Manager and Release Manager. |
| On Hold (unresolved threshold) | 48 hours | Notify Release Manager that ON_HOLD_UNRESOLVED closure becomes available; does not auto-close. |
| Port Readiness re-entry | Complete within 20 minutes | Escalate to Port Operations Lead. |

### SLA behavior

```text
SLA timers pause when the case is waiting on an external party.
SLA timers resume when action becomes possible again.
```

---

## 13. Final Architecture Summary

```text
One Voyage Case
↓
Document Intake
↓
Three independent readiness stages:
  - Document Verification
  - Party Validation
  - Port Readiness
↓
Monitoring
↓
Evidence-change event
↓
Only matching stage re-enters
↓
Ledger Diff Agent records audit trail
↓
Human Review or On Hold if needed
↓
Closure with Cost Impact
```
