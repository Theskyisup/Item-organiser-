"""Simple DB watcher: prints latest rows when USERinformation.db changes.
Run: python watch_db.py
"""
import time
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / 'USERinformation.db'

if not DB.exists():
    print('USERinformation.db not found at', DB)
    raise SystemExit(1)

last_mtime = DB.stat().st_mtime

def print_latest():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT rowid, Username, Password FROM ImportantInfo ORDER BY rowid DESC LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    print('\n===', time.strftime('%Y-%m-%d %H:%M:%S'), '===')
    for r in rows:
        print(r)

print('Watching', DB)
print_latest()
try:
    while True:
        m = DB.stat().st_mtime
        if m != last_mtime:
            last_mtime = m
            print_latest()
        time.sleep(1)
except KeyboardInterrupt:
    print('\nStopped')
