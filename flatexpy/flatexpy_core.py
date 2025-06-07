"""LaTeX flattening utility for academic paper submission.

This module provides functionality to flatten LaTeX documents by recursively
processing `input` and `include` commands, copying referenced graphics, and
producing a single consolidated LaTeX file.
"""

import argparse
import logging
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Tuple


def _setup_logger() -> logging.Logger:
    """Set up logging configuration."""
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.INFO)

    if not _logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        _logger.addHandler(handler)

    return _logger


logger = _setup_logger()


@dataclass
class LatexExpandConfig:
    """Configuration for LaTeX expansion operations."""

    graphic_extensions: List[str] = field(
        default_factory=lambda: [".pdf", ".png", ".jpg", ".jpeg", ".eps"]
    )
    ignore_commented_lines: bool = True
    root_directory: str = "."
    output_encoding: str = "utf-8"


class LatexExpandError(Exception):
    """Base exception for LaTeX expansion operations."""


class GraphicsNotFoundError(LatexExpandError):
    """Raised when a graphics file cannot be found."""


def _create_output_dir(output_dir: str, is_overwrite: bool) -> None:
    """create output directory if not exists"""
    path = Path(output_dir)
    if is_overwrite or (not path.exists()):
        os.makedirs(path, exist_ok=True)
    else:
        raise FileExistsError(f" Directory exists: {output_dir} :: {is_overwrite}")


