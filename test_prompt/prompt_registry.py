"""Shared prompt registry for task 9/10 extraction harnesses."""

from prompt_v2 import PROMPT_TEMPLATE_V2
from prompt_v3 import PROMPT_TEMPLATE_V3
from prompt_v4 import PROMPT_TEMPLATE_V4


PROMPT_REGISTRY = {
    "v2": PROMPT_TEMPLATE_V2,
    "v3": PROMPT_TEMPLATE_V3,
    "v4": PROMPT_TEMPLATE_V4,
}

DEFAULT_PROMPT_VERSION = "v4"

