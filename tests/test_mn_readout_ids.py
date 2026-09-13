# SPDX-License-Identifier: MIT
"""Small source fixtures: these tests do not need the local paper or vendor data."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

from scripts.build_mn_readout_ids import (
    FLYWIRE,
    ROOT,
    build_document,
    select_mn_rows,
    validate_output_path,
)


LEFT_MN9 = "720575940660219265"
RIGHT_MN9 = "720575940618238523"


def row(body_id=LEFT_MN9, side="R", **extra):
    return {
        "Connectome": FLYWIRE,
        "Body_ID": body_id,
        "Root_Side": side,
        "Type": "MN9",
        "Target_Muscle": "9",
        **extra,
    }


def write_xlsx_fixture(path, rows):
    """Exercise the real raw-XML reader, with exact IDs stored as shared strings."""
    headers = ["Connectome", "Body_ID", "Root_Side", "Type", "Target_Muscle"]
    values = [headers, *[[r.get(k, "") for k in headers] for r in rows]]
    strings = []
    sheet_rows = []
    for number, values_row in enumerate(values, 1):
        cells = []
        for column, value in zip("ABCDE", values_row):
            index = len(strings)
            strings.append(str(value))
            cells.append(f'<c r="{column}{number}" t="s"><v>{index}</v></c>')
        sheet_rows.append(f'<row r="{number}">{"".join(cells)}</row>')
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            f'<workbook xmlns="{main}" xmlns:r="{rel}"><sheets>'
            '<sheet name="MNs" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships><Relationship Id="rId1" '
            'Target="worksheets/sheet1.xml"/></Relationships>',
        )
        archive.writestr(
            "xl/sharedStrings.xml",
            f'<sst xmlns="{main}">'
            + "".join(f"<si><t>{escape(s)}</t></si>" for s in strings)
            + "</sst>",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet xmlns="{main}"><sheetData>'
            + "".join(sheet_rows)
            + "</sheetData></worksheet>",
        )


class MnReadoutIdsTests(unittest.TestCase):
    def test_real_xml_keeps_precision_and_source_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            xlsx = Path(directory) / "source.xlsx"
            completeness = Path(directory) / "v783.csv"
            write_xlsx_fixture(
                xlsx,
                [row(), row(RIGHT_MN9, "L"), row("123", Connectome="MaleCNS")],
            )
            completeness.write_text(f",Completed\n{LEFT_MN9},True\n", encoding="utf-8")
            actual = build_document(xlsx, completeness)
            self.assertEqual(actual, build_document(xlsx, completeness))
            self.assertEqual(actual["schema_version"], "mn_readout_ids_v1")
            self.assertEqual(actual["n_neurons"], 2)
            self.assertEqual(actual["source"]["sheet"], "MNs")
            self.assertEqual(actual["source"]["filter"], {"Connectome": FLYWIRE})
            self.assertEqual(len(actual["source"]["sha256"]), 64)
            self.assertEqual(len(actual["source"]["completeness_sha256"]), 64)
            self.assertEqual(
                [r["Body_ID"] for r in actual["neurons"]], [LEFT_MN9, RIGHT_MN9]
            )
            self.assertEqual([r["in_v783"] for r in actual["neurons"]], [True, False])

    def test_preserves_unknown_muscle_literal(self):
        actual = select_mn_rows([row(Target_Muscle="Unknown")], {LEFT_MN9})
        self.assertEqual(actual[0]["Target_Muscle"], "Unknown")

    def test_excludes_other_connectomes_even_if_incomplete(self):
        actual = select_mn_rows([row(), {"Connectome": "MaleCNS"}], {LEFT_MN9})
        self.assertEqual(len(actual), 1)

    def test_rejects_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            select_mn_rows([row(), row()], {LEFT_MN9})

    def test_rejects_missing_fields_including_id(self):
        for field in ("Body_ID", "Root_Side", "Type", "Target_Muscle"):
            for value in (None, "", " "):
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(ValueError, field):
                        select_mn_rows([row(**{field: value})], {LEFT_MN9})

    def test_rejects_lossy_ids_and_invalid_side(self):
        for value in (float(LEFT_MN9), int(LEFT_MN9), "720575940660219265.0", "7.2e17"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Body_ID"):
                    select_mn_rows([row(value)], {LEFT_MN9})
        with self.assertRaisesRegex(ValueError, "Root_Side"):
            select_mn_rows([row(side="Unknown")], {LEFT_MN9})

    def test_rejects_empty_flywire_sheet(self):
        with self.assertRaisesRegex(ValueError, "no FlyWire"):
            select_mn_rows([], set())

    def test_protects_frozen_data_site_sim_and_inputs(self):
        xlsx = ROOT / "docs/papers/source.xlsx"
        completeness = ROOT / "vendor/source.csv"
        for output in (
            ROOT / "data/stim_protocol.json",
            ROOT / "data/grid_levels.json",
            ROOT / "data/lookup_table.json",
            ROOT / "data/cells.json",
            ROOT / "data/replay_neurons.json",
            ROOT / "site/data/any.json",
            ROOT / "sim/any.json",
            xlsx,
            completeness,
        ):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    validate_output_path(output, xlsx, completeness)
        validate_output_path(ROOT / "data/mn_readout_ids.json", xlsx, completeness)

    def test_checked_in_artifact_has_all_66_and_keeps_mn9_conventions(self):
        document = json.loads((ROOT / "data/mn_readout_ids.json").read_text(encoding="utf-8"))
        neurons = document["neurons"]
        self.assertEqual(document["n_neurons"], 66)
        self.assertEqual(len(neurons), 66)
        self.assertEqual(len({r["Body_ID"] for r in neurons}), 66)
        self.assertTrue(all(r["in_v783"] is True for r in neurons))
        self.assertTrue(all(isinstance(r["Body_ID"], str) for r in neurons))
        counts = Counter(r["Type"] for r in neurons)
        self.assertEqual(len(counts), 24)
        self.assertEqual({t: counts[t] for t in ("MN9", "MN11D", "MN11V", "CEM")},
                         {"MN9": 2, "MN11D": 2, "MN11V": 2, "CEM": 6})
        by_id = {r["Body_ID"]: r for r in neurons}
        self.assertEqual(by_id[LEFT_MN9]["Root_Side"], "R")
        self.assertEqual(by_id[RIGHT_MN9]["Root_Side"], "L")


if __name__ == "__main__":
    unittest.main()
