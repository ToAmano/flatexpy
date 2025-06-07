# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2024-01-XX

### Added
- Initial release of flatexpy
- LaTeX document flattening functionality
- Support for `\input` and `\include` commands
- Graphics file handling with `\includegraphics`
- Support for `\graphicspath` command
- Automatic graphics file copying to output directory
- Configurable graphics file extensions
- Comment handling and preservation
- Circular dependency detection
- Command-line interface
- Comprehensive test suite
- Type annotations for better IDE support

### Features
- Flattens LaTeX documents by recursively processing includes
- Copies referenced graphics files to output directory
- Preserves document structure with include markers
- Handles nested includes correctly
- Supports custom configuration options
- Cross-platform compatibility (Windows, macOS, Linux)
- Python 3.8+ support

[Unreleased]: https://github.com/ToAmano/flatexpy/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ToAmano/flatexpy/releases/tag/v1.0.0
