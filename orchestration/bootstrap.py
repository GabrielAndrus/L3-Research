"""
Bootstrap for in-place integration under the repo root.

Loads the vendored CulFiT files the F1 evaluation needs (`CulFiT/utils/
prompt_utils.py` and `llm_utils.py`) by explicit filesystem path under unique
module names, then aliases them as `utils.prompt_utils` / `utils.llm_utils` so
the upstream CulFiT code runs UNMODIFIED. A bare `utils` is never put on
sys.path, so there is no risk of resolving to a different `utils` package.

Fiona's Agent A loader (Cultural_Commonsense_Knowledge_Graph) was removed when
the multi-agent harness was archived under archive/fiona-agents/.

Nothing in the original CulFiT repo is edited or copied.
"""

from __future__ import annotations
import importlib.util
import os
import sys
import types

# ---- Resolve repo roots relative to this file --------------------------------
# This file lives at CSC494/orchestration/bootstrap.py
_THIS = os.path.dirname(os.path.abspath(__file__))
CSC494 = os.path.dirname(_THIS)
CULFIT = os.path.join(CSC494, "CulFiT")


def _load(module_name: str, file_path: str):
    """Load a single .py file as `module_name`, registering it in sys.modules."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_pkg(name: str):
    """Create an empty namespace package entry so `pkg.sub` aliasing works."""
    if name not in sys.modules:
        pkg = types.ModuleType(name)
        pkg.__path__ = []  # mark as package
        sys.modules[name] = pkg
    return sys.modules[name]


def install():
    """
    Make the vendored CulFiT modules importable. Call once before importing
    anything that needs the CulFiT prompts. Returns a dict of the loaded modules.
    """
    # --- CulFiT -------------------------------------------------------------
    # CulFiT code does `from utils.prompt_utils import ...` and
    # `from utils.llm_utils import ...`. We satisfy that by registering a
    # `utils` package whose submodules point at CulFiT's files specifically.
    culfit_prompt_utils = _load("culfit_prompt_utils",
                                os.path.join(CULFIT, "utils", "prompt_utils.py"))

    # NOTE: llm_utils imports tenacity/openai (only needed for api/local modes).
    # Load it lazily so mock mode runs with zero extra deps.
    culfit_llm_utils = None
    try:
        culfit_llm_utils = _load("culfit_llm_utils",
                                 os.path.join(CULFIT, "utils", "llm_utils.py"))
    except ImportError as e:
        import logging
        logging.getLogger(__name__).info(
            "culfit_llm_utils not loaded (%s); fine for mock mode.", e)

    # Alias them under the `utils.*` names the upstream file expects.
    _ensure_pkg("utils")
    sys.modules["utils.prompt_utils"] = culfit_prompt_utils
    if culfit_llm_utils is not None:
        sys.modules["utils.llm_utils"] = culfit_llm_utils

    return {
        "culfit_prompt_utils": culfit_prompt_utils,
        "culfit_llm_utils": culfit_llm_utils,
    }
