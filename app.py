from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import anthropic
import openai
import requests
import streamlit as st

from backend import has_api_key, stream_tier_response, validate_startup
from constants import PRESET_PROMPTS, TIER3_MODEL_LABELS, TIERS, Tier3Model
from prompts import TIER_2_SYSTEM_PROMPT, TIER_3_SYSTEM_PROMPT
from state import clear_responses, init_state

_PROJECT_DIR = Path(__file__).parent

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Under the Hood: AI & Mental Health",
    page_icon="🧠",
    layout="centered",
)

# ── Load custom CSS ──────────────────────────────────────────────────────────

_css_path = _PROJECT_DIR / "styles" / "custom.css"
st.markdown(f"<style>{_css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────────────

init_state()

# ── Startup validation ───────────────────────────────────────────────────────

startup = validate_startup()

# ── UI helpers ───────────────────────────────────────────────────────────────


def _stream_to_placeholder(token_stream: Generator[str, None, None]) -> str:
    """Consume a token generator, rendering to an st.empty() placeholder.

    Returns the fully accumulated response text.
    """
    placeholder = st.empty()
    accumulated = ""

    for token in token_stream:
        accumulated += token
        placeholder.markdown(
            f'<div class="response-area">\n\n{accumulated}▌\n\n</div>',
            unsafe_allow_html=True,
        )

    placeholder.markdown(
        f'<div class="response-area">\n\n{accumulated}\n\n</div>',
        unsafe_allow_html=True,
    )
    return accumulated


def _render_tier_header(tier_num: int) -> None:
    """Render the styled header card for a tier."""
    tier = TIERS[tier_num]
    accent_class = f"tier-header-t{tier_num}"
    badge_class = f"guardrail-badge-t{tier_num}"

    model_html = ""
    if tier.model_name:
        model_html = f'<span class="model-badge">{tier.model_name}</span>'
    elif tier_num == 3:
        selected: Tier3Model = st.session_state.tier3_selected_model
        model_html = (
            f'<span class="model-badge">{TIER3_MODEL_LABELS[selected]}</span>'
        )

    badge_html = f'<div class="guardrail-badge {badge_class}">{tier.badge}</div>'
    parts = [
        f'<div class="tier-header {accent_class}">',
        f'<div class="tier-title">Tier {tier_num}: {tier.label}</div>',
    ]
    if model_html:
        parts.append(model_html)
    parts.append(badge_html)
    parts.append("</div>")

    st.markdown("\n".join(parts), unsafe_allow_html=True)


def _render_behind_the_scenes(tier_num: int) -> None:
    """Render the 'Behind the Scenes' expander for a tier."""
    tier = TIERS[tier_num]

    with st.expander("🔍 Behind the Scenes"):
        if tier_num == 1:
            st.markdown(f"**Model:** {tier.model_name}")
            st.markdown("**System Prompt:**")
            st.markdown("_No system prompt_")
        elif tier_num == 2:
            st.markdown(f"**Model:** {tier.model_name}")
            st.markdown("**System Prompt:**")
            st.text_area(
                "Tier 2 system prompt",
                key="tier2_system_prompt",
                height=200,
                label_visibility="collapsed",
            )
            st.button(
                "Reset to default",
                key="reset_t2_prompt",
                on_click=lambda: st.session_state.__setitem__(
                    "tier2_system_prompt", TIER_2_SYSTEM_PROMPT,
                ),
            )
        elif tier_num == 3:
            selected: Tier3Model = st.session_state.tier3_selected_model
            st.markdown(f"**Model:** {TIER3_MODEL_LABELS[selected]}")
            st.markdown("**System Prompt:**")
            st.text_area(
                "Tier 3 system prompt",
                key="tier3_system_prompt",
                height=300,
                label_visibility="collapsed",
            )
            st.button(
                "Reset to default",
                key="reset_t3_prompt",
                on_click=lambda: st.session_state.__setitem__(
                    "tier3_system_prompt", TIER_3_SYSTEM_PROMPT,
                ),
            )
            st.markdown("**User Context (simulated memory about Alex):**")
            st.markdown(
                "- Has mentioned feeling stressed about work\n"
                "- Recently went through a breakup (3 months ago)\n"
                "- Lives alone, moved to a new city 6 months ago\n"
                "- Feeling isolated, trouble making new friends\n"
                "- No known history of mental health treatment"
            )
        elif tier_num == 4:
            st.markdown("**Model:** Purpose-built clinical AI (e.g., Wysa, Woebot)")
            st.markdown(
                "These apps use proprietary models fine-tuned on clinical data "
                "with extensive safety validation."
            )

        st.markdown(f"**What this tier demonstrates:** {tier.explanation}")


def _render_cached_response(text: str) -> None:
    """Display a previously-cached response."""
    st.markdown(
        f'<div class="response-area">\n\n{text}\n\n</div>',
        unsafe_allow_html=True,
    )


def _render_placeholder() -> None:
    """Display the empty-state placeholder."""
    st.markdown(
        '<div class="response-area"><span class="response-placeholder">'
        "Response will appear here...</span></div>",
        unsafe_allow_html=True,
    )


# ── Layout ───────────────────────────────────────────────────────────────────

st.markdown("# Under the Hood: How AI Responds to Mental Health")
st.markdown(
    '<p class="subtitle"><em>Same prompt. Different engineering. '
    "Different outcomes.</em></p>",
    unsafe_allow_html=True,
)

# ── Prompt input ─────────────────────────────────────────────────────────────

prompt_input = st.text_input(
    "Enter a prompt",
    value=st.session_state.prompt,
    placeholder="Type a message someone might share about their mental health...",
    label_visibility="collapsed",
)

if prompt_input != st.session_state.prompt:
    st.session_state.prompt = prompt_input
    if prompt_input != st.session_state.active_prompt:
        clear_responses()

# ── Preset prompt buttons ────────────────────────────────────────────────────

preset_cols = st.columns(len(PRESET_PROMPTS))
for col, (label, text) in zip(preset_cols, PRESET_PROMPTS.items()):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state.prompt = text
            st.session_state.active_prompt = text
            clear_responses()
            st.rerun()

st.markdown("---")

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["Tier 1", "Tier 2", "Tier 3", "Tier 4"])

