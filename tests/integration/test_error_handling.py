"""Integration tests for error conditions and edge cases."""

import os
import tempfile

import pytest

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander, LatexExpandError


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

    def test_nonexistent_input_file(self) -> None:
        """Test error when main input file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                os.makedirs("output")

                # Test flattening nonexistent file
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)

                with pytest.raises(LatexExpandError):
                    expander.flatten_latex("nonexistent.tex", "output/out.tex")

            finally:
                os.chdir(original_cwd)

    def test_permission_denied_input_file(self) -> None:
        """Test error when input file cannot be read due to permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create a file and remove read permissions
                test_file = "restricted.tex"
                with open(test_file, "w") as f:
                    f.write(
                        "\\documentclass{article}\\begin{document}Test\\end{document}"
                    )

                # Remove read permissions (Unix only)
                if hasattr(os, "chmod"):
                    os.chmod(test_file, 0o000)

                    os.makedirs("output")

                    # Test flattening
                    config = LatexExpandConfig(root_directory=".")
                    expander = LatexExpander(config)

                    with pytest.raises(LatexExpandError):
                        expander.flatten_latex(test_file, "output/out.tex")

                    # Restore permissions for cleanup
                    os.chmod(test_file, 0o644)

            finally:
                os.chdir(original_cwd)

    def test_empty_input_file(self) -> None:
        """Test handling of empty input file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create empty file
                with open("empty.tex", "w") as f:
                    pass  # Empty file

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("empty.tex", "output/empty_flat.tex")

                # Should produce empty output
                assert result == ""
                assert os.path.exists("output/empty_flat.tex")

                with open("output/empty_flat.tex", "r") as f:
                    assert f.read() == ""

            finally:
                os.chdir(original_cwd)

    def test_deeply_nested_circular_dependency(self) -> None:
        """Test deeply nested circular dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create chain: main -> level1 -> level2 -> level3 -> level1
                files = {
                    "main.tex": "\\documentclass{article}\\begin{document}\\input{level1}\\end{document}",
                    "level1.tex": "Level1 \n \\input{level2}",
                    "level2.tex": "Level2 \n \\input{level3}",
                    "level3.tex": "Level3 \n \\input{level1}",  # Circular back to level1
                }

                for filename, content in files.items():
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Should include each level only once
                assert result.count("Level1") == 1
                assert result.count("Level2") == 1
                assert result.count("Level3") == 1

            finally:
                os.chdir(original_cwd)

    def test_invalid_latex_syntax(self) -> None:
        """Test handling of files with invalid LaTeX syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create file with malformed LaTeX commands
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{malformed_file}\n"
                    "\\end{document}\n"
                )

                malformed_content = (
                    "\\input{incomplete\n"  # Missing closing brace
                    "\\includegraphics[width=\n"  # Incomplete command
                    "Normal text\n"
                )

                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("malformed_file.tex", "w") as f:
                    f.write(malformed_content)

                os.makedirs("output")

                # Test flattening (should handle malformed commands gracefully)
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Should include the malformed content as-is
                assert "\\input{incomplete" in result
                assert "\\includegraphics[width=" in result
                assert "Normal text" in result

            finally:
                os.chdir(original_cwd)

    def test_binary_file_inclusion_attempt(self) -> None:
        """Test handling when trying to include binary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create main document trying to include binary file
                main_content = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "\\input{binary_file}\n"
                    "\\end{document}\n"
                )

                # Create a binary file with .tex extension
                with open("binary_file.tex", "wb") as f:
                    f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")  # PNG header

                with open("main.tex", "w") as f:
                    f.write(main_content)

                os.makedirs("output")

                # Test flattening (should handle binary content gracefully or error)
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)

                # This might raise an error or handle it gracefully depending on implementation
                try:
                    result = expander.flatten_latex("main.tex", "output/main_flat.tex")
                    # If it succeeds, the binary content might be garbled but shouldn't crash
                    assert isinstance(result, str)
                except (LatexExpandError, UnicodeDecodeError):
                    # This is also acceptable behavior for binary files
                    pass

            finally:
                os.chdir(original_cwd)
