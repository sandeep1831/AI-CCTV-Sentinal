# Backend API — Architectural Contracts

**Status: CURRENT contract, FUTURE implementation.** Only `/` and `/health` exist today (Task 1). Everything below defines *responsibility*, not working endpoints — per Task 2 §18-19: "these are architectural contracts; implementation belongs to later tasks."

Framework: **FastAPI** — chosen for typed request/response models, dependency injection, WebSocket support, automatic OpenAPI docs, and testability.

## Route groups

| Group | Base path | Responsibility |
|---|---|---|
| Cameras | `/api/v1/cameras` | Expose configured camera metadata and status |
| Detections | `/api/v1/detections` | Ingest raw detector output (from edge) / query recent detections |
| Events | `/api/v1/events` | Query confirmed, risk-scored events |
| Alerts | `/api/v1/alerts` | Query alerts; record human acknowledgement |
| Feedback | `/api/v1/feedback` | Submit CONFIRM/DISMISS/UNCERTAIN judgments |
| Models | `/api/v1/models` | Query model registry / current production version |
| System | `/api/v1/system` | Health and operational metrics |

## Endpoint responsibilities

### Cameras
- `GET /api/v1/cameras` — list configured cameras and their current status.
- `GET /api/v1/cameras/{camera_id}` — detail for one camera, including its zones.

### Detections
- `POST /api/v1/detections` — accept a batch of raw `Detection` records from an edge node.
- `GET /api/v1/detections` — query recent raw detections (debugging/observability, not the primary consumer path).

### Events
- `GET /api/v1/events` — list confirmed `Event` records, filterable by camera/zone/risk level/time range.
- `GET /api/v1/events/{event_id}` — full detail for one event, including its risk reasoning.

### Alerts
- `GET /api/v1/alerts` — list dispatched `Alert` records.
- `POST /api/v1/alerts/{event_id}/acknowledge` — record human acknowledgement of the alert(s) for an event.

### Feedback
- `POST /api/v1/feedback` — submit a `Feedback` record (CONFIRM/DISMISS/UNCERTAIN) for an event.

### Models
- `GET /api/v1/models` — list registered `ModelVersion` records and their lifecycle state.
- `GET /api/v1/models/current` — the model version currently serving PRODUCTION traffic.

### System
- `GET /api/v1/system/health` — aggregate AI / camera / database / notification / IoT status.
- `GET /api/v1/system/metrics` — observability metrics (see `docs/architecture/system-architecture.md` and `configs/system.yaml` → `observability.tracked_metrics`).

## Request/response bodies

All request and response bodies use the schemas in `backend/schemas/` (`Camera`, `Detection`, `Track`, `Event`, `Alert`, `Feedback`, `ModelVersion`, …) so the API layer never invents its own ad-hoc shapes.
