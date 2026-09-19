# SPDX-License-Identifier: MIT
"""M1j female v783 runner: 128 physical slots, frozen left MN9 primary."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sim.malecns import m1j_adapter as adapter
from sim.malecns.m1j_phase0 import main, run as run_brain, summarize

SIDES = {'L': 720575940660219265, 'R': 720575940618238523}


def expected_protocol():
    return adapter.expected_protocol('female')


def validate_protocol(protocol):
    return adapter.validate_protocol(protocol, 'female')


def run(host_free_kib):
    return run_brain(host_free_kib, 'female')


if __name__ == '__main__':
    main('female')
