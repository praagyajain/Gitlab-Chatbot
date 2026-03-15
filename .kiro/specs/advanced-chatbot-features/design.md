# Design Document: Advanced Chatbot Features

## Overview

This document describes the technical design for adding advanced features to the GitLab Guide chatbot — a Streamlit-based RAG application. The features span UX improvements (empty state, onboarding, topic clustering), personalization (role-based prompting, search history), retrieval quality (conversation memory, follow-up suggestions), safety (sensitive topic flagging), and accessibility/i18n.

The existing architecture is:
- `app.py` — Streamlit UI, session state management, rendering
- `chatbot.py` — `GitLabChatbot` class wrapping LangChain `ConversationalRetrievalChain`
- `config.py` — centralized constants
- `data_processor.py` — FAISS index builder

All new features are implemented as additions to these files plus new supporting modules. No changes to the FAISS index or embedding pipeline are required.

---

## Architecture

The design follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py (UI Layer)                     │
│  Sidebar │ Main Chat Area │ Empty State │ Onboarding Banner  │
└────────────────────────┬────────────────────────────────────┘
                         │ calls
┌────────────────────────▼────────────────────────────────────┐
│                   Feature Modules                            │
│  clustering.py │ follow_up.py │ sensitive.py │ export.py    │
│  onboarding.py │ i18n.py      │ feedback.py  │              │
└────────────────────────┬────────────────────────────────────┘
                         │ calls
┌────────────────────────▼────────────────────────────────────┐
│                   chatbot.py (RAG Layer)                     │
│  GitLabChatbot  │  ConversationalRetrievalChain              │
│  ConversationBufferWindowMemory (k=5)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              FAISS Vectorstore + Gemini LLM                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **All state lives in `st.session_state`**: Streamlit re-renders on every interaction; all mutable state (bookmarks, feedback, search history, role, onboarding flags) is stored in `st.session_state` to survive re-renders within a session.
- **Feature modules are stateless helpers**: Each new module exposes pure functions or simple classes; they do not import Streamlit directly (except where rendering is unavoidable), making them independently testable.
- **No new LLM chains**: Follow-up generation and sensitive-topic detection reuse the existing `ChatGoogleGenerativeAI` instance via direct calls rather than new chains, keeping initialization cost low.
- **No persistent storage**: All data (bookmarks, feedback, history) is session-scoped. Export functions serialize from `st.session_state` at download time.

---

## Components and Interfaces

### 1. `clustering.py` — Semantic Topic Clustering

Responsible for mapping handbook URLs to named clusters and providing per-cluster starter questions.

```python
CLUSTER_PREFIXES: dict[str, str]  # url_prefix -> cluster_name
CLUSTER_QUESTIONS: dict[str, list[str]]  # cluster_name -> [questions]

def get_cluster(url: str) -> str:
    """Return cluster name for a URL, defaulting to 'General'."""

def get_starter_question(cluster: str) -> str:
    """Return a representative starter question for the cluster."""

def get_cluster_questions(cluster: str) -> list[str]:
    """Return example questions filtered to the given cluster."""
```

### 2. `follow_up.py` — Follow-Up Question Generator

Makes a secondary Gemini call to produce 2–3 follow-up questions.

```python
def generate_follow_ups(
    answer: str,
    llm: ChatGoogleGenerativeAI,
) -> list[str]:
    """
    Return 2-3 follow-up question strings, or [] on failure.
    Never raises — failures are silently swallowed.
    """
```

### 3. `sensitive.py` — Sensitive Topic Detector

Classifies queries using keyword matching and source URL path inspection.

```python
SENSITIVE_KEYWORDS: frozenset[str]
SENSITIVE_URL_PATHS: frozenset[str]

def is_sensitive(query: str, source_urls: list[str]) -> bool:
    """Return True if query or any source URL matches sensitive patterns."""

DISCLAIMER_HTML: str  # styled warning box HTML
```

### 4. `export.py` — Export Service

Serializes bookmarks to Markdown or PDF bytes.

```python
def bookmarks_to_markdown(bookmarks: list[dict]) -> str:
    """Render bookmarks as a Markdown string."""

def bookmarks_to_pdf(bookmarks: list[dict]) -> bytes:
    """Render bookmarks as PDF bytes using fpdf2."""
```

Bookmark dict schema: `{"question": str, "answer": str, "sources": list[{"title": str, "url": str}]}`

### 5. `onboarding.py` — Onboarding Flow

Defines the five curated questions and manages step progression.

