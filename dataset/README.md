# Dataset folder

This folder contains sport-specific dataset directories for PocketCoach AI.

Each folder is a placeholder for the dataset assets for that sport.

Imported archive data is available under:

- `dataset/archive2/` — imported from attached folder `archive (2)/sports`
- `dataset/archive3/` — imported from attached folder `archive (3)/dataset`
- `dataset/dataset_archive3_label_mapping.json` — structured train label counts for archive3

A manifest of the imported archives is available at `dataset/archive_manifest.json`.

Use `dataset/import_archives.py` to refresh or re-import the attached archives if the source attachments move.

## Auditing and training readiness

`source_catalog.json` records candidate external sources, their expected media,
annotation type, and current licensing status. `unverified` and
`academic_noncommercial` sources are blocked from training until their terms
are confirmed.

Run the local inventory without modifying dataset files:

```powershell
python dataset/audit_dataset.py --output dataset/dataset_inventory.json --csv dataset/dataset_inventory.csv
```

Add `--hash` when duplicate-file detection is required. The report separates
images, videos, and annotation files; an image count is not a pose-sequence
count and does not establish training suitability. No model is trained or
loaded by this audit.

The latest non-hashing inventory run found 29,814 images, no videos, and 3
annotation-extension files across 39 category folders. Duplicate detection
was not enabled, and the extension-based annotation count does not establish
that these files contain usable pose labels.

## Pose extraction, training, and tracking verification

The compatible Python MediaPipe range is pinned in
`backend/requirements.txt`. Train the auditable nearest-centroid pose
baseline from local images:

```powershell
python dataset/train_pose_model.py --output dataset/models/pose_classifier.json
```

The default categories are the three active categories with local image
assets. Missing categories are reported rather than silently represented as
trained classes. This model classifies broad pose-category signals; it is not
a replacement for sport-specific technique evaluation.

Verify detection and temporal tracking on a camera or recorded video:

```powershell
python dataset/verify_pose_tracking.py --source 0 --report tracking_report.json
```

The verifier reports detection rate, reliable landmark coverage, and the
longest tracking-loss streak. It exits non-zero when the configured quality
thresholds are not met.

For the full feature/model comparison and independent test split:

```powershell
python dataset\compare_pose_models.py
```

See [MODEL_ACCURACY_AUDIT.md](./MODEL_ACCURACY_AUDIT.md) for the evaluation
policy and its limitations.

`category_model_plan.json` defines the independent evidence and readiness
requirements for all nine top-level categories. Categories with missing,
static-only, unpermitted, or non-temporal data are reported as blocked rather
than receiving a misleading placeholder model.

Labeled archive3 training images are also merged into structured sport folders under each supported category in `dataset/<sport>/archive3/train/`.

The archive3 label normalization maps external category labels to repo-supported sport keys and copies the training images into their corresponding sport directories.

Directory structure:

- badminton/
- tennis/
- pickleball/
- squash/
- kickboxing/
- muay_thai/
- karate/
- taekwondo/
- judo/
- brazilian_jiu_jitsu/
- wrestling/
- fencing/
- basketball/
- volleyball/
- handball/
- archery/
- stretching/
- mobility_training/
- rehabilitation/
- home_workout/
- calisthenics/
