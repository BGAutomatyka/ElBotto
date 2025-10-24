from __future__ import annotations

from elbotto.packaging import create_install_bundle


if __name__ == "__main__":
    created = create_install_bundle()
    print(f"Utworzono archiwum: {created}")
