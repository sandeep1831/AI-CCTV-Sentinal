"""AI-CCTV Sentinel — Full Task 1 environment verification.

Checks Python, PyTorch, CUDA/GPU, Ultralytics, YOLO26, OpenCV,
FastAPI, and Pydantic. A missing GPU is reported but does not fail
the overall check — this system must run correctly on CPU-only
machines as well as CUDA-capable ones.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    results: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.results.append(CheckResult(name, passed, detail))

    @property
    def overall_pass(self) -> bool:
        return all(r.passed for r in self.results)


def check_python(report: Report) -> None:
    version = sys.version.split()[0]
    major, minor = sys.version_info.major, sys.version_info.minor
    ok = (major, minor) >= (3, 10)
    report.add("Python", ok, f"v{version}")


def check_pytorch(report: Report) -> tuple[bool, bool]:
    """Returns (torch_ok, cuda_available)."""
    try:
        import torch

        report.add("PyTorch", True, f"v{torch.__version__}")

        cuda_available = torch.cuda.is_available()
        if cuda_available:
            report.add("CUDA", True, f"v{torch.version.cuda}")
            gpu_name = torch.cuda.get_device_name(0)
            report.add("GPU", True, gpu_name)
        else:
            report.add("CUDA", True, "NOT AVAILABLE")
            report.add("GPU", True, "CPU MODE")

        return True, cuda_available
    except Exception as exc:  # noqa: BLE001
        report.add("PyTorch", False, str(exc))
        report.add("CUDA", False, "N/A")
        report.add("GPU", False, "N/A")
        return False, False


def check_ultralytics(report: Report) -> None:
    try:
        import ultralytics

        report.add("Ultralytics", True, f"v{ultralytics.__version__}")
    except Exception as exc:  # noqa: BLE001
        report.add("Ultralytics", False, str(exc))


def check_yolo26(report: Report) -> None:
    try:
        from ultralytics import YOLO

        YOLO("yolo26n.pt")
        report.add("YOLO26", True, "yolo26n.pt loaded")
    except Exception as exc:  # noqa: BLE001
        report.add("YOLO26", False, str(exc))


def check_opencv(report: Report) -> None:
    try:
        import cv2

        report.add("OpenCV", True, f"v{cv2.__version__}")
    except Exception as exc:  # noqa: BLE001
        report.add("OpenCV", False, str(exc))


def check_fastapi(report: Report) -> None:
    try:
        import fastapi

        report.add("FastAPI", True, f"v{fastapi.__version__}")
    except Exception as exc:  # noqa: BLE001
        report.add("FastAPI", False, str(exc))


def check_pydantic(report: Report) -> None:
    try:
        import pydantic

        report.add("Pydantic", True, f"v{pydantic.__version__}")
    except Exception as exc:  # noqa: BLE001
        report.add("Pydantic", False, str(exc))


def print_report(report: Report) -> None:
    line = "=" * 60
    print(line)
    print("AI-CCTV SENTINEL — ENVIRONMENT VERIFICATION")
    print(line)
    print()

    label_width = max(len(r.name) for r in report.results)
    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        detail = f" ({r.detail})" if r.detail else ""
        print(f"{r.name.ljust(label_width)} : {status}{detail}")

    print()
    print(line)
    overall = "PASS" if report.overall_pass else "FAIL"
    print(f"OVERALL STATUS: {overall}")
    print(line)


def main() -> None:
    report = Report()

    check_python(report)
    check_pytorch(report)
    check_ultralytics(report)
    check_yolo26(report)
    check_opencv(report)
    check_fastapi(report)
    check_pydantic(report)

    print_report(report)

    if not report.overall_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