class LatexExpander:
    """Handles LaTeX document flattening and graphics collection."""

    def __init__(self, config: Optional[LatexExpandConfig] = None) -> None:
        """Initialize the LaTeX expander.

        Args:
            config: Configuration object. If None, uses default configuration.
        """
        self.config = config or LatexExpandConfig()

        # Compiled regex patterns for better performance
        self._input_pattern = re.compile(r"\\(input|include)\{([^}]+)\}")
        self._graphicspath_pattern = re.compile(r"\\graphicspath\{((\{[^}]+\})+)\}")
        self._includegraphics_pattern = re.compile(
            r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
        )

        # State tracking
        self._visited_files: Set[str] = set()
        self._graphics_paths: List[str] = []
        self._collected_graphics: Set[str] = set()

    def _resolve_file_path(self, file_path: str) -> Path:
        """Resolve file path and check existence.

        Args:
            file_path: Path to resolve.

        Returns:
            Resolved Path object.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        path = Path(file_path)
        if not path.exists():
            # Try adding .tex extension
            tex_path = path.with_suffix(".tex")
            if tex_path.exists():
                return tex_path
            raise FileNotFoundError(
                f"Coud not resolve filepath, File not found: {file_path}"
            )
        return path

    def _is_line_commented(self, line: str) -> bool:
        """Check if a line is commented out.

        Args:
            line: Line to check.

        Returns:
            True if line is commented, False otherwise.
        """
        return line.lstrip().startswith("%")

    def _extract_graphics_paths(self, line: str) -> List[str]:
        """Extract graphics paths from \\graphicspath command.

        Args:
            line: Line to parse.

        Returns:
            List of extracted paths.
        """
        match = self._graphicspath_pattern.search(line)
        if not match:
            return []

        paths_str = match.group(1)
        paths = re.findall(r"\{([^}]+)\}", paths_str)
        return [os.path.normpath(path) for path in paths]

    def _add_extension_to_filename(self, filename: str, ext: str) -> str:
        """Add extension to filename if not exists.

        Args:
            filename: Name of file (may be without extension).
            ext: extension to add (eg. .pdf, .png)

        Returns:
            Full filename with extension.
        """
        if not ext.startswith("."):
            raise ValueError(f"ext should start with `.` :: got {ext} ")
        has_ext: bool = bool(os.path.splitext(filename)[1])
        if not has_ext:  # without extension
            candidate_with_ext = filename + ext
        else:
            candidate_with_ext = filename
        return candidate_with_ext

    def _find_graphics_file(self, graphic_name: str, search_dir: str) -> Optional[str]:
        """Find graphics file with possible extensions.

        Args:
            graphic_name: Name of graphics file (may be without extension).
            search_dir: Directory to search in.

        Returns:
            Full path to graphics file if found, None otherwise.
        """
        search_paths: List[str] = [search_dir] + self._graphics_paths

        for search_path in search_paths:
            candidate = os.path.join(search_path, graphic_name)
            for ext in self.config.graphic_extensions:
                candidate_with_ext = self._add_extension_to_filename(candidate, ext)
                if os.path.exists(candidate_with_ext):
                    return candidate_with_ext
        logger.warning("No graphic file found :: %s", graphic_name)
        return None

    def _copy_graphics_file(self, source_path: str, dest_dir: str) -> None:
        """Copy graphics file to root directory.

        Args:
            source_path: Source path of graphics file.
            dest_dir: Destination directory to copy to.
        """
        if source_path in self._collected_graphics:
            return

        filename: str = os.path.basename(source_path)
        dest_path: str = os.path.join(dest_dir, filename)

        try:
            shutil.copy2(source_path, dest_path)
            self._collected_graphics.add(source_path)
            logger.info("Copied graphics: %s -> %s", source_path, dest_path)
        except IOError as e:
            raise LatexExpandError(f"Failed to copy graphics file: {e}") from e

    def _process_includegraphics(
        self, line: str, root_dir: str, output_dir: str
    ) -> str:
        """Process \\includegraphics commands in a line.

        Args:
            line: Line to process.
            current_dir: Current directory context.
            output_dir: Output directory for copying files.
        """
        match = self._includegraphics_pattern.search(line)
        if not match:
            return line
        graphic_name: str = match.group(1)
        graphics_path = self._find_graphics_file(graphic_name, root_dir)
        if graphics_path:
            filename: str = os.path.basename(graphics_path)
            self._copy_graphics_file(graphics_path, output_dir)
            line = line.replace(graphic_name, filename)
            return line
        logger.warning("Graphics file not found: \\includegraphics{%s}", graphic_name)
        return line

    def _process_input_include(
        self,
        line: str,
        root_dir: str,
        output_dir: str,
    ) -> Tuple[str, bool]:
        """Process \\input or \\include commands.

        Args:
            line: Line to process.
            root_dir: Root directory.
            output_dir: Output directory.

        Returns:
            Tuple of (processed_content, was_processed).
        """
        match = self._input_pattern.search(line)
        if not match:
            return line, False

        cmd, relative_path = match.groups()
        include_path = os.path.join(root_dir, relative_path)

        if not include_path.endswith(".tex"):
            include_path += ".tex"

        try:
            resolved_path = self._resolve_file_path(include_path)
            logger.info("Processing %s: %s", cmd, include_path)

            included_content = self._flatten_file(
                str(resolved_path), root_dir, output_dir
            )

            result = (
                f"% >>> {cmd}{{{relative_path}}} >>>\n"
                f"{included_content}"
                f"% <<< {cmd}{{{relative_path}}} <<<\n"
            )
            return result, True

        except FileNotFoundError:
            logger.warning(" Failed to process input, File not found: %s", include_path)
            return line, False

    def _read_file(self, file_path: str) -> List[str]:
        """Read a file to list of lines

        Args:
            file_path: File path to be read.

        Returns:
            List of lines.
        """
        try:
            with open(file_path, "r", encoding=self.config.output_encoding) as f:
                lines = f.readlines()
        except IOError as e:
            raise LatexExpandError(f"Failed to read file {file_path}: {e}") from e
        return lines

    def _update_graphics_path(self, line: str) -> None:
        """Update self._graphics_path from line.

        Args:
            line: Content to be parsed.

        Returns:
            None
        """
        new_graphics_paths = self._extract_graphics_paths(line)
        for path in new_graphics_paths:
            if path not in self._graphics_paths:
                self._graphics_paths.append(path)
        if new_graphics_paths:
            logger.info("Updated graphics paths: %s", self._graphics_paths)

    def _flatten_file(self, file_path: str, root_dir: str, output_dir: str) -> str:
        """Flatten a single LaTeX file.

        Args:
            file_path: Path to file to flatten.
            root_dir: Root directory.
            output_dir: Output directory.

        Returns:
            Flattened content as string.
        """
        abs_path: str = os.path.abspath(file_path)
        if abs_path in self._visited_files:
            logger.info("Skipping already included file: %s", file_path)
            return ""
        self._visited_files.add(abs_path)

        # read a file
        lines = self._read_file(file_path)

        flattened_content: List[str] = []

        for line in lines:
            # Skip commented lines if configured
            if self.config.ignore_commented_lines and self._is_line_commented(line):
                flattened_content.append(line)
                continue

            # Process graphics paths
            self._update_graphics_path(line)

            # Process includegraphics and update line
            line = self._process_includegraphics(line, root_dir, output_dir)

            # Process input/include
            processed_line, _ = self._process_input_include(line, root_dir, output_dir)
            flattened_content.append(processed_line)

        return "".join(flattened_content)

    def flatten_latex(self, input_file: str, output_file: str) -> str:
        """Flatten a LaTeX document.

        Args:
            input_file: Path to input LaTeX file.
            output_file: Path to output file. If None, returns content only.

        Returns:
            Flattened LaTeX content.

        Raises:
            LatexExpandError: If flattening fails.
        """
        try:
            input_path = self._resolve_file_path(input_file)
            root_dir = self.config.root_directory
            output_dir: str = os.path.split(output_file)[0]

            # Reset state for new operation
            self._visited_files.clear()
            self._graphics_paths.clear()
            self._collected_graphics.clear()

            logger.info("Starting LaTeX flattening: %s to %s", input_file, output_file)
            flattened_content = self._flatten_file(
                str(input_path), root_dir, output_dir
            )

            if output_file:
                with open(output_file, "w", encoding=self.config.output_encoding) as f:
                    f.write(flattened_content)
                logger.info("Flattened LaTeX written to: %s", output_file)

            return flattened_content

        except Exception as e:
            raise LatexExpandError(f"Failed to flatten LaTeX: {e}") from e

    def show_config(self) -> None:
        """show configuration"""
        logger.info("graphic_extensions     :: %s", self.config.graphic_extensions)
        logger.info("ignore_commented_lines :: %s", self.config.ignore_commented_lines)
        logger.info("root_directory         :: %s", self.config.root_directory)
        logger.info("output_encoding        :: %s", self.config.output_encoding)


def main() -> None:
    """Main entry point for command-line usage."""
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

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine output file
    input_path = Path(args.input_file)
    output_path = args.output
    output_file = os.path.join(
        output_path, f"{input_path.stem}_flattened{input_path.suffix}"
    )

    # extract root dir
    root_dir = os.path.dirname(args.input_file) or "./"

    # Create configuration
    config = LatexExpandConfig(
        graphic_extensions=args.graphics_exts,
        ignore_commented_lines=args.ignore_comments,
        root_directory=root_dir,
    )

    # Perform flattening
    try:
        _create_output_dir(output_path, args.force)
        expander = LatexExpander(config)
        expander.flatten_latex(args.input_file, output_file)
        print(f"Successfully flattened {args.input_file} to {output_file}")
    except (LatexExpandError, FileExistsError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
