"""Integration tests for different configuration options."""

import os
import tempfile

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander


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

                # Create images with custom extensions
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

    def test_ignore_commented_lines_disabled(self) -> None:
        """Test with ignore_commented_lines set to False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with commented content
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "% This is a comment\n"
                    "Regular content\n"
                    "\\input{chapter}\n"
                    "\\end{document}\n"
                )

                chapter_content = (
                    "% Chapter comment\n" "Chapter content\n" "% Another comment\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapter.tex", "w") as f:
                    f.write(chapter_content)

                os.makedirs("output")

                # Test with ignore_commented_lines=False
                config = LatexExpandConfig(
                    root_directory=".", ignore_commented_lines=False
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # All content should be processed normally
                assert "% This is a comment" in result
                assert "Regular content" in result
                assert "Chapter content" in result
                assert "% Chapter comment" in result

            finally:
                os.chdir(original_cwd)

    def test_custom_output_encoding(self) -> None:
        """Test flattening with custom output encoding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with special characters
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage[utf8]{inputenc}\n"
                    "\\begin{document}\n"
                    "Special characters: ñáéíóú\n"
                    "\\input{chapter_with_accents}\n"
                    "\\end{document}\n"
                )

                chapter_content = (
                    "More special characters: ü ö ä ß\n" "Greek letters: α β γ δ ε\n"
                )

                # Write files with UTF-8 encoding
                with open("main.tex", "w", encoding="utf-8") as f:
                    f.write(main_content)

                with open("chapter_with_accents.tex", "w", encoding="utf-8") as f:
                    f.write(chapter_content)

                os.makedirs("output")

                # Test with UTF-8 encoding
                config = LatexExpandConfig(root_directory=".", output_encoding="utf-8")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify special characters are preserved
                assert "ñáéíóú" in result
                assert "ü ö ä ß" in result
                assert "α β γ δ ε" in result

                # Verify output file has correct encoding
                with open("output/main_flat.tex", "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "ñáéíóú" in content
                    assert "ü ö ä ß" in content

            finally:
                os.chdir(original_cwd)

    def test_mixed_graphics_extensions(self) -> None:
        """Test with mix of default and custom graphics extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{standard_png}\n"
                    "\\includegraphics{standard_pdf}\n"
                    "\\includegraphics{custom_svg}\n"
                    "\\includegraphics{custom_webp}\n"
                    "\\end{document}\n"
                )

                # Create images with different extensions
                files = {
                    "standard_png.png": b"PNG data",
                    "standard_pdf.pdf": b"PDF data",
                    "custom_svg.svg": b"SVG data",
                    "custom_webp.webp": b"WebP data",
                }

                for filename, data in files.items():
                    with open(filename, "wb") as f:
                        f.write(data)

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test with mixed extensions
                config = LatexExpandConfig(
                    root_directory=".",
                    graphic_extensions=[".png", ".pdf", ".svg", ".webp"],
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all graphics are found
                assert "\\includegraphics{standard_png.png}" in result
                assert "\\includegraphics{standard_pdf.pdf}" in result
                assert "\\includegraphics{custom_svg.svg}" in result
                assert "\\includegraphics{custom_webp.webp}" in result

                # Verify all files are copied
                for filename in files.keys():
                    assert os.path.exists(f"output/{filename}")

            finally:
                os.chdir(original_cwd)

    def test_configuration_with_subdirectory_graphics(self) -> None:
        """Test configuration options with graphics in subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("images/photos")
                os.makedirs("images/diagrams")

                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\graphicspath{{images/photos/}{images/diagrams/}}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{photo1}\n"
                    "\\includegraphics{diagram1}\n"
                    "\\end{document}\n"
                )

                # Create graphics with custom extensions
                with open("images/photos/photo1.heic", "wb") as f:
                    f.write(b"HEIC photo data")

                with open("images/diagrams/diagram1.drawio", "wb") as f:
                    f.write(b"DrawIO diagram data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test with custom extensions for specific file types
                config = LatexExpandConfig(
                    root_directory=".",
                    graphic_extensions=[".heic", ".drawio", ".png", ".pdf"],
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify custom extensions work with graphicspath
                assert "\\includegraphics{photo1.heic}" in result
                assert "\\includegraphics{diagram1.drawio}" in result

                # Verify files are copied
                assert os.path.exists("output/photo1.heic")
                assert os.path.exists("output/diagram1.drawio")

            finally:
                os.chdir(original_cwd)

    def test_configuration_inheritance(self) -> None:
        """Test that configuration is properly inherited in nested operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with nested includes
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{level1}\n"
                    "\\end{document}\n"
                )

                level1_content = "Level 1 content\n" "\\input{level2}\n"

                level2_content = "Level 2 content\n" "Special chars: ñáéíóú\n"

                # Write files
                with open("main.tex", "w", encoding="utf-8") as f:
                    f.write(main_content)

                with open("level1.tex", "w", encoding="utf-8") as f:
                    f.write(level1_content)

                with open("level2.tex", "w", encoding="utf-8") as f:
                    f.write(level2_content)

                os.makedirs("output")

                # Test with custom configuration
                config = LatexExpandConfig(
                    root_directory=".",
                    output_encoding="utf-8",
                    ignore_commented_lines=True,
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify configuration is applied at all levels
                assert "Level 1 content" in result
                assert "Level 2 content" in result
                assert "ñáéíóú" in result

                # Verify nested includes work with configuration
                assert ">>> input{level1} >>>" in result
                assert ">>> input{level2} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_default_vs_custom_configuration(self) -> None:
        """Test difference between default and custom configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create test document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{image}\n"
                    "\\end{document}\n"
                )

                # Create images with different extensions
                with open("image.png", "wb") as f:
                    f.write(b"PNG data")

                with open("image.webp", "wb") as f:
                    f.write(b"WebP data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output1")
                os.makedirs("output2")

                # Test with default configuration
                default_expander = LatexExpander()  # Uses default config
                result1 = default_expander.flatten_latex(
                    "main.tex", "output1/main_flat.tex"
                )

                # Test with custom configuration
                custom_config = LatexExpandConfig(
                    graphic_extensions=[
                        ".webp",
                        ".png",
                    ]  # Different order, includes webp
                )
                custom_expander = LatexExpander(custom_config)
                result2 = custom_expander.flatten_latex(
                    "main.tex", "output2/main_flat.tex"
                )

                # Default should find PNG (first in default list)
                assert "\\includegraphics{image.png}" in result1
                assert os.path.exists("output1/image.png")

                # Custom should find WebP (first in custom list)
                assert "\\includegraphics{image.webp}" in result2
                assert os.path.exists("output2/image.webp")

            finally:
                os.chdir(original_cwd)
