# tasks.md — VoyageRelease

**Source:** `/solution/VoyageRelease/sdd.md` (final approved revision)
**Registry resolutions:** `/solution/VoyageRelease/tasks/registry-resolved.json`

Per-T-entry build plan for the Phase 2 Prototyping → Phase 3 Implementation → Phase 4 Validate phases. Every declaration in the SDD is mirrored 1-to-1 by a T-entry here; rule-type defaults and "implicit behavior" do NOT collapse to omissions.

## Inventory

| Class | Source in sdd.md | T-entry section | Count |
|---|---|---|---|
| Case file | §1 Case Metadata | §1 | 1 (T01) |
| Triggers | §1 Case Triggers | §2 | 1 (T02) |
| Variables / arguments | §1 Case Variables | §3 | 28 (T03–T30) |
| Stages | §2 Stage headings | §4 | 9 (T31–T39) |
| Tasks | §2 per-stage Tasks tables | §5 | 9 (T40–T48) |
| Conditions | §2 entry/exit + §1 case exit | §6 | 44 (T49–T92) |
| SLA | §1 Case-Level SLA + escalations | §7 | 3 (T93–T95) |
| **Total** | | | **95** |

Final cross-check counts are confirmed at the bottom of this file after all T-entries are written.

---

## Section 1 — Case file

### T01: Create case file "VoyageRelease"
- name: VoyageRelease
- file-path: caseplan.json
- description: "Reviews and approves the release of a maritime voyage. Verifies the five shipping documents, screens shipper / consignee / vessel operator against denied-party lists, confirms destination port readiness, and routes flagged items through human review before issuing a release outcome."
- identifier-type: constant
- case-identifier: VOY
- priority-choiceset: [Low, Medium, High, Critical]
- priority-default: Medium
- case-app-enabled: true
- case-directly-pass-task-outputs: Direct
- order: first
- verify: caseplan.json created with root case node; identifier-type=constant, prefix=VOY; case-app enabled; default priority Medium

---

## Section 2 — Triggers (T02+)

### T02: Configure event trigger "Voyage record created"
- display-name: "Voyage record created"
- description: "Fires whenever a new MeridianCase entity record is created in UiPath Data Fabric. The trigger reuses the existing MeridianCase entity (rather than minting a new VoyageRelease entity) per user direction."
- type-id: af2a53ad-5d90-3d4e-bf3c-55b6d91595cd
- connection-id: 340a34eb-b132-42ae-9efc-95c151a40b54
- folder-key: 19901aa0-a2af-4d48-851e-de9ae597df07
- connector-key: uipath-uipath-dataservice
- object-name: MeridianCase
- event-operation: CREATED
- event-mode: webhooks
- service-type: Intsvc.EventTrigger
- input-values: {}
- filter: —
- order: after T01
- verify: Trigger node appended to nodes[]; entry-points.json carries the matching entry; capture TriggerId

> **Review item carried from registry-resolved.json:** Both MeridianCase and VoyageRelease cases will fire on the same MeridianCase entity record creation (each new record spawns one case of each kind). User confirmed reuse over minting a new VoyageRelease entity in Data Fabric.

---

## Section 3 — Variables and Arguments (T03–T30)

> Trigger-payload paths follow the SDD. `destinationPortCode`/`shipper`/`consignee`/`vesselOperator` are dotted into `response.parties.*` because four distinct case variables cannot share a single sourceFields path — see "Not Covered" at the bottom of this file for an entity-schema-verification note.

### T03: Declare variable "caseId"
- name: caseId
- category: Variable
- type: string
- default: —
- source-triggers: T02
- source-fields: response.caseId
- description: External case id supplied by the trigger record.
- order: after T02
- verify: Variable added; sourceTriggers references T02

### T04: Declare variable "vesselName"
- name: vesselName
- category: Variable
- type: string
- default: —
- source-triggers: T02
- source-fields: response.voyage
- description: Vessel name carried in the trigger payload's `voyage` field on the MeridianCase entity.
- order: after T03
- verify: Variable added; sourceTriggers references T02

### T05: Declare variable "voyageNumber"
- name: voyageNumber
- category: Variable
- type: string
- default: —
- source-triggers: T02
- source-fields: response.externalKey
- description: Voyage number carried in the trigger payload's `externalKey` field on the MeridianCase entity.
- order: after T04
- verify: Variable added; sourceTriggers references T02

### T06: Declare variable "destinationPortCode"
- name: destinationPortCode
- category: Variable
- type: string
- default: —
- source-triggers: T02
- source-fields: response.parties.destinationPortCode
- description: Destination port code; sub-field of the entity's `parties` slot.
- order: after T05
- verify: Variable added; sourceTriggers references T02

### T07: Declare variable "shipper"
- name: shipper
- category: Variable
- type: string
- default: —
- source-triggers: T02
- source-fields: response.parties.shipper
- description: Shipper name; sub-field of the entity's `parties` slot.
- order: after T06
- verify: Variable added; sourceTriggers references T02

### T08: Declare variable "consignee"
- name: consignee
- category: Variable
- type: string
- default: —
- source-triggers: T02
- source-fields: response.parties.consignee
- description: Consignee name; sub-field of the entity's `parties` slot.
- order: after T07
- verify: Variable added; sourceTriggers references T02

### T09: Declare variable "vesselOperator"
- name: vesselOperator
- category: Variable
- type: string
- default: —
- source-triggers: T02
- source-fields: response.parties.vesselOperator
- description: Vessel operator name; sub-field of the entity's `parties` slot.
- order: after T08
- verify: Variable added; sourceTriggers references T02

### T10: Declare variable "bolDocument"
- name: bolDocument
- category: Variable
- type: file
- default: —
- source-triggers: T02
- source-fields: response.bolDocument
- description: Bill of Lading attachment from the trigger record.
- order: after T09
- verify: Variable added; type=file; sourceTriggers references T02

### T11: Declare variable "cargoManifestDocument"
- name: cargoManifestDocument
- category: Variable
- type: file
- default: —
- source-triggers: T02
- source-fields: response.cargoManifestDocument
- description: Cargo manifest attachment from the trigger record.
- order: after T10
- verify: Variable added; type=file

### T12: Declare variable "certificateOfOriginDocument"
- name: certificateOfOriginDocument
- category: Variable
- type: file
- default: —
- source-triggers: T02
- source-fields: response.certificateOfOriginDocument
- description: Certificate of Origin attachment from the trigger record.
- order: after T11
- verify: Variable added; type=file

