"""Extract MediaPipe landmarks and train a deterministic pose classifier.

This is a baseline movement-category model, not a technique-quality model.
It only trains categories that have local image assets and never treats
missing categories as negative examples. The output is JSON so it can be
audited and loaded without adding a model-serving dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np

IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
POSE = mp.solutions.pose


def _feature(landmarks: Any) -> np.ndarray:
    points = np.array(
        [[lm.x, lm.y, lm.z, lm.visibility] for lm in landmarks.landmark],
        dtype=np.float32,
    )
    center = (points[11, :3] + points[12, :3]) / 2.0
    shoulder_width = float(np.linalg.norm(points[11, :2] - points[12, :2]))
    if shoulder_width < 1e-6:
        raise ValueError("shoulder_width_too_small")
    points[:, :3] = (points[:, :3] - center) / shoulder_width
    return points.reshape(-1)


def _files(category: Path) -> list[Path]:
    return sorted(
        path for path in category.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def _split(path: Path, validation_fraction: float) -> str:
    digest = hashlib.sha256(path.as_posix().encode()).hexdigest()
    return "validation" if int(digest[:8], 16) / 0xFFFFFFFF < validation_fraction else "train"


def collect_features(
    root: Path,
    categories: list[str],
    max_per_category: int,
    validation_fraction: float,
) -> tuple[dict[str, list[np.ndarray]], Counter[str], list[dict[str, str]]]:
    samples: dict[str, list[np.ndarray]] = {"train": [], "validation": []}
    labels: dict[str, list[str]] = {"train": [], "validation": []}
    failures: Counter[str] = Counter()
    failure_examples: list[dict[str, str]] = []
    with POSE.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    ) as pose:
        for category in categories:
            paths = _files(root / category)
            if max_per_category > 0:
                paths = paths[:max_per_category]
            for path in paths:
                image = cv2.imread(str(path))
                if image is None:
                    failures["image_read_failed"] += 1
                    continue
                result = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                if not result.pose_landmarks:
                    failures["pose_not_detected"] += 1
                    if len(failure_examples) < 20:
                        failure_examples.append({"path": str(path), "reason": "pose_not_detected"})
                    continue
                try:
                    vector = _feature(result.pose_landmarks)
                except ValueError as exc:
                    failures[str(exc)] += 1
                    continue
                split = _split(path.relative_to(root), validation_fraction)
                samples[split].append(vector)
                labels[split].append(category)
    return (
        {
            "train": [np.array(x) for x in samples["train"]],
            "validation": [np.array(x) for x in samples["validation"]],
            "train_labels": labels["train"],
            "validation_labels": labels["validation"],
        },
        Counter(labels["train"] + labels["validation"]),
        failure_examples + [{"reason": key, "count": str(value)} for key, value in failures.items()],
    )


def _fit(samples: list[np.ndarray], labels: list[str]) -> dict[str, Any]:
    classes = sorted(set(labels))
    centroids = {}
    for label in classes:
        values = np.stack([sample for sample, item in zip(samples, labels) if item == label])
        centroids[label] = values.mean(axis=0).round(7).tolist()
    return {"model_type": "nearest_centroid_pose_v1", "classes": classes, "centroids": centroids}


def _predict(model: dict[str, Any], sample: np.ndarray) -> str:
    return min(
        model["classes"],
        key=lambda label: float(np.linalg.norm(sample - np.array(model["centroids"][label], dtype=np.float32))),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--categories", nargs="+", default=["boxing", "table_tennis", "badminton"])
    parser.add_argument("--max-per-category", type=int, default=250)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--min-live-accuracy", type=float, default=0.8)
    parser.add_argument("--output", type=Path, default=Path("dataset/models/pose_classifier.json"))
    args = parser.parse_args()
    if not 0 < args.validation_fraction < 1:
        raise SystemExit("--validation-fraction must be between 0 and 1")
    if not 0 <= args.min_live_accuracy <= 1:
        raise SystemExit("--min-live-accuracy must be between 0 and 1")

    root = args.root.resolve()
    categories = [
        category for category in args.categories
        if (root / category).is_dir() and _files(root / category)
    ]
    missing = sorted(set(args.categories) - set(categories))
    if len(categories) < 2:
        raise SystemExit("At least two categories with local image directories are required")

    collected, _, failures = collect_features(
        root, categories, args.max_per_category, args.validation_fraction
    )
    train_labels = collected.pop("train_labels")
    validation_labels = collected.pop("validation_labels")
    if len(collected["train"]) == 0 or len(collected["validation"]) == 0:
        raise SystemExit("No usable train/validation pose samples were extracted")

    model = _fit(collected["train"], train_labels)
    predictions = [_predict(model, sample) for sample in collected["validation"]]
    correct = sum(prediction == label for prediction, label in zip(predictions, validation_labels))
    confusion = Counter(f"{actual}->{predicted}" for actual, predicted in zip(validation_labels, predictions))
    report = {
        **model,
        "output": str(args.output.resolve()),
        "categories_requested": args.categories,
        "categories_trained": categories,
        "missing_categories": missing,
        "samples": {
            "train": len(collected["train"]),
            "validation": len(collected["validation"]),
            "validation_accuracy": round(correct / len(predictions), 4),
        },
        "validated_for_live_integration": correct / len(predictions) >= args.min_live_accuracy,
        "live_integration_accuracy_threshold": args.min_live_accuracy,
        "confusion": dict(sorted(confusion.items())),
        "extraction_failures": failures,
        "training_scope": "pose category baseline from local images; not technique-quality validation",
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("categories_trained", "missing_categories", "samples", "output")}, indent=2))


if __name__ == "__main__":
    main()
