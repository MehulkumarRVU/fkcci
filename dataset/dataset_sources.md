# Dataset sources and attachments

This repository contains sports dataset placeholders under `dataset/`.

## Attached dataset sources

- `archive (2)` attachments include a `sports/` folder with raw dataset assets for:
  - badminton
  - baseball
  - basketball
  - boxing
  - chess
  - cricket
  - fencing
  - football
  - formula1
  - gymnastics
  - hockey
  - ice_hockey
  - kabaddi
  - motogp
  - shooting
  - swimming
  - table_tennis
  - tennis
  - volleyball
  - weight_lifting
  - wrestling
  - wwe

- `archive (3)` attachments include a Kaggle-style dataset scaffold with:
  - `dataset/train.csv`
  - `dataset/test.csv`
  - `dataset/sample_submission.csv`
  - `dataset/train/`
  - `dataset/test/`

## Imported archive data

The attached archives were imported into the repo as follows:

- `dataset/archive2/` — imported from `archive (2)/sports/`
- `dataset/archive3/` — imported from `archive (3)/dataset/`
- `dataset/archive_manifest.json` — import summary
- `dataset/import_archives.py` — helper script to refresh the import

Imported details:

- `archive2` categories imported: 21
- `archive2` files copied: 14,346
- `archive3` items copied: 10,286

Supported categories copied into existing repo directories:

- badminton
- basketball
- fencing
- football
- gymnastics
- hockey
- ice_hockey
- tennis
- volleyball
- wrestling

New categories created in `dataset/` from archive2:

- baseball
- boxing
- chess
- cricket
- formula1
- kabaddi
- motogp
- shooting
- swimming
- table_tennis
- weight_lifting
- wwe

Structured archive3 train images are also merged into sport folders as:

- `dataset/<sport>/archive3/train/`

Archive3 label mapping:

- Badminton → badminton
- Cricket → cricket
- Wrestling → wrestling
- Tennis → tennis
- Soccer → football
- Swimming → swimming
- Karate → karate

## Requested Kaggle dataset searches

Use these searches to locate supplemental datasets on Kaggle:

- [pickleball](https://www.kaggle.com/search?q=pickleball)
- [squash](https://www.kaggle.com/search?q=squash)
- [muay thai](https://www.kaggle.com/search?q=muay+thai)
- [kickboxing](https://www.kaggle.com/search?q=kickboxing)
- [taekwondo](https://www.kaggle.com/search?q=taekwondo)
- [judo](https://www.kaggle.com/search?q=judo)
- [brazilian jiu jitsu](https://www.kaggle.com/search?q=brazilian+jiu+jitsu)
- [handball](https://www.kaggle.com/search?q=handball)
- [calisthenics](https://www.kaggle.com/search?q=calisthenics)
- [stretching](https://www.kaggle.com/search?q=stretching)
- [rehabilitation exercise](https://www.kaggle.com/search?q=rehabilitation+exercise)
- [mobility exercise](https://www.kaggle.com/search?q=mobility+exercise)
- [home workout](https://www.kaggle.com/search?q=home+workout)

## Integration guidance

- Copy files from `archive (2)/sports/<sport>/` into the matching `dataset/<sport>/` directory.
- Add CSV or annotation files from `archive (3)/dataset/` into `dataset/<sport>/` as needed.
- For sports not yet in the repo, create a matching directory under `dataset/` and add a placeholder `README.md`.

## Notes

This file records the dataset sources currently available in attachments, the completed archive import, and the requested Kaggle sources for the repo.
