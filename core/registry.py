from typing import List
from importlib import import_module

# Python 3.11 has tomllib; fall back to toml if needed
try:
    import tomllib  # type: ignore
except Exception:  # pragma: no cover
    import toml as tomllib  # type: ignore

from core.types import HealthModule


def load_enabled_modules() -> List[HealthModule]:
    with open("config.toml", "rb") as f:
        cfg = tomllib.load(f)
    mods = []
    mod_cfg = cfg.get("modules", {})
    ordered = sorted(((m, v.get("order", 999)) for m, v in mod_cfg.items() if v.get("enabled", True)), key=lambda x: x[1])
    for name, _ in ordered:
        mod = import_module(f"modules.{name}.{name}")
        mods.append(mod)
    return mods
