"""Test main function in ddpc.util.find_prim."""

from pathlib import Path
from ddpc.util import find_prim, scale_atom_pos, find_orth


s_folder = Path(f"{__file__}/../structures").resolve()
(s_folder / "output").mkdir(exist_ok=True, parents=True)


def test_find_prim(snapshot):
    """Follow snakemake inp, out, par convention."""
    for s in s_folder.iterdir():
        # xyz has no lattice info
        if s.name.endswith(".as"):
            p = s
            op = s.parent / "output" / s.with_suffix(".prim").name
            fmt = "vasp"
            symprec = 1e-5

            find_prim(p, op, fmt, symprec)
            assert f"{s=}\n{op=}" == snapshot


def test_scale_atom_pos(snapshot):
    """Follow snakemake inp, out, par convention."""
    for s in s_folder.iterdir():
        # xyz has no lattice info
        if s.name.endswith(".as"):
            p = s
            op = s.parent / "output" / s.with_suffix(".POSCAR").name
            scale_atom_pos(p, op)
            assert f"{s=}\n{op=}" == snapshot


def test_find_orth(snapshot):
    """Follow snakemake inp, out, par convention."""
    for s in s_folder.iterdir():
        # xyz has no lattice info
        if s.name.endswith(".as"):
            p = s
            op = s.parent / "output" / s.with_suffix(".orth").name
            fmt = "vasp"
            mlen = 15.0

            find_orth(p, op, fmt, mlen)
            assert f"{s=}\n{op=}" == snapshot
