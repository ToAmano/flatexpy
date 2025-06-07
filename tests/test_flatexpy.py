"""Comprehensive unit tests for flatexpy.py using PyTest."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from flatexpy.flatexpy import (
    GraphicsNotFoundError,
    LatexExpandConfig,
    LatexExpander,
    LatexExpandError,
    _create_output_dir,
    main,
)


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


class TestExceptions:
    """Test cases for custom exception classes."""

    def test_latex_expand_error(self) -> None:
        """Test LatexExpandError exception."""
        with pytest.raises(LatexExpandError) as exc_info:
            raise LatexExpandError("Test error message")
        assert str(exc_info.value) == "Test error message"

    def test_graphics_not_found_error(self) -> None:
        """Test GraphicsNotFoundError exception."""
        with pytest.raises(GraphicsNotFoundError) as exc_info:
            raise GraphicsNotFoundError("Graphics not found")
        assert str(exc_info.value) == "Graphics not found"
        assert issubclass(GraphicsNotFoundError, LatexExpandError)


class TestCreateDir:
    @patch("os.makedirs")
    @patch("pathlib.Path.exists")
    def test_create_output_dir_success(
        self, mock_exists: MagicMock, mock_makedirs: MagicMock
    ) -> None:
        """Test successful output directory creation."""
        mock_exists.return_value = False
        _create_output_dir("output", False)
        mock_makedirs.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_create_output_dir_exists(self, mock_exists: MagicMock) -> None:
        """Test output directory creation when directory exists."""
        mock_exists.return_value = True

        with pytest.raises(FileExistsError):
            _create_output_dir("output", False)


class TestLatexExpander:
    """Test cases for LatexExpander class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = LatexExpandConfig()
        self.expander = LatexExpander(self.config)

    def test_init_with_config(self) -> None:
        """Test initialization with custom config."""
        custom_config = LatexExpandConfig(ignore_commented_lines=False)
        expander = LatexExpander(custom_config)
        assert expander.config == custom_config

    def test_init_without_config(self) -> None:
        """Test initialization with default config."""
        expander = LatexExpander()
        assert isinstance(expander.config, LatexExpandConfig)
        assert expander.config.ignore_commented_lines is True

    def test_is_line_commented(self) -> None:
        """Test comment line detection."""
        assert self.expander._is_line_commented("% This is a comment")
        assert self.expander._is_line_commented("  % Comment with spaces")
        assert not self.expander._is_line_commented("Not a comment")
        assert not self.expander._is_line_commented("\\input{file} % inline comment")

    def test_extract_graphics_paths(self) -> None:
        """Test graphics path extraction."""
        line1 = "\\graphicspath{{figures/}{images/}}"
        paths1 = self.expander._extract_graphics_paths(line1)
        assert paths1 == ["figures", "images"]

        line2 = "\\graphicspath{{../graphics/}}"
        paths2 = self.expander._extract_graphics_paths(line2)
        assert paths2 == ["../graphics"]

        line3 = "No graphics path here"
        paths3 = self.expander._extract_graphics_paths(line3)
        assert paths3 == []

    @patch("pathlib.Path.exists")
    def test_resolve_file_path_exists(self, mock_exists: MagicMock) -> None:
        """Test file path resolution when file exists."""
        mock_exists.return_value = True
        result = self.expander._resolve_file_path("test.tex")
        assert result == Path("test.tex")

    @patch("pathlib.Path.exists")
    def test_resolve_file_path_with_tex_extension(self, mock_exists: MagicMock) -> None:
        """Test file path resolution with automatic .tex extension."""

        def side_effect():
            # Return True only for the .tex version
            return mock_exists.return_value

        mock_exists.side_effect = [
            False,
            True,
        ]  # First call returns False, second returns True
        result = self.expander._resolve_file_path("test")
        assert result == Path("test.tex")

    @patch("pathlib.Path.exists")
    def test_resolve_file_path_not_found(self, mock_exists: MagicMock) -> None:
        """Test file path resolution when file doesn't exist."""
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError):
            self.expander._resolve_file_path("nonexistent.tex")

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

    def test_process_input_include_found(self) -> None:
        """Test processing input/include commands when file is found."""
        with (
            patch.object(self.expander, "_resolve_file_path") as mock_resolve,
            patch.object(self.expander, "_flatten_file") as mock_flatten,
        ):

            mock_resolve.return_value = Path("included.tex")
            mock_flatten.return_value = "Included content\n"

            line = "\\input{included}"
            result, was_processed = self.expander._process_input_include(
                line, ".", "output"
            )

            assert was_processed
            assert ">>> input{included} >>>" in result
            assert "Included content" in result
            assert "<<< input{included} <<<" in result

    def test_process_input_include_not_found(self) -> None:
        """Test processing input/include commands when file is not found."""
        with patch.object(self.expander, "_resolve_file_path") as mock_resolve:
            mock_resolve.side_effect = FileNotFoundError("File not found")

            line = "\\input{missing}"
            result, was_processed = self.expander._process_input_include(
                line, ".", "output"
            )

            assert not was_processed
            assert result == line

    def test_process_input_include_no_match(self) -> None:
        """Test processing line without input/include commands."""
        line = "This is just text"
        result, was_processed = self.expander._process_input_include(
            line, ".", "output"
        )

        assert not was_processed
        assert result == line

    @patch("builtins.open", new_callable=mock_open, read_data="Line 1\nLine 2\n")
    @patch("os.path.abspath")
    @patch("os.path.dirname")
    def test_flatten_file_basic(
        self, mock_dirname: MagicMock, mock_abspath: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test basic file flattening."""
        mock_abspath.return_value = "/abs/path/file.tex"
        mock_dirname.return_value = "/abs/path"

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

    @patch("builtins.open")
    def test_flatten_file_io_error(self, mock_open_func: MagicMock) -> None:
        """Test file flattening with IO error."""
        mock_open_func.side_effect = IOError("Permission denied")

        with pytest.raises(LatexExpandError):
            self.expander._flatten_file("file.tex", ".", "output")

    def test_flatten_latex_integration(self) -> None:
        """Test full LaTeX flattening integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            input_file = os.path.join(temp_dir, "main.tex")
            output_dir = os.path.join(temp_dir, "output")
            output_file = os.path.join(output_dir, "main_flat.tex")
            os.makedirs(output_dir)

            with open(input_file, "w") as f:
                f.write(
                    "\\documentclass{article}\n\\begin{document}\nHello World\n\\end{document}\n"
                )

            # Test flattening
            result = self.expander.flatten_latex(input_file, output_file)

            assert os.path.exists(output_file)
            assert "Hello World" in result

            with open(output_file, "r") as f:
                content = f.read()
                assert content == result


class TestMainFunction:
    """Test cases for main function and CLI argument parsing."""

    @patch("sys.argv", ["flatexpy.py", "input.tex", "--force"])
    @patch("flatexpy.flatexpy.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy._create_output_dir")
    @patch("builtins.print")
    def test_main_basic(
        self,
        mock_print: MagicMock,
        mock_flatten: MagicMock,
        mock_createoutput: MagicMock,
    ) -> None:
        """Test basic main function execution."""
        mock_flatten.return_value = "flattened content"
        mock_createoutput.return_value = None

        main()

        mock_flatten.assert_called_once()
        mock_print.assert_called_once()

    @patch("sys.argv", ["flatexpy.py", "input.tex", "--verbose"])
    @patch("flatexpy.flatexpy.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy._create_output_dir")
    @patch("logging.getLogger")
    def test_main_verbose(
        self,
        mock_get_logger: MagicMock,
        mock_flatten: MagicMock,
        mock_createoutput: MagicMock,
    ) -> None:
        """Test main function with verbose flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_flatten.return_value = "flattened content"
        mock_createoutput.return_value = None

        main()

        mock_logger.setLevel.assert_called()

    @patch("sys.argv", ["flatexpy.py", "input.tex", "-o", "custom_output/", "-f"])
    @patch("flatexpy.flatexpy.LatexExpander.flatten_latex")
    def test_main_custom_output(self, mock_flatten: MagicMock) -> None:
        """Test main function with custom output directory."""
        mock_flatten.return_value = "flattened content"

        main()

        args, kwargs = mock_flatten.call_args
        assert "custom_output/" in args[1]

    @patch("sys.argv", ["flatexpy.py", "input.tex"])
    @patch("flatexpy.flatexpy.LatexExpander.flatten_latex")
    @patch("flatexpy.flatexpy._create_output_dir")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_error_handling(
        self,
        mock_print: MagicMock,
        mock_exit: MagicMock,
        mock_flatten: MagicMock,
        mock_createoutput: MagicMock,
    ) -> None:
        """Test main function error handling."""
        mock_flatten.side_effect = LatexExpandError("Test error")
        mock_createoutput.return_value = None

        main()

        mock_exit.assert_called_once_with(1)
        mock_print.assert_called()


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow_with_includes(self) -> None:
        """Test complete workflow with includes and graphics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set working directory to temp_dir for relative path resolution
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main file
                main_file = "main.tex"
                with open(main_file, "w") as f:
                    f.write("\\documentclass{article}\n")
                    f.write("\\begin{document}\n")
                    f.write("\\input{chapter1}\n")
                    f.write("\\end{document}\n")

                # Create included file
                chapter_file = "chapter1.tex"
                with open(chapter_file, "w") as f:
                    f.write("Chapter 1 content\n")

                # Create output directory
                output_dir = "output"
                output_file = os.path.join(output_dir, "main_flat.tex")
                os.makedirs(output_dir)

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex(main_file, output_file)

                assert "Chapter 1 content" in result
                assert ">>> input{chapter1} >>>" in result
                assert "<<< input{chapter1} <<<" in result
                assert os.path.exists(output_file)
            finally:
                os.chdir(original_cwd)

    def test_graphics_processing(self) -> None:
        """Test graphics file processing and copying."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set working directory to temp_dir for relative path resolution
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main file with graphics
                main_file = "main.tex"
                with open(main_file, "w") as f:
                    f.write("\\documentclass{article}\n")
                    f.write("\\begin{document}\n")
                    f.write("\\includegraphics{test_image}\n")
                    f.write("\\end{document}\n")

                # Create test image
                image_file = "test_image.png"
                with open(image_file, "wb") as f:
                    f.write(b"fake image data")

                # Create output directory
                output_dir = "output"
                output_file = os.path.join(output_dir, "main_flat.tex")
                os.makedirs(output_dir)

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex(main_file, output_file)

                # Check that graphics reference is updated
                assert "test_image.png" in result

                # Check that image was copied
                copied_image = os.path.join(output_dir, "test_image.png")
                assert os.path.exists(copied_image)
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