### T13: Declare variable "insuranceCertificateDocument"
- name: insuranceCertificateDocument
- category: Variable
- type: file
- default: —
- source-triggers: T02
- source-fields: response.insuranceCertificateDocument
- description: Insurance certificate attachment from the trigger record.
- order: after T12
- verify: Variable added; type=file

### T14: Declare variable "qualityCertificateDocument"
- name: qualityCertificateDocument
- category: Variable
- type: file
- default: —
- source-triggers: T02
- source-fields: response.qualityCertificateDocument
- description: Quality certificate attachment from the trigger record.
- order: after T13
- verify: Variable added; type=file

### T15: Declare variable "docResult"
- name: docResult
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Document Verification outcome — `PASS`, `FAIL`, or `REVIEW`. Written by Run VerificationAgent task; read by Document Verification stage exits and Document Review entry.
- order: after T14
- verify: Variable added; no trigger source (producer is Task T41 Run VerificationAgent)

### T16: Declare variable "docComment"
- name: docComment
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: One-sentence rationale produced by VerificationAgent; surfaced in the closure summary.
- order: after T15
- verify: Variable added

### T17: Declare variable "flaggedDocument"
- name: flaggedDocument
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: When `docResult == "REVIEW"`, the key of the document the reviewer must re-upload (one of `bolDocument`, `cargoManifestDocument`, `certificateOfOriginDocument`, `insuranceCertificateDocument`, `qualityCertificateDocument`). Cleared on every Document Intake activation.
- order: after T16
- verify: Variable added

### T18: Declare variable "partyResult"
- name: partyResult
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Party Validation outcome — `PASS`, `FAIL`, or `REVIEW`. Written by Run PartyValidationAgent; read by Party Validation exits and Party Review entry.
- order: after T17
- verify: Variable added

### T19: Declare variable "partyComment"
- name: partyComment
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: One-sentence rationale produced by PartyValidationAgent.
- order: after T18
- verify: Variable added

### T20: Declare variable "partyScore"
- name: partyScore
- category: Variable
- type: float
- default: —
- source-triggers: —
- source-fields: —
- description: Worst denied-party score (0.0–1.0); 0.0 when CLEAR. Surfaced in the closure summary.
- order: after T19
- verify: Variable added; type=float

### T21: Declare variable "portResult"
- name: portResult
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Port Readiness outcome — `PASS`, `FAIL`, or `REVIEW`. Written by Run PortLookupTool; read by Port Readiness exits and Port Review entry.
- order: after T20
- verify: Variable added

### T22: Declare variable "portComment"
- name: portComment
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: One-sentence rationale produced by PortLookupTool.
- order: after T21
- verify: Variable added

### T23: Declare variable "reviewDecision"
- name: reviewDecision
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Reviewer decision on the active review lane — `APPROVE` or `REJECT`. Cleared by Run DUExtraction's `=`-output assignments on every Document Intake activation.
- order: after T22
- verify: Variable added

### T24: Declare variable "reviewComment"
- name: reviewComment
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Reviewer's free-text comment; surfaced in the closure summary. Cleared on Document Intake re-entry.
- order: after T23
- verify: Variable added

### T25: Declare variable "reviewOriginStage"
- name: reviewOriginStage
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Tag of whichever review lane fires (`"Party Validation"`, `"Port Readiness"`, `"Document Verification"`) so the closure summary can name which check produced the override.
- order: after T24
- verify: Variable added

### T26: Declare variable "partyOverride"
- name: partyOverride
- category: Variable
- type: boolean
- default: false
- source-triggers: —
- source-fields: —
- description: Per-lane flag set `true` only by Party Review APPROVE. Gates Party Validation's completion exit (`partyResult === "PASS" || partyOverride === true`) and suppresses its REVIEW divert on re-entry (`partyResult === "REVIEW" && partyOverride !== true`).
- order: after T25
- verify: Variable added; type=boolean; default=false

### T27: Declare variable "portOverride"
- name: portOverride
- category: Variable
- type: boolean
- default: false
- source-triggers: —
- source-fields: —
- description: Per-lane flag set `true` only by Port Review APPROVE. Gates Port Readiness's completion exit and suppresses its REVIEW divert on re-entry.
- order: after T26
- verify: Variable added; type=boolean; default=false

### T28: Declare variable "approvedOverride"
- name: approvedOverride
- category: Variable
- type: boolean
- default: false
- source-triggers: —
- source-fields: —
- description: Set `true` by ANY review lane's APPROVE (Party / Port / Document Review). Read ONLY by ReleaseCoordinatorAgent at Released for the `RELEASED` vs `RELEASED_WITH_OVERRIDE` decision. NOT used for gating — see `partyOverride` and `portOverride`.
- order: after T27
- verify: Variable added; type=boolean; default=false

### T29: Declare variable "closureSummary"
- name: closureSummary
- category: Variable
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Human-readable case summary written by ReleaseCoordinatorAgent in Released or Rejected.
- order: after T28
- verify: Variable added

### T30: Declare Out argument "releaseOutcome"
- name: releaseOutcome
- category: Out
- type: string
- default: —
- source-triggers: —
- source-fields: —
- description: Final outcome — `RELEASED`, `RELEASED_WITH_OVERRIDE`, or `REJECTED`. Written exactly once per case; the producer is the active terminal stage's task (Released's Write closure summary task OR Rejected's Write rejection summary task).
- producer: Task at Released or Rejected (via `=`-assignment output)
- order: after T29
- verify: Out-arg added to caseplan.json.variables.outputs[]; producer presence will be checked by the Phase 3 end-of-phase validator (Check 2)

---

## Section 4 — Stages (T31–T39)

### T31: Create stage "Document Intake"
- display-name: Document Intake
- stage-type: regular
- is-required: true
- description: Runs DUExtraction against the trigger record's five document attachments and emits a single `documentPacket` payload for downstream verification. Re-entered when Document Review approves a corrected document — DUExtraction's Outputs clear `reviewDecision` / `reviewComment` / `flaggedDocument` on every run so the next review lane starts clean. Override flags (`approvedOverride`, `partyOverride`, `portOverride`) are deliberately NOT cleared — they must persist for the lifetime of the case.
- order: after T30
- verify: Stage node appended; capture StageId; isRequired=true; stageType=regular

### T32: Create stage "Document Verification"
- display-name: Document Verification
- stage-type: regular
- is-required: true
- description: Runs VerificationAgent against the extracted `documentPacket`. The agent emits `docResult` (`PASS` / `FAIL` / `REVIEW`), a one-sentence `docComment`, and (when `REVIEW`) the `flaggedDocument` key the reviewer must re-upload. Completion gates on `PASS`; `FAIL` diverts to Rejected; `REVIEW` diverts to Document Review.
- order: after T31
- verify: Stage node appended; capture StageId