# ── Tier 1 ───────────────────────────────────────────────────────────────────

with tab1:
    _render_tier_header(1)

    if not startup.ollama_ready:
        st.warning(startup.ollama_error)

    has_prompt = bool(st.session_state.prompt.strip())
    has_cached = st.session_state.tier1_response is not None
    btn_label = "Re-send to Tier 1" if has_cached else "Send to Tier 1"

    st.markdown('<div class="send-btn send-btn-t1">', unsafe_allow_html=True)
    send_t1 = st.button(
        btn_label,
        key="send_t1",
        disabled=not has_prompt or not startup.ollama_ready,
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if send_t1:
        st.session_state.active_prompt = st.session_state.prompt
        try:
            st.session_state.tier1_response = _stream_to_placeholder(
                stream_tier_response(1, st.session_state.active_prompt),
            )
        except requests.RequestException as exc:
            st.error(f"❌ Error: {exc}. Check that Ollama is running.")
    elif has_cached:
        _render_cached_response(st.session_state.tier1_response)
    else:
        _render_placeholder()

    _render_behind_the_scenes(1)


# ── Tier 2 ───────────────────────────────────────────────────────────────────

with tab2:
    _render_tier_header(2)

    if not startup.ollama_ready:
        st.warning(startup.ollama_error)

    has_prompt = bool(st.session_state.prompt.strip())
    has_cached = st.session_state.tier2_response is not None
    btn_label = "Re-send to Tier 2" if has_cached else "Send to Tier 2"

    st.markdown('<div class="send-btn send-btn-t2">', unsafe_allow_html=True)
    send_t2 = st.button(
        btn_label,
        key="send_t2",
        disabled=not has_prompt or not startup.ollama_ready,
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if send_t2:
        st.session_state.active_prompt = st.session_state.prompt
        try:
            st.session_state.tier2_response = _stream_to_placeholder(
                stream_tier_response(
                    2,
                    st.session_state.active_prompt,
                    system_prompt=st.session_state.tier2_system_prompt,
                ),
            )
        except requests.RequestException as exc:
            st.error(f"❌ Error: {exc}. Check that Ollama is running.")
    elif has_cached:
        _render_cached_response(st.session_state.tier2_response)
    else:
        _render_placeholder()

    _render_behind_the_scenes(2)


# ── Tier 3 ───────────────────────────────────────────────────────────────────

_MODEL_RADIO_MAP: dict[str, Tier3Model] = {
    "Claude Sonnet 4.5": "claude",
    "GPT-5.2": "gpt",
}

with tab3:
    _render_tier_header(3)

    if not startup.has_anthropic_key and not startup.has_openai_key:
        st.warning(
            "⚠️ API keys not found. Set ANTHROPIC_API_KEY and/or OPENAI_API_KEY"
            " in your .env file."
        )

    # Model toggle — only show options with available keys
    model_options = [
        label for label, key in _MODEL_RADIO_MAP.items()
        if has_api_key(key) or (not startup.has_anthropic_key and not startup.has_openai_key)
    ]

    default_idx = 0
    if st.session_state.tier3_selected_model == "gpt" and "GPT-5.2" in model_options:
        default_idx = model_options.index("GPT-5.2")

    selected_model_label = st.radio(
        "Select model",
        model_options,
        index=default_idx,
        horizontal=True,
        label_visibility="collapsed",
    )

    new_selection = _MODEL_RADIO_MAP[selected_model_label]
    if new_selection != st.session_state.tier3_selected_model:
        st.session_state.tier3_selected_model = new_selection

    # Determine which cached response to show
    if new_selection == "claude":
        has_cached = st.session_state.tier3_claude_response is not None
        cached_response = st.session_state.tier3_claude_response
        key_available = startup.has_anthropic_key
        missing_key_msg = "⚠️ ANTHROPIC_API_KEY not found. Set it in your .env file."
    else:
        has_cached = st.session_state.tier3_gpt_response is not None
        cached_response = st.session_state.tier3_gpt_response
        key_available = startup.has_openai_key
        missing_key_msg = "⚠️ OPENAI_API_KEY not found. Set it in your .env file."

    if not key_available:
        st.warning(missing_key_msg)

    has_prompt = bool(st.session_state.prompt.strip())
    btn_label = "Re-send to Tier 3" if has_cached else "Send to Tier 3"

    st.markdown('<div class="send-btn send-btn-t3">', unsafe_allow_html=True)
    send_t3 = st.button(
        btn_label,
        key="send_t3",
        disabled=not has_prompt or not key_available,
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if send_t3:
        st.session_state.active_prompt = st.session_state.prompt
        try:
            response = _stream_to_placeholder(
                stream_tier_response(
                    3,
                    st.session_state.active_prompt,
                    new_selection,
                    system_prompt=st.session_state.tier3_system_prompt,
                ),
            )
            if new_selection == "claude":
                st.session_state.tier3_claude_response = response
            else:
                st.session_state.tier3_gpt_response = response
        except (anthropic.APIError, openai.APIError) as exc:
            st.error(
                f"❌ Error: {exc}. Check your API key and internet connection."
            )
    elif has_cached:
        _render_cached_response(cached_response)
    else:
        _render_placeholder()

    _render_behind_the_scenes(3)


# ── Tier 4 ───────────────────────────────────────────────────────────────────

with tab4:
    _render_tier_header(4)

    st.markdown(
        """<div class="info-card">
        <p>For the final tier, we switch to a <strong>purpose-built mental health
        application</strong> (e.g., Wysa) to see how domain-specific clinical
        engineering shapes the response. The presenter will demo this live on a
        separate screen.</p>
        <p><strong>What Tier 4 adds beyond general AI:</strong></p>
        <ul>
            <li>Evidence-based therapeutic frameworks (CBT, DBT)</li>
            <li>Clinical input in conversation design</li>
            <li>Structured safety escalation protocols</li>
            <li>Peer-reviewed validation</li>
            <li>Purpose-built UX for sensitive conversations</li>
        </ul>
        </div>""",
        unsafe_allow_html=True,
    )

    _render_behind_the_scenes(4)
