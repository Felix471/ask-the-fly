# SPDX-License-Identifier: MIT
"""Phase P2: separate 30-trial dose curves and a matched-layout combination.

Read-only validation: python -B -m sim.run_pharyngeal_p2 --check-design
WSL2 flybrain only: python -B -m sim.run_pharyngeal_p2 --n-proc 13
P1 and all frozen/model sources remain unchanged. No C2/P1 trials are reused.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np

from sim import run_pharyngeal as p1
from sim.run_mn_readouts import load_json, published_grid_seed, sha256, summarize_trials, write_csv
from scripts.mn_readouts_from_replays import aggregate_metrics, neuron_metrics, validate_spikes

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data/stim_protocol_pharyngeal_p2.json"
CHANNELS = p1.CHANNELS
make_stimulation = p1.make_stimulation
CORE_GROUPS = p1.CORE_GROUPS
CEM_GROUPS = p1.CEM_GROUPS
N_TRIALS = 30
DOSES = (0, 60, 80, 120, 200)
PAIR_IDS = ("P2_pair_a_sugar", "P2_pair_b_PhG1", "P2_pair_c_both")


def phase_p2_seed(condition_index, trial, base_seed=20260910):
    for value, upper, name in ((condition_index, 13, "condition_index"), (trial, N_TRIALS, "trial")):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not 0 <= value < upper:
            raise ValueError(f"invalid {name}")
    return published_grid_seed(min(condition_index, 10), trial, base_seed)


def select_conditions():
    result = []
    for kind in ("PhG1", "PhG4"):
        for hz in DOSES:
            index = len(result)
            result.append({"cond_id": f"P2_{kind}_{hz}", "condition_index": index,
                           "seed_index": index, "phase": f"{kind}_dose",
                           "rates": {c: hz if c == kind else 0 for c in CHANNELS},
                           "monitored_types": [kind], "driven_types": [kind] if hz else [],
                           "monitor_sugar": False})
    for name, sugar, phg in zip(PAIR_IDS, (120, 0, 120), (0, 100, 100)):
        result.append({"cond_id": name, "condition_index": len(result), "seed_index": 10,
                       "phase": "paired", "rates": {c: sugar if c == "sugar" else phg if c == "PhG1" else 0 for c in CHANNELS},
                       "monitored_types": ["PhG1"], "driven_types": ["PhG1"] if phg else [],
                       "monitor_sugar": True})
    return result


def load_design():
    extra = load_json(SPEC)
    if extra["p1_protocol"] != "data/stim_protocol_pharyngeal.json" or sha256(p1.SPEC) != extra["p1_protocol_sha256"]:
        raise ValueError("P1 referencing protocol mismatch")
    original, protocol, cells = p1.load_design()
    grid_sugar = load_json(ROOT / "data/grid_levels.json")["levels"]["sugar"]
    if tuple(grid_sugar[name] for name in ("none", "low", "medium", "high", "very_high")) != DOSES:
        raise ValueError("P2 dose levels differ from the frozen sugar grid")
    if any(extra[k] != original[k] for k in ("base_protocol", "base_protocol_sha256", "channels", "n_poisson_units")):
        raise ValueError("P2 must inherit the frozen protocol and identical P1 stimulation layout")
    trial = extra["trial"]
    if trial["n_trials"] != N_TRIALS or trial["base_seed"] != 20260910 or trial["seed_scheme"] != "published_grid_v1_batch40":
        raise ValueError("P2 requires 30 published-grid-formula trials")
    if extra["conditions"] != select_conditions():
        raise ValueError("conditions differ from the authorised 13-condition design")
    spec = {**original, **extra}
    p1.make_stimulation(spec, cells)
    for condition in select_conditions():
        groups_for(spec, protocol, condition, cells)
    return spec, protocol, cells


def groups_for(spec, protocol, condition, cells):
    groups = p1.groups_for(spec, protocol)
    selected = [n["Body_ID"] for n in spec["pharyngeal_neurons"] if n["Type"] in condition["monitored_types"]]
    groups["monitored_pharyngeal"] = selected
    if condition["driven_types"]:
        groups["driven_pharyngeal"] = [n["Body_ID"] for n in spec["pharyngeal_neurons"] if n["Type"] in condition["driven_types"]]
    if condition["monitor_sugar"]:
        groups["monitored_sugar"] = [str(i) for i in cells["sets"]["sugar"]["ids"]]
    if condition["rates"]["sugar"]:
        groups["driven_sugar"] = [str(i) for i in cells["sets"]["sugar"]["ids"]]
    return groups


def _individual_descriptions(spec, cells, condition):
    rows = [{"Body_ID": n["Body_ID"], "Root_Side": n["Root_Side"], "Type": n["Type"],
             "Target_Muscle": n["Target_Muscle"], "role": "MN_readout", "input_hz": 0}
            for n in spec["readout_neurons"]]
    rows += [{"Body_ID": n["Body_ID"], "Root_Side": n["Root_Side"], "Type": n["Type"],
              "Target_Muscle": "", "role": "monitored_pharyngeal", "input_hz": condition["rates"][n["Type"]]}
             for n in spec["pharyngeal_neurons"] if n["Type"] in condition["monitored_types"]]
    if condition["monitor_sugar"]:
        rows += [{"Body_ID": str(i), "Root_Side": "", "Type": "frozen_sugar_set", "Target_Muscle": "",
                  "role": "monitored_sugar", "input_hz": condition["rates"]["sugar"]}
                 for i in cells["sets"]["sugar"]["ids"]]
    if len({n["Body_ID"] for n in rows}) != len(rows):
        raise ValueError("recorded neurons overlap")
    return rows


def result_identity(condition, identity):
    return {**identity, "condition_id": condition["cond_id"], "condition_index": condition["condition_index"],
            "seed_index": condition["seed_index"], "phase": condition["phase"],
            "input_hz": condition["rates"], "monitored_types": condition["monitored_types"],
            "driven_types": condition["driven_types"], "monitor_sugar": condition["monitor_sugar"],
            "seeds": [phase_p2_seed(condition["condition_index"], t) for t in range(N_TRIALS)]}


def _validate_trial_indices(trials, ids):
    if trials.shape != ids.shape or not np.issubdtype(trials.dtype, np.integer) or np.any((trials < 0) | (trials >= N_TRIALS)):
        raise ValueError("invalid raw trial indices")


def validate_result(saved, path, expected, spec, protocol, cells, condition):
    """Require every completion marker and reconstruct metrics, including silence."""
    if saved.get("identity") != expected or saved.get("completed_trials") != list(range(N_TRIALS)):
        raise ValueError("stored result identity/completion mismatch")
    if saved.get("spikes_sha256") != sha256(path):
        raise ValueError("stored raw spike hash mismatch")
    descriptions = _individual_descriptions(spec, cells, condition)
    roots = [n["Body_ID"] for n in descriptions]
    sources = [n for n in descriptions if n["role"] != "MN_readout"]
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
        active_ids = {int(n["Body_ID"]) for n in sources if n["input_hz"] > 0}
        if not set(map(int, poi_ids)).issubset(active_ids):
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
        print(f"reuse verified {name}: 30 trials", flush=True)
        return saved
    from brian2 import SpikeMonitor, ms
    from sim.network import build_network
    copied, mapping = p1.make_stimulation(spec, cells)
    network = build_network(protocol, copied, mapping)
    source_monitor = SpikeMonitor(network.poisson, name="phase_p2_poisson_monitor")
    network.net.add(source_monitor)
    network.net.store("init")
    expected = result_identity(condition, identity)
    descriptions = _individual_descriptions(spec, cells, condition)
    roots = [n["Body_ID"] for n in descriptions]
    source_roots = [n["Body_ID"] for n in descriptions if n["role"] != "MN_readout"]
    poi_to_root = np.array([network.i2flyid[int(i)] for i in network.target_indices], dtype=np.int64)
    groups = groups_for(spec, protocol, condition, cells)
    individual, grouped = [], []
    arrays = {key: [] for key in ("flywire_id", "t_ms", "trial", "poisson_target_id", "poisson_t_ms", "poisson_trial")}
    started = time.perf_counter()
    for trial, seed in enumerate(expected["seeds"]):
        spikes = network.run_trial(condition["rates"], seed, 1000)
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
        arrays["poisson_target_id"].append(source_ids[selected])
        arrays["poisson_t_ms"].append(source_times[selected])
        arrays["poisson_trial"].append(np.full(int(selected.sum()), trial, dtype=np.int64))
    np.savez_compressed(raw_path, **{k: np.concatenate(v) for k, v in arrays.items()},
                        seeds=np.array(expected["seeds"], dtype=np.int64), completed_trials=np.arange(N_TRIALS, dtype=np.int64),
                        saved_neuron_ids=np.array(roots, dtype=np.int64), poisson_saved_target_ids=np.array(source_roots, dtype=np.int64))
    saved = {"identity": expected, "completed_trials": list(range(N_TRIALS)), "spikes_sha256": sha256(raw_path),
             "individual": individual, "grouped": grouped, "elapsed_s": time.perf_counter() - started}
    validate_result(saved, raw_path, expected, spec, protocol, cells, condition)
    ledger.write_text(json.dumps(saved, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"complete {name}: 30/30 trials; {len(roots)} recorded neurons", flush=True)
    return saved


def paired_statistics(a, b, c):
    values = [np.asarray(v, dtype=float) for v in (a, b, c)]
    if any(v.shape != (N_TRIALS,) or not np.all(np.isfinite(v)) or np.any(v < 0) for v in values):
        raise ValueError("paired vectors must each contain 30 finite nonnegative rates")
    a, b, c = values
    defined = a != 0
    ratios = [float(c[i] / a[i]) if defined[i] else None for i in range(N_TRIALS)]
    delta = c - a - b
    mean = float(np.mean(delta))
    return {"ratio_mean": float(np.mean(ratios)) if np.all(defined) else None,
            "ratio_sd": float(np.std(ratios, ddof=0)) if np.all(defined) else None,
            "ratio_defined_trials": int(defined.sum()), "ratio_total_trials": N_TRIALS,
            "ratio_values": ratios, "delta_values_hz": delta.tolist(),
            "delta_mean_hz": mean, "delta_sd_hz": float(np.std(delta, ddof=0)),
            "above_sum_trials": int(np.sum(delta > 0)), "equal_sum_trials": int(np.sum(delta == 0)),
            "below_sum_trials": int(np.sum(delta < 0)),
            "relation": "superadditive" if mean > 0 else "falls short" if mean < 0 else "equal"}


def validate_paired_inputs(results, out):
    pairs = [r for name in PAIR_IDS for r in results if r["identity"]["condition_id"] == name]
    if len(pairs) != 3 or [r["identity"]["condition_id"] for r in pairs] != list(PAIR_IDS):
        raise ValueError("expected exactly one result per paired condition")
    expected_seeds = [phase_p2_seed(10, t) for t in range(N_TRIALS)]
    for result in pairs:
        if result["identity"]["seeds"] != expected_seeds:
            raise ValueError("paired seed lists differ")
    source_sets = {}
    for role, count in (("monitored_sugar", 23), ("monitored_pharyngeal", 8)):
        sets = [{int(r["Body_ID"]) for r in p["individual"] if r["role"] == role} for p in pairs]
        if any(s != sets[0] for s in sets) or len(sets[0]) != count:
            raise ValueError("paired monitored source sets differ")
        source_sets[role] = sets[0]
    if not source_sets["monitored_sugar"].isdisjoint(source_sets["monitored_pharyngeal"]):
        raise ValueError("paired source populations overlap")
    data = []
    for result in pairs:
        path = Path(out) / f"{result['identity']['condition_id']}.npz"
        if sha256(path) != result["spikes_sha256"]:
            raise ValueError("paired raw spike hash mismatch")
        with np.load(path, allow_pickle=False) as raw:
            if not np.array_equal(raw["seeds"], expected_seeds) or not np.array_equal(raw["completed_trials"], np.arange(N_TRIALS)):
                raise ValueError("paired raw seeds/completion differ")
            data.append({k: raw[k].copy() for k in ("poisson_target_id", "poisson_t_ms", "poisson_trial")})
    for role, left, inactive in (("monitored_sugar", 0, 1), ("monitored_pharyngeal", 1, 0)):
        roots = source_sets[role]
        if np.any(np.isin(data[inactive]["poisson_target_id"], list(roots))):
            raise ValueError("inactive paired source emitted Poisson spikes")
        for root in roots:
            for trial in range(N_TRIALS):
                arrays = []
                for index in (left, 2):
                    raw = data[index]
                    mask = (raw["poisson_target_id"] == root) & (raw["poisson_trial"] == trial)
                    arrays.append(raw["poisson_t_ms"][mask])
                if not np.array_equal(arrays[0], arrays[1]):
                    raise ValueError("shared active paired-channel Poisson spike trains differ")
    return {"n_paired_trials": N_TRIALS, "sugar_a_c_identical": True, "PhG1_b_c_identical": True,
            "n_sugar_neuron_trials": 23 * N_TRIALS, "n_PhG1_neuron_trials": 8 * N_TRIALS}


def write_summary(results, spec, protocol, cells, out):
    conditions = select_conditions()
    if [r["identity"]["condition_id"] for r in results] != [c["cond_id"] for c in conditions]:
        raise ValueError("expected exactly 13 complete results in canonical order")
    summaries = []
    for condition, result in zip(conditions, results):
        readouts = {}
        for group in groups_for(spec, protocol, condition, cells):
            rows = sorted((r for r in result["grouped"] if r["readout"] == group), key=lambda r: r["trial"])
            if [r["trial"] for r in rows] != list(range(N_TRIALS)):
                raise ValueError("missing/duplicate readout trial")
            readouts[group] = summarize_trials([r["rate_hz"] for r in rows], [r["first_spike_ms"] for r in rows])
        summaries.append({**condition, "readouts": readouts})
    paired = {}
    paired_trials = []
    for group in CORE_GROUPS + CEM_GROUPS + ("CEM", "monitored_pharyngeal", "monitored_sugar"):
        rates = [[r["rate_hz"] for r in sorted(result["grouped"], key=lambda x: x["trial"]) if r["readout"] == group]
                 for result in results[-3:]]
        stats = paired_statistics(*rates)
        paired[group] = stats
        for trial in range(N_TRIALS):
            paired_trials.append({"readout": group, "trial": trial, "seed": phase_p2_seed(10, trial),
                                  "a_hz": rates[0][trial], "b_hz": rates[1][trial], "c_hz": rates[2][trial],
                                  "ratio_c_a": stats["ratio_values"][trial], "delta_c_a_b_hz": stats["delta_values_hz"][trial]})
    input_audit = validate_paired_inputs(results, out)
    summary = {"schema_version": "pharyngeal_screen_p2_v1", "n_conditions": 13, "n_trials_per_condition": N_TRIALS,
               "n_trials": 390, "n_mn_readouts": 12, "n_poisson_units": 151, "std_ddof": 0,
               "group_members": p1.groups_for(spec, protocol), "conditions": summaries,
               "paired_statistics": paired, "paired_input_audit": input_audit,
               "latency": "Median first spike among active trials; group first spike is earliest member; active counts always reported.",
               "ratio": "Mean and population SD of trial-wise c/a; undefined overall if any denominator is zero.",
               "additivity": "Paired delta=c-a-b; descriptive mean relation, not an inferential test."}
    write_csv(out / "individual_trials.csv", [r for result in results for r in result["individual"]])
    write_csv(out / "group_trials.csv", [r for result in results for r in result["grouped"]])
    write_csv(out / "paired_trials.csv", paired_trials)
    write_csv(out / "readout_summary.csv", [{"condition_id": c["cond_id"], "readout": g, **v} for c in summaries for g, v in c["readouts"].items()])
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = []
    for phase in ("PhG1_dose", "PhG4_dose", "paired"):
        selected = [c for c in summaries if c["phase"] == phase]
        for metric in ("rate", "latency"):
            for title, groups in (("MN", CORE_GROUPS), ("Individual CEM", CEM_GROUPS),
                                  ("Monitored source sanity", ("monitored_pharyngeal", "monitored_sugar"))):
                units = "mean ± population SD, Hz; n = 30" if metric == "rate" else "median ms; active trials / 30"
                lines += [f"### {phase}: {title} {metric} ({units})", "", "| Condition | " + " | ".join(groups) + " |",
                          "|---|" + "---:|" * len(groups)]
                for c in selected:
                    values = []
                    for g in groups:
                        value = c["readouts"].get(g)
                        if value is None:
                            values.append("not monitored")
                        elif metric == "rate":
                            values.append(f"{value['rate_mean_hz']:.3f} ± {value['rate_std_hz']:.3f}")
                        else:
                            median = "none" if value["latency_median_ms"] is None else f"{value['latency_median_ms']:.2f}"
                            values.append(f"{median} ({value['active_trials']}/30)")
                    lines.append(f"| {c['cond_id']} | " + " | ".join(values) + " |")
                lines.append("")
    lines += ["### Paired combination (trial-wise mean ± population SD)", "",
              "| Readout | a: sugar Hz | b: PhG1 Hz | c: both Hz | c/a | c-a-b Hz | Mean relation | Above/equal/below sum trials |",
              "|---|---:|---:|---:|---:|---:|---|---:|"]
    for g, value in paired.items():
        rates = [f"{c['readouts'][g]['rate_mean_hz']:.3f} ± {c['readouts'][g]['rate_std_hz']:.3f}" for c in summaries[-3:]]
        ratio = f"undefined ({value['ratio_defined_trials']}/30 defined)" if value["ratio_mean"] is None else f"{value['ratio_mean']:.6f} ± {value['ratio_sd']:.6f}"
        lines.append(f"| {g} | " + " | ".join(rates) + f" | {ratio} | {value['delta_mean_hz']:.3f} ± {value['delta_sd_hz']:.3f} | {value['relation']} | {value['above_sum_trials']}/{value['equal_sum_trials']}/{value['below_sum_trials']} |")
    lines += ["", "Shared active-channel Poisson spike trains verified identical for every paired trial: sugar a/c and PhG1 b/c.", ""]
    (out / "tables.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def source_files(spec, protocol):
    return p1.source_files(spec, protocol) + [SPEC, Path(__file__).resolve()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-proc", type=int, default=13)
    parser.add_argument("--out", type=Path, default=ROOT / "results/pharyngeal/p2")
    parser.add_argument("--check-design", action="store_true")
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.n_proc <= 32:
        parser.error("n-proc must be 1..32")
    if args.check_design and args.summarize_only:
        parser.error("choose only one no-simulation mode")
    out = args.out.resolve()
    if out != (ROOT / "results/pharyngeal/p2").resolve():
        parser.error("output must be exactly results/pharyngeal/p2/")
    spec, protocol, cells = load_design()
    if args.check_design:
        print("design valid: 13 conditions x 30 = 390 trials; 151 fixed Poisson units; paired seeds identical; 12 MNs and monitored-source sanity; no simulation")
        return
    files = source_files(spec, protocol)
    hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in files}
    if args.summarize_only:
        meta = load_json(out / "run_meta.json")
        identity = meta["identity"]
        if identity["source_sha256"] != hashes or meta["n_trials_completed"] != 390 or meta["status"] != "complete":
            raise ValueError("run provenance does not match current sources or complete design")
        results = [load_result(c, spec, protocol, cells, out, identity) for c in select_conditions()]
        write_summary(results, spec, protocol, cells, out)
        print("summary valid: 390 complete trials; all metrics reconstructed and paired input events matched; no simulation")
        return
    if platform.system() != "Linux" or "microsoft" not in platform.release().lower():
        raise RuntimeError("Brian2 runs only in the configured WSL2 flybrain environment")
    import brian2
    import Cython
    import joblib
    from joblib import Parallel, delayed
    if brian2.__version__ != "2.9.0":
        raise RuntimeError("P2 requires the configured Brian2 2.9.0 environment")
    identity = {"source_sha256": hashes, "seed_scheme": "published_grid_v1_batch40", "phase": "P2",
                "condition_index_scope": "New P2 indices 0..12; paired conditions share seed_index=10; not lookup-grid indices",
                "brian2_version": brian2.__version__, "duration_ms": 1000, "channels": list(CHANNELS),
                "python_version": platform.python_version(), "numpy_version": np.__version__,
                "joblib_version": joblib.__version__, "cython_version": Cython.__version__,
                "brian2_codegen_backend": "cython", "n_poisson_units": 151, "poisson_inputs_recorded": True}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    print("P2: 13 conditions x 30 = 390 trials; fixed labellar101 + PhG50 layout; paired seed identity", flush=True)
    results = Parallel(n_jobs=min(13, args.n_proc), backend="loky")(
        delayed(_run_condition)(c, spec, protocol, cells, out, identity) for c in select_conditions())
    if any(sha256(p) != hashes[p.relative_to(ROOT).as_posix()] for p in files):
        raise ValueError("source changed during the run")
    write_summary(results, spec, protocol, cells, out)
    meta = {"identity": identity, "git_commit": commit, "status": "complete", "n_conditions": 13,
            "n_trials_completed": 390, "n_proc": min(13, args.n_proc),
            "completed_at": datetime.now(timezone.utc).isoformat(), "elapsed_s": time.perf_counter() - started}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"P2 complete: 390/390 trials; {meta['elapsed_s']:.1f} s", flush=True)


if __name__ == "__main__":
    main()