```python
ONBOARDING_QUESTIONS: list[str]  # exactly 5 questions

def get_current_question(step: int) -> str | None:
    """Return question for step index, or None if tour is complete."""
```

### 6. `i18n.py` — Internationalization

Provides a translation dictionary and lookup with English fallback.

```python
SUPPORTED_LANGUAGES: list[str]  # ["English", "French", "Spanish", "German", "Japanese"]
TRANSLATIONS: dict[str, dict[str, str]]  # lang -> {key -> translated_string}

def t(key: str, lang: str) -> str:
    """Return translated string for key in lang, falling back to English."""
```

### 7. `feedback.py` — Feedback Store Utilities

Helper functions for managing the feedback list in session state.

```python
def record_feedback(
    session_state,
    question: str,
    answer: str,
    rating: str,  # "up" | "down"
    sources: list[dict],
    comment: str = "",
) -> None:
    """Append or update a feedback record in session_state.feedback."""

def feedback_to_json(feedback: list[dict]) -> str:
    """Serialize feedback list to JSON string."""
```

### 8. `chatbot.py` — Extended `GitLabChatbot`

Minimal additions to the existing class:

- `ask()` return dict gains `"raw_answer": str` (answer without HTML) for use by `follow_up.py` and `sensitive.py`
- `clear_memory()` already exists; no change needed
- Role-context injection: `app.py` builds the system prompt string and passes it; `GitLabChatbot` gains an optional `role_context: str` parameter on `ask()` that prepends to the question context

---

## Data Models

All runtime data lives in `st.session_state`. Below are the schemas for new keys.

### `st.session_state.bookmarks`
```python
list[dict]
# Each entry:
{
    "question": str,
    "answer": str,       # plain text, no HTML
    "sources": list[{"title": str, "url": str}],
    "message_index": int  # index into st.session_state.messages
}
```

### `st.session_state.feedback`
```python
list[dict]
# Each entry:
{
    "question": str,
    "answer": str,
    "rating": "up" | "down",
    "timestamp": str,    # ISO 8601
    "sources": list[{"title": str, "url": str}],
    "comment": str       # "" if no comment
}
```

### `st.session_state.search_history`
```python
list[str]  # ordered list of submitted questions, newest last
```

### `st.session_state.role_profile`
```python
str | None  # e.g. "Engineer", None if "Other / Skip"
```

### `st.session_state.onboarding_complete`
```python
bool  # True once user completes or skips onboarding
```

### `st.session_state.onboarding_step`
```python
int  # 0-4 during tour, 5 when complete
```

### `st.session_state.font_size`
```python
str  # "small" | "medium" | "large"
```

### `st.session_state.language`
```python
str  # "English" | "French" | "Spanish" | "German" | "Japanese"
```

### `st.session_state.selected_cluster`
```python
str | None  # active cluster filter, None = all
```

### `st.session_state.rated_messages`
```python
set[int]  # set of message indices that have been rated
```

### Cluster Prefix Mapping (static, in `clustering.py`)

| URL Prefix | Cluster |
|---|---|
| `/handbook/engineering/` | Engineering |
| `/handbook/product/` | Engineering |
| `/handbook/company/culture/` | Culture |
| `/handbook/values/` | Culture |
| `/handbook/company/culture/all-remote/` | Remote Work |
| `/handbook/finance/` | Finance |
| `/handbook/total-rewards/` | Finance |
| `/handbook/people-group/` | People Ops |
| `/handbook/hiring/` | People Ops |
| `/handbook/security/` | Security |
| `/handbook/legal/` | Security |
| *(no match)* | General |

### Sensitive Topic Keywords (static, in `sensitive.py`)

Keywords: `compensation`, `salary`, `equity`, `legal`, `termination`, `pip`, `performance improvement plan`, `harassment`, `medical leave`, `severance`, `layoff`

Sensitive URL paths: `/handbook/total-rewards/`, `/handbook/legal/`, `/handbook/people-group/employment/`

### Onboarding Questions (static, in `onboarding.py`)

1. "What are GitLab's core values and how do they guide daily work?"
2. "What are the key guidelines for working remotely at GitLab?"
3. "How does GitLab approach communication and what are the norms?"
4. "What is the handbook-first approach and why does GitLab use it?"
5. "How do I get help when I'm stuck or have a question at GitLab?"

### Translation Keys (in `i18n.py`)

Keys include: `sidebar_title`, `try_asking`, `clear_chat`, `recent_questions`, `people_also_asked`, `bookmarks`, `export_markdown`, `export_pdf`, `role_label`, `font_size_label`, `language_label`, `feedback_prompt`, `onboarding_banner_title`, `onboarding_banner_body`, `start_tour`, `skip_tour`, `next_question`


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Cluster assignment covers all URLs

