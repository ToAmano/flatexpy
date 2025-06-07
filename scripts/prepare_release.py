#!/usr/bin/env python3
"""Script to prepare a release for flatexpy."""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def update_version(version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")

    # Update version in pyproject.toml
    content = re.sub(r'version = "[^"]*"', f'version = "{version}"', content)

    pyproject_path.write_text(content, encoding="utf-8")
    print(f"Updated version to {version} in pyproject.toml")


def update_conda_meta(version: str) -> None:
    """Update version in conda meta.yaml."""
    meta_path = Path("conda/meta.yaml")
    if meta_path.exists():
        content = meta_path.read_text(encoding="utf-8")

        # Update version in conda meta.yaml
        content = re.sub(
            r'{% set version = "[^"]*" %}',
            f'{{% set version = "{version}" %}}',
            content,
        )

        meta_path.write_text(content, encoding="utf-8")
        print(f"Updated version to {version} in conda/meta.yaml")


def run_tests() -> None:
    """Run the test suite."""
    print("Running tests...")
    result = run_command(["python", "-m", "pytest", "tests/", "-v"])
    if result.returncode != 0:
        print("Tests failed!")
        sys.exit(1)
    print("Tests passed!")


def run_linting() -> None:
    """Run linting checks."""
    print("Running linting checks...")

    # Run black check
    result = run_command(["black", "--check", "flatexpy", "tests"], check=False)
    if result.returncode != 0:
        print("Code formatting issues found. Run 'black flatexpy tests' to fix.")
        sys.exit(1)

    # Run isort check
    result = run_command(["isort", "--check-only", "flatexpy", "tests"], check=False)
    if result.returncode != 0:
        print("Import sorting issues found. Run 'isort flatexpy tests' to fix.")
        sys.exit(1)

    # Run flake8
    result = run_command(["flake8", "flatexpy", "tests"], check=False)
    if result.returncode != 0:
        print("Linting issues found. Please fix them before releasing.")
        sys.exit(1)

    print("Linting checks passed!")


def build_package() -> None:
    """Build the package."""
    print("Building package...")

    # Clean previous builds
    for path in ["build", "dist", "flatexpy.egg-info"]:
        if Path(path).exists():
            shutil.rmtree(path)

    # Build package
    run_command(["python", "-m", "build"])

    # Check package
    run_command(["twine", "check", "dist/*"])

    print("Package built successfully!")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Prepare a release for flatexpy")
    parser.add_argument("version", help="Version to release (e.g., 1.0.1)")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-lint", action="store_true", help="Skip linting checks")

    args = parser.parse_args()

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print("Version must be in format X.Y.Z (e.g., 1.0.1)")
        sys.exit(1)

    print(f"Preparing release {args.version}...")

    # Update versions
    update_version(args.version)
    update_conda_meta(args.version)

    # Run checks
    if not args.skip_lint:
        run_linting()

    if not args.skip_tests:
        run_tests()

    # Build package
    build_package()

    print(f"\nRelease {args.version} prepared successfully!")
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Commit the version updates")
    print("3. Create a git tag: git tag v{args.version}")
    print("4. Push the tag: git push origin v{args.version}")
    print("5. Create a GitHub release")
    print("6. Upload to PyPI: twine upload dist/*")


if __name__ == "__main__":
    main()
