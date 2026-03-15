# Requirements Document

## Introduction

This document defines requirements for advanced features to be added to the GitLab Guide chatbot — a Streamlit-based RAG application that answers questions about GitLab's Handbook and Product Direction using FAISS vector search and Google Gemini. The features span UX improvements, personalization, accessibility, and retrieval quality enhancements.

## Glossary

- **Chatbot**: The GitLab Guide Streamlit application (`app.py` + `chatbot.py`)
- **Session**: A single browser session in Streamlit, represented by `st.session_state`
- **RAG**: Retrieval-Augmented Generation — the pipeline that retrieves relevant handbook chunks before generating an answer
- **Vectorstore**: The FAISS index built from scraped GitLab handbook pages
- **Cluster**: A named grouping of handbook topics (e.g., Engineering, Culture, Remote Work, Finance)
- **Bookmark**: A user-starred question-answer pair saved within the current session
- **Feedback_Store**: An in-session (and optionally persisted) log of thumbs-up/thumbs-down ratings and optional comments
- **Onboarding_Flow**: A guided sequence of five curated questions presented to first-time users
- **Role_Profile**: A user-selected role (e.g., Engineer, Designer, Sales, People Ops) used to tailor retrieval and answer framing
- **Sensitive_Topic_Detector**: The component that classifies a query as touching HR, compensation, or legal subject matter
- **Follow_Up_Generator**: The LLM sub-call that produces 2–3 suggested follow-up questions after each answer
- **Search_History**: The ordered list of questions asked during the current session
- **Export_Service**: The component that serializes bookmarked answers into PDF or Markdown format

---

## Requirements

### Requirement 1: Semantic Topic Clustering

**User Story:** As a new GitLab employee, I want to browse handbook topics by category, so that I can discover relevant content without knowing exactly what to search for.

#### Acceptance Criteria

1. THE Chatbot SHALL display a topic-cluster panel in the sidebar containing at minimum the categories: Engineering, Culture, Remote Work, Finance, People Ops, and Security.
2. WHEN a user selects a cluster category, THE Chatbot SHALL pre-populate the chat input with a representative starter question for that category.
3. WHEN a user selects a cluster category, THE Chatbot SHALL filter the "Try asking" example questions in the sidebar to show only questions relevant to that category.
4. THE Chatbot SHALL assign each handbook source document to exactly one cluster based on its URL path prefix (e.g., `/handbook/engineering/` → Engineering, `/handbook/finance/` → Finance).
5. IF a source document URL does not match any known cluster prefix, THEN THE Chatbot SHALL assign it to a default "General" cluster.

---

### Requirement 2: Conversation Memory

**User Story:** As a user asking follow-up questions, I want the chatbot to remember what we discussed earlier in the session, so that I don't have to repeat context with every message.

#### Acceptance Criteria

1. THE Chatbot SHALL retain the last 5 conversation turns (question + answer pairs) in session memory using `ConversationBufferWindowMemory`.
2. WHEN a follow-up question is asked that references a pronoun or implicit subject from a prior turn, THE Chatbot SHALL resolve the reference using the stored conversation history.
3. WHEN a user clicks "Clear Chat History", THE Chatbot SHALL reset the conversation memory to an empty state.
4. WHILE a session is active, THE Chatbot SHALL persist conversation memory in `st.session_state` so that a page re-render does not erase history.
5. IF the conversation history exceeds 5 turns, THEN THE Chatbot SHALL drop the oldest turn to maintain the window size.

---

### Requirement 3: Suggested Follow-Up Questions

**User Story:** As a user reading an answer, I want to see smart follow-up questions, so that I can continue exploring related topics without having to think of what to ask next.

#### Acceptance Criteria

1. WHEN the Chatbot returns an answer, THE Follow_Up_Generator SHALL produce exactly 2–3 follow-up question suggestions relevant to the answer content.
2. THE Follow_Up_Generator SHALL generate follow-up questions using the same LLM (Gemini) with a dedicated prompt that instructs it to produce short, distinct, curiosity-driven questions.
3. WHEN a user clicks a suggested follow-up question, THE Chatbot SHALL submit that question as the next user message.
4. THE Chatbot SHALL display follow-up suggestions below the assistant answer, visually distinct from the answer body.
5. IF the LLM call for follow-up generation fails, THEN THE Chatbot SHALL silently omit the suggestions without displaying an error to the user.

---

