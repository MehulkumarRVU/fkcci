from pathlib import Path
p = Path('dataset/README.md')
print('exists', p.exists())
with p.open('r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        print(f'{i}: {line!r}')
