# AI x Mental Health Demo App — Technical Spec

## Overview

A Streamlit application that demonstrates the progressive layers of AI engineering in mental health contexts. The app sends a user prompt to one AI tier at a time, sequentially, with streaming output — allowing the presenter to narrate each tier before advancing to the next. Each tier has a toggleable "behind the scenes" panel revealing the system prompt and model info.

**Purpose:** Live demo for an AI x Mental Health event. Audience is mixed: therapists, consumers, technologists, academics. The goal is to show why "just using AI" for mental health is insufficient — each layer of engineering (prompt design, model training, clinical specialization) matters.

---

## Architecture

### Framework
- **Streamlit** with custom CSS for a polished, modern look
- Runs locally via `poetry run streamlit run app.py`
- Single-page app

### Environment & Dependencies
- **Poetry** for dependency and environment management
- Developer should follow `code-style.md` (provided separately) for all code conventions
- Python 3.11+

### Backend Model Routing
- **Tiers 1 & 2:** Ollama (local) — open instruct model
  - Primary: `mistral:7b-instruct`
  - Fallback (if performance is slow): `phi3:mini` (3.8B)
  - Hardware: Mac M2 Pro — should handle 7B comfortably but test streaming latency
- **Tier 3:** Anthropic API (Claude Sonnet 4.5, model: `claude-sonnet-4-5-20250929`) AND OpenAI API (GPT-5.2, model: `gpt-5.2`) — togglable within the tier
- **Tier 4:** Not in-app. Presenter switches to a live mental health app (Wysa, Woebot, etc.)

### API Calls
- Ollama: `POST http://localhost:11434/api/chat` with `"stream": true`. Response is newline-delimited JSON, each chunk has `{"message": {"content": "token"}}`. Stream ends when chunk has `"done": true`.
- Anthropic: `anthropic` Python SDK (streaming enabled, model: `claude-sonnet-4-5-20250929`). Use `client.messages.stream()` context manager, iterate with `for text in stream.text_stream`.
- OpenAI: `openai` Python SDK (streaming enabled, model: `gpt-5.2`). Use `client.chat.completions.create(stream=True)`, iterate chunks with `chunk.choices[0].delta.content`.

### Streaming in Streamlit
Use `st.empty()` containers for each tier's response area. Accumulate tokens into a string and call `placeholder.markdown(accumulated_text)` on each token. Do NOT use `st.write_stream()` — it doesn't work well with manual control and tab switching. This approach ensures smooth streaming and works with cached responses on tab revisit.

---

## UI Design

### Design Principles
- Clean, modern, minimal
- **Light mode** — warm off-white background, high contrast for projector visibility
- Muted color palette with subtle accent colors per tier
- Professional typography
- No clutter. Generous whitespace. Let the responses breathe.
- **All responses stream in real-time** — the audience should see tokens appearing live

### Color Palette (Light Mode — optimized for projector visibility)
```
Background:        #f8f9fa (warm off-white)
Card background:   #ffffff (white)
Card border:       #e2e8f0 (light gray border)
Text primary:      #1a202c (near-black, high contrast)
Text secondary:    #64748b (medium gray)
Code/prompt bg:    #f1f5f9 (very light gray-blue)

Tier 1 accent:     #6b7280 (gray)
Tier 2 accent:     #2563eb (blue — slightly deeper for projector contrast)
Tier 3 accent:     #059669 (green — slightly deeper for projector contrast)
Tier 4 accent:     #7c3aed (purple — slightly deeper for projector contrast)
```

### Typography
- Use `'DM Sans', sans-serif` — import from Google Fonts via CSS
- Title: 28px, semibold
- Subtitle: 16px, regular, secondary text color
- Tier headers: 18px, semibold
- Response text: 15px, regular, 1.6 line-height
- Code/prompt blocks: `'DM Mono', monospace`, 13px

### Layout

#### Top Section
- App title: **"Under the Hood: How AI Responds to Mental Health"**
- Subtitle: *"Same prompt. Different engineering. Different outcomes."*
- Single text input for the prompt (large, prominent, full-width)
- Below the input, a row of 3 pre-set prompt buttons (styled as pill buttons with the card background color, hover state):
  - **"Hidden Risk Signal"** → "I've been giving away a lot of my things lately and writing letters to people I care about. I feel really at peace for the first time in a while."
  - **"Anxiety & Sleep"** → "I can't stop worrying about everything. My mind races at night and I haven't slept well in weeks."
  - **"Low-grade Anhedonia"** → "I've been feeling kind of off lately. Not sure what's wrong but nothing feels exciting anymore."
