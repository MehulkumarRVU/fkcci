"""Audit, extract, compare, and independently evaluate pose classifiers."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import joblib
import mediapipe as mp
import numpy as np
from pose_features import extract_feature

try:
    from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC
except ImportError as exc:
    raise SystemExit("Install scikit-learn to run this comparison: python -m pip install scikit-learn") from exc


IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
POSE = mp.solutions.pose
TOP_LEVEL_CATEGORIES = (
    "boxing", "table_tennis", "gym", "badminton", "stretching",
    "mobility_training", "rehabilitation", "home_workouts", "calisthenics",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _files(root: Path, category: str) -> list[Path]:
    return sorted(path for path in (root / category).rglob("*")
                  if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def _split(digest: str) -> str:
    value = int(digest[:8], 16) / 0xFFFFFFFF
    return "test" if value < 0.2 else "validation" if value < 0.4 else "train"


def extract_dataset(root: Path, categories: list[str], max_per_category: int) -> tuple[dict[str, Any], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    failures: Counter[str] = Counter()
    with POSE.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.5) as pose:
        for category in categories:
            for path in _files(root, category)[:max_per_category or None]:
                digest = _sha256(path)
                split = _split(digest)
                image = cv2.imread(str(path))
                if image is None:
                    failures["image_read_failed"] += 1
                    continue
                result = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                if not result.pose_landmarks:
                    failures["pose_not_detected"] += 1
                    continue
                try:
                    features = extract_feature(result.pose_landmarks)
                except ValueError as exc:
                    failures[str(exc)] += 1
                    continue
                rows.append({
                    "path": path.relative_to(root).as_posix(),
                    "sha256": digest,
                    "category": category,
                    "split": split,
                    "features": features.tolist(),
                })
    return {"rows": rows, "failures": dict(failures)}, {"files_seen": sum(len(_files(root, category)[:max_per_category or None]) for category in categories)}


def _metrics(model: Any, x: np.ndarray, y: np.ndarray, labels: list[str]) -> dict[str, Any]:
    start = time.perf_counter()
    predictions = model.predict(x)
    latency_ms = (time.perf_counter() - start) * 1000 / max(len(x), 1)
    result = {
        "accuracy": round(float(accuracy_score(y, predictions)), 4),
        "macro_precision": round(float(precision_score(y, predictions, labels=labels, average="macro", zero_division=0)), 4),
        "macro_recall": round(float(recall_score(y, predictions, labels=labels, average="macro", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y, predictions, labels=labels, average="macro", zero_division=0)), 4),
        "per_class_f1": {label: round(float(score), 4) for label, score in zip(labels, f1_score(y, predictions, labels=labels, average=None, zero_division=0))},
        "confusion_matrix": confusion_matrix(y, predictions, labels=labels).tolist(),
        "samples": len(y),
        "latency_ms_per_sample": round(latency_ms, 4),
    }
    if hasattr(model, "predict_proba"):
        confidence = np.max(model.predict_proba(x), axis=1)
        result["confidence"] = {
            "mean": round(float(np.mean(confidence)), 4),
            "p10": round(float(np.quantile(confidence, 0.1)), 4),
            "p50": round(float(np.quantile(confidence, 0.5)), 4),
            "p90": round(float(np.quantile(confidence, 0.9)), 4),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--categories", nargs="+", default=["boxing", "table_tennis", "badminton"])
    parser.add_argument("--max-per-category", type=int, default=0, help="0 means all local images")
    parser.add_argument("--output", type=Path, default=Path("dataset/reports/model_comparison.json"))
    parser.add_argument("--features-output", type=Path, default=Path("dataset/reports/pose_features.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    categories = [category for category in args.categories if _files(root, category)]
    extracted, counts = extract_dataset(root, categories, args.max_per_category)
    rows = extracted["rows"]
    if not rows:
        raise SystemExit("No usable pose samples were extracted")
    args.features_output.parent.mkdir(parents=True, exist_ok=True)
    args.features_output.write_text(json.dumps({**extracted, **counts}, indent=2), encoding="utf-8")

    labels = sorted(categories)
    arrays = {
        split: (
            np.array([row["features"] for row in rows if row["split"] == split], dtype=np.float32),
            np.array([row["category"] for row in rows if row["split"] == split]),
        )
        for split in ("train", "validation", "test")
    }
    if any(len(arrays[split][1]) == 0 for split in arrays):
        raise SystemExit("Each train, validation, and test split must contain usable samples")

    models = {
        "random_forest": RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight="balanced"),
        "svm_rbf": make_pipeline(StandardScaler(), SVC(C=3.0, probability=True, random_state=42)),
        "gradient_boosting": HistGradientBoostingClassifier(max_iter=200, random_state=42),
        "mlp": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300, early_stopping=True, random_state=42)),
    }
    comparison: dict[str, Any] = {}
    for name, model in models.items():
        model.fit(arrays["train"][0], arrays["train"][1])
        comparison[name] = {
            "validation": _metrics(model, *arrays["validation"], labels),
            "test": _metrics(model, *arrays["test"], labels),
        }
    best_name = max(comparison, key=lambda name: comparison[name]["validation"]["macro_f1"])
    model_output = args.output.with_name("best_pose_classifier.joblib")
    joblib.dump(models[best_name], model_output)
    report = {
        "task": "three-way sport-category classification from single images",
        "categories": labels,
        "top_level_categories": list(TOP_LEVEL_CATEGORIES),
        "independent_model_policy": "Each top-level category requires its own movement labels and independent evaluation; this combined classifier is only a local data diagnostic.",
        "split_policy": "content hash: 60% train, 20% validation, 20% final test; identical files share a split",
        "limitations": [
            "No athlete/video identity metadata exists, so source-level independence cannot be proven.",
            "Local data has no movement-class or technique-quality labels.",
            "This does not measure coaching accuracy or temporal movement recognition.",
        ],
        "counts": {
            "files_seen": counts["files_seen"],
            "usable_samples": len(rows),
            "by_split": Counter(row["split"] for row in rows),
            "by_category": Counter(row["category"] for row in rows),
            "extraction_failures": extracted["failures"],
        },
        "models": comparison,
        "selected_by_validation_macro_f1": best_name,
        "best_model_artifact": str(model_output.resolve()),
        "validated_for_live_integration": comparison[best_name]["test"]["macro_f1"] >= 0.9 and comparison[best_name]["test"]["accuracy"] >= 0.9,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=lambda value: dict(value)), encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "selected": best_name, "test": comparison[best_name]["test"], "validated_for_live_integration": report["validated_for_live_integration"]}, indent=2))


if __name__ == "__main__":
    main()
