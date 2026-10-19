"""Build one release of the EV-SIENT public data hub.

    venv/bin/python -I platform/hub/build_hub.py --hub-version 2026-10-18.1

Run with -I: the inputs it downloads are untrusted, and -I keeps the current directory and any
PYTHON* settings off the import path. This file puts only its own folder there, for hubbuild.
See platform/hub/README.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hubbuild.build import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
