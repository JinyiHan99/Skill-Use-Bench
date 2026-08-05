"""
requests.sessions
~~~~~~~~~~~~~~~~~

This module provides a Session object to manage and persist settings across
requests (cookies, auth, proxies).
"""

from __future__ import annotations

import os
import sys
import time
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

from .hooks import default_hooks, dispatch_hook

if sys.platform == "win32":
    preferred_clock = time.perf_counter
else:
    preferred_clock = time.time


def merge_setting(
    request_setting: Any, session_setting: Any, dict_class: type = OrderedDict
) -> Any:
    """Determines appropriate setting for a given request."""

    if session_setting is None:
        return request_setting

    if request_setting is None:
        return session_setting

    if not (
        isinstance(session_setting, Mapping) and isinstance(request_setting, Mapping)
    ):
        return request_setting

    merged_setting = dict_class(session_setting)
    merged_setting.update(request_setting)

    none_keys = [k for (k, v) in merged_setting.items() if v is None]
    for key in none_keys:
        del merged_setting[key]

    return merged_setting
