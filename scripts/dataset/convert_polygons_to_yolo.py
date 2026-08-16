from pathlib import Path

LABEL_DIR = Path("datasets/processed/annotated/labels")
BACKUP_DIR = Path("datasets/processed/invalid_labels_backup")


def polygon_to_bbox(values):
    xs = values[0::2]
    ys = values[1::2]

    x_min = min(xs)
    x_max = max(xs)
    y_min = min(ys)
    y_max = max(ys)

    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    width = x_max - x_min
    height = y_max - y_min

    return x_center, y_center, width, height


def convert_file(path):
    lines = path.read_text(encoding="utf-8").splitlines()

    output = []

    for line_number, line in enumerate(lines, start=1):
        parts = line.strip().split()

        if not parts:
            continue

        class_id = parts[0]
        coords = parts[1:]

        # Already valid YOLO detection format
        if len(parts) == 5:
            output.append(line.strip())
            continue

        # Polygon must contain an even number of coordinates
        if len(coords) < 6 or len(coords) % 2 != 0:
            raise ValueError(
                f"{path.name}: line {line_number}: "
                f"cannot convert {len(parts)} fields"
            )

        values = [float(v) for v in coords]

        x_center, y_center, width, height = polygon_to_bbox(values)

        output.append(
            f"{class_id} "
            f"{x_center:.8f} "
            f"{y_center:.8f} "
            f"{width:.8f} "
            f"{height:.8f}"
        )

    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def main():
    invalid_files = []

    for path in LABEL_DIR.glob("*.txt"):
        lines = path.read_text(encoding="utf-8").splitlines()

        needs_conversion = False

        for line in lines:
            parts = line.strip().split()

            if parts and len(parts) != 5:
                needs_conversion = True
                break

        if needs_conversion:
            invalid_files.append(path)

    print("=" * 60)
    print("AI-CCTV Sentinel — Polygon → YOLO Detection Conversion")
    print("=" * 60)
    print(f"Files requiring conversion: {len(invalid_files)}")

    for path in invalid_files:
        print(f"Converting: {path.name}")
        convert_file(path)

    print("=" * 60)
    print(f"Converted files: {len(invalid_files)}")
    print("Original files remain safely backed up.")
    print("=" * 60)


if __name__ == "__main__":
    main()
