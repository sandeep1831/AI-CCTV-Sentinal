from pathlib import Path
from collections import Counter

ROOT = Path("datasets/processed/annotated")
IMAGE_DIR = ROOT / "images"
LABEL_DIR = ROOT / "labels"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

images = [
    p for p in IMAGE_DIR.iterdir()
    if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
]

labels = list(LABEL_DIR.glob("*.txt"))

image_stems = {p.stem for p in images}
label_stems = {p.stem for p in labels}

class_counts = Counter()

total_boxes = 0
invalid_rows = 0
empty_labels = 0

for label_file in labels:
    lines = label_file.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()

    valid_lines = [line.strip() for line in lines if line.strip()]

    if not valid_lines:
        empty_labels += 1
        continue

    for line in valid_lines:
        parts = line.split()

        if len(parts) != 5:
            invalid_rows += 1
            continue

        class_id = parts[0]

        if class_id not in {"0", "1", "2", "3"}:
            invalid_rows += 1
            continue

        try:
            values = [float(x) for x in parts[1:]]

            if not all(0 <= x <= 1 for x in values):
                invalid_rows += 1
                continue

        except ValueError:
            invalid_rows += 1
            continue

        class_counts[class_id] += 1
        total_boxes += 1


print()
print("=" * 65)
print("AI-CCTV SENTINEL - MERGED DATASET VERIFICATION")
print("=" * 65)

print(f"Images              : {len(images)}")
print(f"Label files         : {len(labels)}")
print(f"Matched             : {len(image_stems & label_stems)}")
print(f"Images without label: {len(image_stems - label_stems)}")
print(f"Labels without image: {len(label_stems - image_stems)}")
print(f"Total boxes         : {total_boxes}")
print(f"Empty label files   : {empty_labels}")
print(f"Invalid rows        : {invalid_rows}")

print()
print("CLASS DISTRIBUTION")
print("-" * 30)

for class_id in ["0", "1", "2", "3"]:
    print(f"Class {class_id}: {class_counts[class_id]}")

print()
print("CLASS MEANING")
print("-" * 30)
print("0 = snake")
print("1 = monkey")
print("2 = dog")
print("3 = person")

print()
if (
    len(labels) == len(images)
    and len(image_stems & label_stems) == len(images)
    and len(label_stems - image_stems) == 0
    and invalid_rows == 0
    and empty_labels == 0
    and all(class_counts[str(i)] > 0 for i in range(4))
):
    print("STATUS: PASS")
    print("Merged dataset is structurally valid.")
else:
    print("STATUS: CHECK REQUIRED")

print("=" * 65)