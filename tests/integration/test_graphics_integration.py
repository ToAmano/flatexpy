"""Integration tests for graphics file handling."""

import os
import tempfile

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander


class TestGraphicsIntegration:
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

    def test_multiple_graphicspath_directories(self) -> None:
        """Test graphics with multiple directories in \\graphicspath."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("figures")
                os.makedirs("images")

                # Create main document with multiple graphics paths
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\graphicspath{{figures/}{images/}}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{chart1}\n"
                    "\\includegraphics{chart2}\n"
                    "\\end{document}\n"
                )

                # Create images in different subdirectories
                with open("figures/chart1.png", "wb") as f:
                    f.write(b"chart1 data")

                with open("images/chart2.jpg", "wb") as f:
                    f.write(b"chart2 data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify both graphics are found and updated
                assert "\\includegraphics{chart1.png}" in result
                assert "\\includegraphics{chart2.jpg}" in result

                # Verify both files are copied
                assert os.path.exists("output/chart1.png")
                assert os.path.exists("output/chart2.jpg")

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

    def test_graphics_in_included_files(self) -> None:
        """Test graphics handling in included files."""
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
                    "\\input{chapter_with_graphics}\n"
                    "\\end{document}\n"
                )

                # Create included file with graphics
                chapter_content = (
                    "\\section{Results}\n"
                    "Here are the results:\n"
                    "\\includegraphics{result_plot}\n"
                    "\\includegraphics[width=0.8\\textwidth]{comparison}\n"
                )

                # Create graphics files
                with open("figures/result_plot.pdf", "wb") as f:
                    f.write(b"result plot data")

                with open("figures/comparison.png", "wb") as f:
                    f.write(b"comparison plot data")

                # Write files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapter_with_graphics.tex", "w") as f:
                    f.write(chapter_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify graphics in included content are processed
                assert "\\includegraphics{result_plot.pdf}" in result
                assert (
                    "\\includegraphics[width=0.8\\textwidth]{comparison.png}" in result
                )

                # Verify files are copied
                assert os.path.exists("output/result_plot.pdf")
                assert os.path.exists("output/comparison.png")

                # Verify include markers are present
                assert ">>> input{chapter_with_graphics} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_graphics_with_custom_extensions(self) -> None:
        """Test graphics handling with custom file extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{diagram}\n"
                    "\\includegraphics{photo}\n"
                    "\\end{document}\n"
                )

                # Create images with custom extensions
                with open("diagram.svg", "wb") as f:
                    f.write(b"SVG diagram data")

                with open("photo.tiff", "wb") as f:
                    f.write(b"TIFF photo data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening with custom extensions
                config = LatexExpandConfig(
                    root_directory=".", graphic_extensions=[".svg", ".tiff", ".png"]
                )
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify custom extensions are found and processed
                assert "\\includegraphics{diagram.svg}" in result
                assert "\\includegraphics{photo.tiff}" in result

                # Verify files are copied
                assert os.path.exists("output/diagram.svg")
                assert os.path.exists("output/photo.tiff")

            finally:
                os.chdir(original_cwd)

    def test_graphics_file_name_conflicts(self) -> None:
        """Test handling when graphics files have same name but different paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("figures1")
                os.makedirs("figures2")

                # Create main document
                main_content = (
                    "\\documentclass{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\begin{document}\n"
                    "\\includegraphics{figures1/chart}\n"
                    "\\includegraphics{figures2/chart}\n"
                    "\\end{document}\n"
                )

                # Create files with same name in different directories
                with open("figures1/chart.png", "wb") as f:
                    f.write(b"chart1 data")

                with open("figures2/chart.png", "wb") as f:
                    f.write(b"chart2 data")

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # The second file will overwrite the first due to same basename
                # This is expected behavior - user should be aware of naming conflicts
                assert os.path.exists("output/chart.png")

                # Both references should be updated to just the filename
                assert "\\includegraphics{chart.png}" in result

            finally:
                os.chdir(original_cwd)
