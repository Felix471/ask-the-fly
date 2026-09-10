#!/usr/bin/env python3
"""Extract and validate the frozen FlyWire cell sets without executing notebooks."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "vendor/fly-brain/code/paper-phil-drosophila/example.ipynb"
FIGURES = ROOT / "vendor/fly-brain/code/paper-phil-drosophila/figures.ipynb"
BENCHMARK = ROOT / "vendor/fly-brain/code/benchmark.py"
COMPLETENESS_REL = "vendor/fly-brain/data/2025_Completeness_783.csv"
COMPLETENESS = ROOT / COMPLETENESS_REL


def code_sources(path: Path) -> list[str]:
    """Return code-cell sources from a notebook parsed strictly as JSON."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


def notebook_lists(sources: list[str], name: str) -> list[list[int]]:
    """Find all ``name = [integer, ...]`` assignments in code cells."""
    pattern = re.compile(rf"(?m)^\s*{re.escape(name)}\s*=\s*(\[[\s\S]*?\])")
    values: list[list[int]] = []
    for source in sources:
        for match in pattern.finditer(source):
            value = ast.literal_eval(match.group(1))
            if not isinstance(value, list) or not all(
                isinstance(item, int) and not isinstance(item, bool) for item in value
            ):
                raise ValueError(f"{name} is not a list of integers")
            values.append(value)
    if not values:
        raise ValueError(f"No assignment found for {name}")
    return values


def notebook_scalars(sources: list[str], name: str) -> list[int]:
    """Find all ``name = integer`` assignments in code cells."""
    pattern = re.compile(rf"(?m)^\s*{re.escape(name)}\s*=\s*(\d+)\b")
    values = [int(match.group(1)) for source in sources for match in pattern.finditer(source)]
    if not values:
        raise ValueError(f"No assignment found for {name}")
    return values


def require_identical(values: list[Any], name: str) -> Any:
    first = values[0]
    if any(value != first for value in values[1:]):
        raise ValueError(f"Repeated assignments for {name} are not identical")
    return first


def require_ids(ids: list[int], expected: int, name: str) -> list[int]:
    if len(ids) != expected:
        raise ValueError(f"{name}: expected {expected} IDs, found {len(ids)}")
    if len(set(ids)) != len(ids):
        raise ValueError(f"{name}: duplicate IDs found")
    return sorted(ids)


