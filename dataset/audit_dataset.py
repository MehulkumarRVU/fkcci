"""Build a factual inventory of local dataset assets.

The audit intentionally distinguishes files from usable training samples:
video frames and repeated copies are not treated as independent examples, and
images are not reported as pose annotations unless an annotation file exists.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}
ANNOTATION_EXTENSIONS = {".csv", ".json", ".jsonl", ".mat", ".pkl", ".xml", ".yaml", ".yml"}
IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__"}


def _files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and not any(part in IGNORED_DIRECTORIES for part in path.parts):
            yield path


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _category_paths(dataset_root: Path) -> list[Path]:
    return sorted(
        path for path in dataset_root.iterdir()
        if path.is_dir() and path.name not in IGNORED_DIRECTORIES
        and not path.name.startswith("archive")
    )


def audit(dataset_root: Path, include_hashes: bool = False) -> dict[str, Any]:
    duplicate_groups: dict[str, list[str]] = defaultdict(list)
    categories: list[dict[str, Any]] = []
    total = Counter()

    for category_path in _category_paths(dataset_root):
        counts = Counter()
        files: list[dict[str, Any]] = []
        for path in _files(category_path):
            extension = path.suffix.lower()
            kind = (
                "image" if extension in IMAGE_EXTENSIONS else
                "video" if extension in VIDEO_EXTENSIONS else
                "annotation" if extension in ANNOTATION_EXTENSIONS else
                "other"
            )
            counts[kind] += 1
            total[kind] += 1
            item: dict[str, Any] = {
                "path": path.relative_to(dataset_root).as_posix(),
                "bytes": path.stat().st_size,
                "kind": kind,
            }
            if include_hashes:
                digest = _sha256(path)
                item["sha256"] = digest
                duplicate_groups[digest].append(item["path"])
            files.append(item)

        categories.append({
            "category": category_path.name,
            "files": sum(counts.values()),
            "images": counts["image"],
            "videos": counts["video"],
            "annotations": counts["annotation"],
            "other": counts["other"],
            "pose_annotations_detected": counts["annotation"] > 0,
            "training_readiness": (
                "candidate" if counts["video"] or counts["annotation"] else
                "image_only" if counts["image"] else
                "empty"
            ),
            "assets": files,
        })

    duplicates = [
        {"sha256": digest, "paths": paths}
        for digest, paths in sorted(duplicate_groups.items())
        if len(paths) > 1
    ]
    return {
        "schema_version": 1,
        "dataset_root": str(dataset_root),
        "totals": {
            "files": sum(total.values()),
            "images": total["image"],
            "videos": total["video"],
            "annotations": total["annotation"],
            "other": total["other"],
        },
        "categories": categories,
        "duplicate_groups": duplicates,
        "duplicate_file_count": sum(len(group["paths"]) for group in duplicates),
    }


def _write_csv(report: dict[str, Any], output: Path) -> None:
    fields = [
        "category", "files", "images", "videos", "annotations", "other",
        "pose_annotations_detected", "training_readiness",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for category in report["categories"]:
            writer.writerow({field: category[field] for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--hash", action="store_true", dest="include_hashes")
    args = parser.parse_args()

    report = audit(args.root.resolve(), include_hashes=args.include_hashes)
    output = args.output or args.root / "dataset_inventory.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.csv:
        _write_csv(report, args.csv)
    print(json.dumps({
        "output": str(output),
        "totals": report["totals"],
        "categories": len(report["categories"]),
        "duplicate_groups": len(report["duplicate_groups"]),
    }, indent=2))


if __name__ == "__main__":
    main()
