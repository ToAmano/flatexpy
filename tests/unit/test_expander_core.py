"""Test cases for core LatexExpander functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from pybtex.database import parse_file

from flatexpy.flatexpy_core import (
    GraphicsNotFoundError,
    LatexExpandConfig,
    LatexExpander,
    LatexExpandError,
    _create_output_dir,
    main,
)


class TestLatexExpanderCore:
    """Test cases for core LatexExpander class functionality."""

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

    def test_initial_state(self) -> None:
        """Test that expander starts with clean state."""
        assert len(self.expander._visited_files) == 0
        assert len(self.expander._graphics_paths) == 0
        assert len(self.expander._collected_graphics) == 0
        assert len(self.expander._bibliography_files) == 0
        assert len(self.expander._citation_keys) == 0

    def test_compiled_patterns(self) -> None:
        """Test that regex patterns are compiled correctly."""
        # Test input pattern
        assert self.expander._input_pattern.pattern == r"\\(input|include)\{([^}]+)\}"

        # Test graphicspath pattern
        assert (
            self.expander._graphicspath_pattern.pattern
            == r"\\graphicspath\{((\{[^}]+\})+)\}"
        )

        # Test includegraphics pattern
        assert (
            self.expander._includegraphics_pattern.pattern
            == r"\\(?:includegraphics|plotone|plottwo)(?:\[[^\]]*\])?\{([^}]+)\}(?:\{([^}]+)\})?"
        )
        assert self.expander._bibliography_pattern.pattern == r"\\bibliography\{([^}]+)\}"
        assert (
            self.expander._citation_pattern.pattern
            == r"\\(?:cite[a-zA-Z*]*|nocite)\s*(?:\[[^\]]*\]\s*)*\{([^}]+)\}"
        )

    def test_is_line_commented(self) -> None:
        """Test comment line detection."""
        assert self.expander._is_line_commented("% This is a comment")
        assert self.expander._is_line_commented("  % Comment with spaces")
        assert self.expander._is_line_commented("\t% Comment with tab")
        assert not self.expander._is_line_commented("Not a comment")
        assert not self.expander._is_line_commented("\\input{file} % inline comment")
        assert not self.expander._is_line_commented("")
        assert not self.expander._is_line_commented("   ")

    def test_extract_graphics_paths(self) -> None:
        """Test graphics path extraction."""
        # Single path
        line1 = "\\graphicspath{{figures/}}"
        paths1 = self.expander._extract_graphics_paths(line1)
        assert paths1 == ["figures"]

        # Multiple paths
        line2 = "\\graphicspath{{figures/}{images/}}"
        paths2 = self.expander._extract_graphics_paths(line2)
        assert paths2 == ["figures", "images"]

        # Path with parent directory
        line3 = "\\graphicspath{{../graphics/}}"
        paths3 = self.expander._extract_graphics_paths(line3)
        assert paths3 == ["../graphics"]

        # No graphics path
        line4 = "No graphics path here"
        paths4 = self.expander._extract_graphics_paths(line4)
        assert paths4 == []

        # Complex paths
        line5 = "\\graphicspath{{./figures/}{../images/}{/abs/path/}}"
        paths5 = self.expander._extract_graphics_paths(line5)
        assert paths5 == ["figures", "../images", "/abs/path"]

    def test_add_extension_to_filename(self) -> None:
        """Test adding extension to filename."""
        # File without extension
        result1 = self.expander._add_extension_to_filename("image", ".png")
        assert result1 == "image.png"

        # File with extension
        result2 = self.expander._add_extension_to_filename("image.jpg", ".png")
        assert result2 == "image.jpg"

        # Extension without dot should raise error
        with pytest.raises(ValueError, match="ext should start with"):
            self.expander._add_extension_to_filename("image", "png")

    def test_update_graphics_path(self) -> None:
        """Test updating graphics paths."""
        # Initially empty
        assert len(self.expander._graphics_paths) == 0

        # Add first path
        line1 = "\\graphicspath{{figures/}}"
        self.expander._update_graphics_path(line1)
        assert self.expander._graphics_paths == ["figures"]

        # Add second path
        line2 = "\\graphicspath{{images/}}"
        self.expander._update_graphics_path(line2)
        assert self.expander._graphics_paths == ["figures", "images"]

        # Add duplicate path (should not add)
        line3 = "\\graphicspath{{figures/}}"
        self.expander._update_graphics_path(line3)
        assert self.expander._graphics_paths == ["figures", "images"]

    def test_extract_bibliography_files(self) -> None:
        """Test extracting bibliography database names."""
        line = "\\bibliography{local,lsst, refs_ads}"
        assert self.expander._extract_bibliography_files(line) == [
            "local",
            "lsst",
            "refs_ads",
        ]

    def test_extract_citation_keys(self) -> None:
        """Test extracting citation keys from cite-like commands."""
        line = "Text \\citep[see][]{key1,key2} and \\nocite{key3}"
        assert self.expander._extract_citation_keys(line) == ["key1", "key2", "key3"]

    def test_rewrite_bibliography_command(self) -> None:
        """Test rewriting bibliography command to merged output."""
        self.expander._bib_output_stem = "main_flattened"
        line = "\\bibliography{local,lsst}\n"
        assert (
            self.expander._rewrite_bibliography_command(line)
            == "\\bibliography{main_flattened}\n"
        )

    def test_resolve_bib_path_prefers_local_file(self) -> None:
        """Test local bibliography databases are preferred over TEXMFHOME."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            texmf_dir = root_dir / "texmf"
            local_bib = root_dir / "refs.bib"
            texmf_bib = texmf_dir / "bibtex" / "bib" / "misc" / "refs.bib"
            texmf_bib.parent.mkdir(parents=True)
            local_bib.write_text("@article{localref, title={Local}}\n", encoding="utf-8")
            texmf_bib.write_text("@article{texmfref, title={Texmf}}\n", encoding="utf-8")

            expander = LatexExpander(
                LatexExpandConfig(root_directory=temp_dir, texmfhome=str(texmf_dir))
            )
            assert expander._resolve_bib_path("refs", temp_dir) == local_bib

    def test_collect_bib_entries_keeps_first_duplicate(self) -> None:
        """Test duplicate keys keep the first database entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            first_bib = Path(temp_dir) / "first_refs.bib"
            second_bib = Path(temp_dir) / "second_refs.bib"
            first_bib.write_text(
                "@article{dupkey, title={First Title}}\n", encoding="utf-8"
            )
            second_bib.write_text(
                "@article{dupkey, title={Second Title}}\n", encoding="utf-8"
            )

            first_db = parse_file(str(first_bib))
            second_db = parse_file(str(second_bib))

            self.expander._collect_bib_entries(first_db, str(first_bib))
            self.expander._collect_bib_entries(second_db, str(second_bib))

            assert (
                self.expander._bib_entries_by_key["dupkey"].fields["title"]
                == "First Title"
            )

    def test_show_config(self) -> None:
        """Test configuration display."""
        # This method logs configuration, so we test it doesn't raise errors
        self.expander.show_config()  # Should not raise any exception

    def test_state_reset_in_flatten_latex(self) -> None:
        """Test that state is reset when starting new flatten operation."""
        # Add some state
        self.expander._visited_files.add("/some/file.tex")
        self.expander._graphics_paths.append("some/path")
        self.expander._collected_graphics.add("some/graphic.png")

        # Create temporary test files
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "test.tex")
            output_dir = os.path.join(temp_dir, "output")
            output_file = os.path.join(output_dir, "test_flat.tex")

            with open(input_file, "w") as f:
                f.write("\\documentclass{article}\\begin{document}Test\\end{document}")

            os.makedirs(output_dir)

            # Call flatten_latex - this should reset state
            self.expander.flatten_latex(input_file, output_file)

            # State should be reset and then populated with new operation
            # At minimum, the input file should be in visited files
            assert len(self.expander._visited_files) >= 1

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

    def test_flatten_latex_writes_merged_bibliography(self) -> None:
        """Test bibliography collection and unified .bib generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "main.tex")
            included_file = os.path.join(temp_dir, "section.tex")
            bibliography_file = os.path.join(temp_dir, "refs.bib")
            output_dir = os.path.join(temp_dir, "output")
            output_file = os.path.join(output_dir, "main_flat.tex")
            os.makedirs(output_dir)

            with open(input_file, "w", encoding="utf-8") as f:
                f.write(
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\citep{beta}\n"
                    "\\input{section}\n"
                    "\\bibliography{refs}\n"
                    "\\end{document}\n"
                )

            with open(included_file, "w", encoding="utf-8") as f:
                f.write("Nested cite \\cite{alpha}.\n")

            with open(bibliography_file, "w", encoding="utf-8") as f:
                f.write(
                    "@article{alpha,\n"
                    "  title = {Alpha Title}\n"
                    "}\n\n"
                    "@article{beta,\n"
                    "  title = {Beta Title}\n"
                    "}\n\n"
                    "@article{gamma,\n"
                    "  title = {Gamma Title}\n"
                    "}\n"
                )

            expander = LatexExpander(LatexExpandConfig(root_directory=temp_dir))
            result = expander.flatten_latex(input_file, output_file)

            merged_bib = os.path.join(output_dir, "main_flattened.bib")
            assert "\\bibliography{main_flattened}" in result
            assert os.path.exists(merged_bib)

            with open(merged_bib, "r", encoding="utf-8") as f:
                merged_content = f.read()
                assert "alpha" in merged_content
                assert "beta" in merged_content
                assert "gamma" not in merged_content
                assert merged_content.index("@article{alpha") < merged_content.index(
                    "@article{beta"
                )

    def test_normalize_bibliography_output_fixes_pybtex_escaping(self) -> None:
        """Test post-processing for known pybtex escaping issues."""
        output = (
            "@article{ref,\n"
            "  title = {A\\\\_B and C\\\\#D},\n"
            "  url = {https://example.com/a\\\\_b\\\\#c},\n"
            "  doi = {10.1234/foo\\\\_bar},\n"
            "  adsurl = {https://ads.example/x\\\\_y}\n"
            "}\n"
        )

        normalized = self.expander._normalize_bibliography_output(output)
        assert "title = {A\\_B and C\\#D}" in normalized
        assert "url = {https://example.com/a_b#c}" in normalized
        assert "doi = {10.1234/foo_bar}" in normalized
        assert "adsurl = {https://ads.example/x_y}" in normalized