*For any* handbook URL, `get_cluster(url)` returns exactly one cluster name from the known set (Engineering, Culture, Remote Work, Finance, People Ops, Security, General), and any URL that does not match a known prefix is assigned to "General".

**Validates: Requirements 1.4, 1.5**

---

### Property 2: Cluster question filtering

*For any* cluster name, every question returned by `get_cluster_questions(cluster)` belongs to that cluster, and no question from a different cluster is included.

**Validates: Requirements 1.3**

---

### Property 3: Conversation memory window invariant

*For any* sequence of conversation turns added to `ConversationBufferWindowMemory(k=5)`, the memory never retains more than 5 turns, and when the window is exceeded the oldest turn is dropped.

**Validates: Requirements 2.1, 2.5**

---

### Property 4: Follow-up generation count and failure safety

*For any* non-empty answer string passed to `generate_follow_ups`, the function either returns a list of 2 or 3 strings, or returns an empty list if the LLM call raises an exception — it never raises itself.

**Validates: Requirements 3.1, 3.5**

---

### Property 5: Bookmark toggle round-trip

*For any* question-answer pair, adding it to the bookmark list and then adding it again (toggle) results in the bookmark list returning to its original state (the entry is removed).

**Validates: Requirements 4.3**

---

### Property 6: Markdown export completeness

*For any* non-empty list of bookmarks, `bookmarks_to_markdown(bookmarks)` returns a string that contains each bookmark's question text and answer text.

**Validates: Requirements 4.5**

---

### Property 7: PDF export produces valid bytes

*For any* non-empty list of bookmarks, `bookmarks_to_pdf(bookmarks)` returns a non-empty bytes object beginning with the PDF magic bytes (`%PDF`).

**Validates: Requirements 4.6**

---

### Property 8: Sensitive keyword detection

*For any* query string containing at least one word from `SENSITIVE_KEYWORDS`, `is_sensitive(query, [])` returns `True`.

**Validates: Requirements 5.1**

---

### Property 9: Sensitive URL path detection

*For any* list of source URLs where at least one URL contains a path from `SENSITIVE_URL_PATHS`, `is_sensitive("", source_urls)` returns `True`.

**Validates: Requirements 5.5**

---

### Property 10: Disclaimer presence matches sensitivity

*For any* query and source URL list, the disclaimer HTML is prepended to the answer if and only if `is_sensitive(query, source_urls)` returns `True`.

**Validates: Requirements 5.2, 5.4**

---

### Property 11: Onboarding sequence completeness

*For any* step index `i` in `[0, 1, 2, 3, 4]`, `get_current_question(i)` returns a non-empty string; for step index `5` (or greater), it returns `None`.

**Validates: Requirements 6.2**

---

### Property 12: Role-context prompt injection

*For any* non-None role string, the system prompt string built by `app.py` contains a role-specific instruction mentioning that role; when role is `None` (Other / Skip), no role instruction is added.

**Validates: Requirements 7.3, 7.4**

---

### Property 13: Search history ordering

*For any* sequence of questions submitted during a session, `st.session_state.search_history` contains those questions in submission order (oldest first, newest last).

**Validates: Requirements 8.1**

---

### Property 14: Search history display slice

*For any* search history list of length `n`, the sidebar displays `min(n, 10)` questions, always showing the most recent ones.

**Validates: Requirements 8.2**

---

### Property 15: Feedback record completeness

*For any* call to `record_feedback(session_state, question, answer, rating, sources)`, the resulting record in `session_state.feedback` contains non-empty values for `question`, `answer`, `rating`, `timestamp`, and `sources`.

**Validates: Requirements 9.2**

---

### Property 16: Feedback comment appended

*For any* existing feedback record and any comment string, calling `record_feedback` with that comment updates the record so that `record["comment"] == comment`.

**Validates: Requirements 9.4**

---

### Property 17: Feedback JSON serialization round-trip

*For any* list of feedback records, `json.loads(feedback_to_json(feedback))` produces a list of equal length containing the same records.

**Validates: Requirements 9.6**

---

### Property 18: Rating update (no duplicate records)

*For any* message index that has already been rated, submitting a new rating via `record_feedback` updates the existing record rather than appending a new one, so the feedback list length does not increase.

**Validates: Requirements 9.7**

---

### Property 19: Language instruction in system prompt

*For any* non-English language selection, the system prompt string contains an explicit instruction to respond in that language.

