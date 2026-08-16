from pathlib import Path
import shutil
import hashlib

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_IMAGES = PROJECT_ROOT / "datasets" / "processed" / "annotated" / "images"
OUTPUT_LABELS = PROJECT_ROOT / "datasets" / "processed" / "annotated" / "labels"

DATASETS = {
    "snake": {
        "root": PROJECT_ROOT / "datasets" / "raw" / "public" / "snake",
        "class_id": 0,
    },
    "monkey": {
        "root": PROJECT_ROOT / "datasets" / "raw" / "public" / "monkey_import",
        "class_id": 1,
    },
    "dog": {
        "root": PROJECT_ROOT / "datasets" / "raw" / "public" / "dog",
        "class_id": 2,
    },
    "person": {
        "root": PROJECT_ROOT / "datasets" / "raw" / "public" / "person_import",
        "class_id": 3,
    },
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def file_hash(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()


def find_images(root):
    return [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def find_label(root, image):
    candidates = list(root.rglob("labels/" + image.stem + ".txt"))

    if candidates:
        return candidates[0]

    return None


def make_unique_name(image, dataset_name):
    return f"{dataset_name}__{image.name}"


def convert_label(label_path, output_path, class_id):
    lines_out = []

    if label_path is not None and label_path.exists():
        for line in label_path.read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines():

            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) != 5:
                continue

            try:
                float(parts[1])
                float(parts[2])
                float(parts[3])
                float(parts[4])
            except ValueError:
                continue

            lines_out.append(
                f"{class_id} "
                f"{parts[1]} "
                f"{parts[2]} "
                f"{parts[3]} "
                f"{parts[4]}"
            )

    output_path.write_text(
        "\n".join(lines_out) + ("\n" if lines_out else ""),
        encoding="utf-8"
    )


def main():

    print("=" * 70)
    print("AI-CCTV Sentinel - Task 4 Dataset Merge")
    print("=" * 70)

    OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)
    OUTPUT_LABELS.mkdir(parents=True, exist_ok=True)

    total_images = 0
    total_labels = 0
    total_boxes = 0
    total_no_label = 0
    total_duplicates = 0

    existing_hashes = {}

    for dataset_name, info in DATASETS.items():

        root = info["root"]
        class_id = info["class_id"]

        print()
        print("-" * 70)
        print(f"PROCESSING: {dataset_name.upper()}")
        print(f"Source: {root}")
        print(f"Project class ID: {class_id}")
        print("-" * 70)

        if not root.exists():
            print("WARNING: Dataset folder does not exist.")
            continue

        images = find_images(root)

        print(f"Source images found: {len(images)}")

        dataset_images = 0
        dataset_labels = 0
        dataset_boxes = 0
        dataset_no_label = 0

        for image in images:

            label = find_label(root, image)

            if label is None:
                dataset_no_label += 1

            try:
                image_hash = file_hash(image)
            except Exception as e:
                print(f"WARNING: Could not hash {image.name}: {e}")
                continue

            if image_hash in existing_hashes:
                total_duplicates += 1
                continue

            output_name = make_unique_name(image, dataset_name)

            output_image = OUTPUT_IMAGES / output_name
            output_label = OUTPUT_LABELS / (
                Path(output_name).stem + ".txt"
            )

            try:
                shutil.copy2(image, output_image)
            except Exception as e:
                print(f"WARNING: Could not copy {image}: {e}")
                continue

            convert_label(
                label,
                output_label,
                class_id
            )

            existing_hashes[image_hash] = output_image

            dataset_images += 1
            total_images += 1

            if label is not None:
                dataset_labels += 1
                total_labels += 1

                for line in output_label.read_text(
                    encoding="utf-8"
                ).splitlines():

                    if line.strip():
                        dataset_boxes += 1
                        total_boxes += 1

        total_no_label += dataset_no_label

        print(f"Images imported : {dataset_images}")
        print(f"Labels imported : {dataset_labels}")
        print(f"Boxes imported  : {dataset_boxes}")
        print(f"No-label images : {dataset_no_label}")

    print()
    print("=" * 70)
    print("MERGE COMPLETE")
    print("=" * 70)

    print(f"TOTAL IMAGES       : {total_images}")
    print(f"TOTAL LABEL FILES  : {total_labels}")
    print(f"TOTAL BOXES        : {total_boxes}")
    print(f"NO-LABEL IMAGES    : {total_no_label}")
    print(f"EXACT DUPLICATES   : {total_duplicates}")

    print()
    print(f"Images output:")
    print(OUTPUT_IMAGES)

    print()
    print(f"Labels output:")
    print(OUTPUT_LABELS)

    print("=" * 70)


if __name__ == "__main__":
    main()