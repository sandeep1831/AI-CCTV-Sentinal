from pathlib import Path
import shutil
import hashlib
import random

# ============================================================
# AI-CCTV SENTINEL
# Task 4 - Build Final Merged Dataset
#
# Class IDs:
#   0 = snake
#   1 = monkey
#   2 = dog
#   3 = person
#
# Current source folders:
#   datasets/raw/public/snake
#   datasets/raw/public/monkey_import
#   datasets/raw/public/dog
#   datasets/raw/public/person_import
#
# Final dataset:
#   datasets/yolo/sentinel_v1
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCES = {
    "snake": {
        "path": PROJECT_ROOT / "datasets/raw/public/snake",
        "class_id": 0,
    },
    "monkey": {
        "path": PROJECT_ROOT / "datasets/raw/public/monkey_import",
        "class_id": 1,
    },
    "dog": {
        "path": PROJECT_ROOT / "datasets/raw/public/dog",
        "class_id": 2,
    },
    "person": {
        "path": PROJECT_ROOT / "datasets/raw/public/person_import",
        "class_id": 3,
    },
}

OUTPUT = PROJECT_ROOT / "datasets/yolo/sentinel_v1"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

RANDOM_SEED = 42

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10


def sha1_file(path, chunk_size=1024 * 1024):
    """Calculate SHA1 hash of an image."""
    h = hashlib.sha1()

    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def find_images(root):
    """Find images without repeatedly scanning labels."""
    images = []

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(path)

    return images


def build_label_index(root):
    """
    Build a dictionary:

        image_stem -> label file

    This avoids the extremely slow:
        root.rglob("labels/" + image.stem + ".txt")
    """

    index = {}

    for label in root.rglob("labels/*.txt"):
        index[label.stem] = label

    return index


def read_label_file(label_path, class_id):
    """
    Read YOLO labels and force all valid objects
    into the requested project class.
    """

    output = []

    if label_path is None:
        return output

    try:
        text = label_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return output

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) != 5:
            continue

        try:
            # Original class ID
            int(parts[0])

            x = float(parts[1])
            y = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])

        except ValueError:
            continue

        # Validate YOLO geometry
        values = [x, y, w, h]

        if not all(0.0 <= v <= 1.0 for v in values):
            continue

        if w <= 0 or h <= 0:
            continue

        # Replace source class with project class
        output.append(
            f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
        )

    return output


def prepare_output():

    if OUTPUT.exists():
        print()
        print("Existing final dataset found.")
        print(f"Output: {OUTPUT}")
        print()
        answer = input(
            "Delete existing sentinel_v1 and rebuild? [Y/N]: "
        ).strip().lower()

        if answer != "y":
            print("Cancelled.")
            raise SystemExit(0)

        print("Deleting existing final dataset...")

        shutil.rmtree(OUTPUT)

    for split in ["train", "val", "test"]:

        (OUTPUT / "images" / split).mkdir(
            parents=True,
            exist_ok=True,
        )

        (OUTPUT / "labels" / split).mkdir(
            parents=True,
            exist_ok=True,
        )


def process_source(name, config):

    root = config["path"]
    class_id = config["class_id"]

    print()
    print("=" * 70)
    print(f"PROCESSING: {name.upper()}")
    print(f"Source: {root}")
    print(f"Project class ID: {class_id}")
    print("=" * 70)

    if not root.exists():
        print(f"ERROR: Source does not exist: {root}")
        return []

    print("Finding images...")

    images = find_images(root)

    print(f"Images found: {len(images)}")

    print("Building label index...")

    label_index = build_label_index(root)

    print(f"Label files indexed: {len(label_index)}")

    records = []

    missing_labels = 0
    empty_labels = 0
    invalid_labels = 0

    for i, image in enumerate(images, start=1):

        label = label_index.get(image.stem)

        if label is None:
            missing_labels += 1
            continue

        labels = read_label_file(label, class_id)

        if not labels:
            empty_labels += 1
            continue

        records.append(
            {
                "image": image,
                "labels": labels,
                "class_id": class_id,
                "source": name,
            }
        )

        if i % 1000 == 0:
            print(
                f"Processed {i}/{len(images)} images..."
            )

    print()
    print(f"{name.upper()} SUMMARY")
    print(f"Images found       : {len(images)}")
    print(f"Labels indexed     : {len(label_index)}")
    print(f"Usable pairs       : {len(records)}")
    print(f"Missing labels     : {missing_labels}")
    print(f"Empty/invalid      : {empty_labels}")

    return records


def make_unique_name(image, class_name, used_names):

    original = image.stem

    # Use source class in filename
    base = f"{class_name}_{original}"

    name = base

    counter = 1

    while name in used_names:

        name = f"{base}_{counter}"

        counter += 1

    used_names.add(name)

    return name


def split_records(records):

    random.seed(RANDOM_SEED)

    random.shuffle(records)

    total = len(records)

    train_end = int(total * TRAIN_RATIO)

    val_end = train_end + int(total * VAL_RATIO)

    train = records[:train_end]
    val = records[train_end:val_end]
    test = records[val_end:]

    return {
        "train": train,
        "val": val,
        "test": test,
    }


