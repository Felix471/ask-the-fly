# SPDX-License-Identifier: MIT
"""Male-only data adapter calling the unchanged Shiu equations in sim.network."""
import json
from pathlib import Path
import sys

from sim.malecns.substrate import DATA, ROOT, sha256, verify_record


def load_configuration(verify=True):
    if verify:
        verify_record()
    protocol = json.loads((DATA / 'stim_protocol_malecns.json').read_text(encoding='utf-8'))
    cells = json.loads((DATA / 'cells.json').read_text(encoding='utf-8'))
    base = json.loads((ROOT / 'data/stim_protocol.json').read_text(encoding='utf-8'))
    if protocol['model'] != base['model'] or protocol['trial'] != base['trial']:
        raise ValueError('Male adapter must retain every frozen model and trial parameter')
    if protocol['male_provenance']['reference_protocol_sha256'] != sha256(ROOT / 'data/stim_protocol.json'):
        raise ValueError('Reference protocol hash mismatch')
    if protocol['readout']['primary'] != 16949 or protocol['readout']['secondary'] != 10331:
        raise ValueError('Readout convention changed')
    for field in ('connectivity_file', 'completeness_file'):
        path = (ROOT / protocol[field]).resolve()
        if not path.is_relative_to(DATA.resolve()):
            raise ValueError('Male substrate files must remain under data/malecns')
    layout = protocol['male_provenance']['stimulation_layout']
    ids = [i for name in layout['channel_order'] for i in cells['sets'][name]['ids']]
    if len(ids) != layout['poisson_units'] or len(ids) != len(set(ids)):
        raise ValueError('Male physical input layout changed or overlaps')
    return protocol, cells


def build_male_network(verify=True):
    if sys.platform != 'linux':
        raise RuntimeError('Male Brian2 runs require the existing WSL2 flybrain environment')
    protocol, cells = load_configuration(verify=verify)
    # Import only at the simulation boundary. The female file is never modified.
    from sim.network import build_network
    model = build_network(protocol, cells, protocol['male_provenance']['stimulation_layout']['channel_order'])
    return model, protocol, cells
