"""Batch-3 raw-data validation shared by the gate and proposed drop list."""
from .encode import prompt_addendum
from .levels import levels_for
from .stability import DIMENSIONS, level_statistics

REPEATS = 6
LANGS = ('zh', 'en')


def statistics(foods, records):
    if not foods or len({f['key'] for f in foods}) != len(foods):
        raise ValueError('batch 3 requires a nonempty food list with distinct keys')
    seen = set()
    versions = set()
    for row, record in enumerate(records, 1):
        index, lang, repeat = (record.get(k) for k in ('food_index', 'lang', 'repeat'))
        if (type(index) is not int or not 0 <= index < len(foods) or lang not in LANGS
                or type(repeat) is not int or not 1 <= repeat <= REPEATS):
            raise ValueError(f'row {row}: invalid food_index / lang / repeat')
        slot = index, lang, repeat
        if slot in seen:
            raise ValueError(f'row {row}: duplicate observation {slot}')
        seen.add(slot)
        if record.get('food') != foods[index]:
            raise ValueError(f'row {row}: food identity differs from approved list')
        if ('prompt_addendum' not in record
                or record['prompt_addendum'] != prompt_addendum(foods[index])):
            raise ValueError(f'row {row}: prompt addendum does not match food flag')
        if record.get('prompt_version') != 'encode_v2.3' or record.get('schema_version') != 'schema_v2':
            raise ValueError(f'row {row}: expected encode_v2.3 / schema_v2')
        version = record.get('encoder_version', '')
        if not version.endswith('@encode_v2.3'):
            raise ValueError(f'row {row}: invalid encoder version')
        versions.add(version)
        if 'error' in record:
            if 'entry' in record:
                raise ValueError(f'row {row}: both entry and error')
            continue
        entry = record.get('entry', {})
        if entry.get('encoder_version') != version:
            raise ValueError(f'row {row}: entry encoder version mismatch')
        if entry.get('encoder_addendum') != prompt_addendum(foods[index]):
            raise ValueError(f'row {row}: entry addendum mismatch')
        for dimension in DIMENSIONS:
            if entry.get(dimension) not in levels_for(dimension):
                raise ValueError(f'row {row}: missing/invalid {dimension}')
    if len(versions) > 1:
        raise ValueError('mixed encoder versions')
    return level_statistics(foods, records, REPEATS, LANGS, DIMENSIONS)
