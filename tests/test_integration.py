"""Comprehensive integration tests for flatexpy.py.

This module contains integration tests that test the complete workflow of the LaTeX
flattening functionality, including real file processing, graphics handling, and
complex document structures.
"""

import os
import tempfile

import pytest

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander, LatexExpandError


class TestBasicIntegration:
    """Basic integration tests for common use cases."""

    def test_simple_document_flattening(self) -> None:
        """Test flattening of a simple document with no includes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create simple document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "Hello World!\n"
                    "\\end{document}\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                # Create output directory
                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify results
                assert "Hello World!" in result
                assert os.path.exists("output/main_flat.tex")

                with open("output/main_flat.tex", "r") as f:
                    content = f.read()
                    assert content == result
                    assert "\\documentclass{article}" in content

            finally:
                os.chdir(original_cwd)

    def test_document_with_single_include(self) -> None:
        """Test flattening document with a single \\input command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "Before include\n"
                    "\\input{chapter1}\n"
                    "After include\n"
                    "\\end{document}\n"
                )

                # Create included file
                chapter_content = "This is chapter 1 content.\n"

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapter1.tex", "w") as f:
                    f.write(chapter_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify results
                assert "Before include" in result
                assert "This is chapter 1 content." in result
                assert "After include" in result
                assert ">>> input{chapter1} >>>" in result
                assert "<<< input{chapter1} <<<" in result

            finally:
                os.chdir(original_cwd)

    def test_document_with_multiple_includes(self) -> None:
        """Test flattening document with multiple \\input commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with multiple includes
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{intro}\n"
                    "\\input{chapter1}\n"
                    "\\input{conclusion}\n"
                    "\\end{document}\n"
                )

                # Create included files
                files_content = {
                    "intro.tex": "Introduction section.\n",
                    "chapter1.tex": "Chapter 1 content.\n",
                    "conclusion.tex": "Conclusion section.\n",
                }

                with open("main.tex", "w") as f:
                    f.write(main_content)

                for filename, content in files_content.items():
                    with open(filename, "w") as f:
                        f.write(content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all content is included in correct order
                assert "Introduction section." in result
                assert "Chapter 1 content." in result
                assert "Conclusion section." in result

                # Check order is preserved
                intro_pos = result.find("Introduction section.")
                chapter_pos = result.find("Chapter 1 content.")
                conclusion_pos = result.find("Conclusion section.")

                assert intro_pos < chapter_pos < conclusion_pos

                # Check include markers
                assert ">>> input{intro} >>>" in result
                assert ">>> input{chapter1} >>>" in result
                assert ">>> input{conclusion} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_nested_includes(self) -> None:
        """Test flattening document with nested \\input commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "Main content\n"
                    "\\input{level1}\n"
                    "\\end{document}\n"
                )

                # Create level 1 file that includes level 2
                level1_content = (
                    "Level 1 content\n" "\\input{level2}\n" "More level 1 content\n"
                )

                # Create level 2 file
                level2_content = "Level 2 content\n"

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("level1.tex", "w") as f:
                    f.write(level1_content)

                with open("level2.tex", "w") as f:
                    f.write(level2_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify nested content is included
                assert "Main content" in result
                assert "Level 1 content" in result
                assert "Level 2 content" in result
                assert "More level 1 content" in result

                # Check nested markers
                assert ">>> input{level1} >>>" in result
                assert ">>> input{level2} >>>" in result
                assert "<<< input{level2} <<<" in result
                assert "<<< input{level1} <<<" in result

            finally:
                os.chdir(original_cwd)


class TestGraphicsHandling:
    """Integration tests for graphics file handling."""

    def test_single_graphics_file(self) -> None:
        """Test document with single \\includegraphics command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with graphics
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "Here is an image:\n"
                    "\\includegraphics{figure1}\n"
                    "\\end{document}\n"
                )

                # Create fake image file
                with open("figure1.png", "wb") as f:
                    f.write(b"fake PNG data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify graphics reference is updated
                assert "\\includegraphics{figure1.png}" in result

                # Verify image file is copied
                assert os.path.exists("output/figure1.png")

                # Verify copied file has same content
                with open("figure1.png", "rb") as original:
                    with open("output/figure1.png", "rb") as copied:
                        assert original.read() == copied.read()

            finally:
                os.chdir(original_cwd)

    def test_multiple_graphics_files(self) -> None:
        """Test document with multiple \\includegraphics commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with multiple graphics
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{figure1}\n"
                    "\\includegraphics{figure2.jpg}\n"
                    "\\includegraphics[width=0.5\\textwidth]{figure3}\n"
                    "\\end{document}\n"
                )

                # Create fake image files
                images = ["figure1.png", "figure2.jpg", "figure3.pdf"]
                for img in images:
                    with open(img, "wb") as f:
                        f.write(f"fake {img} data".encode())

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all graphics references are updated
                assert "\\includegraphics{figure1.png}" in result
                assert "\\includegraphics{figure2.jpg}" in result
                assert "\\includegraphics[width=0.5\\textwidth]{figure3.pdf}" in result

                # Verify all image files are copied
                for img in images:
                    assert os.path.exists(f"output/{img}")

            finally:
                os.chdir(original_cwd)

    def test_graphics_with_graphicspath(self) -> None:
        """Test graphics handling with \\graphicspath command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("figures")

                # Create main document with graphicspath
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\graphicspath{{figures/}}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{chart}\n"
                    "\\end{document}\n"
                )

                # Create image in subdirectory
                with open("figures/chart.png", "wb") as f:
                    f.write(b"fake chart data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify graphics reference is updated to just filename
                assert "\\includegraphics{chart.png}" in result

                # Verify image file is copied to root output directory
                assert os.path.exists("output/chart.png")

            finally:
                os.chdir(original_cwd)

    def test_missing_graphics_file(self) -> None:
        """Test handling of missing graphics files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with missing graphics
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{missing_figure}\n"
                    "\\end{document}\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening (should not raise exception, just log warning)
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Original graphics command should remain unchanged
                assert "\\includegraphics{missing_figure}" in result

            finally:
                os.chdir(original_cwd)


