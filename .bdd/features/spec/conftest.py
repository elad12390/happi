from __future__ import annotations

import sys
from pathlib import Path

bdd_root = Path(__file__).parent.parent.parent
if str(bdd_root) not in sys.path:
    sys.path.insert(0, str(bdd_root))

from steps.spec_steps import *  # noqa: E402, F403
