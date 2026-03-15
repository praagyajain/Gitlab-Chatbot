# Implementation Plan: Advanced Chatbot Features

## Overview

Incremental implementation of 11 advanced features for the GitLab Guide chatbot. Each task builds on the previous, starting with standalone feature modules, then wiring them into `app.py` and `chatbot.py`. All state lives in `st.session_state`; feature modules are stateless helpers.

## Tasks

- [x] 1. Add dependencies and initialize session state
  - Add `fpdf2` and `hypothesis` to `requirements.txt`
  - Add `_init_session_state()` to `app.py` that initializes all new `st.session_state` keys: `bookmarks`, `feedback`, `search_history`, `role_profile`, `onboarding_complete`, `onboarding_step`, `font_size`, `language`, `selected_cluster`, `rated_messages`
  - Call `_init_session_state()` at the top of `app.py` before any rendering
  - _Requirements: 2.4, 4.2, 8.1, 9.2_

- [x] 2. Implement `clustering.py`
  - [x] 2.1 Create `clustering.py` with `CLUSTER_PREFIXES`, `CLUSTER_QUESTIONS`, `get_cluster()`, `get_starter_question()`, and `get_cluster_questions()`
    - `get_cluster` must match longest prefix first and default to `"General"`
    - `CLUSTER_QUESTIONS` must include questions for all 7 clusters (Engineering, Culture, Remote Work, Finance, People Ops, Security, General)
    - _Requirements: 1.1, 1.3, 1.4, 1.5_

  - [ ]* 2.2 Write property test for cluster assignment (Property 1)
    - **Property 1: Cluster assignment covers all URLs**
    - **Validates: Requirements 1.4, 1.5**

  - [ ]* 2.3 Write property test for cluster question filtering (Property 2)
    - **Property 2: Cluster question filtering**
    - **Validates: Requirements 1.3**

  - [ ]* 2.4 Write unit tests for `clustering.py`
    - `test_cluster_engineering_url`: `get_cluster("/handbook/engineering/dev")` → `"Engineering"`
    - `test_cluster_general_fallback`: `get_cluster("/handbook/unknown/path")` → `"General"`

- [x] 3. Implement `follow_up.py`
  - [x] 3.1 Create `follow_up.py` with `generate_follow_ups(answer, llm) -> list[str]`
    - Must catch all exceptions and return `[]` on failure — never raises
    - Prompt must instruct Gemini to produce exactly 2–3 short, distinct, curiosity-driven questions
    - _Requirements: 3.1, 3.2, 3.5_

  - [ ]* 3.2 Write property test for follow-up generation (Property 4)
    - **Property 4: Follow-up generation count and failure safety**
    - **Validates: Requirements 3.1, 3.5**

- [x] 4. Implement `sensitive.py`
  - [x] 4.1 Create `sensitive.py` with `SENSITIVE_KEYWORDS`, `SENSITIVE_URL_PATHS`, `is_sensitive()`, and `DISCLAIMER_HTML`
    - `is_sensitive` checks both keyword matching (case-insensitive) and source URL path inspection
    - `DISCLAIMER_HTML` must render as a visually distinct styled warning box
    - _Requirements: 5.1, 5.3, 5.5_

  - [ ]* 4.2 Write property test for sensitive keyword detection (Property 8)
    - **Property 8: Sensitive keyword detection**
    - **Validates: Requirements 5.1**

  - [ ]* 4.3 Write property test for sensitive URL path detection (Property 9)
    - **Property 9: Sensitive URL path detection**
    - **Validates: Requirements 5.5**

  - [ ]* 4.4 Write property test for disclaimer presence (Property 10)
    - **Property 10: Disclaimer presence matches sensitivity**
    - **Validates: Requirements 5.2, 5.4**

- [x] 5. Implement `export.py`
  - [x] 5.1 Create `export.py` with `bookmarks_to_markdown()` and `bookmarks_to_pdf()`
    - `bookmarks_to_pdf` uses `fpdf2`; on failure falls back to returning markdown bytes with a warning prepended
    - Bookmark dict schema: `{"question": str, "answer": str, "sources": list[{"title": str, "url": str}]}`
    - _Requirements: 4.5, 4.6_

  - [ ]* 5.2 Write property test for markdown export completeness (Property 6)
    - **Property 6: Markdown export completeness**
    - **Validates: Requirements 4.5**

  - [ ]* 5.3 Write property test for PDF export validity (Property 7)
    - **Property 7: PDF export produces valid bytes**
    - **Validates: Requirements 4.6**

