import signal
import sys

import gi

gi.require_version("Gtk", "4.0")

from src.application import SlideScannerApplication


def main():
    app = SlideScannerApplication()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