### Requirement 4: Bookmarking and Export

**User Story:** As a user who found a useful answer, I want to bookmark it and later export my saved answers, so that I can reference key information after the session.

#### Acceptance Criteria

1. THE Chatbot SHALL display a bookmark (⭐) button alongside each assistant answer.
2. WHEN a user clicks the bookmark button on an answer, THE Chatbot SHALL add the corresponding question-answer pair to the session's bookmark list stored in `st.session_state`.
3. WHEN a user clicks the bookmark button on an already-bookmarked answer, THE Chatbot SHALL remove that entry from the bookmark list (toggle behavior).
4. THE Chatbot SHALL display the count of current bookmarks in the sidebar.
5. WHEN a user clicks "Export as Markdown", THE Export_Service SHALL generate a `.md` file containing all bookmarked question-answer pairs with their source URLs and offer it as a download.
6. WHEN a user clicks "Export as PDF", THE Export_Service SHALL generate a `.pdf` file containing all bookmarked question-answer pairs with their source URLs and offer it as a download.
7. IF the bookmark list is empty, THEN THE Chatbot SHALL disable the export buttons and display a tooltip indicating no bookmarks have been saved.

---

### Requirement 5: Sensitive Topic Flagging

**User Story:** As a user asking about HR policies or compensation, I want to see a disclaimer, so that I know to verify sensitive information with the appropriate team.

#### Acceptance Criteria

1. THE Sensitive_Topic_Detector SHALL classify a query as sensitive if it contains keywords or semantic patterns related to: compensation, salary, equity, legal, termination, performance improvement plans, harassment, or medical leave.
2. WHEN a query is classified as sensitive, THE Chatbot SHALL prepend a disclaimer to the answer stating that the user should verify the information with HR/People Ops or Legal before acting on it.
3. THE disclaimer SHALL be visually distinct from the answer body (e.g., rendered in a styled warning box).
4. WHEN a query is not classified as sensitive, THE Chatbot SHALL omit the disclaimer entirely.
5. THE Sensitive_Topic_Detector SHALL evaluate sensitivity based on both keyword matching and the URL path of retrieved source documents (e.g., `/handbook/total-rewards/`, `/handbook/legal/`).

---

### Requirement 6: Onboarding Mode

**User Story:** As a new GitLab hire, I want a guided first-run experience, so that I can quickly learn the five most important things about working at GitLab.

#### Acceptance Criteria

1. WHEN a user opens the Chatbot for the first time in a session and has not previously dismissed the onboarding prompt, THE Chatbot SHALL display an onboarding banner offering to start the guided tour.
2. WHEN a user accepts the onboarding tour, THE Onboarding_Flow SHALL present five curated questions sequentially, one at a time, each answered by the RAG pipeline.
3. THE five onboarding questions SHALL cover: GitLab's core values, remote work guidelines, communication norms, the handbook-first approach, and how to get help.
4. WHEN the user completes or skips the onboarding tour, THE Chatbot SHALL set a session flag (`onboarding_complete`) to prevent the banner from reappearing during the same session.
5. WHEN a user clicks "Skip" at any point during the onboarding tour, THE Onboarding_Flow SHALL immediately exit and return the user to the standard chat interface.
6. THE Onboarding_Flow SHALL allow the user to ask follow-up questions after each curated answer before advancing to the next onboarding step.

---

### Requirement 7: Role-Based Personalization

**User Story:** As a user with a specific role at GitLab, I want the chatbot to tailor its answers to my role, so that I receive the most relevant information for my day-to-day work.

#### Acceptance Criteria

1. WHEN a user opens the Chatbot for the first time in a session, THE Chatbot SHALL prompt the user to select their role from: Engineer, Designer, Product Manager, Sales, People Ops, Finance, Marketing, and "Other / Skip".
2. WHEN a role is selected, THE Chatbot SHALL store the Role_Profile in `st.session_state` and display the selected role in the sidebar.
3. WHEN a role is selected, THE Chatbot SHALL append a role-context instruction to the LLM system prompt (e.g., "The user is an Engineer. Prioritize engineering-specific handbook sections.").
4. WHEN the user selects "Other / Skip", THE Chatbot SHALL proceed without role-based prompt modification.
5. THE Chatbot SHALL allow the user to change their role at any time via a selector in the sidebar, and THE Chatbot SHALL update the Role_Profile immediately upon change.
6. WHILE a Role_Profile is active, THE Chatbot SHALL bias retrieval toward handbook sections associated with that role's cluster.

