# GEMINI.md - Development History and Code Conventions

This document records the development history, technical decisions, and code quality conventions of the `flatexpy` project, built collaboratively with the AI assistant "Gemini".

---

## 1. Project Background and Decisions

### Purpose of Development
To provide a Python-native command-line (CLI) utility and library that "easily" flattens modular LaTeX documents recursively (resolving `\input` and `\include`), copies referenced graphics (with support for `\graphicspath`), and generates a single consolidated LaTeX file suitable for academic paper submissions.

### Decision Process
1.  **Survey of Existing Tools**: Evaluated Perl-based `latexpand` and existing Python-based `flatlatex`, identifying a need for a robust, modern, cross-platform Python solution with complete type-safety, direct graphics file copy capabilities, and structured block indicators.
2.  **Naming Decision**: Established the name **`flatexpy`** to reflect its role as a flat LaTeX python utility.
3.  **Include Markers**: Chose to insert clear structured comments (`% >>> input{...} >>>` and `% <<< input{...} <<<`) into the flattened file to facilitate tracing the source of text blocks in the generated output.
4.  **CI and Code Formatting (GitHub Connection)**: Integrated GitHub Actions workflows referencing `ToAmano/cellify` and adapted a strict `pre-commit` hook pipeline using modern linters and formatters.

---

## 2. Development & Coding Conventions

### ① Complete Type Hinting 【Strictly Required】
All Python modules under `flatexpy/` must have **complete type annotations** to ensure static verification, IDE auto-completion, and long-term codebase maintainability.

*   **Function Signatures**: Explicitly annotate parameter types and return types using the `typing` module or standard generic collections.
    ```python
    from typing import List, Optional
    from flatexpy.flatexpy_core import LatexExpandConfig

    def main(args: Optional[List[str]] = None) -> int:
        ...
    ```
*   **Static Analysis**: Ensure all changes are validated by running `mypy` and resolving all static type errors.

### ② Branch Management and PR Lifecycle
To maintain clean git history and isolate changes:
*   **One Branch Per Task/Feature**: Create a new, dedicated branch for each specific task or feature. Avoid making unrelated changes in an active branch.
*   **PR Integration**: Always create a Pull Request (PR) on GitHub. Once merged, clean up and delete the local and remote branches.

---

## 3. Testing & Linting Conventions and Execution

To guarantee code quality, the project uses `pytest` for testing inside the [tests/](file:///Users/amano/works/research/flatexpy/tests/) directory and `pre-commit` for style/standards checks.

### ① Execution Before Commit 【Strictly Required】
Always run and pass the full test suite and pre-commit checks locally before executing a `git commit`:

1.  **Run Pytest**:
    ```bash
    # Install package with development dependencies
    pip install -e ".[dev]"

    # Run the test suite
    pytest
    ```
2.  **Run Pre-commit**:
    ```bash
    # Install the pre-commit Git hooks (one-time setup)
    pre-commit install

    # Run check pipeline manually on all files
    pre-commit run --all-files
    ```

### ② Formatting & Linting Pipeline
*   **isort & black**: Standardize imports sorting and code style.
*   **mypy**: Verify type safety rules.
*   **flake8 & pylint**: Check complexity, code smell, and conventions. Pylint rules are tuned to ignore warnings on complex CLI parsing where code remains readable.

---

## 4. Future Roadmap and Milestones
*   Feature for removing commented lines (`--ignore-comments` refinements).
*   Support for `standalone` and `import` packages.
*   Support for `bibtex` flattening and compilation helpers.
