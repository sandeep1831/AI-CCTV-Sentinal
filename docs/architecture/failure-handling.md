# Failure Handling

**Status: CURRENT design** (configuration + interface contracts exist; actual reconnect/retry logic implementation is FUTURE).

See [`docs/diagrams/08-failure-recovery-flow.mermaid`](../diagrams/08-failure-recovery-flow.mermaid).

## Camera failure handling

```text
Camera stream → Heartbeat → Healthy?
    Yes → Process
    No  → Reconnect → Retry policy → Alert admin (if retries exhausted)
```

Camera status is one of `ONLINE | DEGRADED | OFFLINE | RECONNECTING` (`backend.schemas.camera.CameraStatus`). Reconnect behavior (initial delay, max delay, backoff multiplier, heartbeat interval) is configured in `configs/video.yaml` under `ingestion.reconnect` — never hard-coded.

## AI failure handling

```text
Inference error → Log error → Retry → Continue stream
```

An inference failure on one frame must never crash the backend or halt the stream. `Detector.predict()` implementations are expected to raise a typed exception that calling code catches, logs, and recovers from — not to propagate an unhandled crash.

## Failure isolation

The following failure domains are designed to be independent, so that one failing subsystem does not cascade into another:

```text
Camera failure
AI failure
Database failure
Notification failure
IoT failure
```

Each corresponds to a distinct component boundary (`VideoSource`, `Detector`/`Tracker`, storage layer, `AlertManager` channels, IoT integration) with its own error handling, per `docs/architecture/component-architecture.md`.

## Offline / fallback mode

If internet connectivity is unavailable, the edge node continues operating locally:

```text
CCTV → Edge AI → Local detection → Local alarm → Local event queue
```

`configs/system.yaml` defines `offline_mode.local_event_queue_path` and `offline_mode.sync_on_reconnect`. When connectivity returns, the local queue synchronizes with the backend rather than being lost.

## What's implemented vs designed only

| Behavior | Status |
|---|---|
| Camera status enum + reconnect config schema | CURRENT |
| Actual RTSP reconnect logic | FUTURE |
| AI failure isolation contract (interface-level) | CURRENT |
| Actual retry/backoff implementation | FUTURE |
| Offline queue config | CURRENT |
| Actual local queue + sync implementation | FUTURE |
