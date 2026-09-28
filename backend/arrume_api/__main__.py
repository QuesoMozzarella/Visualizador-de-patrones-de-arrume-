"""Arranca la API (y el frontend, si esta compilado) en este equipo.

    python -m arrume_api              escucha en 127.0.0.1:5000
    python -m arrume_api --abrir      y abre el navegador

Es el servidor de desarrollo de Flask: pensado para usarlo en local, no
para exponerlo a internet.
"""

from __future__ import annotations

import argparse
import threading
import webbrowser
from collections.abc import Sequence

from .app import create_app


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arrume_api")
    parser.add_argument("--puerto", type=int, default=5000)
    parser.add_argument("--abrir", action="store_true", help="abrir el navegador")
    args = parser.parse_args(argv)

    app = create_app()
    if args.abrir:
        direccion = f"http://127.0.0.1:{args.puerto}/"
        threading.Timer(1.0, webbrowser.open, args=(direccion,)).start()
    app.run(host="127.0.0.1", port=args.puerto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
