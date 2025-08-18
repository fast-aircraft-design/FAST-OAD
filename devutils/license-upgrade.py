import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")  # Check or fix flag
    parser.add_argument("files", nargs="*")  # Files to check

    args = parser.parse_args()

    cmd = [
        "insert_license",
        "--license-filepath",
        "license-header.txt",
        "--use-current-year",
    ] + args.files

    if args.check:
        # In check mode, capture output and fail if changes needed
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or result.stdout.strip():
            print(
                "Some files have incorrect license header.\nRun locally 'pre-commit run license-headers-fix --all-files' to fix automatically"
            )
            return 1
        print("All license headers are up to date")
        return 0
    else:
        # In fix mode, run normally
        return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
