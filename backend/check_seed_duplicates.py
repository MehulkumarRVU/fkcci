import re
from pathlib import Path
from collections import Counter

text = Path('app/seed_data.py').read_text(encoding='utf-8')
names = re.findall(r'"name"\s*:\s*"([^"]+)"', text)
counts = Counter(names)
dups = [(name, count) for name, count in counts.items() if count > 1]
print(f'Total skill names: {len(names)}')
print(f'Duplicate entries: {len(dups)}')
for name, count in dups:
    print(name, count)
