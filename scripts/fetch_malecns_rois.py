# SPDX-License-Identifier: MIT
"""Fetch public MaleCNS legacy ROI meshes once; no browser/runtime requests.

Existing downloads are reused only after manifest verification, never downloaded
again. Unknown/unmatched ROI names are reported, never inferred anatomically.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'data/external/malecns_rois'
BASE = 'https://storage.googleapis.com/flyem-male-cns/rois/fullbrain-roi-v4/'

# Exact nomenclature alternatives, not fuzzy/sub-string matching. The actual
# matched names (and every missing component) are recorded in the manifest.
GROUPS = {
    'sez': [('GNG',), ('SAD',), ('AMMC(L)', 'AMMC_L'), ('AMMC(R)', 'AMMC_R'), ('PRW',)],
    'al_l': [('AL(L)', 'AL_L')], 'al_r': [('AL(R)', 'AL_R')],
    'cx': [('FB',), ('EB',), ('PB',), ('NO',)],
}
for side in ('L', 'R'):
    # MaleCNS names the lobes by Greek letter (aL, a'L vertical; bL, b'L, gL medial).
    GROUPS['mb_'+side.lower()] = [(f'{part}({side})', f'{part}_{side}', f'MB_{part}_{side}')
                                  for part in ('CA', 'PED', 'aL', "a'L", 'bL', "b'L", 'gL')]
    GROUPS['ol_'+side.lower()] = [(f'{part}({side})', f'{part}_{side}')
                                  for part in ('ME', 'LO', 'LOP', 'LA', 'AME')]


def match_groups(names):
    names = set(names)
    groups, missing = {}, {}
    for key, components in GROUPS.items():
        matched, absent = [], []
        for alternatives in components:
            found = [name for name in alternatives if name in names]
            if len(found) > 1:
                raise ValueError(f'Ambiguous ROI component {key}: {found}')
            if found:
                matched.extend(found)
            else:
                absent.append(list(alternatives))
        if absent:
            missing[key] = absent
        else:
            groups[key] = matched
    return groups, missing


def download(url):
    with urlopen(url, timeout=120) as response:
        return response.read()


def local_path(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative or not relative:
        raise ValueError(f'Unsafe mesh path: {relative}')
    # Colons in legacy names (e.g. 123:0) cannot be Windows filenames/ADS, and Windows
    # filesystems are case-insensitive (MaleCNS has both AL(L) and aL(L)), so every
    # part carries a short hash of its exact spelling.
    target = root.joinpath(*(f"{quote(part, safe='')}~{hashlib.sha256(part.encode()).hexdigest()[:8]}"
                             for part in path.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f'Path outside mesh cache: {relative}')
    return target


def fetch_one(root, relative, records, downloader=download):
    target = local_path(root, relative)
    url = BASE+quote(relative, safe='/')
    if target.exists():
        blob = target.read_bytes()
        record = dict(url=url, bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())
        if records.get(relative) != record:
            raise ValueError(f'Existing file lacks a matching manifest record: {relative}')
        return blob
    blob = downloader(url)
    record = dict(url=url, bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())
    if relative in records and records[relative] != record:
        raise ValueError(f'Download changed versus recorded manifest: {relative}')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as out:
        out.write(blob)
    records[relative] = record
    return blob


def roi_names(properties):
    inline = properties['inline']
    labels = [p['values'] for p in inline['properties'] if p['type'] == 'label']
    if len(labels) != 1 or len(labels[0]) != len(inline['ids']):
        raise ValueError('Invalid segment name properties')
    names = dict(zip(labels[0], inline['ids']))
    if len(names) != len(inline['ids']):
        raise ValueError('Duplicate ROI names')
    return names


def fetch(root=DEST, downloader=download):
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else dict(
        source=BASE, files={})
    if manifest['source'] != BASE:
        raise ValueError('Unexpected mesh source')
    def save():
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    def get(relative):
        blob = fetch_one(root, relative, manifest['files'], downloader)
        save()  # every completed file remains resumable after a later failure
        return blob
    info = json.loads(get('info'))
    if info.get('mesh') != 'mesh':
        raise ValueError('Expected legacy mesh directory')
    names = roi_names(json.loads(get('segment_properties/info')))
    groups, missing = match_groups(names)
    manifest.update(groups=groups, unmatched=missing, available_names=sorted(names), meshes={})
    save()
    for name in sorted({name for members in groups.values() for name in members}):
        mesh = json.loads(get('mesh/'+str(names[name])+':0'))
        fragments = mesh['fragments']
        if not fragments or len(set(fragments)) != len(fragments):
            raise ValueError(f'Invalid mesh fragments: {name}')
        for fragment in fragments:
            get('mesh/'+fragment)
        manifest['meshes'][name] = dict(segment_id=str(names[name]), fragments=fragments)
        save()
        print(f'{name}: {len(fragments)} fragments', flush=True)
    print(json.dumps(dict(matched=groups, unmatched=missing), indent=2))
    return manifest


if __name__ == '__main__':
    try:
        fetch()
    except (OSError, ValueError) as exc:
        sys.exit(f'ROI fetch failed: {exc}')
