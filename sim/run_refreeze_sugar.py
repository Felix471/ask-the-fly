# SPDX-License-Identifier: MIT
"""R1: paired sugar-set pilot plus original Phase 0 gates and adapted A-prime.

22 conditions x 30 trials = 660 runs, research only. No frozen/product changes.
python -B -m sim.run_refreeze_sugar --check-design
WSL2 flybrain only: python -B -m sim.run_refreeze_sugar --n-proc 13
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np

from sim import run_pharyngeal as p1
from sim.run_mn_readouts import load_json, published_grid_seed, sha256, summarize_trials, write_csv
from scripts.build_mn_readout_ids import read_v783_ids
from scripts.cem_inputs import exact_id
from scripts.cross_check_cells import FLYWIRE, read_xlsx
from scripts.mn_readouts_from_replays import aggregate_metrics, neuron_metrics, validate_spikes

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data/stim_protocol_refreeze_sugar.json"
N_TRIALS = 30
N_CONDITIONS = 22
DOSES = (0, 60, 80, 120, 200)
CORE_GROUPS = ("MN9_L", "MN9_R", "MN11D", "MN11V")
SOURCE_GROUPS = ("frozen_sugar23", "candidate33", "LB3b13", "LB3c20", "shared12", "bitter42")
DRIVE_GROUPS = ("frozen_sugar23", "candidate33", "LB3c20", "bitter42")
SEED_INDICES = tuple(range(5)) + tuple(range(5)) + tuple(range(5, 16)) + (3,)


def phase_r1_seed(condition_index, trial, base_seed=20260910):
    for value, upper, name in ((condition_index, N_CONDITIONS, "condition_index"), (trial, N_TRIALS, "trial")):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not 0 <= value < upper:
            raise ValueError(f"invalid {name}")
    return published_grid_seed(SEED_INDICES[condition_index], trial, base_seed)


def select_conditions():
    definitions = [(f"R1_old_{dose}", (dose, 0, 0, 0)) for dose in DOSES]
    definitions += [(f"R1_new_{dose}", (0, dose, 0, 0)) for dose in DOSES]
    definitions += [(f"R1_A_new_{dose}", (0, dose, 0, 0)) for dose in (25, 50, 100)]
    definitions += [(f"R1_B_new200_bitter{dose}", (0, 200, 0, dose)) for dose in (25, 50, 100, 200)]
    definitions += [(f"R1_C_bitter{dose}", (0, 0, 0, dose)) for dose in (25, 50, 100, 200)]
    definitions += [("R1_Aprime_LB3c20_120", (0, 0, 120, 0))]
    return [{"cond_id": name, "condition_index": index, "seed_index": SEED_INDICES[index],
             "group_rates": dict(zip(DRIVE_GROUPS, rates))} for index, (name, rates) in enumerate(definitions)]


def candidate_source_rows(rows, v783):
    selected, seen = [], set()
    for row in rows:
        if row.get("Connectome") != FLYWIRE or row.get("Subtype") not in {"LB3b", "LB3c"} or row.get("Root_Side") != "L":
            continue
        root = exact_id(row.get("Body_ID"))
        if not isinstance(row["Body_ID"], str) or root in seen or row.get("Type") != "LB3":
            raise ValueError("invalid candidate source annotation or duplicate root")
        seen.add(root)
        fields = ("Body_ID", "Root_Side", "Type", "Subtype", "Entry_Nerve")
        selected.append({**{k: row.get(k, "") for k in fields}, "in_v783": str(root) in v783})
    if len(selected) != 33 or [sum(n["Subtype"] == k for n in selected) for k in ("LB3b", "LB3c")] != [13, 20]:
        raise ValueError("expected exactly 13 LB3b and 20 LB3c XLSX-side-L FlyWire cells")
    if not all(n["in_v783"] for n in selected):
        raise ValueError("candidate neuron absent from v783")
    return selected


def source_groups(spec, cells):
    rows = spec["candidate_neurons"]
    roots = [exact_id(n["Body_ID"]) for n in rows]
    if len(roots) != 33 or len(set(roots)) != 33:
        raise ValueError("candidate must have 33 distinct roots")
    if not all(isinstance(n["Body_ID"], str) and n.get("in_v783") is True and
               n.get("Root_Side") == "L" and n.get("Type") == "LB3" and
               n.get("Subtype") in {"LB3b", "LB3c"} for n in rows):
        raise ValueError("candidate IDs must preserve exact XLSX L-side LB3b/LB3c typing and v783 presence")
    old = [str(exact_id(i)) for i in cells["sets"]["sugar"]["ids"]]
    bitter = [str(exact_id(i)) for i in cells["sets"]["bitter"]["ids"]]
    candidate = [n["Body_ID"] for n in rows]
    lb3b = [n["Body_ID"] for n in rows if n["Subtype"] == "LB3b"]
    lb3c = [n["Body_ID"] for n in rows if n["Subtype"] == "LB3c"]
    shared = [root for root in candidate if root in set(old)]
    result = dict(zip(SOURCE_GROUPS, (old, candidate, lb3b, lb3c, shared, bitter)))
    if [len(result[g]) for g in SOURCE_GROUPS] != [23, 33, 13, 20, 12, 42]:
        raise ValueError("source counts/overlap differ from the authorised R1 design")
    if len(set(old)) != 23 or len(set(bitter)) != 42 or (set(old) | set(candidate)) & set(bitter):
        raise ValueError("invalid duplicated or overlapping sugar/bitter sources")
    if len(set(old) | set(candidate) | set(bitter)) != 86:
        raise ValueError("expected 86 unique monitored source GRNs")
    return result


def make_stimulation(spec, cells):
    """Original P1 physical-root order plus missing candidate roots, each exactly once."""
    expanded, original_mapping = p1.make_stimulation(spec, cells)
    original = [str(exact_id(i)) for name in original_mapping.values() for i in expanded["sets"][name]["ids"]]
    groups = source_groups(spec, cells)
    extra = sorted(set(groups["candidate33"]) - set(original), key=int)
    roots = original + extra
    if len(original) != 151 or len(extra) != 14 or len(roots) != 165 or len(set(roots)) != 165:
        raise ValueError("expected fixed 151 original roots plus 14 added candidate roots")
    copied, mapping = deepcopy(cells), {}
    for root in roots:
        channel = f"r1_{root}"
        if channel in copied["sets"]:
            raise ValueError("research singleton would overwrite existing set")
        copied["sets"][channel] = {"ids": [root]}
        mapping[channel] = channel
    return copied, mapping


def effective_rates(spec, cells, condition):
    _, mapping = make_stimulation(spec, cells)
    groups = source_groups(spec, cells)
    requested = condition["group_rates"]
    if tuple(requested) != DRIVE_GROUPS:
        raise ValueError("unexpected logical drive groups or order")
    rates, assigned = dict.fromkeys(mapping, 0), set()
    for group, hz in requested.items():
        if isinstance(hz, (bool, np.bool_)) or not isinstance(hz, (int, float, np.number)) or not np.isfinite(hz) or hz < 0:
            raise ValueError("drive rates must be finite and nonnegative")
        if hz == 0:
            continue
        for root in groups[group]:
            if root in assigned:
                raise ValueError("active logical groups overlap; additive or last-write input forbidden")
            assigned.add(root)
            rates[f"r1_{root}"] = hz
    return rates


def groups_for(spec, protocol, condition, cells):
    rows = spec["readout_neurons"]
    result = {"MN9_L": [str(protocol["readout"]["left"])], "MN9_R": [str(protocol["readout"]["right"])]}
    for kind in ("MN11D", "MN11V"):
        result[kind] = [n["Body_ID"] for n in rows if n["Type"] == kind]
    if [len(result[g]) for g in CORE_GROUPS] != [1, 1, 2, 2] or set(r for ids in result.values() for r in ids) != {n["Body_ID"] for n in rows}:
        raise ValueError("expected exactly six MN readout neurons")
    result.update(source_groups(spec, cells))
    driven = [channel.removeprefix("r1_") for channel, hz in effective_rates(spec, cells, condition).items() if hz > 0]
    if driven:
        result["actual_driven_union"] = driven
    return result


def build_spec():
    """Read source documents and return the exact new protocol; no writes/simulation."""
    prior, protocol, cells = p1.load_design()
    source = prior["pharyngeal_source"]
    v783 = read_v783_ids(ROOT / protocol["completeness_file"])
    rows = read_xlsx(ROOT / source["file"])["GRNs"]
    candidate = candidate_source_rows(rows, v783)
    groups = source_groups({"candidate_neurons": candidate}, cells)
    all_ids = set(groups["frozen_sugar23"]) | set(groups["candidate33"]) | set(groups["bitter42"])
    all_sources = []
    for row in rows:
        if row.get("Connectome") == FLYWIRE and row.get("Body_ID") in all_ids:
            fields = ("Body_ID", "Root_Side", "Type", "Subtype", "Entry_Nerve")
            all_sources.append({**{k: row.get(k, "") for k in fields}, "in_v783": row["Body_ID"] in v783})
    if len(all_sources) != 86 or len({n["Body_ID"] for n in all_sources}) != 86 or not all(n["in_v783"] for n in all_sources):
        raise ValueError("all 86 source annotations must occur exactly once in XLSX and v783")
    old_rows = [n for n in all_sources if n["Body_ID"] in set(groups["frozen_sugar23"])]
    if {n["Root_Side"] for n in old_rows} != {"L"}:
        raise ValueError("candidate must match the frozen sugar stimulus side under XLSX naming")
    return {"schema_version": "refreeze_sugar_r1_v1", "base_protocol": prior["base_protocol"],
            "base_protocol_sha256": prior["base_protocol_sha256"], "p1_protocol": "data/stim_protocol_pharyngeal.json",
            "p1_protocol_sha256": sha256(p1.SPEC), "frozen_cells_sha256": prior["frozen_cells_sha256"],
            "candidate_source": {**source, "selection": "Exact FlyWire rows, Type LB3, Subtype LB3b or LB3c, Root_Side L; 13+20=33 cells. XLSX L is the frozen Shiu right-stimulus side."},
            "candidate_neurons": candidate, "source_neurons": all_sources,
            "readout_neurons": [n for n in prior["readout_neurons"] if n["Type"] != "CEM"],
            "n_poisson_units": 165, "layout": "Original P1 physical order (151 roots), followed by 14 missing candidate roots sorted numerically. One singleton channel per unique root; candidate overlaps 12 frozen sugar and seven frozen water cells. Every physical neuron receives one effective rate/refractory assignment.",
            "trial": {"n_trials": N_TRIALS, "base_seed": 20260910, "seed_scheme": "published_grid_v1_batch40",
                      "seed_rule": "20260910+1000*(seed_index%40)+trial, trial0..29. Old/new five-dose curves share seedindices0..4; eleven Phase0 additions use5..15; Aprime120 shares3 with new120. 660 runs, 480 distinct seed values."},
            "conditions": select_conditions(),
            "reused_conditions": {"D_baseline": "R1_new_0", "A_sugar200": "R1_new_200", "B_bitter0": "R1_new_200", "Aprime_candidate120": "R1_new_120"},
            "analysis": {"rate": "Count per full1second; MN9 L/R individual, MN11D/V two-cell mean; all86sourceGRNs recorded individually including inactive sources; groups overlap and are not additive.",
            "std": "Population SD across30trials, ddof=0.", "latency": "First-spike median among active trials with active counts; group first spike is earliest member.",
            "normalization": "Divide each set's mean and each trial rate at every dose by that set's OWN mean at200Hz; 200Hz means become1 while trial SD remains nonzero. Do not propagate uncertainty in the estimated200Hz mean; zero denominator means undefined.",
            "paired": "Old/new ratio of means at each dose and paired differences; normalized new-minus-old per-trial differences. Aprime LB3c20-minus-candidate33 at120Hz paired mean/SD. Verify actual shared-root Poisson events.",
            "shape_flag": "Preregistered descriptive screen: at interior60/80/120Hz flag if absolute mean paired normalized difference exceeds twice its population SD. Our design, not a significance test or a demonstrated change of full-grid dish ranking.",
            "size_caveat": "33/23 is the ratio of expected total external Poisson input at equal per-cell Hz, not a predicted MN-output ratio; cell identities and circuit interactions also change.",
            "phase0": "Require exact A25/50/100/200, B0/25/50/100/200 at candidate200, C25/50/100/200, and D0 coverage with30trials each. Original left-only hard gates retained: A strict increases except zero/zero and A200>Dmean+5Dsd+5; B nonincrease and B200<0.5B0; Cmean<=Dmean+2Dsd+1; D complete. Also report strict all-zero C/D for both MN9 sides separately."},
            "results": "results/refreeze/sugar_r1/ (local/gitignored; no product or lookup changes)"}


def load_design():
    extra = load_json(SPEC)
    if extra != build_spec():
        raise ValueError("R1 protocol differs from source annotations or authorised design")
    prior, protocol, cells = p1.load_design()
    spec = {**prior, **extra}
    for condition in select_conditions():
        groups_for(spec, protocol, condition, cells)
    return spec, protocol, cells


def _individual_descriptions(spec, cells, condition):
    rates = effective_rates(spec, cells, condition)
    rows = [{"Body_ID": n["Body_ID"], "Root_Side": n["Root_Side"], "Type": n["Type"], "Subtype": "",
             "Target_Muscle": n["Target_Muscle"], "role": "MN_readout", "input_hz": 0} for n in spec["readout_neurons"]]
    annotations = {n["Body_ID"]: n for n in spec.get("source_neurons", spec["candidate_neurons"])}
    groups = source_groups(spec, cells)
    roots = sorted(set(groups["frozen_sugar23"]) | set(groups["candidate33"]) | set(groups["bitter42"]), key=int)
    for root in roots:
        source = annotations.get(root, {})
        rows.append({"Body_ID": root, "Root_Side": source.get("Root_Side", ""), "Type": source.get("Type", "frozen_source_set"),
                     "Subtype": source.get("Subtype", ""), "Target_Muscle": "", "role": "source_GRN", "input_hz": rates[f"r1_{root}"]})
    if len(rows) != 92 or len({n["Body_ID"] for n in rows}) != 92:
        raise ValueError("expected six MNs and86unique source GRNs")
    return rows


def result_identity(condition, identity):
    return {**identity, "condition_id": condition["cond_id"], "condition_index": condition["condition_index"],
            "seed_index": condition["seed_index"], "group_rates": condition["group_rates"],
            "seeds": [phase_r1_seed(condition["condition_index"], t) for t in range(N_TRIALS)]}


def _validate_trial_indices(trials, ids):
    if trials.shape != ids.shape or not np.issubdtype(trials.dtype, np.integer) or np.any((trials < 0) | (trials >= N_TRIALS)):
        raise ValueError("invalid raw trial indices")


def validate_result(saved, path, expected, spec, protocol, cells, condition):
    if saved.get("identity") != expected or saved.get("completed_trials") != list(range(N_TRIALS)):
        raise ValueError("stored result identity/completion mismatch")
    if saved.get("spikes_sha256") != sha256(path):
        raise ValueError("stored raw spike hash mismatch")
    descriptions = _individual_descriptions(spec, cells, condition)
    roots = [n["Body_ID"] for n in descriptions]
    sources = [n for n in descriptions if n["role"] == "source_GRN"]
    groups = groups_for(spec, protocol, condition, cells)
    with np.load(path, allow_pickle=False) as raw:
        fields = {"flywire_id", "t_ms", "trial", "seeds", "completed_trials", "saved_neuron_ids",
                  "poisson_target_id", "poisson_t_ms", "poisson_trial", "poisson_saved_target_ids"}
        if set(raw.files) != fields:
            raise ValueError("unexpected raw spike fields")
        ids, times, trials = raw["flywire_id"], raw["t_ms"], raw["trial"]
        validate_spikes(ids, times, 1000)
        _validate_trial_indices(trials, ids)
        for key, values in (("seeds", expected["seeds"]), ("completed_trials", list(range(N_TRIALS))),
                            ("saved_neuron_ids", [int(r) for r in roots]),
                            ("poisson_saved_target_ids", [int(n["Body_ID"]) for n in sources])):
            if not np.issubdtype(raw[key].dtype, np.integer) or not np.array_equal(raw[key], values):
                raise ValueError(f"invalid raw {key}")
        if not set(map(int, ids)).issubset(map(int, roots)):
            raise ValueError("raw spikes include unrequested neurons")
        poi_ids, poi_times, poi_trials = raw["poisson_target_id"], raw["poisson_t_ms"], raw["poisson_trial"]
        validate_spikes(poi_ids, poi_times, 1000)
        _validate_trial_indices(poi_trials, poi_ids)
        if not set(map(int, poi_ids)).issubset({int(n["Body_ID"]) for n in sources if n["input_hz"] > 0}):
            raise ValueError("Poisson events include unrequested or inactive source units")
        individual, grouped = [], []
        for trial in range(N_TRIALS):
            mask = trials == trial
            metrics = neuron_metrics(ids[mask], times[mask], roots, 1000)
            prefix = {"condition_id": condition["cond_id"], "condition_index": condition["condition_index"], "trial": trial, "seed": expected["seeds"][trial]}
            individual.extend({**prefix, **n, **metrics[n["Body_ID"]]} for n in descriptions)
            grouped.extend({**prefix, "readout": name, **aggregate_metrics([metrics[r] for r in members])}
                           for name, members in groups.items())
    if saved.get("individual") != individual or saved.get("grouped") != grouped:
        raise ValueError("saved metrics differ from raw spike reconstruction")
    return saved


def load_result(condition, spec, protocol, cells, out, identity):
    ledger, raw = out / f"{condition['cond_id']}.json", out / f"{condition['cond_id']}.npz"
    if not ledger.exists() or not raw.exists():
        raise ValueError(f"{condition['cond_id']}: incomplete output; refusing overwrite or silent inference")
    return validate_result(load_json(ledger), raw, result_identity(condition, identity), spec, protocol, cells, condition)


def _run_condition(condition, spec, protocol, cells, output_dir, identity):
    out, name = Path(output_dir), condition["cond_id"]
    ledger, raw_path = out / f"{name}.json", out / f"{name}.npz"
    if ledger.exists() or raw_path.exists():
        saved = load_result(condition, spec, protocol, cells, out, identity)
        print(f"reuse verified {name}: 30 trials", flush=True)
        return saved
    from brian2 import SpikeMonitor, ms
    from sim.network import build_network
    copied, mapping = make_stimulation(spec, cells)
    rates = effective_rates(spec, cells, condition)
    network = build_network(protocol, copied, mapping)
    source_monitor = SpikeMonitor(network.poisson, name="refreeze_poisson_monitor")
    network.net.add(source_monitor)
    network.net.store("init")
    expected = result_identity(condition, identity)
    descriptions = _individual_descriptions(spec, cells, condition)
    roots = [n["Body_ID"] for n in descriptions]
    source_roots = [n["Body_ID"] for n in descriptions if n["role"] == "source_GRN"]
    poi_to_root = np.array([network.i2flyid[int(i)] for i in network.target_indices], dtype=np.int64)
    groups = groups_for(spec, protocol, condition, cells)
    individual, grouped = [], []
    arrays = {key: [] for key in ("flywire_id", "t_ms", "trial", "poisson_target_id", "poisson_t_ms", "poisson_trial")}
    started = time.perf_counter()
    for trial, seed in enumerate(expected["seeds"]):
        spikes = network.run_trial(rates, seed, 1000)
        pieces = [(int(root), np.asarray(spikes.get(int(root), []), dtype=float) * 1000) for root in roots]
        ids = np.concatenate([np.full(len(times), root, dtype=np.int64) for root, times in pieces])
        times = np.concatenate([times for _, times in pieces])
        metrics = neuron_metrics(ids, times, roots, 1000)
        prefix = {"condition_id": name, "condition_index": condition["condition_index"], "trial": trial, "seed": seed}
        individual.extend({**prefix, **n, **metrics[n["Body_ID"]]} for n in descriptions)
        grouped.extend({**prefix, "readout": group, **aggregate_metrics([metrics[r] for r in members])}
                       for group, members in groups.items())
        arrays["flywire_id"].append(ids)
        arrays["t_ms"].append(times)
        arrays["trial"].append(np.full(len(times), trial, dtype=np.int64))
        source_ids = poi_to_root[np.asarray(source_monitor.i, dtype=np.int64)]
        source_times = np.asarray(source_monitor.t / ms, dtype=float)
        if not np.all(np.isin(source_ids, np.array(source_roots, dtype=np.int64))):
            raise ValueError("unexpected active Poisson unit outside recorded sources")
        arrays["poisson_target_id"].append(source_ids)
        arrays["poisson_t_ms"].append(source_times)
        arrays["poisson_trial"].append(np.full(len(source_times), trial, dtype=np.int64))
    np.savez_compressed(raw_path, **{k: np.concatenate(v) for k, v in arrays.items()},
                        seeds=np.array(expected["seeds"], dtype=np.int64), completed_trials=np.arange(N_TRIALS, dtype=np.int64),
                        saved_neuron_ids=np.array(roots, dtype=np.int64), poisson_saved_target_ids=np.array(source_roots, dtype=np.int64))
    saved = {"identity": expected, "completed_trials": list(range(N_TRIALS)), "spikes_sha256": sha256(raw_path),
             "individual": individual, "grouped": grouped, "elapsed_s": time.perf_counter() - started}
    validate_result(saved, raw_path, expected, spec, protocol, cells, condition)
    ledger.write_text(json.dumps(saved, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"complete {name}: 30/30 trials; 92 recorded neurons", flush=True)
    return saved


def _rates(values):
    vector = np.asarray(values, dtype=float)
    if vector.shape != (N_TRIALS,) or not np.all(np.isfinite(vector)) or np.any(vector < 0):
        raise ValueError("expected 30 finite nonnegative rates")
    return vector


def paired_statistics(old, new):
    old, new = _rates(old), _rates(new)
    delta = new - old
    denominator = float(np.mean(old))
    return {"ratio_of_means": float(np.mean(new)) / denominator if denominator > 0 else None,
            "delta_values_hz": delta.tolist(), "delta_mean_hz": float(delta.mean()), "delta_sd_hz": float(delta.std(ddof=0)),
            "increase_trials": int(np.sum(delta > 0)), "equal_trials": int(np.sum(delta == 0)), "decrease_trials": int(np.sum(delta < 0))}


def normalized_statistics(old, new, old200, new200):
    old, new, old200, new200 = map(_rates, (old, new, old200, new200))
    old_den, new_den = float(old200.mean()), float(new200.mean())
    result = {"old_200_mean_hz": old_den, "new_200_mean_hz": new_den, "old_normalized_mean": None,
              "old_normalized_sd": None, "new_normalized_mean": None, "new_normalized_sd": None,
              "delta_values": None, "delta_mean": None, "delta_sd": None, "exceeds_two_sd": None}
    old_scaled = old / old_den if old_den > 0 else None
    new_scaled = new / new_den if new_den > 0 else None
    for prefix, scaled in (("old", old_scaled), ("new", new_scaled)):
        if scaled is not None:
            result[f"{prefix}_normalized_mean"] = float(scaled.mean())
            result[f"{prefix}_normalized_sd"] = float(scaled.std(ddof=0))
    if old_scaled is not None and new_scaled is not None:
        delta = new_scaled - old_scaled
        result.update({"delta_values": delta.tolist(), "delta_mean": float(delta.mean()), "delta_sd": float(delta.std(ddof=0)),
                       "exceeds_two_sd": bool(abs(float(delta.mean())) > 2 * float(delta.std(ddof=0)))})
    return result


def phase0_gates(summaries):
    by_name = {c["cond_id"]: c for c in summaries}
    expected = {c["cond_id"] for c in select_conditions()}
    if len(summaries) != N_CONDITIONS or len(by_name) != N_CONDITIONS or set(by_name) != expected:
        raise ValueError("Phase0 requires complete canonical R1 coverage; no missing or duplicate conditions")
    for name, cell in by_name.items():
        for side in ("MN9_L", "MN9_R"):
            values = cell["readouts"][side]
            if values["n_trials"] != N_TRIALS:
                raise ValueError("Phase0 requires 30 complete trials per condition")
            if any(not np.isfinite(values[key]) or values[key] < 0 for key in ("rate_mean_hz", "rate_std_hz")):
                raise ValueError("Phase0 requires finite nonnegative statistics")
    a_names = [f"R1_A_new_{dose}" for dose in (25, 50, 100)] + ["R1_new_200"]
    b_names = ["R1_new_200"] + [f"R1_B_new200_bitter{dose}" for dose in (25, 50, 100, 200)]
    c_names = [f"R1_C_bitter{dose}" for dose in (25, 50, 100, 200)]
    def mean(name):
        return by_name[name]["readouts"]["MN9_L"]["rate_mean_hz"]
    baseline = by_name["R1_new_0"]["readouts"]["MN9_L"]
    d_mean, d_sd = baseline["rate_mean_hz"], baseline["rate_std_hz"]
    a, b, c = [mean(n) for n in a_names], [mean(n) for n in b_names], [mean(n) for n in c_names]
    gates = {"A": bool(all(right > left or (left == 0 and right == 0) for left, right in zip(a, a[1:])) and a[-1] > d_mean + 5 * d_sd + 5),
             "B": bool(all(right <= left for left, right in zip(b, b[1:])) and b[-1] < 0.5 * b[0]),
             "C": bool(all(value <= d_mean + 2 * d_sd + 1 for value in c)), "D": bool(baseline["n_trials"] >= N_TRIALS)}
    strict = {}
    for side in ("MN9_L", "MN9_R"):
        for label, names in (("C", c_names), ("D", ["R1_new_0"])):
            strict[f"{label}_all_zero_{side}"] = all(by_name[n]["readouts"][side]["rate_mean_hz"] == 0 and
                                                       by_name[n]["readouts"][side]["rate_std_hz"] == 0 for n in names)
    return {"gates": gates, "overall_pass": all(gates.values()), "strict_silence": strict,
            "A_doses_hz": [25, 50, 100, 200], "A_means_hz": a, "A200_minimum_exclusive_hz": d_mean + 5 * d_sd + 5,
            "B_doses_hz": [0, 25, 50, 100, 200], "B_means_hz": b, "B200_maximum_exclusive_hz": 0.5 * b[0],
            "C_doses_hz": [25, 50, 100, 200], "C_means_hz": c, "C_maximum_inclusive_hz": d_mean + 2 * d_sd + 1,
            "D_mean_hz": d_mean, "D_sd_hz": d_sd, "readout": "Frozen left MN9 only; strict additional C/D silence also reported for right."}


def validate_paired_inputs(results, out, spec, cells):
    conditions = select_conditions()
    if [r["identity"]["condition_id"] for r in results] != [c["cond_id"] for c in conditions]:
        raise ValueError("expected exactly22results in canonical order")
    raw_inputs = []
    for condition, result in zip(conditions, results):
        seeds = [phase_r1_seed(condition["condition_index"], trial) for trial in range(N_TRIALS)]
        path = Path(out) / f"{condition['cond_id']}.npz"
        if result["identity"]["seeds"] != seeds or sha256(path) != result["spikes_sha256"]:
            raise ValueError("paired result seeds/raw hash mismatch")
        with np.load(path, allow_pickle=False) as raw:
            for field, expected in (("seeds", seeds), ("completed_trials", list(range(N_TRIALS)))):
                if field not in raw.files or not np.issubdtype(raw[field].dtype, np.integer) or not np.array_equal(raw[field], expected):
                    raise ValueError("paired raw seeds/completion mismatch")
            ids, times, trials = raw["poisson_target_id"], raw["poisson_t_ms"], raw["poisson_trial"]
            validate_spikes(ids, times, 1000)
            _validate_trial_indices(trials, ids)
            active = {int(channel.removeprefix("r1_")) for channel, hz in effective_rates(spec, cells, condition).items() if hz > 0}
            if not set(map(int, ids)).issubset(active):
                raise ValueError("inactive source emitted Poisson events")
            raw_inputs.append((ids.copy(), times.copy(), trials.copy()))
    groups = source_groups(spec, cells)
    comparisons = [(dose_index, dose_index + 5, groups["shared12"]) for dose_index in range(5)]
    comparisons.append((8, 21, groups["LB3c20"]))
    for left, right, roots in comparisons:
        for root in roots:
            for trial in range(N_TRIALS):
                trains = []
                for index in (left, right):
                    ids, times, trials = raw_inputs[index]
                    trains.append(times[(ids == int(root)) & (trials == trial)])
                if not np.array_equal(trains[0], trains[1]):
                    raise ValueError("paired shared-root Poisson trains differ")
    return {"old_new_shared12_identical": True, "old_new_shared_neuron_trials": 1800,
            "old_new_active_shared_neuron_trials": 1440, "old_new_zero_drive_shared_neuron_trials": 360,
            "Aprime_shared20_identical": True, "Aprime_shared_neuron_trials": 600}


def write_summary(results, spec, protocol, cells, out):
    conditions = select_conditions()
    if [r["identity"]["condition_id"] for r in results] != [c["cond_id"] for c in conditions]:
        raise ValueError("expected exactly22complete results in canonical order")
    summaries, arrays = [], {}
    for condition, result in zip(conditions, results):
        name, readouts = condition["cond_id"], {}
        arrays[name] = {}
        for group in groups_for(spec, protocol, condition, cells):
            rows = sorted((r for r in result["grouped"] if r["readout"] == group), key=lambda r: r["trial"])
            if [r["trial"] for r in rows] != list(range(N_TRIALS)):
                raise ValueError("missing/duplicate readout trial")
            arrays[name][group] = [r["rate_hz"] for r in rows]
            readouts[group] = summarize_trials(arrays[name][group], [r["first_spike_ms"] for r in rows])
        summaries.append({**condition, "readouts": readouts})
    curves, normalized, paired_rows = [], [], []
    for dose in DOSES:
        for group in CORE_GROUPS:
            old, new = arrays[f"R1_old_{dose}"][group], arrays[f"R1_new_{dose}"][group]
            paired = paired_statistics(old, new)
            scaled = normalized_statistics(old, new, arrays["R1_old_200"][group], arrays["R1_new_200"][group])
            scaled["interior_shape_flag"] = scaled["exceeds_two_sd"] if dose in (60, 80, 120) else None
            curves.append({"sugar_hz": dose, "readout": group, **paired})
            normalized.append({"sugar_hz": dose, "readout": group, **scaled})
            for trial in range(N_TRIALS):
                paired_rows.append({"sugar_hz": dose, "readout": group, "trial": trial,
                                    "seed": phase_r1_seed(DOSES.index(dose), trial), "old_hz": old[trial], "new_hz": new[trial],
                                    "delta_hz": paired["delta_values_hz"][trial],
                                    "normalized_delta": None if scaled["delta_values"] is None else scaled["delta_values"][trial]})
    aprime = {g: paired_statistics(arrays["R1_new_120"][g], arrays["R1_Aprime_LB3c20_120"][g]) for g in CORE_GROUPS}
    summary = {"schema_version": "refreeze_sugar_r1_v1", "n_conditions": 22, "n_trials_per_condition": N_TRIALS,
               "n_trials": 660, "n_unique_seeds": 480, "n_mn_readouts": 6, "n_monitored_source_grns": 86,
               "n_poisson_units": 165, "std_ddof": 0, "source_groups": source_groups(spec, cells),
               "conditions": summaries, "old_new_paired": curves, "normalized_curves": normalized,
               "Aprime_subset_minus_candidate": aprime, "phase0": phase0_gates(summaries),
               "paired_input_audit": validate_paired_inputs(results, out, spec, cells),
               "analysis_definitions": spec["analysis"]}
    write_csv(out / "individual_trials.csv", [r for result in results for r in result["individual"]])
    write_csv(out / "group_trials.csv", [r for result in results for r in result["grouped"]])
    write_csv(out / "paired_curve_trials.csv", paired_rows)
    write_csv(out / "readout_summary.csv", [{"condition_id": c["cond_id"], "readout": g, **v} for c in summaries for g, v in c["readouts"].items()])
    write_csv(out / "normalized_curves.csv", [{k: v for k, v in r.items() if k != "delta_values"} for r in normalized])
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = []
    for metric in ("rate", "latency"):
        for title, groups in (("MN", CORE_GROUPS), ("Source sanity", SOURCE_GROUPS + ("actual_driven_union",))):
            units = "mean ± population SD, Hz; n=30" if metric == "rate" else "median ms; active trials /30"
            lines += [f"### R1 {title} {metric} ({units})", "", "| Condition | " + " | ".join(groups) + " |", "|---|" + "---:|" * len(groups)]
            for cell in summaries:
                entries = []
                for group in groups:
                    value = cell["readouts"].get(group)
                    if value is None:
                        entries.append("not driven")
                    elif metric == "rate":
                        entries.append(f"{value['rate_mean_hz']:.3f} ± {value['rate_std_hz']:.3f}")
                    else:
                        median = "none" if value["latency_median_ms"] is None else f"{value['latency_median_ms']:.2f}"
                        entries.append(f"{median} ({value['active_trials']}/30)")
                lines.append(f"| {cell['cond_id']} | " + " | ".join(entries) + " |")
            lines.append("")
    lines += ["### Paired old/new sugar curves", "", "| Sugar Hz | Readout | New/old ratio of means | New-minus-old Hz ± SD |", "|---:|---|---:|---:|"]
    for row in curves:
        ratio = "undefined" if row["ratio_of_means"] is None else f"{row['ratio_of_means']:.6f}"
        lines.append(f"| {row['sugar_hz']} | {row['readout']} | {ratio} | {row['delta_mean_hz']:.3f} ± {row['delta_sd_hz']:.3f} |")
    lines += ["", "### Curves divided by their own mean at200Hz", "", "| Sugar Hz | Readout | Old normalized mean ± SD | New normalized mean ± SD | Paired normalized delta ± SD | Interior shape flag |", "|---:|---|---:|---:|---:|---|"]
    for row in normalized:
        entries = []
        for mean_key, sd_key in (("old_normalized_mean", "old_normalized_sd"), ("new_normalized_mean", "new_normalized_sd"), ("delta_mean", "delta_sd")):
            entries.append("undefined" if row[mean_key] is None else f"{row[mean_key]:.6f} ± {row[sd_key]:.6f}")
        flag = "not tested" if row["interior_shape_flag"] is None else str(row["interior_shape_flag"])
        lines.append(f"| {row['sugar_hz']} | {row['readout']} | " + " | ".join(entries) + f" | {flag} |")
    lines += ["", spec["analysis"]["normalization"], "", spec["analysis"]["shape_flag"], "", spec["analysis"]["size_caveat"], "",
              "### A-prime at120Hz: LB3c20 minus candidate33, paired", "", "| Readout | Subset/candidate ratio of means | Paired difference mean ± SD Hz | Increase/equal/decrease |", "|---|---:|---:|---:|"]
    for group, row in aprime.items():
        ratio = "undefined" if row["ratio_of_means"] is None else f"{row['ratio_of_means']:.6f}"
        lines.append(f"| {group} | {ratio} | {row['delta_mean_hz']:.3f} ± {row['delta_sd_hz']:.3f} | {row['increase_trials']}/{row['equal_trials']}/{row['decrease_trials']} |")
    lines += ["", "### Original Phase0 hard gates", "", "| Gate | Result |", "|---|---|"]
    for gate, passed in summary["phase0"]["gates"].items():
        lines.append(f"| {gate} | {'PASS' if passed else 'FAIL'} |")
    for label, passed in summary["phase0"]["strict_silence"].items():
        lines.append(f"| Additional {label} | {passed} |")
    lines += ["", spec["analysis"]["phase0"], ""]
    (out / "tables.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def source_files(spec, protocol):
    return p1.source_files(spec, protocol) + [SPEC, Path(__file__).resolve(), ROOT / "scripts/phase0_report.py"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-proc", type=int, default=13)
    parser.add_argument("--out", type=Path, default=ROOT / "results/refreeze/sugar_r1")
    parser.add_argument("--check-design", action="store_true")
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.n_proc <= 32:
        parser.error("n-proc must be1..32")
    if args.check_design and args.summarize_only:
        parser.error("choose one no-simulation mode")
    out = args.out.resolve()
    if out != (ROOT / "results/refreeze/sugar_r1").resolve():
        parser.error("output must be exactly results/refreeze/sugar_r1/")
    spec, protocol, cells = load_design()
    if args.check_design:
        print("design valid:22conditions x30=660trials;165unique physical roots;6MNs+86sourceGRNs;pairedold/new andAprime inputs;no simulation")
        return
    files = source_files(spec, protocol)
    hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in files}
    if args.summarize_only:
        meta = load_json(out / "run_meta.json")
        identity = meta["identity"]
        if identity["source_sha256"] != hashes or meta["n_trials_completed"] != 660 or meta["status"] != "complete":
            raise ValueError("run provenance differs from current sources or complete design")
        results = [load_result(c, spec, protocol, cells, out, identity) for c in select_conditions()]
        write_summary(results, spec, protocol, cells, out)
        print("summary valid:660complete trials;allmetrics reconstructed and pairedinputs matched;no simulation")
        return
    if platform.system() != "Linux" or "microsoft" not in platform.release().lower():
        raise RuntimeError("Brian2 runs only in the configured WSL2 flybrain environment")
    import brian2
    import Cython
    import joblib
    from joblib import Parallel, delayed
    if brian2.__version__ != "2.9.0":
        raise RuntimeError("R1 requires Brian2 2.9.0")
    _, mapping = make_stimulation(spec, cells)
    identity = {"source_sha256": hashes, "seed_scheme": "published_grid_v1_batch40", "phase": "R1",
                "condition_index_scope": "22new conditions, paired seedindices0..4 and3, eleven additional seedindices5..15;notlookupgrid identities",
                "brian2_version": brian2.__version__, "duration_ms": 1000, "channels": list(mapping),
                "effective_rates_by_condition": {c["cond_id"]: effective_rates(spec, cells, c) for c in select_conditions()},
                "python_version": platform.python_version(), "numpy_version": np.__version__, "joblib_version": joblib.__version__,
                "cython_version": Cython.__version__, "brian2_codegen_backend": "cython", "n_poisson_units": 165, "poisson_inputs_recorded": True}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    print("R1:22conditions x30=660trials;165singleton physical channels;frozenmodel unchanged", flush=True)
    results = Parallel(n_jobs=min(N_CONDITIONS, args.n_proc), backend="loky")(
        delayed(_run_condition)(c, spec, protocol, cells, out, identity) for c in select_conditions())
    if any(sha256(p) != hashes[p.relative_to(ROOT).as_posix()] for p in files):
        raise ValueError("source changed during the run")
    summary = write_summary(results, spec, protocol, cells, out)
    meta = {"identity": identity, "git_commit": commit, "status": "complete", "n_conditions": 22,
            "n_trials_completed": 660, "n_proc": min(N_CONDITIONS, args.n_proc),
            "completed_at": datetime.now(timezone.utc).isoformat(), "elapsed_s": time.perf_counter() - started}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"R1complete:660/660trials;{meta['elapsed_s']:.1f}s;originalPhase0overall={summary['phase0']['overall_pass']}", flush=True)


if __name__ == "__main__":
    main()
