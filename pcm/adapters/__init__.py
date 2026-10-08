"""Adapter registry. Every module in this folder (and in <data>/adapters/) that defines an `Adapter` subclass is found."""
import importlib
import importlib.util
import os
import pkgutil

from .base import Adapter, AdapterError, Unsupported   # noqa: F401


def _subclasses(mod):
    return [c for c in vars(mod).values() if isinstance(c, type) and issubclass(c, Adapter) and c is not Adapter
            and c.__module__ == mod.__name__]


def discover(extra_dir=None):
    found = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name == "base":
            continue
        for cls in _subclasses(importlib.import_module("%s.%s" % (__name__, info.name))):
            found[cls.id] = cls
    if extra_dir and os.path.isdir(extra_dir):             # drop-in adapters written by the user
        for fn in sorted(os.listdir(extra_dir)):
            if fn.endswith(".py") and not fn.startswith("_"):
                spec = importlib.util.spec_from_file_location("pcm_user_" + fn[:-3], os.path.join(extra_dir, fn))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for cls in _subclasses(mod):
                    found[cls.id] = cls
    return found
