## Code Conventions

### Language & Runtime
- Python 3.11+
- Use type hints on all function signatures
- Use `from __future__ import annotations` for forward references

### Data Structures
- Use Pydantic `BaseModel` for data objects that cross boundaries (config, API responses, extracted content)
- Use `dataclass` for simple internal-only structures if Pydantic feels heavy
- Use `Literal` types for finite string values (e.g., `Literal["youtube", "article"]`)
- Use Pydantic's `Field()` for validation constraints (min/max, patterns)

### Naming
- Functions: `snake_case`, verb-first for actions (`extract_metadata`, `detect_url_type`)
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private functions/methods: prefix with `_`
- Be explicit over clever (`youtube_url` not `yt_url`)

### Error Handling
- Define custom exceptions in `src/trellis/core/exceptions.py`
- Inherit from `TrellisError` base class
- Raise specific exceptions, not generic `Exception` or `ValueError`
- Include context in error messages (what failed, why, what input caused it)
- Never silently swallow exceptions

### Function Design
- Single responsibility—one function, one job
- Pure functions where possible (no side effects)
- Functions return values; only CLI layer prints to stdout
- Keep functions short (<30 lines is a good target)
- Document non-obvious parameters and return values

### Module Structure
- One primary abstraction per module
- Public API at top of file, private helpers below
- Imports grouped: stdlib, third-party, local (with blank lines between)

### Testing
- Use pytest
- Test files mirror source structure: `src/trellis/ingestion/youtube.py` → `tests/ingestion/test_youtube.py`
- Test function names: `test_<function>_<scenario>` (e.g., `test_detect_url_type_youtube_standard`)
- Mark slow/integration tests with `@pytest.mark.integration`
- Fixtures go in `conftest.py` at appropriate level
- Test behavior, not implementation details

### Dependencies
- Add dependencies via Poetry (`poetry add <package>`)
- Pin major versions for stability
- Prefer well-maintained libraries with clear APIs

### Documentation
- Docstrings on public functions (keep brief—what it does, not how)
- No docstrings needed for obvious/simple functions
- Comments explain *why*, not *what*
- Update specs if implementation diverges from plan

### Git
- Commit messages: imperative mood, concise (`Add URL detection module` not `Added URL detection module`)
- One logical change per commit
- Don't commit commented-out code or debug prints

## Project-Specific Patterns

### Configuration
- Load from `~/.config/trellis/config.toml`
- Use `src/trellis/config.py` for config access
- Environment variables override file config (e.g., `TRELLIS_VAULT_PATH`)
- Never hardcode paths or API keys

### CLI
- Use Typer for CLI commands
- Commands in `src/trellis/cli/`
- Keep CLI layer thin—delegate to core modules
- User-facing errors should be clear and actionable

### LLM Integration
- Abstract provider behind `LLMProvider` protocol (see ARCHITECTURE.md AD-4)
- Never hardcode prompts in function bodies—keep in dedicated prompt files or constants
- Log token usage for cost awareness

## What Not To Do

- Don't add features not in the current stage spec
- Don't create abstractions "for future use"—build what's needed now
- Don't use `print()` for debugging—use logging or remove before commit
- Don't catch exceptions just to re-raise them unchanged
- Don't write "wrapper" functions that just call one other function
