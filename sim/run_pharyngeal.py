# SPDX-License-Identifier: MIT
"""Phase P1: 19 conditions x 10 trials; research-only pharyngeal screen.

Validate without simulation: python -B -m sim.run_pharyngeal --check-design
Run only in WSL2 flybrain: python -B -m sim.run_pharyngeal --n-proc 13
All numerical/model parameters are inherited from the frozen base protocol.
The only additional stimulation channels are the 50 XLSX PhG1-16 neurons.
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

from sim.run_mn_readouts import (
    groups_for as mn_groups_for, load_json, published_grid_seed, sha256,
    summarize_trials, write_csv,
)
from scripts.build_mn_readout_ids import read_v783_ids, select_mn_rows
from scripts.cem_inputs import exact_id, select_pharyngeal_rows
from scripts.cross_check_cells import FLYWIRE, read_xlsx
from scripts.mn_readouts_from_replays import aggregate_metrics, neuron_metrics, validate_spikes

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data/stim_protocol_pharyngeal.json"
LABELLAR = ("sugar", "bitter", "water", "ir94e")
PHG_TYPES = tuple(f"PhG{i}" for i in range(1, 17))
CHANNELS = LABELLAR + PHG_TYPES
PHG_COUNTS = (8, 5, 2, 4, 2, 2, 5, 4, 4, 2, 2, 2, 2, 2, 2, 2)
CORE_GROUPS = ("MN9_L", "MN9_R", "MN11D", "MN11V")
CEM_GROUPS = tuple(f"CEM_{side}{i}" for side in ("L", "R") for i in range(1, 4))
N_TRIALS = 10
C2_CONTROL = ROOT / "results/mn-readouts/c2/G_shigh_bnone_wnone_inone.json"


def phase_p_seed(condition_index, trial, base_seed=20260910):
    """Apply the published batch-40 formula to explicit Phase P indices 0..18."""
    for value, upper, name in ((condition_index, 19, "condition_index"), (trial, N_TRIALS, "trial")):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not 0 <= value < upper:
            raise ValueError(f"invalid {name}")
    return published_grid_seed(condition_index, trial, base_seed)


def select_conditions():
    definitions = [("P_baseline", [])]
    definitions += [(f"P_{kind}", [kind]) for kind in PHG_TYPES]
    definitions += [("P_all_pharyngeal", list(PHG_TYPES)), ("P_PhG1_sugar_high", ["PhG1"])]
    result = []
    for index, (name, kinds) in enumerate(definitions):
        rates = {channel: 100 if channel in kinds else 0 for channel in CHANNELS}
        if name == "P_PhG1_sugar_high":
            rates["sugar"] = 120
        result.append({"cond_id": name, "condition_index": index, "rates": rates,
                       "driven_types": list(kinds)})
    return result


def make_stimulation(spec, cells):
    """Add isolated research sets to a copy; always construct all 151 Poisson units."""
    copied = deepcopy(cells)
    mapping = {name: name for name in LABELLAR}
    labellar_ids = []
    for name, count in zip(LABELLAR, (23, 42, 18, 18)):
        ids = [exact_id(i) for i in copied["sets"][name]["ids"]]
        if len(ids) != count or len(set(ids)) != count:
            raise ValueError(f"invalid frozen {name} population")
        labellar_ids.extend(ids)
    if len(set(labellar_ids)) != 101:
        raise ValueError("frozen labellar channels overlap")
    rows = spec["pharyngeal_neurons"]
    if len(rows) != 50 or {n["Type"] for n in rows} != set(PHG_TYPES):
        raise ValueError("expected all 50 PhG1-16 neurons")
    phg_ids = [exact_id(n["Body_ID"]) for n in rows]
    if len(set(phg_ids)) != 50 or not set(phg_ids).isdisjoint(labellar_ids):
        raise ValueError("pharyngeal neurons repeat or overlap frozen labellar neurons")
    if not all(isinstance(n["Body_ID"], str) and n.get("in_v783") is True for n in rows):
        raise ValueError("PhG IDs must be exact strings present in v783")
    for kind, count in zip(PHG_TYPES, PHG_COUNTS):
        selected = [n for n in rows if n["Type"] == kind]
        if len(selected) != count or {n["Root_Side"] for n in selected} != {"L", "R"}:
            raise ValueError(f"unexpected count or missing side for {kind}")
        set_name = f"phase_p_{kind}"
        if set_name in copied["sets"]:
            raise ValueError(f"research set would overwrite existing {set_name}")
        copied["sets"][set_name] = {"ids": [n["Body_ID"] for n in selected]}
        mapping[kind] = set_name
    return copied, mapping


def groups_for(spec, protocol, condition=None, cells=None):
    result = mn_groups_for(spec, protocol)
    cems = sorted((n for n in spec["readout_neurons"] if n["Type"] == "CEM"),
                  key=lambda n: (n["Root_Side"], exact_id(n["Body_ID"])))
    for side in ("L", "R"):
        selected = [n for n in cems if n["Root_Side"] == side]
        if len(selected) != 3:
            raise ValueError("expected three XLSX-side CEM neurons per side")
        for index, neuron in enumerate(selected, 1):
            result[f"CEM_{side}{index}"] = [neuron["Body_ID"]]
    if condition is not None:
        driven = [n["Body_ID"] for n in spec["pharyngeal_neurons"] if n["Type"] in condition["driven_types"]]
        if driven:
            result["driven_pharyngeal"] = driven
        if condition["rates"]["sugar"]:
            if cells is None:
                raise ValueError("sugar sanity requires frozen cells")
            result["driven_sugar"] = [str(i) for i in cells["sets"]["sugar"]["ids"]]
    return result


def source_pharyngeal_rows(sheets, v783):
    fields = ("Body_ID", "Root_Side", "Type", "Subtype", "Entry_Nerve")
    return [{**{name: row.get(name, "") for name in fields},
             "in_v783": row["Body_ID"] in v783}
            for row in select_pharyngeal_rows(sheets["GRNs"])]


def load_design():
    spec = load_json(SPEC)
    base_path = ROOT / spec["base_protocol"]
    if base_path.resolve() != (ROOT / "data/stim_protocol.json").resolve() or sha256(base_path) != spec["base_protocol_sha256"]:
        raise ValueError("frozen base protocol mismatch")
    protocol = load_json(base_path)
    if protocol["trial"]["duration_ms"] != 1000 or list(protocol["stimulus"]["channels"]) != list(LABELLAR):
        raise ValueError("frozen duration or original channel order changed")
    trial = spec["trial"]
    if trial["n_trials"] != N_TRIALS or trial["seed_scheme"] != "published_grid_v1_batch40" or trial["base_seed"] != 20260910:
        raise ValueError("Phase P requires 10 trials and the published grid seed formula")
    if spec["channels"] != list(CHANNELS) or spec["conditions"] != select_conditions():
        raise ValueError("conditions differ from the authorised 19-condition design")
    if spec["n_poisson_units"] != 151:
        raise ValueError("the same 151 Poisson units must be used in every condition")
    inventory_path = ROOT / spec["readout_source"]
    inventory = load_json(inventory_path)
    selected = [n for n in inventory["neurons"] if n["Type"] in {"MN9", "MN11D", "MN11V", "CEM"}]
    if selected != spec["readout_neurons"] or not all(n["in_v783"] for n in selected):
        raise ValueError("MN readouts differ from verified inventory")
    source = spec["pharyngeal_source"]
    if source["sheet"] != "GRNs" or source["Connectome"] != FLYWIRE:
        raise ValueError("PhG inventory must use the XLSX GRNs FlyWire rows")
    xlsx = ROOT / source["file"]
    completeness = ROOT / protocol["completeness_file"]
    if sha256(xlsx) != source["sha256"] or sha256(completeness) != source["completeness_sha256"]:
        raise ValueError("XLSX or v783 completeness hash mismatch")
    if source["file"] != inventory["source"]["file"] or source["sha256"] != inventory["source"]["sha256"]:
        raise ValueError("PhG and MN inventories must come from the same verified workbook")
    v783 = read_v783_ids(completeness)
    sheets = read_xlsx(xlsx)
    if source_pharyngeal_rows(sheets, v783) != spec["pharyngeal_neurons"]:
        raise ValueError("PhG source rows do not match the exact XLSX fields")
    source_mns = [n for n in select_mn_rows(sheets["MNs"], v783) if n["Type"] in {"MN9", "MN11D", "MN11V", "CEM"}]
    if source_mns != selected:
        raise ValueError("MN readouts no longer match the source XLSX")
    cells = load_json(ROOT / "data/cells.json")
    if sha256(ROOT / "data/cells.json") != spec["frozen_cells_sha256"]:
        raise ValueError("frozen labellar cell sets mismatch")
    make_stimulation(spec, cells)
    for condition in select_conditions():
        groups_for(spec, protocol, condition, cells)
    return spec, protocol, cells


def source_files(spec, protocol):
    relative = [
        "data/stim_protocol_pharyngeal.json", "sim/run_pharyngeal.py", "sim/run_mn_readouts.py",
        "sim/network.py", "sim/grid.py", "scripts/mn_readouts_from_replays.py",
        "scripts/build_mn_readout_ids.py", "scripts/cem_inputs.py", "scripts/cross_check_cells.py",
        "scripts/validate_release.py", "data/stim_protocol.json", "data/stim_protocol_mn.json",
        "data/cells.json", "data/grid_levels.json", "data/lookup_table.json", spec["readout_source"],
        spec["pharyngeal_source"]["file"], protocol["connectivity_file"], protocol["completeness_file"],
    ]
    return [ROOT / name for name in relative]


def result_identity(condition, identity):
    return {**identity, "condition_id": condition["cond_id"], "condition_index": condition["condition_index"],
            "input_hz": condition["rates"], "driven_types": condition["driven_types"],
            "seeds": [phase_p_seed(condition["condition_index"], t) for t in range(N_TRIALS)]}


def _individual_descriptions(spec, cells, condition):
    rows = [{"Body_ID": n["Body_ID"], "Root_Side": n["Root_Side"], "Type": n["Type"],
             "Target_Muscle": n["Target_Muscle"], "role": "MN_readout"} for n in spec["readout_neurons"]]
    rows += [{"Body_ID": n["Body_ID"], "Root_Side": n["Root_Side"], "Type": n["Type"],
              "Target_Muscle": "", "role": "driven_pharyngeal"} for n in spec["pharyngeal_neurons"]
             if n["Type"] in condition["driven_types"]]
    if condition["rates"]["sugar"]:
        rows += [{"Body_ID": str(i), "Root_Side": "", "Type": "frozen_sugar_set",
                  "Target_Muscle": "", "role": "driven_sugar"} for i in cells["sets"]["sugar"]["ids"]]
    if len({n["Body_ID"] for n in rows}) != len(rows):
        raise ValueError("MN readouts overlap driven cells")
    return rows


def validate_result(saved, path, expected, spec, protocol, cells, condition):
    """Reconstruct every saved metric from NPZ; missing trials never become silence."""
    if saved.get("identity") != expected or saved.get("completed_trials") != list(range(N_TRIALS)):
        raise ValueError("stored result identity/completion mismatch")
    if saved.get("spikes_sha256") != sha256(path):
        raise ValueError("stored raw spike hash mismatch")
    descriptions = _individual_descriptions(spec, cells, condition)
    roots = [n["Body_ID"] for n in descriptions]
    groups = groups_for(spec, protocol, condition, cells)
    with np.load(path, allow_pickle=False) as spikes:
        if set(spikes.files) != {"flywire_id", "t_ms", "trial", "seeds", "completed_trials", "saved_neuron_ids"}:
            raise ValueError("unexpected raw spike fields")
        ids, times, trials = spikes["flywire_id"], spikes["t_ms"], spikes["trial"]
        validate_spikes(ids, times, 1000)
        if trials.shape != ids.shape or not np.issubdtype(trials.dtype, np.integer) or np.any((trials < 0) | (trials >= N_TRIALS)):
            raise ValueError("invalid raw trial indices")
        for key, values in (("seeds", expected["seeds"]), ("completed_trials", list(range(N_TRIALS))),
                            ("saved_neuron_ids", [int(r) for r in roots])):
            if not np.issubdtype(spikes[key].dtype, np.integer) or not np.array_equal(spikes[key], values):
                raise ValueError(f"invalid raw {key}")
        if not set(map(int, ids)).issubset(map(int, roots)):
            raise ValueError("raw spikes include unrequested neurons")
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
    ledger = out / f"{condition['cond_id']}.json"
    spikes = out / f"{condition['cond_id']}.npz"
    if not ledger.exists() or not spikes.exists():
        raise ValueError(f"{condition['cond_id']}: incomplete output; refusing to overwrite or infer silent trials")
    return validate_result(load_json(ledger), spikes, result_identity(condition, identity),
                           spec, protocol, cells, condition)


def _run_condition(condition, spec, protocol, cells, output_dir, identity):
    # No Brian2 object or import exists before the main process passes the WSL gate.
    out = Path(output_dir)
    name = condition["cond_id"]
    ledger, spikes_path = out / f"{name}.json", out / f"{name}.npz"
    if ledger.exists() or spikes_path.exists():
        saved = load_result(condition, spec, protocol, cells, out, identity)
        print(f"reuse verified {name}: 10 trials", flush=True)
        return saved
    from sim.network import build_network
    copied_cells, mapping = make_stimulation(spec, cells)
    network = build_network(protocol, copied_cells, mapping)
    expected = result_identity(condition, identity)
    descriptions = _individual_descriptions(spec, cells, condition)
    roots = [n["Body_ID"] for n in descriptions]
    groups = groups_for(spec, protocol, condition, cells)
    individual, grouped, raw_ids, raw_times, raw_trials = [], [], [], [], []
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
        raw_ids.append(ids)
        raw_times.append(times)
        raw_trials.append(np.full(len(times), trial, dtype=np.int64))
    np.savez_compressed(spikes_path, flywire_id=np.concatenate(raw_ids), t_ms=np.concatenate(raw_times),
                        trial=np.concatenate(raw_trials), seeds=np.array(expected["seeds"], dtype=np.int64),
                        completed_trials=np.arange(N_TRIALS, dtype=np.int64),
                        saved_neuron_ids=np.array(roots, dtype=np.int64))
    saved = {"identity": expected, "completed_trials": list(range(N_TRIALS)),
             "spikes_sha256": sha256(spikes_path), "individual": individual, "grouped": grouped,
             "elapsed_s": time.perf_counter() - started}
    validate_result(saved, spikes_path, expected, spec, protocol, cells, condition)
    ledger.write_text(json.dumps(saved, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"complete {name}: 10/10 trials; {len(roots)} recorded neurons", flush=True)
    return saved


def c2_control(spec, protocol):
    """Read an existing 30-trial comparator; do not run an unrequested 20th condition."""
    saved = load_json(C2_CONTROL)
    identity = saved["identity"]
    if identity["cell_id"] != "G_shigh_bnone_wnone_inone" or identity["global_index"] != 240:
        raise ValueError("unexpected C2 sugar-only control")
    if identity["input_hz"] != dict(zip(LABELLAR, (120, 0, 0, 0))) or saved["completed_trials"] != list(range(30)):
        raise ValueError("C2 control conditions/completion mismatch")
    if identity["seeds"] != [published_grid_seed(240, t) for t in range(30)]:
        raise ValueError("C2 control seed mismatch")
    for source in ("data/stim_protocol.json", "data/stim_protocol_mn.json", "data/cells.json",
                   "data/mn_readout_ids.json", "sim/network.py", protocol["connectivity_file"],
                   protocol["completeness_file"]):
        if identity["source_sha256"].get(source) != sha256(ROOT / source):
            raise ValueError(f"C2 control source differs: {source}")
    c2_spec = load_json(ROOT / "data/stim_protocol_mn.json")
    if c2_spec["readout_neurons"] != spec["readout_neurons"]:
        raise ValueError("C2 control readout selection mismatch")
    raw_path = C2_CONTROL.with_suffix(".npz")
    if saved["spikes_sha256"] != sha256(raw_path):
        raise ValueError("C2 control raw spike hash mismatch")
    summaries = {}
    groups = groups_for(spec, protocol)
    with np.load(raw_path, allow_pickle=False) as raw:
        validate_spikes(raw["flywire_id"], raw["t_ms"], 1000)
        if raw["trial"].shape != raw["flywire_id"].shape or not np.issubdtype(raw["trial"].dtype, np.integer):
            raise ValueError("C2 control raw trial shape/type mismatch")
        if np.any((raw["trial"] < 0) | (raw["trial"] >= 30)) or not np.array_equal(raw["seeds"], identity["seeds"]):
            raise ValueError("C2 control raw trial/seed mismatch")
        arrays = {g: [] for g in groups}
        latencies = {g: [] for g in groups}
        roots = [n["Body_ID"] for n in spec["readout_neurons"]]
        for trial in range(30):
            mask = raw["trial"] == trial
            metrics = neuron_metrics(raw["flywire_id"][mask], raw["t_ms"][mask], roots, 1000)
            for group, members in groups.items():
                metric = aggregate_metrics([metrics[r] for r in members])
                arrays[group].append(metric["rate_hz"])
                latencies[group].append(metric["first_spike_ms"])
                if group in CORE_GROUPS or group == "CEM":
                    previous = [r for r in saved["grouped"] if r["trial"] == trial and r["readout"] == group]
                    if len(previous) != 1 or any(previous[0][k] != v for k, v in metric.items()):
                        raise ValueError("C2 control metrics disagree with its raw spikes")
        summaries = {g: summarize_trials(arrays[g], latencies[g]) for g in groups}
    lookup = load_json(ROOT / "data/lookup_table.json")
    matches = [row for row in lookup["cells"] if row["hz"] == identity["input_hz"]]
    if len(matches) != 1:
        raise ValueError("C2 control must identify exactly one frozen lookup cell")
    value = matches[0]
    if not np.isclose(summaries["MN9_L"]["rate_mean_hz"], value["mn9_left_mean"], rtol=0, atol=0.00051):
        raise ValueError("C2 left MN9 mean does not match the frozen lookup")
    return {"source": C2_CONTROL.relative_to(ROOT).as_posix(), "sha256": sha256(C2_CONTROL),
            "raw_sha256": sha256(raw_path), "identity": identity, "readouts": summaries,
            "comparison": "Descriptive unpaired comparison, n=10 Phase P versus n=30 existing C2. Phase P constructs 151 Poisson units versus C2's 101, changing random-stream consumption even for reused seed values; statistical independence is not established by this layout change."}


def write_summary(results, spec, protocol, cells, out, comparator):
    if [r["identity"]["condition_id"] for r in results] != [c["cond_id"] for c in select_conditions()]:
        raise ValueError("expected exactly 19 complete results in canonical condition order")
    individual = [r for result in results for r in result["individual"]]
    grouped = [r for result in results for r in result["grouped"]]
    summaries = []
    for condition, result in zip(select_conditions(), results):
        readouts = {}
        for group in groups_for(spec, protocol, condition, cells):
            rows = sorted((r for r in result["grouped"] if r["readout"] == group), key=lambda r: r["trial"])
            if [r["trial"] for r in rows] != list(range(N_TRIALS)):
                raise ValueError("missing/duplicate readout trial")
            readouts[group] = summarize_trials([r["rate_hz"] for r in rows], [r["first_spike_ms"] for r in rows])
        summaries.append({**condition, "readouts": readouts})
    combo = summaries[-1]
    ratios = {}
    for group in CORE_GROUPS + CEM_GROUPS:
        numerator = combo["readouts"][group]["rate_mean_hz"]
        denominator = comparator["readouts"][group]["rate_mean_hz"]
        ratios[group] = numerator / denominator if denominator else None
    summary = {"schema_version": "pharyngeal_screen_p1_v1", "n_conditions": 19, "n_trials_per_condition": N_TRIALS,
               "n_trials": 190, "n_mn_readouts": 12, "n_stimulable_pharyngeal_neurons": 50,
               "n_poisson_units": 151, "std_ddof": 0,
               "latency": "Median first spike in active trials only; type/group first spike is earliest member; active counts always reported. No driven group exists for baseline.",
               "group_members": groups_for(spec, protocol), "conditions": summaries,
               "sugar_only_reference": comparator, "combination_to_sugar_only_ratios": ratios}
    write_csv(out / "individual_trials.csv", individual)
    write_csv(out / "group_trials.csv", grouped)
    flat = [{"condition_id": c["cond_id"], "readout": g, **value}
            for c in summaries for g, value in c["readouts"].items()]
    write_csv(out / "readout_summary.csv", flat)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = []
    for title, groups in (("MN rates", CORE_GROUPS), ("Individual CEM rates", CEM_GROUPS),
                          ("Driven-cell rate sanity", ("driven_pharyngeal", "driven_sugar"))):
        lines += [f"### {title} (mean ± population SD, Hz; n = 10)", "",
                  "| Condition | " + " | ".join(groups) + " |", "|---|" + "---:|" * len(groups)]
        for c in summaries:
            values = ["not driven" if g not in c["readouts"] else
                      f"{c['readouts'][g]['rate_mean_hz']:.3f} ± {c['readouts'][g]['rate_std_hz']:.3f}" for g in groups]
            lines.append(f"| {c['cond_id']} | " + " | ".join(values) + " |")
        lines.append("")
    for title, groups in (("MN latency medians", CORE_GROUPS), ("Individual CEM latency medians", CEM_GROUPS),
                          ("Driven-cell latency sanity", ("driven_pharyngeal", "driven_sugar"))):
        lines += [f"### {title} (ms; active trials / 10)", "",
                  "| Condition | " + " | ".join(groups) + " |", "|---|" + "---:|" * len(groups)]
        for c in summaries:
            values = []
            for g in groups:
                value = c["readouts"].get(g)
                if value is None:
                    values.append("not driven")
                else:
                    median = "none" if value["latency_median_ms"] is None else f"{value['latency_median_ms']:.2f}"
                    values.append(f"{median} ({value['active_trials']}/10)")
            lines.append(f"| {c['cond_id']} | " + " | ".join(values) + " |")
        lines.append("")
    lines += ["### PhG1 + sugar-high versus existing sugar-only C2 (descriptive)", "",
              "| Readout | Sugar only, n = 30, mean ± SD Hz | PhG1 + sugar, n = 10, mean ± SD Hz | Ratio |",
              "|---|---:|---:|---:|"]
    for g in CORE_GROUPS + CEM_GROUPS:
        ref, combined = comparator["readouts"][g], combo["readouts"][g]
        ratio = "undefined (zero reference)" if ratios[g] is None else f"{ratios[g]:.6f}"
        lines.append(f"| {g} | {ref['rate_mean_hz']:.3f} ± {ref['rate_std_hz']:.3f} | "
                     f"{combined['rate_mean_hz']:.3f} ± {combined['rate_std_hz']:.3f} | {ratio} |")
    lines += ["", comparator["comparison"], ""]
    (out / "tables.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-proc", type=int, default=13)
    parser.add_argument("--out", type=Path, default=ROOT / "results/pharyngeal/p1")
    parser.add_argument("--check-design", action="store_true")
    parser.add_argument("--summarize-only", action="store_true", help="verify raw ledgers and regenerate tables; no simulation")
    args = parser.parse_args()
    if not 1 <= args.n_proc <= 32:
        parser.error("n-proc must be 1..32")
    if args.check_design and args.summarize_only:
        parser.error("choose only one no-simulation mode")
    out = args.out.resolve()
    if not out.is_relative_to((ROOT / "results/pharyngeal").resolve()):
        parser.error("output must stay inside results/pharyngeal/")
    spec, protocol, cells = load_design()
    comparator = c2_control(spec, protocol)
    if args.check_design:
        print("design valid: 19 conditions x 10 published-grid-formula trials; 151 fixed Poisson units; 12 MNs plus driven-cell sanity; no simulation")
        return
    files = source_files(spec, protocol)
    hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in files}
    if args.summarize_only:
        meta = load_json(out / "run_meta.json")
        identity = meta["identity"]
        if identity["source_sha256"] != hashes or meta["n_trials_completed"] != 190 or meta["status"] != "complete":
            raise ValueError("run provenance does not match current sources or complete design")
        if identity["c2_comparator_sha256"] != comparator["sha256"]:
            raise ValueError("C2 comparator changed after Phase P run")
        results = [load_result(c, spec, protocol, cells, out, identity) for c in select_conditions()]
        write_summary(results, spec, protocol, cells, out, comparator)
        print("summary valid: 190 complete trials; every saved metric reconstructed from raw spikes; no simulation")
        return
    if platform.system() != "Linux" or "microsoft" not in platform.release().lower():
        raise RuntimeError("Brian2 runs only in the configured WSL2 flybrain environment")
    import brian2
    import Cython
    import joblib
    from joblib import Parallel, delayed
    if brian2.__version__ != "2.9.0":
        raise RuntimeError("Phase P requires the configured Brian2 2.9.0 environment")
    identity = {"source_sha256": hashes, "seed_scheme": "published_grid_v1_batch40",
                "condition_index_scope": "Phase P indices 0..18, not a lookup-grid cell index",
                "brian2_version": brian2.__version__, "duration_ms": 1000, "channels": list(CHANNELS),
                "python_version": platform.python_version(), "numpy_version": np.__version__,
                "joblib_version": joblib.__version__, "cython_version": Cython.__version__,
                "brian2_codegen_backend": "cython", "n_poisson_units": 151,
                "c2_comparator_sha256": comparator["sha256"]}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    print("P1: 19 conditions x 10 trials; model unchanged; fixed labellar101 + PhG50 stimulation channels", flush=True)
    results = Parallel(n_jobs=min(19, args.n_proc), backend="loky")(
        delayed(_run_condition)(c, spec, protocol, cells, out, identity) for c in select_conditions())
    if any(sha256(p) != hashes[p.relative_to(ROOT).as_posix()] for p in files):
        raise ValueError("source changed during the run")
    if comparator["sha256"] != sha256(C2_CONTROL):
        raise ValueError("C2 comparator changed during the run")
    write_summary(results, spec, protocol, cells, out, comparator)
    meta = {"identity": identity, "git_commit": commit, "status": "complete", "n_conditions": 19,
            "n_trials_completed": 190, "n_proc": min(19, args.n_proc),
            "completed_at": datetime.now(timezone.utc).isoformat(), "elapsed_s": time.perf_counter() - started}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"P1 complete: 190/190 trials; {meta['elapsed_s']:.1f} s", flush=True)


if __name__ == "__main__":
    main()