---

### Requirement 8: Search History and Smart Suggestions

**User Story:** As a returning user within a session, I want to see my past questions and trending questions from other users, so that I can quickly revisit topics and discover what others are asking.

#### Acceptance Criteria

1. THE Chatbot SHALL maintain an ordered Search_History list in `st.session_state` containing every question submitted during the session.
2. THE Chatbot SHALL display the Search_History in the sidebar under a "Recent Questions" section, showing the 10 most recent questions.
3. WHEN a user clicks a question in the Search_History, THE Chatbot SHALL re-submit that question as a new chat message.
4. THE Chatbot SHALL display a "People also asked" section in the sidebar containing a static curated list of at least 8 trending questions drawn from common GitLab handbook topics.
5. WHEN a user clicks a question in the "People also asked" section, THE Chatbot SHALL submit that question as a new chat message.
6. IF the Search_History is empty, THEN THE Chatbot SHALL hide the "Recent Questions" section from the sidebar.

---

### Requirement 9: Answer Feedback Loop

**User Story:** As a user who received an answer, I want to rate it with a thumbs up or down and optionally leave a comment, so that the system can improve retrieval quality over time.

#### Acceptance Criteria

1. THE Chatbot SHALL display a 👍 and 👎 button below each assistant answer.
2. WHEN a user clicks 👍 or 👎, THE Feedback_Store SHALL record the question, answer, rating, timestamp, and retrieved source URLs in `st.session_state`.
3. WHEN a user clicks 👎, THE Chatbot SHALL display an optional free-text comment field prompting "What could be improved?".
4. WHEN a user submits a comment, THE Feedback_Store SHALL append the comment text to the corresponding feedback record.
5. THE Chatbot SHALL visually indicate which answers have already been rated (e.g., highlight the selected button) so the user cannot accidentally rate the same answer twice.
6. THE Chatbot SHALL provide a sidebar control to download all session feedback as a JSON file for offline analysis.
7. IF a user attempts to rate an already-rated answer, THEN THE Chatbot SHALL allow the user to change their rating by clicking the opposite button, updating the Feedback_Store record accordingly.

---

### Requirement 10: Accessibility and Internationalization

**User Story:** As a user with accessibility needs or a non-English preference, I want font size controls, keyboard navigation, and multilingual support, so that I can use the chatbot comfortably.

#### Acceptance Criteria

1. THE Chatbot SHALL provide font size controls in the sidebar offering at least three size options: Small (14px), Medium (16px, default), and Large (20px).
2. WHEN a font size option is selected, THE Chatbot SHALL apply the chosen size to all chat message text via injected CSS without requiring a page reload.
3. THE Chatbot SHALL ensure all interactive controls (buttons, chat input, sidebar selectors) are reachable and operable via keyboard navigation in accordance with standard browser tab-order behavior.
4. WHERE multilingual support is enabled, THE Chatbot SHALL accept a language preference selection (English, French, Spanish, German, Japanese) in the sidebar.
5. WHERE a non-English language is selected, THE Chatbot SHALL instruct the LLM via the system prompt to respond in the selected language.
6. WHERE a non-English language is selected, THE Chatbot SHALL translate all static UI labels (sidebar headings, button text, placeholder text) to the selected language using a bundled translation dictionary.
7. IF a translation key is missing for the selected language, THEN THE Chatbot SHALL fall back to the English string for that label.

---

### Requirement 11: Empty State Design

**User Story:** As a first-time user opening the chatbot, I want to see example prompts grouped by category instead of a blank chat box, so that I immediately understand what the chatbot can help me with.

#### Acceptance Criteria

1. WHEN the chat history is empty and no onboarding tour is active, THE Chatbot SHALL display an empty-state panel in the main content area showing example prompts grouped by category.
2. THE empty-state panel SHALL include at least four categories: Values & Culture, Engineering, Remote Work, and People & Hiring, each with 2–3 example prompts.
3. WHEN a user clicks an example prompt in the empty-state panel, THE Chatbot SHALL submit that prompt as the first user message and hide the empty-state panel.
4. WHEN the chat history contains at least one message, THE Chatbot SHALL hide the empty-state panel and display the chat history instead.
5. THE empty-state panel SHALL be visually consistent with the existing dark-theme design (GitLab orange accent colors, Inter font, rounded cards).
