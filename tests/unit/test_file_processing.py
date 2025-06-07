"""Test cases for file processing functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander, LatexExpandError


class TestFileProcessing:
    """Test cases for file processing functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = LatexExpandConfig()
        self.expander = LatexExpander(self.config)

    @patch("pathlib.Path.exists")
    def test_resolve_file_path_exists(self, mock_exists: MagicMock) -> None:
        """Test file path resolution when file exists."""
        mock_exists.return_value = True
        result = self.expander._resolve_file_path("test.tex")
        assert result == Path("test.tex")

    @patch("pathlib.Path.exists")
    def test_resolve_file_path_with_tex_extension(self, mock_exists: MagicMock) -> None:
        """Test file path resolution with automatic .tex extension."""
        mock_exists.side_effect = [False, True]  # First call False, second True
        result = self.expander._resolve_file_path("test")
        assert result == Path("test.tex")

    @patch("pathlib.Path.exists")
    def test_resolve_file_path_not_found(self, mock_exists: MagicMock) -> None:
        """Test file path resolution when file doesn't exist."""
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError):
            self.expander._resolve_file_path("nonexistent.tex")

    def test_resolve_file_path_real_files(self) -> None:
        """Test file path resolution with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create test file
                test_file = "test.tex"
                with open(test_file, "w") as f:
                    f.write("test content")

                # Test existing file
                result = self.expander._resolve_file_path(test_file)
                assert result == Path(test_file)
                assert result.exists()

                # Test file without extension
                result2 = self.expander._resolve_file_path("test")
                assert result2 == Path("test.tex")
                assert result2.exists()

            finally:
                os.chdir(original_cwd)

    @patch("builtins.open", new_callable=mock_open, read_data="Line 1\nLine 2\n")
    def test_read_file_success(self, mock_file: MagicMock) -> None:
        """Test successful file reading."""
        result = self.expander._read_file("test.tex")
        assert result == ["Line 1\n", "Line 2\n"]
        mock_file.assert_called_once_with("test.tex", "r", encoding="utf-8")

    @patch("builtins.open")
    def test_read_file_io_error(self, mock_open_func: MagicMock) -> None:
        """Test file reading with IO error."""
        mock_open_func.side_effect = IOError("Permission denied")

        with pytest.raises(LatexExpandError, match="Failed to read file"):
            self.expander._read_file("test.tex")

    def test_read_file_real_file(self) -> None:
        """Test reading real file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.tex")
            test_content = (
                "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}\n"
            )

            with open(test_file, "w") as f:
                f.write(test_content)

            result = self.expander._read_file(test_file)
            assert result == test_content.splitlines(keepends=True)

    @patch("builtins.open", new_callable=mock_open, read_data="Line 1\nLine 2\n")
    @patch("os.path.abspath")
    def test_flatten_file_basic(
        self, mock_abspath: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test basic file flattening."""
        mock_abspath.return_value = "/abs/path/file.tex"

        result = self.expander._flatten_file("file.tex", ".", "output")
        assert "Line 1\nLine 2\n" == result

    @patch("builtins.open", new_callable=mock_open, read_data="Line 1\nLine 2\n")
    @patch("os.path.abspath")
    def test_flatten_file_already_visited(
        self, mock_abspath: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test that already visited files are skipped."""
        mock_abspath.return_value = "/abs/path/file.tex"
        self.expander._visited_files.add("/abs/path/file.tex")

        result = self.expander._flatten_file("file.tex", ".", "output")
        assert result == ""
        # File should not be opened since it was already visited
        mock_file.assert_not_called()

    def test_flatten_file_with_comments(self) -> None:
        """Test file flattening with comment handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.tex")
            test_content = "\\documentclass{article}\n% This is a comment\n\\begin{document}\nHello\n% Another comment\n\\end{document}\n"

            with open(test_file, "w") as f:
                f.write(test_content)

            # Test with comment ignoring enabled (default)
            result = self.expander._flatten_file(test_file, temp_dir, temp_dir)
            assert "% This is a comment" in result
            assert "% Another comment" in result
            assert "Hello" in result

    def test_flatten_file_encoding(self) -> None:
        """Test file flattening with different encoding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.tex")
            test_content = "Special chars: ñáéíóú\n"

            # Write with UTF-8
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            # Read with UTF-8 configuration
            config = LatexExpandConfig(output_encoding="utf-8")
            expander = LatexExpander(config)

            result = expander._flatten_file(test_file, temp_dir, temp_dir)
            assert "ñáéíóú" in result
