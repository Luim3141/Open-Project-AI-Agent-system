"""Main workflow definitions and caller-bound security hardening candidate.

Historical definitions below are incomplete business workflows, not acceptance evidence.
secure_workflows removes shared PM authority and requires exact Gateway proposal decisions.
deploy hardens the current live nodes so unrelated runtime fixes are preserved.
Historical implementation notes:
1. All incoming Webhooks use Header Authentication with credential '2w9dSdmYbywZDuMB' (X-QLDAPM-Webhook-Token).
2. All outgoing HTTP Requests to Gateway use Bearer Auth with credential 'DBWkxwb2izrbu17C' (Authorization: Bearer <PM_TOKEN>).
3. Real HTTP Request nodes replace all mock code nodes.
4. Retry policies (3 attempts, exponential backoff) configured on all HTTP request nodes.
5. WF01: Ingests documents via Gateway knowledge_ingest command.
6. WF02: Syncs Work Packages via Gateway list_work_packages command.
7. WF03: Starts real AI/Supervisor run via Gateway /api/v1/ai-runs.
8. WF04: Retrieves real agent traces via Gateway /api/v1/agent-runs/{id}/trace.
9. WF05: Verifies PM role and proposal pending status via Gateway /api/v1/proposals/{id}.
10. WF06: Executes mutation via Gateway /api/v1/commands with auto_execute=true and reads back WP to verify.
11. WF07: Signs daily brief request with HMAC automation key and queries Gateway.
12. WF08: Evaluates sprint readiness using real work packages from Gateway.
13. WF09: Queries bug work packages via Gateway and performs triage classification.
14. WF10: Fetches real project options from Gateway for task decomposition.
15. WF11: Fetches WP from Gateway, validates QA criteria, and checks transition readiness.
16. WF12: Calculates real workload distribution from Gateway work packages.
17. WF13: Triggers real Qdrant re-indexing via Gateway knowledge_ingest.
18. WF14: Formats and logs error traces to Gateway /internal/automation/commands.
19. WF15: Performs real reconciliation between OpenProject WP count and Qdrant points_count.
20. WF16: Generates executive insights using Gateway get_insights command.
"""
import os
from pathlib import Path

import json
import time
import requests
try:
    from .n8n_integration_adapter import enable_project6_files, enable_project6_business
except ImportError:
    from n8n_integration_adapter import enable_project6_files, enable_project6_business

N8N_BASE = "http://localhost:5679"
GATEWAY_URL = "http://qldapm-ai-gateway-1:8090"
QDRANT_URL = "http://qldapm-qdrant:6333"

COOKIE = os.environ.get("QLDAPM_N8N_SESSION", "")
HEADERS = {"Cookie": f"n8n-auth={COOKIE}", "Content-Type": "application/json"}

WEBHOOK_CRED_ID = "2w9dSdmYbywZDuMB"
GATEWAY_CRED_ID = "DBWkxwb2izrbu17C"

RETRY_CONFIG = {
    "maxTries": 3,
    "waitBetweenTries": 1000,
    "retryOnFail": True
}


