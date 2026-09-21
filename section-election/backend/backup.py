"""Consistent private SQLite backup; does not create voting codes or send mail."""
import argparse,os,sqlite3
from pathlib import Path

def backup(source,target):
    os.umask(0o077)
    if not Path(source).is_file():raise ValueError('Source database does not exist')
    with open(target,'xb'):pass
    src=sqlite3.connect(source);dst=sqlite3.connect(target)
    try:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Backup integrity check failed')
    finally:src.close();dst.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--output',required=True);a=p.parse_args();backup(a.db,a.output)
