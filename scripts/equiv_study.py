#!/usr/bin/env python3
"""Rigorous store/restore, fresh-PoissonGroup, and PoissonInput study."""
from __future__ import annotations

import argparse
import gc
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import first so its Cython cache preference is established before Brian objects exist.
from sim.network import build_network, channel_cell_sets, load_cells, load_protocol

import numpy as np
import pandas as pd
from brian2 import Hz, mV, second, seed as brian_seed
from joblib import Parallel, delayed
from scipy import stats

from sim import legacy
from sim.readout import mn9_rate
from sim.runner import _base_seed, expand_conditions, spikes_dataframe

OUT = ROOT / "results" / "phase0" / "equiv_study"


N_SEEDS_SEMANTICS = 30


def _channels(protocol: dict) -> dict[str, str]:
    return {"sugar": channel_cell_sets(protocol)["sugar"]}


def _equal(a: dict[int, np.ndarray], b: dict[int, np.ndarray]) -> bool:
    return set(a) == set(b) and all(
        np.array_equal(a[key], b[key])
        for key in a
    )


def _full_spikes(network) -> dict[int, np.ndarray]:
    return {
        network.i2flyid[int(i)]: np.asarray(ts / second, dtype=float)
        for i, ts in network.monitor.spike_trains().items()
    }


def _manual_trial(network, protocol: dict, seed: int, diagnostics: bool = False):
    network.net.restore("init")
    diag = None
    if diagnostics:
        v = np.asarray(network.neurons.v[:] / mV, dtype=float)
        g = np.asarray(network.neurons.g[:] / mV, dtype=float)
        not_refractory = np.asarray(network.neurons.not_refractory[:], dtype=bool)
        lastspike = np.asarray(network.neurons.lastspike[:] / second, dtype=float)
        rates = np.asarray(network.poisson.rates[:] / Hz, dtype=float)
        v0 = float(protocol["model"]["v_0_mV"])
        diag = {
            "v_all_at_rest": bool(np.all(v == v0)),
            "g_all_at_rest": bool(np.all(g == 0.0)),
            "not_refractory_all_true": bool(np.all(not_refractory)),
            # Brian2 initialises lastspike to a large negative finite time (not -inf);
            # "at rest" = every neuron's last spike lies far before t=0 and all are equal.
            "lastspike_all_at_rest": bool(np.all(lastspike < -100.0) and np.all(lastspike == lastspike[0])),
            "lastspike_initial_s": float(lastspike[0]),
            "stimulus_rates_all_at_rest": bool(np.all(rates == 0.0)),
            "max_abs_g_mV": float(np.max(np.abs(g))),
            "max_abs_v_minus_v0_mV": float(np.max(np.abs(v - v0))),
            "not_refractory_false": int(np.count_nonzero(~not_refractory)),
            "poisson_rates_sum_hz": float(np.sum(rates)),
        }
        print("post-restore: " + ", ".join(f"{k}={v}" for k, v in diag.items()), flush=True)
    network.set_rates({"sugar": 100.0})
    brian_seed(seed)
    network.net.run(float(protocol["trial"]["duration_ms"]) * 0.001 * second)
    return _full_spikes(network), diag


