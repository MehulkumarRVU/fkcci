import sqlite3
from app.database import SQLALCHEMY_DATABASE_URL

db = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
print('DB PATH:', db)
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='skills'")
print('skills_table_exists', cur.fetchone()[0])
try:
    cur.execute('SELECT sport_type, COUNT(*) FROM skills GROUP BY sport_type')
    print('skill_counts_by_sport', cur.fetchall())
    cur.execute('SELECT id, name, sport_type, difficulty_level, is_active FROM skills WHERE sport_type="boxing"')
    print('boxing_skills', cur.fetchall())
except Exception as e:
    print('ERROR', e)
finally:
    conn.close()