class TestCommentHandling:
    """Integration tests for comment handling."""

    def test_commented_includes_ignored(self) -> None:
        """Test that commented \\input commands are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with commented include
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "% \\input{commented_file}\n"
                    "\\input{real_file}\n"
                    "\\end{document}\n"
                )

                # Create both files
                with open("commented_file.tex", "w") as f:
                    f.write("This should not be included.\n")

                with open("real_file.tex", "w") as f:
                    f.write("This should be included.\n")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(
                    root_directory=".", ignore_commented_lines=True
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify only real file is included
                assert "This should be included." in result
                assert "This should not be included." not in result
                assert "% \\input{commented_file}" in result  # Comment preserved

            finally:
                os.chdir(original_cwd)

    def test_preserve_comments_option(self) -> None:
        """Test that comments are preserved in output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with comments
                main_content = (
                    "\\documentclass{article}\n"
                    "% This is a main comment\n"
                    "\\begin{document}\n"
                    "\\input{chapter}\n"
                    "\\end{document}\n"
                )

                # Create included file with comments
                chapter_content = (
                    "% Chapter comment\n" "Chapter content\n" "% Another comment\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapter.tex", "w") as f:
                    f.write(chapter_content)

                os.makedirs("output")

                # Test flattening with comment preservation
                config = LatexExpandConfig(
                    root_directory=".", ignore_commented_lines=True
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify comments are preserved
                assert "% This is a main comment" in result
                assert "% Chapter comment" in result
                assert "% Another comment" in result
                assert "Chapter content" in result

            finally:
                os.chdir(original_cwd)


class TestErrorHandling:
    """Integration tests for error conditions and edge cases."""

    def test_circular_includes(self) -> None:
        """Test handling of circular include dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create circular dependency: main -> file1 -> file2 -> file1
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{file1}\n"
                    "\\end{document}\n"
                )

                file1_content = "File 1 content\n" "\\input{file2}\n"

                file2_content = (
                    "File 2 content\n"
                    "\\input{file1}\n"  # Circular reference
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("file1.tex", "w") as f:
                    f.write(file1_content)

                with open("file2.tex", "w") as f:
                    f.write(file2_content)

                os.makedirs("output")

                # Test flattening (should handle circular reference gracefully)
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # First inclusion should work, second should be skipped
                assert "File 1 content" in result
                assert "File 2 content" in result
                # Count occurrences to ensure no infinite recursion
                assert result.count("File 1 content") == 1

            finally:
                os.chdir(original_cwd)

    def test_missing_input_file(self) -> None:
        """Test handling of missing \\input files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with missing include
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "Before missing\n"
                    "\\input{nonexistent}\n"
                    "After missing\n"
                    "\\end{document}\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening (should continue despite missing file)
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Should preserve original include command when file not found
                assert "Before missing" in result
                assert "\\input{nonexistent}" in result
                assert "After missing" in result

            finally:
                os.chdir(original_cwd)

    def test_output_directory_creation_failure(self) -> None:
        """Test handling when output directory cannot be created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create simple document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "Test content\n"
                    "\\end{document}\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                # Create a file where we want to create a directory
                with open("output", "w") as f:
                    f.write("blocking file")

                # Test flattening (should fail due to directory creation issue)
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)

                with pytest.raises(LatexExpandError):
                    expander.flatten_latex("main.tex", "output/main_flat.tex")

            finally:
                os.chdir(original_cwd)

    def test_file_encoding_issues(self) -> None:
        """Test handling of files with different encodings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{special_chars}\n"
                    "\\end{document}\n"
                )

                # Create file with special characters
                special_content = "Special chars: ñáéíóú\n"

                with open("main.tex", "w", encoding="utf-8") as f:
                    f.write(main_content)

                with open("special_chars.tex", "w", encoding="utf-8") as f:
                    f.write(special_content)

                os.makedirs("output")

                # Test flattening with UTF-8 encoding
                config = LatexExpandConfig(root_directory=".", output_encoding="utf-8")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify special characters are preserved
                assert "ñáéíóú" in result

                # Verify output file has correct encoding
                with open("output/main_flat.tex", "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "ñáéíóú" in content

            finally:
                os.chdir(original_cwd)


class TestComplexDocuments:
    """Integration tests for complex document structures."""

    def test_document_with_packages_and_includes(self) -> None:
        """Test complex document with packages, graphics, and multiple includes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create complex main document
                main_content = (
                    "\\documentclass[12pt]{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\usepackage{amsmath}\n"
                    "\\graphicspath{{figures/}}\n"
                    "\\title{Complex Document}\n"
                    "\\author{Test Author}\n"
                    "\\begin{document}\n"
                    "\\maketitle\n"
                    "\\input{abstract}\n"
                    "\\input{introduction}\n"
                    "\\input{methods}\n"
                    "\\input{results}\n"
                    "\\input{conclusion}\n"
                    "\\end{document}\n"
                )

                # Create directory structure
                os.makedirs("figures")

                # Create included files
                files_content = {
                    "abstract.tex": (
                        "\\begin{abstract}\n"
                        "This is the abstract.\n"
                        "\\end{abstract}\n"
                    ),
                    "introduction.tex": (
                        "\\section{Introduction}\n"
                        "Introduction text with figure:\n"
                        "\\includegraphics{intro_fig}\n"
                    ),
                    "methods.tex": (
                        "\\section{Methods}\n"
                        "Methods description.\n"
                        "\\input{detailed_methods}\n"
                    ),
                    "detailed_methods.tex": (
                        "\\subsection{Detailed Methods}\n" "Detailed methodology.\n"
                    ),
                    "results.tex": (
                        "\\section{Results}\n"
                        "Results with equation:\n"
                        "\\begin{equation}\n"
                        "E = mc^2\n"
                        "\\end{equation}\n"
                        "And figure:\n"
                        "\\includegraphics{results_fig}\n"
                    ),
                    "conclusion.tex": ("\\section{Conclusion}\n" "Final thoughts.\n"),
                }

                # Create image files
                images = ["intro_fig.png", "results_fig.jpg"]
                for img in images:
                    with open(f"figures/{img}", "wb") as f:
                        f.write(f"fake {img} data".encode())

                # Write all files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                for filename, content in files_content.items():
                    with open(filename, "w") as f:
                        f.write(content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all sections are included
                assert "\\begin{abstract}" in result
                assert "\\section{Introduction}" in result
                assert "\\section{Methods}" in result
                assert "\\subsection{Detailed Methods}" in result
                assert "\\section{Results}" in result
                assert "\\section{Conclusion}" in result

                # Verify graphics are processed
                assert "\\includegraphics{intro_fig.png}" in result
                assert "\\includegraphics{results_fig.jpg}" in result

                # Verify image files are copied
                assert os.path.exists("output/intro_fig.png")
                assert os.path.exists("output/results_fig.jpg")

                # Verify include markers are present
                assert ">>> input{abstract} >>>" in result
                assert ">>> input{detailed_methods} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_document_with_subdirectories(self) -> None:
        """Test document with includes from subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("chapters")
                os.makedirs("appendices")

                # Create main document
                main_content = (
                    "\\documentclass{book}\n"
                    "\\begin{document}\n"
                    "\\input{chapters/chapter1}\n"
                    "\\input{chapters/chapter2}\n"
                    "\\input{appendices/appendix_a}\n"
                    "\\end{document}\n"
                )

                # Create chapter files
                chapter1_content = "\\chapter{First Chapter}\n" "Chapter 1 content.\n"

                chapter2_content = "\\chapter{Second Chapter}\n" "Chapter 2 content.\n"

                appendix_content = (
                    "\\appendix\n" "\\chapter{Appendix A}\n" "Appendix content.\n"
                )

                # Write all files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapters/chapter1.tex", "w") as f:
                    f.write(chapter1_content)

                with open("chapters/chapter2.tex", "w") as f:
                    f.write(chapter2_content)

                with open("appendices/appendix_a.tex", "w") as f:
                    f.write(appendix_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all content is included
                assert "\\chapter{First Chapter}" in result
                assert "\\chapter{Second Chapter}" in result
                assert "\\chapter{Appendix A}" in result
                assert "Chapter 1 content." in result
                assert "Chapter 2 content." in result
                assert "Appendix content." in result

                # Verify include markers with paths
                assert ">>> input{chapters/chapter1} >>>" in result
                assert ">>> input{chapters/chapter2} >>>" in result
                assert ">>> input{appendices/appendix_a} >>>" in result

            finally:
                os.chdir(original_cwd)


class TestConfigurationOptions:
    """Integration tests for different configuration options."""

    def test_custom_graphics_extensions(self) -> None:
        """Test flattening with custom graphics extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{figure1}\n"
                    "\\includegraphics{figure2}\n"
                    "\\end{document}\n"
                )

                # Create images with different extensions
                with open("figure1.svg", "wb") as f:
                    f.write(b"fake SVG data")

                with open("figure2.tiff", "wb") as f:
                    f.write(b"fake TIFF data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening with custom extensions
                config = LatexExpandConfig(
                    root_directory=".", graphic_extensions=[".svg", ".tiff"]
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify custom extensions are found
                assert "\\includegraphics{figure1.svg}" in result
                assert "\\includegraphics{figure2.tiff}" in result

                # Verify files are copied
                assert os.path.exists("output/figure1.svg")
                assert os.path.exists("output/figure2.tiff")

            finally:
                os.chdir(original_cwd)

    def test_custom_root_directory(self) -> None:
        """Test flattening with custom root directory configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("project/src")
                os.makedirs("project/output")

                # Create main document in subdirectory
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{chapter}\n"
                    "\\end{document}\n"
                )

                chapter_content = "Chapter content.\n"

                with open("project/src/main.tex", "w") as f:
                    f.write(main_content)

                with open("project/src/chapter.tex", "w") as f:
                    f.write(chapter_content)

                # Test flattening with custom root directory
                config = LatexExpandConfig(root_directory="project/src")
                expander = LatexExpander(config)
                result = expander.flatten_latex(
                    "project/src/main.tex", "project/output/main_flat.tex"
                )

                # Verify content is included
                assert "Chapter content." in result
                assert os.path.exists("project/output/main_flat.tex")

            finally:
                os.chdir(original_cwd)


class TestPerformanceAndLimits:
    """Integration tests for performance and system limits."""

    def test_large_number_of_includes(self) -> None:
        """Test flattening document with many include files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with many includes
                num_files = 50
                main_content = "\\documentclass{article}\n\\begin{document}\n"

                for i in range(num_files):
                    main_content += f"\\input{{file{i:03d}}}\n"

                main_content += "\\end{document}\n"

                # Create many small files
                for i in range(num_files):
                    with open(f"file{i:03d}.tex", "w") as f:
                        f.write(f"Content of file {i:03d}.\n")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all files are included
                for i in range(num_files):
                    assert f"Content of file {i:03d}." in result
                    assert f">>> input{{file{i:03d}}} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_deeply_nested_includes(self) -> None:
        """Test flattening with deeply nested include structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create deeply nested structure
                depth = 20

                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{level000}\n"
                    "\\end{document}\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                # Create nested files
                for i in range(depth):
                    content = f"Level {i:03d} content.\n"
                    if i < depth - 1:
                        content += f"\\input{{level{i+1:03d}}}\n"

                    with open(f"level{i:03d}.tex", "w") as f:
                        f.write(content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all levels are included
                for i in range(depth):
                    assert f"Level {i:03d} content." in result
                    assert f">>> input{{level{i:03d}}} >>>" in result

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
