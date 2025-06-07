"""Test cases for utility functions."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flatexpy.flatexpy_core import _create_output_dir


class TestCreateOutputDir:
    """Test cases for _create_output_dir utility function."""

    @patch("os.makedirs")
    @patch("pathlib.Path.exists")
    def test_create_output_dir_success(
        self, mock_exists: MagicMock, mock_makedirs: MagicMock
    ) -> None:
        """Test successful output directory creation."""
        mock_exists.return_value = False
        _create_output_dir("output", False)
        mock_makedirs.assert_called_once_with(Path("output"), exist_ok=True)

    @patch("pathlib.Path.exists")
    def test_create_output_dir_exists_no_overwrite(
        self, mock_exists: MagicMock
    ) -> None:
        """Test output directory creation when directory exists and overwrite is False."""
        mock_exists.return_value = True

        with pytest.raises(FileExistsError, match="Directory exists: output"):
            _create_output_dir("output", False)

    @patch("os.makedirs")
    @patch("pathlib.Path.exists")
    def test_create_output_dir_exists_with_overwrite(
        self, mock_exists: MagicMock, mock_makedirs: MagicMock
    ) -> None:
        """Test output directory creation when directory exists and overwrite is True."""
        mock_exists.return_value = True
        _create_output_dir("output", True)
        mock_makedirs.assert_called_once_with(Path("output"), exist_ok=True)

    @patch("os.makedirs")
    @patch("pathlib.Path.exists")
    def test_create_output_dir_not_exists_with_overwrite(
        self, mock_exists: MagicMock, mock_makedirs: MagicMock
    ) -> None:
        """Test output directory creation when directory doesn't exist and overwrite is True."""
        mock_exists.return_value = False
        _create_output_dir("output", True)
        mock_makedirs.assert_called_once_with(Path("output"), exist_ok=True)

    def test_create_output_dir_with_nested_path(self) -> None:
        """Test directory creation with nested path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "level1", "level2", "output")
            _create_output_dir(nested_path, False)
            assert os.path.exists(nested_path)
            assert os.path.isdir(nested_path)

    def test_create_output_dir_absolute_path(self) -> None:
        """Test directory creation with absolute path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "absolute_output")
            _create_output_dir(output_path, False)
            assert os.path.exists(output_path)
            assert os.path.isdir(output_path)
