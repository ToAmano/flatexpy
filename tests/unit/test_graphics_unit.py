"""Unit test cases for graphics processing functionality."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander, LatexExpandError


class TestGraphicsUnit:
    """Unit test cases for graphics processing functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = LatexExpandConfig()
        self.expander = LatexExpander(self.config)

    @patch("os.path.exists")
    @patch("os.path.join")
    def test_find_graphics_file_found(
        self, mock_join: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test finding graphics file when it exists."""
        mock_exists.return_value = True
        mock_join.return_value = "figures/image.png"

        result = self.expander._find_graphics_file("image", "figures")
        assert result == "figures/image.png"

    @patch("os.path.exists")
    def test_find_graphics_file_not_found(self, mock_exists: MagicMock) -> None:
        """Test finding graphics file when it doesn't exist."""
        mock_exists.return_value = False

        result = self.expander._find_graphics_file("nonexistent", "figures")
        assert result is None

    @patch("os.path.exists")
    def test_find_graphics_file_with_extension(self, mock_exists: MagicMock) -> None:
        """Test finding graphics file that already has extension."""

        def exists_side_effect(path: str) -> bool:
            return path == "figures/image.png"

        mock_exists.side_effect = exists_side_effect

        result = self.expander._find_graphics_file("image.png", "figures")
        assert result == "figures/image.png"

    @patch("os.path.exists")
    def test_find_graphics_file_multiple_extensions(
        self, mock_exists: MagicMock
    ) -> None:
        """Test finding graphics file with multiple possible extensions."""

        def exists_side_effect(path: str) -> bool:
            return path == "figures/image.jpg"  # Only .jpg exists

        mock_exists.side_effect = exists_side_effect

        result = self.expander._find_graphics_file("image", "figures")
        assert result == "figures/image.jpg"

    @patch("os.path.exists")
    def test_find_graphics_file_with_graphics_paths(
        self, mock_exists: MagicMock
    ) -> None:
        """Test finding graphics file using graphics paths."""
        # Set up graphics paths
        self.expander._graphics_paths = ["images", "figures"]

        def exists_side_effect(path: str) -> bool:
            return path == "images/chart.png"  # Only exists in images/

        mock_exists.side_effect = exists_side_effect

        result = self.expander._find_graphics_file("chart", ".")
        assert result == "images/chart.png"

    @patch("shutil.copy2")
    @patch("os.path.basename")
    @patch("os.path.join")
    def test_copy_graphics_file_success(
        self, mock_join: MagicMock, mock_basename: MagicMock, mock_copy: MagicMock
    ) -> None:
        """Test successful graphics file copying."""
        mock_basename.return_value = "image.png"
        mock_join.return_value = "output/image.png"

        self.expander._copy_graphics_file("source/image.png", "output")

        mock_copy.assert_called_once_with("source/image.png", "output/image.png")
        assert "source/image.png" in self.expander._collected_graphics

    @patch("shutil.copy2")
    def test_copy_graphics_file_already_copied(self, mock_copy: MagicMock) -> None:
        """Test that already copied graphics are skipped."""
        self.expander._collected_graphics.add("source/image.png")

        self.expander._copy_graphics_file("source/image.png", "output")

        mock_copy.assert_not_called()

    @patch("shutil.copy2")
    @patch("os.path.basename")
    @patch("os.path.join")
    def test_copy_graphics_file_io_error(
        self, mock_join: MagicMock, mock_basename: MagicMock, mock_copy: MagicMock
    ) -> None:
        """Test graphics file copying with IO error."""
        mock_basename.return_value = "image.png"
        mock_join.return_value = "output/image.png"
        mock_copy.side_effect = IOError("Permission denied")

        with pytest.raises(LatexExpandError):
            self.expander._copy_graphics_file("source/image.png", "output")

    def test_copy_graphics_file_real_files(self) -> None:
        """Test copying real graphics files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source file
            source_dir = os.path.join(temp_dir, "source")
            dest_dir = os.path.join(temp_dir, "dest")
            os.makedirs(source_dir)
            os.makedirs(dest_dir)

            source_file = os.path.join(source_dir, "test.png")
            with open(source_file, "wb") as f:
                f.write(b"fake PNG data")

            # Copy file
            self.expander._copy_graphics_file(source_file, dest_dir)

            # Verify file was copied
            dest_file = os.path.join(dest_dir, "test.png")
            assert os.path.exists(dest_file)

            # Verify content is the same
            with open(source_file, "rb") as sf, open(dest_file, "rb") as df:
                assert sf.read() == df.read()

            # Verify file is tracked as collected
            assert source_file in self.expander._collected_graphics

    def test_process_includegraphics_found(self) -> None:
        """Test processing includegraphics when file is found."""
        with (
            patch.object(self.expander, "_find_graphics_file") as mock_find,
            patch.object(self.expander, "_copy_graphics_file") as mock_copy,
        ):
            mock_find.return_value = "path/to/image.png"

            line = "\\includegraphics{image}"
            result = self.expander._process_includegraphics(line, ".", "output")

            assert "image.png" in result
            mock_copy.assert_called_once()

    def test_process_includegraphics_not_found(self) -> None:
        """Test processing includegraphics when file is not found."""
        with patch.object(self.expander, "_find_graphics_file") as mock_find:
            mock_find.return_value = None

            line = "\\includegraphics{missing}"
            result = self.expander._process_includegraphics(line, ".", "output")

            assert result == line

    def test_process_includegraphics_no_match(self) -> None:
        """Test processing line without includegraphics command."""
        line = "This is just text"
        result = self.expander._process_includegraphics(line, ".", "output")
        assert result == line

    def test_process_includegraphics_with_options(self) -> None:
        """Test processing includegraphics with options."""
        with (
            patch.object(self.expander, "_find_graphics_file") as mock_find,
            patch.object(self.expander, "_copy_graphics_file") as mock_copy,
        ):
            mock_find.return_value = "path/to/figure.pdf"

            line = "\\includegraphics[width=0.5\\textwidth]{figure}"
            result = self.expander._process_includegraphics(line, ".", "output")

            assert "\\includegraphics[width=0.5\\textwidth]{figure.pdf}" in result
            mock_copy.assert_called_once()

    def test_process_includegraphics_multiple_in_line(self) -> None:
        """Test processing line with multiple includegraphics commands."""
        with (
            patch.object(self.expander, "_find_graphics_file") as mock_find,
            patch.object(self.expander, "_copy_graphics_file") as mock_copy,
        ):
            # Only the first match will be processed (search() not findall())
            mock_find.return_value = "path/to/image1.png"

            line = "\\includegraphics{image1} and \\includegraphics{image2}"
            result = self.expander._process_includegraphics(line, ".", "output")

            assert "image1.png" in result
            assert "\\includegraphics{image2}" in result  # Second one unchanged
            mock_copy.assert_called_once()

    def test_find_graphics_file_real_files(self) -> None:
        """Test finding graphics files with real file system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory structure
            figures_dir = os.path.join(temp_dir, "figures")
            os.makedirs(figures_dir)

            # Create test images
            png_file = os.path.join(figures_dir, "chart.png")
            jpg_file = os.path.join(temp_dir, "photo.jpg")

            with open(png_file, "wb") as f:
                f.write(b"fake PNG")
            with open(jpg_file, "wb") as f:
                f.write(b"fake JPG")

            # Set up graphics paths
            self.expander._graphics_paths = ["figures"]

            # Test finding file in graphics path
            result1 = self.expander._find_graphics_file("chart", figures_dir)
            assert result1 == png_file

            # Test finding file in search directory
            result2 = self.expander._find_graphics_file("photo", temp_dir)
            assert result2 == jpg_file

            # Test file not found
            result3 = self.expander._find_graphics_file("missing", temp_dir)
            assert result3 is None
