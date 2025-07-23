"""Tests for the write functions in ddpc.io.read.dspaw_as."""

from pathlib import Path

from ddpc.io.read import rescu_xyz as rrx
from ddpc.io.write import rescu_xyz as wrx


def test_write(snapshot):
    """Tests reading various as files."""
    for s in Path(f"{__file__}/../structures").resolve().iterdir():
        if s.name.endswith(".xyz"):
            original_lines = s.read_text().split("\n")
            atoms = rrx.read(s)
            write_lines = wrx.write("-", atoms)
            for line, write_line in zip(original_lines, write_lines.split("\n"), strict=True):
                if line.startswith("AtomType"):  # ignore comment line
                    continue
                # compare them, ignore white spaces
                ori_list = line.split()
                write_list = write_line.split()
                for o, w in zip(ori_list, write_list, strict=True):
                    # ignore trailing decimal
                    if o.strip() != w.strip() and abs(float(o.strip()) - float(w.strip())) > 1e-4:
                        raise ValueError(f"{ori_list} != {write_list}")

            assert f"{s.name}\n{atoms}" == snapshot
