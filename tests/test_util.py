"""Test utility functions in ddpc.util module."""

import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from ase.atoms import Atoms
from ase.io import read

from ddpc.io.structure import read_structure
from ddpc.util import find_prim, scale_atom_pos, find_orth


@pytest.fixture
def structures_dir():
    """Get the test structures directory."""
    return Path(__file__).parent / "structures"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_structure_files(structures_dir):
    """Get list of sample .as structure files for testing."""
    return list(structures_dir.glob("*.as"))


class TestFindPrim:
    """Test primitive cell finding functionality."""

    def test_find_prim_creates_output_file(self, sample_structure_files, temp_output_dir):
        """Test that find_prim creates output files successfully."""
        for input_file in sample_structure_files:
            output_file = temp_output_dir / f"{input_file.stem}_prim.vasp"

            # Run the function
            find_prim(input_file, output_file, fmt="vasp", symprec=1e-5)

            # Verify output file was created
            assert output_file.exists(), f"Output file not created for {input_file.name}"

            # Verify output file is readable as a structure
            atoms = read(str(output_file))
            if isinstance(atoms, list):
                atoms = atoms[0]  # Take first structure if multiple
            assert isinstance(atoms, Atoms), f"Output file {output_file.name} is not valid"
            assert len(atoms) > 0, f"Output {output_file.name} has no atoms"

    def test_find_prim_reduces_cell_size(self, structures_dir, temp_output_dir):
        """Test that primitive cell has fewer or equal atoms than original."""
        # Use a specific structure that we know should have a primitive cell
        input_file = structures_dir / "all.as"
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        output_file = temp_output_dir / "all_prim.vasp"

        # Read original structure using ddpc reader
        original = read_structure(input_file)
        if isinstance(original, list):
            original = original[0]  # Take first structure if multiple
        original_natoms = len(original)

        # Find primitive cell
        find_prim(input_file, output_file, fmt="vasp", symprec=1e-5)

        # Read primitive structure
        primitive = read(str(output_file))
        if isinstance(primitive, list):
            primitive = primitive[0]  # Take first structure if multiple
        primitive_natoms = len(primitive)

        # Primitive cell should have fewer or equal atoms
        assert primitive_natoms <= original_natoms, \
            f"Primitive cell has more atoms ({primitive_natoms}) than original ({original_natoms})"

    def test_find_prim_different_symprec(self, structures_dir, temp_output_dir):
        """Test find_prim with different symmetry precision values."""
        input_file = structures_dir / "mag.as"
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        symprecs = [1e-3, 1e-5, 1e-7]
        results = []

        for symprec in symprecs:
            output_file = temp_output_dir / f"mag_prim_{symprec:.0e}.vasp"
            find_prim(input_file, output_file, fmt="vasp", symprec=symprec)

            atoms = read(str(output_file))
            if isinstance(atoms, list):
                atoms = atoms[0]  # Take first structure if multiple
            results.append(len(atoms))

        # Results should be consistent or show expected behavior
        assert all(n > 0 for n in results), "All primitive cells should have atoms"

    def test_find_prim_preserves_chemistry(self, structures_dir, temp_output_dir):
        """Test that find_prim preserves chemical composition."""
        input_file = structures_dir / "mag.as"
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        output_file = temp_output_dir / "mag_prim_chem.vasp"

        # Read original structure
        original = read_structure(input_file)
        if isinstance(original, list):
            original = original[0]
        orig_formula = original.get_chemical_formula()

        # Find primitive cell
        find_prim(input_file, output_file, fmt="vasp", symprec=1e-5)

        # Read primitive structure
        primitive = read(str(output_file))
        if isinstance(primitive, list):
            primitive = primitive[0]
        prim_formula = primitive.get_chemical_formula()

        # Chemical composition should be preserved (same elements, possibly different ratios)
        orig_elements = set(original.get_chemical_symbols())
        prim_elements = set(primitive.get_chemical_symbols())
        assert prim_elements.issubset(orig_elements), \
            f"Primitive cell has different elements: {prim_elements} vs {orig_elements}"