**Validates: Requirements 10.5**

---

### Property 20: Translation lookup with fallback

*For any* translation key and language, `t(key, lang)` returns a non-empty string; if the key is missing for the given language, it returns the English string for that key.

**Validates: Requirements 10.6, 10.7**

---

## Error Handling

### LLM Failures
- `generate_follow_ups` catches all exceptions and returns `[]` — the UI simply renders no follow-up buttons.
- `GitLabChatbot.ask()` propagates exceptions to `app.py`, which catches them and renders a user-friendly error message (existing behavior, unchanged).

### Export Failures
- `bookmarks_to_pdf` catches `fpdf2` errors and falls back to returning `bookmarks_to_markdown(...).encode()` as a plain-text download, with a warning message prepended.

### Missing Translation Keys
- `t(key, lang)` falls back to `TRANSLATIONS["English"][key]`; if the English key is also missing, returns the key string itself as a last resort.

### Sensitive Topic Detection Errors
- `is_sensitive` is pure Python with no I/O; it cannot fail. No error handling needed.

### Onboarding State Corruption
- If `onboarding_step` is out of range, `get_current_question` clamps it and returns `None`, causing the tour to end gracefully.

### Session State Missing Keys
- All new session state keys are initialized in a single `_init_session_state()` function called at the top of `app.py`, ensuring keys always exist before use.

---

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are required. They are complementary:
- Unit tests cover specific examples, integration points, and edge cases.
- Property-based tests verify universal correctness across randomized inputs.

### Property-Based Testing

**Library**: `hypothesis` (Python)

Each correctness property above maps to exactly one `@given`-decorated test. Tests are configured with `settings(max_examples=100)`.

Each test is tagged with a comment in the format:
```
# Feature: advanced-chatbot-features, Property N: <property_text>
```

**Example**:
```python
from hypothesis import given, settings, strategies as st

# Feature: advanced-chatbot-features, Property 1: Cluster assignment covers all URLs
@given(st.text(min_size=1))
@settings(max_examples=100)
def test_cluster_assignment_covers_all_urls(url):
    result = get_cluster(url)
    assert result in VALID_CLUSTERS
```

**Properties to implement as PBT** (one test each):
- Property 1: `get_cluster` returns valid cluster for any URL
- Property 2: `get_cluster_questions` returns only questions for the given cluster
- Property 3: Memory window never exceeds 5 turns
- Property 4: `generate_follow_ups` returns 2–3 items or [] on failure
- Property 5: Bookmark toggle is a round-trip
- Property 6: Markdown export contains all bookmark content
- Property 7: PDF export produces valid bytes
- Property 8: Keyword detection returns True for sensitive queries
- Property 9: URL path detection returns True for sensitive source URLs
- Property 10: Disclaimer presence matches `is_sensitive` result
- Property 11: Onboarding sequence returns non-None for steps 0–4, None for step ≥5
- Property 12: Role prompt injection present iff role is not None
- Property 13: Search history preserves submission order
- Property 14: Search history display slice is min(n, 10) most recent
- Property 15: Feedback record has all required fields
- Property 16: Feedback comment is stored in record
- Property 17: Feedback JSON round-trip preserves all records
- Property 18: Re-rating updates record, does not duplicate
- Property 19: Non-English language produces language instruction in prompt
- Property 20: Translation lookup falls back to English for missing keys

### Unit Tests

Unit tests focus on specific examples and integration points. Avoid duplicating what property tests already cover.

**Key unit test cases**:
- `test_cluster_engineering_url`: `get_cluster("/handbook/engineering/dev")` → `"Engineering"`
- `test_cluster_general_fallback`: `get_cluster("/handbook/unknown/path")` → `"General"`
- `test_onboarding_questions_topics`: ONBOARDING_QUESTIONS covers values, remote work, communication, handbook-first, getting help
- `test_empty_state_categories`: empty-state data has ≥4 categories each with 2–3 prompts
- `test_font_size_options`: font size options include Small, Medium, Large
- `test_supported_languages`: SUPPORTED_LANGUAGES contains English, French, Spanish, German, Japanese
- `test_people_also_asked_count`: static trending questions list has ≥8 items
- `test_clear_memory_resets_history`: after `clear_memory()`, memory buffer is empty
- `test_follow_up_click_sets_pending`: clicking a follow-up button sets `pending_question`
- `test_role_selection_stored`: selecting a role stores it in `session_state.role_profile`
- `test_onboarding_complete_flag_on_skip`: skipping sets `onboarding_complete = True`
