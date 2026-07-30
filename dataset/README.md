# Dataset folder

This folder contains sport-specific dataset directories for PocketCoach AI.

Each folder is a placeholder for the dataset assets for that sport.

Imported archive data is available under:

- `dataset/archive2/` — imported from attached folder `archive (2)/sports`
- `dataset/archive3/` — imported from attached folder `archive (3)/dataset`
- `dataset/dataset_archive3_label_mapping.json` — structured train label counts for archive3

A manifest of the imported archives is available at `dataset/archive_manifest.json`.

Use `dataset/import_archives.py` to refresh or re-import the attached archives if the source attachments move.

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
