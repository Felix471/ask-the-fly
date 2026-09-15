"""Export additive v1.2 assets. Never overwrite the frozen v1 lookup/replays."""
import shutil
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def main():
    shutil.copyfile(ROOT / 'data/lookup_table_v1_2.json', ROOT / 'site/data/lookup_table_v1_2.json')
    shutil.copytree(ROOT / 'data/replay_v1_2', ROOT / 'site/data/replay_v1_2', dirs_exist_ok=True)
    source = ROOT / 'results/mn11_animation_preview/frames'
    frames = [source / f'{prefix}{state}_{i}.png' for prefix in ('','inset_')
              for state in ('eats','mouth_moves','proboscis_only','no_response') for i in range(1,5)]
    if not all(p.is_file() for p in frames):
        raise FileNotFoundError('Run scripts.mn11_anim_preview on the approved v3 board first')
    target = ROOT / 'site/assets/response'
    target.mkdir(exist_ok=True)
    for path in frames:
        shutil.copyfile(path, target / path.name)
    manifest = json.loads((source.parent / 'manifest.json').read_text(encoding='utf8'))
    record = {
        'schema': 'response_assets_v1',
        'source': manifest['source'].replace('\\', '/'),
        'source_sha256': manifest['source_sha256'],
        'generator': 'Built-in image generation, reference-guided action board; original sprite style retained',
        'processing': 'scripts/mn11_anim_preview.py using scripts/prep_assets.py helpers',
        'interpretation': 'Owner-reviewed illustrative actions, not measured behaviour',
        'files': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in frames},
    }
    (target / 'manifest.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
    print('Exported additive lookup, 400 baseline packs and 32 response frames; frozen paths untouched')


if __name__ == '__main__':
    main()
