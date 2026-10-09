from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULES_DIR = REPO_ROOT / "modules"
CONFIG_DIR = REPO_ROOT / "config"
# Built web client (apps/web). Override for packaged deployments.
# The child's phone app, served only by the phone gateway (ADR-0012).
KID_APP = REPO_ROOT / "apps" / "kid-app"
