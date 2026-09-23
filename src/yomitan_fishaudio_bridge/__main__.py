import argparse
import sys

from .gui import run_gui
from .server import run_headless


def main(argv=None):
    p = argparse.ArgumentParser(prog="yomitan-fishaudio-bridge")
    p.add_argument("--background", action="store_true", help="Start without showing the window")
    p.add_argument("--headless", action="store_true", help="Run server without GUI")
    p.add_argument("--port", type=int, default=None)
    args = p.parse_args(argv)

    if args.headless:
        run_headless(port=args.port)
    else:
        run_gui(background=args.background)


if __name__ == "__main__":
    sys.exit(main())
