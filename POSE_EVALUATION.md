# Pose analysis evaluation

## Confirmed architecture

The browser loads MediaPipe Pose from the CDN and sends normalized landmark
coordinates to the FastAPI service. The backend uses sport-specific,
rule-based analyzers for supported activities. It does not currently contain a
PocketCoach-trained movement classifier or a learned technique-scoring model.
Results are tagged `heuristic_v2_biomechanics` so they are not confused with
future calibrated models.

The analysis path is:

1. Camera frames -> MediaPipe Pose landmarks.
2. Browser quality gate and skeleton rendering.
3. Realtime backend analysis for live feedback.
4. Buffered backend analysis with visibility filtering, temporal smoothing,
   score aggregation, and reaction-state measurement.
5. Session persistence records scores only for a supported, reliable result;
   otherwise it stores an explicit unevaluable/unsupported status with null
   score fields.

## Implemented safeguards

- Landmark coordinates must be finite and visibility must meet the configured
  threshold (`POSE_VISIBILITY_THRESHOLD`, default `0.5`).
- Frames must meet configured coverage (`POSE_MIN_FRAME_COVERAGE`, default
  `0.5`) and have a reliably visible torso.
- Unreliable frames return `score: null`,
  `evaluation_status: "insufficient_evidence"`, and explicit reasons.
- Missing or occluded landmarks are never replaced with a previous coordinate
  during smoothing.
- Body-relative normalization is available through
  `PoseUtils.normalize_landmarks` for scale-robust feature extraction.
- Skills are checked against the selected analyzer before evaluation.
- Unsupported sports and failed full-session analysis are not persisted as
  fabricated technique scores.
- Frontend live feedback displays a retry message instead of local coaching
  when the visible landmark coverage is too low.

## Reproducible validation

From the repository root, using the configured Python interpreter:

```powershell
python -m pytest
python -m compileall -q backend
```

The latest validation in this environment produced **80 passed, 1 skipped**.
The suite includes focused regressions for invalid coordinates, missing torso
landmarks, scale normalization, non-fabricating smoothing, unreliable
realtime analysis, and unsupported skills.

No PCK, F1, expert-agreement, calibration, or real-world latency claim is made:
the repository does not currently include an independent, consented,
expert-labeled landmark/movement test set or a device benchmark harness.

## Data and training requirements

Future learned movement models should ingest versioned records shaped like:

```json
{
  "athlete_id": "pseudonymous-id",
  "session_id": "session-id",
  "sport": "boxing",
  "skill": "Jab",
  "camera_view": "front",
  "frames": [
    {
      "timestamp_ms": 0,
      "landmarks": [{"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 1.0}],
      "landmark_quality": "valid"
    }
  ],
  "phase_labels": [],
  "technique_labels": [],
  "reviewer_id": "pseudonymous-reviewer-id",
  "consent_version": "version"
}
```

Splits must be athlete- and recording-independent. Raw video should not be
stored by default; retention, consent, provenance, reviewer corrections, and
model version must be recorded before training. Predictions and user behavior
must not be treated as ground truth without expert review.

## Known limitations and next priorities

The system cannot infer ball/racket contact, punch impact force, injury risk,
or reliable 3D biomechanics from a single 2D camera. The next highest-impact
work is to add consented expert labels, benchmark camera views and occlusion,
make sport-specific phase/counter logic consume the same filtered sequence as
scoring, and calibrate score thresholds against independent expert ratings.