### T33: Create stage "Party Validation"
- display-name: Party Validation
- stage-type: regular
- is-required: true
- description: Runs PartyValidationAgent to screen shipper, consignee, and vessel operator against denied-party lists. Emits `partyResult` (`PASS` / `FAIL` / `REVIEW`), a one-sentence `partyComment`, and a 0.0–1.0 `partyScore`. Completion gates on `partyResult == "PASS"` OR `partyOverride === true`. The REVIEW divert is suppressed when `partyOverride === true` so re-entry from Party Review's `return-to-origin` does not re-route back to Party Review.
- order: after T32
- verify: Stage node appended; capture StageId

### T34: Create stage "Port Readiness"
- display-name: Port Readiness
- stage-type: regular
- is-required: true
- description: Runs the PortLookupTool API workflow to confirm the destination port is open for the voyage. Emits `portResult` (`PASS` / `FAIL` / `REVIEW`) and a one-sentence `portComment`. Completion gates on `PASS` OR `portOverride === true` (Port Review approved). REVIEW = port not in lookup / indeterminate; FAIL = explicitly denied port. Port Review lane reachable only on REVIEW.
- order: after T33
- verify: Stage node appended; capture StageId

### T35: Create stage "Released"
- display-name: Released
- stage-type: regular
- is-required: true
- description: Terminal happy-path stage. Runs ReleaseCoordinatorAgent to compose a one-sentence `closureSummary` from the verification, party, and port comments, then writes `releaseOutcome` — `RELEASED_WITH_OVERRIDE` when `approvedOverride === true`, otherwise `RELEASED`.
- order: after T34
- verify: Stage node appended; capture StageId

### T36: Create exception stage "Party Review"
- display-name: Party Review
- stage-type: exception
- is-required: false
- is-interrupting: true
- description: Human review lane that fires when `partyResult == "REVIEW"`. The reviewer decides APPROVE (case continues forward past Party Validation) or REJECT (case routes to Rejected). On APPROVE, the lane sets `partyOverride = true` and `approvedOverride = true`, then returns to Party Validation via `return-to-origin`. On REJECT, the lane routes directly to Rejected via `exit-only` — no override flag is written.
- order: after T35
- verify: Stage node appended as ExceptionStage; isInterrupting=true; capture StageId

### T37: Create exception stage "Port Review"
- display-name: Port Review
- stage-type: exception
- is-required: false
- is-interrupting: true
- description: Human review lane that fires when `portResult == "REVIEW"`. On APPROVE, sets `portOverride = true` and `approvedOverride = true`, returns to Port Readiness. On REJECT, routes directly to Rejected via `exit-only`.
- order: after T36
- verify: Stage node appended as ExceptionStage; isInterrupting=true; capture StageId

