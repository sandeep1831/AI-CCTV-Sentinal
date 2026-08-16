# Deployment Architecture

**Status: CURRENT** design, **FUTURE** execution (only the Development profile's environment — not its full pipeline — exists today, from Task 1).

See [`docs/diagrams/07-deployment-architecture.mermaid`](../diagrams/07-deployment-architecture.mermaid).

## Two profiles

### Development (CURRENT environment, FUTURE pipeline wiring)

```text
Recorded video / local webcam
        ↓
Developer PC (Windows, CPU or local GPU)
        ↓
YOLO26n (verified in Task 1)
        ↓
FastAPI (localhost, verified in Task 1)
```

Used for building and testing individual components against recorded or local video, without any real CCTV dependency.

### Pilot (FUTURE)

```text
Existing CCTV / NVR
        ↓
Private LAN
        ↓
Edge GPU / Server
        ↓
FastAPI
        ↓
PostgreSQL
        ↓
Dashboard / Mobile
        ↓
IoT Alarm
```

Used once real cameras are connected on-site. Requires the database, dashboard/mobile client, and IoT integration — all explicitly out of scope for Task 2.

## Why edge-first

CCTV video is high-bandwidth and latency-sensitive. The architecture keeps inference at the edge and only sends **metadata + event snapshot** to any backend/cloud component — never continuous raw video (see `security-architecture.md` and `privacy` sections below).

```text
CCTV → Local Network → Edge AI → Detection → metadata + snapshot only → Backend → Dashboard/Mobile
```

This reduces bandwidth use, reduces latency, reduces privacy exposure, and removes a hard dependency on cloud/internet availability (see Offline/Fallback Mode).

## Export path (FUTURE, not performed in Task 2)

Ultralytics' current stack documents exporting YOLO26 to ONNX, TensorRT, OpenVINO, and other formats for edge deployment. This is deferred until a specific edge target (e.g. Jetson, industrial PC) is chosen and real latency is measured — no export figures should be assumed from literature.

## Latency budget (conceptual only)

```text
Frame capture + Preprocessing + Inference + Tracking + Temporal logic + Risk calculation + Alert generation
```

No fixed end-to-end latency number is promised here; it must be measured on the actual target hardware once deployed, per the reference paper's caution against assuming literature latency figures.
