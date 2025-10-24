"""Wejście programu w trybie modułu (`python -m elbotto`)."""

from __future__ import annotations

from elbotto.cli import run_cli


def main() -> None:
    run_cli()


if __name__ == "__main__":  # pragma: no cover - uruchamiane ręcznie
    main()
