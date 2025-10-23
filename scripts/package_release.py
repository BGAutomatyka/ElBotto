"""Tworzy pojedynczy plik ZIP gotowy do instalacji przez pip."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
FILES: Iterable[Path] = (
    ROOT / "pyproject.toml",
    ROOT / "README.md",
    ROOT / "src",
    ROOT / "data",
)


def _add_path(zip_file: zipfile.ZipFile, path: Path) -> None:
    if path.is_dir():
        for child in sorted(path.iterdir()):
            _add_path(zip_file, child)
    else:
        arcname = path.relative_to(ROOT)
        zip_file.write(path, arcname)


def create_install_bundle(filename: str = "elbotto_install_bundle.zip") -> Path:
    """Zwraca ścieżkę do archiwum z projektem."""

    DIST.mkdir(exist_ok=True)
    archive_path = DIST / filename
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in FILES:
            if path.exists():
                _add_path(bundle, path)
    return archive_path


if __name__ == "__main__":
    created = create_install_bundle()
    print(f"Utworzono archiwum: {created}")
