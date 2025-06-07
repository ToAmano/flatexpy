"""Test cases for LatexExpandConfig dataclass."""

import pytest

from flatexpy.flatexpy_core import LatexExpandConfig


class TestLatexExpandConfig:
    """Test cases for LatexExpandConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that default configuration values are set correctly."""
        config = LatexExpandConfig()
        assert config.graphic_extensions == [".pdf", ".png", ".jpg", ".jpeg", ".eps"]
        assert config.ignore_commented_lines is True
        assert config.root_directory == "."
        assert config.output_encoding == "utf-8"

    def test_custom_values(self) -> None:
        """Test that custom configuration values are set correctly."""
        config = LatexExpandConfig(
            graphic_extensions=[".png", ".svg"],
            ignore_commented_lines=False,
            root_directory="/custom/path",
            output_encoding="latin-1",
        )
        assert config.graphic_extensions == [".png", ".svg"]
        assert config.ignore_commented_lines is False
        assert config.root_directory == "/custom/path"
        assert config.output_encoding == "latin-1"

    def test_field_types(self) -> None:
        """Test that configuration fields have correct types."""
        config = LatexExpandConfig()
        assert isinstance(config.graphic_extensions, list)
        assert isinstance(config.ignore_commented_lines, bool)
        assert isinstance(config.root_directory, str)
        assert isinstance(config.output_encoding, str)

    def test_graphic_extensions_list_modification(self) -> None:
        """Test that graphic_extensions list can be modified."""
        config = LatexExpandConfig()
        original_extensions = config.graphic_extensions.copy()

        # Modify the list
        config.graphic_extensions.append(".svg")

        # Verify modification
        assert len(config.graphic_extensions) == len(original_extensions) + 1
        assert ".svg" in config.graphic_extensions
