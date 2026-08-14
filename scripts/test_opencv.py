"""AI-CCTV Sentinel — OpenCV environment verification script."""

import cv2


def main() -> None:
    print("=" * 60)
    print("OpenCV Environment Check")
    print("=" * 60)

    print("OpenCV version:", cv2.__version__)
    print("OpenCV check   : PASSED")


if __name__ == "__main__":
    main()
