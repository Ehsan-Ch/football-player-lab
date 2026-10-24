"""Revision-pinned acquisition. Raw provider data stays local and untracked."""
import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REVISION='4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
BASE=f'https://raw.githubusercontent.com/hudl/open-data/{REVISION}/'
STAGES={'Round of 16','Quarter-finals','Semi-finals','Final','3rd Place Final'}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def download(path):
    with urllib.request.urlopen(BASE+path,timeout=90) as response:raw=response.read(20_000_001)
    if len(raw)>20_000_000:raise ValueError('Source file too large')
    return raw

def prepare(root='data'):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'manifest.json').exists():raise ValueError('Use a new data directory')
    raw=download('data/matches/43/106.json');matches=json.loads(raw)
    selected=sorted([m for m in matches if m['competition_stage']['name'] in STAGES],key=lambda m:(m['match_date'],m['match_id']))
    if len(selected)!=16:raise ValueError(f'Expected 16 knockout matches, found {len(selected)}')
    (root/'matches.json').write_bytes(raw)
    tasks=[f'data/{kind}/{m["match_id"]}.json' for m in selected for kind in ('events','lineups')]
    def worker(path):
        content=download(path);dest=root/Path(path).relative_to('data');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
        return {'path':str(Path(path).relative_to('data')).replace('\\','/'),'sha256':digest(content),'bytes':len(content)}
    with ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(worker,tasks))
    manifest={'revision':REVISION,'selection':'All 16 World Cup 2022 knockout-stage matches, including the third-place match. Group stage excluded.',
              'match_ids':[m['match_id'] for m in selected],'files':[{'path':'matches.json','sha256':digest(raw),'bytes':len(raw)},*files]}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Downloaded {len(files)} files for {len(selected)} matches',flush=True)

def load(root):
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if manifest['revision']!=REVISION:raise ValueError('Unexpected source revision')
    for f in manifest['files']:
        path=(root/f['path']).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path.read_bytes())!=f['sha256']:raise ValueError('Source integrity mismatch')
    matches=json.loads((root/'matches.json').read_bytes())
    return manifest,[m for m in matches if m['match_id'] in manifest['match_ids']]
