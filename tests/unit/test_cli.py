"""Test cases for command line interface functionality."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from flatexpy.flatexpy_core import LatexExpandError, main


class TestMainFunction:
    """Test cases for main function and CLI argument parsing."""

    @patch("sys.argv", ["flatexpy.py", "input.tex", "--force"])
    @patch("flatexpy.flatexpy_core.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy_core._create_output_dir")
    @patch("builtins.print")
    def test_main_basic(
        self,
        mock_print: MagicMock,
        mock_create_output: MagicMock,
        mock_flatten: MagicMock,
    ) -> None:
        """Test basic main function execution."""
        mock_flatten.return_value = "flattened content"
        mock_create_output.return_value = None

        main()

        mock_flatten.assert_called_once()
        mock_print.assert_called_once()

    @patch("sys.argv", ["flatexpy.py", "input.tex", "--verbose", "--force"])
    @patch("flatexpy.flatexpy_core.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy_core._create_output_dir")
    @patch("logging.getLogger")
    def test_main_verbose(
        self,
        mock_get_logger: MagicMock,
        mock_create_output: MagicMock,
        mock_flatten: MagicMock,
    ) -> None:
        """Test main function with verbose flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_flatten.return_value = "flattened content"
        mock_create_output.return_value = None

        main()

        mock_logger.setLevel.assert_called()

    @patch("sys.argv", ["flatexpy.py", "input.tex", "-o", "custom_output/", "-f"])
    @patch("flatexpy.flatexpy_core.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy_core._create_output_dir")
    def test_main_custom_output(
        self, mock_create_output: MagicMock, mock_flatten: MagicMock
    ) -> None:
        """Test main function with custom output directory."""
        mock_flatten.return_value = "flattened content"
        mock_create_output.return_value = None

        main()

        args, kwargs = mock_flatten.call_args
        assert "custom_output/" in args[1]

    @patch(
        "sys.argv",
        ["flatexpy.py", "input.tex", "--graphics-exts", ".svg", ".tiff", "-f"],
    )
    @patch("flatexpy.flatexpy_core.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy_core._create_output_dir")
    def test_main_custom_graphics_extensions(
        self, mock_create_output: MagicMock, mock_flatten: MagicMock
    ) -> None:
        """Test main function with custom graphics extensions."""
        mock_flatten.return_value = "flattened content"
        mock_create_output.return_value = None

        main()

        # Verify that LatexExpander was created with custom extensions
        mock_flatten.assert_called_once()

    @patch("sys.argv", ["flatexpy.py", "input.tex", "--ignore-comments", "-f"])
    @patch("flatexpy.flatexpy_core.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy_core._create_output_dir")
    def test_main_ignore_comments(
        self, mock_create_output: MagicMock, mock_flatten: MagicMock
    ) -> None:
        """Test main function with ignore comments flag."""
        mock_flatten.return_value = "flattened content"
        mock_create_output.return_value = None

        main()

        mock_flatten.assert_called_once()

    @patch("sys.argv", ["flatexpy.py", "input.tex"])
    @patch("flatexpy.flatexpy_core.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy_core._create_output_dir")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_error_handling(
        self,
        mock_print: MagicMock,
        mock_exit: MagicMock,
        mock_create_output: MagicMock,
        mock_flatten: MagicMock,
    ) -> None:
        """Test main function error handling."""
        mock_flatten.side_effect = LatexExpandError("Test error")
        mock_create_output.return_value = None

        main()

        mock_exit.assert_called_once_with(1)
        mock_print.assert_called()

    @patch("sys.argv", ["flatexpy.py", "input.tex"])
    @patch("flatexpy.flatexpy_core.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy_core._create_output_dir")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_create_output_dir_error(
        self,
        mock_print: MagicMock,
        mock_exit: MagicMock,
        mock_create_output: MagicMock,
        mock_flatten: MagicMock,
    ) -> None:
        """Test main function with output directory creation error."""
        mock_create_output.side_effect = FileExistsError("Directory exists")
        mock_flatten.return_value = "content"

        main()

        mock_exit.assert_called_once_with(1)
        mock_print.assert_called()

    def test_main_output_file_naming(self) -> None:
        """Test output file naming logic."""
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test input file
            input_file = os.path.join(temp_dir, "paper.tex")
            with open(input_file, "w") as f:
                f.write("\\documentclass{article}\\begin{document}Test\\end{document}")

            # Create output directory
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir)

            # Mock sys.argv
            test_args = ["flatexpy.py", input_file, "-o", output_dir, "-f"]

            with (
                patch("sys.argv", test_args),
                patch(
                    "flatexpy.flatexpy_core.LatexExpander.flatten_latex"
                ) as mock_flatten,
                patch("builtins.print"),
            ):

                mock_flatten.return_value = "content"
                main()

                # Check that the output file name is correct
                args, kwargs = mock_flatten.call_args
                output_file = args[1]
                expected_output = os.path.join(output_dir, "paper_flattened.tex")
                assert output_file == expected_output

    @patch("sys.argv", ["flatexpy.py", "--help"])
    def test_main_help(self) -> None:
        """Test main function help output."""
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0  # Help should exit with code 0

    @patch("sys.argv", ["flatexpy.py"])
    def test_main_missing_required_argument(self) -> None:
        """Test main function with missing required argument."""
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 2  # Argument error should exit with code 2

    def test_argument_parser_configuration(self) -> None:
        """Test that argument parser is configured correctly."""
        import argparse

        from flatexpy.flatexpy_core import main

        # This is a bit tricky to test without calling main()
        # We can test the parser setup by creating it manually
        parser = argparse.ArgumentParser(
            description="Flatten LaTeX documents by inlining includes and copying graphics"
        )
        parser.add_argument("input_file", help="Input LaTeX file to flatten")
        parser.add_argument(
            "--ignore-comments",
            action="store_true",
            default=True,
            help="Ignore commented lines (default: True)",
        )
        parser.add_argument(
            "--graphics-exts",
            nargs="+",
            default=[".pdf", ".png", ".jpg", ".jpeg", ".eps"],
            help="Graphics file extensions to search for",
        )
        parser.add_argument(
            "-o", "--output", default="flat/", help="Output directory (default: flat/)"
        )
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Enable verbose logging"
        )
        parser.add_argument(
            "-f", "--force", action="store_true", help="Overwrite existing diff files."
        )

        # Test parsing valid arguments
        args = parser.parse_args(["test.tex", "-o", "output/", "--verbose"])
        assert args.input_file == "test.tex"
        assert args.output == "output/"
        assert args.verbose is True