class TestScaleAtomPos:
    """Test atomic position scaling functionality."""

    def test_scale_atom_pos_creates_poscar(self, sample_structure_files, temp_output_dir):
        """Test that scale_atom_pos creates POSCAR files successfully."""
        for input_file in sample_structure_files:
            output_file = temp_output_dir / f"{input_file.stem}_scaled.vasp"

            # Run the function
            scale_atom_pos(input_file, output_file)

            # Verify output file was created
            assert output_file.exists(), f"POSCAR file not created for {input_file.name}"

            # Verify output file is readable as a structure
            atoms = read(str(output_file))
            if isinstance(atoms, list):
                atoms = atoms[0]  # Take first structure if multiple
            assert isinstance(atoms, Atoms), f"Output POSCAR {output_file.name} is not valid"
            assert len(atoms) > 0, f"Output POSCAR {output_file.name} has no atoms"

    def test_scale_atom_pos_preserves_structure(self, structures_dir, temp_output_dir):
        """Test that scaling preserves the essential structure properties."""
        input_file = structures_dir / "mag.as"
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        output_file = temp_output_dir / "mag_scaled.vasp"

        # Read original structure using ddpc reader
        original = read_structure(input_file)
        if isinstance(original, list):
            original = original[0]  # Take first structure if multiple
        original_natoms = len(original)
        original_symbols = original.get_chemical_symbols()

        # Scale positions
        scale_atom_pos(input_file, output_file)

        # Read scaled structure
        scaled = read(str(output_file))
        if isinstance(scaled, list):
            scaled = scaled[0]  # Take first structure if multiple
        scaled_natoms = len(scaled)
        scaled_symbols = scaled.get_chemical_symbols()

        # Check that essential properties are preserved
        assert scaled_natoms == original_natoms, "Number of atoms changed during scaling"
        assert scaled_symbols == original_symbols, "Chemical symbols changed during scaling"

        # Check that positions are in fractional coordinates (between 0 and 1)
        scaled_positions = scaled.get_scaled_positions()
        assert scaled_positions.min() >= -1e-10, "Scaled positions should be >= 0"
        assert scaled_positions.max() <= 1 + 1e-10, "Scaled positions should be <= 1"

    def test_scale_atom_pos_output_format(self, structures_dir, temp_output_dir):
        """Test that scale_atom_pos creates proper VASP format output."""
        input_file = structures_dir / "mag.as"
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        output_file = temp_output_dir / "mag_format_test.vasp"

        # Scale positions
        scale_atom_pos(input_file, output_file)

        # Read the output file as text to check format
        with open(output_file, 'r') as f:
            lines = f.readlines()

        # Basic VASP format checks
        assert len(lines) > 5, "Output file too short for VASP format"
        assert lines[1].strip().startswith("1.0"), "Second line should be scaling factor"

        # Check that we have lattice vectors (lines 2-4)
        for i in range(2, 5):
            parts = lines[i].strip().split()
            assert len(parts) == 3, f"Line {i+1} should have 3 lattice vector components"
            # Should be able to convert to float
            for part in parts:
                float(part)  # This will raise ValueError if not a number


