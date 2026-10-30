"""Verify pose detection and tracking on a camera or video file.

Use ``--source 0`` for a webcam or pass a video path. The command emits a
JSON report and returns non-zero when detection/tracking quality is below the
requested thresholds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp

POSE = mp.solutions.pose
CORE_INDICES = (11, 12, 23, 24)
TRACK_INDICES = (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)


def _quality(result: Any, visibility: float) -> tuple[bool, float]:
    if not result.pose_landmarks:
        return False, 0.0
    landmarks = result.pose_landmarks.landmark
    visible = sum(
        index < len(landmarks) and landmarks[index].visibility >= visibility
        for index in TRACK_INDICES
    )
    return visible / len(TRACK_INDICES) >= 0.75, visible / len(TRACK_INDICES)


def verify(source: str, max_frames: int, visibility: float, min_detection_rate: float,
           min_tracking_rate: float) -> dict[str, Any]:
    capture = cv2.VideoCapture(int(source) if source.isdigit() else source)
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open source: {source}")
    detected = tracked = frames = longest_loss = current_loss = 0
    with POSE.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        while frames < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            frames += 1
            result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            has_pose, coverage = _quality(result, visibility)
            if result.pose_landmarks:
                detected += 1
            if has_pose:
                tracked += 1
                current_loss = 0
            else:
                current_loss += 1
                longest_loss = max(longest_loss, current_loss)
    capture.release()
    if frames == 0:
        raise RuntimeError("Source produced no frames")
    report = {
        "source": source,
        "frames": frames,
        "detected_frames": detected,
        "tracked_frames": tracked,
        "detection_rate": round(detected / frames, 4),
        "tracking_rate": round(tracked / frames, 4),
        "longest_tracking_loss_frames": longest_loss,
        "thresholds": {
            "visibility": visibility,
            "min_detection_rate": min_detection_rate,
            "min_tracking_rate": min_tracking_rate,
        },
        "passed": detected / frames >= min_detection_rate and tracked / frames >= min_tracking_rate,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Camera index such as 0, or a video path")
    parser.add_argument("--max-frames", type=int, default=300)
    parser.add_argument("--visibility", type=float, default=0.5)
    parser.add_argument("--min-detection-rate", type=float, default=0.8)
    parser.add_argument("--min-tracking-rate", type=float, default=0.7)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = verify(args.source, args.max_frames, args.visibility, args.min_detection_rate, args.min_tracking_rate)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