### T38: Create exception stage "Document Review"
- display-name: Document Review
- stage-type: exception
- is-required: false
- is-interrupting: true
- description: Human review lane that fires when `docResult == "REVIEW"`. The reviewer re-uploads the corrected document named in `flaggedDocument` and picks APPROVE or REJECT. APPROVE re-enters Document Intake via `exit-only` (forward route — NOT return-to-origin) so DUExtraction re-runs on the corrected file. REJECT routes to Rejected via `exit-only`. APPROVE sets `approvedOverride = true` (no per-lane override flag — Doc Review forward-routes, doesn't gate the originating stage).
- order: after T37
- verify: Stage node appended as ExceptionStage; isInterrupting=true; capture StageId

### T39: Create exception stage "Rejected"
- display-name: Rejected
- stage-type: exception
- is-required: false
- is-interrupting: true
- description: Terminal exception lane. Entered from any primary or review stage that produces a `FAIL` / `REJECT` signal (6 entry rules). Runs ReleaseCoordinatorAgent once to compose a closure summary, writes `releaseOutcome = "REJECTED"`, then exits the case via the case-exit on `selected-stage-completed("Rejected")`.
- order: after T38
- verify: Stage node appended as ExceptionStage; isInterrupting=true; capture StageId

---

## Section 5 — Tasks (T40–T48)

> Unresolved tasks (DUExtraction, PortLookupTool, all three action apps) follow planning.md §3.4: `taskTypeId: <UNRESOLVED: …>`, `inputs:` and `outputs:` omitted, wiring intent captured in a trailing fenced `text` block. Phase 2 emits placeholder task nodes; user wires real resources via Phase 3 re-entry or post-publish.

### T40: Add rpa task "Run DUExtraction" to "Document Intake"
- display-name: Run DUExtraction
- type: rpa
- stage: Document Intake
- taskTypeId: <UNRESOLVED: solution-project DUExtraction — bindings resolve at solution pack/deploy>
- resource-name: DUExtraction
- resource-folder: <UNRESOLVED — solution-bound>
- binding-sub-type: —
- isRequired: true
- runOnlyOnce: false
- lane: 0
- order: after T39
- verify: Task node appended to Document Intake stage; placeholder emitted; capture TaskId. Wiring deferred.

```text
wiring notes (user must attach):
  inputs:
    - caseId <= =metadata.ExternalId
  outputs:
    - documentpacket -> documentPacket
    - (=-assignments) reviewDecision = ""; reviewComment = ""; flaggedDocument = ""
```

> **Review item carried from registry-resolved.json:** DUExtraction not yet deployed/published. Phase 2 will bind via solution-project name+folder; runtime requires the RPA package to be deployed before the case can fire.

### T41: Add agent task "Run VerificationAgent" to "Document Verification"
- display-name: Run VerificationAgent
- type: agent
- stage: Document Verification
- taskTypeId: 965ac3e9-96b8-4d6c-a777-c6ec630618a3
- resource-name: VerificationAgent
- resource-folder: dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian
- resource-folder-key: 7c909ff8-2863-4066-8cbb-2d6dfeefbdbf
- process-key: Meridian.agent.VerificationAgent
- process-version: 1.0.0-debug.63918209397
- binding-sub-type: Agent
- isRequired: true
- runOnlyOnce: false
- lane: 0
- inputs:
  - field: documentPacket
    binding: =vars.documentPacket
- outputs:
  - field: docResult
    target: -> docResult
  - field: docComment
    target: -> docComment
  - field: flaggedDocument
    target: -> flaggedDocument
- order: after T40
- verify: Task node appended; taskTypeId bound to deployed agent; capture TaskId; full Phase 2 schema discovery via `uip maestro case tasks describe --type agent --id 965ac3e9-...`

### T42: Add agent task "Run PartyValidationAgent" to "Party Validation"
- display-name: Run PartyValidationAgent
- type: agent
- stage: Party Validation
- taskTypeId: de933600-26f3-45fb-8274-e75865599c4d
- resource-name: PartyValidationAgent
- resource-folder: dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian
- resource-folder-key: 7c909ff8-2863-4066-8cbb-2d6dfeefbdbf
- process-key: Meridian.agent.PartyValidationAgent
- process-version: 1.0.0-debug.63918209397
- binding-sub-type: Agent
- isRequired: true
- runOnlyOnce: true
- lane: 0
- inputs:
  - field: shipper
    binding: =vars.shipper
  - field: consignee
    binding: =vars.consignee
  - field: vessel_operator
    binding: =vars.vesselOperator
- outputs:
  - field: partyResult
    target: -> partyResult
  - field: partyComment
    target: -> partyComment
  - field: partyScore
    target: -> partyScore
- order: after T41
- verify: Task node appended; `runOnlyOnce: true` so Party Review return-to-origin skips the agent and re-evaluates the stage gate with `partyOverride`

### T43: Add api-workflow task "Run PortLookupTool" to "Port Readiness"
- display-name: Run PortLookupTool
- type: api-workflow
- stage: Port Readiness
- taskTypeId: <UNRESOLVED: solution-project PortLookupTool — bindings resolve at solution pack/deploy>
- resource-name: PortLookupTool
- resource-folder: <UNRESOLVED — solution-bound>
- binding-sub-type: Api
- isRequired: true
- runOnlyOnce: true
- lane: 0
- order: after T42
- verify: Task node appended as placeholder; capture TaskId; wiring deferred until PortLookupTool API workflow is deployed

```text
wiring notes (user must attach):
  inputs:
    - destinationPortCode <= =vars.destinationPortCode
  outputs:
    - portResult -> portResult
    - portComment -> portComment
```

> **Review item:** PortLookupTool not yet deployed. Phase 2 binds via solution-project name+folder; runtime requires the API workflow deployed before this stage fires.

### T44: Add agent task "Write closure summary" to "Released"
- display-name: Write closure summary
- type: agent
- stage: Released
- taskTypeId: 05a27308-2df8-49b0-89ce-cb2e15fbc20f
- resource-name: ReleaseCoordinatorAgent
- resource-folder: dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian
- resource-folder-key: 7c909ff8-2863-4066-8cbb-2d6dfeefbdbf
- process-key: Meridian.agent.ReleaseCoordinatorAgent
- process-version: 1.0.0-debug.63918209397
- binding-sub-type: Agent
- dispatch-operation: outcomeContext = "released"
- isRequired: true
- runOnlyOnce: true
- lane: 0
- inputs:
  - field: caseId
    binding: =metadata.ExternalId
  - field: docComment
    binding: =vars.docComment
  - field: partyComment
    binding: =vars.partyComment
  - field: portComment
    binding: =vars.portComment
  - field: reviewComment
    binding: =vars.reviewComment
  - field: approvedOverride
    binding: =vars.approvedOverride
  - field: outcomeContext
    binding: "released"
- outputs:
  - field: closureSummary
    target: -> closureSummary
  - field: (=-assignment)
    target: releaseOutcome = =js:(vars.approvedOverride === true ? "RELEASED_WITH_OVERRIDE" : "RELEASED")
- order: after T43
- verify: Task node appended; producer for Out-arg `releaseOutcome` declared via `=`-assignment output; Phase 3 end-of-phase Check 2 confirms producer presence

### T45: Add action task "Party reviewer decision" to "Party Review"
- display-name: Party reviewer decision
- type: action
- stage: Party Review
- taskTypeId: <UNRESOLVED: action-app PartyReviewApp not deployed in tenant>
- action-app-id: <UNRESOLVED>
- action-app-deployment-folder: <UNRESOLVED>
- action-type: PartyReview
- recipient: Role:Maritime Compliance Reviewer
- priority: High
- task-title: Review denied-party screening for this voyage
- isRequired: true
- runOnlyOnce: false
- lane: 0
- order: after T44
- verify: Task node appended as Rule-8 placeholder; capture TaskId; wiring deferred until PartyReviewApp deployed and registered

```text
wiring notes (user must attach):
  inputs (action-app input schema):
    - caseId <= =metadata.ExternalId
    - shipper <= =vars.shipper
    - consignee <= =vars.consignee
    - vesselOperator <= =vars.vesselOperator
    - partyResult <= =vars.partyResult
    - partyComment <= =vars.partyComment
    - partyScore <= =vars.partyScore
  outputs (action-app response):
    - Action -> reviewDecision
    - reviewComment -> reviewComment
    - (=-assignments)
        reviewOriginStage = "Party Validation"
        partyOverride = =js:(vars.reviewDecision === "APPROVE")
        approvedOverride = =js:(vars.reviewDecision === "APPROVE")
  actions (button mappings):
    - "Approve" -> reviewDecision = "APPROVE"
    - "Reject"  -> reviewDecision = "REJECT"
```

> **Review item:** PartyReviewApp not deployed. App must set `partyOverride = true` AND `approvedOverride = true` on APPROVE.

### T46: Add action task "Port reviewer decision" to "Port Review"
- display-name: Port reviewer decision
- type: action
- stage: Port Review
- taskTypeId: <UNRESOLVED: action-app PortReviewApp not deployed in tenant>
- action-app-id: <UNRESOLVED>
- action-app-deployment-folder: <UNRESOLVED>
- action-type: PortReview
- recipient: Role:Maritime Compliance Reviewer
- priority: High
- task-title: Review port readiness for this voyage
- isRequired: true
- runOnlyOnce: false
- lane: 0
- order: after T45
- verify: Task node appended as Rule-8 placeholder; capture TaskId; wiring deferred

```text
wiring notes (user must attach):
  inputs:
    - caseId <= =metadata.ExternalId
    - destinationPortCode <= =vars.destinationPortCode
    - portResult <= =vars.portResult
    - portComment <= =vars.portComment
  outputs:
    - Action -> reviewDecision
    - reviewComment -> reviewComment
    - (=-assignments)
        reviewOriginStage = "Port Readiness"
        portOverride = =js:(vars.reviewDecision === "APPROVE")
        approvedOverride = =js:(vars.reviewDecision === "APPROVE")
  actions:
    - "Approve" -> reviewDecision = "APPROVE"
    - "Reject"  -> reviewDecision = "REJECT"
```

> **Review item:** PortReviewApp not deployed. App must set `portOverride = true` AND `approvedOverride = true` on APPROVE.

### T47: Add action task "Document reviewer decision" to "Document Review"
- display-name: Document reviewer decision
- type: action
- stage: Document Review
- taskTypeId: <UNRESOLVED: action-app DocumentReviewApp not deployed in tenant>
- action-app-id: <UNRESOLVED>
- action-app-deployment-folder: <UNRESOLVED>
- action-type: DocumentReview
- recipient: Role:Maritime Compliance Reviewer
- priority: High
- task-title: Re-upload the flagged document
- isRequired: true
- runOnlyOnce: false
- lane: 0
- order: after T46
- verify: Task node appended as Rule-8 placeholder; capture TaskId; wiring deferred until DocumentReviewApp deployed with the required 5-slot output schema

```text
wiring notes (user must attach):
  inputs:
    - caseId <= =metadata.ExternalId
    - flaggedDocument <= =vars.flaggedDocument
    - docComment <= =vars.docComment
    - bolDocument <= =vars.bolDocument
    - cargoManifestDocument <= =vars.cargoManifestDocument
    - certificateOfOriginDocument <= =vars.certificateOfOriginDocument
    - insuranceCertificateDocument <= =vars.insuranceCertificateDocument
    - qualityCertificateDocument <= =vars.qualityCertificateDocument
  outputs (5 conditional document-slot outputs — app routes upload into matching slot, others emit null):
    - Action -> reviewDecision
    - reviewComment -> reviewComment
    - bolDocument -> bolDocument
    - cargoManifestDocument -> cargoManifestDocument
    - certificateOfOriginDocument -> certificateOfOriginDocument
    - insuranceCertificateDocument -> insuranceCertificateDocument
    - qualityCertificateDocument -> qualityCertificateDocument
    - (=-assignments)
        reviewOriginStage = "Document Verification"
        approvedOverride = =js:(vars.reviewDecision === "APPROVE")
  actions:
    - "Approve" -> reviewDecision = "APPROVE"
    - "Reject"  -> reviewDecision = "REJECT"
```

> **Review item:** DocumentReviewApp not deployed. App MUST expose 5 file output fields (one per document slot) and route the re-uploaded file into whichever matches `flaggedDocument` set by VerificationAgent. The other 4 emit null. App also sets `approvedOverride = true` on APPROVE — no per-lane flag (Doc Review forward-routes).

### T48: Add agent task "Write rejection summary" to "Rejected"
- display-name: Write rejection summary
- type: agent
- stage: Rejected
- taskTypeId: 05a27308-2df8-49b0-89ce-cb2e15fbc20f
- resource-name: ReleaseCoordinatorAgent
- resource-folder: dhananjay.mendgudli.sub@gmail.com's workspace/Debug_Meridian
- resource-folder-key: 7c909ff8-2863-4066-8cbb-2d6dfeefbdbf
- process-key: Meridian.agent.ReleaseCoordinatorAgent
- process-version: 1.0.0-debug.63918209397
- binding-sub-type: Agent
- dispatch-operation: outcomeContext = "rejected"
- isRequired: true
- runOnlyOnce: true
- lane: 0
- inputs:
  - field: caseId
    binding: =metadata.ExternalId
  - field: docComment
    binding: =vars.docComment
  - field: partyComment
    binding: =vars.partyComment
  - field: portComment
    binding: =vars.portComment
  - field: reviewComment
    binding: =vars.reviewComment
  - field: reviewOriginStage
    binding: =vars.reviewOriginStage
  - field: outcomeContext
    binding: "rejected"
- outputs:
  - field: closureSummary
    target: -> closureSummary
  - field: (=-assignment)
    target: releaseOutcome = "REJECTED"
- order: after T47
- verify: Task node appended; second producer for Out-arg `releaseOutcome` (writes "REJECTED" literal). Phase 3 Check 2 sees two producers (T44 + T48) for releaseOutcome — both write paths exist and the case satisfies the write-once contract because only one terminal stage fires per execution.

---

## Section 6 — Conditions (T49–T92)

> Order within §6 per planning.md §4.7: stage entry → stage exit → case exit → task entry.

### Section 6A — Stage entry conditions (T49–T63, 15 entries)

### T49: Add stage-entry condition for "Document Intake" (case-entered)
- scope: stage-entry
- target-stage: Document Intake
- rule-type: case-entered
- condition-expression: —
- interrupting: false
- display-name: Entry Rule 1
- order: after T48
- verify: Stage-entry condition appended to Document Intake.entryConditions; first stage of the case

### T50: Add stage-entry condition for "Document Intake" (re-entry from Document Review)
- scope: stage-entry
- target-stage: Document Intake
- rule-type: selected-stage-exited
- rule-target-stage: Document Review
- condition-expression: =js:(vars.reviewDecision === "APPROVE")
- interrupting: true
- display-name: Entry Rule 2
- order: after T49
- verify: Stage-entry condition appended; re-entry on Doc Review APPROVE so DUExtraction re-runs on the corrected file

### T51: Add stage-entry condition for "Document Verification"
- scope: stage-entry
- target-stage: Document Verification
- rule-type: selected-stage-completed
- rule-target-stage: Document Intake
- condition-expression: —
- interrupting: false
- display-name: Entry Rule 1
- order: after T50
- verify: Stage-entry condition appended; fires when Document Intake completes

### T52: Add stage-entry condition for "Party Validation"
- scope: stage-entry
- target-stage: Party Validation
- rule-type: selected-stage-completed
- rule-target-stage: Document Verification
- condition-expression: —
- interrupting: false
- display-name: Entry Rule 1
- order: after T51
- verify: Stage-entry condition appended

### T53: Add stage-entry condition for "Port Readiness"
- scope: stage-entry
- target-stage: Port Readiness
- rule-type: selected-stage-completed
- rule-target-stage: Party Validation
- condition-expression: —
- interrupting: false
- display-name: Entry Rule 1
- order: after T52
- verify: Stage-entry condition appended

### T54: Add stage-entry condition for "Released"
- scope: stage-entry
- target-stage: Released
- rule-type: selected-stage-completed
- rule-target-stage: Port Readiness
- condition-expression: —
- interrupting: false
- display-name: Entry Rule 1
- order: after T53
- verify: Stage-entry condition appended

### T55: Add stage-entry condition for "Party Review" (interrupting on REVIEW)
- scope: stage-entry
- target-stage: Party Review
- rule-type: selected-stage-exited
- rule-target-stage: Party Validation
- condition-expression: =js:(vars.partyResult === "REVIEW")
- interrupting: true
- display-name: Entry Rule 1
- order: after T54
- verify: Stage-entry condition appended; interrupting=true on ExceptionStage

### T56: Add stage-entry condition for "Port Review" (interrupting on REVIEW)
- scope: stage-entry
- target-stage: Port Review
- rule-type: selected-stage-exited
- rule-target-stage: Port Readiness
- condition-expression: =js:(vars.portResult === "REVIEW")
- interrupting: true
- display-name: Entry Rule 1
- order: after T55
- verify: Stage-entry condition appended; interrupting=true

### T57: Add stage-entry condition for "Document Review" (interrupting on REVIEW)
- scope: stage-entry
- target-stage: Document Review
- rule-type: selected-stage-exited
- rule-target-stage: Document Verification
- condition-expression: =js:(vars.docResult === "REVIEW")
- interrupting: true
- display-name: Entry Rule 1
- order: after T56
- verify: Stage-entry condition appended; interrupting=true

### T58: Add stage-entry condition for "Rejected" (from Document Verification FAIL)
- scope: stage-entry
- target-stage: Rejected
- rule-type: selected-stage-exited
- rule-target-stage: Document Verification
- condition-expression: =js:(vars.docResult === "FAIL")
- interrupting: true
- display-name: Entry Rule 1
- order: after T57
- verify: Stage-entry condition appended; interrupting=true

### T59: Add stage-entry condition for "Rejected" (from Party Validation FAIL)
- scope: stage-entry
- target-stage: Rejected
- rule-type: selected-stage-exited
- rule-target-stage: Party Validation
- condition-expression: =js:(vars.partyResult === "FAIL")
- interrupting: true
- display-name: Entry Rule 2
- order: after T58
- verify: Stage-entry condition appended

### T60: Add stage-entry condition for "Rejected" (from Port Readiness FAIL)
- scope: stage-entry
- target-stage: Rejected
- rule-type: selected-stage-exited
- rule-target-stage: Port Readiness
- condition-expression: =js:(vars.portResult === "FAIL")
- interrupting: true
- display-name: Entry Rule 3
- order: after T59
- verify: Stage-entry condition appended

### T61: Add stage-entry condition for "Rejected" (from Party Review REJECT)
- scope: stage-entry
- target-stage: Rejected
- rule-type: selected-stage-exited
- rule-target-stage: Party Review
- condition-expression: =js:(vars.reviewDecision === "REJECT")
- interrupting: true
- display-name: Entry Rule 4
- order: after T60
- verify: Stage-entry condition appended

### T62: Add stage-entry condition for "Rejected" (from Port Review REJECT)
- scope: stage-entry
- target-stage: Rejected
- rule-type: selected-stage-exited
- rule-target-stage: Port Review
- condition-expression: =js:(vars.reviewDecision === "REJECT")
- interrupting: true
- display-name: Entry Rule 5
- order: after T61
- verify: Stage-entry condition appended

### T63: Add stage-entry condition for "Rejected" (from Document Review REJECT)
- scope: stage-entry
- target-stage: Rejected
- rule-type: selected-stage-exited
- rule-target-stage: Document Review
- condition-expression: =js:(vars.reviewDecision === "REJECT")
- interrupting: true
- display-name: Entry Rule 6
- order: after T62
- verify: Stage-entry condition appended

### Section 6B — Stage exit conditions (T64–T81, 18 entries)

### T64: Add stage-exit condition for "Document Intake" (Complete Rule 1)
- scope: stage-exit
- target-stage: Document Intake
- rule-type: required-tasks-completed
- condition-expression: —
- exit-type: exit-only
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T63
- verify: Stage-exit condition appended; stage completes when Run DUExtraction completes

### T65: Add stage-exit condition for "Document Verification" (Complete Rule 1, PASS)
- scope: stage-exit
- target-stage: Document Verification
- rule-type: required-tasks-completed
- condition-expression: =js:(vars.docResult === "PASS")
- exit-type: exit-only
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T64
- verify: Stage-exit condition appended; PASS gate

### T66: Add stage-exit condition for "Document Verification" (Exit Rule 1, FAIL → Rejected)
- scope: stage-exit
- target-stage: Document Verification
- rule-type: selected-tasks-completed
- rule-target-task: Run VerificationAgent
- condition-expression: =js:(vars.docResult === "FAIL")
- exit-type: exit-only
- exit-to-stage: Rejected
- marks-stage-complete: false
- display-name: Exit Rule 1
- order: after T65
- verify: Divert exit appended; FAIL routes to Rejected

### T67: Add stage-exit condition for "Document Verification" (Exit Rule 2, REVIEW → Document Review)
- scope: stage-exit
- target-stage: Document Verification
- rule-type: selected-tasks-completed
- rule-target-task: Run VerificationAgent
- condition-expression: =js:(vars.docResult === "REVIEW")
- exit-type: exit-only
- exit-to-stage: Document Review
- marks-stage-complete: false
- display-name: Exit Rule 2
- order: after T66
- verify: Divert exit appended; REVIEW routes to Document Review

### T68: Add stage-exit condition for "Party Validation" (Complete Rule 1, PASS or partyOverride)
- scope: stage-exit
- target-stage: Party Validation
- rule-type: required-tasks-completed
- condition-expression: =js:(vars.partyResult === "PASS" || vars.partyOverride === true)
- exit-type: exit-only
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T67
- verify: Completion exit appended; gate covers PASS or partyOverride==true (re-entry via Party Review APPROVE)

### T69: Add stage-exit condition for "Party Validation" (Exit Rule 1, FAIL → Rejected)
- scope: stage-exit
- target-stage: Party Validation
- rule-type: selected-tasks-completed
- rule-target-task: Run PartyValidationAgent
- condition-expression: =js:(vars.partyResult === "FAIL")
- exit-type: exit-only
- exit-to-stage: Rejected
- marks-stage-complete: false
- display-name: Exit Rule 1
- order: after T68
- verify: Divert exit appended

### T70: Add stage-exit condition for "Party Validation" (Exit Rule 2, REVIEW guarded → Party Review)
- scope: stage-exit
- target-stage: Party Validation
- rule-type: selected-tasks-completed
- rule-target-task: Run PartyValidationAgent
- condition-expression: =js:(vars.partyResult === "REVIEW" && vars.partyOverride !== true)
- exit-type: exit-only
- exit-to-stage: Party Review
- marks-stage-complete: false
- display-name: Exit Rule 2
- order: after T69
- verify: REVIEW divert guarded by partyOverride !== true so re-entry from Party Review return-to-origin does not loop back

### T71: Add stage-exit condition for "Port Readiness" (Complete Rule 1, PASS or portOverride)
- scope: stage-exit
- target-stage: Port Readiness
- rule-type: required-tasks-completed
- condition-expression: =js:(vars.portResult === "PASS" || vars.portOverride === true)
- exit-type: exit-only
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T70
- verify: Completion exit appended

### T72: Add stage-exit condition for "Port Readiness" (Exit Rule 1, FAIL → Rejected)
- scope: stage-exit
- target-stage: Port Readiness
- rule-type: selected-tasks-completed
- rule-target-task: Run PortLookupTool
- condition-expression: =js:(vars.portResult === "FAIL")
- exit-type: exit-only
- exit-to-stage: Rejected
- marks-stage-complete: false
- display-name: Exit Rule 1
- order: after T71
- verify: Divert exit appended

### T73: Add stage-exit condition for "Port Readiness" (Exit Rule 2, REVIEW guarded → Port Review)
- scope: stage-exit
- target-stage: Port Readiness
- rule-type: selected-tasks-completed
- rule-target-task: Run PortLookupTool
- condition-expression: =js:(vars.portResult === "REVIEW" && vars.portOverride !== true)
- exit-type: exit-only
- exit-to-stage: Port Review
- marks-stage-complete: false
- display-name: Exit Rule 2
- order: after T72
- verify: REVIEW divert guarded by portOverride !== true

### T74: Add stage-exit condition for "Released" (Complete Rule 1)
- scope: stage-exit
- target-stage: Released
- rule-type: required-tasks-completed
- condition-expression: —
- exit-type: exit-only
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T73
- verify: Completion exit appended; stage completes when Write closure summary completes (Required for Case Completion: Yes)

### T75: Add stage-exit condition for "Party Review" (Complete Rule 1, APPROVE return-to-origin)
- scope: stage-exit
- target-stage: Party Review
- rule-type: required-tasks-completed
- condition-expression: =js:(vars.reviewDecision === "APPROVE")
- exit-type: return-to-origin
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T74
- verify: return-to-origin appended; APPROVE returns to Party Validation; gate at Party Validation re-evaluates with partyOverride

### T76: Add stage-exit condition for "Party Review" (Exit Rule 1, REJECT → Rejected)
- scope: stage-exit
- target-stage: Party Review
- rule-type: selected-tasks-completed
- rule-target-task: Party reviewer decision
- condition-expression: =js:(vars.reviewDecision === "REJECT")
- exit-type: exit-only
- exit-to-stage: Rejected
- marks-stage-complete: false
- display-name: Exit Rule 1
- order: after T75
- verify: REJECT exit appended; routes directly to Rejected without setting any override flag

### T77: Add stage-exit condition for "Port Review" (Complete Rule 1, APPROVE return-to-origin)
- scope: stage-exit
- target-stage: Port Review
- rule-type: required-tasks-completed
- condition-expression: =js:(vars.reviewDecision === "APPROVE")
- exit-type: return-to-origin
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T76
- verify: return-to-origin appended

### T78: Add stage-exit condition for "Port Review" (Exit Rule 1, REJECT → Rejected)
- scope: stage-exit
- target-stage: Port Review
- rule-type: selected-tasks-completed
- rule-target-task: Port reviewer decision
- condition-expression: =js:(vars.reviewDecision === "REJECT")
- exit-type: exit-only
- exit-to-stage: Rejected
- marks-stage-complete: false
- display-name: Exit Rule 1
- order: after T77
- verify: REJECT exit appended

### T79: Add stage-exit condition for "Document Review" (Exit Rule 1, APPROVE → Document Intake)
- scope: stage-exit
- target-stage: Document Review
- rule-type: selected-tasks-completed
- rule-target-task: Document reviewer decision
- condition-expression: =js:(vars.reviewDecision === "APPROVE")
- exit-type: exit-only
- exit-to-stage: Document Intake
- marks-stage-complete: false
- display-name: Exit Rule 1
- order: after T78
- verify: Forward route exit appended; Document Review forward-routes (NOT return-to-origin) so DUExtraction re-runs on the corrected file. Both Document Review exits are Marks Complete: No — the stage routes via diverts and has no Yes-completion exit.

### T80: Add stage-exit condition for "Document Review" (Exit Rule 2, REJECT → Rejected)
- scope: stage-exit
- target-stage: Document Review
- rule-type: selected-tasks-completed
- rule-target-task: Document reviewer decision
- condition-expression: =js:(vars.reviewDecision === "REJECT")
- exit-type: exit-only
- exit-to-stage: Rejected
- marks-stage-complete: false
- display-name: Exit Rule 2
- order: after T79
- verify: REJECT exit appended

### T81: Add stage-exit condition for "Rejected" (Complete Rule 1)
- scope: stage-exit
- target-stage: Rejected
- rule-type: required-tasks-completed
- condition-expression: —
- exit-type: exit-only
- marks-stage-complete: true
- display-name: Complete Rule 1
- order: after T80
- verify: Completion exit appended; stage completes when Write rejection summary completes; case then exits via case-exit T83

### Section 6C — Case exit + Task entry conditions (T82–T92, 11 entries)

### T82: Add case-exit condition (Complete Rule 1, required-stages-completed)
- scope: case-exit
- target: case
- rule-type: required-stages-completed
- condition-expression: —
- exit-type: exit-only
- marks-case-complete: true
- display-name: Complete Rule 1
- order: after T81
- verify: Case-exit condition appended to metadata.caseExitRules; case completes when all required-for-completion stages have completed (i.e., the Released happy path)

### T83: Add case-exit condition (Exit Rule 1, alternate disposition on Rejected)
- scope: case-exit
- target: case
- rule-type: selected-stage-completed
- rule-target-stage: Rejected
- condition-expression: —
- exit-type: exit-only
- marks-case-complete: false
- display-name: Exit Rule 1
- order: after T82
- verify: Alternate disposition appended; case exits without "completing" when Rejected fires; Marks Case Complete = No (Rejected is not Required for Case Completion)

### T84: Add task-entry condition for "Run DUExtraction"
- scope: task-entry
- target-task: Run DUExtraction
- parent-stage: Document Intake
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T83
- verify: Task-entry condition appended; fires whenever Document Intake is entered (first time + re-entry via Document Review APPROVE)

### T85: Add task-entry condition for "Run VerificationAgent"
- scope: task-entry
- target-task: Run VerificationAgent
- parent-stage: Document Verification
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T84
- verify: Task-entry condition appended

### T86: Add task-entry condition for "Run PartyValidationAgent"
- scope: task-entry
- target-task: Run PartyValidationAgent
- parent-stage: Party Validation
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T85
- verify: Task-entry condition appended; task has runOnlyOnce=true so it's skipped on Party Review return-to-origin re-entry

### T87: Add task-entry condition for "Run PortLookupTool"
- scope: task-entry
- target-task: Run PortLookupTool
- parent-stage: Port Readiness
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T86
- verify: Task-entry condition appended; runOnlyOnce=true semantics same as T86

### T88: Add task-entry condition for "Write closure summary"
- scope: task-entry
- target-task: Write closure summary
- parent-stage: Released
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T87
- verify: Task-entry condition appended

### T89: Add task-entry condition for "Party reviewer decision"
- scope: task-entry
- target-task: Party reviewer decision
- parent-stage: Party Review
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T88
- verify: Task-entry condition appended

### T90: Add task-entry condition for "Port reviewer decision"
- scope: task-entry
- target-task: Port reviewer decision
- parent-stage: Port Review
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T89
- verify: Task-entry condition appended

### T91: Add task-entry condition for "Document reviewer decision"
- scope: task-entry
- target-task: Document reviewer decision
- parent-stage: Document Review
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T90
- verify: Task-entry condition appended

### T92: Add task-entry condition for "Write rejection summary"
- scope: task-entry
- target-task: Write rejection summary
- parent-stage: Rejected
- rule-type: current-stage-entered
- condition-expression: —
- display-name: Entry Rule 1
- order: after T91
- verify: Task-entry condition appended

---

## Section 7 — SLA and escalation (T93–T95)

### T93: Set case-level SLA
- target: case
- sla-type: time-based
- duration: 24
- unit: h
- order: after T92
- verify: Case-level slaRules[] populated with a single time-based default; no condition-based rules in this case

### T94: Add SLA escalation rule "At-Risk"
- target: case
- threshold-percent: 75
- recipient: UserGroup:Maritime Compliance Reviewers
- action: Notify
- display-name: At-Risk
- order: after T93
- verify: At-Risk escalation entry appended; fires at 75% of SLA duration; recipient identity-resolution will populate `tasks/recipients-resolved.json` per `plugins/sla/planning.md § Identity Resolution`

### T95: Add SLA escalation rule "Breached"
- target: case
- threshold-percent: 100
- recipient: UserGroup:Operations Leadership
- action: Notify
- display-name: Breached
- order: after T94
- verify: Breach escalation entry appended; fires at 100% of SLA duration

---

## Section 8 — Not Covered (planning concerns surfaced for the user)

The following items are referenced in the SDD but are outside the scope of `caseplan.json`. They remain notes for the user, not T-entries.

1. **MeridianCase entity schema verification (medium).** The trigger reuses the existing `MeridianCase` Data Fabric entity (per user direction, rather than minting a new `VoyageRelease` entity). The SDD assumes a payload shape with top-level scalar fields (`response.caseId`, `response.voyage`, `response.externalKey`) plus a nested `response.parties.*` object for the four party-related fields and top-level `response.<docName>Document` file fields. The actual entity schema needs verification before publish:
   - Confirm `parties` is an object with sub-fields `destinationPortCode`, `shipper`, `consignee`, `vesselOperator` — OR adjust T06–T09 paths to whatever shape the entity actually has.
   - Confirm the 5 document file fields exist with the renamed names (`bolDocument`, `cargoManifestDocument`, `certificateOfOriginDocument`, `insuranceCertificateDocument`, `qualityCertificateDocument`) — OR rename the case variables (T10–T14) to match the entity.
   - Confirm `caseId`, `voyage`, `externalKey` are scalar string fields on the entity.

2. **Co-firing on the same entity (medium).** Both `MeridianCase` and `VoyageRelease` cases will fire on every new MeridianCase record creation — one case of each kind per record. Confirm this is intended; if not, author a dedicated `VoyageRelease` entity in Data Fabric and re-point T02's `object-name` to it.

3. **DUExtraction RPA package (high).** The RPA project lives at `/solution/DUExtraction/` in this solution; identity is bound via the solution-project name + folder pattern at solution pack/deploy time. The package MUST be deployed before this case can fire.

4. **PortLookupTool API workflow (high).** The api-workflow project lives at `/solution/PortLookupTool/`; identity binds at pack/deploy time. MUST be deployed before Port Readiness can run.

5. **PartyReviewApp action app (high).** Not deployed in the tenant. The deployed app MUST set `partyOverride = true` AND `approvedOverride = true` on its APPROVE button; no override flag on REJECT.

6. **PortReviewApp action app (high).** Not deployed. App MUST set `portOverride = true` AND `approvedOverride = true` on APPROVE; nothing on REJECT.

7. **DocumentReviewApp action app (high).** Not deployed. App MUST expose 5 file output fields (one per document slot) and route the reviewer's re-upload into whichever matches `flaggedDocument` (set by VerificationAgent in Stage 2). The other 4 emit null. App also sets `approvedOverride = true` on APPROVE; no per-lane flag (Doc Review forward-routes, doesn't gate).

