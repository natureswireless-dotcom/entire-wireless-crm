"""Consistent SQLite backup. Does not include uploaded documents or statement files."""
import argparse
import sqlite3
from pathlib import Path
p=argparse.ArgumentParser(description='Back up the CRM SQLite database without loading CRM integrations.')
p.add_argument('database',type=Path,help='Path to isp_crm_v2.db')
p.add_argument('destination',type=Path,help='New private backup file path; must not exist')
a=p.parse_args()
if not a.database.is_file(): p.error('Source database does not exist.')
if a.destination.exists(): p.error('Destination already exists; choose a new backup filename.')
a.destination.parent.mkdir(parents=True,exist_ok=True)
# Exclusive creation prevents accidentally overwriting an existing backup.
fd=a.destination.open('xb'); fd.close(); a.destination.chmod(0o600)
try:
    with sqlite3.connect(a.database.resolve().as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(a.destination) as target:
        source.backup(target)
        if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise RuntimeError('Backup integrity check failed')
except Exception:
    a.destination.unlink(missing_ok=True)
    raise
print('Database backup complete. Copy customer_documents and statements separately.')