def copy_record(record, split, output_name):

    image = record["image"]
    labels = record["labels"]

    destination_image = (
        OUTPUT
        / "images"
        / split
        / f"{output_name}{image.suffix.lower()}"
    )

    destination_label = (
        OUTPUT
        / "labels"
        / split
        / f"{output_name}.txt"
    )

    shutil.copy2(
        image,
        destination_image,
    )

    destination_label.write_text(
        "\n".join(labels) + "\n",
        encoding="utf-8",
    )


def write_yaml():

    yaml_content = """path: datasets/yolo/sentinel_v1

train: images/train
val: images/val
test: images/test

nc: 4

names:
  0: snake
  1: monkey
  2: dog
  3: person
"""

    yaml_path = OUTPUT / "data.yaml"

    yaml_path.write_text(
        yaml_content,
        encoding="utf-8",
    )

    print()
    print(f"Created: {yaml_path}")


def verify_final():

    print()
    print("=" * 70)
    print("FINAL DATASET VERIFICATION")
    print("=" * 70)

    total_images = 0
    total_labels = 0
    total_boxes = 0

    class_counts = {
        "0": 0,
        "1": 0,
        "2": 0,
        "3": 0,
    }

    for split in ["train", "val", "test"]:

        image_dir = OUTPUT / "images" / split
        label_dir = OUTPUT / "labels" / split

        images = [
            p
            for p in image_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in IMAGE_EXTENSIONS
        ]

        labels = list(label_dir.glob("*.txt"))

        total_images += len(images)
        total_labels += len(labels)

        boxes = 0

        for label in labels:

            try:
                lines = label.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()
            except Exception:
                continue

            for line in lines:

                line = line.strip()

                if not line:
                    continue

                parts = line.split()

                if len(parts) != 5:
                    continue

                class_id = parts[0]

                if class_id in class_counts:
                    class_counts[class_id] += 1

                boxes += 1
                total_boxes += 1

        print(
            f"{split.upper():5} | "
            f"images={len(images):6} | "
            f"labels={len(labels):6} | "
            f"boxes={boxes:7}"
        )

    print()
    print(f"TOTAL IMAGES : {total_images}")
    print(f"TOTAL LABELS : {total_labels}")
    print(f"TOTAL BOXES  : {total_boxes}")

    print()
    print("CLASS DISTRIBUTION")

    print(f"0 snake  : {class_counts['0']}")
    print(f"1 monkey : {class_counts['1']}")
    print(f"2 dog    : {class_counts['2']}")
    print(f"3 person : {class_counts['3']}")

    print()

    if total_images == total_labels:
        print("IMAGE/LABEL PAIRING: PASS")
    else:
        print("IMAGE/LABEL PAIRING: WARNING")

    if all(
        value > 0
        for value in class_counts.values()
    ):
        print("ALL 4 CLASSES: PASS")
    else:
        print("ALL 4 CLASSES: WARNING")

    print()
    print("FINAL DATASET:")
    print(OUTPUT)


def main():

    print("=" * 70)
    print("AI-CCTV SENTINEL - TASK 4 FINAL DATASET BUILDER")
    print("=" * 70)

    print()
    print("Project class mapping:")
    print("0 = snake")
    print("1 = monkey")
    print("2 = dog")
    print("3 = person")

    print()
    print("Preparing output directory...")

    prepare_output()

    all_records = []

    # --------------------------------------------------------
    # Process each source
    # --------------------------------------------------------

    for name, config in SOURCES.items():

        records = process_source(
            name,
            config,
        )

        all_records.extend(records)

    print()
    print("=" * 70)
    print("ALL SOURCES COMBINED")
    print("=" * 70)

    print(f"Usable image/label pairs: {len(all_records)}")

    if not all_records:
        print("ERROR: No usable records found.")
        return

    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    print()
    print("Creating train/val/test split...")

    splits = split_records(all_records)

    print(
        f"Train: {len(splits['train'])}"
    )

    print(
        f"Val  : {len(splits['val'])}"
    )

    print(
        f"Test : {len(splits['test'])}"
    )

    # --------------------------------------------------------
    # Copy
    # --------------------------------------------------------

    print()
    print("Copying files into final dataset...")

    used_names = set()

    for split_name in ["train", "val", "test"]:

        records = splits[split_name]

        print()
        print(
            f"Processing {split_name.upper()} "
            f"({len(records)} files)..."
        )

        for i, record in enumerate(
            records,
            start=1,
        ):

            output_name = make_unique_name(
                record["image"],
                record["source"],
                used_names,
            )

            copy_record(
                record,
                split_name,
                output_name,
            )

            if i % 500 == 0:
                print(
                    f"  Copied {i}/{len(records)}"
                )

    # --------------------------------------------------------
    # YAML
    # --------------------------------------------------------

    write_yaml()

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    verify_final()

    print()
    print("=" * 70)
    print("TASK 4 DATASET BUILD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()