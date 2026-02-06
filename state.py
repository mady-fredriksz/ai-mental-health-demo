from __future__ import annotations

from dataclasses import dataclass, fields

import streamlit as st

from constants import Tier3Model
from prompts import TIER_2_SYSTEM_PROMPT, TIER_3_SYSTEM_PROMPT


@dataclass
class AppState:
    prompt: str = ""
    active_prompt: str = ""
    tier1_response: str | None = None
    tier2_response: str | None = None
    tier3_claude_response: str | None = None
    tier3_gpt_response: str | None = None
    tier3_selected_model: Tier3Model = "claude"
    tier2_system_prompt: str = TIER_2_SYSTEM_PROMPT
    tier3_system_prompt: str = TIER_3_SYSTEM_PROMPT


def init_state() -> None:
    """Populate missing session-state keys from AppState defaults."""
    defaults = AppState()
    for f in fields(AppState):
        if f.name not in st.session_state:
            st.session_state[f.name] = getattr(defaults, f.name)


def get_state() -> AppState:
    """Return a typed snapshot of the current session state."""
    return AppState(**{f.name: st.session_state[f.name] for f in fields(AppState)})


def clear_responses() -> None:
    """Reset all cached tier responses to None."""
    st.session_state.tier1_response = None
    st.session_state.tier2_response = None
    st.session_state.tier3_claude_response = None
    st.session_state.tier3_gpt_response = None
