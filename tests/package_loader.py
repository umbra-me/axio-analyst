"""Load the repository root as the installed `axio_analyst` package."""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if "axio_analyst" not in sys.modules:
    package_spec = importlib.util.spec_from_file_location(
        "axio_analyst",
        REPO_ROOT / "__init__.py",
        submodule_search_locations=[str(REPO_ROOT)],
    )
    if package_spec is None or package_spec.loader is None:
        raise RuntimeError("Could not create the axio_analyst test package")
    package = importlib.util.module_from_spec(package_spec)
    sys.modules["axio_analyst"] = package
    package_spec.loader.exec_module(package)
