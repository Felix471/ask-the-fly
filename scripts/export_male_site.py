# SPDX-License-Identifier: MIT
"""Ship the frozen male lookup and dish-occupied trial-0 replays; no simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.grid import grid_cell_id, resolve_levels

def shipping_rule(root):
    count = len(read(root / 'data/dishes.json'))
    return f'cells occupied by the {count} dishes; the other recorded cells stay in the research pack'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def current_commit(root):
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()


def occupied_cells(root, table):
    dishes = read(root / 'data/dishes.json')
    if not dishes or len({d['key'] for d in dishes}) != len(dishes):
        raise ValueError('male: expected nonempty dictionary with distinct keys')
    cells = sorted({grid_cell_id(resolve_levels(table, dish)) for dish in dishes})
    # Phase 2's 55 occupied cells is a historical comparison, not a size guard.
    return cells


def source_manifest(root, ids):
    folder = root / 'data/replay_male'
    path = folder / 'manifest.json'
    manifest = read(path)
    if (manifest.get('schema_version') != 'replay_manifest_v1' or manifest.get('fly') != 'male'
            or manifest.get('n_cells') != 400 or len(manifest.get('cells', {})) != 400):
        raise ValueError('male: invalid 400-cell research manifest')
    entries = {}
    for cid in ids:
        if cid not in manifest['cells']:
            raise ValueError('male: dish cell absent from research manifest: ' + cid)
        file = folder / (cid + '.bin')
        entries[cid] = dict(manifest['cells'][cid], sha256=sha256(file), bytes=file.stat().st_size)
    return dict(schema_version='replay_manifest_v1', fly='male', n_cells=len(ids),
                n_cells_recorded=400, shipping_rule=shipping_rule(root), variants=['baseline'],
                source_manifest_sha256=sha256(path), cells=entries)


def check_export(root=ROOT, *, research_optional=False):
    """Verify site assets; CI can validate the shipped hashes without the ignored pack."""
    problems = []
    source = root / 'data/lookup_table_male.json'
    target = root / 'site/data/lookup_table_male.json'
    if source.read_bytes() != target.read_bytes():
        problems.append('male: source/site table bytes differ')
    ids = occupied_cells(root, read(source))
    folder = root / 'site/data/replay_male'
    manifest = read(folder / 'manifest.json')
    expected = dict(schema_version='replay_manifest_v1', fly='male', n_cells=len(ids),
                    n_cells_recorded=400, shipping_rule=shipping_rule(root), variants=['baseline'])
    for key, value in expected.items():
        if manifest.get(key) != value:
            problems.append('male: invalid replay manifest ' + key)
    for key, length in [('git_commit', 40), ('source_manifest_sha256', 64)]:
        if not re.fullmatch('[0-9a-f]{' + str(length) + '}', str(manifest.get(key, ''))):
            problems.append('male: invalid replay manifest ' + key)
    entries = manifest.get('cells')
    if not isinstance(entries, dict):
        return problems + ['male: invalid replay manifest cells']
    if set(entries) != set(ids):
        problems.append('male: replay manifest does not cover exactly the dish cells')
    for cid in ids:
        file = folder / (cid + '.bin')
        entry = entries.get(cid, {})
        if not file.is_file():
            problems.append('male: missing dish replay ' + cid)
        elif not isinstance(entry, dict) or entry.get('sha256') != sha256(file) or entry.get('bytes') != file.stat().st_size:
            problems.append('male: replay sha256/bytes mismatch ' + cid)
    expected_names = {cid + '.bin' for cid in ids}
    for file in sorted(folder.glob('*.bin')):
        if file.name not in expected_names:
            problems.append('male: orphan file ' + file.name)
    # A checkout without the research pack still checks every shipped file above.
    if not research_optional or (root / 'data/replay_male').exists():
        expected = source_manifest(root, ids)
        if {k: v for k, v in manifest.items() if k != 'git_commit'} != expected:
            problems.append('male: site manifest differs from research manifest/files')
    return problems


def export(root=ROOT, *, force=False):
    target = root / 'site/data/lookup_table_male.json'
    folder = root / 'site/data/replay_male'
    if not force and (target.exists() or folder.exists()):
        raise FileExistsError('Male site outputs exist; use --force to replace them')
    source = root / 'data/lookup_table_male.json'
    manifest = dict(source_manifest(root, occupied_cells(root, read(source))), git_commit=current_commit(root))
    # Validate all inputs before replacing any output. --force removes only stale .bin
    # assets inside this exact site folder, never the research pack.
    target.parent.mkdir(parents=True, exist_ok=True)
    folder.mkdir(exist_ok=True)
    shutil.copyfile(source, target)
    for cid in manifest['cells']:
        shutil.copyfile(root / f'data/replay_male/{cid}.bin', folder / (cid + '.bin'))
    for file in folder.glob('*.bin'):
        if file.stem not in manifest['cells']:
            file.unlink()
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                                        encoding='utf-8', newline='\n')
    problems = check_export(root)
    if problems:
        raise ValueError('\n'.join(problems))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--force', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        problems = check_export()
        if problems:
            raise ValueError('\n'.join(problems))
        manifest = read(ROOT / 'site/data/replay_male/manifest.json')
    else:
        manifest = export(force=args.force)
    replay_bytes = sum(entry['bytes'] for entry in manifest['cells'].values())
    all_bytes = replay_bytes + sum((ROOT / rel).stat().st_size for rel in
        ('site/data/replay_male/manifest.json', 'site/data/lookup_table_male.json'))
    print(f"Male site {'verified' if args.check else 'exported'}: {manifest['n_cells']} cells, "
          f'{replay_bytes} replay bytes; {all_bytes} total shipped table/manifest/replay bytes')


if __name__ == '__main__':
    main()
