# django_auto_api/config.py
from django.conf import settings


DEFAULT_CONFIG = {
    # If None → include all non-contrib apps.
    # If list → only include these app labels (e.g. ["blog", "orders"])
    "INCLUDE_APPS": None,

    # Extra apps to skip (app labels), even if INCLUDE_APPS is None
    "EXCLUDE_APPS": [],

    # Later you can add stuff like:
    # "OPENAI_MODEL": "gpt-4o-mini",
}


def get_config():
    user_cfg = getattr(settings, "DJANGO_AUTO_API", {}) or {}
    cfg = DEFAULT_CONFIG.copy()
    cfg.update(user_cfg)
    return cfg
