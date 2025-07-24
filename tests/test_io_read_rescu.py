"""Tests for the read functions in ddpc.io.read.dspaw_as."""

from pathlib import Path

from ddpc.io.read import rescu_xyz
from loguru import logger


def test_read(snapshot):
    """Tests reading various as files."""
    for s in sorted(Path(f"{__file__}/../structures").resolve().iterdir()):
        if s.name.endswith(".xyz"):
            atoms = rescu_xyz.read(s)
            logger.info(atoms)
            assert f"{s.name}\n{atoms}" == snapshot