8. **ReleaseCoordinatorAgent input contract (medium).** Phase 1 inferred ReleaseCoordinatorAgent's input fields (`caseId`, `docComment`, `partyComment`, `portComment`, `reviewComment`, `approvedOverride`, `outcomeContext`) from the SDD's intended use. Phase 2 must run `uip maestro case tasks describe --type agent --id 05a27308-2df8-49b0-89ce-cb2e15fbc20f --output json` to confirm the deployed agent's actual schema. If the deployed agent has different field names, T44 and T48 inputs must be re-bound.

9. **PortLookupTool result domain (low).** Per the SDD's port-result semantics note, `REVIEW` = port not in lookup / indeterminate; `FAIL` = explicitly denied. If the deployed `PortLookupTool` only ever emits `PASS` / `FAIL` (no `REVIEW`), the Port Review lane is unreachable — an acceptable state, but worth documenting.

---

## Final cross-check

| Class | Count in this file | Match to sdd.md |
|---|---|---|
| Case file | 1 (T01) | ✅ §1 Case Metadata |
| Triggers | 1 (T02) | ✅ §1 Case Triggers — 1 row |
| Variables / arguments | 28 (T03–T30) | ✅ §1 Case Variables — 28 rows (27 Variable + 1 Out) |
| Stages | 9 (T31–T39) | ✅ §2 — 5 primary + 4 exception |
| Tasks | 9 (T40–T48) | ✅ §2 — 1 per stage |
| Conditions | 44 (T49–T92) | ✅ §2 stage entry/exit + task entry tables, §1 case exit |
| ↳ Stage entry | 15 (T49–T63) | ✅ |
| ↳ Stage exit | 18 (T64–T81) | ✅ |
| ↳ Case exit | 2 (T82–T83) | ✅ |
| ↳ Task entry | 9 (T84–T92) | ✅ |
| SLA | 3 (T93–T95) | ✅ §1 Case-Level SLA + 2 escalations |
| **Total** | **95** | ✅ |

End of tasks.md.
