# flatexpy

[![PyPI version](https://badge.fury.io/py/flatexpy.svg)](https://badge.fury.io/py/flatexpy)
[![Python versions](https://img.shields.io/pypi/pyversions/flatexpy.svg)](https://pypi.org/project/flatexpy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/ToAmano/flatexpy/workflows/Tests/badge.svg)](https://github.com/ToAmano/flatexpy/actions)
[![Coverage](https://codecov.io/gh/ToAmano/flatexpy/branch/main/graph/badge.svg)](https://codecov.io/gh/ToAmano/flatexpy)

A LaTeX flattening utility for academic paper submission that recursively processes `\input` and `\include` commands, copies referenced graphics, and produces a single consolidated LaTeX file.

## Features

- **Flattens LaTeX documents** by recursively processing `\input` and `\include` commands
- **Copies graphics files** referenced by `\includegraphics` to the output directory
- **Supports `\graphicspath`** command for flexible graphics organization
- **Preserves document structure** with clear include markers
- **Handles circular dependencies** gracefully
- **Configurable graphics extensions** (PDF, PNG, JPG, EPS, etc.)
- **Comment handling** with preservation options
- **Cross-platform** support (Windows, macOS, Linux)
- **Type-safe** with full type annotations
- **Comprehensive testing** with high coverage

## Installation

### From PyPI (Recommended)

```bash
pip install flatexpy
```

### From conda-forge

```bash
conda install -c conda-forge flatexpy
```

### From Source

```bash
git clone https://github.com/ToAmano/flatexpy.git
cd flatexpy
pip install -e .
```

## Quick Start

### Command Line Usage

```bash
# Basic usage
flatexpy input.tex

# Specify output directory
flatexpy input.tex -o output_directory/

# Custom graphics extensions
flatexpy input.tex --graphics-exts .png .jpg .svg

# Verbose output
flatexpy input.tex -v
```

### Python API Usage

```python
from flatexpy import LatexExpander, LatexExpandConfig

# Basic usage
expander = LatexExpander()
result = expander.flatten_latex("input.tex", "output/flattened.tex")

# Custom configuration
config = LatexExpandConfig(
    graphic_extensions=[".png", ".jpg", ".pdf"],
    ignore_commented_lines=True,
    root_directory=".",
    output_encoding="utf-8"
)
expander = LatexExpander(config)
result = expander.flatten_latex("input.tex", "output/flattened.tex")
```

## Use Cases

### Academic Paper Submission

Many academic journals require submission of a single LaTeX file. flatexpy helps by:

1. **Combining multiple files**: Merges your modular LaTeX project into one file
2. **Including graphics**: Copies all referenced images to the output directory
3. **Maintaining structure**: Keeps track of original file organization with markers

### Example Workflow

```bash
# Original project structure
paper/
├── main.tex
├── sections/
│   ├── introduction.tex
│   ├── methodology.tex
│   └── results.tex
├── figures/
│   ├── diagram1.pdf
│   └── plot1.png
└── bibliography.bib

# Flatten the document
flatexpy main.tex -o submission/

# Result
submission/
├── main_flattened.tex  # Single file with all content
├── diagram1.pdf        # Copied graphics
└── plot1.png
```

## Configuration Options

### Command Line Arguments

- `input_file`: Input LaTeX file to flatten
- `-o, --output`: Output directory (default: `flat/`)
- `--graphics-exts`: Graphics file extensions to search for
- `--ignore-comments`: Ignore commented lines (default: True)
- `-v, --verbose`: Enable verbose logging

### Python Configuration

```python
from flatexpy import LatexExpandConfig

config = LatexExpandConfig(
    graphic_extensions=[".pdf", ".png", ".jpg", ".jpeg", ".eps"],
    ignore_commented_lines=True,
    root_directory=".",
    output_encoding="utf-8"
)
```

## Advanced Features

### Graphics Path Handling

flatexpy automatically processes `\graphicspath` commands:

```latex
\graphicspath{{figures/}{images/}}
\includegraphics{plot1}  % Finds figures/plot1.png or images/plot1.png
```

### Include Markers

The flattened output includes markers showing original file structure:

```latex
% >>> input{sections/introduction} >>>
\section{Introduction}
This is the introduction content.
% <<< input{sections/introduction} <<<
```

### Circular Dependency Detection

flatexpy detects and handles circular includes gracefully, preventing infinite loops.

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/ToAmano/flatexpy.git
cd flatexpy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=flatexpy

# Run specific test file
pytest tests/test_integration.py
```

### Code Quality

```bash
# Format code
black flatexpy tests
isort flatexpy tests

# Lint code
flake8 flatexpy tests
mypy flatexpy

# Run all quality checks
tox -e lint
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Types of Contributions

- Bug reports and fixes
- Feature requests and implementations
- Documentation improvements
- Test coverage improvements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Support

- **Bug Reports**: [GitHub Issues](https://github.com/ToAmano/flatexpy/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/ToAmano/flatexpy/discussions)
- **Documentation**: [GitHub README](https://github.com/ToAmano/flatexpy#readme)

## Similar Projects

- [latexpand](https://www.ctan.org/pkg/latexpand) - Perl-based LaTeX flattening tool
- [flatlatex](https://pypi.org/project/flatlatex/) - Another Python LaTeX flattening tool

## Acknowledgments

- Inspired by the need for easier academic paper submission workflows
- Built with modern Python best practices and comprehensive testing
