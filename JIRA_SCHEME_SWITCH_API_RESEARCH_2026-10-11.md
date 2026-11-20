# Jira workflow scheme switch — verified API contracts, 2026-10-11

Status: **DOCS / OPENAPI VERIFIED; SITE NOT TESTED**. Public official documentation only. No Jira/MCP/credential service calls, no approval request, no mutation or guard bypass. Only this findings file was created. AGENTS.md was read in the authoritative directory. Research was time-boxed; no implementation inspected.

## 1. Required-mappings API — exact contract

`POST /rest/api/3/workflowscheme/update/mappings`, operationId `getRequiredWorkflowSchemeMappings`. Request body required, `Content-Type: application/json`. This calculates mappings for proposed scheme changes; it is not the scheme update operation. Request schema `WorkflowSchemeUpdateRequiredMappingsRequest`; successful response `200 application/json`, schema `WorkflowSchemeUpdateRequiredMappingsResponse`. [Official reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-schemes/#api-rest-api-3-workflowscheme-update-mappings-post).

Request shape (placeholders, not verified site IDs):

```json
{
  "id": "<workflow-scheme-id>",
  "defaultWorkflowId": "<desired-default-workflow-id>",
  "workflowsForIssueTypes": [
    { "issueTypeIds": ["<issue-type-id>"], "workflowId": "<desired-workflow-id>" }
  ]
}
```

`id` and `workflowsForIssueTypes` are required; each association requires both `issueTypeIds` and `workflowId`. `defaultWorkflowId` is optional/nullable, only used for global-scoped schemes; documentation says omission selects Jira Workflow (`jira`), so omission is NOT documented as preserving the existing default. No `projectId`, `targetSchemeId`, version or status mapping inputs are in this request; additional properties are forbidden. [Official OpenAPI](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130).

Response shape (illustrative placeholders; not a guarantee every field is present):

```json
{
  "statusMappingsByIssueTypes": [
    { "issueTypeId": "<issue-type-id>", "statusIds": ["<old-status-requiring-mapping>"] }
  ],
  "statusMappingsByWorkflows": [
    {
      "sourceWorkflowId": "<source-workflow-id>",
      "targetWorkflowId": "<target-workflow-id>",
      "statusIds": ["<old-status-requiring-mapping>"]
    }
  ],
  "statuses": [
    { "category": "TODO", "id": "<status-id>", "name": "<status-name>" }
  ],
  "statusesPerWorkflow": [
    {
      "initialStatusId": "<initial-status-id>",
      "statuses": ["<status-id>"],
      "workflowId": "<workflow-id>"
    }
  ]
}
```

`statusIds` identifies statuses needing a mapping, NOT selected target destinations. The four response arrays have `uniqueItems: true`; no response or nested response properties are marked required. `category` enum is `TODO | IN_PROGRESS | DONE`. Exact structural schemas are below. [Official OpenAPI](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130).

**Switch integration uncertainty:** the switch docs link to this calculator, but do not provide an explicit source-scheme→target-scheme calculator example or project selector. Treating `id` as the current/source scheme and supplying the target scheme's desired workflow associations is a reasonable integration inference, NOT site-tested proof. Project-specific filtering and shared-source-scheme behavior remain UNKNOWN. Do not invent a `projectId` parameter. [Switch reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-schemes/#api-rest-api-3-workflowscheme-project-switch-post).

## 2. Switch, permissions, restrictions and errors

`POST /rest/api/3/workflowscheme/project/switch`, operationId `switchWorkflowSchemeForProject`: Experimental (`x-experimental: true`), not deprecated. Body: `projectId: string`, `targetSchemeId: string`, `mappingsByIssueTypeOverride: MappingsByIssueTypeOverride[]`. Request body required; the published object schema has NO `required` array, although the operation needs the project/target inputs in practice. Root allows additional properties; nested mapping objects do not. [Official OpenAPI](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130).

- `mappingsByIssueTypeOverride` is per issue type, containing `statusMappings` pairs `oldStatusId`→`newStatusId`, all string IDs. It is required semantically when old workflow statuses disappear in the target. These migrate issue statuses; they are not issue-type→workflow assignments. The destination must be interpreted in that issue type's new workflow, not merely found somewhere in the target scheme. No documented rule says same status category or same name establishes identity.
- Do not confuse switch's `mappingsByIssueTypeOverride` with update's differently named `statusMappingsByIssueTypeOverride`. The calculator reports both issue-type and workflow requirements; the switch request exposes only the issue-type override field.
- Classic/company-managed projects only. Unlike `PUT /rest/api/3/workflowscheme/project` (explicitly no issues allowed; success 204), switch documents issue migration and no empty-project prerequisite. This verifies an API migration route in documentation, NOT QAG3 availability or permission.
- Switch needs **Administer Jira global permission**, not merely Administer projects. OAuth classic: `manage:jira-configuration`; granular: `write:workflow-scheme:jira` AND `write:project:jira`; Connect: `ADMIN`.
- Calculator permissions: Administer Jira for all/global schemes; Administer projects for project-scoped schemes. OAuth classic: `manage:jira-configuration`; granular: `write:workflow-scheme:jira` (despite being a calculator); Connect: `ADMIN`.

[Switch and mappings reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-schemes/), [empty-project PUT reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-scheme-project-associations/#api-rest-api-3-workflowscheme-project-put).

| Operation | Documented responses / error semantics |
|---|---|
| Switch | 303 task started; 400 invalid request; 401 incorrect/missing credentials **or insufficient permissions**; 409 conflicting running task |
| Calculator | 200 mappings; 400 invalid request; 401 incorrect/missing credentials **or insufficient permissions** |
| GET task | 200 task envelope; 401 incorrect/missing credentials; 403 insufficient permissions; 404 task not found |

Switch/calculator do NOT explicitly enumerate 403/404 in this OpenAPI; do not import PUT's response matrix. Switch 409's example includes `errors.conflictingTaskId` as a string. Neither calculator's 400/401 nor switch's 400/401/409 declares an exact error-body schema; 409 provides an example only. Generic Jira error documentation offers optional `errorMessages: string[]`, `errors: object` with string-valued nonempty keys, `status: integer`, but does not guarantee a body. [Official OpenAPI](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130), [generic status-code reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#status-codes).

## 3. 303 Location and task polling

Switch success is **303**, not 200/204 completion. Its JSON body schema is `TaskProgressBeanObject`. Atlassian's general async contract supplies the queued task URL in `Location`; the switch OpenAPI does not separately declare a `headers.Location` schema. Poll with `GET /rest/api/3/task/{taskId}`; 200 returns the SAME envelope schema. [Async contract](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#async), [task reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-tasks/#api-rest-api-3-task-taskId-get).

Recommended client handling (engineering guidance, NOT site-tested): preserve raw 303/Location/body/task ID; avoid automatic redirect hiding the 303. Follow a validated task URL using GET, never repeat the POST to follow Location. Reject unexpected credential destinations; keep the approved site/cloud scope. `self` and `id` are documented envelope fields, usable for reconciliation if the transport loses the header; missing/untrustworthy task identity means UNKNOWN, not success/retry.

Task status enum: `ENQUEUED`, `RUNNING`, `COMPLETE`, `FAILED`, `CANCEL_REQUESTED`, `CANCELLED`, `DEAD`. Recommended handling: poll ENQUEUED/RUNNING; CANCEL_REQUESTED is not finished cancellation; only COMPLETE is a completion candidate. FAILED/CANCELLED/DEAD are not success. Unknown status, polling timeout or 404 is indeterminate, not authorization to resubmit. The docs do not prescribe a polling interval, deadline, task-order guarantee, switch idempotency key or rollback semantics. Async tasks are explicitly not guaranteed to execute in submission order. [Official OpenAPI](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130), [async reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#async).

`result` is unconstrained JSON (`{}` after removing its description). There is NO switch-specific result schema: do not invent `result.success`, counts, or `result.errors`. Task `progress` is a percentage, `elapsedRuntime` milliseconds; `submittedBy` is int64, not documented as an accountId string. Task reads need Administer Jira OR task creator, OAuth `read:jira-work`, Connect `NONE`. Retention documentation says 14 days as of September 2019, changeable without notice. Completion still requires independent association/status/data read-back before declaring migration verified; migration's validator/post-function/Resolution/automation behavior is UNKNOWN here. [Task reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-tasks/), [Official OpenAPI](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130).

## 4. Exact structural OpenAPI schemas

Retrieved public official OpenAPI on `2026-10-11T14:38:49.6268382Z`; OpenAPI `3.0.1`; `info.version` = `1001.0.0-SNAPSHOT-0c0db68a171663452b321ade8630cf9c8cada05d`. SHA256 of decoded response re-encoded as UTF-8: `a7f554a7e0f6689b97dddcffb4952488d89f137e575042cb47ec04412cc41447`. Source: [Atlassian OpenAPI download](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130).

Below preserves structural validation keywords exactly; prose `description` annotations and `example` annotations are omitted. The task's actual `description` PROPERTY is retained. Place this schema-name map under `components.schemas` to resolve the refs. No implicit `required`, limits or nullability added.

```json
{
  "WorkflowSchemeProjectSwitchBean": {
    "additionalProperties": true,
    "properties": {
      "mappingsByIssueTypeOverride": {"items": {"$ref": "#/components/schemas/MappingsByIssueTypeOverride"}, "type": "array"},
      "projectId": {"type": "string"},
      "targetSchemeId": {"type": "string"}
    },
    "type": "object"
  },
  "MappingsByIssueTypeOverride": {
    "additionalProperties": false,
    "properties": {
      "issueTypeId": {"type": "string"},
      "statusMappings": {"items": {"$ref": "#/components/schemas/WorkflowAssociationStatusMapping"}, "type": "array"}
    },
    "type": "object"
  },
  "WorkflowAssociationStatusMapping": {
    "additionalProperties": false,
    "properties": {"newStatusId": {"type": "string"}, "oldStatusId": {"type": "string"}},
    "type": "object"
  },
  "WorkflowSchemeUpdateRequiredMappingsRequest": {
    "additionalProperties": false,
    "properties": {
      "defaultWorkflowId": {"nullable": true, "type": "string"},
      "id": {"type": "string"},
      "workflowsForIssueTypes": {"items": {"$ref": "#/components/schemas/WorkflowSchemeAssociation"}, "type": "array"}
    },
    "required": ["id", "workflowsForIssueTypes"],
    "type": "object"
  },
  "WorkflowSchemeAssociation": {
    "additionalProperties": false,
    "properties": {
      "issueTypeIds": {"items": {"type": "string"}, "type": "array", "uniqueItems": true},
      "workflowId": {"type": "string"}
    },
    "required": ["issueTypeIds", "workflowId"],
    "type": "object"
  },
  "WorkflowSchemeUpdateRequiredMappingsResponse": {
    "additionalProperties": false,
    "properties": {
      "statusMappingsByIssueTypes": {"items": {"$ref": "#/components/schemas/RequiredMappingByIssueType"}, "type": "array", "uniqueItems": true},
      "statusMappingsByWorkflows": {"items": {"$ref": "#/components/schemas/RequiredMappingByWorkflows"}, "type": "array", "uniqueItems": true},
      "statuses": {"items": {"$ref": "#/components/schemas/StatusMetadata"}, "type": "array", "uniqueItems": true},
      "statusesPerWorkflow": {"items": {"$ref": "#/components/schemas/StatusesPerWorkflow"}, "type": "array", "uniqueItems": true}
    },
    "type": "object"
  },
  "RequiredMappingByIssueType": {
    "additionalProperties": false,
    "properties": {
      "issueTypeId": {"type": "string"},
      "statusIds": {"items": {"type": "string"}, "type": "array", "uniqueItems": true}
    },
    "type": "object"
  },
  "RequiredMappingByWorkflows": {
    "additionalProperties": false,
    "properties": {
      "sourceWorkflowId": {"type": "string"},
      "statusIds": {"items": {"type": "string"}, "type": "array", "uniqueItems": true},
      "targetWorkflowId": {"type": "string"}
    },
    "type": "object"
  },
  "StatusMetadata": {
    "additionalProperties": false,
    "properties": {
      "category": {"enum": ["TODO", "IN_PROGRESS", "DONE"], "type": "string"},
      "id": {"type": "string"},
      "name": {"type": "string"}
    },
    "type": "object"
  },
  "StatusesPerWorkflow": {
    "additionalProperties": false,
    "properties": {
      "initialStatusId": {"type": "string"},
      "statuses": {"items": {"type": "string"}, "type": "array", "uniqueItems": true},
      "workflowId": {"type": "string"}
    },
    "type": "object"
  },
  "TaskProgressBeanObject": {
    "additionalProperties": false,
    "properties": {
      "description": {"type": "string"},
      "elapsedRuntime": {"format": "int64", "type": "integer"},
      "finished": {"format": "int64", "type": "integer"},
      "id": {"type": "string"},
      "lastUpdate": {"format": "int64", "type": "integer"},
      "message": {"type": "string"},
      "progress": {"format": "int64", "type": "integer"},
      "result": {},
      "self": {"format": "uri", "type": "string"},
      "started": {"format": "int64", "type": "integer"},
      "status": {"enum": ["ENQUEUED", "RUNNING", "COMPLETE", "FAILED", "CANCEL_REQUESTED", "CANCELLED", "DEAD"], "type": "string"},
      "submitted": {"format": "int64", "type": "integer"},
      "submittedBy": {"format": "int64", "type": "integer"}
    },
    "required": ["elapsedRuntime", "id", "lastUpdate", "progress", "self", "status", "submitted", "submittedBy"],
    "type": "object"
  }
}
```

## 5. Limits / handoff

Verified documentation only; no site availability, credentials, permission, live calculator, task, migration, rollback or gate behavior tested. No local guard changed. Exact source/target use of calculator for a project switch remains an explicitly labeled integration inference; switch-specific task `result` schema is UNKNOWN. This note does not authorize application or qualify Jira E2E.
