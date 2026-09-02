import json
import sqlite3
from pathlib import Path
from app.database import SQLALCHEMY_DATABASE_URL
from urllib import request, error

print('Checking SQLite database...')
db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///','')
print('db_path:', db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='skills'")
print('skills_table_exists:', cur.fetchone()[0])
cur.execute('SELECT sport_type, COUNT(*) FROM skills GROUP BY sport_type')
print('skill_counts_by_sport:', cur.fetchall())
cur.execute("SELECT id, name, sport_type, difficulty_level, is_active FROM skills WHERE sport_type='boxing'")
boxing_rows = cur.fetchall()
print('boxing_skills_count:', len(boxing_rows))
for row in boxing_rows:
    print(row)
conn.close()

print('\nChecking API endpoint...')
try:
    url = 'http://localhost:8080/api/skills/?sport_type=boxing'
    resp = request.urlopen(url, timeout=5)
    data = json.loads(resp.read().decode('utf-8'))
    print('api_status:', resp.status)
    print('api_boxing_skill_count:', len(data))
    for skill in data:
        print(skill['id'], skill['name'], skill['difficulty_level'], skill['is_active'])
except error.URLError as e:
    print('api_error:', e)
except Exception as e:
    print('api_exception:', type(e).__name__, e)
