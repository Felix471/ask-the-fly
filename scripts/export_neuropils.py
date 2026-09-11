#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write site/data/neuropils.json: 2D anterior-view outlines of neuropil groups.

Source meshes: JFRC2NP neuropil surfaces (Ito et al. 2014 nomenclature) transformed
into FlyWire space, as distributed in fafbseg-py's data folder (JFRC2NP.surf.fw.zip),
unpacked into data/external/neuropils/ (gitignored). Each group is the union of its
member meshes; the outline is the 2D convex hull of the projected vertices, in the
same normalised frame as site/data/neuropils.json's sibling neurons.json ("frame").
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MESH_DIR = ROOT / "data" / "external" / "neuropils"
NEURONS_JSON = ROOT / "site" / "data" / "neurons.json"
OUT = ROOT / "site" / "data" / "neuropils.json"

GROUPS = [
    ("sez", "SEZ", "食道下区", ["GNG", "SAD", "AMMC_L", "AMMC_R", "PRW"]),
    ("al_l", "AL", "触角叶", ["AL_L"]),
    ("al_r", "AL", "触角叶", ["AL_R"]),
    ("mb_l", "MB", "蘑菇体", ["MB_CA_L", "MB_PED_L", "MB_ML_L", "MB_VL_L"]),
    ("mb_r", "MB", "蘑菇体", ["MB_CA_R", "MB_PED_R", "MB_ML_R", "MB_VL_R"]),
    ("cx", "CX", "中央复合体", ["FB", "EB", "PB", "NO"]),
    ("ol_l", "OL", "视叶", ["ME_L", "LO_L", "LOP_L", "LA_L", "AME_L"]),
    ("ol_r", "OL", "视叶", ["ME_R", "LO_R", "LOP_R", "LA_R", "AME_R"]),
]


def read_ply_vertices(path: Path) -> np.ndarray:
    data = path.read_bytes()
    end = data.index(b"end_header\n") + len(b"end_header\n")
    header = data[:end].decode("ascii").splitlines()
    n_vertex = next(int(line.split()[2]) for line in header if line.startswith("element vertex"))
    fmt = next(line.split()[1] for line in header if line.startswith("format"))
    props = [line.split()[2] for line in header if line.startswith("property float") or line.startswith("property double")]
    if fmt != "binary_little_endian" or len(props) < 3:
        raise ValueError(f"{path}: unsupported PLY ({fmt}, {props})")
    dtype = np.dtype([(name, "<f4") for name in props[: len(props)]])
    vertices = np.frombuffer(data, dtype=dtype, count=n_vertex, offset=end)
    return np.column_stack([vertices["x"], vertices["y"], vertices["z"]]).astype(np.float64)


def convex_hull(points: np.ndarray) -> np.ndarray:
    """Andrew's monotone chain; returns the hull in counter-clockwise order."""
    pts = np.unique(points, axis=0)
    if len(pts) < 3:
        return pts
    order = np.lexsort((pts[:, 1], pts[:, 0]))
    pts = pts[order]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def simplify(polygon: np.ndarray, tolerance: float) -> np.ndarray:
    """Douglas-Peucker on a closed ring (tolerance in normalised units)."""
    if len(polygon) < 4:
        return polygon
    # Closed ring: split at the vertex farthest from vertex 0, simplify both open
    # halves, then join (plain Douglas-Peucker degenerates when start == end).
    far = int(np.argmax(np.hypot(*(polygon - polygon[0]).T)))
    if far == 0:
        return polygon

    def dp(points):
        if len(points) < 3:
            return points
        a, b = points[0], points[-1]
        ab = b - a
        norm = np.hypot(*ab) or 1e-12
        rel = points - a
        dist = np.abs(ab[0] * rel[:, 1] - ab[1] * rel[:, 0]) / norm
        i = int(np.argmax(dist))
        if dist[i] > tolerance:
            left = dp(points[: i + 1])
            right = dp(points[i:])
            return np.vstack([left[:-1], right])
        return np.array([a, b])

    first = dp(polygon[: far + 1])
    second = dp(np.vstack([polygon[far:], polygon[:1]]))
    return np.vstack([first[:-1], second[:-1]])


def main() -> int:
    neurons = json.loads(NEURONS_JSON.read_text(encoding="utf-8"))
    frame = neurons.get("frame")
    if not frame:
        raise SystemExit("site/data/neurons.json has no 'frame'; re-run scripts/export_neurons.py first")
    lo = np.array(frame["lo"], dtype=np.float64)
    span = float(frame["span"])
    offset = np.array(frame["offset"], dtype=np.float64)
    voxel = np.array(frame.get("voxel_nm", [4.0, 4.0]), dtype=np.float64)

    groups = []
    for key, label_en, label_zh, members in GROUPS:
        points = []
        for member in members:
            path = MESH_DIR / f"{member}.ply"
            if not path.exists():
                print(f"warning: missing mesh {member}")
                continue
            xyz = read_ply_vertices(path)
            points.append(xyz[:, :2] / voxel)  # nm -> FlyWire voxel units (x, y at 4 nm)
        if not points:
            continue
        xy = np.vstack(points)
        norm = (xy - lo) / span + offset
        hull = convex_hull(norm)
        hull = simplify(hull, 0.002)
        centroid = norm.mean(axis=0)
        groups.append({
            "key": key, "label_en": label_en, "label_zh": label_zh, "members": members,
            "polygon": [[round(float(x), 4), round(float(y), 4)] for x, y in hull],
            "label_at": [round(float(centroid[0]), 4), round(float(centroid[1]), 4)],
        })
    payload = {
        "schema_version": "neuropils_v1",
        "view": "anterior (x mediolateral, y dorsoventral), same frame as neurons.json",
        "source": ("JFRC2NP neuropil surfaces (Ito et al. 2014 nomenclature) transformed to FlyWire space, "
                   "from fafbseg-py data/JFRC2NP.surf.fw.zip; 2D convex hull of each group's projected vertices"),
        "groups": groups,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT}: {len(groups)} groups, {OUT.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
