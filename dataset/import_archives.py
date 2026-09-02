from pathlib import Path
import shutil
import json
import csv

BASE_DIR = Path(__file__).resolve().parent
ARCHIVE2_SRC = Path(r"C:/Users/kumar/Downloads/archive (2)/sports")
ARCHIVE3_SRC = Path(r"C:/Users/kumar/Downloads/archive (3)/dataset")
ARCHIVE2_DEST = BASE_DIR / "archive2"
ARCHIVE3_DEST = BASE_DIR / "archive3"

ARCHIVE3_LABEL_MAP = {
    "Badminton": "badminton",
    "Cricket": "cricket",
    "Wrestling": "wrestling",
    "Tennis": "tennis",
    "Soccer": "football",
    "Swimming": "swimming",
    "Karate": "karate",
}

report = {
    "archive2_src_exists": ARCHIVE2_SRC.exists(),
    "archive3_src_exists": ARCHIVE3_SRC.exists(),
    "archive2_categories": [],
    "archive3_items": [],
    "supported_categories_copied": [],
    "new_categories_created": [],
    "archive2_files_copied": 0,
    "archive3_files_copied": 0,
    "archive3_structured_train_files_copied": 0,
    "archive3_label_mapping": ARCHIVE3_LABEL_MAP,
    "archive3_train_label_counts": {},
    "archive3_train_missing_files": [],
}

if not ARCHIVE2_SRC.exists():
    raise FileNotFoundError(f"Archive2 source not found: {ARCHIVE2_SRC}")

if ARCHIVE2_DEST.exists():
    shutil.rmtree(ARCHIVE2_DEST)
ARCHIVE2_DEST.mkdir(parents=True, exist_ok=True)

for src_dir in sorted(ARCHIVE2_SRC.iterdir()):
    if not src_dir.is_dir():
        continue

    slug = src_dir.name.replace(" ", "_")
    target_dir = BASE_DIR / slug
    report["archive2_categories"].append(slug)

    if target_dir.exists():
        archive_subdir = target_dir / "archive2"
        if archive_subdir.exists():
            shutil.rmtree(archive_subdir)
        shutil.copytree(src_dir, archive_subdir)
        report["supported_categories_copied"].append(slug)
        report["archive2_files_copied"] += sum(1 for _ in archive_subdir.rglob("*") if _.is_file())
    else:
        shutil.copytree(src_dir, target_dir)
        readme = target_dir / "README.md"
        readme.write_text(
            f"# {slug}\n\nImported from attached archive (2) under `sports/{src_dir.name}`.\n"
        )
        report["new_categories_created"].append(slug)
        report["archive2_files_copied"] += sum(1 for _ in target_dir.rglob("*") if _.is_file())

    dest_archive2 = ARCHIVE2_DEST / slug
    shutil.copytree(src_dir, dest_archive2)

if not ARCHIVE3_SRC.exists():
    raise FileNotFoundError(f"Archive3 source not found: {ARCHIVE3_SRC}")

if ARCHIVE3_DEST.exists():
    shutil.rmtree(ARCHIVE3_DEST)
shutil.copytree(ARCHIVE3_SRC, ARCHIVE3_DEST)
report["archive3_items"] = [p.name for p in sorted(ARCHIVE3_DEST.iterdir())]
report["archive3_files_copied"] = sum(1 for _ in ARCHIVE3_DEST.rglob("*") if _.is_file())

archive3_train_csv = ARCHIVE3_DEST / "train.csv"
archive3_train_src = ARCHIVE3_DEST / "train"
if archive3_train_csv.exists() and archive3_train_src.exists():
    with archive3_train_csv.open("r", encoding="utf-8", errors="ignore") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            image_id, label = row[0].strip(), row[1].strip()
            sport_key = ARCHIVE3_LABEL_MAP.get(label, label.lower().replace(" ", "_"))
            report["archive3_train_label_counts"][sport_key] = report["archive3_train_label_counts"].get(sport_key, 0) + 1
            source_image = archive3_train_src / image_id
            dest_dir = BASE_DIR / sport_key / "archive3" / "train"
            dest_dir.mkdir(parents=True, exist_ok=True)
            if source_image.exists():
                shutil.copy2(source_image, dest_dir / image_id)
                report["archive3_structured_train_files_copied"] += 1
            else:
                report["archive3_train_missing_files"].append(str(source_image))

structured_index = BASE_DIR / "dataset_archive3_label_mapping.json"
structured_index.write_text(json.dumps(report["archive3_train_label_counts"], indent=2))

manifest_path = BASE_DIR / "archive_manifest.json"
manifest_path.write_text(json.dumps(report, indent=2))
print("Archive import complete")
print(json.dumps(report, indent=2))