def benchmark_sugar_ids(path: Path) -> list[int]:
    """Parse EXPERIMENTS from source with AST; never import benchmark.py."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXPERIMENTS"
            for target in node.targets
        ):
            experiments = ast.literal_eval(node.value)
            return experiments["sugar"]["neu_exc"]
    raise ValueError("No EXPERIMENTS assignment found in benchmark.py")


def validation(ids: list[int], available: set[int]) -> dict[str, Any]:
    missing = sorted(set(ids) - available)
    return {
        "count": len(ids),
        "present_count": len(ids) - len(missing),
        "missing_count": len(missing),
        "missing_ids": missing,
    }


def overlap(left: list[int], right: list[int]) -> dict[str, Any]:
    shared = sorted(set(left) & set(right))
    return {"count": len(shared), "ids": shared}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def stimulation_protocol(sets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Return the frozen Phase-0/Phase-1 stimulation contract."""
    phase1_base = list(range(0, 201, 20))
    return {
        "protocol_version": "1.0",
        "data_version": "flywire_v783",
        "connectivity_file": "vendor/fly-brain/data/2025_Connectivity_783.parquet",
        "completeness_file": COMPLETENESS_REL,
        "model": {
            "source": "vendor/fly-brain/code/paper-phil-drosophila/model.py (MIT, Shiu et al. 2024)",
            "v_0_mV": -52,
            "v_rst_mV": -52,
            "v_th_mV": -45,
            "t_mbr_ms": 20,
            "tau_ms": 5,
            "t_rfc_ms": 2.2,
            "t_dly_ms": 1.8,
            "w_syn_mV": 0.275,
            "f_poi": 250,
            "integration": "linear",
            "dt_ms": 0.1,
        },
        "trial": {
            "duration_ms": 1000,
            "n_trials": 30,
            "sanity_n_trials": 5,
            "seed_rule": "trial i uses seed base_seed+i; base_seed=20260910",
        },
        "stimulus": {
            "type": "PoissonInput per GRN, N=1, weight=w_syn*f_poi, refractory of stimulated GRNs set to 0",
            "channels": {
                "sugar": {"cell_set": "sugar", "count": sets["sugar"]["count"]},
                "bitter": {"cell_set": "bitter", "count": sets["bitter"]["count"]},
                "water": {"cell_set": "water", "count": sets["water"]["count"], "phase": "1"},
                "ir94e": {"cell_set": "ir94e", "count": sets["ir94e"]["count"], "phase": "1"},
            },
        },
        "readout": {
            "neuron": "MN9",
            "left": sets["mn9"]["left"],
            "right": sets["mn9"]["right"],
            "aggregation": "left_only",
            "aggregation_rationale": "Paper (Shiu 2024) stimulates right-hemisphere sugar GRNs and reads the contralateral LEFT MN9 (figures.ipynb id_mn9 = 720575940660219265). We follow the paper. Right MN9 is recorded and reported but not used for gates. FROZEN for the whole project.",
            "rate_definition": "spikes in [0, duration] / duration, mean over trials; also report std over trials",
        },
        "phase0_conditions": {
            "A_sugar_dose": {"sugar_hz": [25, 50, 100, 200], "bitter_hz": 0},
            "B_bitter_suppression": {
                "sugar_hz": 200,
                "bitter_hz": [0, 25, 50, 100, 200],
            },
            "C_bitter_alone": {"sugar_hz": 0, "bitter_hz": [25, 50, 100, 200]},
            "D_baseline": {"sugar_hz": 0, "bitter_hz": 0},
            "A_prime_sugar_bench21": {
                "cell_set": "sugar_bench21",
                "sugar_hz": [25, 50, 100, 200],
            },
        },
        "phase1_characterization": {
            "sugar_hz": phase1_base,
            "bitter_hz": phase1_base,
            "water_hz": list(range(0, 261, 20)),
            "ir94e_hz": phase1_base,
            "pairs": ["sugar_x_bitter", "sugar_x_water", "sugar_x_ir94e"],
        },
        "notes": [
            "Paper calibrated w_syn on FlyWire v630; we run v783 only, absolute Hz may differ.",
            "Model baseline firing is 0 Hz by construction (no intrinsic activity); condition D measures it anyway.",
        ],
    }