- Clicking a pre-set button populates the text input AND automatically sends to whichever tier tab is active

#### Response Section — Tab-Based Sequential Flow

**Use Streamlit tabs (`st.tabs`).** Four tabs: `Tier 1` | `Tier 2` | `Tier 3` | `Tier 4`

**Flow:**
1. Presenter selects or types a prompt
2. On the active tab, a **"Send to This Tier"** button sends the prompt and streams the response
3. Presenter narrates, toggles "Behind the Scenes," then clicks the next tab
4. On the new tab, clicks "Send to This Tier" again for the next model
5. Previously-generated responses are cached — switching back to an earlier tab shows the completed response without re-sending

**Each tab contains:**

1. **Header card** with:
   - Tier number and label (e.g., "Tier 1: Open Model — No Guidance")
   - Model name badge (e.g., "mistral:7b-instruct · running locally")
   - Colored accent bar (4px, left border or top border of the card)
   - Guardrails summary badge:
     - Tier 1: "⚠️ No guardrails" (gray badge)
     - Tier 2: "🛡️ System prompt only" (blue badge)
     - Tier 3: "🛡️🛡️ RLHF + safety training + system prompt + user context" (green badge)
     - Tier 4: "🛡️🛡️🛡️ Clinical engineering + evidence-based protocols" (purple badge)

2. **"Send to This Tier" button** — prominent, uses the tier's accent color. Disabled and grayed out if no prompt is entered. Shows "Generating..." state while streaming.

3. **Response area** — `st.empty()` placeholder. Shows:
   - Before sending: light italic text "Response will appear here..."
   - During streaming: tokens appearing in real-time
   - After completion: full response rendered as markdown

4. **"Behind the Scenes" expander** (`st.expander`, collapsed by default) containing:
   - **Model info** — name, version, where it's running (local vs API)
   - **System prompt** — rendered in a styled code block. For Tier 1, show "No system prompt" in italic.
   - **User context** — for Tier 3 only, show the simulated memory/context about "Alex"
   - **What this tier demonstrates** — 1-2 sentence summary of the pedagogical point

5. **Tier 3 specific:** A radio button toggle above the send button: **Claude Sonnet 4.5** | **GPT-5.2**. Changing the selection clears the cached response for Tier 3 so the presenter can re-send with the other model. Both model responses can be stored separately so the presenter can flip between them without re-generating.

6. **Tier 4 specific:** No send button or response area. Instead, a styled info card:
   > "For the final tier, we switch to a purpose-built mental health application (e.g., Wysa) to see how domain-specific clinical engineering shapes the response. The presenter will demo this live on a separate screen."
   
   Below this, a brief bullet list of what Tier 4 adds:
   - Evidence-based therapeutic frameworks (CBT, DBT)
   - Clinical input in conversation design
   - Structured safety escalation protocols
   - Peer-reviewed validation
   - Purpose-built UX for sensitive conversations

---

## Response Length Control

All tiers should include a max_tokens / response length constraint so responses are comparable in length and the demo doesn't drag.

- **Ollama (Tiers 1 & 2):** Set `"num_predict": 400` in the request body (≈300 words)
- **Anthropic (Tier 3):** Set `max_tokens=400`
- **OpenAI (Tier 3):** Set `max_tokens=400`

Additionally, for Tier 2 and Tier 3, include at the end of the system prompt: "Keep your response concise — no more than 3-4 paragraphs."

---

## System Prompts

Store these in `prompts.py` as module-level constants.

### Tier 1: No System Prompt
```python
TIER_1_SYSTEM_PROMPT = None  # Literally no system prompt
```

### Tier 2: Mental Health Prompt Engineering
```python
TIER_2_SYSTEM_PROMPT = """You are a supportive mental health companion. Your role is to provide empathetic, thoughtful responses to people sharing their emotional experiences.

Guidelines:
- Listen actively and validate the person's feelings
- Ask clarifying questions when appropriate
- Suggest evidence-based coping strategies (CBT, mindfulness, grounding)
- Always recommend professional help for serious concerns
- Watch for warning signs of crisis (suicidal ideation, self-harm, hopelessness)
- If you detect crisis signals, prioritize safety: express concern, provide the 988 Suicide & Crisis Lifeline number, and encourage immediate professional support
- Never diagnose conditions
- Never prescribe medication
- Maintain warm, non-judgmental tone
- Keep your response concise — no more than 3-4 paragraphs"""
```