- [x] 6. Implement `onboarding.py`
  - [x] 6.1 Create `onboarding.py` with `ONBOARDING_QUESTIONS` (exactly 5) and `get_current_question(step)`
    - Questions must cover: core values, remote work, communication norms, handbook-first, getting help
    - `get_current_question` returns `None` for step ≥ 5; clamps out-of-range step gracefully
    - _Requirements: 6.2, 6.3_

  - [ ]* 6.2 Write property test for onboarding sequence completeness (Property 11)
    - **Property 11: Onboarding sequence completeness**
    - **Validates: Requirements 6.2**

  - [ ]* 6.3 Write unit tests for `onboarding.py`
    - `test_onboarding_questions_topics`: verify all 5 topic areas are covered

- [x] 7. Implement `i18n.py`
  - [x] 7.1 Create `i18n.py` with `SUPPORTED_LANGUAGES`, `TRANSLATIONS` dict, and `t(key, lang)`
    - Must support: English, French, Spanish, German, Japanese
    - `t()` falls back to English string; if English key also missing, returns the key itself
    - Translation keys: `sidebar_title`, `try_asking`, `clear_chat`, `recent_questions`, `people_also_asked`, `bookmarks`, `export_markdown`, `export_pdf`, `role_label`, `font_size_label`, `language_label`, `feedback_prompt`, `onboarding_banner_title`, `onboarding_banner_body`, `start_tour`, `skip_tour`, `next_question`
    - _Requirements: 10.4, 10.6, 10.7_

  - [ ]* 7.2 Write property test for translation lookup with fallback (Property 20)
    - **Property 20: Translation lookup with fallback**
    - **Validates: Requirements 10.6, 10.7**

  - [ ]* 7.3 Write unit tests for `i18n.py`
    - `test_supported_languages`: verify all 5 languages present

- [x] 8. Implement `feedback.py`
  - [x] 8.1 Create `feedback.py` with `record_feedback()` and `feedback_to_json()`
    - `record_feedback` appends a new record or updates an existing one (matched by question+answer) — never duplicates
    - Record schema: `{"question", "answer", "rating", "timestamp" (ISO 8601), "sources", "comment"}`
    - _Requirements: 9.2, 9.4, 9.7_

  - [ ]* 8.2 Write property test for feedback record completeness (Property 15)
    - **Property 15: Feedback record completeness**
    - **Validates: Requirements 9.2**

  - [ ]* 8.3 Write property test for feedback comment appended (Property 16)
    - **Property 16: Feedback comment appended**
    - **Validates: Requirements 9.4**

  - [ ]* 8.4 Write property test for feedback JSON round-trip (Property 17)
    - **Property 17: Feedback JSON serialization round-trip**
    - **Validates: Requirements 9.6**

  - [ ]* 8.5 Write property test for no duplicate feedback records (Property 18)
    - **Property 18: Rating update (no duplicate records)**
    - **Validates: Requirements 9.7**

- [x] 9. Checkpoint — Ensure all module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Extend `chatbot.py`
  - [x] 10.1 Add `raw_answer` key to the dict returned by `ask()` (plain text, no HTML)
    - Add optional `role_context: str = ""` parameter to `ask()` that prepends a role instruction to the question context when non-empty
    - _Requirements: 7.3, 7.4_

  - [ ]* 10.2 Write property test for conversation memory window invariant (Property 3)
    - **Property 3: Conversation memory window invariant**
    - **Validates: Requirements 2.1, 2.5**

  - [ ]* 10.3 Write unit tests for `chatbot.py` extensions
    - `test_clear_memory_resets_history`: after `clear_memory()`, memory buffer is empty

- [x] 11. Wire topic clustering into `app.py` sidebar
  - Add a cluster selector panel to the sidebar using `clustering.py`
  - When a cluster is selected, store in `st.session_state.selected_cluster`, pre-populate chat input via `st.session_state.pending_question`, and filter the "Try asking" example questions to `get_cluster_questions(cluster)`
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 12. Wire conversation memory into `app.py`
  - Ensure `st.session_state.search_history` is appended with each submitted question
  - Display "Recent Questions" section in sidebar showing last 10 from `search_history`; hide section when history is empty
  - Add "People also asked" section with ≥ 8 static trending questions; clicking any question sets `pending_question`
  - When "Clear Chat History" is clicked, also clear `search_history`
  - _Requirements: 2.3, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 12.1 Write property test for search history ordering (Property 13)
    - **Property 13: Search history ordering**
    - **Validates: Requirements 8.1**

  - [ ]* 12.2 Write property test for search history display slice (Property 14)
    - **Property 14: Search history display slice**
    - **Validates: Requirements 8.2**

