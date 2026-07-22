#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


def default_install_root() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "research-reading-contract"


def venv_python(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install RRC into an isolated environment and connect it to an agent."
    )
    parser.add_argument(
        "--agent",
        choices=["codex", "claude", "both"],
        required=True,
        help="Agent integration to configure.",
    )
    parser.add_argument(
        "--scope", choices=["user", "project"], default="user"
    )
    parser.add_argument("--project", help="Project root for project scope.")
    parser.add_argument(
        "--install-root",
        type=Path,
        default=default_install_root(),
        help="Isolated installation directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an unrecognized skill directory at the destination.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if sys.version_info < (3, 10):
        print("RRC requires Python 3.10 or newer.", file=sys.stderr)
        return 2

    repository = Path(__file__).resolve().parents[1]
    environment = args.install_root.expanduser().resolve() / "venv"
    python = venv_python(environment)
    if not python.exists():
        print(f"Creating isolated environment at {environment}")
        environment.parent.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True).create(environment)

    run([str(python), "-m", "pip", "install", "--upgrade", str(repository)])

    common = ["--agent", args.agent, "--scope", args.scope]
    if args.project:
        common.extend(["--project", str(Path(args.project).expanduser().resolve())])
    setup_command = [
        str(python),
        "-m",
        "research_reading_contract",
        "setup",
        *common,
    ]
    if args.force:
        setup_command.append("--force")
    run(setup_command)
    run(
        [
            str(python),
            "-m",
            "research_reading_contract",
            "doctor",
            *common,
        ]
    )

    print("\nRRC is ready inside the selected agent workflow.")
    print("Restart the agent only if the new skill does not appear immediately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