def main() -> int:
    example_sources = code_sources(EXAMPLE)
    figure_sources = code_sources(FIGURES)

    sugar = require_ids(notebook_lists(example_sources, "sugar_GRNs")[0], 23, "sugar_GRNs")
    bitter = require_ids(notebook_lists(example_sources, "bitter_GRNs")[0], 42, "bitter_GRNs")
    mn9_left = require_identical(notebook_scalars(example_sources, "MN9_left"), "MN9_left")
    mn9_right = require_identical(notebook_scalars(example_sources, "MN9_right"), "MN9_right")

    sugar_fig = require_ids(
        require_identical(notebook_lists(figure_sources, "neu_sugar"), "neu_sugar"),
        21,
        "neu_sugar",
    )
    sugar_left = require_ids(notebook_lists(figure_sources, "neu_sugar_left")[0], 10, "neu_sugar_left")
    bitter_fig = require_ids(notebook_lists(figure_sources, "neu_bitter")[0], 21, "neu_bitter")
    ir94e = require_ids(notebook_lists(figure_sources, "neu_ir94e")[0], 18, "neu_ir94e")
    water = require_ids(notebook_lists(figure_sources, "neu_water")[0], 18, "neu_water")
    figure_mn9_left = require_identical(notebook_scalars(figure_sources, "id_mn9"), "id_mn9")
    figure_mn9 = require_ids(notebook_lists(figure_sources, "ids_mn9")[0], 2, "ids_mn9")
    sugar_bench = require_ids(benchmark_sugar_ids(BENCHMARK), 21, "EXPERIMENTS.sugar.neu_exc")

    first_column = pd.read_csv(COMPLETENESS, usecols=[0]).iloc[:, 0]
    available = {int(value) for value in first_column.dropna()}

    sets = {
        "sugar": {
            "ids": sugar,
            "count": 23,
            "source": "example.ipynb::sugar_GRNs",
            "role": "primary sugar set (Phase 0 gates)",
        },
        "sugar_bench21": {
            "ids": sugar_bench,
            "count": 21,
            "source": "benchmark.py::EXPERIMENTS.sugar.neu_exc",
            "role": "appendix run A' only",
        },
        "sugar_fig21": {
            "ids": sugar_fig,
            "count": 21,
            "source": "figures.ipynb::neu_sugar",
            "role": "paper figures right-hemisphere sugar set",
            "note": (
                "identical to sugar_bench21"
                if sugar_fig == sugar_bench
                else "not identical to sugar_bench21"
            ),
        },
        "sugar_left10": {
            "ids": sugar_left,
            "count": 10,
            "source": "figures.ipynb::neu_sugar_left",
            "role": "paper figures left-hemisphere sugar set",
        },
        "bitter": {
            "ids": bitter,
            "count": 42,
            "source": "example.ipynb::bitter_GRNs",
            "role": "primary bitter set",
        },
        "bitter_fig21": {
            "ids": bitter_fig,
            "count": 21,
            "source": "figures.ipynb::neu_bitter",
            "role": "paper figures bitter set",
        },
        "water": {
            "ids": water,
            "count": 18,
            "source": "figures.ipynb::neu_water",
            "role": "Phase 1 only",
        },
        "ir94e": {
            "ids": ir94e,
            "count": 18,
            "source": "figures.ipynb::neu_ir94e",
            "role": "Phase 1 only",
        },
        "mn9": {
            "left": mn9_left,
            "right": mn9_right,
            "source": "example.ipynb",
            "note": "figures.ipynb lists 720575940645521262 as right MN9; that ID is absent from v783",
        },
    }

    validations = {
        name: validation(entry["ids"], available)
        for name, entry in sets.items()
        if "ids" in entry
    }
    validations["mn9"] = validation([mn9_left, mn9_right], available)
    validations["mn9_figures"] = validation(figure_mn9, available)

    overlaps = {
        "sugar_vs_sugar_fig21": overlap(sugar, sugar_fig),
        "sugar_vs_sugar_bench21": overlap(sugar, sugar_bench),
        "sugar_fig21_vs_sugar_bench21": overlap(sugar_fig, sugar_bench),
        "sugar23_fig21_bench21_common": {
            "count": len(set(sugar) & set(sugar_fig) & set(sugar_bench)),
            "ids": sorted(set(sugar) & set(sugar_fig) & set(sugar_bench)),
        },
        "sugar_vs_sugar_left10": overlap(sugar, sugar_left),
        "sugar_fig21_vs_sugar_left10": overlap(sugar_fig, sugar_left),
        "sugar_bench21_vs_sugar_left10": overlap(sugar_bench, sugar_left),
        "bitter_vs_bitter_fig21": overlap(bitter, bitter_fig),
    }

    cells = {
        "data_version": "flywire_v783",
        "completeness_file": COMPLETENESS_REL,
        "sets": sets,
        "validation": validations,
        "overlaps": overlaps,
    }
    write_json(ROOT / "data/cells.json", cells)
    write_json(ROOT / "data/stim_protocol.json", stimulation_protocol(sets))

    print("Validation against flywire_v783")
    for name, result in validations.items():
        print(
            f"  {name}: count={result['count']}, present={result['present_count']}, "
            f"missing={result['missing_count']}, missing_ids={result['missing_ids']}"
        )
    print("Overlaps")
    for name, result in overlaps.items():
        print(f"  {name}: count={result['count']}, ids={result['ids']}")
    print(f"  sugar_fig21_identical_to_sugar_bench21: {sugar_fig == sugar_bench}")
    print(f"  figures_id_mn9: {figure_mn9_left}")

    fatal_ids = sugar + bitter + [mn9_left, mn9_right]
    fatal_missing = sorted(set(fatal_ids) - available)
    if fatal_missing:
        print(f"ERROR: required primary IDs missing from v783: {fatal_missing}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, SyntaxError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
