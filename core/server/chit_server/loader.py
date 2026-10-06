from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_file_module(path: "str | Path") -> ModuleType:
    """Load a python file by path.

    Submodule folders use hyphens (home-assistant, time-intelligence) and are not importable
    packages; the registry and tests load their server code by file path instead. Sibling files in
    the same `server/` folder are loaded the same way (`load_file_module(Path(__file__).with_name("x.py"))`)
    so that two submodules can both have a `reader.py` without colliding on sys.modules.
    """
    path = Path(path).resolve()
    name = "chit_mod_" + hashlib.sha1(str(path).encode()).hexdigest()[:10] + "_" + path.stem
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module