- [x] 13. Wire follow-up suggestions into `app.py`
  - After each assistant answer, call `generate_follow_ups(raw_answer, llm)` and render 2–3 clickable suggestion buttons below the answer
  - Clicking a suggestion sets `st.session_state.pending_question`
  - If `generate_follow_ups` returns `[]`, render nothing
  - _Requirements: 3.1, 3.3, 3.4, 3.5_

  - [ ]* 13.1 Write unit test for follow-up click behavior
    - `test_follow_up_click_sets_pending`: clicking a follow-up button sets `pending_question`

- [x] 14. Wire sensitive topic flagging into `app.py`
  - After receiving `result` from `chatbot.ask()`, call `is_sensitive(prompt, source_urls)`
  - If sensitive, prepend `DISCLAIMER_HTML` to the rendered answer
  - If not sensitive, render answer without disclaimer
  - _Requirements: 5.2, 5.3, 5.4_

- [x] 15. Wire bookmarking and export into `app.py`
  - Render a ⭐ bookmark button alongside each assistant answer (toggle behavior using `message_index`)
  - Display bookmark count in sidebar
  - Add "Export as Markdown" and "Export as PDF" download buttons in sidebar using `st.download_button`; disable both when `bookmarks` is empty with a tooltip
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 15.1 Write property test for bookmark toggle round-trip (Property 5)
    - **Property 5: Bookmark toggle round-trip**
    - **Validates: Requirements 4.3**

- [x] 16. Wire answer feedback loop into `app.py`
  - Render 👍 / 👎 buttons below each assistant answer
  - On click, call `record_feedback()`; visually highlight the selected button for already-rated messages (using `st.session_state.rated_messages`)
  - On 👎, show an optional free-text comment field; on submit, call `record_feedback` again with the comment
  - Add "Download Feedback JSON" button in sidebar using `st.download_button`
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [x] 17. Wire onboarding flow into `app.py`
  - On first load (when `onboarding_complete` is False), display an onboarding banner with "Start Tour" and "Skip" buttons
  - "Skip" sets `onboarding_complete = True` immediately
  - "Start Tour" sets `onboarding_step = 0`; render the current onboarding question via the RAG pipeline; show "Next" and "Skip" controls; advance step on "Next"; set `onboarding_complete = True` at step 5
  - Allow free-form follow-up questions between onboarding steps
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 17.1 Write unit test for onboarding skip behavior
    - `test_onboarding_complete_flag_on_skip`: skipping sets `onboarding_complete = True`

- [x] 18. Wire role-based personalization into `app.py`
  - On first load (before onboarding or chat), prompt role selection from: Engineer, Designer, Product Manager, Sales, People Ops, Finance, Marketing, "Other / Skip"
  - Store selection in `st.session_state.role_profile`; display in sidebar
  - Add role selector widget in sidebar for changing role at any time
  - Pass `role_context` string to `chatbot.ask()` when `role_profile` is not None
  - When `role_profile` is None (Other / Skip), pass no role context
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 18.1 Write property test for role-context prompt injection (Property 12)
    - **Property 12: Role-context prompt injection**
    - **Validates: Requirements 7.3, 7.4**

  - [ ]* 18.2 Write unit test for role selection storage
    - `test_role_selection_stored`: selecting a role stores it in `session_state.role_profile`

- [x] 19. Wire accessibility and i18n into `app.py`
  - Add font size selector in sidebar (Small/14px, Medium/16px default, Large/20px); on change, inject CSS via `st.markdown` to update chat message font size without page reload
  - Add language selector in sidebar using `SUPPORTED_LANGUAGES`; store in `st.session_state.language`
  - Apply `t(key, lang)` to all static UI labels (sidebar headings, button text, placeholder text)
  - When non-English language selected, append language instruction to LLM system prompt via `role_context` or a dedicated prompt parameter
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [ ]* 19.1 Write property test for language instruction in system prompt (Property 19)
    - **Property 19: Language instruction in system prompt**
    - **Validates: Requirements 10.5**

  - [ ]* 19.2 Write unit tests for accessibility options
    - `test_font_size_options`: font size options include Small, Medium, Large

- [x] 20. Implement empty state panel in `app.py`
  - When `messages` is empty and `onboarding_complete` is True (or onboarding not active), render an empty-state panel with ≥ 4 categories (Values & Culture, Engineering, Remote Work, People & Hiring), each with 2–3 example prompts as clickable cards
  - Clicking a prompt sets `pending_question` and hides the panel
  - Panel must use existing dark-theme styles (GitLab orange accents, Inter font, rounded cards)
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 20.1 Write unit test for empty state categories
    - `test_empty_state_categories`: empty-state data has ≥ 4 categories each with 2–3 prompts

- [x] 21. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests use `hypothesis` with `@settings(max_examples=100)`
- Unit tests and property tests live in a `tests/` directory
