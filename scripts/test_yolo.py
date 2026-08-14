"""AI-CCTV Sentinel — Ultralytics YOLO26 environment verification script."""

from ultralytics import YOLO


def main() -> None:
    print("=" * 60)
    print("Ultralytics YOLO26 Environment Check")
    print("=" * 60)

    model = YOLO("yolo26n.pt")

    print("YOLO26n loaded successfully.")
    print("Model:", model)

    print("YOLO check    : PASSED")


if __name__ == "__main__":
    main()
