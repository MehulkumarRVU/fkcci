from pathlib import Path

DATASET_ROOT = Path(__file__).resolve().parent

sports = ['football','badminton','cricket','swimming','wrestling','karate','tennis']
for s in sports:
    p = DATASET_ROOT/s/'archive3'/'train'
    print(s, p.exists(), 'files=', sum(1 for _ in p.glob('*') if _.is_file()) if p.exists() else 0)
print('archive_manifest exists', (DATASET_ROOT/'archive_manifest.json').exists())
print('archive3_label_mapping exists', (DATASET_ROOT/'dataset_archive3_label_mapping.json').exists())
