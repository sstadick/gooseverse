#!/usr/bin/env python3
"""Execute the README's complete programs against current package branches."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", nargs="+", default=["gcc", "clang"],
                        help="Native compilers to test (default: gcc clang); TinyCC always runs.")
    args = parser.parse_args()
    readme = Path(__file__).resolve().parents[1] / "README.md"
    examples = re.findall(r"^```goose\n(.*?)^```$", readme.read_text(), re.M | re.S)
    if not examples:
        raise SystemExit("README.md contains no Goose examples")
    goose = os.environ.get("GOOSE", "goose")
    subprocess.run([goose, "--version"], check=True)
    with tempfile.TemporaryDirectory(prefix="gooseverse-") as directory:
        root = Path(directory)
        env = dict(os.environ, GOOSE_HOME=str(root / "packages"))
        for index, code in enumerate(examples, 1):
            work = root / str(index)
            work.mkdir()
            source = work / "main.goose"
            source.write_text(code)
            print(f"Example {index}: TinyCC, {', '.join(args.cc)}", flush=True)
            subprocess.run([goose, "run", str(source), "--debug"],
                           cwd=work, env=env, check=True, timeout=180)
            for cc in args.cc:
                executable = work / f"example-{cc}"
                subprocess.run([goose, "build", str(source), "--debug", "-O2",
                                "--cc", cc, "-o", str(executable)],
                               cwd=work, env=env, check=True, timeout=180)
                subprocess.run([str(executable)], cwd=work, env=env,
                               check=True, timeout=30)
    print(f"Passed {len(examples)} examples on TinyCC and {', '.join(args.cc)}.")


if __name__ == "__main__":
    main()
