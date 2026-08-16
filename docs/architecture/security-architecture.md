# Security & Privacy Architecture

**Status: CURRENT design.** Authentication/authorization implementation is FUTURE (Task 1's FastAPI skeleton has no auth yet).

## Network posture

```text
CCTV → Private LAN → Edge Server → Authenticated API → Authorized Dashboard
```

- Raw RTSP streams are never exposed publicly — they stay on the private LAN between cameras and the edge server.
- Only the authenticated API surface (and, later, the dashboard/mobile app) is reachable outside that LAN.

## Required security controls (design targets for later tasks)

- Authentication and authorization on every non-public API route.
- HTTPS required in production (`configs/system.yaml` → `api.require_https_in_production`); local development may run plain HTTP.
- All secrets (RTSP credentials, database URL, MQTT credentials, Firebase project ID) come from environment variables — see `.env.example` and `backend/core/config.py`. None are ever placed in YAML or source code.
- API input validation via Pydantic schemas (`backend/schemas/`) on every request/response boundary.
- Audit logs for admin actions (model promotion/rollback, camera enable/disable, user management).
- Restricted admin actions — e.g. only authorized roles may acknowledge CRITICAL alerts or call `ModelRegistry.promote()` / `.rollback()`.

## Secret handling contract

`configs/camera.yaml` never stores a literal RTSP URL — only a `url_env` reference to an environment variable name (see `backend.core.config.resolve_env_reference`). The same pattern applies to any other credential-shaped configuration. `.gitignore` excludes `.env` and all `.env.*` files except `.env.example`.

## Privacy architecture

The system incidentally captures people on campus, so it is designed to minimize what is retained:

```text
Raw video → Local processing (edge only) → Event snapshot only when required → Controlled storage
```

- Continuous raw video is **never** uploaded or stored centrally — only per-event metadata and, where necessary, a single snapshot/short clip tied to a specific `Event` (`backend.schemas.event.Event.snapshot_uri`).
- Retention of stored snapshots must be configurable (FUTURE — retention policy is not implemented in Task 2).
- Access to stored event media must be restricted and auditable (FUTURE).
- These practices apply even during pilot deployment, not just as a theoretical goal.

## What's implemented vs designed only

| Control | Status |
|---|---|
| Env-var-only secrets pattern | CURRENT |
| `.gitignore` excludes secrets/weights/datasets | CURRENT |
| Pydantic request/response validation shapes | CURRENT (schemas defined) |
| Actual authentication/authorization | FUTURE |
| HTTPS termination | FUTURE (config flag exists) |
| Audit log implementation | FUTURE |
| Snapshot retention policy enforcement | FUTURE |
