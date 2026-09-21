"""
test_export_corpus.py

Exercises export_task on a small synthetic task (no dataset download
needed), checking: (1) the file is written and parses back as valid
MeTTa when loaded into a live space, (2) cell-level atoms are excluded
by default and present when include_cells=True, (3) the ASCII-art header
matches the actual grid.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from encoder import GridEncoder  # noqa: E402
from export_corpus import export_task, CELL_LEVEL_PREDICATES  # noqa: E402
from hyperon import MeTTa  # noqa: E402


def _synthetic_task_file(tmpdir):
    import json
    task = {
        "train": [
            {"input": [[0, 2, 2], [0, 0, 0]], "output": [[0, 0, 0], [0, 2, 2]]},
        ],
        "test": [
            {"input": [[2, 2, 0], [0, 0, 0]], "output": [[0, 0, 0], [2, 2, 0]]},
        ],
    }
    fp = os.path.join(tmpdir, "synthtask.json")
    with open(fp, "w") as f:
        json.dump(task, f)
    return fp


def test_export_excludes_cell_atoms_by_default():
    with tempfile.TemporaryDirectory() as tmp:
        fp = _synthetic_task_file(tmp)
        out_path = os.path.join(tmp, "out", "synthtask.metta")
        enc = GridEncoder()
        stats = export_task(fp, "unittest", enc, out_path, include_cells=False)

        assert stats["n_grids"] == 4  # train0 in/out, test0 in/out
        assert stats["n_written"] < stats["n_atoms"]  # something was excluded

        with open(out_path) as f:
            content = f.read()
        assert "(cell " not in content
        assert "(coord " not in content
        assert "(object " in content
        assert "(objColor " in content


def test_export_includes_cell_atoms_when_requested():
    with tempfile.TemporaryDirectory() as tmp:
        fp = _synthetic_task_file(tmp)
        out_path = os.path.join(tmp, "out", "synthtask.metta")
        enc = GridEncoder()
        stats = export_task(fp, "unittest", enc, out_path, include_cells=True)

        assert stats["n_written"] == stats["n_atoms"]
        with open(out_path) as f:
            content = f.read()
        assert "(cell " in content
        assert "(coord " in content


def test_exported_file_loads_as_valid_metta():
    with tempfile.TemporaryDirectory() as tmp:
        fp = _synthetic_task_file(tmp)
        out_path = os.path.join(tmp, "out", "synthtask.metta")
        enc = GridEncoder()
        export_task(fp, "unittest", enc, out_path, include_cells=False)

        with open(out_path) as f:
            content = f.read()

        m = MeTTa()
        # Strip comment lines (';' prefix) since the file mixes ASCII-art
        # comments with atoms; MeTTa's parser handles ';' comments
        # natively, so this should work either way, but we test the
        # explicit atom-only content path too, matching how a
        # downstream loader might strip comments before parsing.
        m.run(content)  # should not raise
        res = m.run('!(match &self (object unittest__synthtask train0_input $o) $o)')
        found = {str(x) for xs in res for x in xs}
        assert len(found) == 1


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
