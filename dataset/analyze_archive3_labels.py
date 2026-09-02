from pathlib import Path
import csv

base = Path('dataset/archive3')
for name in ['train.csv', 'test.csv']:
    path = base / name
    print('===', name, 'exists', path.exists())
    if not path.exists():
        continue
    with path.open('r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = next(reader)
        print('header:', header)
        if name == 'train.csv':
            labels = {}
            for row in reader:
                if len(row) < 2:
                    continue
                label = row[1].strip()
                labels[label] = labels.get(label, 0) + 1
            print('unique labels:', len(labels))
            for label, count in sorted(labels.items(), key=lambda x: (-x[1], x[0])):
                print(label, count)
        else:
            rows = [row for row in reader]
            print('rows', len(rows), 'sample', rows[:5])
