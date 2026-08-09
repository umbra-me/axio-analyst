"""Axio Analyst - provider-neutral AI analysis for Binary Ninja.

The guard keeps provider and prompt modules importable under stock Python for
tests. Binary Ninja is present when it loads the plugin and registration then
happens normally.
"""

from .core.version import VERSION as __version__

try:
    import binaryninja  # noqa: F401
except ModuleNotFoundError as exc:
    if exc.name != "binaryninja":
        raise
else:
    from .host.registration import register_plugin

    register_plugin()