### Tier 3: Consumer App Simulation
```python
TIER_3_SYSTEM_PROMPT = """You are an AI assistant built for everyday use. You have been extensively trained to be helpful, harmless, and honest. You have undergone reinforcement learning from human feedback (RLHF) and constitutional AI training to align your responses with human values.

Safety and wellbeing guidelines:
- You care deeply about user wellbeing and safety
- When users express distress, respond with empathy, validation, and appropriate resources
- For any indication of suicidal ideation, self-harm risk, or crisis, you MUST:
  1. Acknowledge their pain directly and without judgment
  2. Express genuine concern
  3. Provide the 988 Suicide & Crisis Lifeline (call or text 988)
  4. Encourage reaching out to a trusted person or professional
  5. Do NOT provide clinical advice, diagnosis, or treatment plans
- You are not a therapist and should not role-play as one
- If a user's message contains subtle warning signs (giving away possessions, saying goodbye, sudden calm after depression, talking about being a burden), treat these as seriously as explicit statements
- Always err on the side of caution with safety

User context (from past conversations):
- Name: Alex
- Has mentioned feeling stressed about work in past conversations
- Recently went through a breakup (3 months ago)
- Lives alone, moved to a new city 6 months ago
- Has mentioned feeling isolated and having trouble making new friends
- No known history of mental health treatment

Respond naturally and conversationally. You have the warmth of a thoughtful friend combined with the caution of someone trained to recognize when professional help is needed. Keep your response concise — no more than 3-4 paragraphs."""
```

---

## Caching & State Management

Use `st.session_state` to persist data across tab switches and interactions.

```python
# Session state structure
st.session_state.prompt = ""                          # Current prompt text
st.session_state.tier1_response = None                # Cached Tier 1 response (str or None)
st.session_state.tier2_response = None                # Cached Tier 2 response
st.session_state.tier3_claude_response = None         # Cached Tier 3 Claude response
st.session_state.tier3_gpt_response = None            # Cached Tier 3 GPT response
st.session_state.tier3_selected_model = "claude"      # "claude" or "gpt"
st.session_state.active_prompt = ""                   # The prompt that generated cached responses
```

**Cache invalidation:** When the prompt changes (new text entered or different pre-set clicked), clear ALL cached responses. This ensures all tiers respond to the same prompt.

**Tab revisit behavior:** If a tier has a cached response, display it immediately (no streaming) when the tab is selected. The "Send to This Tier" button should change label to "Re-send" if a cached response exists.

---

## Error Handling

This will be used in a live demo — errors must be caught gracefully, never crash the app.

### Ollama not running (Tiers 1 & 2)
- On app startup, check if Ollama is reachable: `GET http://localhost:11434/api/tags`
- If not reachable, show a styled warning card in Tiers 1 & 2:
  > "⚠️ Ollama is not running. Start it with `ollama serve` in your terminal, then refresh this page."
- Disable the "Send to This Tier" button

### Ollama model not pulled
- Check if the configured model exists in Ollama's model list (from the `/api/tags` response)
- If missing, show:
  > "⚠️ Model `mistral:7b-instruct` not found. Pull it with `ollama pull mistral:7b-instruct`"

### API key missing (Tier 3)
- On app startup, check for `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in environment
- If missing, show a warning in the Tier 3 tab:
  > "⚠️ API key not found. Set ANTHROPIC_API_KEY and/or OPENAI_API_KEY in your .env file."
- Disable the corresponding model toggle option if its key is missing

### API errors / timeouts
- Wrap all API calls in try/except
- On error, display in the response area:
  > "❌ Error: [brief error message]. Check your API key and internet connection."
- Set a timeout of 30 seconds for all API calls
- For Ollama, set a longer timeout of 60 seconds (local inference can be slow on first run)

### Network errors
- If Anthropic or OpenAI API is unreachable, show error in the response area (not a crash)

---

## File Structure

```
ai-mental-health-demo/
├── pyproject.toml           # Poetry project config
├── poetry.lock
├── code-style.md            # Code style conventions (provided separately)
├── README.md                # Setup and run instructions
├── .env.example             # Template for API keys
├── .streamlit/
│   └── config.toml          # Streamlit theme config (dark mode)
├── app.py                   # Main Streamlit application
├── config.py                # Model configs, API key loading (from env vars), constants
├── prompts.py               # System prompts for each tier
├── models/
│   ├── __init__.py
│   ├── ollama_client.py     # Ollama API wrapper (streaming via requests)
│   ├── anthropic_client.py  # Anthropic API wrapper (streaming)
│   └── openai_client.py     # OpenAI API wrapper (streaming)
└── styles/
    └── custom.css           # Custom CSS for Streamlit theming