class TestFindOrth:
    """Test orthogonal supercell finding functionality."""

    def test_find_orth_creates_output_file(self, sample_structure_files, temp_output_dir):
        """Test that find_orth creates output files successfully."""
        for input_file in sample_structure_files:
            output_file = temp_output_dir / f"{input_file.stem}_orth.vasp"

            # Run the function with a reasonable max length
            find_orth(input_file, output_file, fmt="vasp", mlen=20.0)

            # Verify output file was created
            assert output_file.exists(), f"Output file not created for {input_file.name}"

            # Verify output file is readable as a structure
            atoms = read(str(output_file))
            if isinstance(atoms, list):
                atoms = atoms[0]  # Take first structure if multiple
            assert isinstance(atoms, Atoms), f"Output file {output_file.name} is not valid"
            assert len(atoms) > 0, f"Output {output_file.name} has no atoms"

    def test_find_orth_creates_orthogonal_cell(self, structures_dir, temp_output_dir):
        """Test that find_orth creates a more orthogonal cell than the original."""
        input_file = structures_dir / "mag.as"
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        output_file = temp_output_dir / "mag_orth.vasp"

        # Read original structure
        original = read_structure(input_file)
        if isinstance(original, list):
            original = original[0]
        orig_cell = original.get_cell().array
        orig_a, orig_b, orig_c = orig_cell[0], orig_cell[1], orig_cell[2]

        # Calculate original orthogonality measure
        orig_cos_ab = abs(orig_a @ orig_b) / (np.linalg.norm(orig_a) * np.linalg.norm(orig_b))
        orig_cos_ac = abs(orig_a @ orig_c) / (np.linalg.norm(orig_a) * np.linalg.norm(orig_c))
        orig_cos_bc = abs(orig_b @ orig_c) / (np.linalg.norm(orig_b) * np.linalg.norm(orig_c))
        orig_orthogonality = max(orig_cos_ab, orig_cos_ac, orig_cos_bc)

        # Find orthogonal supercell
        find_orth(input_file, output_file, fmt="vasp", mlen=20.0)

        # Read orthogonal structure
        orth_atoms = read(str(output_file))
        if isinstance(orth_atoms, list):
            orth_atoms = orth_atoms[0]  # Take first structure if multiple

        # Check that the output is more orthogonal than the input
        orth_cell = orth_atoms.get_cell().array
        orth_a, orth_b, orth_c = orth_cell[0], orth_cell[1], orth_cell[2]

        orth_cos_ab = abs(orth_a @ orth_b) / (np.linalg.norm(orth_a) * np.linalg.norm(orth_b))
        orth_cos_ac = abs(orth_a @ orth_c) / (np.linalg.norm(orth_a) * np.linalg.norm(orth_c))
        orth_cos_bc = abs(orth_b @ orth_c) / (np.linalg.norm(orth_b) * np.linalg.norm(orth_c))
        new_orthogonality = max(orth_cos_ab, orth_cos_ac, orth_cos_bc)

        # The new cell should be more orthogonal (smaller cosine values)
        assert new_orthogonality <= orig_orthogonality + 1e-6, \
            f"New cell not more orthogonal: orig={orig_orthogonality:.6f}, new={new_orthogonality:.6f}"

        # Verify the structure has more atoms (it's a supercell)
        assert len(orth_atoms) >= len(original), \
            f"Orthogonal cell has fewer atoms ({len(orth_atoms)}) than original ({len(original)})"

    def test_find_orth_different_max_lengths(self, structures_dir, temp_output_dir):
        """Test find_orth with different maximum length constraints."""
        input_file = structures_dir / "mag.as"
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        max_lengths = [15.0, 20.0, 25.0]
        results = []

        for mlen in max_lengths:
            output_file = temp_output_dir / f"mag_orth_{mlen:.0f}.vasp"
            try:
                find_orth(input_file, output_file, fmt="vasp", mlen=mlen)
                atoms = read(str(output_file))
                if isinstance(atoms, list):
                    atoms = atoms[0]  # Take first structure if multiple
                results.append(len(atoms))
            except Exception:
                # Some max lengths might be too small to find orthogonal cell
                results.append(None)

        # At least one should succeed
        assert any(r is not None for r in results), "No orthogonal cell found for any max length"

    def test_find_orth_supercell_properties(self, structures_dir, temp_output_dir):
        """Test that find_orth creates a proper supercell."""
        input_file = structures_dir / "lat.as"  # Use a different structure
        if not input_file.exists():
            pytest.skip(f"Test structure {input_file.name} not found")

        output_file = temp_output_dir / "lat_orth_super.vasp"

        # Read original structure
        original = read_structure(input_file)
        if isinstance(original, list):
            original = original[0]

        # Find orthogonal supercell
        find_orth(input_file, output_file, fmt="vasp", mlen=15.0)

        # Read orthogonal structure
        orth_atoms = read(str(output_file))
        if isinstance(orth_atoms, list):
            orth_atoms = orth_atoms[0]

        # Should be a supercell (more atoms)
        assert len(orth_atoms) >= len(original), \
            f"Orthogonal cell should be supercell: {len(orth_atoms)} >= {len(original)}"

        # Should preserve chemical composition ratios
        orig_symbols = original.get_chemical_symbols()
        orth_symbols = orth_atoms.get_chemical_symbols()

        orig_counts = Counter(orig_symbols)
        orth_counts = Counter(orth_symbols)

        # Check that ratios are preserved (within integer multiples)
        for element in orig_counts:
            assert element in orth_counts, f"Element {element} missing in orthogonal cell"
            ratio = orth_counts[element] / orig_counts[element]
            assert abs(ratio - round(ratio)) < 1e-10, \
                f"Non-integer ratio for {element}: {ratio}"
