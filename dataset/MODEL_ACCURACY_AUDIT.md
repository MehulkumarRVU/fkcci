# Model accuracy audit

## Baseline

The previous `nearest_centroid_pose_v1` artifact reported 42.61% validation
accuracy on 399 training and 115 validation samples. The result is not an
independent test result.

## Findings

- The target is a three-way **sport-folder** classifier, not a movement or
  technique classifier. Each sport folder contains heterogeneous images with
  no movement-class annotations.
- The baseline uses one centroid per sport and Euclidean distance. It cannot
  represent multimodal pose distributions within a sport.
- The old split is a path hash split with only train/validation partitions.
  There is no final test set and no athlete/video identity metadata.
- The available local data is image-only. There are no local videos or pose
  annotation files from which to train an LSTM/GRU or validate temporal
  movement recognition.
- The current feature vector contains normalized landmarks, but no explicit
  joint-angle, limb-length, symmetry, or confidence-derived features.
- A 90% result on this folder-level proxy would not establish 90% coaching
  accuracy.

## Reproducible comparison

The latest checked-in comparison report evaluated 3,474 usable image samples
(2,077 train / 676 validation / 721 test) from 5,093 files seen. Its selected
gradient-boosting classifier achieved 68.93% test accuracy and 60.65% test
macro-F1. Table Tennis test F1 was 36.17%. The result is below the project's
90% accuracy and macro-F1 integration gate, and the task remains broad
single-image sport-folder classification, not coaching or temporal movement
recognition. The data inventory and model report do not establish licensing or
athlete/video-level independence.

Run:

```powershell
python dataset\compare_pose_models.py
```

The command writes a feature manifest and a model comparison report. It uses
content-hash splits (60/20/20), keeps exact duplicates in one split, reports
macro metrics and confusion matrices, and selects the model by validation
macro-F1 before evaluating once on the final test partition.

No model is eligible for live integration unless both final-test accuracy and
macro-F1 are at least 0.90. Existing sport analyzers remain the fallback.

The nine-category readiness and evidence policy is recorded in
`category_model_plan.json`. The current comparison is deliberately not nine
models: a single-image sport-folder classifier is only a diagnostic of local
data separability. It must not be reported as nine coaching capabilities.
Adaptive Training is cross-cutting and remains inside the nine categories,
not a tenth model.

The selected experimental estimator is saved as
`dataset/reports/best_pose_classifier.joblib`. It is an offline artifact only:
the report's `validated_for_live_integration` flag must be true before adding
an inference path to the application.
