import signal
import sys
import logging
import sys


from src.application import SlideScannerApplication


def main():
    app = SlideScannerApplication()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    return app.run(sys.argv)


if __name__ == "__main__":
    logging.getLogger("PIL").setLevel(logging.WARN)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARN)

    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(message)s",
        stream=sys.stdout,
    )

    sys.exit(main())
