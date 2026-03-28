import os
import streamlit.components.v1 as components

_PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR = os.path.join(_PARENT_DIR, "frontend", "build")

_component_func = components.declare_component(
    "premium_audio_recorder",
    path=_BUILD_DIR,
)

def st_premium_audio_recorder(key=None, default=None, **kwargs):
    return _component_func(
        key=key,
        default=default,
        **kwargs
    )