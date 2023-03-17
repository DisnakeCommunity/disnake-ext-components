"""A simple CLI command to run example files with a bot token from env."""

import argparse
import importlib.util
import os
import subprocess
import sys
import typing

import dotenv

_KEY: typing.Final[str] = "EXAMPLE_TOKEN"


def _main() -> typing.NoReturn:
    # First, get the token from dotenv.
    dotenv.load_dotenv()

    token = os.getenv(_KEY)
    if not token:
        print("Token not found! Please set 'EXAMPLE_TOKEN' in .env.")
        sys.exit(1)

    # Get the passed example using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("example", type=str)

    result = parser.parse_args()
    example: str = f"examples.{result.example}"

    # Check if example module exists:
    if not importlib.util.find_spec(example):
        print(f"Cound not find example {example!r}.")
        sys.exit(1)

    args = ["env", f"{_KEY}={token}", "poetry", "run", "python", "-m", example]

    # Open a subprocess that runs our args list.
    print(f"Running example {example!r}...")
    try:
        process = subprocess.run(args, capture_output=True, cwd=os.getcwd())
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, stopping example.")
        sys.exit(0)

    if process.returncode != 0:
        print(process.stdout.decode(), process.stderr.decode(), sep="\n")
    else:
        print(process.stdout.decode())

    # And finally, propagate slotscheck's return code.
    sys.exit(process.returncode)


if __name__ == "__main__":
    _main()
