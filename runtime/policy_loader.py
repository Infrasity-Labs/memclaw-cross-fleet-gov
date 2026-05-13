import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


class PolicyLoader:
    @staticmethod
    def load(path: str) -> dict:
        resolved = os.path.normpath(os.path.join(_REPO_ROOT, path))
        if not os.path.exists(resolved):
            raise FileNotFoundError(
                f"Policy file not found: {resolved!r}. "
                f"Original path argument: {path!r}"
            )
        with open(resolved, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
