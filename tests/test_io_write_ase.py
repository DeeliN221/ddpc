"""Test output to ase supported formats."""

from pathlib import Path
import tempfile
from ddpc.io.read import dspaw_as as rda
from ase.io import write

all_formats = [
    # "abinit-in", # not support fix atom
    "crystal",
    "cube",
    "dftb",
    # "espresso-in", # has to manually specify pseudopotential
    "extxyz",
    "findsym",
    "gamess-us-in",
    "gaussian-in",
    "gen",
    "gromacs",
    "gromos",
    "html",
    "json",
    "jsv",
    "lammps-data",
    "onetep-in",
    "proteindatabank",
    "py",
    "res",
    "rmc6f",
    "struct",
    "sys",
    "vasp",
    "vasp-xdatcar",
    "x3d",
    "xsd",
    "xsf",
    "xtd",
    "xyz",
]


def test_write(snapshot):
    """Tests reading various as files."""
    for s in sorted(Path(f"{__file__}/../structures").resolve().iterdir()):
        if s.name.endswith(".as"):
            atoms = rda.read(s)
            for fmt in all_formats:
                print(f"{s}: {fmt=}")
                tpf = tempfile.NamedTemporaryFile(delete=False)
                write(tpf.name, atoms, format=fmt)
                with open(tpf.name, "r") as f:
                    write_lines = f.read()
                    # print(write_lines)
