#!/usr/bin/env python3
"""
Code formatting script for the AI Trading Bot project.

This script provides convenient commands for formatting code using Black and isort.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def format_code():
    """Format all Python code using Black and isort."""
    print("🎨 Starting code formatting...")

    # Get project root
    project_root = Path(__file__).parent.parent

    # Format with Black
    black_cmd = [
        sys.executable,
        "-m",
        "black",
        str(project_root / "src"),
        str(project_root / "tests"),
        str(project_root / "run.py"),
        "--line-length=88",
        "--target-version=py38",
    ]

    if not run_command(black_cmd, "Black formatting"):
        return False

    # Sort imports with isort
    isort_cmd = [
        sys.executable,
        "-m",
        "isort",
        str(project_root / "src"),
        str(project_root / "tests"),
        str(project_root / "run.py"),
        "--profile=black",
        "--line-length=88",
    ]

    if not run_command(isort_cmd, "Import sorting"):
        return False

    print("🎉 Code formatting completed successfully!")
    return True


def check_formatting():
    """Check if code is properly formatted without making changes."""
    print("🔍 Checking code formatting...")

    project_root = Path(__file__).parent.parent

    # Check with Black
    black_cmd = [
        sys.executable,
        "-m",
        "black",
        str(project_root / "src"),
        str(project_root / "tests"),
        str(project_root / "run.py"),
        "--line-length=88",
        "--target-version=py38",
        "--check",
    ]

    if not run_command(black_cmd, "Black formatting check"):
        return False

    # Check with isort
    isort_cmd = [
        sys.executable,
        "-m",
        "isort",
        str(project_root / "src"),
        str(project_root / "tests"),
        str(project_root / "run.py"),
        "--profile=black",
        "--line-length=88",
        "--check-only",
    ]

    if not run_command(isort_cmd, "Import sorting check"):
        return False

    print("✅ All code is properly formatted!")
    return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python format_code.py [format|check]")
        print("  format - Format all code with Black and isort")
        print("  check  - Check if code is properly formatted")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "format":
        success = format_code()
    elif command == "check":
        success = check_formatting()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: format, check")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
