# Vexa External API Interfaces

This document catalogs all outward‑facing APIs and published contracts that **vexa** dispatches for external consumption.  Sources: `architecture.calm.json`, `contracts.seal.json`, and the corresponding source directories.

## 1. Service‑level APIs (HTTP / WebSocket / RPC)

| Interface | Type | Path (source) | Description |
|-----------|------|---------------|-------------|
| **agent-api-rest** | API | `core/agent/services/agent-api` | Unit control‑plane; dispatches work to the runtime spawn and provides the meeting‑copilot endpoint. |
| **gateway-rest** | API | `core/gateway/services/gateway` | Edge API: auth (scopes), REST routing, and WebSocket fan‑out. |
| **gateway-ws** | WebSocket | `core/gateway/services/gateway` | WebSocket endpoint for real‑time session streaming from the gateway. |
| **admin-api-rest** | API | `core/identity/services/admin-api` | Identity service: token mint/validate, user management, and per‑user calendar connections. |
| **stt-endpoint** | API | `core/meetings/services/transcription` | Speech‑to‑text endpoint (first‑party STT via `faster‑whisper`/`CTranslate2` or OpenAI‑compatible `/v1/audio/transcriptions`). |
| **desktop-rest** | API | `core/meetings/services/desktop` | All‑in‑one dev host combining bot, collector, and gateway in a single process. |
| **desktop-ingest-ws** | WebSocket | `core/meetings/services/desktop` | WebSocket for live audio ingestion into the desktop host. |
| **meeting-api-rest** | API | `core/meetings/services/meeting-api` | Meeting hub: collector, bot‑spawn, recordings, sessions, and calendar import/autojoin. |
| **service-authority-rest** | API | `core/meetings/contracts/service-authority.v1` | Optional operator‑provided admission/continue decision endpoint (outside the core OSS). |
| **system-webhook-rest** | API | `core/meetings/contracts/webhook.v1` | Optional operator‑provided signed webhook endpoint for `meeting.completed` and `bot.failed` events. |
| **mcp-http** | API (FastAPI) | `core/meetings/services/mcp` | stateless FastAPI mount at `/mcp` exposing tools & prompts over HTTP. |
| **runtime-rest** | API | `core/runtime/src` | Runtime kernel: `POST /workloads` to spawn containers (Docker/K8s/process). |

## 2. Published Contract Schemas (versioned data contracts)

| Contract | Path (source) | Domain |
|----------|---------------|--------|
| **api.v1** | `core/gateway/contracts/api.v1` | Gateway public contract. |
| **ws.v1** | `core/gateway/contracts/ws.v1` | Gateway WebSocket contract. |
| **identity.v1** | `core/identity/contracts/identity.v1` | Identity contract (users, API tokens). |
| **acts.v1** | `core/meetings/contracts/acts.v1` | Meeting actions contract (leave/speak). |
| **captured-signal.v1** | `core/meetings/contracts/captured-signal.v1` | Captured signal contract. |
| **flagged-issue.v1** | `core/meetings/contracts/flagged-issue.v1` | Flagged issue contract. |
| **invocation.v1** | `core/meetings/contracts/invocation.v1` | Invocation contract. |
| **lifecycle.v1** | `core/meetings/contracts/lifecycle.v1` | Bot status contract with transition timing. |
| **service-authority.v1** | `core/meetings/contracts/service-authority.v1` | Service‑authority admission contract (opt‑in). |
| **transcript.v1** | `core/meetings/contracts/transcript.v1` | Raw transcript contract. |
| **webhook.v1** | `core/meetings/contracts/webhook.v1` | Delivery contract for terminal events. |
| **runtime.v1** | `core/runtime/contracts/runtime.v1` | Runtime contract (workload model). |
| **schedule.v1** | `core/runtime/contracts/schedule.v1` | Scheduling contract for workloads. |
| **execution-targets.v1** | `deploy/contracts/execution-targets.v1` | Deployment target contract. |
| **config.v1** | `deploy/contracts/config.v1` | Per‑service deployment config contract. |

## 3. Client SDKs (published libraries)

| SDK | Path | Notes |
|-----|------|-------|
| **vexa‑client** | `sdks/` | Public client library (governed by P1–P12). |
| **vexa‑cli** | `sdks/` | CLI entry point (part of the same SDK surface). |
| **transcript‑rendering** | `sdks/` | Transcript rendering utilities. |

*Governed by `docs/docs/governance/architecture.mdx` (P1–P12). The SDK surface is its `index`/contract; it may depend only on what the dependency rules allow.*

---

**Note:** All interfaces listed above are the *single writers* or *read‑only* surfaces defined by the architecture model.  Consumers must adhere to the rendered contracts (`*.v1`) and must not re‑derive producer data (P23 single‑writer control).