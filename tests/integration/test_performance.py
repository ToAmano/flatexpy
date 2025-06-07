"""Integration tests for performance and system limits."""

import os
import tempfile

import pytest

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander


class TestPerformance:
    """Integration tests for performance and system limits."""

    @pytest.mark.slow
    def test_large_number_of_includes(self) -> None:
        """Test flattening document with many include files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with many includes
                num_files = 100  # Increased from 50 for more stress testing
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

                # Verify output file exists and has reasonable size
                assert os.path.exists("output/main_flat.tex")
                file_size = os.path.getsize("output/main_flat.tex")
                assert file_size > 0

            finally:
                os.chdir(original_cwd)

    @pytest.mark.slow
    def test_deeply_nested_includes(self) -> None:
        """Test flattening with deeply nested include structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create deeply nested structure
                depth = 50  # Increased from 20 for more stress testing

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

    def test_large_file_content(self) -> None:
        """Test flattening with large file content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{large_content}\n"
                    "\\end{document}\n"
                )

                # Create large content file
                large_content = ""
                for i in range(1000):  # Create 1000 lines of content
                    large_content += f"This is line {i:04d} of the large content file. "
                    large_content += (
                        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                    )
                    large_content += "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n"

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("large_content.tex", "w") as f:
                    f.write(large_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify large content is included
                assert "This is line 0000" in result
                assert "This is line 0999" in result
                assert len(result) > len(
                    large_content
                )  # Should include wrapper content

            finally:
                os.chdir(original_cwd)

    def test_many_graphics_files(self) -> None:
        """Test flattening with many graphics files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("figures")

                # Create main document with many graphics
                num_graphics = 50
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\graphicspath{{figures/}}\n"
                    "\\begin{document}\n"
                )

                for i in range(num_graphics):
                    main_content += f"\\includegraphics{{figure{i:03d}}}\n"

                main_content += "\\end{document}\n"

                # Create many graphics files
                for i in range(num_graphics):
                    ext = [".png", ".jpg", ".pdf"][i % 3]  # Vary extensions
                    filename = f"figures/figure{i:03d}{ext}"
                    with open(filename, "wb") as f:
                        f.write(f"fake figure {i:03d} data".encode())

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all graphics are processed
                for i in range(num_graphics):
                    ext = [".png", ".jpg", ".pdf"][i % 3]
                    assert f"\\includegraphics{{figure{i:03d}{ext}}}" in result
                    assert os.path.exists(f"output/figure{i:03d}{ext}")

            finally:
                os.chdir(original_cwd)

    def test_complex_nested_structure_with_graphics(self) -> None:
        """Test complex nested structure with graphics at each level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("figures")

                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\graphicspath{{figures/}}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{main_figure}\n"
                    "\\input{level1}\n"
                    "\\end{document}\n"
                )

                # Create nested files with graphics at each level
                levels = 10
                for i in range(levels):
                    content = f"\\section{{Level {i+1}}}\n"
                    content += f"Content for level {i+1}.\n"
                    content += f"\\includegraphics{{level{i+1}_figure}}\n"

                    if i < levels - 1:
                        content += f"\\input{{level{i+2}}}\n"

                    with open(f"level{i+1}.tex", "w") as f:
                        f.write(content)

                    # Create graphics file for this level
                    with open(f"figures/level{i+1}_figure.png", "wb") as f:
                        f.write(f"level {i+1} figure data".encode())

                # Create main figure
                with open("figures/main_figure.png", "wb") as f:
                    f.write(b"main figure data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all levels and graphics are processed
                assert "\\includegraphics{main_figure.png}" in result
                for i in range(levels):
                    assert f"Content for level {i+1}." in result
                    assert f"\\includegraphics{{level{i+1}_figure.png}}" in result
                    assert os.path.exists(f"output/level{i+1}_figure.png")

                assert os.path.exists("output/main_figure.png")

            finally:
                os.chdir(original_cwd)

    def test_memory_usage_with_repetitive_content(self) -> None:
        """Test memory efficiency with repetitive content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with many similar includes
                num_files = 20
                main_content = "\\documentclass{article}\n\\begin{document}\n"

                for i in range(num_files):
                    main_content += f"\\input{{chapter{i:02d}}}\n"

                main_content += "\\end{document}\n"

                # Create many files with similar but unique content
                base_content = (
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
                    "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
                    "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                    "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
                    "culpa qui officia deserunt mollit anim id est laborum.\n"
                    * 50  # Repeat 50 times
                )

                for i in range(num_files):
                    content = f"\\section{{Chapter {i+1}}}\n"
                    content += f"Chapter {i+1} specific content.\n"
                    content += base_content

                    with open(f"chapter{i:02d}.tex", "w") as f:
                        f.write(content)

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all chapters are included
                for i in range(num_files):
                    assert f"\\section{{Chapter {i+1}}}" in result
                    assert f"Chapter {i+1} specific content." in result

                # Verify the result is substantial
                assert len(result) > len(base_content) * num_files

            finally:
                os.chdir(original_cwd)

    @pytest.mark.slow
    def test_wide_include_tree(self) -> None:
        """Test flattening with wide include tree (many files at same level)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                width = 30  # Number of files at each level
                depth = 3  # Number of levels

                main_content = "\\documentclass{article}\n\\begin{document}\n"
                for i in range(width):
                    main_content += f"\\input{{level0_file{i:02d}}}\n"
                main_content += "\\end{document}\n"

                # Create wide tree structure
                for level in range(depth):
                    for i in range(width):
                        filename = f"level{level}_file{i:02d}.tex"
                        content = f"Level {level} File {i} content.\n"

                        # Each file at levels 0 and 1 includes files from next level
                        if level < depth - 1:
                            for j in range(width):
                                content += f"\\input{{level{level+1}_file{j:02d}}}\n"

                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(content)

                with open("main.tex", "w", encoding="utf-8") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify content from all levels
                for level in range(depth):
                    for i in range(width):
                        assert f"Level {level} File {i} content." in result

            finally:
                os.chdir(original_cwd)

    def test_performance_with_comments(self) -> None:
        """Test performance with many comments in files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "% Main document comment\n"
                    "\\begin{document}\n"
                    "\\input{commented_file}\n"
                    "\\end{document}\n"
                    "% End comment\n"
                )

                # Create file with many comments
                commented_content = ""
                for i in range(500):  # 500 lines with mix of comments and content
                    if i % 3 == 0:
                        commented_content += f"% Comment line {i}\n"
                    elif i % 3 == 1:
                        commented_content += f"Content line {i}\n"
                    else:
                        commented_content += f"More content {i} % inline comment\n"

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("commented_file.tex", "w") as f:
                    f.write(commented_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify comments and content are preserved
                assert "% Comment line 0" in result
                assert "Content line 1" in result
                assert "% inline comment" in result
                assert ">>> input{commented_file} >>>" in result

            finally:
                os.chdir(original_cwd)
