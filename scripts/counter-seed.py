#!/usr/bin/env python3
"""Create one-time SQL import from an explicitly captured real counter total."""
import argparse,json,sys
from datetime import datetime
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('snapshot',type=Path)
args=parser.parse_args()
snapshot=json.loads(args.snapshot.read_text(encoding='utf-8'))
total=snapshot['total']
if not isinstance(total,int) or isinstance(total,bool) or total<0:
    raise SystemExit('total must be a non-negative integer')
started=snapshot['startedAt']
datetime.fromisoformat(started.replace('Z','+00:00'))
print('-- One-time initial import only. Existing counters are never reset.')
print("INSERT INTO site_views(id,total,started_at) VALUES('global',%d,'%s') ON CONFLICT(id) DO NOTHING;" % (total,started.replace("'","''")))
