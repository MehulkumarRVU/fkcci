from pathlib import Path
import csv

path = Path('dataset/archive3/train.csv')
print('exists', path.exists())
with path.open('r', encoding='utf-8', errors='ignore') as f:
    reader = csv.reader(f)
    header = next(reader)
    print('header', header)
    for i, row in enumerate(reader):
        print('row', row)
        if i >= 4:
            break

if (Path('dataset/archive3/train')).exists():
    sample = sorted(Path('dataset/archive3/train').iterdir())[:20]
    print('train dir sample count', len(sample))
    for p in sample:
        print(p.name)
