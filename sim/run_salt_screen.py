# SPDX-License-Identifier: MIT
"""S1: six source-bound salt-input conditions, ten trials each; research only.

python -B -m sim.run_salt_screen --check-design
WSL2 only: python -B -m sim.run_salt_screen --n-proc 13
All physical stimulation roots occur once. No frozen/model/P1/P2 file changes.
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
SPEC = ROOT / "data/stim_protocol_salt.json"
N_TRIALS = 10
N_CONDITIONS = 6
CORE_GROUPS = ("MN9_L", "MN9_R", "MN11D", "MN11V")
SOURCE_GROUPS = ("LB3b25", "LB3d29", "LB3d22", "overlap7", "frozen_sugar23")
DRIVE_GROUPS = ("LB3b25", "LB3d29", "LB3d22", "frozen_sugar23")
SEED_INDICES = (0, 1, 2, 2, 3, 3)


def phase_s1_seed(condition_index, trial, base_seed=20260910):
    for value, upper, name in ((condition_index, N_CONDITIONS, "condition_index"), (trial, N_TRIALS, "trial")):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not 0 <= value < upper:
            raise ValueError(f"invalid {name}")
    return published_grid_seed(SEED_INDICES[condition_index], trial, base_seed)


def select_conditions():
    definitions = (("S1_baseline", (0, 0, 0, 0)), ("S1_LB3b_25", (100, 0, 0, 0)),
                   ("S1_LB3d_29", (0, 100, 0, 0)), ("S1_LB3d_22", (0, 0, 100, 0)),
                   ("S1_sugar_120", (0, 0, 0, 120)), ("S1_sugar_120_LB3d_22", (0, 0, 100, 120)))
    return [{"cond_id": name, "condition_index": index, "seed_index": SEED_INDICES[index],
             "group_rates": dict(zip(DRIVE_GROUPS, rates))} for index, (name, rates) in enumerate(definitions)]


def salt_source_rows(rows, v783):
    """Only exact Table S1 FlyWire LB3b/LB3d source annotations, without inference."""
    selected = []
    seen = set()
    for row in rows:
        if row.get("Connectome") != FLYWIRE or row.get("Subtype") not in {"LB3b", "LB3d"}:
            continue
        root = exact_id(row.get("Body_ID"))
        if root in seen or row.get("Root_Side") not in {"L", "R"} or row.get("Type") != "LB3":
            raise ValueError("unexpected or duplicate salt source annotation")
        seen.add(root)
        fields = ("Body_ID", "Root_Side", "Type", "Subtype", "Entry_Nerve")
        selected.append({**{k: row.get(k, "") for k in fields}, "in_v783": str(root) in v783})
    for kind, count in (("LB3b", 25), ("LB3d", 29)):
        subset = [n for n in selected if n["Subtype"] == kind]
        if len(subset) != count or {n["Root_Side"] for n in subset} != {"L", "R"}:
            raise ValueError(f"expected all {count} FlyWire {kind} cells on both sides")
    if not all(n["in_v783"] for n in selected):
        raise ValueError("salt source neuron absent from v783")
    return selected


def source_groups(spec, cells):
    rows = spec["salt_neurons"]
    ids = [exact_id(n["Body_ID"]) for n in rows]
    if len(ids) != 54 or len(set(ids)) != 54 or not all(isinstance(n["Body_ID"], str) and n.get("in_v783") is True for n in rows):
        raise ValueError("expected 54 distinct exact source IDs in v783")
    if any(n.get("Type") != "LB3" or n.get("Subtype") not in {"LB3b", "LB3d"} for n in rows):
        raise ValueError("salt sources must preserve XLSX Type and Subtype")
    lb3b = [n["Body_ID"] for n in rows if n["Subtype"] == "LB3b"]
    lb3d = [n["Body_ID"] for n in rows if n["Subtype"] == "LB3d"]
    sugar = [str(exact_id(i)) for i in cells["sets"]["sugar"]["ids"]]
    overlap = [r for r in lb3d if r in set(sugar)]
    outside = [r for r in lb3d if r not in set(sugar)]
    result = dict(zip(SOURCE_GROUPS, (lb3b, lb3d, outside, overlap, sugar)))
    if [len(result[k]) for k in SOURCE_GROUPS] != [25, 29, 22, 7, 23] or len(set(sugar)) != 23:
        raise ValueError("source group counts differ from the confirmed overlap design")
    if len(set(lb3b) & set(sugar)) != 1 or set(lb3b) & set(lb3d):
        raise ValueError("source overlaps differ from the confirmed design")
    if len(set(lb3b) | set(lb3d) | set(sugar)) != 69:
        raise ValueError("expected 69 monitored source GRNs")
    return result


def make_stimulation(spec, cells):
    """197 singleton channels prevent duplicate Poisson units and refractory writes."""
    expanded, original_mapping = p1.make_stimulation(spec, cells)
    original = [str(exact_id(i)) for name in original_mapping.values() for i in expanded["sets"][name]["ids"]]
    groups = source_groups(spec, cells)
    extra = sorted((set(groups["LB3b25"]) | set(groups["LB3d29"])) - set(original), key=int)
    roots = original + extra
    if len(original) != 151 or len(roots) != 197 or len(set(roots)) != 197:
        raise ValueError("expected the original 151 roots followed by 46 distinct added salt roots")
    copied, mapping = deepcopy(cells), {}
    for root in roots:
        channel = f"s1_{root}"
        if channel in copied["sets"]:
            raise ValueError("research singleton would overwrite an existing set")
        copied["sets"][channel] = {"ids": [root]}
        mapping[channel] = channel
    return copied, mapping


def effective_rates(spec, cells, condition):
    _, mapping = make_stimulation(spec, cells)
    groups = source_groups(spec, cells)
    requested = condition["group_rates"]
    if tuple(requested) != DRIVE_GROUPS:
        raise ValueError("unexpected logical drive groups or order")
    rates = dict.fromkeys(mapping, 0)
    assigned = set()
    for group, hz in requested.items():
        if isinstance(hz, (bool, np.bool_)) or not isinstance(hz, (int, float, np.number)) or not np.isfinite(hz) or hz < 0:
            raise ValueError("drive rates must be finite and nonnegative")
        if hz == 0:
            continue
        for root in groups[group]:
            if root in assigned:
                raise ValueError("active logical groups overlap; additive or last-write drive is forbidden")
            assigned.add(root)
            rates[f"s1_{root}"] = hz
    return rates


def groups_for(spec, protocol, condition, cells):
    readouts = spec["readout_neurons"]
    result = {"MN9_L": [str(protocol["readout"]["left"])], "MN9_R": [str(protocol["readout"]["right"])]}
    for kind in ("MN11D", "MN11V"):
        result[kind] = [n["Body_ID"] for n in readouts if n["Type"] == kind]
    if [len(result[k]) for k in CORE_GROUPS] != [1, 1, 2, 2]:
        raise ValueError("expected six MN readout neurons")
    if set(r for roots in result.values() for r in roots) != {n["Body_ID"] for n in readouts}:
        raise ValueError("MN groups do not match selected six readouts")
    result.update(source_groups(spec, cells))
    rates = effective_rates(spec, cells, condition)
    driven = [channel.removeprefix("s1_") for channel, hz in rates.items() if hz > 0]
    if driven:
        result["actual_driven_union"] = driven
    return result


def build_spec():
    """Source extraction for the new JSON; this function does not write files."""
    prior, protocol, cells = p1.load_design()
    source = prior["pharyngeal_source"]
    v783 = read_v783_ids(ROOT / protocol["completeness_file"])
    rows = salt_source_rows(read_xlsx(ROOT / source["file"])["GRNs"], v783)
    return {"schema_version": "salt_screen_s1_v1", "base_protocol": prior["base_protocol"],
            "base_protocol_sha256": prior["base_protocol_sha256"], "p1_protocol": "data/stim_protocol_pharyngeal.json",
            "p1_protocol_sha256": sha256(p1.SPEC), "frozen_cells_sha256": prior["frozen_cells_sha256"],
            "salt_source": {**source, "selection": "Connectome is FAFB - Flywire (exact workbook en dash); Type=LB3, Subtype=LB3b or LB3d; all rows, both Root_Side values."},
            "salt_neurons": rows, "readout_neurons": [n for n in prior["readout_neurons"] if n["Type"] != "CEM"],
            "n_poisson_units": 197, "layout": "Preserve the original 151 P1 physical-root order, append missing LB3b/LB3d IDs numerically sorted. One singleton channel per physical root; each root receives one Poisson unit and one effective-rate/refractory assignment.",
            "overlap_rule": "In combination, all frozen sugar23 remain at120 Hz, including seven LB3d overlap cells. Only the other LB3d22 receive100 Hz. No added drive on the overlap7; no frozen set is altered.",
            "trial": {"n_trials": N_TRIALS, "base_seed": 20260910, "seed_scheme": "published_grid_v1_batch40",
                      "seed_rule": "20260910+1000*(seed_index%40)+trial, trial0..9. Conditionindices0..5 use seedindices0,1,2,2,3,3; explicit new research conditions, not original-grid or replay trials."},
            "conditions": select_conditions(), "analysis": {"rate": "Spike count / full1second. MN9L/R individually; MN11D/V two-cell means including silence; all69sourceGRNs individually, grouped into25/29/22/overlap7/frozensugar23 and actual driven union.",
            "std": "Population SD across10trials, ddof=0.", "latency": "First-spike median among active trials with active counts; group first spike is earliest member.",
            "paired": "Exact same Poisson events for shared LB3d22 between29/22, and sugar23 alone/combination; verify raw inputs. Report combo/sugar ratio of means and mean+SD of trial-wise ratios (undefined overall if any sugar denominator zero), plus paired differences."},
            "results": "results/salt/s1/ (local/gitignored; no lookup/product changes)"}


def load_design():
    extra = load_json(SPEC)
    if extra != build_spec():
        raise ValueError("salt protocol differs from verified source rows or the authorised S1 design")
    prior, protocol, cells = p1.load_design()
    spec = {**prior, **extra}
    for condition in select_conditions():
        groups_for(spec, protocol, condition, cells)
    return spec, protocol, cells


def _individual_descriptions(spec, cells, condition):
    rates = effective_rates(spec, cells, condition)
    rows = [{"Body_ID": n["Body_ID"], "Root_Side": n["Root_Side"], "Type": n["Type"],
             "Subtype": "", "Target_Muscle": n["Target_Muscle"], "role": "MN_readout", "input_hz": 0}
            for n in spec["readout_neurons"]]
    sources = {n["Body_ID"]: n for n in spec["salt_neurons"]}
    groups = source_groups(spec, cells)
    roots = sorted(set(groups["LB3b25"]) | set(groups["LB3d29"]) | set(groups["frozen_sugar23"]), key=int)
    for root in roots:
        annotation = sources.get(root, {})
        rows.append({"Body_ID": root, "Root_Side": annotation.get("Root_Side", ""),
                     "Type": annotation.get("Type", "frozen_sugar_set"), "Subtype": annotation.get("Subtype", ""),
                     "Target_Muscle": "", "role": "source_GRN", "input_hz": rates[f"s1_{root}"]})
    if len(rows) != 75 or len({n["Body_ID"] for n in rows}) != 75:
        raise ValueError("expected six MNs and69unique source GRNs")
    return rows


def result_identity(condition, identity):
    return {**identity, "condition_id": condition["cond_id"], "condition_index": condition["condition_index"],
            "seed_index": condition["seed_index"], "group_rates": condition["group_rates"],
            "seeds": [phase_s1_seed(condition["condition_index"], t) for t in range(N_TRIALS)]}


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
            prefix = {"condition_id": condition["cond_id"], "condition_index": condition["condition_index"],
                      "trial": trial, "seed": expected["seeds"][trial]}
            individual.extend({**prefix, **n, **metrics[n["Body_ID"]]} for n in descriptions)
            grouped.extend({**prefix, "readout": name, **aggregate_metrics([metrics[r] for r in members])}
                           for name, members in groups.items())
    if saved.get("individual") != individual or saved.get("grouped") != grouped:
        raise ValueError("saved metrics differ from raw spike reconstruction")
    return saved


def load_result(condition, spec, protocol, cells, out, identity):
    ledger, raw = out / f"{condition['cond_id']}.json", out / f"{condition['cond_id']}.npz"
    if not ledger.exists() or not raw.exists():
        raise ValueError(f"{condition['cond_id']}: incomplete output; refusing to overwrite or infer silence")
    return validate_result(load_json(ledger), raw, result_identity(condition, identity), spec, protocol, cells, condition)


def _run_condition(condition, spec, protocol, cells, output_dir, identity):
    out, name = Path(output_dir), condition["cond_id"]
    ledger, raw_path = out / f"{name}.json", out / f"{name}.npz"
    if ledger.exists() or raw_path.exists():
        saved = load_result(condition, spec, protocol, cells, out, identity)
        print(f"reuse verified {name}:10trials", flush=True)
        return saved
    from brian2 import SpikeMonitor, ms
    from sim.network import build_network
    copied, mapping = make_stimulation(spec, cells)
    rates = effective_rates(spec, cells, condition)
    network = build_network(protocol, copied, mapping)
    source_monitor = SpikeMonitor(network.poisson, name="salt_poisson_monitor")
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
        selected = np.isin(source_ids, np.array(source_roots, dtype=np.int64))
        if not np.all(selected):
            raise ValueError("unexpected active Poisson unit outside all69recorded sources")
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
    print(f"complete {name}:10/10trials;75recorded neurons", flush=True)
    return saved


def paired_statistics(base, combo):
    base, combo = np.asarray(base, dtype=float), np.asarray(combo, dtype=float)
    if any(v.shape != (N_TRIALS,) or not np.all(np.isfinite(v)) or np.any(v < 0) for v in (base, combo)):
        raise ValueError("paired vectors must each contain10finite nonnegative rates")
    defined = base > 0
    ratios = [float(c / b) if b > 0 else None for b, c in zip(base, combo)]
    delta = combo - base
    mean_base = float(np.mean(base))
    return {"ratio_of_means": float(np.mean(combo)) / mean_base if mean_base > 0 else None,
            "ratio_mean": float(np.mean(ratios)) if np.all(defined) else None,
            "ratio_sd": float(np.std(ratios, ddof=0)) if np.all(defined) else None,
            "ratio_defined_trials": int(defined.sum()), "ratio_total_trials": N_TRIALS,
            "ratio_values": ratios, "delta_values_hz": delta.tolist(), "delta_mean_hz": float(np.mean(delta)),
            "delta_sd_hz": float(np.std(delta, ddof=0)), "increase_trials": int(np.sum(delta > 0)),
            "equal_trials": int(np.sum(delta == 0)), "decrease_trials": int(np.sum(delta < 0))}


def validate_paired_inputs(results, out, spec, cells):
    names = [c["cond_id"] for c in select_conditions()]
    if [r["identity"]["condition_id"] for r in results] != names:
        raise ValueError("expected exactly six results in canonical order")
    sources = source_groups(spec, cells)
    data = []
    for index, result in enumerate(results):
        expected = [phase_s1_seed(index, t) for t in range(N_TRIALS)]
        if result["identity"]["seeds"] != expected:
            raise ValueError("declared paired seeds differ")
        path = Path(out) / f"{names[index]}.npz"
        if sha256(path) != result["spikes_sha256"]:
            raise ValueError("paired raw spike hash mismatch")
        with np.load(path, allow_pickle=False) as raw:
            for field, values in (("seeds", expected), ("completed_trials", list(range(N_TRIALS)))):
                if field not in raw.files or not np.issubdtype(raw[field].dtype, np.integer) or not np.array_equal(raw[field], values):
                    raise ValueError("paired raw seeds/completion mismatch")
            ids, times, trials = raw["poisson_target_id"], raw["poisson_t_ms"], raw["poisson_trial"]
            validate_spikes(ids, times, 1000)
            _validate_trial_indices(trials, ids)
            active = {int(k.removeprefix("s1_")) for k, hz in effective_rates(spec, cells, select_conditions()[index]).items() if hz > 0}
            if not set(map(int, ids)).issubset(active):
                raise ValueError("inactive source emitted Poisson events")
            data.append((ids.copy(), times.copy(), trials.copy()))
    for group, left, right in (("LB3d22", 2, 3), ("frozen_sugar23", 4, 5)):
        for root in sources[group]:
            for trial in range(N_TRIALS):
                trains = []
                for index in (left, right):
                    ids, times, trials = data[index]
                    trains.append(times[(ids == int(root)) & (trials == trial)])
                if not np.array_equal(trains[0], trains[1]):
                    raise ValueError(f"shared {group} Poisson input trains differ")
    return {"LB3d22_29_vs22_identical": True, "sugar23_alone_vs_combo_identical": True,
            "LB3d22_neuron_trials": 220, "sugar23_neuron_trials": 230}


def write_summary(results, spec, protocol, cells, out):
    conditions = select_conditions()
    if [r["identity"]["condition_id"] for r in results] != [c["cond_id"] for c in conditions]:
        raise ValueError("expected exactly six complete results in canonical order")
    summaries = []
    for condition, result in zip(conditions, results):
        readouts = {}
        for group in groups_for(spec, protocol, condition, cells):
            rows = sorted((r for r in result["grouped"] if r["readout"] == group), key=lambda r: r["trial"])
            if [r["trial"] for r in rows] != list(range(N_TRIALS)):
                raise ValueError("missing/duplicate readout trial")
            readouts[group] = summarize_trials([r["rate_hz"] for r in rows], [r["first_spike_ms"] for r in rows])
        summaries.append({**condition, "readouts": readouts})
    paired, trial_rows = {}, []
    for group in CORE_GROUPS + SOURCE_GROUPS:
        rates = [[r["rate_hz"] for r in sorted(result["grouped"], key=lambda r: r["trial"]) if r["readout"] == group]
                 for result in results[-2:]]
        stats = paired_statistics(*rates)
        paired[group] = stats
        for trial in range(N_TRIALS):
            trial_rows.append({"readout": group, "trial": trial, "seed": phase_s1_seed(4, trial),
                               "sugar_hz": rates[0][trial], "combination_hz": rates[1][trial],
                               "ratio": stats["ratio_values"][trial], "delta_hz": stats["delta_values_hz"][trial]})
    summary = {"schema_version": "salt_screen_s1_v1", "n_conditions": 6, "n_trials_per_condition": 10,
               "n_trials": 60, "n_mn_readouts": 6, "n_monitored_source_grns": 69, "n_poisson_units": 197,
               "std_ddof": 0, "source_groups": source_groups(spec, cells), "conditions": summaries,
               "paired_combo_vs_sugar": paired, "paired_input_audit": validate_paired_inputs(results, out, spec, cells)}
    write_csv(out / "individual_trials.csv", [r for result in results for r in result["individual"]])
    write_csv(out / "group_trials.csv", [r for result in results for r in result["grouped"]])
    write_csv(out / "paired_trials.csv", trial_rows)
    write_csv(out / "readout_summary.csv", [{"condition_id": c["cond_id"], "readout": g, **v} for c in summaries for g, v in c["readouts"].items()])
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = []
    for metric in ("rate", "latency"):
        for title, groups in (("MN", CORE_GROUPS), ("Source GRN sanity", SOURCE_GROUPS + ("actual_driven_union",))):
            units = "mean ± population SD, Hz; n = 10" if metric == "rate" else "median ms; active trials / 10"
            lines += [f"### S1 {title} {metric} ({units})", "", "| Condition | " + " | ".join(groups) + " |",
                      "|---|" + "---:|" * len(groups)]
            for c in summaries:
                values = []
                for group in groups:
                    value = c["readouts"].get(group)
                    if value is None:
                        values.append("not driven")
                    elif metric == "rate":
                        values.append(f"{value['rate_mean_hz']:.3f} ± {value['rate_std_hz']:.3f}")
                    else:
                        median = "none" if value["latency_median_ms"] is None else f"{value['latency_median_ms']:.2f}"
                        values.append(f"{median} ({value['active_trials']}/10)")
                lines.append(f"| {c['cond_id']} | " + " | ".join(values) + " |")
            lines.append("")
    lines += ["### Combination versus sugar alone", "", "| Readout | Ratio of means | Paired trial ratio mean ± SD | Paired difference Hz ± SD | Increase/equal/decrease trials |",
              "|---|---:|---:|---:|---:|"]
    for group in CORE_GROUPS:
        value = paired[group]
        mean_ratio = "undefined" if value["ratio_of_means"] is None else f"{value['ratio_of_means']:.6f}"
        trial_ratio = f"undefined ({value['ratio_defined_trials']}/10 defined)" if value["ratio_mean"] is None else f"{value['ratio_mean']:.6f} ± {value['ratio_sd']:.6f}"
        lines.append(f"| {group} | {mean_ratio} | {trial_ratio} | {value['delta_mean_hz']:.3f} ± {value['delta_sd_hz']:.3f} | {value['increase_trials']}/{value['equal_trials']}/{value['decrease_trials']} |")
    lines += ["", "Shared active source Poisson trains match exactly: LB3d22 in29/22 conditions, and sugar23 alone/in combination.", ""]
    (out / "tables.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def source_files(spec, protocol):
    return p1.source_files(spec, protocol) + [SPEC, Path(__file__).resolve()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-proc", type=int, default=13)
    parser.add_argument("--out", type=Path, default=ROOT / "results/salt/s1")
    parser.add_argument("--check-design", action="store_true")
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.n_proc <= 32:
        parser.error("n-proc must be1..32")
    if args.check_design and args.summarize_only:
        parser.error("choose one no-simulation mode")
    out = args.out.resolve()
    if out != (ROOT / "results/salt/s1").resolve():
        parser.error("output must be exactly results/salt/s1/")
    spec, protocol, cells = load_design()
    if args.check_design:
        print("design valid:6conditions x10=60trials;197unique physical stimulation roots;6MNs+69sourceGRNs;matched22subset/sugarinput pairs;no simulation")
        return
    files = source_files(spec, protocol)
    hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in files}
    if args.summarize_only:
        meta = load_json(out / "run_meta.json")
        identity = meta["identity"]
        if identity["source_sha256"] != hashes or meta["n_trials_completed"] != 60 or meta["status"] != "complete":
            raise ValueError("run provenance does not match current sources or complete design")
        results = [load_result(c, spec, protocol, cells, out, identity) for c in select_conditions()]
        write_summary(results, spec, protocol, cells, out)
        print("summary valid:60complete trials;allmetrics reconstructed and pairedinput events matched;no simulation")
        return
    if platform.system() != "Linux" or "microsoft" not in platform.release().lower():
        raise RuntimeError("Brian2 runs only in the configured WSL2 flybrain environment")
    import brian2
    import Cython
    import joblib
    from joblib import Parallel, delayed
    if brian2.__version__ != "2.9.0":
        raise RuntimeError("S1 requires Brian2 2.9.0")
    _, mapping = make_stimulation(spec, cells)
    identity = {"source_sha256": hashes, "seed_scheme": "published_grid_v1_batch40", "phase": "S1",
                "condition_index_scope": "New indices0..5;seedindices0,1,2,2,3,3;not lookup-grid identities",
                "brian2_version": brian2.__version__, "duration_ms": 1000, "channels": list(mapping),
                "effective_rates_by_condition": {c["cond_id"]: effective_rates(spec, cells, c) for c in select_conditions()},
                "python_version": platform.python_version(), "numpy_version": np.__version__,
                "joblib_version": joblib.__version__, "cython_version": Cython.__version__,
                "brian2_codegen_backend": "cython", "n_poisson_units": 197, "poisson_inputs_recorded": True}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    print("S1:6conditions x10=60trials;197singleton physical channels;frozenmodel unchanged", flush=True)
    results = Parallel(n_jobs=min(N_CONDITIONS, args.n_proc), backend="loky")(
        delayed(_run_condition)(c, spec, protocol, cells, out, identity) for c in select_conditions())
    if any(sha256(p) != hashes[p.relative_to(ROOT).as_posix()] for p in files):
        raise ValueError("source changed during the run")
    write_summary(results, spec, protocol, cells, out)
    meta = {"identity": identity, "git_commit": commit, "status": "complete", "n_conditions": 6,
            "n_trials_completed": 60, "n_proc": min(N_CONDITIONS, args.n_proc),
            "completed_at": datetime.now(timezone.utc).isoformat(), "elapsed_s": time.perf_counter() - started}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"S1complete:60/60trials;{meta['elapsed_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
