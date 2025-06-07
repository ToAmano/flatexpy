"""Basic integration tests for common use cases."""

import os
import tempfile

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander


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

    def test_include_vs_input_commands(self) -> None:
        """Test that both \\input and \\include commands work."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document with both input and include
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{chapter1}\n"
                    "\\include{chapter2}\n"
                    "\\end{document}\n"
                )

                # Create included files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapter1.tex", "w") as f:
                    f.write("Chapter 1 via input\n")

                with open("chapter2.tex", "w") as f:
                    f.write("Chapter 2 via include\n")

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify both are included
                assert "Chapter 1 via input" in result
                assert "Chapter 2 via include" in result
                assert ">>> input{chapter1} >>>" in result
                assert ">>> include{chapter2} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_file_extensions_handling(self) -> None:
        """Test handling of files with and without .tex extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document that includes files with/without extension
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{chapter1}\n"  # Without .tex
                    "\\input{chapter2.tex}\n"  # With .tex
                    "\\end{document}\n"
                )

                # Create included files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapter1.tex", "w") as f:
                    f.write("Chapter 1 content\n")

                with open("chapter2.tex", "w") as f:
                    f.write("Chapter 2 content\n")

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify both are included correctly
                assert "Chapter 1 content" in result
                assert "Chapter 2 content" in result

            finally:
                os.chdir(original_cwd)