def build_workflows():
    wfs = {}

    # WF01: Local Document Ingestion
    wfs["WF01"] = {
        "name": "WF01: Local Document Ingestion",
        "nodes": [
            {
                "id": "trigger",
                "name": "Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "6db33976-509a-47b6-bce0-e15c28fee03b",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-ingest",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "prepare",
                "name": "Prepare Ingest Payload",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [360, 200],
                "parameters": {
                    "jsCode": """
const item = $input.first().json;
const body = item.body || item;
const path = body.file_path || body.path || 'user-story-web-quan-ly-du-an-rut-gon.docx';
return [{ json: { path: path, action: 'knowledge_ingest', idempotency_key: 'wf01-' + Date.now() } }];
"""
                }
            },
            {
                "id": "gateway_ingest",
                "name": "Call Gateway Knowledge Ingest",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [620, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({action: 'knowledge_ingest', arguments: {id: ($json.body && $json.body.id) || $json.id || 38}, idempotency_key: 'wf01-' + Date.now()}) }}",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_result",
                "name": "Format Ingest Result",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [880, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
return [{ json: { status: 'INGEST_COMPLETED', target: res.result || res, correlation_id: res.correlation_id, ingested_at: new Date().toISOString() } }];
"""
                }
            }
        ],
        "connections": {
            "Webhook Trigger": {"main": [[{"node": "Prepare Ingest Payload", "type": "main", "index": 0}]]},
            "Prepare Ingest Payload": {"main": [[{"node": "Call Gateway Knowledge Ingest", "type": "main", "index": 0}]]},
            "Call Gateway Knowledge Ingest": {"main": [[{"node": "Format Ingest Result", "type": "main", "index": 0}]]}
        }
    }

    # WF02: OpenProject Event Sync & RAG Synchronization
    wfs["WF02"] = {
        "name": "WF02: OpenProject Event Sync",
        "nodes": [
            {
                "id": "trigger",
                "name": "WP Event Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "d2a9d1e0-55e0-441f-baa9-c2f78ef215f7",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-op-sync",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_wps",
                "name": "Fetch OpenProject Work Packages",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "list_work_packages", "arguments": {"limit": 30}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "sync_rag",
                "name": "Sync Work Package To RAG",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [620, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "knowledge_ingest", "arguments": {"id": 38}, "idempotency_key": "wf02-sync-38"}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_sync",
                "name": "Format Sync & RAG Verification",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [880, 200],
                "parameters": {
                    "jsCode": """
const syncRes = $input.first().json;
const listRes = $('Fetch OpenProject Work Packages').first().json;
const total = listRes.result?.total || 332;
const ingest = syncRes.result || {};
return [{
  json: {
    status: 'SYNCED',
    total_work_packages: total,
    rag_status: ingest.status || 'INDEXED',
    chunks_indexed: ingest.chunks_indexed || 1,
    vector_indexed: ingest.vector_indexed !== false,
    sync_verified: true,
    correlation_id: syncRes.correlation_id || listRes.correlation_id,
    synced_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "WP Event Webhook": {"main": [[{"node": "Fetch OpenProject Work Packages", "type": "main", "index": 0}]]},
            "Fetch OpenProject Work Packages": {"main": [[{"node": "Sync Work Package To RAG", "type": "main", "index": 0}]]},
            "Sync Work Package To RAG": {"main": [[{"node": "Format Sync & RAG Verification", "type": "main", "index": 0}]]}
        }
    }

    # WF03: Natural Language Request Orchestrator
    wfs["WF03"] = {
        "name": "WF03: Natural Language Request Orchestrator",
        "nodes": [
            {
                "id": "trigger",
                "name": "User Request Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "593ff10a-29a1-43c4-83cb-0d89599f8a5b",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-agent-request",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "parse",
                "name": "Parse & Route Prompt",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [360, 200],
                "parameters": {
                    "jsCode": """
const item = $input.first().json;
const body = item.body || item;
const prompt = body.prompt || body.text || 'Phân tích tổng quan dự án 5';
const engine = body.engine || 'supervisor';
const run_class = body.run_class || 'interactive';
const idempotencyKey = 'wf03-' + Date.now();
return [{
  json: {
    prompt: prompt,
    engine: engine,
    run_class: run_class,
    idempotency_key: idempotencyKey
  }
}];
"""
                }
            },
            {
                "id": "call_gateway",
                "name": "Call Gateway AI Run",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [620, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/ai-runs",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
                            {"name": "Idempotency-Key", "value": "={{ $json.idempotency_key }}"}
                        ]
                    },
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({prompt: $json.prompt, engine: $json.engine, run_class: $json.run_class}) }}",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_response",
                "name": "Format Response",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [880, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
return [{
  json: {
    status: 'SUCCESS',
    run_id: res.id || res.result?.id,
    state: res.state || res.result?.state,
    correlation_id: res.correlation_id || res.id,
    created_at: res.created_at || new Date().toISOString(),
    gateway_response: res
  }
}];
"""
                }
            }
        ],
        "connections": {
            "User Request Webhook": {"main": [[{"node": "Parse & Route Prompt", "type": "main", "index": 0}]]},
            "Parse & Route Prompt": {"main": [[{"node": "Call Gateway AI Run", "type": "main", "index": 0}]]},
            "Call Gateway AI Run": {"main": [[{"node": "Format Response", "type": "main", "index": 0}]]}
        }
    }

    # WF04: Multi-Agent Execution Tracking
    wfs["WF04"] = {
        "name": "WF04: Multi-Agent Execution Tracking",
        "nodes": [
            {
                "id": "trigger",
                "name": "Agent Trace Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "cade8513-08fd-47b1-91ac-93c0b5571f8e",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-agent-trace",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_trace",
                "name": "Fetch Gateway Agent Trace",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "GET",
                    "url": f"={GATEWAY_URL}/api/v1/agent-runs/{{{{ ($json.body && $json.body.run_id) || $json.run_id }}}}/trace",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_trace",
                "name": "Format Trace Summary",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
const items = res.result?.items || [];
return [{
  json: {
    status: 'TRACE_RETRIEVED',
    total_events: items.length,
    events: items,
    correlation_id: res.correlation_id,
    fetched_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Agent Trace Webhook": {"main": [[{"node": "Fetch Gateway Agent Trace", "type": "main", "index": 0}]]},
            "Fetch Gateway Agent Trace": {"main": [[{"node": "Format Trace Summary", "type": "main", "index": 0}]]}
        }
    }

    # WF05: Native API Approval Workflow (Full Lifecycle)
    wfs["WF05"] = {
        "name": "WF05: Native API Approval Workflow",
        "nodes": [
            {
                "id": "trigger",
                "name": "Approval Request Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "d78236b5-4d8d-4ee1-9960-dd93a5dbe252",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-approval",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_prop",
                "name": "Fetch Gateway Proposal",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "GET",
                    "url": f"={GATEWAY_URL}/api/v1/proposals/{{{{ ($json.body && $json.body.proposal_id) || $json.proposal_id }}}}",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "process_decision",
                "name": "Process PM Approval Decision",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 200],
                "parameters": {
                    "jsCode": """
const propRes = $input.first().json;
const webhookReq = $('Approval Request Webhook').first().json;
const body = webhookReq.body || webhookReq;
const prop = propRes.result || propRes;
const decision = body.decision; // 'approve', 'reject', or undefined

if (decision === 'reject') {
  return [{
    json: {
      status: 'REJECTED_BY_PM',
      proposal_id: prop.id,
      hash: prop.hash,
      decision: 'REJECTED',
      rejection_recorded: true,
      correlation_id: propRes.correlation_id,
      evaluated_at: new Date().toISOString()
    }
  }];
}

if (decision === 'approve') {
  return [{
    json: {
      status: 'APPROVED_BY_PM',
      proposal_id: prop.id,
      hash: prop.hash,
      decision: 'APPROVED',
      action: prop.command?.action,
      ready_for_execution: true,
      correlation_id: propRes.correlation_id,
      evaluated_at: new Date().toISOString()
    }
  }];
}

// Default: Review / Waiting
return [{
  json: {
    status: 'WAITING_PM_APPROVAL',
    proposal_id: prop.id,
    hash: prop.hash,
    action: prop.command?.action,
    preview: prop.command?.preview,
    human_confirmation_required: true,
    expires_at: prop.expires,
    correlation_id: propRes.correlation_id,
    formatted_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Approval Request Webhook": {"main": [[{"node": "Fetch Gateway Proposal", "type": "main", "index": 0}]]},
            "Fetch Gateway Proposal": {"main": [[{"node": "Process PM Approval Decision", "type": "main", "index": 0}]]}
        }
    }

    # WF06: Native API Execution & Verification (Approval-Gated)
    wfs["WF06"] = {
        "name": "WF06: Native API Execution & Verification",
        "nodes": [
            {
                "id": "trigger",
                "name": "Execute Mutation Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "c4dbe777-be05-42e2-949f-4d6fdd1a836a",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-execute-mutation",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "prepare_mutation",
                "name": "Prepare Mutation Command",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [300, 200],
                "parameters": {
                    "jsCode": """
const req = $input.first().json;
const body = req.body || req;
const action = body.action || 'comment';
const args = body.arguments || { id: 38, lock_version: 3, text: 'WF06 Verification' };
const targetId = args.id || body.work_package_id || 38;
const idempotencyKey = body.idempotency_key || ('wf06-' + Date.now());
return [{
  json: {
    command_payload: {
      action: action,
      arguments: args,
      auto_execute: true,
      idempotency_key: idempotencyKey
    },
    target_id: targetId
  }
}];
"""
                }
            },
            {
                "id": "execute_mutation",
                "name": "Execute Mutation via Gateway",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [500, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={{ $json.command_payload }}",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "prepare_readback",
                "name": "Prepare Read Back Request",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [700, 200],
                "parameters": {
                    "jsCode": """
const execRes = $input.first().json;
const targetId = $('Prepare Mutation Command').first().json.target_id;
return [{
  json: {
    read_payload: {
      action: 'get_work_package',
      arguments: { id: targetId }
    },
    exec_correlation: execRes.correlation_id
  }
}];
"""
                }
            },
            {
                "id": "read_back",
                "name": "Read Back Work Package",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [900, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={{ $json.read_payload }}",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_exec_result",
                "name": "Format Verification Report",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [1100, 200],
                "parameters": {
                    "jsCode": """
const wp = $input.first().json.result || {};
const corr = $('Prepare Read Back Request').first().json.exec_correlation;
return [{
  json: {
    status: 'MUTATION_EXECUTED_AND_VERIFIED',
    work_package_id: wp.id || 38,
    lock_version: wp.lockVersion,
    subject: wp.subject,
    verified_on_native: true,
    correlation_id: corr,
    verified_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Execute Mutation Webhook": {"main": [[{"node": "Prepare Mutation Command", "type": "main", "index": 0}]]},
            "Prepare Mutation Command": {"main": [[{"node": "Execute Mutation via Gateway", "type": "main", "index": 0}]]},
            "Execute Mutation via Gateway": {"main": [[{"node": "Prepare Read Back Request", "type": "main", "index": 0}]]},
            "Prepare Read Back Request": {"main": [[{"node": "Read Back Work Package", "type": "main", "index": 0}]]},
            "Read Back Work Package": {"main": [[{"node": "Format Verification Report", "type": "main", "index": 0}]]}
        }
    }

    # WF07: Daily Project Brief (Dual Trigger: Schedule + Webhook)
    wfs["WF07"] = {
        "name": "WF07: Daily Project Brief",
        "nodes": [
            {
                "id": "webhook_trigger",
                "name": "Daily Trigger Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 160],
                "webhookId": "9b12879d-3f1a-4648-b4b3-d6484a9ee1bc",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-daily-brief",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "schedule_trigger",
                "name": "Daily Schedule 08:00",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [100, 340],
                "parameters": {
                    "rule": {
                        "interval": [
                            {
                                "field": "cronExpression",
                                "expression": "0 8 * * *"
                            }
                        ]
                    }
                }
            },
            {
                "id": "fetch_brief_insights",
                "name": "Fetch Project Insights",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 240],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "get_insights", "arguments": {"days": 7}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_brief",
                "name": "Format Daily Brief",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 240],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
const insights = res.result || {};
return [{
  json: {
    status: 'DAILY_BRIEF_GENERATED',
    trigger_type: 'DAILY_PROJECT_BRIEF',
    schedule_cron: '0 8 * * *',
    timezone: 'Asia/Bangkok',
    insights: insights,
    total_active_wps: insights.total_active || 332,
    velocity_trend: insights.velocity || 'STABLE',
    correlation_id: res.correlation_id,
    generated_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Daily Trigger Webhook": {"main": [[{"node": "Fetch Project Insights", "type": "main", "index": 0}]]},
            "Daily Schedule 08:00": {"main": [[{"node": "Fetch Project Insights", "type": "main", "index": 0}]]},
            "Fetch Project Insights": {"main": [[{"node": "Format Daily Brief", "type": "main", "index": 0}]]}
        }
    }

    # WF08: Sprint Readiness Gate
    wfs["WF08"] = {
        "name": "WF08: Sprint Readiness Gate",
        "nodes": [
            {
                "id": "trigger",
                "name": "Readiness Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "7e3b6a2c-1f8d-4e92-b5c4-a1b2c3d4e5f6",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-sprint-readiness",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_sprint_wps",
                "name": "Fetch Project Work Packages",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "list_work_packages", "arguments": {"limit": 30}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "evaluate_readiness",
                "name": "Evaluate Sprint Readiness Metrics",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
const total = res.result?.total || 0;
const ready = total > 0;
return [{
  json: {
    status: 'EVALUATED',
    gate: 'SPRINT_READINESS',
    ready: ready,
    total_packages: total,
    correlation_id: res.correlation_id,
    evaluated_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Readiness Webhook": {"main": [[{"node": "Fetch Project Work Packages", "type": "main", "index": 0}]]},
            "Fetch Project Work Packages": {"main": [[{"node": "Evaluate Sprint Readiness Metrics", "type": "main", "index": 0}]]}
        }
    }

    # WF09: Bug Lifecycle Automation (Real Triage)
    wfs["WF09"] = {
        "name": "WF09: Bug Lifecycle Automation",
        "nodes": [
            {
                "id": "trigger",
                "name": "Bug Event Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "8f4c7b3d-2e9a-4f03-c6d5-b2c3d4e5f6a7",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-bug-lifecycle",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_bugs",
                "name": "Fetch Bug Work Packages",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "list_work_packages", "arguments": {"query": "bug", "limit": 30}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "triage_bugs",
                "name": "Triage & Classify Bugs",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
const elements = res.result?.items || res.result?._embedded?.elements || (Array.isArray(res.result) ? res.result : []);
const totalBugs = res.result?.total || elements.length;

let blockers = 0;
let inProgress = 0;
let unassigned = 0;
const classified = [];

for (const el of elements) {
  const isBlocker = (el.subject || '').toLowerCase().includes('critical') || (el.priority || '').includes('Immediate');
  const hasAssignee = !!el._links?.assignee?.href;
  if (isBlocker) blockers++;
  if (!hasAssignee) unassigned++;
  classified.push({
    id: el.id,
    subject: el.subject,
    status: el._links?.status?.title || 'Unknown',
    lock_version: el.lockVersion,
    severity: isBlocker ? 'BLOCKER' : 'NORMAL',
    assignee_assigned: hasAssignee
  });
}

const triageAction = blockers > 0 ? 'ESCALATE_CRITICAL_BLOCKERS' : unassigned > 0 ? 'ASSIGN_TRIAGED_BUGS' : 'MONITOR_REGULAR_PROGRESS';

return [{
  json: {
    status: 'TRIAGED',
    total_bugs: totalBugs,
    classified_count: classified.length,
    blockers_count: blockers,
    unassigned_count: unassigned,
    triage_action: triageAction,
    sample_bugs: classified.slice(0, 5),
    correlation_id: res.correlation_id,
    triaged_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Bug Event Webhook": {"main": [[{"node": "Fetch Bug Work Packages", "type": "main", "index": 0}]]},
            "Fetch Bug Work Packages": {"main": [[{"node": "Triage & Classify Bugs", "type": "main", "index": 0}]]}
        }
    }

    # WF10: Task Orchestration & Decomposition
    wfs["WF10"] = {
        "name": "WF10: Task Orchestration & Decomposition",
        "nodes": [
            {
                "id": "trigger",
                "name": "Task Event Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "1a2b3c4d-5e6f-7a8b-9c0d-e1f2a3b4c5d6",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-task-orchestration",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_options",
                "name": "Fetch Project Schema Options",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "get_project_options", "arguments": {}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "plan_decomposition",
                "name": "Generate Decomposition Plan",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 200],
                "parameters": {
                    "jsCode": """
const optRes = $input.first().json;
const webhookReq = $('Task Event Webhook').first().json;
const body = webhookReq.body || webhookReq;
const prompt = body.prompt || 'Feature decomposition';
const allowWrites = body.allow_writes === true;

const users = optRes.result?.users || { '19': 'PM', '20': 'BA', '21': 'BE', '22': 'FE', '23': 'QA' };
const types = optRes.result?.types || { '1': 'Task', '2': 'Subtask', '7': 'Epic' };

const plan = [
  { level: 'EPIC', title: prompt + ' - Epic Container', type_id: 7, owner: '19 (PM)' },
  { level: 'USER_STORY', title: prompt + ' - User Story & Specs', type_id: 1, owner: '20 (BA)' },
  { level: 'SUBTASK', title: prompt + ' - Backend API Implementation', type_id: 2, owner: '21 (BE)' },
  { level: 'SUBTASK', title: prompt + ' - Frontend UI Component', type_id: 2, owner: '22 (FE)' },
  { level: 'SUBTASK', title: prompt + ' - QA Verification & Test Run', type_id: 2, owner: '23 (QA)' }
];

return [{
  json: {
    status: 'ORCHESTRATED',
    orchestration_state: allowWrites ? 'ORCHESTRATED_AND_AUTHORIZED' : 'PLAN_PROPOSED_WAITING_APPROVAL',
    prompt: prompt,
    requires_pm_approval: !allowWrites,
    available_types: types,
    planned_items_count: plan.length,
    plan_hierarchy: plan,
    schema_verified: true,
    correlation_id: optRes.correlation_id,
    planned_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Task Event Webhook": {"main": [[{"node": "Fetch Project Schema Options", "type": "main", "index": 0}]]},
            "Fetch Project Schema Options": {"main": [[{"node": "Generate Decomposition Plan", "type": "main", "index": 0}]]}
        }
    }

    # WF11: QA Gate Verification (Real Acceptance Criteria Check)
    wfs["WF11"] = {
        "name": "WF11: QA Gate Transition",
        "nodes": [
            {
                "id": "trigger",
                "name": "QA Gate Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "2b3c4d5e-6f7a-8b9c-0d1e-f2a3b4c5d6e7",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-qa-gate",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "prepare_qa_req",
                "name": "Prepare QA Request",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [280, 200],
                "parameters": {
                    "jsCode": """
const item = $input.first().json;
const body = item.body || item;
const wpId = Number(body.id || body.work_package_id || 38);
return [{
  json: {
    action: 'get_work_package',
    arguments: { id: wpId, include_context: true }
  }
}];
"""
                }
            },
            {
                "id": "fetch_wp",
                "name": "Fetch Target Work Package",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [480, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={{ $json }}",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "verify_qa_gate",
                "name": "Verify QA Transition Gate",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [680, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
const wp = res.result || {};
const desc = (wp.description && wp.description.raw) || '';
const lockVersion = wp.lockVersion;
const currentStatus = wp._links?.status?.title || 'Open';

return [{
  json: {
    status: 'QA_GATE_CHECKED',
    work_package_id: wp.id || 38,
    subject: wp.subject,
    current_status: currentStatus,
    lock_version: lockVersion,
    acceptance_criteria_verified: true,
    transition_permitted: true,
    target_transition_status: 'Tested',
    blocking_reasons: [],
    correlation_id: res.correlation_id,
    checked_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "QA Gate Webhook": {"main": [[{"node": "Prepare QA Request", "type": "main", "index": 0}]]},
            "Prepare QA Request": {"main": [[{"node": "Fetch Target Work Package", "type": "main", "index": 0}]]},
            "Fetch Target Work Package": {"main": [[{"node": "Verify QA Transition Gate", "type": "main", "index": 0}]]}
        }
    }

    # WF12: Workload Balancing (Real Distribution Analysis)
    wfs["WF12"] = {
        "name": "WF12: Workload Balancing",
        "nodes": [
            {
                "id": "trigger",
                "name": "Workload Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "3c4d5e6f-7a8b-9c0d-1e2f-a3b4c5d6e7f8",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-workload-balance",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_all_wps",
                "name": "Fetch Assigned Work Packages",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "list_work_packages", "arguments": {"limit": 30}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "calc_workload",
                "name": "Calculate Team Workload",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
const elements = res.result?.items || res.result?._embedded?.elements || (Array.isArray(res.result) ? res.result : []);
const total = res.result?.total || elements.length || 332;

const members = {
  '19': { name: 'PM', count: 0, overdue: 0 },
  '20': { name: 'BA', count: 0, overdue: 0 },
  '21': { name: 'BE', count: 0, overdue: 0 },
  '22': { name: 'FE', count: 0, overdue: 0 },
  '23': { name: 'QA', count: 0, overdue: 0 }
};

let unassigned = 0;
const today = new Date().toISOString().split('T')[0];

for (const el of elements) {
  const href = el._links?.assignee?.href;
  const isOverdue = el.dueDate && el.dueDate < today;
  if (href) {
    const match = href.match(/\\/(\\d+)$/);
    const uid = match ? match[1] : null;
    if (uid && members[uid]) {
      members[uid].count++;
      if (isOverdue) members[uid].overdue++;
    } else {
      unassigned++;
    }
  } else {
    unassigned++;
  }
}

let highestLoad = 0;
let bottleneckRole = 'NONE';
for (const [uid, data] of Object.entries(members)) {
  if (data.count > highestLoad) {
    highestLoad = data.count;
    bottleneckRole = data.name;
  }
}

return [{
  json: {
    status: 'WORKLOAD_BALANCED',
    total_assigned_tasks: total,
    total_evaluated_tasks: total,
    unassigned_tasks: unassigned,
    member_distribution: members,
    bottleneck_identified: highestLoad > 15,
    primary_bottleneck_role: bottleneckRole,
    balancing_recommendation: highestLoad > 15 ? ('Rebalance tasks away from ' + bottleneckRole) : 'WORKLOAD_WITHIN_HEALTHY_BOUNDS',
    correlation_id: res.correlation_id,
    evaluated_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Workload Webhook": {"main": [[{"node": "Fetch Assigned Work Packages", "type": "main", "index": 0}]]},
            "Fetch Assigned Work Packages": {"main": [[{"node": "Calculate Team Workload", "type": "main", "index": 0}]]}
        }
    }

    # WF13: Second Brain RAG Re-indexing
    wfs["WF13"] = {
        "name": "WF13: Second Brain RAG Re-indexing",
        "nodes": [
            {
                "id": "trigger",
                "name": "Reindex Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "4d5e6f7a-8b9c-0d1e-2f3a-b4c5d6e7f8a9",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-rag-reindex",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "reindex_cmd",
                "name": "Trigger Knowledge Ingest",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({action: 'knowledge_ingest', arguments: {id: 38}, idempotency_key: 'wf13-' + Date.now()}) }}",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_reindex",
                "name": "Format Reindex Report",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 200],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
return [{
  json: {
    status: 'REINDEX_COMPLETE',
    result: res.result,
    correlation_id: res.correlation_id,
    reindexed_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Reindex Webhook": {"main": [[{"node": "Trigger Knowledge Ingest", "type": "main", "index": 0}]]},
            "Trigger Knowledge Ingest": {"main": [[{"node": "Format Reindex Report", "type": "main", "index": 0}]]}
        }
    }

    # WF14: Error Handling & Retry Router (Bounded Retries & Dead Letter Queue)
    wfs["WF14"] = {
        "name": "WF14: Error Handling & Retry Router",
        "nodes": [
            {
                "id": "trigger",
                "name": "Error Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "5e6f7a8b-9c0d-1e2f-3a4b-c5d6e7f8a9b0",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-error-handler",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "record_error",
                "name": "Evaluate Retry & Dead Letter Routing",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [360, 200],
                "parameters": {
                    "jsCode": """
const item = $input.first().json;
const body = item.body || item;
const retryCount = body.retry_count || 0;
const maxRetries = 3;

if (retryCount < maxRetries) {
  const backoffMs = 1000 * Math.pow(2, retryCount);
  return [{
    json: {
      status: 'ERROR_RECORDED',
      action: 'SCHEDULE_RETRY',
      retry_state: 'RETRY_SCHEDULED',
      source_workflow: body.workflow || 'UNKNOWN',
      error_type: body.error_type || 'TRANSIENT_ERROR',
      current_attempt: retryCount + 1,
      max_retries: maxRetries,
      retry_after_ms: backoffMs,
      handled_at: new Date().toISOString()
    }
  }];
}

// Bounded retries exhausted -> Route to DLQ
return [{
  json: {
    status: 'ERROR_RECORDED',
    action: 'ROUTE_TO_DLQ',
    retry_state: 'ROUTED_TO_DEAD_LETTER_QUEUE',
    source_workflow: body.workflow || 'UNKNOWN',
    error_type: body.error_type || 'EXHAUSTED_ERROR',
    attempts_exhausted: retryCount,
    audit_logged: true,
    alert_severity: 'CRITICAL',
    handled_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Error Webhook": {"main": [[{"node": "Evaluate Retry & Dead Letter Routing", "type": "main", "index": 0}]]}
        }
    }

    # WF15: Reconciliation & Drift Detection (Exact Corpus Reconciliation)
    wfs["WF15"] = {
        "name": "WF15: Reconciliation & Drift Detection",
        "nodes": [
            {
                "id": "trigger",
                "name": "Reconciliation Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "webhookId": "6f7a8b9c-0d1e-2f3a-4b5c-d6e7f8a9b0c1",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-reconciliation",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "fetch_op_count",
                "name": "Fetch OpenProject WP Count",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 200],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "list_work_packages", "arguments": {"limit": 1}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "fetch_qdrant_count",
                "name": "Fetch Qdrant Points Count",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [620, 200],
                "parameters": {
                    "method": "GET",
                    "url": f"{QDRANT_URL}/collections/qldapm_knowledge_dense",
                    "options": {}
                }
            },
            {
                "id": "compare_counts",
                "name": "Execute Deep Corpus Reconciliation",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [880, 200],
                "parameters": {
                    "jsCode": """
const qdrantRes = $input.first().json;
const opTotal = $('Fetch OpenProject WP Count').first().json.result?.total || 332;
const qdrantTotal = qdrantRes.result?.points_count || 1693;

// Exact mathematical and architectural reconciliation
const sqliteWps = 326;
const missingEpics = 10; // Epics 39 to 48 (project containers excluded from initial task crawl)
const duplicateDocEntries = 4; // WPs 49, 50, 53, 75 indexed under both op:wp and actor:19:wp
const sqliteChunksTotal = 1713;
const chunkPointDiff = sqliteChunksTotal - qdrantTotal; // 20 points
const duplicateChunksPurged = 23; // 23 duplicate chunks replaced/deduplicated by source_id
const legacyOrphanPoints = 3; // 3 legacy test points

return [{
  json: {
    status: 'RECONCILIATION_COMPLETE',
    reconciliation_state: 'CORPUS_RECONCILED_VERIFIED',
    openproject_work_packages: opTotal,
    qdrant_vector_points: qdrantTotal,
    drift_detected: false,
    openproject_live_work_packages: opTotal,
    sqlite_indexed_work_packages: sqliteWps,
    wp_difference_explained: {
      total_op: opTotal,
      missing_epics: missingEpics,
      unique_wps_indexed: opTotal - missingEpics,
      duplicate_actor_docs: duplicateDocEntries,
      sqlite_wp_docs_exact: (opTotal - missingEpics) + duplicateDocEntries
    },
    sqlite_chunks_count: sqliteChunksTotal,
    qdrant_vector_points_count: qdrantTotal,
    vector_point_difference_explained: {
      sqlite_chunks: sqliteChunksTotal,
      qdrant_points: qdrantTotal,
      net_difference: chunkPointDiff,
      purged_duplicate_chunks: duplicateChunksPurged,
      legacy_test_points: legacyOrphanPoints,
      reconciliation_match: (duplicateChunksPurged - legacyOrphanPoints) === chunkPointDiff
    },
    historical_1359_explained: '1,359 was the initial WP-only points count before 334 documentation chunks (ADRs + ARCHITECTURE) were ingested (1,359 + 334 = 1,693).',
    drift_status: 'ACCOUNTED_AND_CONSISTENT',
    reconciled_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Reconciliation Webhook": {"main": [[{"node": "Fetch OpenProject WP Count", "type": "main", "index": 0}]]},
            "Fetch OpenProject WP Count": {"main": [[{"node": "Fetch Qdrant Points Count", "type": "main", "index": 0}]]},
            "Fetch Qdrant Points Count": {"main": [[{"node": "Execute Deep Corpus Reconciliation", "type": "main", "index": 0}]]}
        }
    }

    # WF16: Executive Summary Generator (Dual Trigger: Schedule + Webhook)
    wfs["WF16"] = {
        "name": "WF16: Executive Summary Generator",
        "nodes": [
            {
                "id": "trigger",
                "name": "Summary Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 160],
                "webhookId": "7a8b9c0d-1e2f-3a4b-5c6d-e7f8a9b0c1d2",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-executive-summary",
                    "authentication": "headerAuth",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": WEBHOOK_CRED_ID, "name": "QLDAPM Webhook Header Auth"}}
            },
            {
                "id": "periodic_health",
                "name": "Periodic Health Schedule",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [100, 340],
                "parameters": {
                    "rule": {
                        "interval": [
                            {
                                "field": "minutes",
                                "minutesInterval": 15
                            }
                        ]
                    }
                }
            },
            {
                "id": "fetch_insights",
                "name": "Fetch Project Insights",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [360, 240],
                "parameters": {
                    "method": "POST",
                    "url": f"{GATEWAY_URL}/api/v1/commands",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": json.dumps({"action": "get_insights", "arguments": {"days": 30}}),
                    "options": {}
                },
                "credentials": {"httpHeaderAuth": {"id": GATEWAY_CRED_ID, "name": "QLDAPM Gateway Bearer Auth"}}
            },
            {
                "id": "format_summary",
                "name": "Format Executive Report",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [620, 240],
                "parameters": {
                    "jsCode": """
const res = $input.first().json;
const data = res.result || {};
return [{
  json: {
    status: 'EXECUTIVE_SUMMARY_READY',
    trigger_type: 'EXECUTIVE_SUMMARY_TRIGGER',
    insights: data,
    system_health: {
      gateway_connected: true,
      openproject_connected: true,
      qdrant_connected: true
    },
    project_kpis: {
      total_work_packages: 332,
      velocity_trend: data.velocity || 'STABLE',
      active_blockers: data.blockers || 0,
      completion_projection: data.projection || 'ON_SCHEDULE'
    },
    correlation_id: res.correlation_id,
    generated_at: new Date().toISOString()
  }
}];
"""
                }
            }
        ],
        "connections": {
            "Summary Webhook": {"main": [[{"node": "Fetch Project Insights", "type": "main", "index": 0}]]},
            "Periodic Health Schedule": {"main": [[{"node": "Fetch Project Insights", "type": "main", "index": 0}]]},
            "Fetch Project Insights": {"main": [[{"node": "Format Executive Report", "type": "main", "index": 0}]]}
        }
    }

    return secure_workflows(wfs)


def secure_workflows(workflows):
    """Bind interactive calls to their caller; a transport secret never grants PM authority."""
    for code, spec in workflows.items():
        trigger = next(n for n in spec["nodes"] if n["type"] == "n8n-nodes-base.webhook")
        if code == 'WF16':
            spec['name'] = 'WF16: Main Health Monitoring'
            trigger['parameters']['path'] = 'qldapm-monitoring'
            trigger['parameters']['responseMode'] = 'lastNode'
            schedule = next(n for n in spec['nodes'] if n['type']=='n8n-nodes-base.scheduleTrigger')
            schedule['parameters'] = {'rule':{'interval':[{'field':'cronExpression','expression':'0 */15 * * * *'}]}}
            schedule.pop('disabled',None)
            monitor = {'id':'monitor','name':'Probe And Persist Main Health','type':'n8n-nodes-base.httpRequest','typeVersion':4.2,
                'position':[600,240],'credentials':{'httpHeaderAuth':{'id':'qldapmMachineStatus','name':'QLDAPM Gateway status read only'}},
                'parameters':{'method':'GET','url':GATEWAY_URL+'/internal/automation/monitor','authentication':'genericCredentialType',
                    'genericAuthType':'httpHeaderAuth','options':{'timeout':30000,'redirect':{'redirect':{'followRedirects':False}}}}}
            spec['nodes'] = [trigger,schedule,monitor]
            spec['connections'] = {n['name']:{'main':[[{'node':monitor['name'],'type':'main','index':0}]]} for n in (trigger,schedule)}
            spec['settings'] = {**spec.get('settings',{}),'executionTimeout':35}
        if code == 'WF07':
            daily = json.loads((Path(__file__).parent / 'workflows/daily-brief.v2.json').read_text(encoding='utf-8'))
            machine_nodes = [n for n in daily['nodes'] if n['id'] in {'metadata','signature','report'}]
            report = next(n for n in machine_nodes if n['id'] == 'report')
            report['parameters']['url'] = GATEWAY_URL + '/internal/automation/commands'
            schedule = next(n for n in spec['nodes'] if n['type'] == 'n8n-nodes-base.scheduleTrigger')
            schedule['parameters'] = {'rule': {'interval': [{'field':'cronExpression','expression':'0 0 8 * * *'}]}}
            schedule.pop('disabled', None)
            trigger['parameters']['responseMode'] = 'lastNode'
            spec['nodes'] = [trigger,schedule,*machine_nodes]
            spec['connections'] = {n['name']:{'main':[[{'node':machine_nodes[0]['name'],'type':'main','index':0}]]}
                for n in (trigger,schedule)}
            for left,right in zip(machine_nodes,machine_nodes[1:]):
                spec['connections'][left['name']] = {'main':[[{'node':right['name'],'type':'main','index':0}]]}
            final = {'id':'daily_business_result','name':'Require Completed Daily Reports','type':'n8n-nodes-base.code',
                'typeVersion':2,'position':[950,240],'parameters':{'jsCode':
                    "if ($json.result?.state!=='COMPLETED' || $json.result?.status!=='READY') throw new Error('DAILY_REPORT_NOT_READY'); return $input.all();"}}
            spec['nodes'].append(final)
            spec['connections'][report['name']] = {'main':[[{'node':final['name'],'type':'main','index':0}]]}
            spec['settings'] = {**spec.get('settings',{}),'executionTimeout':60}
        if code=='WF03':
            spec['nodes']=[trigger,{'id':'orchestration_request','name':'Prepare Stable Orchestration Request',
                'type':'n8n-nodes-base.code','typeVersion':2,'position':[350,200],
                'parameters':{'jsCode':"""
const body=$input.first().json.body || {};
const uuid=value=>typeof value==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
if (body.operation==='status') return [{json:{action:'get_ai_run',arguments:{id:uuid(body.run_id)?body.run_id.toLowerCase():'invalid'}}}];
if (body.operation && !['start','plan'].includes(body.operation)) return [{json:{action:'INVALID_ORCHESTRATION_OPERATION'}}];
return [{json:{action:'start_ai_run',arguments:{prompt:body.prompt,engine:body.operation==='plan'?'supervisor_gemini':'gemini',run_class:'agent',allow_routine_writes:false},
  idempotency_key:uuid(body.request_id)?'wf03-'+body.request_id.toLowerCase():''}}];
"""}},{'id':'gateway_orchestration','name':'Start Or Poll Persisted Caller Run',
                'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[650,200],
                'parameters':{'method':'POST','url':GATEWAY_URL+'/api/v1/commands','sendBody':True,
                    'specifyBody':'json','jsonBody':'={{ $json }}','options':{}}}]
        if code == 'WF04':
            fetch=next(n for n in spec['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
            formatter=next(n for n in spec['nodes'] if n['type']=='n8n-nodes-base.code')
            formatter['parameters']['jsCode']="""
const response = $input.first().json;
if (response.statusCode >= 400) return [{json:{statusCode:response.statusCode, body:response.body}}];
const body=response.body;
const events=body.result?.items || [];
return [{json:{statusCode:response.statusCode, body:{status:'TRACE_RETRIEVED',total_events:events.length,
  events,correlation_id:body.correlation_id,fetched_at:new Date().toISOString()}}}];
"""
            spec['nodes']=[trigger,fetch,formatter]
        if code == "WF05":
            fetch = next(n for n in spec["nodes"] if n["type"] == "n8n-nodes-base.httpRequest")
            formatter = next(n for n in spec["nodes"] if n["type"] == "n8n-nodes-base.code")
            formatter["parameters"]["jsCode"] = """
const response = $input.first().json;
if (response.statusCode >= 400) return [{json:{statusCode:response.statusCode,body:response.body}}];
const proposal = response.body.result;
const request = $('Approval Request Webhook').first().json.body || {};
if (request.decision) return [{json:{statusCode:400,body:{error:'USE_WF06_FOR_EXACT_PM_DECISION'}}}];
if (!proposal?.id || !proposal?.hash) return [{json:{statusCode:502,body:{error:'PROPOSAL_RECEIPT_REQUIRED'}}}];
return [{json:{statusCode:response.statusCode,body:{status:proposal.lifecycle || proposal.state,proposal,
  correlation_id:response.body.correlation_id,human_confirmation_required:proposal.state==='pending',
  decision_recorded:proposal.state==='rejected' || proposal.state==='done'}}}];
"""
            spec["nodes"] = [trigger, fetch, formatter]
        if code == "WF06":
            spec["nodes"] = [trigger, {
                "id": "decision", "name": "Authenticated Gateway PM Decision", "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2, "position": [620, 200], "parameters": {"method": "POST",
                    "url": "=" + GATEWAY_URL + "/api/v1/proposals/{{ /^[0-9a-f-]{36}$/i.test($json.body?.proposal_id || '') ? $json.body.proposal_id : 'invalid' }}/decision",
                    "sendBody": True, "specifyBody": "json",
                    "jsonBody": "={{ {decision: $json.body?.decision, hash: $json.body?.hash} }}", "options": {}}}]
        if code=='WF15':
            spec['nodes']=[trigger,{'id':'reconcile','name':'Reconcile Exact Native SQLite Qdrant Identity',
                'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[600,200],
                'parameters':{'method':'POST','url':GATEWAY_URL+'/api/v1/commands','sendBody':True,
                    'specifyBody':'json','jsonBody':json.dumps({'action':'knowledge_integrity','arguments':{}}),'options':{}}}]
        if code=='WF14':
            spec['name']='WF14: Durable RAG Recovery'
            spec['nodes']=[trigger,{'id':'recovery_request','name':'Prepare Durable RAG Recovery Request',
                'type':'n8n-nodes-base.code','typeVersion':2,'position':[350,200],
                'parameters':{'jsCode':"""
const body=$input.first().json.body || {};
const uuid=value=>typeof value==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
if (!uuid(body.job_id)) return [{json:{action:'INVALID_RECOVERY_JOB_ID'}}];
const id=body.job_id.toLowerCase();
if (body.operation==='retry') return [{json:{action:'knowledge_sync_retry',arguments:{id},
  idempotency_key:uuid(body.request_id)?'wf14-'+body.request_id.toLowerCase():''}}];
if (body.operation && body.operation!=='status') return [{json:{action:'INVALID_RECOVERY_OPERATION'}}];
return [{json:{action:'knowledge_sync_status',arguments:{id}}}];
"""}},{'id':'gateway_recovery','name':'Read Or Requeue Own Persisted RAG Job',
                'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[650,200],
                'parameters':{'method':'POST','url':GATEWAY_URL+'/api/v1/commands','sendBody':True,
                    'specifyBody':'json','jsonBody':'={{ $json }}','options':{}}}]
        if code=='WF08':
            spec['name']='WF08: Sprint Risk'
            trigger['name']='Sprint Risk Webhook'
            trigger['parameters']['path']='qldapm-sprint-risk'
            spec['nodes']=[trigger,{'id':'sprint_parameters','name':'Prepare Sprint Risk Parameters',
                'type':'n8n-nodes-base.code','typeVersion':2,'position':[350,200],
                'parameters':{'jsCode':"""
const body=$input.first().json.body || {};
const args={};
if (Object.hasOwn(body,'as_of_date')) args.as_of_date=body.as_of_date;
if (Object.hasOwn(body,'sprint_id')) args.sprint_id=body.sprint_id;
return [{json:{action:'sprint_risks',arguments:args}}];
"""}},{'id':'sprint_risks','name':'Analyze Native Relations And Persist Risk Snapshot',
                'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[650,200],
                'parameters':{'method':'POST','url':GATEWAY_URL+'/api/v1/commands','sendBody':True,
                    'specifyBody':'json','jsonBody':'={{ $json }}','options':{}}}]
        if code=='WF12':
            spec['name']='WF12: Weekly Summary'
            trigger['name']='Weekly Summary Webhook'
            trigger['parameters']['path']='qldapm-weekly-summary'
            spec['nodes']=[trigger,{'id':'weekly_parameters','name':'Prepare Weekly Parameters',
                'type':'n8n-nodes-base.code','typeVersion':2,'position':[350,200],
                'parameters':{'jsCode':"""
const body=$input.first().json.body || {};
const args={};
if (Object.hasOwn(body,'as_of_date')) args.as_of_date=body.as_of_date;
return [{json:{action:'weekly_summary',arguments:args}}];
"""}},{'id':'weekly_summary','name':'Generate And Persist Native Weekly Summary',
                'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[650,200],
                'parameters':{'method':'POST','url':GATEWAY_URL+'/api/v1/commands','sendBody':True,
                    'specifyBody':'json','jsonBody':'={{ $json }}','options':{}}}]
        if code in {'WF01', 'WF02', 'WF09', 'WF10', 'WF13'}:
            # These legacy adapters claimed completion from constants or silently indexed WP38.
            prepare = "return [{json:{action:'get_project_options',arguments:{}}}];" if code == 'WF10' else """
const body=$input.first().json.body || {};
if (!Number.isSafeInteger(body.id) || body.id<=0) return [{json:{action:'INVALID_EXPLICIT_NATIVE_TARGET'}}];
"""
            if code == 'WF09':
                prepare += "return [{json:{action:'get_work_package',arguments:{id:body.id,include_context:true}}}];"
                prepare = """
const body=$input.first().json.body || {};
if (!body.operation) {
  if (!Number.isSafeInteger(body.id) || body.id<=0) return [{json:{action:'INVALID_EXPLICIT_NATIVE_TARGET'}}];
  return [{json:{action:'get_work_package',arguments:{id:body.id,include_context:true}}}];
}
if (['actor_id','role','admin','owner','approved','qa_pass','auto_execute'].some(k=>Object.hasOwn(body,k)))
  return [{json:{action:'INVALID_BUG_AUTHORITY_CLAIM'}}];
if (body.operation==='triage') {
  const args={};
  if (Object.hasOwn(body,'id')) args.id=body.id;
  if (Object.hasOwn(body,'report')) args.report=body.report;
  return [{json:{action:'bug_triage',arguments:args}}];
}
if (!['create','assign','fix','retest','review','transition'].includes(body.operation) ||
    typeof body.request_id!=='string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(body.request_id))
  return [{json:{action:'INVALID_BUG_PROPOSAL_REQUEST'}}];
const args={operation:body.operation};
for (const key of ['id','lock_version','report','source_id','duplicate_disposition','assignee_id','text','status_id','qa_evidence_id','qa_evidence_hash'])
  if (Object.hasOwn(body,key)) args[key]=body[key];
return [{json:{action:'bug_propose',arguments:args,idempotency_key:'wf09-'+body.request_id.toLowerCase()}}];
"""
            elif code != 'WF10':
                operation = {'WF01':'ingest', 'WF02':'upsert', 'WF13':'reindex'}[code]
                prepare += """
const uuid=value=>typeof value==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
if (!uuid(body.request_id) || body.file_path || body.path) return [{json:{action:'INVALID_NATIVE_INGEST_REQUEST'}}];
"""
                prepare += "if (body.operation && body.operation!==" + json.dumps(operation) + ") return [{json:{action:'UNSUPPORTED_NATIVE_INGEST_OPERATION'}}];\n"
                prepare += "return [{json:{action:'knowledge_ingest',arguments:{id:body.id},idempotency_key:'" + code.lower() + "-'+body.request_id.toLowerCase()}}];"
            if code == 'WF01':
                prepare = """
const fileBody=$input.first().json.body || {};
if (Object.hasOwn(fileBody,'source_key')) {
  if (typeof fileBody.source_key!=='string' || !/^[a-z0-9][a-z0-9_-]{0,63}$/.test(fileBody.source_key) ||
      ['id','path','file_path','content','project_id'].some(k=>Object.hasOwn(fileBody,k)))
    return [{json:{action:'INVALID_FILE_SOURCE_REQUEST'}}];
  const operation=fileBody.operation || 'ingest';
  const args={source_key:fileBody.source_key};
  if (operation==='search') {
    args.query=fileBody.query;
    if (Object.hasOwn(fileBody,'limit')) args.limit=fileBody.limit;
    return [{json:{action:'knowledge_file_search',arguments:args}}];
  }
  if (operation==='read') return [{json:{action:'knowledge_file_read',arguments:{...args,document_id:fileBody.document_id}}}];
  if (!['ingest','reindex'].includes(operation) || typeof fileBody.request_id!=='string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(fileBody.request_id))
    return [{json:{action:'INVALID_FILE_INGEST_REQUEST'}}];
  return [{json:{action:'knowledge_file_ingest',arguments:args,idempotency_key:'wf01-file-'+fileBody.request_id.toLowerCase()}}];
}
""" + prepare
                prepare = enable_project6_files(prepare)
            if code == 'WF02':
                prepare = """
const syncBody=$input.first().json.body || {};
if (['sync','status'].includes(syncBody.operation)) {
  if (['id','path','file_path','source_key','content'].some(k=>Object.hasOwn(syncBody,k)))
    return [{json:{action:'INVALID_INCREMENTAL_SYNC_REQUEST'}}];
  if (syncBody.operation==='status') return [{json:{action:'knowledge_incremental_status',arguments:{}}}];
  if (typeof syncBody.request_id!=='string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(syncBody.request_id))
    return [{json:{action:'INVALID_INCREMENTAL_SYNC_REQUEST'}}];
  return [{json:{action:'knowledge_incremental_sync',arguments:{},idempotency_key:'wf02-sync-'+syncBody.request_id.toLowerCase()}}];
}
""" + prepare
            if code == 'WF13':
                prepare = """
const feedback=$input.first().json.body || {};
const validFeedbackId=value=>typeof value==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
if (['feedback_submit','feedback_get','feedback_decision','feedback_apply'].includes(feedback.operation)) {
  if (['path','file_path','content','project_id'].some(k=>Object.hasOwn(feedback,k)))
    return [{json:{action:'INVALID_FEEDBACK_REQUEST'}}];
  if (feedback.operation==='feedback_submit') {
    if (!validFeedbackId(feedback.request_id)) return [{json:{action:'INVALID_FEEDBACK_REQUEST'}}];
    const args={note:feedback.note};
    if (Object.hasOwn(feedback,'native_id')) args.native_id=feedback.native_id;
    if (Object.hasOwn(feedback,'source_key')) args.source_key=feedback.source_key;
    return [{json:{action:'knowledge_feedback_submit',arguments:args,idempotency_key:'wf13-feedback-'+feedback.request_id.toLowerCase()}}];
  }
  if (!validFeedbackId(feedback.feedback_id)) return [{json:{action:'INVALID_FEEDBACK_REQUEST'}}];
  const id=feedback.feedback_id.toLowerCase();
  if (feedback.operation==='feedback_get') return [{json:{action:'knowledge_feedback_get',arguments:{id}}}];
  if (feedback.operation==='feedback_decision') return [{json:{feedback_decision:true,feedback_id:id,payload:{decision:feedback.decision,hash:feedback.hash}}}];
  if (!validFeedbackId(feedback.request_id)) return [{json:{action:'INVALID_FEEDBACK_REQUEST'}}];
  return [{json:{action:'knowledge_feedback_apply',arguments:{id},idempotency_key:'wf13-apply-'+feedback.request_id.toLowerCase()}}];
}
""" + prepare
            if code == 'WF10':
                prepare = """
const body=$input.first().json.body || {};
if (!['draft','get','adopt','next','from_ba','dependency','dependency_update','dependency_delete'].includes(body.operation)) return [{json:{action:'get_project_options',arguments:{}}}];
if (['actor_id','role','admin','owner','approved','auto_execute','parent_id','native_id','type_id','scope_hash','proposal_id','proposal_hash'].some(k=>Object.hasOwn(body,k)))
  return [{json:{action:'INVALID_WBS_AUTHORITY_OR_PARENT_CLAIM'}}];
const fields={draft:['requirements','nodes','share_for_review','relations'],get:['id'],adopt:['id','hash'],next:['id','hash','retry_hash'],from_ba:['run_id','output_hash','share_for_review'],dependency:['predecessor_id','successor_id','lag'],dependency_update:['relation_id','lag'],dependency_delete:['relation_id']};
if (['dependency_update','dependency_delete'].includes(body.operation) && Object.keys(body).some(key=>!['operation','request_id',...fields[body.operation]].includes(key)))
  return [{json:{action:'INVALID_DEPENDENCY_CHANGE_FIELD'}}];
const args={};
for (const key of fields[body.operation]) if (Object.hasOwn(body,key)) args[key]=body[key];
if (body.operation==='get') return [{json:{action:'wbs_get',arguments:args}}];
if (typeof body.request_id!=='string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(body.request_id))
  return [{json:{action:'INVALID_WBS_REQUEST_KEY'}}];
const dependencyActions={dependency:'create_dependency',dependency_update:'update_dependency',dependency_delete:'delete_dependency'};
return [{json:{action:dependencyActions[body.operation] || 'wbs_'+body.operation,arguments:args,idempotency_key:'wf10-'+body.request_id.toLowerCase()}}];
"""
            spec['nodes'] = [trigger, {'id':'explicit_request','name':'Prepare Explicit Caller Request',
                'type':'n8n-nodes-base.code','typeVersion':2,'position':[350,200],'parameters':{'jsCode':prepare}},
                {'id':'gateway_request','name':'Return Actual Gateway Result',
                'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[650,200],
                'parameters':{'method':'POST','url':GATEWAY_URL+'/api/v1/commands','sendBody':True,
                    'specifyBody':'json','jsonBody':'={{ $json }}','options':{}}}]
            if code == 'WF13':
                spec['nodes'][-1]['parameters']['url'] = "={{ $json.feedback_decision ? " + json.dumps(GATEWAY_URL+'/api/v1/knowledge-feedback/') + " + $json.feedback_id + '/decision' : " + json.dumps(GATEWAY_URL+'/api/v1/commands') + " }}"
                spec['nodes'][-1]['parameters']['jsonBody'] = '={{ $json.feedback_decision ? $json.payload : $json }}'
        if code == 'WF11':
            spec['nodes'] = [trigger, {'id':'qa_target','name':'Require Explicit QA Target',
                'type':'n8n-nodes-base.code','typeVersion':2,'position':[350,200],
                'parameters':{'jsCode':"""
const body=$input.first().json.body || {};
if (['capture','get','review','transition_prepare','run','run_get','from_run','list'].includes(body.operation)) {
  const fields={capture:['operation','native_id','activity_id','request_id'],get:['operation','evidence_id'],
    review:['operation','evidence_id','decision','hash'],transition_prepare:['operation','evidence_id','hash','status_id','request_id'],
    run:['operation','native_id','request_id'],run_get:['operation','run_id'],from_run:['operation','run_id','request_id'],list:['operation']};
  const invalid=()=>[{json:{action:'INVALID_QA_EVIDENCE_REQUEST'}}];
  const uuid=value=>typeof value==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
  if (Object.keys(body).some(k=>!fields[body.operation].includes(k))) return invalid();
  if (body.operation==='list') return [{json:{action:'qa_evidence_list',arguments:{}}}];
  if (body.operation==='run') {
    if (!uuid(body.request_id) || !Number.isSafeInteger(body.native_id) || body.native_id<=0) return invalid();
    return [{json:{action:'qa_test_run',arguments:{native_id:body.native_id},idempotency_key:'wf11-'+body.request_id.toLowerCase()}}];
  }
  if (body.operation==='run_get' || body.operation==='from_run') {
    if (!uuid(body.run_id) || body.operation==='from_run' && !uuid(body.request_id)) return invalid();
    return [{json:{action:body.operation==='run_get'?'qa_test_get':'qa_evidence_from_run',arguments:body.operation==='run_get'?{id:body.run_id.toLowerCase()}:{run_id:body.run_id.toLowerCase()},...(body.operation==='from_run'?{idempotency_key:'wf11-'+body.request_id.toLowerCase()}:{})}}];
  }
  if (body.operation==='capture') {
    if (!uuid(body.request_id) || !Number.isSafeInteger(body.native_id) || body.native_id<=0 || !Number.isSafeInteger(body.activity_id) || body.activity_id<=0) return invalid();
    return [{json:{action:'qa_evidence_capture',arguments:{native_id:body.native_id,activity_id:body.activity_id},idempotency_key:'wf11-'+body.request_id.toLowerCase()}}];
  }
  if (!uuid(body.evidence_id)) return invalid();
  const id=body.evidence_id.toLowerCase();
  if (body.operation==='get') return [{json:{action:'qa_evidence_get',arguments:{id}}}];
  if (typeof body.hash!=='string' || !/^[a-f0-9]{64}$/.test(body.hash)) return invalid();
  if (body.operation==='review') {
    if (!['accept','reject'].includes(body.decision)) return invalid();
    return [{json:{qa_decision:true,evidence_id:id,payload:{decision:body.decision,hash:body.hash}}}];
  }
  if (!uuid(body.request_id) || !Number.isSafeInteger(body.status_id) || body.status_id<=0) return invalid();
  return [{json:{action:'qa_transition_prepare',arguments:{id,hash:body.hash,status_id:body.status_id},idempotency_key:'wf11-'+body.request_id.toLowerCase()}}];
}
const id=body.id;
if (!Number.isSafeInteger(id) || id<=0) return [{json:{action:'INVALID_QA_TARGET'}}];
return [{json:{action:'qa_evidence_list',arguments:{native_id:id}}}];
"""}}, {'id':'qa_gate','name':'Read Native Evidence And Transition Errors',
                'type':'n8n-nodes-base.httpRequest','typeVersion':4.2,'position':[650,200],
                'parameters':{'method':'POST','url':GATEWAY_URL+'/api/v1/commands','sendBody':True,
                    'specifyBody':'json','jsonBody':'={{ $json }}','options':{}}}]
            spec['nodes'][-1]['parameters']['url'] = "={{ $json.qa_decision ? " + json.dumps(GATEWAY_URL+'/api/v1/qa-evidence/') + " + $json.evidence_id + '/decision' : " + json.dumps(GATEWAY_URL+'/api/v1/commands') + " }}"
            spec['nodes'][-1]['parameters']['jsonBody'] = '={{ $json.qa_decision ? $json.payload : $json }}'
        if code not in {'WF07','WF16'}:
            trigger['parameters']['responseMode']='responseNode'
            fetch=next(n for n in spec['nodes'] if n['type']=='n8n-nodes-base.httpRequest')
            fetch['parameters'].setdefault('options',{})['response']={'response':{
                'fullResponse':True,'neverError':True,'responseFormat':'json'}}
            spec['nodes'].append({'id':'reply_gateway_status','name':'Reply With Gateway Status',
                'type':'n8n-nodes-base.respondToWebhook','typeVersion':1.4,'position':[1050,200],
                'parameters':{'respondWith':'json','responseBody':'={{ $json.body }}',
                    'options':{'responseCode':'={{ $json.statusCode }}'}}})
            spec['connections']={left['name']:{'main':[[{'node':right['name'],'type':'main','index':0}]]}
                for left,right in zip(spec['nodes'],spec['nodes'][1:])}
        spec["settings"] = {**spec.get("settings", {}), "executionOrder": "v1", "timezone": "Asia/Bangkok",
            "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none",
            "saveManualExecutions": False, "saveExecutionProgress": False}
        for node in spec["nodes"]:
            if node["type"] == "n8n-nodes-base.scheduleTrigger":
                if code not in {'WF07','WF16'}:
                    # Other schedules still lack a bounded machine operation.
                    node["disabled"] = True
            parameters = node.get("parameters", {})
            if node["type"] != "n8n-nodes-base.httpRequest" or GATEWAY_URL not in parameters.get("url", ""):
                continue
            if (code == 'WF07' and node['id'] == 'report') or (code == 'WF16' and node['id'] == 'monitor'):
                node['retryOnFail'] = False
                continue
            node.pop("credentials", None)
            node["retryOnFail"] = False
            parameters.pop("genericAuthType", None)
            parameters["authentication"] = "none"
            parameters["sendHeaders"] = True
            parameters["headerParameters"] = {"parameters": [{"name": "Authorization",
                "value": "={{ $('" + trigger["name"] + "').first().json.headers.authorization || '' }}"}]}
            parameters.setdefault("options", {})["redirect"] = {"redirect": {"followRedirects": False}}
        if code == 'WF12':
            daily=json.loads((Path(__file__).parent/'workflows/daily-brief.v2.json').read_text(encoding='utf-8'))
            machine=[n for n in daily['nodes'] if n['id'] in {'metadata','signature','report'}]
            for node in machine:
                node['id']='weekly_'+node['id']
                node['name']='Weekly '+node['name']
            machine[0]['parameters']['jsonOutput']="={{ { version: 1, kind: 'weekly_summary', request_key: 'weekly:' + $now.setZone('Asia/Bangkok').startOf('week').toISODate(), nonce: 'n8n:' + $workflow.id + ':' + $execution.id, issued_at: Math.floor($now.toSeconds()) } }}"
            machine[-1]['parameters']['url']=GATEWAY_URL+'/internal/automation/commands'
            machine[-1]['parameters']['options']['timeout']=100000
            machine[-1]['retryOnFail']=False
            machine.append({'id':'weekly_business_result','name':'Verify weekly business completion',
                'type':'n8n-nodes-base.code','typeVersion':2,'position':[900,450],
                'parameters':{'jsCode':"if ($json.result?.state!=='COMPLETED' || $json.result?.status!=='READY') throw new Error('WEEKLY_REPORT_NOT_READY'); return $input.all();"}})
            schedule={'id':'weekly_schedule','name':'Weekly Friday 17:00','type':'n8n-nodes-base.scheduleTrigger',
                'typeVersion':1.2,'position':[100,450],
                'parameters':{'rule':{'interval':[{'field':'cronExpression','expression':'0 0 17 * * 5'}]}}}
            spec['nodes'][-1:-1]=[schedule,*machine]
            for left,right in zip([schedule,*machine],machine):
                spec['connections'][left['name']]={'main':[[{'node':right['name'],'type':'main','index':0}]]}
            spec['settings']['executionTimeout']=120
    from automation.n8n_lifecycle_adapter import attach_lifecycle_adapter
    workflows['WF04'] = attach_lifecycle_adapter(workflows['WF04'], GATEWAY_URL)
    return {code:enable_project6_business(spec) for code,spec in workflows.items()}


def deploy():
    if not COOKIE:
        raise SystemExit("QLDAPM_N8N_SESSION must be supplied privately; deployment requires operator approval")
    print("Fetching existing n8n workflows...")
    r = requests.get(f"{N8N_BASE}/rest/workflows", headers=HEADERS, timeout=10)
    existing = {wf["name"][:4]: wf for wf in r.json().get("data", [])}
    print(f"Found {len(existing)} existing workflows: {list(existing.keys())}")

    workflows = {}
    for code, info in existing.items():
        if code not in {f"WF{i:02d}" for i in range(1, 17)}:
            continue
        response = requests.get(f"{N8N_BASE}/rest/workflows/{info['id']}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        current = response.json()["data"]
        workflows[code] = {key: current[key] for key in ("name", "nodes", "connections", "settings")}
    workflows = secure_workflows(workflows)
    results = {}

    for code, spec in workflows.items():
        if code not in existing:
            print(f"Workflow {code} not found in n8n; skipping.")
            continue
        wf_info = existing[code]
        wfid = wf_info["id"]
        print(f"Deploying {code} ({spec['name']}) [ID: {wfid}]...")

        # Update workflow
        patch_res = requests.patch(
            f"{N8N_BASE}/rest/workflows/{wfid}",
            headers=HEADERS,
            json={
                "name": spec["name"],
                "nodes": spec["nodes"],
                "connections": spec["connections"],
                "settings": spec["settings"]
            },
            timeout=10
        )
        if patch_res.status_code != 200:
            print(f"  PATCH failed: HTTP {patch_res.status_code}")
            results[code] = ("PATCH_FAILED", patch_res.status_code)
            continue

        # Get latest versionId
        wf_fresh = requests.get(f"{N8N_BASE}/rest/workflows/{wfid}", headers=HEADERS, timeout=10).json()["data"]
        version_id = wf_fresh.get("versionId")

        # Deactivate then activate
        requests.post(f"{N8N_BASE}/rest/workflows/{wfid}/deactivate", headers=HEADERS, timeout=10)
        act_res = requests.post(
            f"{N8N_BASE}/rest/workflows/{wfid}/activate",
            headers=HEADERS,
            json={"versionId": version_id},
            timeout=10
        )
        active = act_res.json().get("data", {}).get("active", False)
        print(f"  Activation status: {act_res.status_code}, Active: {active}")
        results[code] = ("PASS" if active else "INACTIVE", act_res.status_code)

    print("\nDEPLOYMENT RESULTS:")
    for code, (status, code_num) in results.items():
        print(f"  {code}: {status} (HTTP {code_num})")


if __name__ == "__main__":
    deploy()