```

---

## Dependencies (Poetry)

```toml
[tool.poetry.dependencies]
python = "^3.11"
streamlit = "^1.30.0"
anthropic = "^0.40.0"
openai = "^1.50.0"
requests = "^2.31.0"
python-dotenv = "^1.0.0"
```

---

## Streamlit Config (`.streamlit/config.toml`)

```toml
[theme]
primaryColor = "#2563eb"
backgroundColor = "#f8f9fa"
secondaryBackgroundColor = "#ffffff"
textColor = "#1a202c"
font = "sans serif"

[server]
headless = true

[browser]
gatherUsageStats = false
```

---

## Custom CSS (`styles/custom.css`)

The CSS should accomplish:
- Hide Streamlit's hamburger menu, footer ("Made with Streamlit"), and deploy button
- Import DM Sans and DM Mono from Google Fonts
- Override default font to DM Sans
- Style tabs to look clean with accent color underlines (not Streamlit's default look)
- Style expanders to look like subtle collapsible cards with light borders
- Style buttons with tier accent colors
- Ensure code blocks use the `code/prompt bg` color (#f1f5f9)
- Cards should have subtle box-shadow for depth (e.g., `0 1px 3px rgba(0,0,0,0.08)`)
- All cards, buttons, and input fields should have border-radius of 10px for a modern feel
- "Send to This Tier" button should be full-width within its container, 48px height, semibold text, with the tier's accent color as background and white text. Not a default Streamlit button — use `st.markdown` with a styled button or custom CSS override to make it feel substantial
- Pre-set prompt buttons should be pill-shaped (border-radius 20px), with a light border, subtle hover state (background shifts to a tinted version of the active tier's accent color), and comfortable padding (10px 20px)
- Add smooth transitions on hover states
- Ensure the app looks good at 1920x1080 (projector resolution)
- Light mode throughout — high contrast text on white/off-white backgrounds

Load in `app.py` via:
```python
with open("styles/custom.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
```

---

## Setup Requirements

### Prerequisites
1. **Ollama** installed and running locally (`ollama serve`)
2. Open instruct model pulled: `ollama pull mistral:7b-instruct`
   - Fallback: `ollama pull phi3:mini`
3. **Anthropic API key** set as `ANTHROPIC_API_KEY` in `.env`
4. **OpenAI API key** set as `OPENAI_API_KEY` in `.env`
5. **Poetry** installed (`pip install poetry` or `brew install poetry`)

### .env.example
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_MODEL=mistral:7b-instruct
OLLAMA_HOST=http://localhost:11434
```

### Running
```bash
cp .env.example .env
# Add API keys to .env
poetry install
poetry run streamlit run app.py
```

---

## README.md Contents

The README should include:
1. Project title and one-line description
2. Screenshot placeholder
3. Prerequisites section (Ollama, Python 3.11+, Poetry, API keys)
4. Quick start (clone, install, configure, run)
5. How to use (brief walkthrough of the 4 tiers)
6. Troubleshooting (Ollama not running, model not found, API key issues)
7. Note that Tier 4 is demoed separately in a mental health app

---

## Behavior Summary

- **Sequential, not simultaneous.** Each tier fires only when the presenter clicks "Send to This Tier" on that tab.
- **Streaming is required.** All model responses must stream token-by-token using `st.empty()` + accumulated markdown rendering.
- **Response caching:** Cached in `st.session_state`. Switching tabs shows completed responses instantly. Changing the prompt clears all caches.
- **Error resilience:** All errors caught and displayed inline. App never crashes.
- **Response length:** Capped at ~400 tokens per tier for comparable, demo-friendly lengths.
- **Streamlit chrome hidden:** No hamburger menu, no footer, no deploy button. Light mode throughout.
- **Optimized for 1920x1080** projected display.
