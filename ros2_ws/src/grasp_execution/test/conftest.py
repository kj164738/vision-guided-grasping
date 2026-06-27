from __future__ import annotations

import sys
from pathlib import Path


WORKSPACE_SRC = Path(__file__).resolve().parents[2]
SIM_CONTROL_PATH = WORKSPACE_SRC / "sim_control"

if str(SIM_CONTROL_PATH) not in sys.path:
    sys.path.insert(0, str(SIM_CONTROL_PATH))
