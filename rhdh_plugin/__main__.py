"""Entry point for python -m rhdh_plugin."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
