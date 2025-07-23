"""Tests for the export functions in ddpc.io.export."""

from pathlib import Path

import pytest

from ddpc.io.band import read_band
from ddpc.io.dos import read_dos


def get_file_info(file_path: Path):
    """Parse the file path to extract data type, spin type, and projection type."""
    parts = file_path.stem.split("_")
    spin_type = parts[0]
    data_ext_part = parts[1]  # e.g., 'pband' or 'dos'

    proj_type = ""
    data_type = ""

    if data_ext_part.startswith("p"):
        proj_type = "p"
        data_type = data_ext_part[1:]  # 'band' or 'dos'
    else:
        data_type = data_ext_part  # 'band' or 'dos'

    file_ext = file_path.suffix[1:]  # remove the leading dot

    return {
        "spin_type": spin_type,
        "proj_type": proj_type,
        "data_type": data_type,
        "file_ext": file_ext,
    }


def test_read_data_from_various_files(parametrized_data_file_path: Path, snapshot):
    """Tests reading various band/dos files using the parametrized fixture.

    It dynamically calls read_dos or read_band based on the file name.
    """
    file_info = get_file_info(parametrized_data_file_path)
    data_type = file_info["data_type"]
    band_mode = range(1, 6)
    dos_mode = range(1, 7)

    df = None
    if data_type == "dos":
        for mode in dos_mode:
            for fmt in ["7.2f", "8.3f", "9.4f"]:
                df = read_dos(parametrized_data_file_path, mode, fmt)
                assert df is not None, (
                    f"X: {parametrized_data_file_path.name}: \
                    {data_type=}, {mode=}, {fmt=}"
                )
                assert str(df) == snapshot
    elif data_type == "band":
        for mode in band_mode:
            for fmt in ["7.2f", "8.3f", "9.4f"]:
                df = read_band(parametrized_data_file_path, mode, fmt)
                assert df is not None, (
                    f"X: {parametrized_data_file_path.name}: \
                    {data_type=}, {mode=}, {fmt=}"
                )
                assert str(df) == snapshot
    else:
        pytest.fail(f"Unknown data type: {data_type} for file: {parametrized_data_file_path.name}")
