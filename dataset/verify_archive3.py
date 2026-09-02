from pathlib import Path
sports = ['football','badminton','cricket','swimming','wrestling','karate','tennis']
for s in sports:
    p = Path('dataset')/s/'archive3'/'train'
    print(s, p.exists(), 'files=', sum(1 for _ in p.glob('*') if _.is_file()) if p.exists() else 0)
print('archive_manifest exists', Path('dataset/archive_manifest.json').exists())
print('archive3_label_mapping exists', Path('dataset_archive3_label_mapping.json').exists())
