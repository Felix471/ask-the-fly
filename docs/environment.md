# Simulation environment (Phase 0.1)

## Decision: WSL2 is the ground-truth backend
- Native Windows was tried once (Python 3.12 venv, `pip install brian2`, `prefs.codegen.target='cython'`): Brian2 failed while preparing `neurongroup_stateupdater` because no C++ compiler is installed (no `cl.exe`). Per project rule, not troubleshot.
- All gated Brian2 runs execute in WSL2 Ubuntu, conda env `flybrain`. The `numpy` codegen target is allowed only for pipeline smoke tests.

## WSL2 setup notes
- WSL2 (NAT mode) initially had no network at all (DNS pointed at 10.255.255.254 via a Tailscale search domain; even raw-IP HTTPS failed). Fixed without sudo by creating `C:\Users\<user>\.wslconfig`:
  ```
  [wsl2]
  networkingMode=mirrored
  dnsTunneling=true
  autoProxy=true
  ```
  followed by `wsl --shutdown`. Revert by deleting the file.
- No passwordless sudo in the distro, so compilers come from conda-forge (`gxx_linux-64`), not apt.
- Miniforge at `~/miniforge3`; env spec in `env/flybrain.yml`, exact export in `env/flybrain-lock.yml`.
- Brian2's Cython cache lives on the Linux filesystem (`~/.cache/brian2_flybrain`), never on `/mnt/d`.

## Verified 2026-09-10
| item | value |
|---|---|
| brian2 | 2.9.0 |
| numpy / cython | 1.26.4 / 3.3.0 |
| compiler | conda-forge g++ 14.4.0 |
| torch | 2.14.0+cu126, CUDA available, RTX 4080 SUPER 16 GB |
| CPU / RAM visible to WSL2 | 32 threads / 62 GB |
| codegen test | 1000-neuron LIF net, cython: first run ~20 s (compile), store/restore rerun 0.24 s |
| paper reset string | `v = v_rst; w = 0; g = 0 * mV` accepted verbatim by Brian2 2.9.0 |

## How to run
```
wsl -e bash -lc 'cd /mnt/d/WhatDoesTheFlyEat && ~/miniforge3/bin/conda run -n flybrain --no-capture-output python scripts/run_phase0.py --stage smoke'
```