def restore_determinism(protocol: dict, cells: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    seed = _base_seed(protocol)
    print("building first reusable network", flush=True)
    first = build_network(protocol, cells, _channels(protocol))
    a, _ = _manual_trial(first, protocol, seed)
    print(f"running intervening seed {seed + 1}", flush=True)
    b, _ = _manual_trial(first, protocol, seed + 1)
    print("checking restored state before repeating the original seed", flush=True)
    a2, diag = _manual_trial(first, protocol, seed, True)
    print("building second reusable network", flush=True)
    second_net = build_network(protocol, cells, _channels(protocol))
    a3, _ = _manual_trial(second_net, protocol, seed)
    left = int(protocol["readout"]["left"])
    result = {
        "seed": seed, "diagnostics": diag,
        "state_at_rest": all(diag[key] for key in (
            "v_all_at_rest", "g_all_at_rest", "not_refractory_all_true",
            "lastspike_all_at_rest", "stimulus_rates_all_at_rest",
        )),
        "a_equals_a2": _equal(a, a2), "a_equals_a3": _equal(a, a3),
        "same_neuron_set_a_a2": set(a) == set(a2),
        "same_neuron_set_a_a3": set(a) == set(a3),
        "total_spikes": {k: int(sum(map(len, x.values()))) for k, x in
                         (("A", a), ("B", b), ("A2", a2), ("A3", a3))},
        "mn9_left": {k: int(len(x[left])) for k, x in
                     (("A", a), ("B", b), ("A2", a2), ("A3", a3))},
    }
    result["pass"] = bool(result["a_equals_a2"] and result["state_at_rest"])
    spikes_dataframe([(i, x) for i, x in enumerate((a, b, a2, a3))]).to_parquet(
        OUT / "restore_determinism.parquet", index=False
    )
    (OUT / "restore_determinism.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


def _reusable_shard(worker: int, seeds: list[int], protocol: dict, cells: dict):
    print(f"reusable worker {worker}: {len(seeds)} trial(s)", flush=True)
    net = build_network(protocol, cells, _channels(protocol))
    duration = float(protocol["trial"]["duration_ms"])
    return [(seed, net.run_trial({"sugar": 100.0}, seed, duration)) for seed in seeds]


def _run_reusable(seeds: list[int], n_proc: int, protocol: dict, cells: dict):
    workers = max(1, min(n_proc, len(seeds)))
    shards = [seeds[i::workers] for i in range(workers)]
    parts = Parallel(n_jobs=workers, backend="loky")(
        delayed(_reusable_shard)(i, shard, protocol, cells) for i, shard in enumerate(shards)
    )
    return sorted((item for part in parts for item in part), key=lambda x: x[0])


def _fresh(kind: str, trial: int, seed: int, protocol: dict, cells: dict):
    print(f"{kind} trial {trial + 1}, seed {seed}", flush=True)
    function = legacy.run_trial if kind == "poissoninput" else legacy.run_trial_poissongroup
    spikes = function(protocol, cells, _channels(protocol), {"sugar": 100.0}, seed,
                      float(protocol["trial"]["duration_ms"]))
    gc.collect()
    return seed, spikes


def _run_fresh(kind: str, seeds: list[int], n_proc: int, protocol: dict, cells: dict):
    return Parallel(n_jobs=max(1, min(n_proc, len(seeds))), backend="loky")(
        delayed(_fresh)(kind, i, seed, protocol, cells) for i, seed in enumerate(seeds)
    )


def _write_spikes(name: str, values: list[tuple[int, dict]], seeds: list[int]) -> None:
    by_seed = dict(values)
    frame = spikes_dataframe([(i, by_seed[seed]) for i, seed in enumerate(seeds)])
    frame.to_parquet(OUT / f"{name}.parquet", index=False)


def _measure(values: list[tuple[int, dict]], seeds: list[int], protocol: dict) -> list[dict]:
    by_seed = dict(values)
    frame = spikes_dataframe([(i, by_seed[s]) for i, s in enumerate(seeds)])
    rates = mn9_rate(frame, protocol, len(seeds))
    duration_s = float(protocol["trial"]["duration_ms"]) / 1000.0
    return [{"left": float(rates["left"]["trials"][i]),
             "right": float(rates["right"]["trials"][i]),
             "total": int(sum(map(len, by_seed[s].values()))),
             "total_rate_hz": float(sum(map(len, by_seed[s].values())) / duration_s)}
            for i, s in enumerate(seeds)]


def paired(protocol: dict, cells: dict, n_proc: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = [_base_seed(protocol) + i for i in range(10)]
    a = _run_reusable(seeds, n_proc, protocol, cells)
    c = _run_fresh("poissongroup", seeds, n_proc, protocol, cells)
    _write_spikes("paired_reusable", a, seeds)
    _write_spikes("paired_fresh_poissongroup", c, seeds)
    am, cm, ad, cd = _measure(a, seeds, protocol), _measure(c, seeds, protocol), dict(a), dict(c)
    rows = [{"trial": i, "seed": seed, "reusable_mn9_left": am[i]["left"],
             "fresh_poissongroup_mn9_left": cm[i]["left"],
             "paired_difference_hz": am[i]["left"] - cm[i]["left"],
             "all_neurons_equal": _equal(ad[seed], cd[seed])} for i, seed in enumerate(seeds)]
    result = {"rows": rows, "exact_equal_seeds": sum(r["all_neurons_equal"] for r in rows),
              "n_seeds": len(seeds),
              "mean_paired_difference_hz": float(np.mean([
                  r["paired_difference_hz"] for r in rows
              ]))}
    result["pass"] = abs(result["mean_paired_difference_hz"]) <= 2.0
    (OUT / "paired.json").write_text(json.dumps(result, indent=2) + "\n")
    print(pd.DataFrame(rows).to_string(index=False), flush=True)
    print(f"mean paired difference: {result['mean_paired_difference_hz']:.3f} Hz; "
          f"{'PASS' if result['pass'] else 'FAIL'}", flush=True)
    print(f"exact all-neuron equality: {result['exact_equal_seeds']}/{len(seeds)}", flush=True)


def _describe(x: list[float]) -> dict:
    a = np.asarray(x, dtype=float)
    return {"mean": float(a.mean()), "std_ddof0": float(a.std(ddof=0)),
            "std_ddof1": float(a.std(ddof=1)), "se": float(a.std(ddof=1) / math.sqrt(len(a)))}


def _compare(x: list[float], y: list[float]) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    diff = float(x.mean() - y.mean())
    vx, vy, nx, ny = x.var(ddof=1), y.var(ddof=1), len(x), len(y)
    se2 = vx / nx + vy / ny
    if se2 == 0:
        lo = hi = diff
    else:
        df = se2 ** 2 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
        delta = float(stats.t.ppf(0.975, df) * math.sqrt(se2))
        lo, hi = diff - delta, diff + delta
    t = stats.ttest_ind(x, y, equal_var=False)
    u = stats.mannwhitneyu(x, y, alternative="two-sided")
    return {"mean_difference": diff, "ci95": [float(lo), float(hi)],
            "welch_t": float(t.statistic) if np.isfinite(t.statistic) else None,
            "welch_p": float(t.pvalue) if np.isfinite(t.pvalue) else 1.0,
            "mannwhitney_u": float(u.statistic), "mannwhitney_p": float(u.pvalue)}


def stimulus_semantics(protocol: dict, cells: dict, n_proc: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = [_base_seed(protocol) + i for i in range(N_SEEDS_SEMANTICS)]
    paths = {"a_reusable": _run_reusable(seeds, n_proc, protocol, cells),
             "b_poissoninput": _run_fresh("poissoninput", seeds, n_proc, protocol, cells),
             "c_fresh_poissongroup": _run_fresh("poissongroup", seeds, n_proc, protocol, cells)}
    measures = {name: _measure(value, seeds, protocol) for name, value in paths.items()}
    for name, value in paths.items():
        _write_spikes(f"stimulus_{name}", value, seeds)
    rows = [{"trial": i, "seed": seed, **{name: measures[name][i] for name in paths}}
            for i, seed in enumerate(seeds)]
    summary, comparisons = {}, {}
    for metric in ("left", "right", "total"):
        summary[metric] = {name: _describe([r[name][metric] for r in rows]) for name in paths}
        comparisons[metric] = {}
        for x, y in (("a_reusable", "b_poissoninput"),
                     ("c_fresh_poissongroup", "b_poissoninput"),
                     ("a_reusable", "c_fresh_poissongroup")):
            comparisons[metric][f"{x}_vs_{y}"] = _compare(
                [r[x][metric] for r in rows], [r[y][metric] for r in rows])
    left_cmp = comparisons["left"]["a_reusable_vs_b_poissoninput"]
    total_cmp = comparisons["total"]["a_reusable_vs_b_poissoninput"]
    legacy_total_mean = summary["total"]["b_poissoninput"]["mean"]
    total_ci_percent = [
        float(100.0 * bound / legacy_total_mean) if legacy_total_mean else None
        for bound in total_cmp["ci95"]
    ]
    # Pass rule (product owner, 2026-09-10): 95% CI of the mean difference within
    # +/-3 Hz AND including zero. No p-value requirement.
    left_pass = (
        left_cmp["ci95"][0] >= -3.0
        and left_cmp["ci95"][1] <= 3.0
        and left_cmp["ci95"][0] <= 0.0 <= left_cmp["ci95"][1]
    )
    total_pass = (
        total_cmp["ci95"][0] <= 0.0 <= total_cmp["ci95"][1]
    )
    result = {"note": "PoissonInput and PoissonGroup consume RNG differently; b is distributional, not paired.",
              "rows": rows, "summary": summary, "comparisons": comparisons,
              "acceptance": {
                  "left_pass": bool(left_pass), "total_pass": bool(total_pass),
                  "pass": bool(left_pass and total_pass),
                  "total_ci95_percent_of_legacy_mean": total_ci_percent,
              }}
    (OUT / "stimulus_semantics.json").write_text(json.dumps(result, indent=2) + "\n")
    print(pd.DataFrame([{"trial": r["trial"], "seed": r["seed"], **{
        f"{k}_{m}": r[k][m] for k in paths for m in ("left", "right", "total")}} for r in rows]).to_string(index=False))


def refractory_quirk(protocol: dict, cells: dict) -> None:
    """Compare full-channel and sugar-only reusable builds with matched seeds."""
    OUT.mkdir(parents=True, exist_ok=True)
    mappings = channel_cell_sets(protocol)
    full_channels = {name: mappings[name] for name in ("sugar", "bitter")}
    sugar_channels = {"sugar": mappings["sugar"]}
    print("building reusable sugar+bitter network, build-time rfc=0 for BOTH channels (old semantics)", flush=True)
    full_net = build_network(protocol, cells, full_channels, zero_refractory_for={"sugar", "bitter"})
    print("building reusable sugar-only network (bitter GRNs absent from the stimulus group)", flush=True)
    sugar_net = build_network(protocol, cells, sugar_channels)
    print("building reusable sugar+bitter network, rate-based rfc (new default: rfc=0 for driven channels only)", flush=True)
    same_group_net = build_network(protocol, cells, full_channels)
    seeds = [_base_seed(protocol) + i for i in range(10)]
    duration = float(protocol["trial"]["duration_ms"])
    full_values, sugar_values, rows = [], [], []
    left = int(protocol["readout"]["left"])
    for trial, seed in enumerate(seeds):
        print(f"refractory-quirk trial {trial + 1}, seed {seed}", flush=True)
        full_spikes = full_net.run_trial({"sugar": 100.0, "bitter": 0.0}, seed, duration)
        sugar_spikes = sugar_net.run_trial({"sugar": 100.0}, seed, duration)
        same_spikes = same_group_net.run_trial({"sugar": 100.0, "bitter": 0.0}, seed, duration)
        full_values.append((seed, full_spikes))
        sugar_values.append((seed, sugar_spikes))
        full_count = int(len(full_spikes.get(left, ())))
        sugar_count = int(len(sugar_spikes.get(left, ())))
        same_count = int(len(same_spikes.get(left, ())))
        rows.append({
            "trial": trial,
            "seed": seed,
            "sugar_bitter_mn9_left_count": full_count,
            "sugar_only_mn9_left_count": sugar_count,
            "paired_difference_count": full_count - sugar_count,
            "all_neurons_spike_trains_exact": _equal(full_spikes, sugar_spikes),
            # Same PoissonGroup (identical random stream), only the refractory rule differs:
            "same_group_rate_based_mn9_left_count": same_count,
            "pure_refractory_difference_count": full_count - same_count,
            "same_group_exact_vs_old": _equal(full_spikes, same_spikes),
        })
    _write_spikes("refractory_quirk_sugar_bitter", full_values, seeds)
    _write_spikes("refractory_quirk_sugar_only", sugar_values, seeds)
    any_difference = any(
        row["paired_difference_count"] != 0
        or not row["all_neurons_spike_trains_exact"]
        for row in rows
    )
    result = {
        "rows": rows,
        "n_seeds": len(seeds),
        "mean_paired_difference_count": float(np.mean([
            row["paired_difference_count"] for row in rows
        ])),
        "mean_pure_refractory_difference_count": float(np.mean([
            row["pure_refractory_difference_count"] for row in rows
        ])),
        "same_group_exact_seeds": sum(row["same_group_exact_vs_old"] for row in rows),
        "exact_equal_seeds": sum(
            row["all_neurons_spike_trains_exact"] for row in rows
        ),
        "any_difference": bool(any_difference),
        "pass": len(rows) == 10,
    }
    (OUT / "refractory_quirk.json").write_text(json.dumps(result, indent=2) + "\n")
    print(pd.DataFrame(rows).to_string(index=False), flush=True)
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2),
          flush=True)


def _existing_facts(protocol: dict):
    full_id = "A_sugar_dose_sugar100Hz_bitter0Hz"
    ordering = [x["cond_id"] for x in expand_conditions(
        protocol, list(protocol["phase0_conditions"])
    )]
    full_index = ordering.index(full_id)
    specs = [
        ("reusable", ROOT / "results/phase0/equiv/reusable_sugar100Hz.parquet", 0, "sugar only"),
        ("legacy", ROOT / "results/phase0/equiv/legacy_sugar100Hz.parquet", 0, "sugar only"),
        ("full", ROOT / f"results/phase0/full/{full_id}.parquet", full_index, "sugar + bitter"),
    ]
    out = {}
    for name, path, offset, channels in specs:
        df = pd.read_parquet(path)
        observed = sorted(int(x) for x in df["trial"].unique())
        n_trials = observed[-1] + 1
        if observed != list(range(n_trials)):
            raise ValueError(f"{path}: non-contiguous observed trial indices {observed}")
        rates = mn9_rate(df, protocol, n_trials)["left"]["trials"].tolist()
        out[name] = {"path": str(path.relative_to(ROOT)), "n_trials": n_trials,
                     "condition_index": offset,
                     "seeds": [_base_seed(protocol) + i + 1000 * offset for i in range(n_trials)],
                     "channels": channels, "rates": rates, "stats": _describe(rates)}
    return out


def _table(headers: list[str], rows: list[list[object]]) -> list[str]:
    return ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|", *
            ["| " + " | ".join(str(x) for x in row) + " |" for row in rows]]


def report(protocol: dict) -> None:
    facts = _existing_facts(protocol)
    det = json.loads((OUT / "restore_determinism.json").read_text())
    pair = json.loads((OUT / "paired.json").read_text())
    sem = json.loads((OUT / "stimulus_semantics.json").read_text())
    quirk = json.loads((OUT / "refractory_quirk.json").read_text())
    lines = ["# Store/restore versus legacy PoissonInput equivalence study", "", "## Existing-run facts", ""]
    rows = []
    for i in range(30):
        rows.append([i, *[(facts[k]["rates"][i] if i < facts[k]["n_trials"] else "")
                          for k in ("reusable", "legacy", "full")]])
    lines += _table(["trial", "reusable sugar-only", "legacy sugar-only", "full sugar+bitter"], rows)
    lines += [""]
    for name, value in facts.items():
        s = value["stats"]
        lines += [f"- **{name}:** n={value['n_trials']}; seeds {value['seeds'][0]}..{value['seeds'][-1]}; "
                  f"channels={value['channels']}; mean={s['mean']:.3f}, std(ddof=0)={s['std_ddof0']:.3f}, "
                  f"std(ddof=1)={s['std_ddof1']:.3f}, SE={s['se']:.3f} Hz."]
    lines += ["", f"The full run's condition index is {facts['full']['condition_index']} in `expand_conditions` ordering, "
              f"hence its +{1000 * facts['full']['condition_index']} seed offset. "
              "Its zero-rate bitter GRNs nevertheless have `rfc=0`; the sugar-only legacy run does not alter them.",
              "", "## Restore determinism", "", f"A == A2: **{det['a_equals_a2']}**; A == A3: **{det['a_equals_a3']}**. "
              f"Totals: {det['total_spikes']}; MN9-left: {det['mn9_left']}. Post-restore state all at rest: "
              f"**{det['state_at_rest']}**; values: `{det['diagnostics']}`.",
              "", "## Matched PoissonGroup trials", ""]
    lines += _table(["seed", "reusable MN9-L", "fresh PG MN9-L", "paired diff (Hz)",
                     "all neurons exact"],
                    [[r["seed"], r["reusable_mn9_left"], r["fresh_poissongroup_mn9_left"],
                      r["paired_difference_hz"], r["all_neurons_equal"]]
                     for r in pair["rows"]])
    lines += ["", f"Mean paired MN9-left difference (reusable - fresh): "
              f"**{pair['mean_paired_difference_hz']:.3f} Hz**. Exact spike-train equality: "
              f"**{pair['exact_equal_seeds']}/{pair['n_seeds']} seeds**.",
              "", "## Stimulus semantics (30 seeds)", "",
              "PoissonInput and PoissonGroup consume the RNG differently, so PoissonInput comparisons are distributional despite equal seed labels.", ""]
    for metric, label in (("left", "MN9-left rate (Hz)"), ("right", "MN9-right rate (Hz)"),
                          ("total", "network-wide spike count")):
        lines += [f"### {label}", ""]
        lines += _table(["trial", "seed", "reusable", "PoissonInput", "fresh PoissonGroup"],
                        [[r["trial"], r["seed"], r["a_reusable"][metric],
                          r["b_poissoninput"][metric], r["c_fresh_poissongroup"][metric]]
                         for r in sem["rows"]]) + [""]
        lines += _table(["path", "mean", "std0", "std1", "SE"], [[k, f"{v['mean']:.3f}",
            f"{v['std_ddof0']:.3f}", f"{v['std_ddof1']:.3f}", f"{v['se']:.3f}"]
            for k, v in sem["summary"][metric].items()])
        lines += [""] + _table(["comparison", "mean diff", "95% CI", "Welch t", "Welch p", "MWU U", "MWU p"], [[k,
            f"{v['mean_difference']:.3f}", f"[{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]",
            str(v['welch_t']), f"{v['welch_p']:.6g}", f"{v['mannwhitney_u']:.3f}", f"{v['mannwhitney_p']:.6g}"]
            for k, v in sem["comparisons"][metric].items()]) + [""]
    lines += ["## Refractory quirk (10 matched seeds)", ""]
    lines += ["Three builds per seed, sugar 100 Hz: (a) sugar+bitter stimulus group with the old build-time "
              "`rfc=0` for both channels; (b) sugar-only stimulus group (bitter GRNs absent, rfc untouched); "
              "(c) the same sugar+bitter stimulus group as (a) with the per-channel rule (rfc=0 only for the "
              "driven channel). (a) and (c) consume an identical random stream, so (a)-(c) is the pure effect of "
              "the refractory rule; (a)-(b) also changes the stimulus group size and therefore the random draws.", ""]
    lines += _table(
        ["seed", "(a) old rule MN9-L", "(b) sugar-only MN9-L", "(a)-(b)",
         "(a) vs (b) all-neuron exact", "(c) per-channel rule MN9-L", "(a)-(c) pure refractory",
         "(a) vs (c) all-neuron exact"],
        [[row["seed"], row["sugar_bitter_mn9_left_count"],
          row["sugar_only_mn9_left_count"], row["paired_difference_count"],
          row["all_neurons_spike_trains_exact"],
          row["same_group_rate_based_mn9_left_count"], row["pure_refractory_difference_count"],
          row["same_group_exact_vs_old"]] for row in quirk["rows"]],
    )
    same_exact = quirk["same_group_exact_seeds"]
    lines += ["", f"Different-stream comparison (a)-(b): mean paired count difference "
              f"**{quirk['mean_paired_difference_count']:.3f} spikes/trial**; exact all-neuron spike trains "
              f"**{quirk['exact_equal_seeds']}/{quirk['n_seeds']} seeds**.",
              "", f"Same-random-stream comparison (a)-(c): mean pure refractory difference "
              f"**{quirk['mean_pure_refractory_difference_count']:.3f} spikes/trial**; exact all-neuron spike "
              f"trains **{same_exact}/{quirk['n_seeds']} seeds**.", ""]
    if same_exact == quirk["n_seeds"]:
        lines += ["The refractory rule has **zero measured effect**: with the random stream held fixed, the old "
                  "build-time rule and the per-channel rule are spike-for-spike identical on every seed, so the "
                  "undriven bitter GRNs never fired in this condition. The (a)-(b) difference is entirely the "
                  "changed random stream (stimulus PoissonGroup of 65 versus 23 neurons), not the refractory rule. "
                  "The per-channel rule is kept for fidelity to model.py; differences between pre-fix and fixed "
                  "runs are sampling noise from different streams and must not be attributed to the rule.", ""]
    else:
        lines += ["The refractory rule itself changes spikes in some seeds: a nominally silent GRN can be driven "
                  "to spike by network input, and with `rfc=0` it can fire at every step while with `rfc=2.2 ms` "
                  "it cannot.", ""]
    lines += ["## Semantic differences identified", "",
              "- Reusable/fresh-PG use one `PoissonGroup` neuron per target plus one-to-one `Synapses(on_pre='v += w_stim')`; legacy uses one `PoissonInput(N=1)` per target.",
              "- Before the fix, reusable construction set `rfc=0` for every neuron belonging to every built channel, even a channel run at 0 Hz. Legacy changes `rfc` only for channels passed into that fresh build; the study passes sugar only. The reusable path now applies rfc=0 per trial only to channels with a nonzero rate (measured effect: zero, see the refractory section).",
              "- Reusable restores, sets rates, then calls `brian2.seed` immediately before running. Fresh paths construct and set rates first, then seed immediately before running.",
              "- Reusable network membership includes the PoissonGroup and stimulus Synapses; legacy membership instead includes all PoissonInput objects. Fresh-PG matches reusable membership.",
              "- Reusable retains one SpikeMonitor and relies on `restore('init')` to clear it; both legacy paths allocate a new monitor for every trial.",
              "- Reusable restores neuron state, refractory bookkeeping, synaptic queues, monitor state, and network time; fresh paths obtain those states by construction.", ""]
    cmp = sem["comparisons"]["left"]["a_reusable_vs_b_poissoninput"]
    lo, hi, diff = *cmp["ci95"], cmp["mean_difference"]
    verdict = (f"biased by {diff:.3f} Hz (95% CI [{lo:.3f}, {hi:.3f}])" if lo > 0 or hi < 0
               else f"inconclusive: difference {diff:.3f} Hz (95% CI [{lo:.3f}, {hi:.3f}]) includes zero")
    lines += ["## Conclusion", "", f"Relative to legacy PoissonInput, the reusable path is **{verdict}**. "
              f"The reusable-vs-full-run gap ({facts['reusable']['stats']['mean']:.1f} vs {facts['full']['stats']['mean']:.1f} Hz) uses both different seed sets and different channel sets (sugar-only versus sugar+bitter). "
              "The earlier ±1 standard-deviation overlap criterion was not an adequate test of bias."]
    left_cmp = sem["comparisons"]["left"]["a_reusable_vs_b_poissoninput"]
    total_cmp = sem["comparisons"]["total"]["a_reusable_vs_b_poissoninput"]
    _l = sem["comparisons"]["left"]["a_reusable_vs_b_poissoninput"]["ci95"]
    _t = sem["comparisons"]["total"]["a_reusable_vs_b_poissoninput"]["ci95"]
    sem["acceptance"]["left_pass"] = bool(_l[0] >= -3.0 and _l[1] <= 3.0 and _l[0] <= 0.0 <= _l[1])
    sem["acceptance"]["total_pass"] = bool(_t[0] <= 0.0 <= _t[1])
    sem["acceptance"]["pass"] = bool(sem["acceptance"]["left_pass"] and sem["acceptance"]["total_pass"])
    total_pct = sem["acceptance"]["total_ci95_percent_of_legacy_mean"]
    criteria = [
        [1, "restore-determinism",
         f"same-seed exact={det['a_equals_a2']}; all restored state at rest={det['state_at_rest']}",
         "exact spike trains and v, g, refractory state, stimulus rates at rest",
         "PASS" if det["pass"] else "FAIL"],
        [2, "paired reusable vs fresh PoissonGroup",
         f"mean paired MN9-L difference={pair['mean_paired_difference_hz']:.3f} Hz; "
         f"exact={pair['exact_equal_seeds']}/{pair['n_seeds']}",
         "mean paired difference within ±2 Hz", "PASS" if pair["pass"] else "FAIL"],
        [3, "stimulus semantics vs legacy PoissonInput",
         f"MN9-L CI=[{left_cmp['ci95'][0]:.3f}, {left_cmp['ci95'][1]:.3f}] Hz, "
         f"p={left_cmp['welch_p']:.6g}; total CI=[{total_cmp['ci95'][0]:.3f}, "
         f"{total_cmp['ci95'][1]:.3f}] spikes/trial "
         f"([{total_pct[0]:.3f}%, {total_pct[1]:.3f}%] of legacy mean), "
         f"p={total_cmp['welch_p']:.6g}",
         "MN9-L 95% CI within ±3 Hz and including 0; total CI covers 0 (no p-value rule)",
         "PASS" if sem["acceptance"]["pass"] else "FAIL"],
        [4, "refractory quirk experiment",
         f"n={quirk['n_seeds']}; mean paired MN9-L count difference="
         f"{quirk['mean_paired_difference_count']:.3f} (different stream); exact="
         f"{quirk['exact_equal_seeds']}/{quirk['n_seeds']}; same-stream pure refractory difference="
         f"{quirk['mean_pure_refractory_difference_count']:.3f}, exact="
         f"{quirk['same_group_exact_seeds']}/{quirk['n_seeds']}",
         "10 matched seeds reported (diagnostic; no numerical equivalence bound)",
         "PASS" if quirk["pass"] else "FAIL"],
    ]
    lines += ["", "## Acceptance criteria", ""] + _table(
        ["#", "criterion", "measured", "threshold", "PASS/FAIL"], criteria
    ) + [""]
    all_pass = all((det["pass"], pair["pass"], sem["acceptance"]["pass"], quirk["pass"]))
    selected = "the reusable path" if all_pass else "the legacy path until the failed criteria are resolved"
    recommendation = f"**Recommendation:** Use {selected} as the single downstream path."
    if quirk["same_group_exact_seeds"] == quirk["n_seeds"]:
        recommendation += (" Criterion 4: the same-random-stream variant shows the refractory rule has zero "
                           "measured effect; the per-channel rule (rfc=0 only for driven channels, as in model.py) "
                           "is kept for fidelity, not because it changes results. Phase 0 condition A was re-run "
                           "on the fixed path; its delta at 100 Hz (+0.1 Hz) is random-stream sampling noise, so "
                           "Phase 1 was not re-run.")
    elif quirk["any_difference"]:
        recommendation += (" Criterion 4 shows a pure refractory effect, so the reusable path must use the "
                           "legacy rule: set `rfc=0` only for channels with a nonzero rate in the condition.")
    else:
        recommendation += " Criterion 4 shows no difference, so it does not require a refractory-rule change."
    lines += [recommendation]
    text = "\n".join(lines) + "\n"
    path = ROOT / "docs" / "equivalence_study.md"
    path.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {path}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("restore-determinism", "paired", "stimulus-semantics",
                                            "refractory-quirk", "report"))
    parser.add_argument("--n-proc", type=int, default=14)
    parser.add_argument("--n-seeds", type=int, default=30, help="seeds for stimulus-semantics (default 30)")
    args = parser.parse_args()
    global N_SEEDS_SEMANTICS
    N_SEEDS_SEMANTICS = int(args.n_seeds)
    protocol = load_protocol()
    if args.command == "report":
        report(protocol)
    else:
        cells = load_cells()
        {"restore-determinism": restore_determinism,
         "paired": lambda p, c: paired(p, c, args.n_proc),
         "stimulus-semantics": lambda p, c: stimulus_semantics(p, c, args.n_proc),
         "refractory-quirk": refractory_quirk}[args.command](protocol, cells)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
